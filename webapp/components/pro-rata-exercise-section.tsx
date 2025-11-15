"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Pencil, TrendingUp, Percent, Building2 } from "lucide-react";
import type { Round, Instrument } from "@/types/cap-table";
import { decimalToPercentage } from "@/lib/formatters";

interface ProRataExerciseSectionProps {
  round: Round;
  holdersWithProRataRights: Array<{
    holderName: string;
    type: "standard" | "super";
    class_name: string;
    percentage?: number;
  }>;
  exercisedProRataRights: Set<string>;
  proRataInstruments: Instrument[];
  onToggleExercise: (
    holderName: string,
    proRataType: "standard" | "super",
    class_name: string,
    percentage?: number
  ) => void;
  onEditProRata: (instrument: Instrument, index: number) => void;
}

export function ProRataExerciseSection({
  round,
  holdersWithProRataRights,
  exercisedProRataRights,
  proRataInstruments,
  onToggleExercise,
  onEditProRata,
}: ProRataExerciseSectionProps) {
  if (holdersWithProRataRights.length === 0) {
    return null;
  }

  return (
    <div className="space-y-5 border-t pt-6">
      <div className="flex items-center justify-between border-b pb-3">
        <h3 className="text-xl font-bold">Exercise Pro-Rata Rights</h3>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {holdersWithProRataRights.map(
          ({ holderName, type, class_name, percentage }) => {
            const isExercised = exercisedProRataRights.has(holderName);
            const existingProRata = proRataInstruments.find(
              (inst) =>
                "holder_name" in inst && inst.holder_name === holderName
            );
            const isSuper = type === "super";

            return (
              <Card
                key={holderName}
                className={`group transition-all cursor-pointer hover:shadow-md ${
                  isExercised
                    ? isSuper
                      ? "border-primary bg-primary/5"
                      : "border-green-500/50 bg-green-500/5"
                    : "border-border hover:border-primary/50"
                }`}
                onClick={() =>
                  onToggleExercise(holderName, type, class_name, percentage)
                }
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1">
                      <div
                        className={`mt-0.5 flex items-center justify-center w-5 h-5 rounded border-2 transition-colors ${
                          isExercised
                            ? "bg-primary border-primary text-primary-foreground"
                            : "border-muted-foreground/30"
                        }`}
                      >
                        {isExercised && (
                          <CheckCircle2 className="h-3.5 w-3.5" />
                        )}
                      </div>
                      <div className="flex-1 space-y-1.5">
                        <div className="flex items-center gap-2">
                          <div className="font-medium text-sm">{holderName}</div>
                          {isSuper && (
                            <Badge variant="default" className="text-xs">
                              Super
                            </Badge>
                          )}
                          {isExercised && (
                            <Badge variant="secondary" className="text-xs">
                              Exercised
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1.5">
                            <TrendingUp className="h-3.5 w-3.5" />
                            <span className="font-medium">
                              {isSuper ? "Super" : "Standard"} Pro-Rata
                            </span>
                          </div>
                          {isSuper && percentage && (
                            <div className="flex items-center gap-1.5">
                              <Percent className="h-3.5 w-3.5" />
                              <span className="font-semibold">
                                {decimalToPercentage(percentage).toFixed(2)}%
                              </span>
                            </div>
                          )}
                          <div className="flex items-center gap-1.5">
                            <Building2 className="h-3.5 w-3.5" />
                            <span className="font-medium">{class_name}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    {isExercised && existingProRata && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation();
                          const actualIndex = round.instruments.findIndex(
                            (inst) => inst === existingProRata
                          );
                          onEditProRata(existingProRata, actualIndex);
                        }}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          }
        )}
      </div>
    </div>
  );
}

