"""
Cap Table Router

Handles cap table CRUD operations and exports (JSON, Excel).
"""

import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from webapp.backend.services.captable_service import cap_table_service
from src.captable.generator import generate_from_data

router = APIRouter(prefix="/api", tags=["cap-table"])


@router.get("/cap-table")
async def get_cap_table():
    """Get current cap table state with computed metrics."""
    data = cap_table_service.get_cap_table()
    metrics = cap_table_service.calculate_metrics()
    
    return {
        "cap_table": data,
        "metrics": metrics
    }


@router.get("/cap-table/download")
async def download_cap_table(format: str = "json"):
    """
    Download cap table in specified format.
    
    Formats: json, excel
    """
    data = cap_table_service.get_cap_table()
    
    if format == "json":
        import json
        from fastapi.responses import Response
        
        json_str = json.dumps(data, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=cap_table.json"}
        )
    
    elif format == "excel":
        # Generate Excel file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            excel_path = Path(tmp_file.name)
            generate_from_data(data, excel_path)
            
            return FileResponse(
                path=str(excel_path),
                filename="cap_table.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@router.get("/cap-table/excel")
async def export_excel():
    """
    Export cap table as Excel workbook.
    Direct download of generated Excel file.
    """
    data = cap_table_service.get_cap_table()
    
    # Generate Excel file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        excel_path = Path(tmp_file.name)
        generate_from_data(data, excel_path)
        
        return FileResponse(
            path=str(excel_path),
            filename="cap_table.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


@router.delete("/cap-table/reset")
async def reset_cap_table():
    """Reset cap table to initial empty state."""
    cap_table_service.reset()
    return {"status": "reset", "message": "Cap table reset to empty state"}

