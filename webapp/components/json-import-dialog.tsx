"use client";

import * as React from "react";
import { useEffect, useRef } from "react";
import Lenis from "lenis";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { AlertCircle, FileText } from "lucide-react";
import type { CapTableData } from "@/types/cap-table";

interface JsonImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (data: CapTableData) => void;
}

export function JsonImportDialog({
  open,
  onOpenChange,
  onImport,
}: JsonImportDialogProps) {
  const [jsonString, setJsonString] = React.useState("");
  const [error, setError] = React.useState<string>("");
  const [validationErrors, setValidationErrors] = React.useState<string[]>([]);
  const [isValidating, setIsValidating] = React.useState(false);
  const lenisWrapperRef = useRef<HTMLDivElement>(null);
  const lenisContentRef = useRef<HTMLDivElement>(null);
  const lenisRef = useRef<Lenis | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Reset form when dialog opens
  React.useEffect(() => {
    if (open) {
      setJsonString("");
      setError("");
      setValidationErrors([]);
    }
  }, [open]);

  // Auto-grow textarea to fit content
  React.useEffect(() => {
    if (textareaRef.current) {
      const textarea = textareaRef.current;
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = "auto";
      // Set height to scrollHeight to fit all content
      textarea.style.height = `${textarea.scrollHeight}px`;
      // Update Lenis when content changes
      if (lenisRef.current) {
        lenisRef.current.resize();
      }
    }
  }, [jsonString, open]);

  // Initialize Lenis for smooth scrolling
  useEffect(() => {
    if (!open) {
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
      return;
    }

    // Small delay to ensure DOM is ready and dialog animation completes
    const timeoutId = setTimeout(() => {
      const wrapper = lenisWrapperRef.current;
      const content = lenisContentRef.current;

      if (!wrapper || !content) {
        return;
      }

      const lenis = new Lenis({
        wrapper: wrapper,
        content: content,
        lerp: 0.05,
        duration: 1.2,
        smoothWheel: true,
        syncTouch: false,
        touchMultiplier: 2,
        wheelMultiplier: 1,
        infinite: false,
        autoResize: true,
        orientation: "vertical",
        gestureOrientation: "vertical",
        anchors: false,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      });

      // Store lenis instance in ref
      lenisRef.current = lenis;

      function raf(time: number) {
        lenis.raf(time);
        requestAnimationFrame(raf);
      }

      requestAnimationFrame(raf);
    }, 150);

    return () => {
      clearTimeout(timeoutId);
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
    };
  }, [open]);

  const handleImport = async () => {
    setError("");
    setValidationErrors([]);

    if (!jsonString.trim()) {
      setError("Please paste JSON data");
      return;
    }

    let parsed: any;
    try {
      parsed = JSON.parse(jsonString);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError(`Invalid JSON: ${err.message}`);
      } else if (err instanceof Error) {
        setError(`Error: ${err.message}`);
      } else {
        setError("An unknown error occurred while parsing JSON");
      }
      return;
    }

    // Basic validation
    if (!parsed || typeof parsed !== "object") {
      setError("Invalid JSON: Expected an object");
      return;
    }

    // Check for required fields
    if (!parsed.schema_version) {
      setError("Missing required field: schema_version");
      return;
    }

    if (!Array.isArray(parsed.holders)) {
      setError("Missing or invalid field: holders (must be an array)");
      return;
    }

    if (!Array.isArray(parsed.rounds)) {
      setError("Missing or invalid field: rounds (must be an array)");
      return;
    }

    // Validate the structure matches CapTableData
    const data: CapTableData = {
      schema_version: parsed.schema_version || "2.0",
      holders: parsed.holders || [],
      rounds: parsed.rounds || [],
    };

    // Validate with server
    setIsValidating(true);
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/validate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        let errorMessage = "Failed to validate data";
        try {
          const errorData = await response.json();
          errorMessage =
            errorData.detail?.error || errorData.error || errorMessage;
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        }
        setError(errorMessage);
        setIsValidating(false);
        return;
      }

      const validationResult = await response.json();

      if (!validationResult.is_valid) {
        const errors = validationResult.validation_errors || [];
        setValidationErrors(errors);
        setError(
          `Validation failed: ${errors.length} error(s) found. Please fix them before importing.`
        );
        setIsValidating(false);
        return;
      }

      // Validation passed, proceed with import
      onImport(data);
      onOpenChange(false);
    } catch (err) {
      console.error("Error validating JSON:", err);
      setError(
        err instanceof Error
          ? `Validation error: ${err.message}`
          : "An unknown error occurred while validating JSON"
      );
    } finally {
      setIsValidating(false);
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Allow default paste behavior
    // The textarea will update with the pasted content
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl h-[80vh] flex flex-col p-0">
        <div className="flex flex-col h-full">
          <DialogHeader className="px-6 pt-6 pb-4 shrink-0">
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Import JSON
            </DialogTitle>
            <DialogDescription>
              Paste your cap table JSON data below. The data should include
              schema_version, holders, and rounds.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 flex flex-col min-h-0 px-6 mb-4">
            <div
              ref={lenisWrapperRef}
              className="flex-1 overflow-hidden border border-input rounded-md"
            >
              <div ref={lenisContentRef} className="w-full">
                <textarea
                  ref={textareaRef}
                  value={jsonString}
                  onChange={(e) => {
                    setJsonString(e.target.value);
                    setError("");
                  }}
                  onPaste={handlePaste}
                  placeholder='Paste your JSON here, for example:&#10;{&#10;  "schema_version": "2.0",&#10;  "holders": [...],&#10;  "rounds": [...]&#10;}'
                  className="font-mono min-h-200px text-sm w-full resize-none border-0 bg-transparent px-3 py-2 rounded-md focus-visible:outline-none focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-50"
                  style={{
                    display: "block",
                    overflow: "hidden",
                  }}
                />
              </div>
            </div>

            {(error || validationErrors.length > 0) && (
              <div className="mt-3 p-3 rounded-md bg-destructive/10 border border-destructive/20 flex items-start gap-2 shrink-0">
                <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                <div className="flex-1">
                  {error && (
                    <p className="text-sm text-destructive font-medium mb-1">
                      {error}
                    </p>
                  )}
                  {validationErrors.length > 0 && (
                    <div className="mt-2 space-y-1">
                      <p className="text-xs font-semibold text-destructive mb-1.5">
                        Validation Errors:
                      </p>
                      <ul className="list-disc list-inside space-y-1 text-xs text-destructive/90">
                        {validationErrors.map((err, idx) => (
                          <li key={idx}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="px-6 pb-6 pt-4 shrink-0 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleImport}
              disabled={!jsonString.trim() || isValidating}
            >
              {isValidating ? "Validating..." : "Import"}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}
