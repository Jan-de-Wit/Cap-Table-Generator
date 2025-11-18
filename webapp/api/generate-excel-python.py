"""
Vercel serverless Python function for generating Excel files from cap table data.
This function is called by the Next.js API route with INTERNAL_API_SECRET authentication.
"""

import json
import os
import sys
from pathlib import Path
import base64
import tempfile

# Add the parent directory's src to the path so we can import captable
# When running on Vercel, the function is in webapp/api/
# We need to go up two levels to get to the project root
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
src_path = project_root / "src"

# Add src to Python path
if src_path.exists():
    sys.path.insert(0, str(src_path))
    print(f"Added to Python path: {src_path}", file=sys.stderr)
else:
    # Try alternative paths (in case of different deployment structure)
    alt_paths = [
        project_root.parent / "src",  # If webapp is nested differently
        current_file.parent.parent / "src",  # If api is at root level
    ]
    for alt_path in alt_paths:
        if alt_path.exists():
            sys.path.insert(0, str(alt_path))
            print(f"Added to Python path (alternative): {alt_path}", file=sys.stderr)
            break

try:
    from captable import generate_from_data
    print("Successfully imported captable", file=sys.stderr)
except ImportError as e:
    # Fallback: try to import from installed package
    try:
        from captable import generate_from_data
        print("Successfully imported captable (from installed package)", file=sys.stderr)
    except ImportError:
        print(f"ERROR: Could not import captable: {e}", file=sys.stderr)
        print(f"Current file: {current_file}", file=sys.stderr)
        print(f"Project root: {project_root}", file=sys.stderr)
        print(f"Src path: {src_path} (exists: {src_path.exists()})", file=sys.stderr)
        print(f"Python path: {sys.path}", file=sys.stderr)
        raise


def handler(request):
    """
    Vercel serverless function handler.
    
    Expected request format:
    {
        "data": {...cap table data...},
        "secret": "INTERNAL_API_SECRET value"
    }
    
    Returns:
        Response with Excel file as base64-encoded string or error message
    """
    try:
        # Verify INTERNAL_API_SECRET
        expected_secret = os.environ.get("INTERNAL_API_SECRET")
        if not expected_secret:
            print("ERROR: INTERNAL_API_SECRET not configured", file=sys.stderr)
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "INTERNAL_API_SECRET not configured"}),
            }
        
        print(f"DEBUG: Expected secret exists: {bool(expected_secret)}", file=sys.stderr)
        print(f"DEBUG: Request type: {type(request)}", file=sys.stderr)
        print(f"DEBUG: Request keys: {list(request.keys()) if isinstance(request, dict) else 'N/A'}", file=sys.stderr)
        
        # Parse request body
        # Vercel Python functions receive request as a dict with "body" as a string
        # Handle different possible request formats
        body = None
        if isinstance(request, dict):
            # Check if body is base64 encoded (Vercel/Lambda format)
            is_base64 = request.get("isBase64Encoded", False)
            
            if "body" in request:
                # Body is a string, parse it
                body_str = request.get("body", "{}")
                print(f"DEBUG: Body type: {type(body_str)}, isBase64Encoded: {is_base64}, Body preview: {str(body_str)[:100]}", file=sys.stderr)
                
                if isinstance(body_str, str):
                    if is_base64:
                        # Body is base64 encoded
                        try:
                            decoded = base64.b64decode(body_str).decode("utf-8")
                            body = json.loads(decoded)
                            print("DEBUG: Body was base64 encoded and decoded", file=sys.stderr)
                        except Exception as e:
                            print(f"DEBUG: Failed to decode base64 body: {e}", file=sys.stderr)
                            body = {}
                    else:
                        # Try to parse as JSON
                        try:
                            body = json.loads(body_str)
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: Failed to parse body as JSON: {e}", file=sys.stderr)
                            # Try base64 decode as fallback
                            try:
                                decoded = base64.b64decode(body_str).decode("utf-8")
                                body = json.loads(decoded)
                                print("DEBUG: Body was base64 encoded (fallback)", file=sys.stderr)
                            except:
                                print(f"DEBUG: Failed to parse body as JSON or base64", file=sys.stderr)
                                body = {}
                else:
                    # Body is already a dict
                    body = body_str
            elif not body:
                # Request itself might be the body (if no "body" key)
                body = request
        elif hasattr(request, "get"):
            # Request-like object with get method
            body_str = request.get("body", "{}")
            if isinstance(body_str, str):
                body = json.loads(body_str)
            else:
                body = body_str
        else:
            # Try to parse as JSON string
            try:
                body = json.loads(str(request))
            except:
                body = {}
        
        if not body:
            print("ERROR: Failed to parse request body", file=sys.stderr)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Failed to parse request body"}),
            }
        
        print(f"DEBUG: Body keys: {list(body.keys()) if isinstance(body, dict) else 'N/A'}", file=sys.stderr)
        
        # Verify secret
        provided_secret = body.get("secret")
        print(f"DEBUG: Provided secret exists: {bool(provided_secret)}", file=sys.stderr)
        print(f"DEBUG: Secret match: {provided_secret == expected_secret}", file=sys.stderr)
        
        if not provided_secret:
            print("ERROR: No secret provided in request", file=sys.stderr)
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Unauthorized: No secret provided"}),
            }
        
        if provided_secret != expected_secret:
            print(f"ERROR: Secret mismatch. Expected length: {len(expected_secret)}, Provided length: {len(provided_secret) if provided_secret else 0}", file=sys.stderr)
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Unauthorized: Invalid secret"}),
            }
        
        # Get cap table data
        data = body.get("data")
        if not data:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'data' field in request"}),
            }
        
        # Generate Excel file in temporary location
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            excel_path = tmp_file.name
        
        try:
            # Generate Excel from data
            generate_from_data(data, excel_path)
            
            # Read the generated Excel file
            with open(excel_path, "rb") as f:
                excel_bytes = f.read()
            
            # Encode as base64 for JSON response
            excel_base64 = base64.b64encode(excel_bytes).decode("utf-8")
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "success": True,
                    "excel": excel_base64,
                    "filename": "cap-table.xlsx",
                }),
            }
        finally:
            # Clean up temporary file
            try:
                os.unlink(excel_path)
            except:
                pass
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR: {error_msg}", file=sys.stderr)
        print(traceback_str, file=sys.stderr)
        
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": error_msg,
                "traceback": traceback_str if os.environ.get("VERCEL_ENV") == "development" else None,
            }),
        }


# Vercel serverless function entry point
# The handler function above is the entry point that Vercel will call
# Vercel Python runtime automatically detects and calls the handler function
__all__ = ["handler"]

