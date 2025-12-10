"use client";

import * as React from "react";
import Image from "next/image";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { RoundForm } from "@/components/round-form";
import { Sidebar } from "@/components/sidebar";
import { HolderDialog } from "@/components/holder-dialog";
import { JsonImportDialog } from "@/components/json-import-dialog";
import {
  Plus,
  Sparkles,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  FileText,
  Users,
  Upload,
  Menu,
  X,
  Undo2,
  Redo2,
} from "lucide-react";
import { toast } from "sonner";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Round, Holder, CapTableData } from "@/types/cap-table";
import {
  useLocalStoragePersistence,
  loadFromLocalStorage,
} from "@/lib/use-local-storage";
import { useValidation } from "@/lib/use-validation";
import { useRounds } from "@/lib/use-rounds";
import { useHolders } from "@/lib/use-holders";
import { useUndoRedo } from "@/lib/use-undo-redo";

export default function Home() {
  // Initialize state - always start empty to avoid hydration mismatch
  const [rounds, setRounds] = React.useState<Round[]>([]);
  const [holders, setHolders] = React.useState<Holder[]>([]);
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [editingHolder, setEditingHolder] = React.useState<Holder | null>(null);
  const [holderDialogOpen, setHolderDialogOpen] = React.useState(false);
  const [jsonImportDialogOpen, setJsonImportDialogOpen] = React.useState(false);
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [selectedRoundIndex, setSelectedRoundIndex] = React.useState<
    number | null
  >(null);
  const [isMounted, setIsMounted] = React.useState(false);

  // Load from localStorage after mount to avoid hydration mismatch
  React.useEffect(() => {
    setIsMounted(true);
    const saved = loadFromLocalStorage();
    if (saved) {
      if (saved.rounds && saved.rounds.length > 0) {
        setRounds(saved.rounds);
        setSelectedRoundIndex(0); // Select first round if data exists
      }
      if (saved.holders && saved.holders.length > 0) {
        setHolders(saved.holders);
      }
    }
  }, []);

  // Use refs to access current state in callbacks
  const roundsRef = React.useRef(rounds);
  const holdersRef = React.useRef(holders);

  React.useEffect(() => {
    roundsRef.current = rounds;
  }, [rounds]);

  React.useEffect(() => {
    holdersRef.current = holders;
  }, [holders]);

  // Use custom hooks for state management
  const roundsManager = useRounds(
    rounds,
    setRounds,
    selectedRoundIndex,
    setSelectedRoundIndex
  );

  const holdersManager = useHolders(holders, setHolders, rounds, setRounds);

  // Use optimized validation hook
  const { validations, validationSummary, isRoundValid, getFieldErrors } =
    useValidation(rounds, { incremental: true });

  // Undo/Redo functionality
  const handleStateChange = React.useCallback(
    (state: {
      rounds: Round[];
      holders: Holder[];
      selectedRoundIndex: number | null;
    }) => {
      setRounds(state.rounds);
      setHolders(state.holders);
      setSelectedRoundIndex(state.selectedRoundIndex);
    },
    []
  );

  const undoRedo = useUndoRedo(
    { rounds, holders, selectedRoundIndex },
    handleStateChange,
    { maxHistorySize: 50, debounceMs: 300 }
  );

  // Stable reference to saveState to avoid useEffect re-runs
  const saveStateRef = React.useRef(undoRedo.saveState);
  React.useEffect(() => {
    saveStateRef.current = undoRedo.saveState;
  }, [undoRedo.saveState]);

  // Save state to history when rounds or holders change
  // Skip saving on initial mount to avoid saving empty state
  const isInitialMount = React.useRef(true);
  const prevStateStringRef = React.useRef<string | null>(null);
  const isSavingRef = React.useRef(false);

  React.useEffect(() => {
    if (isMounted && !isSavingRef.current) {
      const currentState = { rounds, holders, selectedRoundIndex };
      const currentStateString = JSON.stringify({
        rounds: currentState.rounds,
        holders: currentState.holders,
        selectedRoundIndex: currentState.selectedRoundIndex,
      });

      // Skip if state hasn't actually changed (prevents duplicate saves from React strict mode)
      if (prevStateStringRef.current === currentStateString) {
        return;
      }

      prevStateStringRef.current = currentStateString;
      isSavingRef.current = true;

      if (isInitialMount.current) {
        isInitialMount.current = false;
        // Initialize history with current state on first mount
        saveStateRef.current(currentState);
      } else {
        saveStateRef.current(currentState);
      }

      // Reset saving flag after a short delay
      setTimeout(() => {
        isSavingRef.current = false;
      }, 50);
    }
  }, [rounds, holders, selectedRoundIndex, isMounted]);

  // Build cap table data for persistence
  const capTableData = React.useMemo((): CapTableData | null => {
    if (rounds.length === 0 && holders.length === 0) {
      return null;
    }
    // Filter out pro_rata_rights from instruments when not exercised
    // and expand anti-dilution instruments to future rounds
    const processedRounds = rounds.map((round, roundIndex) => {
      const processedInstruments = round.instruments.map((instrument) => {
        // Remove React component-specific fields that shouldn't be in the schema
        const { displayIndex, actualIndex, hasError, ...cleanInstrument } =
          instrument as any;

        // Only process regular instruments (not pro-rata or anti-dilution allocations)
        if ("pro_rata_type" in cleanInstrument) {
          return cleanInstrument; // Keep pro-rata allocations as-is (but cleaned)
        }
        // Anti-dilution allocations have holder_name, class_name, dilution_method, and original_investment_round
        // They don't have anti_dilution_rounds (that's only in original instruments)
        if (
          "dilution_method" in cleanInstrument &&
          !("anti_dilution_rounds" in cleanInstrument) &&
          "holder_name" in cleanInstrument &&
          "class_name" in cleanInstrument &&
          "dilution_method" in cleanInstrument &&
          "original_investment_round" in cleanInstrument
        ) {
          return cleanInstrument; // Keep anti-dilution allocations as-is
        }

        // Check if this instrument has pro_rata_rights
        if (
          "pro_rata_rights" in cleanInstrument &&
          cleanInstrument.pro_rata_rights &&
          "holder_name" in cleanInstrument &&
          cleanInstrument.holder_name
        ) {
          // Check if there's a corresponding pro-rata allocation in any later round
          const holderName = cleanInstrument.holder_name;
          const hasExercisedProRata = rounds.some(
            (laterRound, laterRoundIndex) => {
              if (laterRoundIndex <= roundIndex) {
                return false; // Only check later rounds
              }
              return laterRound.instruments.some(
                (laterInst) =>
                  "pro_rata_type" in laterInst &&
                  "holder_name" in laterInst &&
                  laterInst.holder_name === holderName
              );
            }
          );

          // If not exercised, remove pro_rata_rights and related fields
          if (!hasExercisedProRata) {
            const { pro_rata_rights, pro_rata_percentage, ...rest } =
              cleanInstrument;
            return rest;
          }
        }

        // Remove dilution_method and anti_dilution_rounds from original instruments
        // These will be exported as separate AntiDilutionAllocation instruments
        const { dilution_method, anti_dilution_rounds, ...rest } =
          cleanInstrument as any;
        return rest;
      });

      return {
        ...round,
        instruments: processedInstruments,
      };
    });

    // Expand anti-dilution instruments to future rounds as separate AntiDilutionAllocation instruments
    // First, we need to look at the original rounds (before processing) to get anti_dilution_rounds info
    const expandedRounds = processedRounds.map((round, roundIndex) => {
      // Start with any existing anti-dilution allocations that are already in processedRounds
      // These come from rounds that were loaded from localStorage/import
      const existingAntiDilutionAllocations = round.instruments.filter(
        (inst) =>
          "dilution_method" in inst &&
          !("anti_dilution_rounds" in inst) &&
          "holder_name" in inst &&
          "class_name" in inst &&
          "original_investment_round" in inst
      );

      // New allocations to add from expansion logic
      const antiDilutionInstruments: any[] = [];

      // Helper function to check if a round type supports price-based anti-dilution
      const supportsPriceBasedAntiDilution = (calcType: string): boolean => {
        return !["fixed_shares", "target_percentage"].includes(calcType);
      };

      // Helper function to check if an anti-dilution allocation already exists
      // Check against existing allocations and also check if we've already added it to antiDilutionInstruments
      const hasExistingAntiDilutionAllocation = (
        holderName: string,
        className: string,
        dilutionMethod: string,
        originalInvestmentRound: string
      ): boolean => {
        // Check in existing allocations from processedRounds
        const existsInExisting = existingAntiDilutionAllocations.some(
          (existingInst) => {
            return (
              existingInst.holder_name === holderName &&
              existingInst.class_name === className &&
              existingInst.dilution_method === dilutionMethod &&
              existingInst.original_investment_round === originalInvestmentRound
            );
          }
        );

        if (existsInExisting) {
          return true;
        }

        // Check if we've already added it to antiDilutionInstruments in this iteration
        const existsInNew = antiDilutionInstruments.some((newInst) => {
          return (
            newInst.holder_name === holderName &&
            newInst.class_name === className &&
            newInst.dilution_method === dilutionMethod &&
            newInst.original_investment_round === originalInvestmentRound
          );
        });

        return existsInNew;
      };

      // Look through all previous rounds in the original data to find instruments with anti-dilution protection
      for (
        let prevRoundIndex = 0;
        prevRoundIndex < roundIndex;
        prevRoundIndex++
      ) {
        const prevRound = rounds[prevRoundIndex]; // Use original rounds to get anti_dilution_rounds

        prevRound.instruments.forEach((instrument) => {
          // Skip pro-rata allocations
          if ("pro_rata_type" in instrument) {
            return;
          }

          // Skip anti-dilution allocations (they are already expanded, don't expand them again)
          if (
            "dilution_method" in instrument &&
            !("anti_dilution_rounds" in instrument) &&
            "holder_name" in instrument &&
            "class_name" in instrument &&
            "original_investment_round" in instrument
          ) {
            return;
          }

          // Check if instrument has anti-dilution protection
          // Note: anti_dilution_rounds defaults to "infinite" if not set, so we check if dilution_method exists
          // If dilution_method exists, anti-dilution protection applies (even if anti_dilution_rounds is not explicitly set)
          if (
            "dilution_method" in instrument &&
            instrument.dilution_method &&
            "holder_name" in instrument &&
            instrument.holder_name &&
            "class_name" in instrument &&
            instrument.class_name
          ) {
            const dilutionMethod = instrument.dilution_method;
            // Get anti_dilution_rounds - defaults to "infinite" if not set
            const antiDilutionRounds =
              "anti_dilution_rounds" in instrument
                ? (instrument as any).anti_dilution_rounds
                : undefined; // undefined means infinite

            // Determine how many rounds ahead this applies to
            let roundsAhead: number;
            if (
              antiDilutionRounds === "infinite" ||
              antiDilutionRounds === undefined
            ) {
              roundsAhead = Infinity;
            } else if (typeof antiDilutionRounds === "number") {
              roundsAhead = antiDilutionRounds;
            } else {
              return; // Invalid value, skip
            }

            // For price-based methods (full_ratchet, weighted_average), skip rounds where they can't apply
            // Count only rounds that support price-based anti-dilution
            if (dilutionMethod !== "percentage_based") {
              let applicableRoundsCounted = 0;

              // Count forward from the original round, skipping rounds that don't support price-based
              for (
                let checkRoundIndex = prevRoundIndex + 1;
                checkRoundIndex <= roundIndex;
                checkRoundIndex++
              ) {
                const checkRound = processedRounds[checkRoundIndex];
                const checkCalcType = checkRound.calculation_type;

                if (supportsPriceBasedAntiDilution(checkCalcType)) {
                  applicableRoundsCounted++;

                  // If this is the current round and it supports price-based, check if we should add anti-dilution
                  if (checkRoundIndex === roundIndex) {
                    if (
                      roundsAhead === Infinity ||
                      applicableRoundsCounted <= roundsAhead
                    ) {
                      // Check if this anti-dilution allocation already exists before adding
                      if (
                        !hasExistingAntiDilutionAllocation(
                          instrument.holder_name,
                          instrument.class_name,
                          instrument.dilution_method,
                          prevRound.name
                        )
                      ) {
                        antiDilutionInstruments.push({
                          holder_name: instrument.holder_name,
                          class_name: instrument.class_name,
                          dilution_method: instrument.dilution_method,
                          original_investment_round: prevRound.name,
                        });
                      }
                    }
                    break;
                  }
                }
              }
            } else {
              // For percentage-based, count all rounds (including fixed_shares and target_percentage)
              const roundsSinceOriginal = roundIndex - prevRoundIndex;

              // Check if anti-dilution still applies to this round
              if (
                roundsAhead === Infinity ||
                roundsSinceOriginal <= roundsAhead
              ) {
                // Check if this anti-dilution allocation already exists before adding
                if (
                  !hasExistingAntiDilutionAllocation(
                    instrument.holder_name,
                    instrument.class_name,
                    instrument.dilution_method,
                    prevRound.name
                  )
                ) {
                  antiDilutionInstruments.push({
                    holder_name: instrument.holder_name,
                    class_name: instrument.class_name,
                    dilution_method: instrument.dilution_method,
                    original_investment_round: prevRound.name,
                  });
                }
              }
            }
          }
        });
      }

      // Separate regular instruments from anti-dilution allocations
      const regularInstruments = round.instruments.filter(
        (inst) =>
          !(
            "dilution_method" in inst &&
            !("anti_dilution_rounds" in inst) &&
            "holder_name" in inst &&
            "class_name" in inst &&
            "original_investment_round" in inst
          )
      );

      // Combine: regular instruments + existing allocations + new allocations
      return {
        ...round,
        instruments: [
          ...regularInstruments,
          ...existingAntiDilutionAllocations,
          ...antiDilutionInstruments,
        ],
      };
    });

    return {
      schema_version: "2.0",
      holders,
      rounds: expandedRounds,
    };
  }, [rounds, holders]);

  // Persist raw rounds and holders to localStorage (not processed capTableData)
  // This preserves anti_dilution_rounds so badges and expansion work correctly on reload
  const rawDataForPersistence = React.useMemo((): CapTableData | null => {
    if (rounds.length === 0 && holders.length === 0) {
      return null;
    }
    // Create a simple structure with raw rounds and holders for persistence
    // This preserves anti_dilution_rounds in original instruments
    return {
      schema_version: "2.0",
      holders,
      rounds: rounds.map((round) => ({
        ...round,
        instruments: round.instruments.map((instrument) => {
          // Remove React component-specific fields but keep all other fields including anti_dilution_rounds
          const { displayIndex, actualIndex, hasError, ...cleanInstrument } =
            instrument as any;
          return cleanInstrument;
        }),
      })),
    };
  }, [rounds, holders]);

  useLocalStoragePersistence(rawDataForPersistence, {
    enabled: true,
    debounceMs: 500,
  });

  // Extract operations from hooks
  const {
    addRound,
    updateRound,
    deleteRound,
    reorderRounds,
    updateConversionRefs,
  } = roundsManager;

  const { addHolder, updateHolder, deleteHolder, moveHolderToGroup } =
    holdersManager;

  // Get used groups from all holders
  const usedGroups = React.useMemo(() => {
    const groups = new Set<string>();
    holders.forEach((holder) => {
      if (holder.group) {
        groups.add(holder.group);
      }
    });
    return Array.from(groups);
  }, [holders]);

  // Get used class names from all rounds
  const usedClassNames = React.useMemo(() => {
    const classNames = new Set<string>();
    rounds.forEach((round) => {
      round.instruments.forEach((instrument) => {
        if ("class_name" in instrument && instrument.class_name) {
          classNames.add(instrument.class_name);
        }
      });
    });
    return Array.from(classNames).sort();
  }, [rounds]);

  const handleEditHolder = React.useCallback((holder: Holder) => {
    setEditingHolder(holder);
    setHolderDialogOpen(true);
  }, []);

  const handleEditRound = React.useCallback((index: number) => {
    // Select the round first
    setSelectedRoundIndex(index);
    // Scroll to the round after a short delay
    setTimeout(() => {
      const element = document.getElementById(`round-${index}`);
      element?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  }, []);

  const handleNavigateToError = React.useCallback(
    (roundIndex: number, field?: string) => {
      // Select the round first
      setSelectedRoundIndex(roundIndex);
      // Scroll to the round after a short delay
      setTimeout(() => {
        const element = document.getElementById(`round-${roundIndex}`);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "center" });

          // If a specific field is provided, try to focus on it
          if (field) {
            // Try to find the field input by ID or data attribute
            setTimeout(() => {
              // Field names might be like "name", "round_date", "instruments[0].holder_name", etc.
              const fieldId = field.includes("[")
                ? undefined // Complex nested fields are harder to target
                : `round-${roundIndex}-${field}`;

              if (fieldId) {
                const fieldElement = document.getElementById(fieldId);
                if (fieldElement) {
                  fieldElement.focus();
                  fieldElement.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                  });
                }
              }
            }, 300);
          }
        }
      }, 100);
    },
    []
  );

  const handleSaveHolder = React.useCallback(
    (holder: Holder) => {
      if (editingHolder) {
        updateHolder(editingHolder.name, holder);
      } else {
        addHolder(holder);
      }
      setHolderDialogOpen(false);
      setEditingHolder(null);
    },
    [editingHolder, updateHolder, addHolder]
  );

  const handleAddHolderFromSidebar = React.useCallback(() => {
    setEditingHolder(null);
    setHolderDialogOpen(true);
  }, []);

  const handleDownloadExcel = React.useCallback(async () => {
    if (!capTableData) return;

    setIsGenerating(true);
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/generate-excel`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(capTableData),
      });

      if (!response.ok) {
        let errorMessage = "Failed to generate Excel";
        try {
          const errorData = await response.json();
          errorMessage =
            errorData.detail?.error || errorData.error || errorMessage;
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "cap-table.xlsx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Excel file downloaded", {
        description: "Your cap table has been exported successfully.",
      });
    } catch (error) {
      console.error("Error generating Excel:", error);
      toast.error("Download failed", {
        description:
          error instanceof Error ? error.message : "Unknown error occurred",
      });
    } finally {
      setIsGenerating(false);
    }
  }, [capTableData]);

  const canDownload = React.useMemo(
    () => validationSummary.isValid && rounds.length > 0,
    [validationSummary.isValid, rounds.length]
  );

  const handleCopyJson = React.useCallback(() => {
    if (!capTableData) return;

    const jsonString = JSON.stringify(capTableData, null, 2);
    navigator.clipboard
      .writeText(jsonString)
      .then(() => {
        toast.success("JSON copied", {
          description: "The cap table has been copied to your clipboard.",
        });
      })
      .catch((err) => {
        console.error("Failed to copy JSON:", err);
        toast.error("Copy failed", {
          description: "Failed to copy JSON to clipboard",
        });
      });
  }, [capTableData]);

  const handleDownloadJson = React.useCallback(() => {
    if (!capTableData) return;

    const jsonString = JSON.stringify(capTableData, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cap-table.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("JSON file downloaded", {
      description: "Your cap table has been saved as JSON.",
    });
  }, [capTableData]);

  const handleImportJson = React.useCallback(
    (data: CapTableData) => {
      // Check current state using refs
      if (roundsRef.current.length > 0 || holdersRef.current.length > 0) {
        // Reset current rounds
        setRounds([]);
        setHolders([]);
        setSelectedRoundIndex(null);
      }

      // Set the imported data
      const importedRounds = data.rounds || [];
      const updatedWithRefs = updateConversionRefs(importedRounds);

      setHolders(data.holders || []);
      setRounds(updatedWithRefs);

      // Select the first round if available
      if (data.rounds && data.rounds.length > 0) {
        setSelectedRoundIndex(0);
      }

      toast.success("JSON imported successfully", {
        description: `Imported ${data.rounds?.length || 0} rounds and ${
          data.holders?.length || 0
        } holders.`,
      });
    },
    [updateConversionRefs]
  );

  const handleSelectRound = React.useCallback((index: number) => {
    setSelectedRoundIndex(index);
    setSidebarOpen(false); // Close mobile drawer when selecting
  }, []);

  return (
    <div className="min-h-screen bg-background flex">
      <div className="flex-1 overflow-auto">
        <div className="w-full max-w-3xl mx-auto p-3 sm:p-5 lg:p-6">
          {/* Header */}
          <div className="mb-6 pt-4">
            <div className="mb-6 flex items-center gap-2 justify-between">
              <p className="text-lg font-semibold">zebra.legal</p>
              {/* Mobile menu button */}
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="lg:hidden"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </Button>
            </div>
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-4">
              Cap Table Generator
            </h1>
          </div>

          {/* Rounds Section */}
          <div className="space-y-5">
            {rounds.length > 0 && (
              <div className="space-y-3 pb-2">
                <div className="flex items-center justify-between gap-2 border-b border-border/50 pb-2.5">
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-semibold">
                      {selectedRoundIndex !== null && rounds[selectedRoundIndex]
                        ? `Editing: ${
                            rounds[selectedRoundIndex].name ||
                            `Round ${selectedRoundIndex + 1}`
                          }`
                        : "Select a Round"}
                    </h2>

                    {selectedRoundIndex !== null &&
                      rounds[selectedRoundIndex] &&
                      rounds[selectedRoundIndex].round_date && (
                        <Badge variant="outline" className="text-xs">
                          <span>
                            {new Date(
                              rounds[selectedRoundIndex].round_date
                            ).toLocaleDateString()}
                          </span>
                        </Badge>
                      )}
                  </div>

                  {/* Undo/Redo buttons */}
                  <div className="flex items-center gap-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            onClick={undoRedo.undo}
                            disabled={!undoRedo.canUndo}
                            className="hidden sm:flex"
                          >
                            <Undo2 className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Undo (Ctrl+Z)</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            onClick={undoRedo.redo}
                            disabled={!undoRedo.canRedo}
                            className="hidden sm:flex"
                          >
                            <Redo2 className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Redo (Ctrl+Shift+Z)</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>
                {/* Summary badges */}
                {selectedRoundIndex !== null && rounds[selectedRoundIndex] && (
                  <div className="flex items-center gap-4 flex-wrap">
                    {validations[selectedRoundIndex] &&
                      (() => {
                        const round = rounds[selectedRoundIndex];
                        const regularInstruments = round.instruments.filter(
                          (inst) => !("pro_rata_type" in inst)
                        );
                        const proRataInstruments = round.instruments.filter(
                          (inst) => "pro_rata_type" in inst
                        );
                        const hasInstrumentsOrProRata =
                          regularInstruments.length > 0 ||
                          proRataInstruments.length > 0;
                        const isValid = validations[selectedRoundIndex].isValid;
                        const isComplete = isValid && hasInstrumentsOrProRata;

                        // Determine what's missing
                        let tooltipMessage = "";
                        if (!isComplete) {
                          if (!hasInstrumentsOrProRata) {
                            tooltipMessage =
                              "Add at least one instrument or pro-rata allocation to complete this round.";
                          } else if (!isValid) {
                            const errors =
                              validations[selectedRoundIndex].errors;
                            const errorFields = errors
                              .map((e) => e.field)
                              .filter((f) => f !== "instruments");
                            if (errorFields.length > 0) {
                              const fieldNames = errorFields.map((f) => {
                                if (f === "name") return "Round Name";
                                if (f === "round_date") return "Round Date";
                                if (f === "calculation_type")
                                  return "Round Type";
                                if (f === "valuation") return "Valuation";
                                if (f === "valuation_basis")
                                  return "Valuation Basis";
                                return f;
                              });
                              tooltipMessage = `Please fix: ${fieldNames.join(
                                ", "
                              )}`;
                            } else {
                              tooltipMessage =
                                "Please fix the validation errors to complete this round.";
                            }
                          }
                        }

                        const statusElement = (
                          <div className="flex items-center gap-2">
                            {isComplete ? (
                              <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 shrink-0" />
                            ) : (
                              <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
                            )}
                            <span className="text-sm text-muted-foreground">
                              {isComplete ? "Complete" : "Incomplete"}
                            </span>
                          </div>
                        );

                        if (!isComplete && tooltipMessage) {
                          return (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  {statusElement}
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>{tooltipMessage}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          );
                        }

                        return statusElement;
                      })()}
                    {(() => {
                      const round = rounds[selectedRoundIndex];
                      const regularInstruments = round.instruments.filter(
                        (inst) => !("pro_rata_type" in inst)
                      );
                      const instrumentsCount = regularInstruments.length;
                      const holdersCount = new Set(
                        regularInstruments
                          .filter(
                            (inst) => "holder_name" in inst && inst.holder_name
                          )
                          .map((inst) =>
                            "holder_name" in inst ? inst.holder_name : ""
                          )
                      ).size;
                      return (
                        <>
                          <Badge
                            variant="secondary"
                            className="text-xs font-medium"
                          >
                            <FileText className="h-3 w-3 mr-1" />
                            {instrumentsCount}{" "}
                            {instrumentsCount === 1
                              ? "instrument"
                              : "instruments"}
                          </Badge>
                          <Badge
                            variant="secondary"
                            className="text-xs font-medium"
                          >
                            <Users className="h-3 w-3 mr-1" />
                            {holdersCount}{" "}
                            {holdersCount === 1 ? "holder" : "holders"}
                          </Badge>
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
            )}

            {rounds.length === 0 ? (
              <Card className="border-border shadow-none">
                <CardContent className="pt-12 pb-12">
                  <div className="flex flex-col space-y-4">
                    <div className="rounded-full bg-primary/10 p-4 w-fit">
                      <Sparkles className="h-8 w-8 text-primary" />
                    </div>
                    <div className="space-y-1.5">
                      <h3 className="text-lg font-semibold">Get Started</h3>
                      <p className="text-muted-foreground max-w-md text-sm">
                        Create your first financing round to begin building your
                        capitalization table. You can add multiple rounds,
                        instruments, and pro-rata allocations.
                      </p>
                    </div>
                    <div className="flex gap-2 mt-2">
                      <Button
                        type="button"
                        onClick={addRound}
                        className="w-fit"
                      >
                        <Plus className="h-4 w-4" />
                        Add Round
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setJsonImportDialogOpen(true)}
                        className="w-fit"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Import JSON
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : selectedRoundIndex === null ? (
              <Card className="border-border/50 border-dashed shadow-none">
                <CardContent className="pt-12 pb-12">
                  <div className="flex flex-col items-center text-center space-y-4">
                    <div className="rounded-full bg-primary/10 p-4">
                      <TrendingUp className="h-8 w-8 text-primary" />
                    </div>
                    <div className="space-y-1.5">
                      <h3 className="text-lg font-semibold">Select a Round</h3>
                      <p className="text-muted-foreground max-w-md text-sm">
                        Select a round from the sidebar on the right to view and
                        edit its details.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <RoundsList
                rounds={rounds}
                holders={holders}
                validations={validations}
                usedGroups={usedGroups}
                usedClassNames={usedClassNames}
                onUpdate={updateRound}
                onAddHolder={addHolder}
                onUpdateHolder={updateHolder}
                onDelete={deleteRound}
                selectedRoundIndex={selectedRoundIndex}
                onUndo={undoRedo.undo}
                onRedo={undoRedo.redo}
                canUndo={undoRedo.canUndo}
                canRedo={undoRedo.canRedo}
              />
            )}
          </div>

          {isGenerating && (
            <Card className="mt-5 border-border/50 shadow-none">
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center justify-center gap-2">
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  <p className="text-sm">Generating Excel file...</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      {/* Desktop Sidebar */}
      <Sidebar
        holders={holders}
        rounds={rounds}
        validations={validations}
        selectedRoundIndex={selectedRoundIndex}
        onSelectRound={handleSelectRound}
        onEditHolder={handleEditHolder}
        onEditRound={handleEditRound}
        onDeleteHolder={deleteHolder}
        onDeleteRound={deleteRound}
        onAddRound={addRound}
        onAddHolder={handleAddHolderFromSidebar}
        onDownloadExcel={handleDownloadExcel}
        onCopyJson={handleCopyJson}
        onDownloadJson={handleDownloadJson}
        canDownload={canDownload}
        onReorderRounds={reorderRounds}
        onMoveHolderToGroup={moveHolderToGroup}
        onNavigateToError={handleNavigateToError}
        onUpdateRound={updateRound}
      />
      {/* Mobile Sidebar Drawer */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
          {/* Drawer */}
          <div className="absolute right-0 top-0 bottom-0 w-80 bg-muted/20 border-l flex flex-col h-full animate-in slide-in-from-right duration-300">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Menu</h2>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <div className="flex-1 overflow-auto">
              <div className="w-full">
                <Sidebar
                  holders={holders}
                  rounds={rounds}
                  validations={validations}
                  selectedRoundIndex={selectedRoundIndex}
                  onSelectRound={handleSelectRound}
                  onEditHolder={handleEditHolder}
                  onEditRound={handleEditRound}
                  onDeleteHolder={deleteHolder}
                  onDeleteRound={deleteRound}
                  onAddRound={addRound}
                  onAddHolder={handleAddHolderFromSidebar}
                  onDownloadExcel={handleDownloadExcel}
                  onCopyJson={handleCopyJson}
                  onDownloadJson={handleDownloadJson}
                  canDownload={canDownload}
                  onReorderRounds={reorderRounds}
                  onMoveHolderToGroup={moveHolderToGroup}
                  onNavigateToError={handleNavigateToError}
                  onUpdateRound={updateRound}
                  forceVisible={true}
                />
              </div>
            </div>
          </div>
        </div>
      )}
      <HolderDialog
        open={holderDialogOpen}
        onOpenChange={(open: boolean) => {
          setHolderDialogOpen(open);
          if (!open) {
            setEditingHolder(null);
          }
        }}
        holder={editingHolder}
        existingHolders={holders}
        onSave={handleSaveHolder}
        usedGroups={usedGroups}
      />
      <JsonImportDialog
        open={jsonImportDialogOpen}
        onOpenChange={setJsonImportDialogOpen}
        onImport={handleImportJson}
      />
    </div>
  );
}

// Rounds List Component
function RoundsList({
  rounds,
  holders,
  validations,
  usedGroups,
  usedClassNames,
  onUpdate,
  onAddHolder,
  onUpdateHolder,
  onDelete,
  selectedRoundIndex,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
}: {
  rounds: Round[];
  holders: Holder[];
  validations: import("@/lib/validation").RoundValidation[];
  usedGroups: string[];
  usedClassNames: string[];
  onUpdate: (index: number, round: Round) => void;
  onAddHolder: (holder: Holder) => void;
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  onDelete: (index: number) => void;
  selectedRoundIndex: number | null;
  onUndo?: () => void;
  onRedo?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
}) {
  if (selectedRoundIndex === null || selectedRoundIndex >= rounds.length) {
    return null;
  }

  const round = rounds[selectedRoundIndex];
  const validation = validations[selectedRoundIndex];

  return (
    <div className="space-y-0">
      <div
        key={`round-${selectedRoundIndex}`}
        id={`round-${selectedRoundIndex}`}
      >
        <RoundForm
          round={round}
          holders={holders}
          onUpdate={(updatedRound) =>
            onUpdate(selectedRoundIndex, updatedRound)
          }
          onAddHolder={onAddHolder}
          onUpdateHolder={onUpdateHolder}
          usedGroups={usedGroups}
          usedClassNames={usedClassNames}
          allRounds={rounds}
          roundIndex={selectedRoundIndex}
          onUpdateRound={onUpdate}
          onDelete={() => onDelete(selectedRoundIndex)}
          validation={validation}
          onUndo={onUndo}
          onRedo={onRedo}
          canUndo={canUndo}
          canRedo={canRedo}
        />
      </div>
    </div>
  );
}
