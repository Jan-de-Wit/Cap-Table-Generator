import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { join } from "path";
import { writeFile, readFile, unlink } from "fs/promises";
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

    // Get the project root (two levels up from webapp/app/api)
    const projectRoot = join(process.cwd(), "..", "..");
    const pythonScript = join(projectRoot, "scripts", "generate_excel.py");

    // Call Python script to generate Excel
    return new Promise((resolve, reject) => {
      const python = spawn("python3", [pythonScript, jsonPath, excelPath], {
        cwd: projectRoot,
      });

      let errorOutput = "";

      python.stderr.on("data", (data) => {
        errorOutput += data.toString();
      });

      python.on("close", async (code) => {
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

      python.on("error", async (error) => {
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

