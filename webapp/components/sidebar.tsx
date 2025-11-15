"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users, TrendingUp, Pencil, Plus, CheckCircle2 } from "lucide-react";
import type { Holder, Round } from "@/types/cap-table";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  useDroppable,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

interface SidebarProps {
  holders: Holder[];
  rounds: Round[];
  onEditHolder?: (holder: Holder) => void;
  onEditRound?: (index: number) => void;
  onAddRound?: () => void;
  onAddHolder?: () => void;
  onPreview?: () => void;
  canProceedToPreview?: boolean;
  onReorderRounds?: (startIndex: number, endIndex: number) => void;
  onMoveHolderToGroup?: (
    holderName: string,
    newGroup: string | undefined
  ) => void;
}

export function Sidebar({
  holders,
  rounds,
  onEditHolder,
  onEditRound,
  onAddRound,
  onAddHolder,
  onPreview,
  canProceedToPreview = false,
  onReorderRounds,
  onMoveHolderToGroup,
}: SidebarProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    // Handle round reordering
    if (
      active.id.toString().startsWith("sidebar-round-") &&
      over.id.toString().startsWith("sidebar-round-")
    ) {
      if (onReorderRounds && active.id !== over.id) {
        const oldIndex = parseInt(
          active.id.toString().replace("sidebar-round-", "")
        );
        const newIndex = parseInt(
          over.id.toString().replace("sidebar-round-", "")
        );
        if (!isNaN(oldIndex) && !isNaN(newIndex)) {
          onReorderRounds(oldIndex, newIndex);
        }
      }
      return;
    }

    // Handle holder group movement
    if (
      active.id.toString().startsWith("holder-") &&
      over.id.toString().startsWith("group-")
    ) {
      if (onMoveHolderToGroup) {
        const holderName = active.id.toString().replace("holder-", "");
        const newGroup = over.id.toString().replace("group-", "");
        onMoveHolderToGroup(
          holderName,
          newGroup === "ungrouped" ? undefined : newGroup
        );
      }
      return;
    }
  };
  // Group holders by group
  const groupedHolders = React.useMemo(() => {
    const groups = new Map<string, Holder[]>();
    const ungrouped: Holder[] = [];

    holders.forEach((holder) => {
      if (holder.group) {
        if (!groups.has(holder.group)) {
          groups.set(holder.group, []);
        }
        groups.get(holder.group)!.push(holder);
      } else {
        ungrouped.push(holder);
      }
    });

    // Sort holders alphabetically within each group
    groups.forEach((groupHolders, groupName) => {
      groupHolders.sort((a, b) => a.name.localeCompare(b.name));
    });

    // Sort ungrouped holders alphabetically
    ungrouped.sort((a, b) => a.name.localeCompare(b.name));

    return { groups: Array.from(groups.entries()), ungrouped };
  }, [holders]);

  // Get holders involved in each round (from regular instruments only)
  const getRoundHolders = (round: Round): Holder[] => {
    const holderNames = new Set<string>();
    round.instruments.forEach((instrument) => {
      // Only count regular instruments, not pro-rata allocations
      if (
        "holder_name" in instrument &&
        instrument.holder_name &&
        !("pro_rata_type" in instrument)
      ) {
        holderNames.add(instrument.holder_name);
      }
    });
    return holders.filter((h) => holderNames.has(h.name));
  };

  // Get holders who exercised pro-rata rights in each round
  const getProRataHolders = (round: Round): Holder[] => {
    const holderNames = new Set<string>();
    round.instruments.forEach((instrument) => {
      // Only count pro-rata allocations
      if (
        "holder_name" in instrument &&
        instrument.holder_name &&
        "pro_rata_type" in instrument
      ) {
        holderNames.add(instrument.holder_name);
      }
    });
    return holders.filter((h) => holderNames.has(h.name));
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <div className="hidden lg:block w-80 border-l bg-muted/30 flex flex-col h-screen sticky top-0">
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* Holders Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Holders</h2>
                <Badge variant="secondary" className="ml-auto">
                  {holders.length}
                </Badge>
              </div>

              {/* Grouped Holders */}
              {groupedHolders.groups.map(([groupName, groupHolders]) => (
                <DroppableGroup key={groupName} groupName={groupName}>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-muted-foreground">
                        {groupName}
                      </h3>
                      <Badge variant="outline" className="text-xs">
                        {groupHolders.length}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      {groupHolders.map((holder) => (
                        <DraggableHolder
                          key={holder.name}
                          holder={holder}
                          onEdit={onEditHolder}
                        />
                      ))}
                    </div>
                  </div>
                </DroppableGroup>
              ))}

              {/* Ungrouped Holders */}
              {groupedHolders.ungrouped.length > 0 && (
                <DroppableGroup groupName="ungrouped">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-muted-foreground">
                        Other
                      </h3>
                      <Badge variant="outline" className="text-xs">
                        {groupedHolders.ungrouped.length}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      {groupedHolders.ungrouped.map((holder) => (
                        <DraggableHolder
                          key={holder.name}
                          holder={holder}
                          onEdit={onEditHolder}
                        />
                      ))}
                    </div>
                  </div>
                </DroppableGroup>
              )}

              {holders.length === 0 && (
                <Card className="p-4">
                  <p className="text-sm text-muted-foreground text-center">
                    No holders yet
                  </p>
                </Card>
              )}

              {onAddHolder && (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  size="sm"
                  onClick={onAddHolder}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Holder
                </Button>
              )}
            </div>

            {/* Rounds Section */}
            <div className="space-y-4 border-t pt-6">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Rounds</h2>
                <Badge variant="secondary" className="ml-auto">
                  {rounds.length}
                </Badge>
              </div>

              {rounds.length === 0 ? (
                <Card className="p-4">
                  <p className="text-sm text-muted-foreground text-center">
                    No rounds yet
                  </p>
                </Card>
              ) : (
                <SortableContext
                  items={rounds.map((_, i) => `sidebar-round-${i}`)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-3">
                    {rounds.map((round, index) => {
                      const roundHolders = getRoundHolders(round);
                      const proRataHolders = getProRataHolders(round);
                      return (
                        <DraggableRoundSidebar
                          key={index}
                          id={`sidebar-round-${index}`}
                          round={round}
                          index={index}
                          roundHolders={roundHolders}
                          proRataHolders={proRataHolders}
                          onEdit={onEditRound}
                        />
                      );
                    })}
                  </div>
                </SortableContext>
              )}
              
              {onAddRound && (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  size="sm"
                  onClick={onAddRound}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Round
                </Button>
              )}
            </div>
          </div>

          {/* Bottom Action Button */}
          {onPreview && (
            <div className="border-t p-4">
              <Button
                type="button"
                variant="default"
                className="w-full"
                onClick={onPreview}
                disabled={!canProceedToPreview}
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Preview & Download
              </Button>
            </div>
          )}
        </div>
      </div>
    </DndContext>
  );
}

