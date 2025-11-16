"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RoundForm } from "@/components/round-form";
import { Sidebar } from "@/components/sidebar";
import { HolderDialog } from "@/components/holder-dialog";
import { Plus, Sparkles, GripVertical } from "lucide-react";
import { toast } from "sonner";
import type { Round, Holder, CapTableData } from "@/types/cap-table";
import { validateRound } from "@/lib/validation";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

export default function Home() {
  const [rounds, setRounds] = React.useState<Round[]>([]);
  const [holders, setHolders] = React.useState<Holder[]>([]);
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [expandedRounds, setExpandedRounds] = React.useState<Set<number>>(
    new Set([0])
  );
  const [editingHolder, setEditingHolder] = React.useState<Holder | null>(null);
  const [holderDialogOpen, setHolderDialogOpen] = React.useState(false);

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
    setExpandedRounds(new Set([...expandedRounds, newIndex]));
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
    const previousExpanded = new Set(expandedRounds);

    // Perform deletion
    setRounds(rounds.filter((_, i) => i !== index));
    const newExpanded = new Set(expandedRounds);
    newExpanded.delete(index);
    // Adjust indices
    const adjusted = new Set<number>();
    newExpanded.forEach((idx) => {
      if (idx < index) adjusted.add(idx);
      else if (idx > index) adjusted.add(idx - 1);
    });
    setExpandedRounds(adjusted);

    // Show toast with undo
    toast(`"${roundName}" has been removed.`, {
      description: 'Accident? Hit "Undo" to restore.',
      action: {
        label: "Undo",
        onClick: () => {
          setRounds(previousRounds);
          setExpandedRounds(previousExpanded);
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

  const duplicateRound = (index: number) => {
    const roundToDuplicate = rounds[index];
    const newRound: Round = {
      ...roundToDuplicate,
      name: `${roundToDuplicate.name} (Copy)`,
    };
    const newIndex = rounds.length;
    setRounds([...rounds, newRound]);
    setExpandedRounds(new Set([...expandedRounds, newIndex]));
  };

  const toggleRound = (index: number) => {
    const newExpanded = new Set(expandedRounds);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRounds(newExpanded);
  };

  const reorderRounds = (startIndex: number, endIndex: number) => {
    if (startIndex === endIndex) return;

    const newRounds = Array.from(rounds);
    const [removed] = newRounds.splice(startIndex, 1);
    newRounds.splice(endIndex, 0, removed);
    setRounds(newRounds);

    // Update expanded rounds indices
    const newExpanded = new Set<number>();
    expandedRounds.forEach((idx) => {
      if (idx === startIndex) {
        newExpanded.add(endIndex);
      } else if (startIndex < endIndex) {
        // Moving down
        if (idx > startIndex && idx <= endIndex) {
          newExpanded.add(idx - 1);
        } else {
          newExpanded.add(idx);
        }
      } else {
        // Moving up
        if (idx >= endIndex && idx < startIndex) {
          newExpanded.add(idx + 1);
        } else {
          newExpanded.add(idx);
        }
      }
    });
    setExpandedRounds(newExpanded);
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
    // Expand the round
    setExpandedRounds(new Set([index]));
    // Scroll to the round after a short delay
    setTimeout(() => {
      const element = document.getElementById(`round-${index}`);
      element?.scrollIntoView({ behavior: "smooth", block: "center" });
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
  const completedCount = validations.filter((v) => v.isValid).length;
  const progressPercentage =
    rounds.length > 0 ? (completedCount / rounds.length) * 100 : 0;

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
        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
          {/* Header with Progress Bar */}
          <div className="mb-8 space-y-4">
            <div>
              <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
                Cap Table Generator
              </h1>
              <p className="text-muted-foreground mt-2 text-base">
                Create your capitalization table by adding rounds and
                instruments
              </p>
            </div>

            {/* Progress Bar - More Prominent */}
            {rounds.length > 0 && (
              <div className="bg-card border rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">
                    Progress: {completedCount} of {rounds.length} rounds
                    complete
                  </span>
                  <span className="text-base font-semibold text-primary">
                    {Math.round(progressPercentage)}%
                  </span>
                </div>
                <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-500 rounded-full"
                    style={{ width: `${progressPercentage}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Rounds Section */}
          <div className="space-y-8">
            <div className="flex items-center justify-between border-b pb-3">
              <h2 className="text-3xl font-bold tracking-tight">Rounds</h2>
            </div>

            {rounds.length === 0 ? (
              <Card className="border-dashed shadow-sm">
                <CardContent className="pt-16 pb-16">
                  <div className="flex flex-col items-center text-center space-y-5">
                    <div className="rounded-full bg-primary/10 p-5">
                      <Sparkles className="h-10 w-10 text-primary" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-2xl font-semibold">Get Started</h3>
                      <p className="text-muted-foreground max-w-md text-base">
                        Create your first financing round to begin building your
                        capitalization table. You can add multiple rounds,
                        instruments, and pro-rata allocations.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <DraggableRoundsList
                rounds={rounds}
                holders={holders}
                expandedRounds={expandedRounds}
                validations={validations}
                usedGroups={usedGroups}
                usedClassNames={usedClassNames}
                onReorder={reorderRounds}
                onUpdate={updateRound}
                onAddHolder={addHolder}
                onUpdateHolder={updateHolder}
                onDelete={deleteRound}
                onDuplicate={duplicateRound}
                onToggleExpand={toggleRound}
              />
            )}

            <div className="flex justify-end pt-4">
              <Button
                onClick={addRound}
                size="lg"
                variant="default"
                className="shadow-md hover:shadow-lg transition-shadow"
              >
                <Plus className="h-5 w-5 mr-2" />
                Add Round
              </Button>
            </div>
          </div>

          {isGenerating && (
            <Card className="mt-6">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  <p>Generating Excel file...</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      <Sidebar
        holders={holders}
        rounds={rounds}
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

// Draggable Rounds List Component
function DraggableRoundsList({
  rounds,
  holders,
  expandedRounds,
  validations,
  usedGroups,
  usedClassNames,
  onReorder,
  onUpdate,
  onAddHolder,
  onUpdateHolder,
  onDelete,
  onDuplicate,
  onToggleExpand,
}: {
  rounds: Round[];
  holders: Holder[];
  expandedRounds: Set<number>;
  validations: ReturnType<typeof validateRound>[];
  usedGroups: string[];
  usedClassNames: string[];
  onReorder: (startIndex: number, endIndex: number) => void;
  onUpdate: (index: number, round: Round) => void;
  onAddHolder: (holder: Holder) => void;
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  onDelete: (index: number) => void;
  onDuplicate: (index: number) => void;
  onToggleExpand: (index: number) => void;
}) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = rounds.findIndex((_, i) => `round-${i}` === active.id);
      const newIndex = rounds.findIndex((_, i) => `round-${i}` === over.id);
      if (oldIndex !== -1 && newIndex !== -1) {
        onReorder(oldIndex, newIndex);
      }
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={rounds.map((_, i) => `round-${i}`)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-6">
          {rounds.map((round, index) => (
            <DraggableRoundItem
              key={`round-${index}`}
              id={`round-${index}`}
              round={round}
              index={index}
              holders={holders}
              isExpanded={expandedRounds.has(index)}
              validation={validations[index]}
              usedGroups={usedGroups}
              usedClassNames={usedClassNames}
              allRounds={rounds}
              onUpdate={onUpdate}
              onUpdateRound={onUpdate}
              onAddHolder={onAddHolder}
              onUpdateHolder={onUpdateHolder}
              onDelete={rounds.length > 1 ? onDelete : undefined}
              onDuplicate={onDuplicate}
              onToggleExpand={onToggleExpand}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}

// Draggable Round Item Component
function DraggableRoundItem({
  id,
  round,
  index,
  holders,
  isExpanded,
  validation,
  usedGroups,
  usedClassNames,
  allRounds,
  onUpdate,
  onUpdateRound,
  onAddHolder,
  onUpdateHolder,
  onDelete,
  onDuplicate,
  onToggleExpand,
}: {
  id: string;
  round: Round;
  index: number;
  holders: Holder[];
  isExpanded: boolean;
  validation?: ReturnType<typeof validateRound>;
  usedGroups: string[];
  usedClassNames: string[];
  allRounds: Round[];
  onUpdate: (index: number, round: Round) => void;
  onUpdateRound: (index: number, round: Round) => void;
  onAddHolder: (holder: Holder) => void;
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  onDelete?: (index: number) => void;
  onDuplicate: (index: number) => void;
  onToggleExpand: (index: number) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} id={`round-${index}`}>
      <div className="flex items-start gap-2">
        <div
          {...attributes}
          {...listeners}
          className="mt-2 cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground"
        >
          <GripVertical className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <RoundForm
            round={round}
            holders={holders}
            onUpdate={(updatedRound) => onUpdate(index, updatedRound)}
            onAddHolder={onAddHolder}
            onUpdateHolder={onUpdateHolder}
            usedGroups={usedGroups}
            usedClassNames={usedClassNames}
            allRounds={allRounds}
            roundIndex={index}
            onUpdateRound={onUpdateRound}
            onDelete={onDelete ? () => onDelete(index) : undefined}
            onDuplicate={() => onDuplicate(index)}
            isExpanded={isExpanded}
            onToggleExpand={() => onToggleExpand(index)}
            validation={validation}
          />
        </div>
      </div>
    </div>
  );
}
