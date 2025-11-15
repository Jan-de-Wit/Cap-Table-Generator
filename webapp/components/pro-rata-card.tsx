"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Pencil, Trash2, User, Building2, Percent, TrendingUp } from "lucide-react";
import type { RoundValidation } from "@/lib/validation";
import { getFieldError } from "@/lib/validation";
import { decimalToPercentage } from "@/lib/formatters";

interface ProRataCardProps {
  instrument: {
    holder_name?: string;
    class_name?: string;
    pro_rata_type?: "standard" | "super";
    pro_rata_percentage?: number;
  };
  displayIndex: number;
  actualIndex: number;
  validation?: RoundValidation;
  onEdit: () => void;
  onDelete: () => void;
}

export function ProRataCard({
  instrument,
  displayIndex,
  actualIndex,
  validation,
  onEdit,
  onDelete,
}: ProRataCardProps) {
  const hasError = getFieldError(
    validation?.errors ?? [],
    `instruments[${actualIndex}]`
  );

  const isSuper = instrument.pro_rata_type === "super";

  return (
    <Card
      className={`group hover:shadow-md transition-all ${
        hasError 
          ? "border-destructive bg-destructive/5" 
          : isSuper
          ? "border-primary/30 bg-primary/5 hover:border-primary/50"
          : "border-border hover:border-primary/50"
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center gap-2">
              <div className={`flex items-center justify-center w-8 h-8 rounded-md font-semibold text-sm ${
                isSuper 
                  ? "bg-primary/20 text-primary" 
                  : "bg-muted text-muted-foreground"
              }`}>
                <TrendingUp className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-sm">
                    Pro-Rata Allocation {displayIndex + 1}
                  </h4>
                  {isSuper && (
                    <Badge variant="default" className="text-xs">
                      Super
                    </Badge>
                  )}
                  {hasError && (
                    <Badge variant="destructive" className="text-xs">
                      Error
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-2.5 pl-10">
              {instrument.holder_name && (
                <div className="flex items-center gap-2 text-sm">
                  <div className="text-muted-foreground flex items-center gap-1.5 min-w-[80px]">
                    <User className="h-3.5 w-3.5" />
                    <span>Holder</span>
                  </div>
                  <span className="font-medium text-foreground">{instrument.holder_name}</span>
                </div>
              )}
              {instrument.class_name && (
                <div className="flex items-center gap-2 text-sm">
                  <div className="text-muted-foreground flex items-center gap-1.5 min-w-[80px]">
                    <Building2 className="h-3.5 w-3.5" />
                    <span>Class</span>
                  </div>
                  <span className="font-medium text-foreground">{instrument.class_name}</span>
                </div>
              )}
              {isSuper && instrument.pro_rata_percentage && (
                <div className="flex items-center gap-2 text-sm">
                  <div className="text-muted-foreground flex items-center gap-1.5 min-w-[80px]">
                    <Percent className="h-3.5 w-3.5" />
                    <span>Max %</span>
                  </div>
                  <span className="font-medium text-foreground">
                    {decimalToPercentage(instrument.pro_rata_percentage).toFixed(2)}%
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button 
              type="button" 
              variant="ghost" 
              size="sm" 
              onClick={onEdit}
              className="h-8 w-8 p-0"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button 
              type="button" 
              variant="ghost" 
              size="sm" 
              onClick={onDelete}
              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

