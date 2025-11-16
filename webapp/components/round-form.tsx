"use client";

import * as React from "react";
import { toast } from "sonner";
import { InstrumentDialog } from "@/components/instrument-dialog";
import { RoundParametersSection } from "@/components/round-parameters-section";
import { RoundInstrumentsSection } from "@/components/round-instruments-section";
import { ProRataExerciseSection } from "@/components/pro-rata-exercise-section";
import type { Round, Holder, Instrument } from "@/types/cap-table";
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
    editProRataOnly?: boolean;
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
    // If editing a pro-rata allocation from the pro-rata exercise section,
    // edit the pro-rata allocation directly in the current round
    // (not the original instrument in a previous round)
    if (isProRata && instrument && "pro_rata_type" in instrument) {
      // This is a pro-rata allocation in the current round - edit it directly
      setEditingInstrument({ instrument, index, isProRata });
      setInstrumentDialogOpen(true);
      return;
    }

    // If editing pro-rata rights (not an allocation), find and edit the original instrument
    if (
      isProRata &&
      instrument &&
      "holder_name" in instrument &&
      instrument.holder_name &&
      !("pro_rata_type" in instrument)
    ) {
      const original = findOriginalProRataRightsInstrument(
        instrument.holder_name
      );
      if (original && onUpdateRound) {
        // Edit the original instrument in the previous round, but only show pro-rata fields
        setEditingInstrument({
          instrument: original.instrument,
          index: original.instrumentIndex,
          isProRata: false,
          originalRoundIndex: original.roundIndex,
          editProRataOnly: true,
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
        // Find the pro-rata allocation by matching holder_name
        const holderName =
          "holder_name" in instrument && instrument.holder_name
            ? instrument.holder_name
            : null;

        if (holderName) {
          const proRataIndex = round.instruments.findIndex(
            (inst) =>
              "pro_rata_type" in inst &&
              "holder_name" in inst &&
              inst.holder_name === holderName
          );

          if (proRataIndex !== -1) {
            // Get the existing pro-rata allocation to preserve its data
            const existingProRata = round.instruments[proRataIndex];
            const existingProRataType =
              "pro_rata_type" in existingProRata
                ? existingProRata.pro_rata_type
                : "standard";
            const existingPercentage =
              "pro_rata_percentage" in existingProRata
                ? existingProRata.pro_rata_percentage
                : undefined;

            // Determine the new pro-rata type from the updated original instrument
            const newProRataType =
              "pro_rata_rights" in instrument &&
              instrument.pro_rata_rights === "super"
                ? "super"
                : "standard";

            // Get the new percentage if it's a super pro-rata
            const newPercentage =
              newProRataType === "super" && "pro_rata_percentage" in instrument
                ? instrument.pro_rata_percentage
                : existingPercentage;

            // Update the pro-rata allocation with the new data
            // Preserve exercise_type and partial exercise fields if they exist
            const existingExerciseType =
              "exercise_type" in existingProRata
                ? (existingProRata as any).exercise_type
                : "full";
            const updatedProRata: Instrument = {
              holder_name: holderName,
              class_name:
                "class_name" in instrument ? instrument.class_name : "",
              pro_rata_type: newProRataType,
              exercise_type: existingExerciseType,
              ...(newProRataType === "super" && newPercentage
                ? { pro_rata_percentage: newPercentage }
                : {}),
              ...("partial_exercise_amount" in existingProRata
                ? {
                    partial_exercise_amount: (existingProRata as any)
                      .partial_exercise_amount,
                  }
                : {}),
              ...("partial_exercise_percentage" in existingProRata
                ? {
                    partial_exercise_percentage: (existingProRata as any)
                      .partial_exercise_percentage,
                  }
                : {}),
            };

            const updated = round.instruments.map((inst, i) =>
              i === proRataIndex ? updatedProRata : inst
            );
            updateRound({ instruments: updated });
          }
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
        const holderName =
          "holder_name" in instrument && instrument.holder_name
            ? instrument.holder_name
            : "Unknown";
        const className =
          "class_name" in instrument && instrument.class_name
            ? instrument.class_name
            : "Unknown class";
        toast.success("Instrument added", {
          description: `"${holderName}" - ${className} has been added.`,
        });
      }
    }
    setInstrumentDialogOpen(false);
    setEditingInstrument(null);
  };

  const removeInstrument = (index: number) => {
    const deletedInstrument = round.instruments[index];
    const holderName =
      "holder_name" in deletedInstrument && deletedInstrument.holder_name
        ? deletedInstrument.holder_name
        : "Unknown";
    const className =
      "class_name" in deletedInstrument && deletedInstrument.class_name
        ? deletedInstrument.class_name
        : "Unknown class";

    // Store state for undo
    const previousInstruments = [...round.instruments];

    // Perform deletion
    updateRound({
      instruments: round.instruments.filter((_, i) => i !== index),
    });

    // Show toast with undo
    toast(`"${holderName}" - ${className} has been removed.`, {
      description: "Accident? Hit undo to restore.",
      action: {
        label: "Undo",
        onClick: () => {
          updateRound({ instruments: previousInstruments });
          toast.success("Instrument restored", {
            description: `"${holderName}" - ${className} has been restored.`,
          });
        },
      },
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
        exercise_type: "full",
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
  const roundType = round.name ? round.name.split(" ")[0] : "";

  // Get contextual info
  const instrumentsCount = regularInstruments.length;
  const holdersCount = new Set(
    regularInstruments
      .filter((inst) => "holder_name" in inst && inst.holder_name)
      .map((inst) => ("holder_name" in inst ? inst.holder_name : ""))
  ).size;

  return (
    <div className="relative pb-50">
      {/* Main Content Sections */}
      <div className="space-y-8">
        {/* Round Parameters - Merged with round name editing */}
        <RoundParametersSection
          round={round}
          touchedFields={touchedFields}
          validation={validation}
          onUpdate={updateRound}
          onFieldTouched={(field) =>
            setTouchedFields((prev) => new Set([...prev, field]))
          }
          roundIndex={roundIndex}
        />

        {/* Divider */}
        <div className="border-t border-border/50" />

        {/* Instruments Section */}
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold text-foreground mb-1">
              Instruments
            </h3>
            <p className="text-sm text-muted-foreground">
              Define the instruments and share allocations for this round.
            </p>
          </div>
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
        </div>

        {/* Pro-Rata Section */}
        {hasPreviousRounds && holdersWithProRataRights.length > 0 && (
          <>
            <div className="border-t border-border/50" />
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  Pro-Rata Allocations
                </h3>
                <p className="text-sm text-muted-foreground">
                  Exercise pro-rata rights from previous rounds.
                </p>
              </div>
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
            </div>
          </>
        )}
      </div>

      {editingInstrument && (
        <InstrumentDialog
          key={
            editingInstrument.instrument &&
            "holder_name" in editingInstrument.instrument
              ? `${editingInstrument.instrument.holder_name}-${
                  editingInstrument.index
                }-${JSON.stringify(editingInstrument.instrument)}`
              : `instrument-${editingInstrument.index}`
          }
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
          editProRataOnly={editingInstrument.editProRataOnly}
          originalProRataInstrument={
            editingInstrument.isProRata &&
            editingInstrument.instrument &&
            "holder_name" in editingInstrument.instrument &&
            editingInstrument.instrument.holder_name
              ? (() => {
                  const original = findOriginalProRataRightsInstrument(
                    editingInstrument.instrument &&
                      "holder_name" in editingInstrument.instrument
                      ? editingInstrument.instrument.holder_name
                      : ""
                  );
                  // Always fetch the latest instrument from allRounds
                  if (original && allRounds) {
                    return (
                      allRounds[original.roundIndex]?.instruments?.[
                        original.instrumentIndex
                      ] || original.instrument
                    );
                  }
                  return null;
                })()
              : null
          }
          originalProRataRoundIndex={
            editingInstrument.isProRata &&
            editingInstrument.instrument &&
            "holder_name" in editingInstrument.instrument &&
            editingInstrument.instrument.holder_name
              ? (() => {
                  const original = findOriginalProRataRightsInstrument(
                    editingInstrument.instrument &&
                      "holder_name" in editingInstrument.instrument
                      ? editingInstrument.instrument.holder_name
                      : ""
                  );
                  return original?.roundIndex ?? null;
                })()
              : null
          }
          originalProRataRoundName={
            editingInstrument.isProRata &&
            editingInstrument.instrument &&
            "holder_name" in editingInstrument.instrument &&
            editingInstrument.instrument.holder_name
              ? (() => {
                  const original = findOriginalProRataRightsInstrument(
                    editingInstrument.instrument &&
                      "holder_name" in editingInstrument.instrument
                      ? editingInstrument.instrument.holder_name
                      : ""
                  );
                  if (original && allRounds) {
                    return allRounds[original.roundIndex]?.name ?? null;
                  }
                  return null;
                })()
              : null
          }
        />
      )}
    </div>
  );
}
