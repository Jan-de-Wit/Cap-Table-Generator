"""
FastAPI application for generating Excel cap tables from JSON data.
"""

import sys
from pathlib import Path
from typing import Dict, Any
import tempfile
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import captable module
# First try importing as installed package (for production/Vercel)
# Then fall back to adding src to path (for local development)
try:
    from captable import generate_from_data, CapTableGenerator
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
        logger.info(f"Successfully imported captable module")
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


app = FastAPI(
    title="Cap Table Generator API",
    description="API for generating Excel cap tables from JSON data",
    version="1.0.0"
)

# Configure CORS to allow requests from the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CapTableRequest(BaseModel):
    """Request model for cap table generation."""
    schema_version: str
    holders: list
    rounds: list


def cleanup_file(file_path: str):
    """Background task to clean up temporary file."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(
            f"Warning: Failed to cleanup file {file_path}: {e}", file=sys.stderr)


@app.post("/generate-excel")
async def generate_excel(request: CapTableRequest, background_tasks: BackgroundTasks):
    """
    Generate Excel file from cap table JSON data.

    Args:
        request: Cap table data in JSON format

    Returns:
        Excel file as binary response
    """
    try:
        # Convert Pydantic model to dict
        data = request.model_dump()

        # Validate the data
        generator = CapTableGenerator(json_data=data)
        if not generator.validate():
            errors = generator.get_validation_errors()
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation failed",
                    "validation_errors": errors
                }
            )

        # Create temporary file for Excel output
        excel_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                excel_path = tmp_file.name

            # Generate Excel file
            generator.generate_excel(excel_path)

            # Schedule cleanup after response is sent
            background_tasks.add_task(cleanup_file, excel_path)

            # Return the Excel file
            return FileResponse(
                excel_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename="cap-table.xlsx",
                headers={
                    "Content-Disposition": 'attachment; filename="cap-table.xlsx"'
                }
            )
        except Exception as e:
            # Clean up on error
            if excel_path and os.path.exists(excel_path):
                try:
                    os.unlink(excel_path)
                except:
                    pass
            raise

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR: {error_msg}", file=sys.stderr)
        print(traceback_str, file=sys.stderr)

        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "traceback": traceback_str if os.environ.get("DEBUG") else None
            }
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
