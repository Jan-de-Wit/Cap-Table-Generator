# Quick Start Guide

This guide will get the Cap Table Web App running in minutes.

## Step 1: Backend Setup

Open a terminal and run:

```bash
cd webapp/backend

# Install dependencies
pip install -r requirements.txt

# Create .env file (or copy from .env.example)
cat > .env << 'EOF'
ACTIVE_PROVIDER=openai
ACTIVE_MODEL=gpt-4
OPENAI_API_KEY=your_api_key_here
CORS_ORIGINS=http://localhost:5173
PORT=8000
EOF

# Edit .env and add your actual API key
nano .env  # or use your preferred editor

# Start the server
python -m uvicorn main:app --reload --port 8000
```

**Backend should now be running at http://localhost:8000**

## Step 2: Frontend Setup

Open a **new terminal** and run:

```bash
cd webapp/frontend

# Install dependencies
npm install --legacy-peer-deps

# Start development server
npm run dev
```

**Frontend should now be running at http://localhost:5173**

## Step 3: Open the App

Visit http://localhost:5173 in your browser.

## Example Conversation

Try these prompts to create your first cap table:

1. "Create a cap table for TechCo Inc"
2. "Add two founders: Alice with 5M shares and Bob with 5M shares"
3. "Add a common stock class"
4. "Add a Series A round for $5M investment at $20M pre-money valuation"
5. "Export to Excel"

## Troubleshooting

### Backend won't start

**Error: "No API key found"**
- Make sure you've added your API key to `.env`
- For OpenAI: OPENAI_API_KEY

**Error: "Module not found"**
- Make sure you ran `pip install -r requirements.txt`
- Try installing in a virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

### Frontend won't start

**Error: Dependency issues**
- Use `npm install --legacy-peer-deps` instead of `npm install`

**Error: "VITE_API_URL not defined"**
- The frontend defaults to http://localhost:8000
- If your backend runs on a different port, create a `.env` file:
  ```bash
  echo "VITE_API_URL=http://localhost:YOUR_PORT" > .env
  ```

### Can't connect to backend

**Error in browser console: "Network error"**
- Make sure backend is running on http://localhost:8000
- Check CORS_ORIGINS in backend `.env` includes frontend URL
- Try restarting both servers

## Next Steps

- See `webapp/README.md` for detailed documentation
- See `README.md` in project root for schema documentation
- Explore example cap tables in `examples/` directory
- Run tests: `cd webapp/backend && pytest tests/ -v`

