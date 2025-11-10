from __future__ import annotations

import os
import sys
import json
import logging
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

# Ensure the project src directory is on PYTHONPATH when running via uvicorn
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from captable.schema import CAP_TABLE_SCHEMA
from captable.validation import CapTableValidator


try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # fallback for environments without openai installed


app = FastAPI(title="Cap Table LLM Editor")

# Configure server-side logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("captable.server")
# Also write logs to file for full trace
try:
    _LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "chat.log"))
    fh = logging.FileHandler(_LOG_PATH)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
except Exception:
    pass


class ChatRequest(BaseModel):
    message: str
    # Optional full JSON replacement from client (power user)
    replace_json: Optional[Dict[str, Any]] = None
    # Session identifier for conversation threading
    session_id: Optional[str] = None
    # When true, do not call OpenAI; return the exact payload/messages that would be sent
    dry_run: Optional[bool] = None


class EditPayload(BaseModel):
    mode: str  # 'replace' | 'merge'
    payload: Dict[str, Any]


# In-memory cap table store (initialize empty valid shell)
STATE: Dict[str, Any] = {
    "schema_version": "2.0",
    "company": {"name": "Acme, Inc."},
    "holders": [],
    "rounds": []
}

validator = CapTableValidator()

# In-memory session store: session_id -> list of messages {role, content}
SESSIONS: Dict[str, List[Dict[str, str]]] = {}
MAX_TURNS = 12  # keep last N turns to control prompt size


def _validate_or_422(data: Dict[str, Any]) -> None:
    """Validate cap table data using full validation pipeline.
    
    Raises HTTPException with 422 status if validation fails.
    """
    is_valid, errors = validator.validate(data)
    if not is_valid:
        # Format errors as a dict for consistent error handling
        error_dict = {}
        for i, error in enumerate(errors):
            error_dict[f"validation_error_{i}"] = error
        raise HTTPException(status_code=422, detail=error_dict)


def _get_session_id(req: ChatRequest) -> str:
    # Default to a single-session if none provided
    return req.session_id or "default"


def _append_history(session_id: str, role: str, content: str) -> None:
    hist = SESSIONS.setdefault(session_id, [])
    hist.append({"role": role, "content": content})
    # trim
    if len(hist) > MAX_TURNS * 2:  # user+assistant pairs
        del hist[: len(hist) - MAX_TURNS * 2]


