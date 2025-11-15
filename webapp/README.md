# Cap Table Generator Web App

A Next.js web application for generating capitalization tables with round-based instruments.

## Features

- **Round-based Form**: Add multiple financing rounds with different calculation types
- **Dynamic Holder Management**: Holders are automatically inferred from instruments, with the ability to create new ones on the fly
- **Multiple Instrument Types**: Support for fixed shares, target percentage, valuation-based, convertible, and SAFE instruments
- **Pro-Rata Allocations**: Separate section for managing pro-rata allocations per round
- **JSON Preview**: Preview the generated JSON before downloading
- **Excel Generation**: Download the cap table as an Excel file

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.x
- Python dependencies installed (from project root):
  ```bash
  pip install -r requirements.txt
  ```

### Installation

1. Install Node.js dependencies:
   ```bash
   cd webapp
   npm install
   ```

2. Make sure Python dependencies are installed from the project root:
   ```bash
   cd ..
   pip install -r requirements.txt
   ```

### Running the Development Server

From the `webapp` directory:

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

### Building for Production

```bash
npm run build
npm start
```

## Usage

1. **Add Rounds**: Click "Add Round" to create a new financing round
2. **Configure Round**: Fill in round parameters (name, date, calculation type, etc.)
3. **Add Instruments**: 
   - Go to "Round Instruments" tab to add instruments for this round
   - Go to "Pro-Rata Allocations" tab to add pro-rata allocations
4. **Manage Holders**: When adding instruments, you can select existing holders or create new ones
5. **Preview & Download**: Once all rounds are complete, click "Preview & Download" to see the JSON and generate Excel

## Project Structure

- `app/page.tsx` - Main page component
- `app/api/generate-excel/route.ts` - API route for Excel generation
- `components/round-form.tsx` - Round form component
- `components/holder-selector.tsx` - Holder selector/creator component
- `components/json-preview.tsx` - JSON preview component
- `types/cap-table.ts` - TypeScript type definitions

## API

The `/api/generate-excel` endpoint accepts a POST request with the cap table JSON data and returns an Excel file.
