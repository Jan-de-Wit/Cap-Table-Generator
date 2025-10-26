# Development Setup Guide

## Prerequisites

- Python 3.9 or higher
- Node.js 16+ and npm (for frontend)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Cap Table Generator (OCX)"
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Install Development Dependencies

```bash
pip install -r tests/requirements-test.txt
```

### 3. Frontend Setup

```bash
cd webapp/frontend
npm install
```

### 4. Configuration

Create `.env` file in project root:

```env
OPENAI_API_KEY=your_key_here
OPENAI_PROVIDER=openai
OPENAI_MODEL=gpt-4
CORS_ORIGINS=http://localhost:5173
PORT=8000
```

### 5. Run the Application

#### Start Backend

```bash
# From project root
python -m webapp.backend.main

# Or use uvicorn directly
uvicorn webapp.backend.main:app --reload
```

#### Start Frontend

```bash
# From webapp/frontend
npm run dev
```

Access the application at `http://localhost:5173`

## Development Tools

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov=webapp

# Specific test file
pytest tests/test_cap_table.py -v
```

### Type Checking

```bash
# Check types
mypy src/ webapp/backend/

# Strict mode
mypy --strict src/ webapp/backend/
```

### Code Formatting

```bash
# Format code
black src/ webapp/backend/

# Sort imports
isort src/ webapp/backend/

# Lint
pylint src/ webapp/backend/
```

## Project Structure

```
Cap Table Generator (OCX)/
├── src/captable/         # Core library
│   ├── excel/            # Excel generation
│   ├── formulas/         # Formula resolution
│   └── validation/       # Validation system
├── webapp/
│   ├── backend/          # FastAPI backend
│   │   ├── services/     # Business logic
│   │   ├── routers/      # API routes
│   │   └── main.py       # FastAPI app
│   └── frontend/         # React frontend
├── tests/                # Test suite
├── docs/                 # Documentation
│   ├── guides/           # Developer guides
│   ├── architecture/     # Architecture docs
│   └── api/              # API reference
└── requirements.txt      # Dependencies
```

## Testing

See `docs/guides/TESTING_GUIDE.md` for detailed testing instructions.

## Contributing

See `docs/guides/CONTRIBUTING.md` for contribution guidelines.

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Frontend build errors:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```

**Port already in use:**
```bash
# Change port in .env or kill process
lsof -ti:8000 | xargs kill
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier

Settings file: `.vscode/settings.json`

### PyCharm

1. Configure Python interpreter to `.venv`
2. Mark directories as source roots
3. Configure pytest as test runner