def _log_preview(label: str, session_id: str, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> None:
    try:
        logger.info("%s sid=%s messages_count=%d",
                    label, session_id, len(messages))
        # Log full content without truncation
        for i, m in enumerate(messages):
            content = m.get("content") or ""
            logger.info("msg[%d] role=%s content=%s",
                        i, m.get("role"), content)
        if tools:
            logger.info("tools=%s", json.dumps(tools, indent=2))
    except Exception as e:
        logger.warning("failed to log preview: %s", e)


def _build_schema_digest(schema: Dict[str, Any]) -> str:
    """Create a compact, LLM-friendly schema digest.

    Principles from best practices: keep structure flat, show unions explicitly,
    include minimal rules and examples, avoid verbose JSON Schema syntax.
    """
    lines: List[str] = []

    def type_str(spec: Dict[str, Any]) -> str:
        # oneOf number | FormulaEncodingObject
        if isinstance(spec.get("oneOf"), list):
            parts: List[str] = []
            for opt in spec["oneOf"]:
                if opt.get("type") == "number":
                    parts.append("number")
                elif opt.get("$ref") == "#/$defs/FormulaEncodingObject":
                    parts.append("formula")
                else:
                    parts.append(opt.get("type") or opt.get("$ref", "unknown"))
            return " | ".join(parts)
        # ref to formula
        if spec.get("$ref") == "#/$defs/FormulaEncodingObject":
            return "formula"
        # plain type or $ref
        t = spec.get("type")
        if t:
            return str(t)
        ref = spec.get("$ref")
        if ref:
            return f"ref:{ref.split('/')[-1]}"
        return "unknown"

    def enum_str(spec: Dict[str, Any]) -> Optional[str]:
        if isinstance(spec.get("enum"), list):
            return ", ".join(map(str, spec["enum"]))
        return None

    # Root
    props = schema.get("properties", {})
    required = schema.get("required", [])
    lines.append("Root:")
    for name, spec in props.items():
        lines.append(f"- {name}: {type_str(spec)}")
    if required:
        lines.append(f"- required: {', '.join(required)}")

    defs = schema.get("$defs", {})
    # Selected defs
    for def_name in ["Company", "Holder", "SecurityClass", "Instrument", "Round", "VestingTerms", "FormulaEncodingObject"]:
        d = defs.get(def_name)
        if not isinstance(d, dict):
            continue
        lines.append("")
        lines.append(f"{def_name}:")
        d_props = d.get("properties", {})
        d_req = d.get("required", [])
        for pname, pspec in d_props.items():
            t = type_str(pspec)
            es = enum_str(pspec)
            suffix = f" enum[{es}]" if es else ""
            lines.append(f"- {pname}: {t}{suffix}")
        if d_req:
            lines.append(f"- required: {', '.join(d_req)}")

    # Conditional rules (LLM-friendly mapping)
    rnd = defs.get("Round") or {}
    lines.append("")
    lines.append("Round types and required fields:")
    lines.append("- fixed_shares:")
    lines.append("  - Round requires: (no extra beyond name, round_date, calculation_type)")
    lines.append("  - Each instrument requires: initial_quantity (number | formula)")
    lines.append("- target_percentage:")
    lines.append("  - Round requires: (no extra beyond name, round_date, calculation_type)")
    lines.append("  - Each instrument requires: target_percentage (0..1)")
    lines.append("- valuation_based:")
    lines.append("  - Round requires: valuation_basis (pre_money|post_money), investment_amount (number)")
    lines.append("  - Each instrument requires: (none beyond holder_(name|ref), class_(name|ref))")
    lines.append("  - Note: Provide pre_money_valuation or post_money_valuation (or let model compute price_per_share)")
    lines.append("- convertible:")
    lines.append("  - Round requires: valuation_cap_basis (pre_money|post_money|fixed)")
    lines.append("  - Each instrument requires: (none beyond holder_(name|ref), class_(name|ref))")
    lines.append("  - Notes:")
    lines.append("    - If valuation_cap_basis=fixed: price_per_share required")
    lines.append("    - Else: provide pre_money_valuation or post_money_valuation")
    lines.append("    - Instrument may include discount_rate (0..1) and interest_* fields")

    # Referential guidance and examples
    lines.append("")
    lines.append("Notes:")
    lines.append("- Add holders before instruments referencing holder_name.")
    lines.append(
        "- Percentages are decimals (e.g., 0.20). Dates are YYYY-MM-DD.")
    lines.append(
        "- Example fixed_shares instrument: {holder_name: 'John Doe', class_name: 'Common', initial_quantity: 5000000}.")

    return "\n".join(lines)


SCHEMA_DIGEST = _build_schema_digest(CAP_TABLE_SCHEMA)


def _extract_conversation_summary(session_id: str) -> str:
    """Extract key information from conversation history to help the model remember.
    
    Returns a summary string of important details mentioned in the conversation.
    """
    history = SESSIONS.get(session_id, [])
    if not history:
        return ""
    
    # Collect all user messages for context
    user_messages = [msg.get("content", "") for msg in history if msg.get("role") == "user"]
    
    if not user_messages:
        return ""
    
    # Build a comprehensive summary of user-provided information
    summary_lines = []
    summary_lines.append("Key information from conversation history:")
    summary_lines.append("")
    
    # Include recent user messages (last 5) for context
    for i, msg in enumerate(user_messages[-5:], 1):
        summary_lines.append(f"User message {i}: {msg}")
    
    summary_lines.append("")
    summary_lines.append("IMPORTANT: All information above was already provided. Use it to complete the request without asking again.")
    
    return "\n".join(summary_lines)


def _build_messages(session_id: str, state: Dict[str, Any], user_message: str) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    # Put system messages first, then history, then the new user message last
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "system", "content": "Schema digest (read-only, follow strictly):\n" + SCHEMA_DIGEST})
    messages.append({"role": "system", "content": "Current cap table JSON:\n" + json.dumps(state, indent=2)})
    
    # Add conversation summary if there's history
    summary = _extract_conversation_summary(session_id)
    if summary:
        messages.append({
            "role": "system",
            "content": f"Conversation context (review carefully):\n{summary}\n\nRemember: Use information from previous messages. Do NOT ask for information already provided."
        })
    
    # Tool usage guide to discourage empty payloads and confirmations
    messages.append({
        "role": "system",
        "content": (
            "Tool usage: Call edit_cap_table with non-empty JSON. Examples:\n"
            "- Merge example (add incorporation round): {\"mode\":\"merge\", \"payload\": {\"rounds\": [{\"name\": \"Incorporation\", \"round_date\": \"YYYY-MM-DD\", \"calculation_type\": \"fixed_shares\", \"instruments\": [{\"holder_name\": \"John Doe\", \"class_name\": \"Common\", \"initial_quantity\": 5000000}]}]}}\n"
            "- Merge example (add investment round): {\"mode\":\"merge\", \"payload\": {\"rounds\": [{\"name\": \"Series A\", \"round_date\": \"YYYY-MM-DD\", \"calculation_type\": \"valuation_based\", \"valuation_basis\": \"pre_money\", \"investment_amount\": 750000, \"instruments\": [{\"holder_name\": \"Alice Smith\", \"class_name\": \"Common\"}, {\"holder_name\": \"Bob Johnson\", \"class_name\": \"Common\"}, {\"holder_name\": \"Acme Ventures\", \"class_name\": \"Common\"}]}]}}\n"
            "If any required field is missing, ask a focused question. Do NOT call the tool with an empty payload."
        )
    })
    # include recent history
    for m in SESSIONS.get(session_id, []):
        messages.append({"role": m["role"], "content": m["content"]})
    # current user message last
    messages.append({"role": "user", "content": user_message})
    return messages


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    # Minimal static page; for fuller UI move to templates/static files
    return (
        """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>Cap Table LLM Editor</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; display: flex; height: 100vh; }
      #chat { flex: 1; display: flex; flex-direction: column; }
      #messages { flex: 1; padding: 16px; overflow: auto; border-right: 1px solid #ddd; }
      #input { display: flex; gap: 8px; padding: 8px; border-top: 1px solid #eee; }
      #jsonPanel { width: 50%; padding: 16px; overflow: auto; }
      .bubble { margin-bottom: 12px; }
      .user { color: #333; }
      .assistant { color: #0a5; }
      textarea { width: 100%; height: 70px; }
      pre { background: #fafafa; padding: 12px; border: 1px solid #eee; }
      .tool-call-indicator { 
        padding: 8px 12px; 
        margin: 8px 0; 
        border-radius: 4px; 
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .tool-call-indicator.pending { 
        background: #e3f2fd; 
        color: #1976d2; 
        border-left: 3px solid #1976d2;
      }
      .tool-call-indicator.success { 
        background: #e8f5e9; 
        color: #2e7d32; 
        border-left: 3px solid #2e7d32;
      }
      .tool-call-indicator.error { 
        background: #ffebee; 
        color: #c62828; 
        border-left: 3px solid #c62828;
      }
      .tool-call-indicator.validation_error { 
        background: #fff3e0; 
        color: #e65100; 
        border-left: 3px solid #e65100;
      }
      .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #1976d2;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      .status-text {
        font-weight: 500;
      }
    </style>
  </head>
  <body>
    <div id=\"chat\">
      <div id=\"messages\"></div>
      <div id=\"input\">
        <textarea id=\"text\" placeholder=\"Ask the model to edit the cap table...\"></textarea>
        <button id=\"send\">Send</button>
        <label style=\"display:flex;align-items:center;gap:6px;\"><input type=\"checkbox\" id=\"useStream\" checked /> Stream reply</label>
      </div>
    </div>
    <div id=\"jsonPanel\">
      <h3>Cap Table JSON</h3>
      <pre id=\"json\"></pre>
    </div>
    <script>
      async function refreshJSON(){
        const res = await fetch('/api/cap-table');
        const data = await res.json();
        document.getElementById('json').textContent = JSON.stringify(data, null, 2);
      }
      function showToolCallIndicator(status) {
        const msgs = document.getElementById('messages');
        // Remove existing indicator if any
        const existing = msgs.querySelector('.tool-call-indicator');
        if(existing) existing.remove();
        
        const indicator = document.createElement('div');
        indicator.className = 'tool-call-indicator ' + status;
        
        let text = '';
        if(status === 'pending') {
          text = '<div class="spinner"></div><span class="status-text">Processing tool call...</span>';
        } else if(status === 'success') {
          text = '<span class="status-text">✓ Tool call succeeded</span>';
        } else if(status === 'error') {
          text = '<span class="status-text">✗ Tool call failed</span>';
        } else if(status === 'validation_error') {
          text = '<span class="status-text">⚠ Validation error - retrying...</span>';
        }
        
        indicator.innerHTML = text;
        msgs.appendChild(indicator);
        indicator.scrollIntoView({behavior: 'smooth', block: 'end'});
        return indicator;
      }
      
      async function send(){
        const text = document.getElementById('text').value.trim();
        if(!text) return;
        addMsg('user', text);
        document.getElementById('text').value = '';
        const useStream = document.getElementById('useStream').checked;
        if(useStream){
          try {
            const res = await fetch('/api/chat/stream', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: text})});
            const reader = res.body.getReader();
            let acc = '';
            const decoder = new TextDecoder();
            while(true){
              const {value, done} = await reader.read();
              if(done) break;
              const chunk = decoder.decode(value);
              acc += chunk;
              // incremental render
              if(acc){
                const msgs = document.getElementById('messages');
                const last = msgs.lastElementChild;
                if(last && last.classList.contains('assistant')){
                  msgs.removeChild(last);
                }
                addMsg('assistant', acc);
              }
            }
          } catch(e){
            addMsg('assistant', 'Stream error: '+ e);
          }
          // After streaming, call tool-enabled endpoint to apply edits and refresh JSON
          showToolCallIndicator('pending');
          const applyRes = await fetch('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: text})});
          const applyData = await applyRes.json();
          const status = applyData.tool_call_status || 'success';
          showToolCallIndicator(status);
          if(applyData.error){ addMsg('assistant', 'Edit error: '+applyData.error); }
          await refreshJSON();
        } else {
          showToolCallIndicator('pending');
          const res = await fetch('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: text})});
          const data = await res.json();
          const status = data.tool_call_status || 'success';
          showToolCallIndicator(status);
          if(data.assistant_message){ addMsg('assistant', data.assistant_message); }
          if(data.error){ addMsg('assistant', 'Error: '+data.error); }
          await refreshJSON();
        }
      }
      function addMsg(role, text){
        const el = document.createElement('div');
        el.className = 'bubble '+role;
        el.textContent = (role === 'user' ? 'You: ' : 'Assistant: ') + text;
        document.getElementById('messages').appendChild(el);
        el.scrollIntoView({behavior: 'smooth', block: 'end'});
      }
      document.getElementById('send').addEventListener('click', send);
      document.getElementById('text').addEventListener('keydown', (e)=>{ if(e.key==='Enter' && (e.metaKey||e.ctrlKey)){ send(); }});
      // session id management in localStorage
      const SID_KEY = 'cap_table_session_id';
      function getSessionId(){
        let sid = localStorage.getItem(SID_KEY);
        if(!sid){ sid = 's_' + Math.random().toString(36).slice(2); localStorage.setItem(SID_KEY, sid); }
        return sid;
      }
      // Patch fetch calls to include session_id
      const _origFetch = window.fetch;
      window.fetch = function(url, options){
        if(options && options.body && typeof options.body === 'string' && (url.endsWith('/api/chat') || url.endsWith('/api/chat/stream'))){
          try{
            const obj = JSON.parse(options.body);
            obj.session_id = getSessionId();
            options.body = JSON.stringify(obj);
          }catch(_){/* noop */}
        }
        return _origFetch(url, options);
      }
      refreshJSON();
    </script>
  </body>
</html>
        """
    )


