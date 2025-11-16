"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Circle, AlertCircle } from "lucide-react";
import type { Round } from "@/types/cap-table";
import { validateRound } from "@/lib/validation";

interface RoundsSummaryProps {
  rounds: Round[];
  onRoundClick?: (index: number) => void;
}

export function RoundsSummary({ rounds, onRoundClick }: RoundsSummaryProps) {
  if (rounds.length === 0) return null;

  const validations = rounds.map((round) => validateRound(round));
  const completedCount = validations.filter((v) => v.isValid).length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Rounds Overview</CardTitle>
          <Badge variant="secondary">
            {completedCount} of {rounds.length} complete
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {rounds.map((round, index) => {
            const validation = validations[index];
            const instrumentCount = round.instruments.filter(
              (inst) => !("pro_rata_type" in inst)
            ).length;
            const proRataCount = round.instruments.filter(
              (inst) => "pro_rata_type" in inst
            ).length;

            return (
              <div
                key={index}
                className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                  validation.isValid
                    ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800"
                    : "bg-muted/50 border-border hover:bg-muted cursor-pointer"
                }`}
                onClick={() => onRoundClick?.(index)}
              >
                <div className="flex items-center gap-3 flex-1">
                  {validation.isValid ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  )}
                  <div className="flex-1">
                    <div className="font-semibold">
                      {round.name || `Round ${index + 1}`}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {round.calculation_type.replace("_", " ")} •{" "}
                      {instrumentCount} instrument
                      {instrumentCount !== 1 ? "s" : ""}
                      {proRataCount > 0 &&
                        ` • ${proRataCount} pro-rata allocation${
                          proRataCount !== 1 ? "s" : ""
                        }`}
                    </div>
                  </div>
                </div>
                {!validation.isValid && (
                  <Badge variant="outline" className="text-xs">
                    {validation.errors.length} issue
                    {validation.errors.length !== 1 ? "s" : ""}
                  </Badge>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
