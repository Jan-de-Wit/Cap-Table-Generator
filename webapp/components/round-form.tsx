"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Trash2,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  FileText,
  Users,
  Plus,
} from "lucide-react";
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
        // Find the pro-rata allocation by matching holder_name
        const holderName = "holder_name" in instrument && instrument.holder_name
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
            const existingProRataType = "pro_rata_type" in existingProRata 
              ? existingProRata.pro_rata_type 
              : "standard";
            const existingPercentage = "pro_rata_percentage" in existingProRata
              ? existingProRata.pro_rata_percentage
              : undefined;
            
            // Determine the new pro-rata type from the updated original instrument
            const newProRataType = "pro_rata_rights" in instrument && instrument.pro_rata_rights === "super"
              ? "super"
              : "standard";
            
            // Get the new percentage if it's a super pro-rata
            const newPercentage = newProRataType === "super" && "pro_rata_percentage" in instrument
              ? instrument.pro_rata_percentage
              : existingPercentage;
            
            // Update the pro-rata allocation with the new data
            const updatedProRata: Instrument = {
              holder_name: holderName,
              class_name: "class_name" in instrument ? instrument.class_name : "",
              pro_rata_type: newProRataType,
              ...(newProRataType === "super" && newPercentage
                ? { pro_rata_percentage: newPercentage }
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
      description: 'Accident? Hit "Undo" to restore.',
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

  const hasValidationErrors = validation && !validation.isValid;
  const issuesCount = validation?.errors.length ?? 0;
  const [issuesExpanded, setIssuesExpanded] = React.useState(false);

  // Get field IDs for navigation
  const getFieldId = (field: string) => {
    if (roundIndex === undefined) return undefined;
    const fieldMap: Record<string, string> = {
      name: `round-${roundIndex}-name`,
      round_date: `round-${roundIndex}-round_date`,
      calculation_type: `round-${roundIndex}-calculation-type`,
      valuation: `round-${roundIndex}-valuation`,
      valuation_basis: `round-${roundIndex}-valuation-basis`,
    };
    return fieldMap[field] || undefined;
  };

  return (
    <div className="relative">
      {/* Round Header */}
      <div className={`pb-6 ${
        isComplete
          ? "border-b border-green-200/50 dark:border-green-800/50"
          : "border-b border-border/50"
      }`}>
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2.5 mb-2">
                {isComplete ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 shrink-0" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0" />
                )}
                <h2 className="text-lg font-semibold text-foreground">
                  {round.name || `Round ${roundNumber}`}
                </h2>
              </div>
              <div className="flex items-center gap-4 flex-wrap">
                {round.round_date && (
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <span>{new Date(round.round_date).toLocaleDateString()}</span>
                  </div>
                )}
                <Badge variant="secondary" className="text-xs font-medium">
                  <FileText className="h-3 w-3 mr-1" />
                  {instrumentsCount} {instrumentsCount === 1 ? "instrument" : "instruments"}
                </Badge>
                <Badge variant="secondary" className="text-xs font-medium">
                  <Users className="h-3 w-3 mr-1" />
                  {holdersCount} {holdersCount === 1 ? "holder" : "holders"}
                </Badge>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {onDelete && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onDelete}
                className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                title="Delete round"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Issues Panel */}
      {hasValidationErrors && issuesCount > 0 && (
        <div className="mt-6 mb-6 rounded-md bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/50 dark:border-amber-800/50 p-4">
          <div className="flex items-center gap-2.5 mb-3">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span className="text-sm font-semibold text-foreground">
              Issues found
            </span>
          </div>
          <div className="space-y-2">
            {validation?.errors.map((error, idx) => {
              const fieldId = getFieldId(error.field);
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    if (fieldId) {
                      const element = document.getElementById(fieldId);
                      if (element) {
                        element.scrollIntoView({ behavior: "smooth", block: "center" });
                        element.focus();
                      }
                    }
                  }}
                  className="w-full text-left p-2.5 rounded-md hover:bg-amber-100 dark:hover:bg-amber-950/40 transition-colors border border-amber-200/50 dark:border-amber-800/50"
                >
                  <div className="text-xs font-medium text-foreground">
                    {error.field === "name" ? "Round Name" :
                     error.field === "round_date" ? "Round Date" :
                     error.field === "calculation_type" ? "Calculation Type" :
                     error.field === "valuation" ? "Valuation" :
                     error.field === "valuation_basis" ? "Valuation Basis" :
                     error.field === "instruments" ? "Instruments" :
                     error.field}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {error.message}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Content Sections */}
      <div className="pt-6 space-y-8">
              {/* Round Details Section */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-semibold text-foreground mb-1">
                    Round Details
                  </h3>
                  <p className="text-sm text-muted-foreground mb-6">
                    Configure the basic information and calculation method for this round.
                  </p>
                </div>
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
              </div>

              {/* Divider */}
              <div className="border-t border-border/50" />

              {/* Instruments Section */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-semibold text-foreground mb-1">
                    Instruments
                  </h3>
                  <p className="text-sm text-muted-foreground mb-6">
                    Define the instruments and share allocations for this round.
                  </p>
                </div>
                <RoundInstrumentsSection
                  round={round}
                  calculationType={round.calculation_type}
                  regularInstruments={regularInstruments}
                  validation={validation}
                  onAddInstrument={() =>
                    handleOpenInstrumentDialog(null, -1, false)
                  }
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
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-base font-semibold text-foreground mb-1">
                        Pro-Rata Rights
                      </h3>
                      <p className="text-sm text-muted-foreground mb-6">
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

        {/* Action Bar */}
        <div className="mt-6 flex items-center justify-end gap-3">
          <Button
            type="button"
            variant="default"
            size="sm"
            onClick={() => handleOpenInstrumentDialog(null, -1, false)}
            className="font-medium"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Instrument
          </Button>
        </div>
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
    </div>
  );
}
