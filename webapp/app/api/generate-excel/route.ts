import { NextRequest, NextResponse } from "next/server";

/**
 * Next.js API route that calls the Python serverless function to generate Excel files.
 * Uses INTERNAL_API_SECRET for secure communication between Next.js and Python function.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const data = await request.json();

    // Get INTERNAL_API_SECRET from environment
    const internalApiSecret = process.env.INTERNAL_API_SECRET;
    if (!internalApiSecret) {
      console.error("INTERNAL_API_SECRET is not configured");
      return NextResponse.json(
        { error: "Server configuration error: INTERNAL_API_SECRET not set" },
        { status: 500 }
      );
    }

    // Determine the Python function URL
    // On Vercel, serverless functions are accessible via relative paths
    // The Python function will be at /api/generate-excel-python
    const pythonFunctionUrl = "/api/generate-excel-python";

    // Call Python serverless function
    const response = await fetch(pythonFunctionUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        data,
        secret: internalApiSecret,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
      console.error("Python function error:", errorData);
      return NextResponse.json(
        { error: errorData.error || "Failed to generate Excel" },
        { status: response.status }
      );
    }

    const result = await response.json();
    
    if (!result.success || !result.excel) {
      return NextResponse.json(
        { error: result.error || "Failed to generate Excel" },
        { status: 500 }
      );
    }

    // Decode base64 Excel data
    const excelBuffer = Buffer.from(result.excel, "base64");

    // Return Excel file
    return new NextResponse(excelBuffer, {
      headers: {
        "Content-Type":
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": `attachment; filename="${result.filename || "cap-table.xlsx"}"`,
      },
    });
  } catch (error) {
    console.error("Error generating Excel:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}

