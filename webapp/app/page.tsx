"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { RoundForm } from "@/components/round-form";
import { Sidebar } from "@/components/sidebar";
import { HolderDialog } from "@/components/holder-dialog";
import { Plus, Sparkles, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import type { Round, Holder, CapTableData } from "@/types/cap-table";
import { validateRound } from "@/lib/validation";

export default function Home() {
  const [rounds, setRounds] = React.useState<Round[]>([]);
  const [holders, setHolders] = React.useState<Holder[]>([]);
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [editingHolder, setEditingHolder] = React.useState<Holder | null>(null);
  const [holderDialogOpen, setHolderDialogOpen] = React.useState(false);
  const [selectedRoundIndex, setSelectedRoundIndex] = React.useState<
    number | null
  >(null);

  // Infer new holders from rounds (only add if they don't exist)
  React.useEffect(() => {
    setHolders((prev) => {
      const holderNames = new Set(prev.map((h) => h.name));
      const newHolders: Holder[] = [];

      rounds.forEach((round) => {
        round.instruments.forEach((instrument) => {
          if ("holder_name" in instrument && instrument.holder_name) {
            if (!holderNames.has(instrument.holder_name)) {
              newHolders.push({
                name: instrument.holder_name,
              });
              holderNames.add(instrument.holder_name);
            }
          }
        });
      });

      return newHolders.length > 0 ? [...prev, ...newHolders] : prev;
    });
  }, [rounds]); // Only depend on rounds, not holders to avoid infinite loop

  const addRound = () => {
    const newRound: Round = {
      name: "",
      round_date: new Date().toISOString().split("T")[0],
      calculation_type: "fixed_shares",
      instruments: [],
    };
    const newIndex = rounds.length;
    setRounds([...rounds, newRound]);
    setSelectedRoundIndex(newIndex);

    toast.success("Round added", {
      description: `Round ${newIndex + 1} has been created.`,
    });
  };

  const updateRound = (index: number, round: Round) => {
    const updated = [...rounds];
    updated[index] = round;
    setRounds(updated);
  };

  const deleteRound = (index: number) => {
    const deletedRound = rounds[index];
    const roundName = deletedRound.name || `Round ${index + 1}`;

    // Store state for undo
    const previousRounds = [...rounds];
    const previousSelectedIndex = selectedRoundIndex;

    // Perform deletion
    setRounds(rounds.filter((_, i) => i !== index));

    // Update selected round index
    if (selectedRoundIndex === index) {
      // If we deleted the selected round, select the previous one or first one
      if (rounds.length > 1) {
        setSelectedRoundIndex(index > 0 ? index - 1 : 0);
      } else {
        setSelectedRoundIndex(null);
      }
    } else if (selectedRoundIndex !== null && selectedRoundIndex > index) {
      // If we deleted a round before the selected one, adjust the index
      setSelectedRoundIndex(selectedRoundIndex - 1);
    }

    // Show toast with undo
    toast(`"${roundName}" has been removed.`, {
      description: 'Accident? Hit "Undo" to restore.',
      action: {
        label: "Undo",
        onClick: () => {
          setRounds(previousRounds);
          setSelectedRoundIndex(previousSelectedIndex);
          toast.success("Round restored", {
            description: `"${roundName}" has been restored.`,
          });
        },
      },
    });
  };

  const deleteHolder = (holderName: string) => {
    const deletedHolder = holders.find((h) => h.name === holderName);
    if (!deletedHolder) return;

    // Store state for undo
    const previousHolders = [...holders];
    const previousRounds = rounds.map((round) => ({
      ...round,
      instruments: [...round.instruments],
    }));

    // Remove holder from holders list
    setHolders(holders.filter((h) => h.name !== holderName));

    // Remove all instruments that reference this holder from all rounds
    setRounds(
      rounds.map((round) => ({
        ...round,
        instruments: round.instruments.filter(
          (inst) => !("holder_name" in inst && inst.holder_name === holderName)
        ),
      }))
    );

    // Show toast with undo
    toast(`"${holderName}" has been removed.`, {
      description:
        "The holder and all associated instruments have been removed.",
      action: {
        label: "Undo",
        onClick: () => {
          setHolders(previousHolders);
          setRounds(previousRounds);
          toast.success("Holder restored", {
            description: `"${holderName}" and all instruments have been restored.`,
          });
        },
      },
    });
  };

  const reorderRounds = (startIndex: number, endIndex: number) => {
    if (startIndex === endIndex) return;

    const newRounds = Array.from(rounds);
    const [removed] = newRounds.splice(startIndex, 1);
    newRounds.splice(endIndex, 0, removed);
    setRounds(newRounds);

    // Update selected round index after reordering
    if (selectedRoundIndex === startIndex) {
      setSelectedRoundIndex(endIndex);
    } else if (selectedRoundIndex !== null) {
      // Adjust selected index if it's affected by the reorder
      if (startIndex < selectedRoundIndex && endIndex >= selectedRoundIndex) {
        setSelectedRoundIndex(selectedRoundIndex - 1);
      } else if (
        startIndex > selectedRoundIndex &&
        endIndex <= selectedRoundIndex
      ) {
        setSelectedRoundIndex(selectedRoundIndex + 1);
      }
    }
  };

  const moveHolderToGroup = (
    holderName: string,
    newGroup: string | undefined
  ) => {
    const holder = holders.find((h) => h.name === holderName);
    if (holder) {
      updateHolder(holderName, { ...holder, group: newGroup });
    }
  };

  const addHolder = (holder: Holder) => {
    if (!holders.find((h) => h.name === holder.name)) {
      setHolders([...holders, holder]);
      toast.success("Holder added", {
        description: `"${holder.name}" has been created.`,
      });
    }
  };

  const updateHolder = (oldName: string, updatedHolder: Holder) => {
    // Update holder in the holders list
    const updatedHolders = holders.map((h) =>
      h.name === oldName ? updatedHolder : h
    );
    setHolders(updatedHolders);

    // Update all references to this holder in rounds
    const updatedRounds = rounds.map((round) => ({
      ...round,
      instruments: round.instruments.map((inst) => {
        if ("holder_name" in inst && inst.holder_name === oldName) {
          return { ...inst, holder_name: updatedHolder.name };
        }
        return inst;
      }),
    }));
    setRounds(updatedRounds);
  };

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

  const handleEditHolder = (holder: Holder) => {
    setEditingHolder(holder);
    setHolderDialogOpen(true);
  };

  const handleEditRound = (index: number) => {
    // Select the round first
    setSelectedRoundIndex(index);
    // Scroll to the round after a short delay
    setTimeout(() => {
      const element = document.getElementById(`round-${index}`);
      element?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  };

  const handleNavigateToError = (roundIndex: number, field?: string) => {
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
  };

  const handleSaveHolder = (holder: Holder) => {
    if (editingHolder) {
      updateHolder(editingHolder.name, holder);
    } else {
      addHolder(holder);
    }
    setHolderDialogOpen(false);
    setEditingHolder(null);
  };

  const handleAddHolderFromSidebar = () => {
    setEditingHolder(null);
    setHolderDialogOpen(true);
  };

  const buildCapTableData = (): CapTableData => {
    return {
      schema_version: "2.0",
      holders,
      rounds,
    };
  };

  const handleDownloadExcel = async () => {
    setIsGenerating(true);
    try {
      const data = buildCapTableData();
      const response = await fetch("/api/generate-excel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || "Failed to generate Excel");
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
  };

  const validations = React.useMemo(
    () => rounds.map((round, index) => validateRound(round, rounds, index)),
    [rounds]
  );

  const canDownload = rounds.length > 0 && validations.every((v) => v.isValid);

  const handleCopyJson = () => {
    const data = buildCapTableData();
    const jsonString = JSON.stringify(data, null, 2);
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
  };

  const handleDownloadJson = () => {
    const data = buildCapTableData();
    const jsonString = JSON.stringify(data, null, 2);
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
  };

  return (
    <div className="min-h-screen bg-background flex">
      <div className="flex-1 overflow-auto">
        <div className="w-full max-w-3xl mx-auto p-3 sm:p-5 lg:p-6">
          {/* Header */}
          <div className="mb-6 pt-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">
                Cap Table Generator
              </h1>
              <p className="text-muted-foreground mt-1.5 text-sm">
                {selectedRoundIndex !== null && rounds[selectedRoundIndex]
                  ? `Editing: ${rounds[selectedRoundIndex].name || `Round ${selectedRoundIndex + 1}`}`
                  : "Select a round from the sidebar to edit"}
              </p>
            </div>
          </div>

          {/* Rounds Section */}
          <div className="space-y-5">
            <div className="flex items-center gap-2 border-b border-border/50 pb-2.5">
              <h2 className="text-base font-semibold">
                {selectedRoundIndex !== null && rounds[selectedRoundIndex]
                  ? `Editing: ${rounds[selectedRoundIndex].name || `Round ${selectedRoundIndex + 1}`}`
                  : "Select a Round"}
              </h2>
              {rounds.length > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {rounds.length}
                </Badge>
              )}
            </div>

            {rounds.length === 0 ? (
              <Card className="border-border/50 border-dashed shadow-none">
                <CardContent className="pt-12 pb-12">
                  <div className="flex flex-col items-center text-center space-y-4">
                    <div className="rounded-full bg-primary/10 p-4">
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
                        Select a round from the sidebar on the right to view and edit its
                        details.
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
      <Sidebar
        holders={holders}
        rounds={rounds}
        validations={validations}
        selectedRoundIndex={selectedRoundIndex}
        onSelectRound={setSelectedRoundIndex}
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
      />
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
}: {
  rounds: Round[];
  holders: Holder[];
  validations: ReturnType<typeof validateRound>[];
  usedGroups: string[];
  usedClassNames: string[];
  onUpdate: (index: number, round: Round) => void;
  onAddHolder: (holder: Holder) => void;
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  onDelete: (index: number) => void;
  selectedRoundIndex: number | null;
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
        />
      </div>
    </div>
  );
}
