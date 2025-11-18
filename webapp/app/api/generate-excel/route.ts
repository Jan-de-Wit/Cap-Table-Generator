import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { join, resolve } from "path";
import { writeFile, readFile, unlink, access } from "fs/promises";
import { constants } from "fs";
import { tmpdir } from "os";

/**
 * Next.js API route that calls Python directly to generate Excel files.
 * This approach uses spawn to execute Python scripts directly from Node.js.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
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
    const pythonCmd = process.env.PYTHON_CMD || 'python3';
    
    // Get the project root
    // When Next.js runs, process.cwd() is the webapp directory
    // We need to go up one level to get to the project root
    const currentDir = process.cwd();
    const projectRoot = resolve(currentDir, "..");
    const pythonScript = resolve(projectRoot, "scripts", "generate_excel.py");
    
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
      const pythonPath = process.env.PYTHONPATH || 
        (process.env.HOME ? `${process.env.HOME}/.local/lib/python3.9/site-packages:${process.env.HOME}/.local/lib/python3.10/site-packages:${process.env.HOME}/.local/lib/python3.11/site-packages` : '');
      
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
        reject(new Error(`Failed to spawn Python process: ${error.message}. Make sure Python is installed and available in PATH.`));
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

    console.error("Error generating Excel:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}

