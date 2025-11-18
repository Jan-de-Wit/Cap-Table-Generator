# Cap Table Generator

A tool for generating capitalization tables from JSON data, with both a FastAPI backend and Next.js frontend.

## Features

- **Round-based Cap Table Generation**: Support for multiple financing rounds with different calculation types
- **Excel Export**: Generate comprehensive Excel workbooks with formulas and calculations
- **JSON Schema Validation**: Validates cap table data against a comprehensive schema
- **FastAPI Backend**: RESTful API for generating Excel files from JSON
- **Next.js Frontend**: Modern web interface for building cap tables

## Project Structure

```
.
├── app.py                 # FastAPI application
├── src/captable/          # Core cap table generation logic
├── webapp/                # Next.js frontend application
├── scripts/               # Utility scripts
└── examples/              # Example JSON files
```

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- pip

### Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Install frontend dependencies:
   ```bash
   cd webapp
   npm install
   ```

## Running the FastAPI Server

The FastAPI server provides the backend API for generating Excel files.

### Development Mode

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Endpoints

- `POST /generate-excel` - Generate Excel from JSON (with Pydantic validation)
- `POST /generate-excel-raw` - Generate Excel from JSON (raw dict format, more flexible)
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Example Request

```bash
curl -X POST "http://localhost:8000/generate-excel-raw" \
  -H "Content-Type: application/json" \
  -d @examples/chatgpt.json \
  --output cap-table.xlsx
```

## Running the Frontend

See [webapp/README.md](webapp/README.md) for frontend setup instructions.

The frontend expects the FastAPI server to be running at `http://localhost:8000` by default, or you can set the `NEXT_PUBLIC_FASTAPI_URL` environment variable to point to a different URL.

## Usage

### Using the API Directly

1. Prepare your cap table data in JSON format (see `examples/` for examples)
2. Send a POST request to `/generate-excel-raw` with the JSON data
3. The API will return an Excel file

### Using the Web Interface

1. Start the FastAPI server: `python app.py`
2. Start the Next.js frontend: `cd webapp && npm run dev`
3. Open `http://localhost:3000` in your browser
4. Build your cap table using the web interface
5. Click "Download Excel" to generate and download the Excel file

## Development

### Running Tests

```bash
# Run example generation
python run_example.py
```

### Project Structure

- `src/captable/` - Core Python package
  - `generator.py` - Main orchestrator
  - `excel/` - Excel generation logic
  - `validation/` - Schema and business rule validation
  - `formulas/` - Calculation formulas
- `app.py` - FastAPI application
- `webapp/` - Next.js frontend

## License

[Add your license here]

