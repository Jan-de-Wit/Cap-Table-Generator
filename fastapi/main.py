"""
FastAPI application for generating Excel cap tables from JSON data.
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import captable module
# First try importing as installed package (for production/Vercel)
# Then fall back to adding src to path (for local development)
try:
    from captable import generate_from_data, CapTableGenerator
    from captable.config import get_settings
    from captable.services import CapTableService, ValidationService
    from captable.errors import CapTableError
    from captable.reporting import ValidationReportGenerator
except ImportError:
    # If not installed, add src directory to path
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Build list of possible paths to check
    # Priority: local copy first, then standard locations
    possible_src_paths = [
        # Same directory as main.py (highest priority)
        current_file.parent / "src",
        project_root / "src",  # Standard: project_root/src
        current_file.parent.parent / "src",  # Alternative parent
        Path("/var/task/src"),  # Vercel serverless function location
        Path("/var/task"),  # Vercel root - might have src here
        Path.cwd() / "src",  # Current working directory
    ]

    # Also check if captable is directly in any of these locations
    # Priority: local copy first
    possible_direct_paths = [
        # Directly in fastapi directory (highest priority)
        current_file.parent / "captable",
        Path("/var/task/captable"),  # Vercel root with direct captable
        Path("/var/task/src/captable"),  # Vercel src/captable
        project_root / "src" / "captable",  # Standard location
    ]

    found_path = None
    for src_path in possible_src_paths:
        logger.info(f"Checking {src_path} for captable module")
        if src_path.exists() and (src_path / "captable").exists():
            logger.info(f"Found captable module in {src_path}")
            sys.path.insert(0, str(src_path))
            found_path = src_path
            break

    # If not found in src paths, check direct paths
    if not found_path:
        for direct_path in possible_direct_paths:
            logger.info(f"Checking direct path {direct_path}")
            if direct_path.exists() and direct_path.is_dir():
                parent_path = direct_path.parent
                logger.info(
                    f"Found captable module at {direct_path}, adding {parent_path} to path")
                sys.path.insert(0, str(parent_path))
                found_path = parent_path
                break

    # Try importing again
    try:
        from captable import generate_from_data, CapTableGenerator
        # Try importing new modules
        try:
            from captable.config import get_settings
            from captable.services import CapTableService, ValidationService
            from captable.errors import CapTableError
            from captable.reporting import ValidationReportGenerator
            NEW_MODULES_AVAILABLE = True
        except ImportError:
            NEW_MODULES_AVAILABLE = False
        logger.info(
            f"Successfully imported captable module (new modules: {NEW_MODULES_AVAILABLE})")
    except ImportError as e:
        error_msg = f"ERROR: Could not import captable module"
        print(error_msg, file=sys.stderr)
        print(f"Python path: {sys.path}", file=sys.stderr)
        logger.error(f"Project root: {project_root}")
        logger.error(f"Current file: {current_file}")
        logger.error(f"Checked src paths: {possible_src_paths}")
        logger.error(f"Checked direct paths: {possible_direct_paths}")
        logger.error(f"Import error: {e}")
        raise ImportError(
            f"Could not import captable. Make sure the package is installed "
            f"(pip install .) or the src directory is accessible. "
            f"Current file: {current_file}, Project root: {project_root}"
        ) from e


# Get settings
try:
    if NEW_MODULES_AVAILABLE:
        settings = get_settings()
    else:
        settings = None
except Exception:
    # Fallback if settings can't be loaded
    settings = None
    logger.warning("Could not load settings, using defaults")

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title if settings else "Cap Table Generator API",
    description="API for generating Excel cap tables from JSON data",
    version=settings.api_version if settings else "1.0.0"
)

# Configure CORS
cors_origins = settings.cors_origins if settings else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routes
try:
    from api.v1.routes import router as v1_router
    app.include_router(v1_router)
    logger.info("API v1 routes loaded")
except ImportError as e:
    logger.error(f"Could not load API v1 routes: {e}")
    raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.api_version if settings else "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
