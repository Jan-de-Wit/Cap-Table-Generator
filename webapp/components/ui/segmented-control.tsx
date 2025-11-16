"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SegmentedControlOption {
  value: string;
  label: string;
}

interface SegmentedControlProps {
  value: string;
  onValueChange: (value: string) => void;
  options: SegmentedControlOption[];
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function SegmentedControl({
  value,
  onValueChange,
  options,
  className,
  size = "md",
}: SegmentedControlProps) {
  const sizeClasses = {
    sm: "h-8 text-xs px-2",
    md: "h-9 text-sm px-3",
    lg: "h-10 text-base px-4",
  };

  return (
    <div
      className={cn(
        "inline-flex rounded-lg bg-muted p-1 w-full",
        className
      )}
      role="tablist"
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="tab"
          onClick={() => onValueChange(option.value)}
          className={cn(
            "relative rounded-md font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 flex-1",
            sizeClasses[size],
            value === option.value
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