// Draggable Holder Component
function DraggableHolder({
  holder,
  onEdit,
}: {
  holder: Holder;
  onEdit?: (holder: Holder) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: `holder-${holder.name}` });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style}>
      <Card className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground mr-1"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle cx="3" cy="3" r="1" fill="currentColor" />
              <circle cx="9" cy="3" r="1" fill="currentColor" />
              <circle cx="3" cy="6" r="1" fill="currentColor" />
              <circle cx="9" cy="6" r="1" fill="currentColor" />
              <circle cx="3" cy="9" r="1" fill="currentColor" />
              <circle cx="9" cy="9" r="1" fill="currentColor" />
            </svg>
          </div>
          <div className="space-y-1 flex-1 min-w-0">
            <div className="font-medium text-sm">{holder.name}</div>
            {holder.description && (
              <div className="text-xs text-muted-foreground line-clamp-2">
                {holder.description}
              </div>
            )}
          </div>
          {onEdit && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 shrink-0"
              onClick={() => onEdit(holder)}
              title="Edit holder"
            >
              <Pencil className="h-3 w-3" />
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}

// Droppable Group Component
function DroppableGroup({
  groupName,
  children,
}: {
  groupName: string;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: `group-${groupName}`,
  });

  return (
    <div
      ref={setNodeRef}
      className={isOver ? "ring-2 ring-primary rounded-lg p-1" : ""}
    >
      {children}
    </div>
  );
}

// Draggable Round Sidebar Component
function DraggableRoundSidebar({
  id,
  round,
  index,
  roundHolders,
  proRataHolders,
  onEdit,
}: {
  id: string;
  round: Round;
  index: number;
  roundHolders: Holder[];
  proRataHolders: Holder[];
  onEdit?: (index: number) => void;
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
    <div ref={setNodeRef} style={style}>
      <Card className="p-4">
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div
              {...attributes}
              {...listeners}
              className="cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground"
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 12 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle cx="3" cy="3" r="1" fill="currentColor" />
                <circle cx="9" cy="3" r="1" fill="currentColor" />
                <circle cx="3" cy="6" r="1" fill="currentColor" />
                <circle cx="9" cy="6" r="1" fill="currentColor" />
                <circle cx="3" cy="9" r="1" fill="currentColor" />
                <circle cx="9" cy="9" r="1" fill="currentColor" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm">
                {round.name || `Round ${index + 1}`}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {round.round_date
                  ? new Date(round.round_date).toLocaleDateString()
                  : "No date"}
              </div>
            </div>
            {onEdit && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 shrink-0"
                onClick={() => onEdit(index)}
                title="Edit round"
              >
                <Pencil className="h-3 w-3" />
              </Button>
            )}
          </div>

          {roundHolders.length > 0 ? (
            <div className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground">
                Involved Holders ({roundHolders.length}):
              </div>
              <div className="flex flex-wrap gap-1.5">
                {roundHolders.map((holder) => (
                  <Badge
                    key={holder.name}
                    variant="outline"
                    className="text-xs"
                  >
                    {holder.name}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">No holders yet</div>
          )}

          {proRataHolders.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground">
                Exercised Pro-Rata Rights ({proRataHolders.length}):
              </div>
              <div className="flex flex-wrap gap-1.5">
                {proRataHolders.map((holder) => (
                  <Badge
                    key={holder.name}
                    variant="secondary"
                    className="text-xs"
                  >
                    {holder.name}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