@app.get("/api/cap-table")
def get_cap_table() -> JSONResponse:
    return JSONResponse(STATE)


@app.put("/api/cap-table")
def put_cap_table(payload: Dict[str, Any]) -> JSONResponse:
    _validate_or_422(payload)
    STATE.clear()
    STATE.update(payload)
    return JSONResponse({"ok": True})


def apply_edit(mode: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if mode not in ("replace", "merge"):
        raise HTTPException(
            status_code=400, detail="Invalid mode; expected 'replace' or 'merge'")

    if mode == "replace":
        candidate = payload
    else:
        candidate = {**STATE, **payload}

    _validate_or_422(candidate)
    return candidate


def openai_client() -> Optional[Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = (
    "Role: You edit cap table JSON precisely and safely.\n"
    "Policy:\n"
    "- Always use the edit_cap_table tool for changes; avoid free-form JSON in messages.\n"
    "- Follow the provided schema digest exactly; unknown fields will be rejected.\n"
    "- Percentages are decimals in [0,1] (e.g., 0.20). Dates are YYYY-MM-DD.\n"
    "Conversation Memory:\n"
    "- CRITICAL: Review the ENTIRE conversation history (all previous messages) before responding.\n"
    "- Extract and remember ALL details mentioned in previous messages:\n"
    "  * Names: holder names, class names (Common, Preferred, etc.)\n"
    "  * Dates: Parse dates from various formats:\n"
    "    - '22th June 2023' or '22nd june 2023' = '2023-06-22'\n"
    "    - '28th September 2024' = '2024-09-28'\n"
    "    - Convert all dates to YYYY-MM-DD format\n"
    "  * Amounts: Share quantities (5M = 5000000), investment amounts (250k = 250000), valuations\n"
    "  * Round details: Round names, calculation types, investment amounts per holder\n"
    "  * Clarifications: Class names, quantities, dates, etc.\n"
    "- NEVER ask for information that was already provided in previous messages.\n"
    "- If the user mentions something multiple times, use the MOST RECENT information.\n"
    "- If user says 'each' or 'each invest X', apply that amount to ALL mentioned holders.\n"
    "- Build up information progressively: combine details from multiple messages.\n"
    "- Example: If user says 'alice and bob each get 5M shares' and later says 'common class', use both pieces of info.\n"
    "Behavior:\n"
    "- Make minimal valid edits; when uncertain, request the smallest safe change.\n"
    "- Keep explanations concise; prefer action via tools.\n"
    "- If the user includes multiple requests (e.g., incorporation round AND an investment round), handle all of them in order.\n"
    "- DO NOT ask users to confirm or verify changes. Apply edits directly via the tool.\n"
    "- DO NOT describe what you will do; just do it using the tool.\n"
    "- If you need clarification, ask questions, but ONLY for information NOT mentioned in the conversation history.\n"
    "- When you have enough information from the conversation to proceed, DO IT immediately without asking for confirmation.\n"
    "Missing Data Protocol:\n"
    "- If a user request is missing required fields (e.g., round_date, investment_amount, holder names), "
    "DO NOT guess or invent values. Instead, ask the user to provide the missing information.\n"
    "- However, if information was provided in EARLIER messages in this conversation, use that information.\n"
    "- If a request is ambiguous (e.g., 'add a round' without specifying type or details), ask clarifying questions.\n"
    "- Before applying any edit, verify you have all required fields per the schema. If not, check conversation history first.\n"
    "- Only use the tool when you have complete, valid data. Never fill in missing fields with placeholders or defaults.\n"
    "- When using the tool, the 'payload' must contain actual JSON data to merge/replace, never empty objects.\n"
)


@app.post("/api/chat")
def chat(req: ChatRequest) -> JSONResponse:
    global STATE

    # Optional: client-side full replace (power user)
    if req.replace_json is not None:
        STATE = apply_edit("replace", req.replace_json)
        # record assistant confirmation in history
        sid = _get_session_id(req)
        _append_history(sid, "user", "(uploaded full JSON)")
        _append_history(sid, "assistant", "Replaced cap table JSON.")
        return JSONResponse({"assistant_message": "Replaced cap table JSON.", "tool_call_status": "success"})

    client = openai_client()
    sid = _get_session_id(req)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "edit_cap_table",
                "description": "Apply an edit to the cap table JSON. Use 'merge' for small changes or 'replace' for full updates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "enum": ["replace", "merge"]},
                        "payload": {"type": "object"}
                    },
                    "required": ["mode", "payload"],
                    "additionalProperties": False
                }
            }
        }
    ]

    # Compose messages with history
    messages = _build_messages(sid, STATE, req.message)

    # server-side logging preview
    _log_preview("/api/chat prepared", sid, messages, tools)

    # Dry-run mode via request flag or env LLM_DRY_RUN=1
    if req.dry_run or os.getenv("LLM_DRY_RUN") == "1":
        # persist history even in dry-run
        _append_history(sid, "user", req.message)
        _append_history(sid, "assistant", "(Dry-run) Skipped calling OpenAI.")
        return JSONResponse({
            "dry_run": True,
            "assistant_message": "(Dry-run) Skipped calling OpenAI.",
            "preview": {
                "messages": messages,
                "tools": tools
            },
            "json": STATE,
            "tool_call_status": "skipped"
        })

    if client is None:
        # Offline/dev fallback: echo and persist history
        _append_history(sid, "user", req.message)
        _append_history(sid, "assistant", "(Dev mode) I received your message and can edit JSON when OPENAI_API_KEY is set.")
        return JSONResponse({
            "assistant_message": "(Dev mode) I received your message and can edit JSON when OPENAI_API_KEY is set.",
            "json": STATE,
            "tool_call_status": "dev_mode"
        })

    # Call OpenAI with tool support and retry logic
    max_retries = 2
    retry_count = 0
    tool_call_status = "pending"
    tool_choice_param = "auto"  # Default to auto, can be changed to "required" for retries
    pending_retry = False  # Track if we're waiting for a retry after errors
    
    while retry_count <= max_retries:
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice_param
            )
        except Exception as e:  # pragma: no cover
            logger.error("OpenAI error sid=%s err=%s", sid, e)
            return JSONResponse({"error": f"OpenAI error: {e}", "tool_call_status": "error"}, status_code=500)

        assistant_message = None
        tool_calls = []
        has_error = False  # Reset for this iteration

        choice = resp.choices[0]
        if choice.message.content:
            assistant_message = choice.message.content
        if choice.message.tool_calls:
            tool_calls = choice.message.tool_calls
            logger.info("Received %d tool call(s) sid=%s attempt=%d", len(tool_calls), sid, retry_count + 1)
            pending_retry = False  # Clear pending retry flag if we got tool calls

        # Process all tool calls sequentially
        if tool_calls:
            if len(tool_calls) > 1:
                logger.info("Multiple tool calls received, processing all %d tool calls sid=%s", len(tool_calls), sid)
            
            # Process each tool call sequentially
            all_tool_responses = []
            tool_calls_to_add = []
            has_error = False
            
            for tc_idx, tc in enumerate(tool_calls):
                logger.info("Processing tool call %d/%d: name=%s sid=%s", tc_idx + 1, len(tool_calls), tc.function.name, sid)
                
                # Log full tool call parameters
                args_raw = tc.function.arguments or {}
                if isinstance(args_raw, str):
                    logger.info("Tool call parameters sid=%s name=%s args_raw=%s", 
                                sid, tc.function.name, args_raw)
                else:
                    logger.info("Tool call parameters sid=%s name=%s args_raw=%s", 
                                sid, tc.function.name, json.dumps(args_raw, indent=2))
                
                if tc.function.name == "edit_cap_table":
                    # OpenAI may return arguments as a JSON string
                    if isinstance(args_raw, str):
                        try:
                            args = json.loads(args_raw)
                            logger.info("Parsed tool call arguments sid=%s args=%s", sid, json.dumps(args, indent=2))
                        except Exception:
                            logger.error(
                                "Invalid tool args sid=%s args_raw=%s", sid, args_raw)
                            tool_call_status = "error"
                            has_error = True
                            # Collect tool response with error
                            tool_calls_to_add.append({
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": args_raw}
                            })
                            all_tool_responses.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps({"error": "Invalid tool arguments format - JSON parsing failed"})
                            })
                            continue  # Process next tool call
                    elif isinstance(args_raw, dict):
                        args = args_raw
                        logger.info("Tool call arguments sid=%s args=%s", sid, json.dumps(args, indent=2))
                    else:
                        tool_call_status = "error"
                        has_error = True
                        # Collect tool response with error
                        tool_calls_to_add.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": str(args_raw)}
                        })
                        all_tool_responses.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"error": "Unsupported tool arguments type"})
                        })
                        continue  # Process next tool call

                    mode = args.get("mode")
                    payload = args.get("payload") or {}
                    if not mode:
                        logger.error("Tool call missing 'mode' sid=%s args=%s", sid, json.dumps(args, indent=2))
                        tool_call_status = "error"
                        has_error = True
                        # Collect tool response with error
                        tool_calls_to_add.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": json.dumps(args)}
                        })
                        all_tool_responses.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"error": "Tool call missing required 'mode' field. Must be 'replace' or 'merge'."})
                        })
                        continue  # Process next tool call
                        
                    if not payload or payload == {}:
                        logger.warning("Tool call has empty payload sid=%s - rejecting", sid)
                        tool_call_status = "error"
                        has_error = True
                        # Collect tool response with error
                        tool_calls_to_add.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": json.dumps(args)}
                        })
                        all_tool_responses.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"error": "The tool call payload is empty. Please provide actual JSON data to edit. Do not call the tool with empty payloads."})
                        })
                        continue  # Process next tool call
                        
                    # Log full payload without truncation
                    logger.info("Applying edit sid=%s mode=%s payload=%s",
                                sid, mode, json.dumps(payload, indent=2))
                    try:
                        STATE = apply_edit(mode, payload)
                        logger.info("Edit applied successfully for tool call %d/%d sid=%s mode=%s", 
                                  tc_idx + 1, len(tool_calls), sid, mode)
                        # Collect tool call and response for batch processing
                        tool_calls_to_add.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": json.dumps(args)}
                        })
                        all_tool_responses.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"success": True, "message": "Edit applied successfully"})
                        })
                        logger.info("Tool call %d/%d succeeded sid=%s", tc_idx + 1, len(tool_calls), sid)
                        # Continue to next tool call - STATE has been updated
                    except HTTPException as he:
                        logger.warning(
                            "Validation failed for tool call %d/%d sid=%s errors=%s attempt=%d", 
                            tc_idx + 1, len(tool_calls), sid, he.detail, retry_count + 1)
                        tool_call_status = "validation_error"
                        has_error = True
                        # Format validation errors for LLM
                        error_detail = he.detail
                        if isinstance(error_detail, dict):
                            # Extract error messages from the dict format
                            error_msgs = []
                            for key, value in error_detail.items():
                                if isinstance(value, list):
                                    error_msgs.extend([f"{key}: {e}" for e in value])
                                elif isinstance(value, str):
                                    error_msgs.append(f"{key}: {value}")
                                else:
                                    error_msgs.append(f"{key}: {value}")
                            error_msg = "Validation errors:\n" + "\n".join(f"- {e}" for e in error_msgs)
                        else:
                            error_msg = str(error_detail)
                        
                        # Collect tool call and error response for batch processing
                        tool_calls_to_add.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": json.dumps(args)}
                        })
                        all_tool_responses.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({
                                "error": "Validation failed",
                                "details": error_msg,
                                "payload": payload,
                                "suggestion": "Please fix the validation errors and try again. Check the schema requirements, business rules, relationship integrity, and FEO structure carefully. You MUST retry the tool call with the corrected payload."
                            })
                        })
                        # Continue processing other tool calls, but mark for retry
                        continue
                else:
                    logger.warning("Unknown tool call name: %s sid=%s args=%s", 
                                 tc.function.name, sid, 
                                 args_raw if isinstance(args_raw, str) else json.dumps(args_raw, indent=2))
                    tool_call_status = "error"
                    has_error = True
                    if not assistant_message:
                        assistant_message = f"Received unknown tool call: {tc.function.name}"
                    # Collect tool call and error response
                    tool_calls_to_add.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": json.dumps(args_raw) if isinstance(args_raw, dict) else str(args_raw)}
                    })
                    all_tool_responses.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": f"Unknown tool call: {tc.function.name}. Only 'edit_cap_table' is supported."})
                    })
                    continue
            
            # After processing all tool calls, add them to messages and handle retries
            if tool_calls_to_add:
                messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                    "tool_calls": tool_calls_to_add
                })
                messages.extend(all_tool_responses)
                
                # If there were errors, retry if we have retries left
                if has_error and retry_count < max_retries:
                    retry_count += 1
                    pending_retry = True
                    logger.info("Retrying after processing %d tool calls with errors sid=%s attempt=%d", 
                              len(tool_calls), sid, retry_count + 1)
                    # Add a system message to encourage retrying the tool call
                    messages.append({
                        "role": "system",
                        "content": "IMPORTANT: You received validation errors. You MUST fix the errors and retry the tool call(s) with corrected payloads. Do not just respond with text - call the tool again with the fixes."
                    })
                    # Force tool choice when retrying after validation errors
                    tool_choice_param = "required"  # Force tool call on retry
                    continue
                elif not has_error:
                    # All tool calls succeeded
                    tool_call_status = "success"
                    if not assistant_message:
                        assistant_message = f"Applied {len(tool_calls)} edit(s) successfully."
                    # Get final assistant response after all successful tool calls
                    try:
                        final_resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            tools=tools
                        )
                        final_choice = final_resp.choices[0]
                        if final_choice.message.content:
                            assistant_message = final_choice.message.content
                    except Exception as e:
                        logger.warning("Failed to get final response after tool success sid=%s err=%s", sid, e)
                    break  # Success, exit retry loop
                else:
                    # Errors and out of retries - return error
                    if has_error:
                        _append_history(sid, "user", req.message)
                        error_msg = "Some tool calls failed validation. Check errors above."
                        _append_history(sid, "assistant", assistant_message or error_msg)
                        return JSONResponse({
                            "assistant_message": assistant_message or error_msg,
                            "error": "Some tool calls failed",
                            "json": STATE,
                            "tool_call_status": "validation_error"
                        }, status_code=422)
                    break
        else:
            # No tool calls returned
            if pending_retry or (retry_count > 0 and tool_call_status == "validation_error"):
                # We were retrying but LLM didn't call tools - this is a problem
                logger.warning("Retry attempt %d: LLM returned no tool calls after validation errors sid=%s", 
                             retry_count, sid)
                # Add a system message to force retry
                messages.append({
                    "role": "system",
                    "content": "CRITICAL: You must retry the tool call(s) that failed validation. The previous tool calls had errors that need to be fixed. Call edit_cap_table again with corrected payloads. Do not just respond with text."
                })
                # Force tool call
                tool_choice_param = "required"
                retry_count += 1
                pending_retry = True
                if retry_count <= max_retries:
                    continue
                else:
                    # Out of retries
                    _append_history(sid, "user", req.message)
                    error_msg = "Validation errors occurred but could not be automatically fixed. Please check the errors and try again."
                    _append_history(sid, "assistant", assistant_message or error_msg)
                    return JSONResponse({
                        "assistant_message": assistant_message or error_msg,
                        "error": "Tool calls failed validation and LLM did not retry",
                        "json": STATE,
                        "tool_call_status": "validation_error"
                    }, status_code=422)
            else:
                # No tool calls and not retrying - normal case
                tool_call_status = "no_tool_calls"
                break

    # Get final assistant message if we did retries but didn't succeed (for error cases)
    if tool_calls and retry_count > 0 and tool_call_status != "success":
        try:
            final_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools
            )
            final_choice = final_resp.choices[0]
            if final_choice.message.content:
                assistant_message = final_choice.message.content
        except Exception as e:
            logger.warning("Failed to get final response after retries sid=%s err=%s", sid, e)

    # save turn in history
    _append_history(sid, "user", req.message)
    _append_history(sid, "assistant", assistant_message or "(No change)")

    logger.info("/api/chat done sid=%s msg_len=%d applied=%s status=%s", sid,
                len(assistant_message or ""), bool(tool_calls), tool_call_status)
    return JSONResponse({
        "assistant_message": assistant_message or "(No change)", 
        "json": STATE,
        "tool_call_status": tool_call_status
    })


