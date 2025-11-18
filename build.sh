#!/bin/bash
set -e

echo "🚀 Starting custom build process..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python3 not found, trying python..."
    if command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        echo "❌ Python is not available in the build environment"
        echo "   This may cause runtime errors. Python should be available on Vercel."
        exit 1
    fi
else
    PYTHON_CMD=python3
fi

echo "✅ Found Python: $(which $PYTHON_CMD)"
echo "   Python version: $($PYTHON_CMD --version)"

# Get Python version for site-packages path
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "   Detected Python version: $PYTHON_VERSION"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
WEBAPP_DIR="$PROJECT_ROOT/webapp"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip --quiet
$PYTHON_CMD -m pip install -r "$PROJECT_ROOT/requirements.txt" --quiet --user

# Verify Python dependencies are installed
echo "✅ Verifying Python dependencies..."
$PYTHON_CMD -c "import xlsxwriter; import jsonschema; print('✓ Python packages verified')" || {
    echo "❌ Failed to import Python packages"
    exit 1
}

# Set PYTHON_CMD as environment variable for runtime
export PYTHON_CMD

# Copy captable module to webapp/api for Vercel serverless function
echo "📦 Copying captable module to webapp/api..."
API_DIR="$WEBAPP_DIR/api"
CAPTABLE_SRC="$PROJECT_ROOT/src/captable"
CAPTABLE_DEST="$API_DIR/captable"

if [ -d "$CAPTABLE_SRC" ]; then
    # Create destination directories
    mkdir -p "$CAPTABLE_DEST/excel/sheet_generators"
    mkdir -p "$CAPTABLE_DEST/formulas"
    mkdir -p "$CAPTABLE_DEST/validation"
    mkdir -p "$CAPTABLE_DEST/schemas"
    
    # Copy Python files
    cp "$CAPTABLE_SRC"/*.py "$CAPTABLE_DEST/" 2>/dev/null || true
    cp "$CAPTABLE_SRC/excel"/*.py "$CAPTABLE_DEST/excel/" 2>/dev/null || true
    cp "$CAPTABLE_SRC/excel/sheet_generators"/*.py "$CAPTABLE_DEST/excel/sheet_generators/" 2>/dev/null || true
    cp "$CAPTABLE_SRC/formulas"/*.py "$CAPTABLE_DEST/formulas/" 2>/dev/null || true
    cp "$CAPTABLE_SRC/validation"/*.py "$CAPTABLE_DEST/validation/" 2>/dev/null || true
    
    # Copy schema files
    cp -r "$CAPTABLE_SRC/schemas"/* "$CAPTABLE_DEST/schemas/" 2>/dev/null || true
    
    echo "✅ Captable module copied to $CAPTABLE_DEST"
else
    echo "⚠️  Warning: captable source directory not found at $CAPTABLE_SRC"
    echo "   Serverless function may fail if captable module is not available"
fi

# Install Node.js dependencies and build Next.js
echo "📦 Installing Node.js dependencies..."
cd "$WEBAPP_DIR"
npm install

echo "🔨 Building Next.js application..."
npm run build

echo "✅ Build completed successfully!"

