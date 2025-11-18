"""
Vercel serverless Python function for generating Excel files from cap table data.
This function is called by the Next.js API route.
"""

import json
import os
import sys
from pathlib import Path
import base64
import tempfile

# Import captable module
# Priority: 1. Local module in same directory (for Vercel deployment)
#           2. Parent directory's src (for local development)
#           3. Installed package
current_file = Path(__file__).resolve()
api_dir = current_file.parent  # webapp/api/

# First, try to import from local captable module (same directory as this file)
# This is the primary method for Vercel serverless functions
sys.path.insert(0, str(api_dir))
print(f"Added API directory to Python path: {api_dir}", file=sys.stderr)

# Also try to add parent directory's src for local development
project_root = api_dir.parent.parent  # Go up from webapp/api/ to project root
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
    print(f"Added src to Python path: {src_path}", file=sys.stderr)

try:
    from captable import generate_from_data
    print("Successfully imported captable from local module", file=sys.stderr)
except ImportError as e:
    # Fallback: try alternative paths (in case of different deployment structure)
    alt_paths = [
        project_root.parent / "src",  # If webapp is nested differently
        api_dir.parent / "src",  # If api is at root level
    ]
    for alt_path in alt_paths:
        if alt_path.exists():
            sys.path.insert(0, str(alt_path))
            print(f"Added to Python path (alternative): {alt_path}", file=sys.stderr)
            try:
                from captable import generate_from_data
                print("Successfully imported captable from alternative path", file=sys.stderr)
                break
            except ImportError:
                continue
    else:
        # Last resort: try to import from installed package
        try:
            from captable import generate_from_data
            print("Successfully imported captable (from installed package)", file=sys.stderr)
        except ImportError:
            print(f"ERROR: Could not import captable: {e}", file=sys.stderr)
            print(f"Current file: {current_file}", file=sys.stderr)
            print(f"API directory: {api_dir}", file=sys.stderr)
            print(f"Project root: {project_root}", file=sys.stderr)
            print(f"Src path: {src_path} (exists: {src_path.exists()})", file=sys.stderr)
            print(f"Python path: {sys.path}", file=sys.stderr)
            raise


def handler(request):
    """
    Vercel serverless function handler.

    Expected request format:
    {
        "data": {...cap table data...}
    }

    Returns:
        Response with Excel file as base64-encoded string or error message
    """
    try:
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

                if isinstance(body_str, str):
                    if is_base64:
                        # Body is base64 encoded
                        try:
                            decoded = base64.b64decode(
                                body_str).decode("utf-8")
                            body = json.loads(decoded)
                        except Exception as e:
                            print(
                                f"ERROR: Failed to decode base64 body: {e}", file=sys.stderr)
                            return {
                                "statusCode": 400,
                                "headers": {"Content-Type": "application/json"},
                                "body": json.dumps({"error": "Failed to parse request body"}),
                            }
                    else:
                        # Try to parse as JSON
                        try:
                            body = json.loads(body_str)
                        except json.JSONDecodeError:
                            # Try base64 decode as fallback
                            try:
                                decoded = base64.b64decode(
                                    body_str).decode("utf-8")
                                body = json.loads(decoded)
                            except:
                                print(
                                    f"ERROR: Failed to parse body as JSON or base64", file=sys.stderr)
                                return {
                                    "statusCode": 400,
                                    "headers": {"Content-Type": "application/json"},
                                    "body": json.dumps({"error": "Failed to parse request body"}),
                                }
                else:
                    # Body is already a dict
                    body = body_str
            else:
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

        # Get cap table data
        # Support both direct data and nested data field
        data = body.get("data") if "data" in body else body
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
