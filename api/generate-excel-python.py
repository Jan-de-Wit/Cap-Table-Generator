"""
Vercel serverless function to generate Excel from cap table JSON data.
This function receives JSON data in the request body and returns the Excel file.
"""

import json
import sys
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from io import BytesIO

# Add src to path so we can import captable
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from captable import generate_from_data
except ImportError as e:
    print(f"ERROR: Failed to import captable: {e}", file=sys.stderr)
    print(f"Python path: {sys.path}", file=sys.stderr)
    print(f"Project root: {project_root}", file=sys.stderr)
    raise


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST request to generate Excel file."""
        try:
            # Verify internal secret token to ensure only Next.js can call this function
            expected_secret = os.environ.get('INTERNAL_API_SECRET')
            if expected_secret:
                provided_secret = self.headers.get('X-Internal-Secret')
                if provided_secret != expected_secret:
                    self.send_error(403, "Forbidden: Invalid or missing internal secret")
                    return
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Request body is empty")
                return
            
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Generate Excel file in memory
            # Use BytesIO to create a file-like object in memory
            excel_buffer = BytesIO()
            excel_path = str(excel_buffer)
            
            # For xlsxwriter, we need to write to a temporary file
            # Vercel serverless functions have /tmp directory available
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                excel_path = tmp_file.name
                generate_from_data(data, excel_path)
                
                # Read the generated file
                with open(excel_path, 'rb') as f:
                    excel_data = f.read()
                
                # Clean up
                os.unlink(excel_path)
            
            # Return Excel file
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition', 'attachment; filename="cap-table.xlsx"')
            self.send_header('Content-Length', str(len(excel_data)))
            self.end_headers()
            self.wfile.write(excel_data)
            
        except json.JSONDecodeError as e:
            self.send_error(400, f"Invalid JSON: {str(e)}")
        except ValueError as e:
            self.send_error(400, f"Validation error: {str(e)}")
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        # This function should only be called internally by Next.js
        # Reject direct browser requests
        self.send_error(403, "Forbidden: This endpoint is for internal use only")

