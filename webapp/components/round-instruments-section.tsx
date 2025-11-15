"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { InstrumentCard } from "@/components/instrument-card";
import type { Round, Instrument, CalculationType } from "@/types/cap-table";
import type { RoundValidation } from "@/lib/validation";

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
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Round Instruments ({regularInstruments.length})
        </h3>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onAddInstrument}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Instrument
        </Button>
      </div>
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
          <Card className="border-dashed">
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

