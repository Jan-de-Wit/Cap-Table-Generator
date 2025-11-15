"use client";

import * as React from "react";
import { Label } from "@/components/ui/label";
import { HelpCircle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface FieldWithHelpProps {
  label: string;
  helpText?: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
  htmlFor?: string;
}

export function FieldWithHelp({
  label,
  helpText,
  required,
  error,
  children,
  htmlFor,
}: FieldWithHelpProps) {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center gap-2">
        <Label 
          htmlFor={htmlFor} 
          className={`text-sm font-semibold ${error ? "text-destructive" : required ? "text-foreground" : ""}`}
        >
          {label}
          {required && <span className="text-destructive ml-1.5 font-bold">*</span>}
        </Label>
        {helpText && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help hover:text-foreground transition-colors" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{helpText}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      {children}
      {error && (
        <p className="text-sm font-medium text-destructive">{error}</p>
      )}
    </div>
  );
}

