import { NextRequest, NextResponse } from "next/server";

/**
 * Next.js API route that proxies requests to the Python serverless function.
 * On Vercel, the Python serverless function is at /api/generate-excel-python.
 * This route acts as a proxy to maintain the same API interface.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const data = await request.json();

    // Determine the base URL for the Python serverless function
    // On Vercel, construct URL from the request
    // In development, use localhost
    const isVercel = !!process.env.VERCEL;
    let baseUrl: string;
    
    if (isVercel) {
      // On Vercel, use the request URL to get the correct origin
      const url = new URL(request.url);
      baseUrl = `${url.protocol}//${url.host}`;
    } else {
      // In development, use localhost
      baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
    }

    // Call the Python serverless function
    // Note: Python serverless functions in Vercel are at /api/{filename}
    // Since we have a Next.js route at /api/generate-excel, we'll use a different path
    const pythonApiUrl = `${baseUrl}/api/generate-excel-python`;
    
    console.log("Calling Python serverless function at:", pythonApiUrl);
    console.log("Is Vercel:", isVercel);

    // Get internal secret for authenticating with Python serverless function
    // This ensures only our Next.js app can call the Python function
    const internalSecret = process.env.INTERNAL_API_SECRET;
    
    const response = await fetch(pythonApiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Include internal secret if configured
        ...(internalSecret && { "X-Internal-Secret": internalSecret }),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Python serverless function error:", errorText);
      throw new Error(
        `Python serverless function failed: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    // Get the Excel file as a buffer
    const excelBuffer = await response.arrayBuffer();

    // Return Excel file
    return new NextResponse(excelBuffer, {
      headers: {
        "Content-Type":
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": 'attachment; filename="cap-table.xlsx"',
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

