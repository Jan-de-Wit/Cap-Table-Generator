# Cap Table Generator - API Reference

## Overview

The Cap Table Generator API provides endpoints for LLM-driven cap table creation, editing, and export. This document describes all available endpoints.

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently no authentication required for development.

## Endpoints

### Root Endpoint

#### GET /
Get API information and version.

**Response:**
```json
{
  "name": "Cap Table Generator API",
  "version": "1.0.0",
  "provider": "openai",
  "model": "gpt-4"
}
```

### Configuration

#### GET /api/config
Get current LLM configuration (read-only).

**Response:**
```json
{
  "provider": "openai",
  "model": "gpt-4"
}
```

### Chat & LLM

#### POST /api/chat
Chat endpoint with streaming LLM responses. Uses Server-Sent Events (SSE).

**Request:**
```json
{
  "message": "Create a cap table for Acme Corp",
  "conversation_id": "uuid-optional",
  "execution_mode": "auto|approval",
  "approved_tool_call_ids": [],
  "messages": [] // optional - full message history
}
```

**Response:** SSE stream with events:
- `conversation_id` - Conversation ID
- `content` - Streaming text chunks
- `tool_call` - Tool call requests
- `tool_result` - Tool execution results
- `cap_table_update` - Final cap table state
- `error` - Error messages

### Cap Table Operations

#### GET /api/cap-table
Get current cap table state with computed metrics.

**Response:**
```json
{
  "capTable": {
    "schema_version": "1.0",
    "company": {...},
    "holders": [...],
    "classes": [...],
    "instruments": [...]
  },
  "metrics": {
    "totals": {...},
    "ownership": [...],
    "pool": {...}
  }
}
```

#### GET /api/cap-table/download?format=json
Download cap table as JSON file.

**Query Parameters:**
- `format`: `json` (default) or `excel`

#### GET /api/cap-table/excel
Export cap table as Excel workbook.

**Response:** Excel file download

#### DELETE /api/cap-table/reset
Reset cap table to initial empty state.

### Tools & Execution

#### POST /api/tool/cap_table_editor
Execute a cap table editing tool operation directly.

**Request:**
```json
{
  "operation": "replace|append|upsert|delete|bulkPatch",
  "path": "/holders",
  "value": {...},
  "patch": [...] // for bulkPatch
}
```

**Response:**
```json
{
  "success": true,
  "cap_table": {...},
  "diff": [...],
  "metrics": {...}
}
```

#### POST /api/tool/approve
Approve pending tool calls for execution.

**Request:**
```json
{
  "tool_call_ids": ["id1", "id2"]
}
```

#### GET /api/tool/pending
Get all pending tool calls awaiting approval.

### Conversation Management

#### POST /api/conversation
Create a new conversation.

**Response:**
```json
{
  "conversation_id": "uuid"
}
```

#### GET /api/conversation/{conversation_id}
Get conversation details and message history.

#### DELETE /api/conversation/{conversation_id}
Delete a conversation.

#### POST /api/conversation/cleanup
Remove expired conversations.

#### GET /api/conversation/stats
Get conversation store statistics.

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message",
  "details": "Additional context"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad request
- `404` - Not found
- `500` - Server error

## Examples

### Creating a Cap Table

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a cap table for Acme Corp with 10M authorized shares",
    "execution_mode": "auto"
  }'
```

### Updating a Holder

```bash
curl -X POST http://localhost:8000/api/tool/cap_table_editor \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "append",
    "path": "/holders",
    "value": {
      "name": "John Doe",
      "type": "individual",
      "id": "holder-123"
    }
  }'
```

### Exporting Excel

```bash
curl http://localhost:8000/api/cap-table/excel \
  -o cap_table.xlsx
```

## WebSocket/SSE

The `/api/chat` endpoint uses Server-Sent Events (SSE) for streaming responses. Use an SSE client or EventSource API:

```javascript
const eventSource = new EventSource('/api/chat');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

