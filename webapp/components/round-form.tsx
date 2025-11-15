"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Trash2,
  ChevronDown,
  ChevronRight,
  Copy,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { InstrumentDialog } from "@/components/instrument-dialog";
import { RoundParametersSection } from "@/components/round-parameters-section";
import { RoundInstrumentsSection } from "@/components/round-instruments-section";
import { ProRataExerciseSection } from "@/components/pro-rata-exercise-section";
import type {
  Round,
  Holder,
  Instrument,
} from "@/types/cap-table";
import type { RoundValidation } from "@/lib/validation";

interface RoundFormProps {
  round: Round;
  holders: Holder[];
  onUpdate: (round: Round) => void;
  onAddHolder: (holder: Holder) => void;
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  usedGroups: string[];
  usedClassNames: string[];
  allRounds?: Round[];
  roundIndex?: number;
  onUpdateRound?: (roundIndex: number, round: Round) => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  validation?: RoundValidation;
}

export function RoundForm({
  round,
  holders,
  onUpdate,
  onAddHolder,
  onUpdateHolder,
  usedGroups,
  usedClassNames,
  allRounds,
  roundIndex,
  onUpdateRound,
  onDelete,
  onDuplicate,
  isExpanded = true,
  onToggleExpand,
  validation,
}: RoundFormProps) {
  const [touchedFields, setTouchedFields] = React.useState<Set<string>>(
    new Set()
  );
  const [instrumentDialogOpen, setInstrumentDialogOpen] = React.useState(false);
  const [editingInstrument, setEditingInstrument] = React.useState<{
    instrument: Instrument | null;
    index: number;
    isProRata: boolean;
    originalRoundIndex?: number;
  } | null>(null);

  const updateRound = (updates: Partial<Round>) => {
    onUpdate({ ...round, ...updates });
  };

  const addInstrument = (instrument: Instrument) => {
    updateRound({
      instruments: [...round.instruments, instrument],
    });
  };

  // Find the original instrument where pro-rata rights were defined
  const findOriginalProRataRightsInstrument = (
    holderName: string
  ): {
    roundIndex: number;
    instrumentIndex: number;
    instrument: Instrument;
  } | null => {
    if (!allRounds || roundIndex === undefined) return null;

    // Search backwards through previous rounds
    for (let i = roundIndex - 1; i >= 0; i--) {
      const prevRound = allRounds[i];
      const instrumentIndex = prevRound.instruments.findIndex(
        (inst) =>
          "holder_name" in inst &&
          inst.holder_name === holderName &&
          "pro_rata_rights" in inst &&
          inst.pro_rata_rights
      );
      if (instrumentIndex !== -1) {
        return {
          roundIndex: i,
          instrumentIndex,
          instrument: prevRound.instruments[instrumentIndex],
        };
      }
    }
    return null;
  };

  const handleOpenInstrumentDialog = (
    instrument: Instrument | null,
    index: number,
    isProRata: boolean
  ) => {
    // If editing a pro-rata allocation, find and edit the original instrument instead
    if (
      isProRata &&
      instrument &&
      "holder_name" in instrument &&
      instrument.holder_name
    ) {
      const original = findOriginalProRataRightsInstrument(
        instrument.holder_name
      );
      if (original && onUpdateRound) {
        // Edit the original instrument in the previous round
        setEditingInstrument({
          instrument: original.instrument,
          index: original.instrumentIndex,
          isProRata: false,
          originalRoundIndex: original.roundIndex,
        });
        setInstrumentDialogOpen(true);
        return;
      }
    }
    setEditingInstrument({ instrument, index, isProRata });
    setInstrumentDialogOpen(true);
  };

  const handleSaveInstrument = (instrument: Instrument) => {
    if (editingInstrument) {
      // Check if we're editing an original instrument from a previous round
      if (
        "originalRoundIndex" in editingInstrument &&
        editingInstrument.originalRoundIndex !== undefined &&
        onUpdateRound &&
        allRounds
      ) {
        const originalRound = allRounds[editingInstrument.originalRoundIndex];
        const updatedInstruments = originalRound.instruments.map((inst, i) =>
          i === editingInstrument.index ? instrument : inst
        );
        onUpdateRound(editingInstrument.originalRoundIndex, {
          ...originalRound,
          instruments: updatedInstruments,
        });

        // Also update the pro-rata allocation in the current round if it exists
        const proRataIndex = round.instruments.findIndex(
          (inst) =>
            "pro_rata_type" in inst &&
            "holder_name" in inst &&
            inst.holder_name === (instrument as any).holder_name
        );
        if (proRataIndex !== -1) {
          const updatedProRata: Instrument = {
            holder_name: (instrument as any).holder_name,
            class_name: (instrument as any).class_name,
            pro_rata_type:
              (instrument as any).pro_rata_rights === "super"
                ? "super"
                : "standard",
            ...((instrument as any).pro_rata_rights === "super" &&
            (instrument as any).pro_rata_percentage
              ? { pro_rata_percentage: (instrument as any).pro_rata_percentage }
              : {}),
          };
          const updated = round.instruments.map((inst, i) =>
            i === proRataIndex ? updatedProRata : inst
          );
          updateRound({ instruments: updated });
        }
      } else if (editingInstrument.instrument) {
        // Update existing instrument in current round
        const updated = round.instruments.map((inst, i) =>
          i === editingInstrument.index ? instrument : inst
        );
        updateRound({ instruments: updated });
      } else {
        // Add new instrument
        addInstrument(instrument);
      }
    }
    setInstrumentDialogOpen(false);
    setEditingInstrument(null);
  };

  const removeInstrument = (index: number) => {
    updateRound({
      instruments: round.instruments.filter((_, i) => i !== index),
    });
  };

  const updateInstrument = (index: number, updates: Partial<Instrument>) => {
    const updated = round.instruments.map((inst, i) =>
      i === index ? { ...inst, ...updates } : inst
    );
    updateRound({ instruments: updated });
  };

  const needsValuationBasis = [
    "valuation_based",
    "convertible",
    "safe",
  ].includes(round.calculation_type);

  const isComplete = validation?.isValid ?? false;
  const regularInstruments = round.instruments.filter(
    (inst) => !("pro_rata_type" in inst)
  );
  const proRataInstruments = round.instruments.filter(
    (inst) => "pro_rata_type" in inst
  );

  // Check if there are previous rounds
  const hasPreviousRounds =
    roundIndex !== undefined &&
    roundIndex > 0 &&
    allRounds &&
    allRounds.length > 0;

  // Get holders who have shares in previous rounds (for pro-rata allocations)
  const preExistingHolders = React.useMemo(() => {
    if (!hasPreviousRounds || !allRounds || roundIndex === undefined) {
      return [];
    }

    const holderNames = new Set<string>();
    // Collect all holders from rounds before the current round
    for (let i = 0; i < roundIndex; i++) {
      allRounds[i]?.instruments.forEach((instrument) => {
        if ("holder_name" in instrument && instrument.holder_name) {
          holderNames.add(instrument.holder_name);
        }
      });
    }

    return holders.filter((holder) => holderNames.has(holder.name));
  }, [hasPreviousRounds, allRounds, roundIndex, holders]);

  // Get holders with pro-rata rights from previous rounds
  const holdersWithProRataRights = React.useMemo(() => {
    if (!hasPreviousRounds || !allRounds || roundIndex === undefined) {
      return [];
    }

    const rightsMap = new Map<
      string,
      { type: "standard" | "super"; class_name: string; percentage?: number }
    >();

    // Collect pro-rata rights from all previous rounds
    for (let i = 0; i < roundIndex; i++) {
      allRounds[i]?.instruments.forEach((instrument) => {
        if (
          "holder_name" in instrument &&
          instrument.holder_name &&
          "pro_rata_rights" in instrument &&
          instrument.pro_rata_rights &&
          "class_name" in instrument &&
          instrument.class_name
        ) {
          // Use the most recent pro-rata right type for each holder
          rightsMap.set(instrument.holder_name, {
            type: instrument.pro_rata_rights,
            class_name: instrument.class_name,
            percentage:
              "pro_rata_percentage" in instrument
                ? instrument.pro_rata_percentage
                : undefined,
          });
        }
      });
    }

    return Array.from(rightsMap.entries()).map(([holderName, rights]) => ({
      holderName,
      ...rights,
    }));
  }, [hasPreviousRounds, allRounds, roundIndex]);

  // Track which pro-rata rights are exercised (based on existing pro-rata allocations)
  const exercisedProRataRights = React.useMemo(() => {
    const exercised = new Set<string>();
    proRataInstruments.forEach((instrument) => {
      if ("holder_name" in instrument && instrument.holder_name) {
        exercised.add(instrument.holder_name);
      }
    });
    return exercised;
  }, [proRataInstruments]);

  // Handle toggling pro-rata rights exercise
  const handleToggleProRataExercise = (
    holderName: string,
    proRataType: "standard" | "super",
    class_name: string,
    percentage?: number
  ) => {
    const isExercised = exercisedProRataRights.has(holderName);

    if (isExercised) {
      // Remove the pro-rata allocation
      const updatedInstruments = round.instruments.filter(
        (inst) =>
          !("pro_rata_type" in inst) ||
          ("holder_name" in inst && inst.holder_name !== holderName)
      );
      updateRound({ instruments: updatedInstruments });
    } else {
      // Add the pro-rata allocation
      const proRataAllocation: Instrument = {
        holder_name: holderName,
        class_name: class_name,
        pro_rata_type: proRataType,
        ...(proRataType === "super" && percentage
          ? { pro_rata_percentage: percentage }
          : {}),
      };
      updateRound({
        instruments: [...round.instruments, proRataAllocation],
      });
    }
  };

  // Get round number and display name
  const roundNumber = roundIndex !== undefined ? roundIndex + 1 : 1;
  const displayName = round.name || `Round ${roundNumber}`;
  const roundType = round.name ? round.name.split(' ')[0] : '';
  
  // Get contextual info
  const instrumentsCount = regularInstruments.length;
  const holdersCount = new Set(
    regularInstruments
      .filter((inst) => "holder_name" in inst && inst.holder_name)
      .map((inst) => ("holder_name" in inst ? inst.holder_name : ""))
  ).size;

  return (
    <Card
      className={`shadow-md hover:shadow-lg transition-shadow ${
        isComplete 
          ? "border-green-200 dark:border-green-800 bg-green-50/30 dark:bg-green-950/20" 
          : "border-border"
      }`}
    >
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            {onToggleExpand && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onToggleExpand}
                className="h-8 w-8 p-0"
              >
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5" />
                ) : (
                  <ChevronRight className="h-5 w-5" />
                )}
              </Button>
            )}
            <div className="flex items-center gap-3 flex-1">
              {isComplete ? (
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400 shrink-0" />
              ) : (
                <AlertCircle className="h-6 w-6 text-amber-600 dark:text-amber-400 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <CardTitle className="flex items-center gap-3 text-xl font-bold">
                  <span className="text-primary font-extrabold">Round {roundNumber}</span>
                  {round.name && (
                    <>
                      <span className="text-muted-foreground">—</span>
                      <span>{round.name}</span>
                    </>
                  )}
                  {!isComplete && validation && (
                    <Badge variant="destructive" className="text-xs font-semibold ml-2">
                      {validation.errors.length} issue{validation.errors.length !== 1 ? "s" : ""}
                    </Badge>
                  )}
                </CardTitle>
                {isExpanded && (
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    <span className="font-medium">{instrumentsCount} instrument{instrumentsCount !== 1 ? "s" : ""}</span>
                    <span>•</span>
                    <span className="font-medium">{holdersCount} holder{holdersCount !== 1 ? "s" : ""}</span>
                    {round.round_date && (
                      <>
                        <span>•</span>
                        <span>{new Date(round.round_date).toLocaleDateString()}</span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onDuplicate && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onDuplicate}
                className="h-9 w-9 p-0 hover:bg-accent"
                title="Duplicate round"
              >
                <Copy className="h-4 w-4" />
              </Button>
            )}
            {onDelete && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onDelete}
                className="h-9 w-9 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                title="Delete round"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent className="space-y-8 pt-2">
          <div className="border-b pb-6">
            <RoundParametersSection
              round={round}
              touchedFields={touchedFields}
              validation={validation}
              onUpdate={updateRound}
              onFieldTouched={(field) =>
                setTouchedFields((prev) => new Set([...prev, field]))
              }
            />
          </div>

          <div className="space-y-6">
            <RoundInstrumentsSection
              round={round}
              calculationType={round.calculation_type}
              regularInstruments={regularInstruments}
              validation={validation}
              onAddInstrument={() => handleOpenInstrumentDialog(null, -1, false)}
              onEditInstrument={(instrument, index) =>
                handleOpenInstrumentDialog(instrument, index, false)
              }
              onDeleteInstrument={removeInstrument}
            />

            {hasPreviousRounds && holdersWithProRataRights.length > 0 && (
              <ProRataExerciseSection
                round={round}
                holdersWithProRataRights={holdersWithProRataRights}
                exercisedProRataRights={exercisedProRataRights}
                proRataInstruments={proRataInstruments}
                onToggleExercise={handleToggleProRataExercise}
                onEditProRata={(instrument, index) =>
                  handleOpenInstrumentDialog(instrument, index, true)
                }
              />
            )}
          </div>
        </CardContent>
      )}
      {editingInstrument && (
        <InstrumentDialog
          open={instrumentDialogOpen}
          onOpenChange={(open) => {
            setInstrumentDialogOpen(open);
            if (!open) {
              setEditingInstrument(null);
            }
          }}
          instrument={editingInstrument.instrument}
          calculationType={round.calculation_type}
          holders={editingInstrument.isProRata ? preExistingHolders : holders}
          onSave={handleSaveInstrument}
          onAddHolder={onAddHolder}
          onUpdateHolder={onUpdateHolder}
          usedGroups={usedGroups}
          usedClassNames={usedClassNames}
          isProRata={editingInstrument.isProRata}
        />
      )}
    </Card>
  );
}
