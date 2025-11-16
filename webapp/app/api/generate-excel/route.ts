import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { join, resolve } from "path";
import { writeFile, readFile, unlink, access } from "fs/promises";
import { constants } from "fs";
import { tmpdir } from "os";

export async function POST(request: NextRequest) {
  let jsonPath: string | null = null;
  let excelPath: string | null = null;

  try {
    const data = await request.json();

    // Create a temporary directory for the JSON file
    const tempDir = tmpdir();
    jsonPath = join(tempDir, `cap-table-${Date.now()}.json`);
    excelPath = join(tempDir, `cap-table-${Date.now()}.xlsx`);

    // Write JSON to temporary file
    await writeFile(jsonPath, JSON.stringify(data, null, 2));

    // Get the project root
    // When Next.js runs, process.cwd() is the webapp directory
    // We need to go up one level to get to the project root
    const currentDir = process.cwd();
    const projectRoot = resolve(currentDir, "..");
    const pythonScript = resolve(projectRoot, "scripts", "generate_excel.py");
    
    // Log paths for debugging (remove in production if needed)
    console.log("Current directory:", currentDir);
    console.log("Project root:", projectRoot);
    console.log("Python script path:", pythonScript);
    
    // Verify the script exists
    try {
      await access(pythonScript, constants.F_OK);
    } catch (error) {
      console.error("Script access error:", error);
      throw new Error(`Python script not found at: ${pythonScript}. Current working directory: ${currentDir}, Project root: ${projectRoot}`);
    }

    // Ensure paths are not null
    if (!jsonPath || !excelPath) {
      throw new Error("Failed to create temporary file paths");
    }

    // Call Python script to generate Excel
    return new Promise((resolve, reject) => {
      const python = spawn("python3", [pythonScript, jsonPath!, excelPath!], {
        cwd: projectRoot,
      });

      let errorOutput = "";

      python.stderr?.on("data", (data: Buffer) => {
        errorOutput += data.toString();
      });

      python.on("close", async (code: number | null) => {
        try {
          if (code !== 0) {
            reject(
              new Error(
                `Python script failed: ${errorOutput || "Unknown error"}`
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
        reject(new Error(`Failed to spawn Python process: ${error.message}`));
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

