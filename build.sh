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

# Install local captable package from project root
echo "📦 Installing local captable package..."
cd "$PROJECT_ROOT"
$PYTHON_CMD -m pip install . --quiet --user --no-deps
echo "✅ Captable package installed"

# Verify Python dependencies are installed
echo "✅ Verifying Python dependencies..."
$PYTHON_CMD -c "import xlsxwriter; import jsonschema; print('✓ Python packages verified')" || {
    echo "❌ Failed to import Python packages"
    exit 1
}

# Verify captable package is installed
echo "✅ Verifying captable package..."
$PYTHON_CMD -c "from captable import generate_from_data; print('✓ Captable package verified')" || {
    echo "⚠️  Warning: captable package import failed, but continuing build"
}

# Set PYTHON_CMD as environment variable for runtime
export PYTHON_CMD

# Install Node.js dependencies and build Next.js
echo "📦 Installing Node.js dependencies..."
cd "$WEBAPP_DIR"
npm install

echo "🔨 Building Next.js application..."
npm run build

echo "✅ Build completed successfully!"