# Streamed responses endpoint (assistant text only; edits applied afterwards by client via /api/chat)
@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    client = openai_client()

    async def _gen():  # type: ignore
        # Dev/offline mode: stream a simple echo
        if client is None:
            msg = "(Dev mode) Streaming is unavailable without OPENAI_API_KEY.\n"
            yield msg
            return

        # Stream content (no tools during streaming)
        sid = _get_session_id(req)
        messages = _build_messages(sid, STATE, req.message)

        # Dry-run: stream exactly what would be sent (and persist history)
        if req.dry_run or os.getenv("LLM_DRY_RUN") == "1":
            logger.info("/api/chat/stream dry-run sid=%s", sid)
            yield "(Dry-run stream) Messages that would be sent to OpenAI:\n\n"
            for m in messages:
                yield f"[{m['role']}] {m['content']}\n\n"
            _append_history(sid, "user", req.message)
            _append_history(sid, "assistant", "(Dry-run stream) Previewed prompt")
            return

        try:
            logger.info("/api/chat/stream start sid=%s", sid)
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True
            )
            acc = ""
            for event in stream:
                delta = getattr(event.choices[0].delta, "content", None)
                if delta:
                    acc += delta
                    yield delta
            # After streaming concludes, append to history
            _append_history(sid, "user", req.message)
            _append_history(sid, "assistant", acc or "")
            logger.info("/api/chat/stream done sid=%s chars=%d", sid, len(acc))
        except Exception as e:  # pragma: no cover
            logger.error("/api/chat/stream error sid=%s err=%s", sid, e)
            yield f"\n[Stream error: {e}]\n"

    return StreamingResponse(_gen(), media_type="text/plain")
