## Integrating OpenAI for Cap Table JSON Editing

This guide explains how to integrate the OpenAI API to enable a chat interface where users can ask an LLM to inspect and edit the cap table JSON with schema validation.

### Objectives
- Provide a web UI chat for editing cap table JSON via natural language
- Validate, apply, and display JSON edits safely using the canonical schema
- Leverage tool/function calling so the model proposes structured edits

### Architecture Overview
- Backend: FastAPI server exposing endpoints:
  - `POST /api/chat`: sends user message + current JSON to OpenAI; applies tool calls from the model to update JSON; returns assistant text and updated JSON
  - `GET /api/cap-table`: returns current JSON
  - `PUT /api/cap-table`: replaces current JSON (guarded by validation)
- LLM integration:
  - Provide one key tool/function: `edit_cap_table(data_edit)` where `data_edit` contains minimal JSON changes (full replace or partial merge)
  - On successful tool call, validate the updated JSON against `src/captable/schemas/cap_table_schema.json`; reject with error on validation failure
- Frontend: Minimal single-page chat UI (HTML/JS) that:
  - Displays messages
  - Shows the current cap table JSON alongside
  - Posts chat turns to `/api/chat` and renders updates

### Tool (Function) Design for the LLM
- Name: `edit_cap_table`
- Purpose: Apply JSON edits to the in-memory cap table
- Input schema (Pydantic):
  - `mode`: `replace` | `merge`
  - `payload`: object (for `replace`, the full JSON; for `merge`, a partial fragment)
- Behavior:
  - For `replace`: validate `payload` and replace state
  - For `merge`: shallow merge at object paths specified (simple dict update); validate result
  - Return: success flag and validation errors (if any)

### Model Prompting
- System prompt: instruct the model to:
  - Keep responses concise and explain reasoning briefly
  - Use the `edit_cap_table` tool to make changes, not just describe them
  - Adhere strictly to the schema (percentages as decimals, dates as `YYYY-MM-DD`)
  - Avoid introducing unspecified fields (the server will reject extras)

### Error Handling & Validation
- All edits must pass `jsonschema.Draft201909Validator` against the canonical schema
- If validation fails, return errors to the frontend; the chat should show a concise explanation and keep current JSON unchanged

### Environment & Setup
- Add dependencies to `requirements.txt`: `fastapi`, `uvicorn`, `openai`, `pydantic`
- Configure `OPENAI_API_KEY` in environment
- Run server: `uvicorn server.main:app --reload`

### Security Notes
- Do not store the OpenAI API key in client code
- Apply rate limiting and auth if hosting publicly

### Future Enhancements
- Add streaming responses
- Add websocket for live token streaming
- Support richer tool set (e.g., suggest calculations, generate `FormulaEncodingObject` with examples)
- Add unit tests for edit tool validation


