"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { InstrumentCard } from "@/components/instrument-card";
import type { Round, Instrument, CalculationType } from "@/types/cap-table";
import type { RoundValidation } from "@/lib/validation";
import { getFieldError } from "@/lib/validation";

interface RoundInstrumentsSectionProps {
  round: Round;
  calculationType: CalculationType;
  regularInstruments: Instrument[];
  validation?: RoundValidation;
  onAddInstrument: () => void;
  onEditInstrument: (instrument: Instrument, index: number) => void;
  onDeleteInstrument: (index: number) => void;
}

export function RoundInstrumentsSection({
  round,
  calculationType,
  regularInstruments,
  validation,
  onAddInstrument,
  onEditInstrument,
  onDeleteInstrument,
}: RoundInstrumentsSectionProps) {
  const instrumentsError = getFieldError(validation?.errors ?? [], "instruments");
  const proRataInstruments = round.instruments.filter(
    (inst) => "pro_rata_type" in inst
  );
  const hasAnyInstruments = regularInstruments.length > 0 || proRataInstruments.length > 0;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between border-b pb-3">
        <h3 className="text-xl font-bold">
          Round Instruments
          <span className="ml-2 text-base font-semibold text-muted-foreground">
            ({regularInstruments.length})
          </span>
        </h3>
        <Button
          type="button"
          variant="default"
          size="sm"
          onClick={onAddInstrument}
          className="shadow-sm hover:shadow-md transition-shadow"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Instrument
        </Button>
      </div>
      {instrumentsError && !hasAnyInstruments && (
        <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3">
          <p className="text-sm font-medium text-destructive">{instrumentsError}</p>
        </div>
      )}
      <div className="space-y-3">
        {regularInstruments.map((instrument, displayIndex) => {
          const actualIndex = round.instruments.findIndex(
            (inst) => inst === instrument
          );
          return (
            <InstrumentCard
              key={actualIndex}
              instrument={instrument}
              calculationType={calculationType}
              displayIndex={displayIndex}
              actualIndex={actualIndex}
              validation={validation}
              onEdit={() => onEditInstrument(instrument, actualIndex)}
              onDelete={() => onDeleteInstrument(actualIndex)}
            />
          );
        })}
        {regularInstruments.length === 0 && (
          <Card className={`border-dashed ${instrumentsError && !hasAnyInstruments ? "border-destructive/50" : ""}`}>
            <CardContent className="pt-6 pb-6">
              <p className="text-center text-sm text-muted-foreground">
                No instruments yet. Click "Add Instrument" to get started.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

