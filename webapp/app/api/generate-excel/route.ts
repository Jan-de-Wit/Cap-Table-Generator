import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { join, resolve } from "path";
import { writeFile, readFile, unlink, access } from "fs/promises";
import { constants } from "fs";
import { tmpdir } from "os";

/**
 * Next.js API route that generates Excel files.
 * 
 * In development/local environments: Uses spawn to call local Python script directly
 * In production/Vercel: Calls Python serverless function via HTTP
 * 
 * Uses INTERNAL_API_SECRET for secure communication in production.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  // Check if we're in development/non-production environment
  const isDevelopment = 
    process.env.NODE_ENV === "development" || 
    !process.env.VERCEL ||
    process.env.VERCEL_ENV === "development" ||
    process.env.VERCEL_ENV === "preview";

  if (isDevelopment) {
    // Use local Python instance for development
    return generateExcelLocal(request);
  } else {
    // Use serverless function for production
    return generateExcelServerless(request);
  }
}

/**
 * Generate Excel using local Python script (development mode)
 */
async function generateExcelLocal(
  request: NextRequest
): Promise<NextResponse> {
  let jsonPath: string | null = null;
  let excelPath: string | null = null;

  try {
    const data = await request.json();

    // Create temporary directory for files
    const tempDir = tmpdir();
    const timestamp = Date.now();
    jsonPath = join(tempDir, `cap-table-${timestamp}.json`);
    excelPath = join(tempDir, `cap-table-${timestamp}.xlsx`);

    // Write JSON to temporary file
    await writeFile(jsonPath, JSON.stringify(data, null, 2));

    // Determine Python command (python3 or python)
    const pythonCmd = process.env.PYTHON_CMD || "python3";

    // Get the project root
    // When Next.js runs, process.cwd() is the webapp directory
    // We need to go up one level to get to the project root
    const currentDir = process.cwd();
    const projectRoot = resolve(currentDir, "..");
    const pythonScript = resolve(projectRoot, "scripts", "generate_excel.py");

    console.log("Using local Python instance (development mode)");
    console.log("Current directory:", currentDir);
    console.log("Project root:", projectRoot);
    console.log("Python script path:", pythonScript);
    console.log("Python command:", pythonCmd);

    // Verify the script exists
    try {
      await access(pythonScript, constants.F_OK);
    } catch (error) {
      console.error("Script access error:", error);
      throw new Error(`Python script not found at: ${pythonScript}`);
    }

    // Ensure paths are not null
    if (!jsonPath || !excelPath) {
      throw new Error("Failed to create temporary file paths");
    }

    // Call Python script to generate Excel
    return new Promise<NextResponse>((resolve, reject) => {
      // Build Python path for user-installed packages
      const pythonPath =
        process.env.PYTHONPATH ||
        (process.env.HOME
          ? `${process.env.HOME}/.local/lib/python3.9/site-packages:${process.env.HOME}/.local/lib/python3.10/site-packages:${process.env.HOME}/.local/lib/python3.11/site-packages`
          : "");

      const python = spawn(pythonCmd, [pythonScript, jsonPath!, excelPath!], {
        cwd: projectRoot,
        env: {
          ...process.env,
          ...(pythonPath && { PYTHONPATH: pythonPath }),
        },
      });

      let stdoutOutput = "";
      let errorOutput = "";

      python.stdout?.on("data", (data: Buffer) => {
        stdoutOutput += data.toString();
      });

      python.stderr?.on("data", (data: Buffer) => {
        errorOutput += data.toString();
      });

      python.on("close", async (code: number | null) => {
        try {
          if (code !== 0) {
            console.error("Python stdout:", stdoutOutput);
            console.error("Python stderr:", errorOutput);
            reject(
              new Error(
                `Python script failed with code ${code}: ${errorOutput || stdoutOutput || "Unknown error"}`
              )
            );
            return;
          }

          // Read the generated Excel file
          const excelBuffer = await readFile(excelPath!);

          // Return Excel file
          resolve(
            new NextResponse(excelBuffer, {
              headers: {
                "Content-Type":
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Content-Disposition": 'attachment; filename="cap-table.xlsx"',
              },
            })
          );
        } catch (error) {
          reject(error);
        } finally {
          // Clean up temporary files
          if (jsonPath) {
            await unlink(jsonPath).catch(() => {});
          }
          if (excelPath) {
            await unlink(excelPath).catch(() => {});
          }
        }
      });

      python.on("error", async (error: Error) => {
        console.error("Failed to spawn Python process:", error);
        reject(
          new Error(
            `Failed to spawn Python process: ${error.message}. Make sure Python is installed and available in PATH.`
          )
        );
      });
    });
  } catch (error) {
    // Clean up on error
    if (jsonPath) {
      await unlink(jsonPath).catch(() => {});
    }
    if (excelPath) {
      await unlink(excelPath).catch(() => {});
    }

    console.error("Error generating Excel (local):", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}

/**
 * Generate Excel using serverless Python function (production mode)
 */
async function generateExcelServerless(
  request: NextRequest
): Promise<NextResponse> {
  try {
    const data = await request.json();

    // Get INTERNAL_API_SECRET from environment
    const internalApiSecret = process.env.INTERNAL_API_SECRET;
    if (!internalApiSecret) {
      console.error("INTERNAL_API_SECRET is not configured");
      return NextResponse.json(
        {
          error: "Server configuration error: INTERNAL_API_SECRET not set",
        },
        { status: 500 }
      );
    }

    // Determine the Python function URL
    // On Vercel, serverless functions are accessible via relative paths
    // The Python function will be at /api/generate-excel-python
    // We need to construct an absolute URL for Node.js fetch()
    const baseUrl = 
      process.env.VERCEL_URL 
        ? `https://${process.env.VERCEL_URL}`
        : request.headers.get("host")
        ? `${request.headers.get("x-forwarded-proto") || "https"}://${request.headers.get("host")}`
        : "http://localhost:3000";
    
    const pythonFunctionUrl = `${baseUrl}/api/generate-excel-python`;

    console.log("Using serverless Python function (production mode)");
    console.log("Python function URL:", pythonFunctionUrl);

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
      const errorData = await response.json().catch(() => ({
        error: "Unknown error",
      }));
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
    console.error("Error generating Excel (serverless):", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}

