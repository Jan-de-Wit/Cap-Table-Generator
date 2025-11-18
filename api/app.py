"""
FastAPI application for generating Excel cap tables from JSON data.
"""

from captable import generate_from_data, CapTableGenerator
import sys
from pathlib import Path
from typing import Dict, Any
import tempfile
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path to import captable module
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import captable after path is set up


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
