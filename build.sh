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

# Install Python dependencies
echo "📦 Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip --quiet
$PYTHON_CMD -m pip install -r requirements.txt --quiet --user

# Verify Python dependencies are installed
echo "✅ Verifying Python dependencies..."
$PYTHON_CMD -c "import xlsxwriter; import jsonschema; print('✓ Python packages verified')" || {
    echo "❌ Failed to import Python packages"
    exit 1
}

# Set PYTHON_CMD as environment variable for runtime
export PYTHON_CMD

# Install Node.js dependencies and build Next.js
echo "📦 Installing Node.js dependencies..."
cd webapp
npm install

echo "🔨 Building Next.js application..."
npm run build

echo "✅ Build completed successfully!"

