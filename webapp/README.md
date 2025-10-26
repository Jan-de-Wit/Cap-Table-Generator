# Cap Table Web App

An interactive web application for creating and managing cap tables through natural language conversations with an LLM.

## Overview

The Cap Table Web App provides a chat-based interface where users can:
- Create cap tables by describing them in natural language
- Add or modify holders, security classes, instruments, and financing rounds
- See real-time preview of changes
- Export to JSON or Excel at any time
- View human-readable diffs of recent changes

### Architecture

**Backend**: FastAPI with streaming SSE support  
**Frontend**: React + TypeScript + Vite + TailwindCSS  
**LLM Provider**: OpenAI (configured server-side)  
**Validation**: JSON Schema validation against cap table schema

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- API key for your chosen LLM provider

### Backend Setup

```bash
cd webapp/backend

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
#   - ACTIVE_PROVIDER (openai)
#   - ACTIVE_MODEL (model name, e.g., gpt-4)
#   - OPENAI_API_KEY (your OpenAI API key)

# Start backend server
uvicorn main:app --reload --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd webapp/frontend

# Install dependencies
npm install

# (Optional) Configure API URL
cp .env.example .env
# Default: VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

## Features

### 1. Chat Interface

Natural language interaction with LLM:

**Example conversation:**
```
You: Create a cap table for TechCo with two founders