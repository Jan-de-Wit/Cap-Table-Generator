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

# Import captable module
# First try importing as installed package (for production/Vercel)
# Then fall back to adding src to path (for local development)
try:
    from captable import generate_from_data, CapTableGenerator
except ImportError:
    # If not installed, add src directory to path
    project_root = Path(__file__).parent
    possible_src_paths = [
        project_root / "src",
        project_root.parent / "src",  # If app.py is in a subdirectory
        Path("/var/task/src"),  # Vercel serverless function location
    ]
    
    for src_path in possible_src_paths:
        if src_path.exists() and (src_path / "captable").exists():
            sys.path.insert(0, str(src_path))
            break
    
    # Try importing again
    try:
        from captable import generate_from_data, CapTableGenerator
    except ImportError as e:
        print(f"ERROR: Could not import captable module", file=sys.stderr)
        print(f"Python path: {sys.path}", file=sys.stderr)
        print(f"Project root: {project_root}", file=sys.stderr)
        print(f"Checked paths: {possible_src_paths}", file=sys.stderr)
        raise ImportError(
            f"Could not import captable. Make sure the package is installed "
            f"(pip install .) or the src directory is accessible."
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


@app.post("/generate-excel-raw")
async def generate_excel_raw(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Generate Excel file from cap table JSON data (raw dict format).
    This endpoint accepts any JSON object and is more flexible.

    Args:
        request: Cap table data as raw dictionary

    Returns:
        Excel file as binary response
    """
    try:
        # Validate the data
        generator = CapTableGenerator(json_data=request)
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


# Vercel serverless function handler
# Mangum wraps the FastAPI ASGI app for serverless environments
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # If mangum is not available, create a simple handler
    # This should not happen if requirements.txt is properly installed
    def handler(event, context):
        return {
            "statusCode": 500,
            "body": "Mangum is required for serverless deployment. Install with: pip install mangum"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
