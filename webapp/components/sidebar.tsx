"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Users,
  TrendingUp,
  Pencil,
  Plus,
  CheckCircle2,
  GripVertical,
  FileSpreadsheet,
  Download,
  Copy,
  ChevronUp,
  ChevronDown,
  Trash2,
} from "lucide-react";
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
  DragStartEvent,
  DragOverEvent,
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
  onDeleteHolder?: (holderName: string) => void;
  onDeleteRound?: (index: number) => void;
  onAddRound?: () => void;
  onAddHolder?: () => void;
  onDownloadExcel?: () => void;
  onCopyJson?: () => void;
  onDownloadJson?: () => void;
  canDownload?: boolean;
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
  onDeleteHolder,
  onDeleteRound,
  onAddRound,
  onAddHolder,
  onDownloadExcel,
  onCopyJson,
  onDownloadJson,
  canDownload = false,
  onReorderRounds,
  onMoveHolderToGroup,
}: SidebarProps) {
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [overId, setOverId] = React.useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // Require 8px of movement before drag starts
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragOver = (event: DragOverEvent) => {
    setOverId((event.over?.id as string) ?? null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    setOverId(null);
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
    if (active.id.toString().startsWith("holder-")) {
      let targetGroup: string | undefined;

      // Check if dropped on a group container
      if (over.id.toString().startsWith("group-")) {
        targetGroup = over.id.toString().replace("group-", "");
      }
      // Check if dropped on another holder card (use that holder's group)
      else if (over.id.toString().startsWith("holder-")) {
        const targetHolderName = over.id.toString().replace("holder-", "");
        const targetHolder = holders.find((h) => h.name === targetHolderName);
        if (targetHolder) {
          // Use the target holder's group, or "ungrouped" if no group
          targetGroup = targetHolder.group || "ungrouped";
        }
      }

      if (targetGroup !== undefined && onMoveHolderToGroup) {
        const holderName = active.id.toString().replace("holder-", "");
        onMoveHolderToGroup(
          holderName,
          targetGroup === "ungrouped" ? undefined : targetGroup
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
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="hidden lg:block w-80 border-l bg-muted/20 flex flex-col h-screen sticky top-0">
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto p-3 space-y-5">
            {/* Holders Section */}
            <div className="space-y-3 pt-4">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-base font-semibold">Holders</h2>
                <Badge variant="secondary" className="ml-auto text-xs">
                  {holders.length}
                </Badge>
              </div>

              {/* Grouped Holders */}
              {groupedHolders.groups.map(([groupName, groupHolders]) => (
                <DroppableGroup
                  key={groupName}
                  groupName={groupName}
                  activeId={activeId}
                  overId={overId}
                  holders={groupHolders}
                >
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
                          onDelete={onDeleteHolder}
                          isDragging={activeId === `holder-${holder.name}`}
                          groupName={groupName}
                          activeId={activeId}
                        />
                      ))}
                    </div>
                  </div>
                </DroppableGroup>
              ))}

              {/* Ungrouped Holders */}
              {groupedHolders.ungrouped.length > 0 && (
                <DroppableGroup
                  groupName="ungrouped"
                  activeId={activeId}
                  overId={overId}
                  holders={groupedHolders.ungrouped}
                >
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
                          onDelete={onDeleteHolder}
                          isDragging={activeId === `holder-${holder.name}`}
                          groupName="ungrouped"
                          activeId={activeId}
                        />
                      ))}
                    </div>
                  </div>
                </DroppableGroup>
              )}

              {holders.length === 0 && (
                <Card className="p-2.5 border-border/50 shadow-none transition-all hover:shadow-sm hover:border-border">
                  <p className="text-xs text-muted-foreground text-center">
                    No holders yet
                  </p>
                </Card>
              )}

              {onAddHolder && (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full text-xs"
                  size="sm"
                  onClick={onAddHolder}
                >
                  <Plus className="h-3.5 w-3.5 mr-1.5" />
                  Add Holder
                </Button>
              )}
            </div>

            {/* Rounds Section */}
            <div className="space-y-3 border-t pt-5">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-base font-semibold">Rounds</h2>
                <Badge variant="secondary" className="ml-auto text-xs">
                  {rounds.length}
                </Badge>
              </div>

              {rounds.length === 0 ? (
                <Card className="p-2.5 border-border/50 shadow-none transition-all hover:shadow-sm hover:border-border">
                  <p className="text-xs text-muted-foreground text-center">
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
                          onDelete={onDeleteRound}
                          isDragging={activeId === `sidebar-round-${index}`}
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
                  className="w-full text-xs"
                  size="sm"
                  onClick={onAddRound}
                >
                  <Plus className="h-3.5 w-3.5 mr-1.5" />
                  Add Round
                </Button>
              )}
            </div>
          </div>

          {/* Bottom Action Buttons */}
          {(onDownloadExcel || onCopyJson || onDownloadJson) && (
            <div className="border-t p-4">
              <div className="flex gap-2">
                {onDownloadExcel && (
                  <Button
                    type="button"
                    variant="default"
                    className="flex-1"
                    onClick={onDownloadExcel}
                    disabled={!canDownload}
                  >
                    <FileSpreadsheet className="h-4 w-4 mr-2" />
                    Download Excel
                  </Button>
                )}
                {(onCopyJson || onDownloadJson) && (
                  <JsonDropdownMenu
                    onCopyJson={onCopyJson}
                    onDownloadJson={onDownloadJson}
                    canDownload={canDownload}
                  />
                )}
              </div>
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
  onDelete,
  isDragging: externalIsDragging,
  groupName,
  activeId,
}: {
  holder: Holder;
  onEdit?: (holder: Holder) => void;
  onDelete?: (holderName: string) => void;
  isDragging?: boolean;
  groupName?: string;
  activeId?: string | null;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: internalIsDragging,
  } = useSortable({ id: `holder-${holder.name}` });

  // Make the card itself also a droppable zone for its group
  const { setNodeRef: setDroppableRef, isOver } = useDroppable({
    id: `holder-${holder.name}`,
    data: {
      groupName: groupName || "ungrouped",
    },
  });

  const isDragging = externalIsDragging || internalIsDragging;

  // Combine refs - both sortable and droppable need the same node
  const combinedRef = React.useCallback(
    (node: HTMLDivElement | null) => {
      setNodeRef(node);
      setDroppableRef(node);
    },
    [setNodeRef, setDroppableRef]
  );

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: isDragging ? undefined : transition,
    opacity: isDragging ? 0.4 : 1,
    zIndex: isDragging ? 50 : 1,
  };

  return (
    <div ref={combinedRef} style={style}>
      <Card
        className={`p-2.5 border-border/50 shadow-none transition-all ${
          isDragging
            ? "shadow-lg border-primary/50 scale-105"
            : "hover:shadow-sm hover:border-border"
        }`}
      >
        <div
          className={`flex justify-between gap-2 ${
            holder.description ? "items-start" : "items-center"
          }`}
        >
          <div
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing p-0.5 text-muted-foreground hover:text-foreground mr-0.5 touch-none"
          >
            <GripVertical className="h-4 w-4" />
          </div>
          <div className="space-y-0.5 flex-1 min-w-0">
            <div className="font-medium text-xs">{holder.name}</div>
            {holder.description && (
              <div className="text-xs text-muted-foreground line-clamp-2">
                {holder.description}
              </div>
            )}
          </div>
          <div className="flex gap-1 shrink-0">
            {onEdit && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0"
                onClick={() => onEdit(holder)}
                title="Edit holder"
              >
                <Pencil className="h-2.5 w-2.5" />
              </Button>
            )}
            {onDelete && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0 text-destructive hover:text-destructive"
                onClick={() => onDelete(holder.name)}
                title="Delete holder"
              >
                <Trash2 className="h-2.5 w-2.5" />
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}

// Droppable Group Component
function DroppableGroup({
  groupName,
  children,
  activeId,
  overId,
  holders,
}: {
  groupName: string;
  children: React.ReactNode;
  activeId?: string | null;
  overId?: string | null;
  holders: Holder[];
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: `group-${groupName}`,
  });

  const isDraggingHolder = activeId?.toString().startsWith("holder-");

  // Check if hovering over the group container directly
  const isOverGroup = isOver && isDraggingHolder;

  // Check if hovering over any holder card in this group
  const isOverHolderInGroup = React.useMemo(() => {
    if (!overId || !isDraggingHolder) return false;
    if (overId.toString().startsWith("holder-")) {
      const holderName = overId.toString().replace("holder-", "");
      return holders.some((h) => h.name === holderName);
    }
    return false;
  }, [overId, isDraggingHolder, holders]);

  const isActiveDropZone = isOverGroup || isOverHolderInGroup;

  return (
    <div
      ref={setNodeRef}
      className={`rounded-lg transition-all duration-200 ${
        isActiveDropZone
          ? "ring-2 ring-primary ring-offset-2 bg-primary/5 border-2 border-primary border-dashed"
          : isDraggingHolder
          ? "ring-1 ring-muted border border-dashed border-muted"
          : ""
      }`}
      style={{
        minHeight: isActiveDropZone ? "60px" : "auto",
        padding: isActiveDropZone ? "8px" : "0",
      }}
    >
      {children}
    </div>
  );
}

// JSON Dropdown Menu Component
function JsonDropdownMenu({
  onCopyJson,
  onDownloadJson,
  canDownload,
}: {
  onCopyJson?: () => void;
  onDownloadJson?: () => void;
  canDownload: boolean;
}) {
  const [open, setOpen] = React.useState(false);

  const handleCopy = () => {
    onCopyJson?.();
    setOpen(false);
  };

  const handleDownload = () => {
    onDownloadJson?.();
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="shrink-0"
          disabled={!canDownload}
        >
          {open ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-48 p-2">
        <div className="space-y-1">
          {onCopyJson && (
            <Button
              type="button"
              variant="ghost"
              className="w-full justify-start"
              onClick={handleCopy}
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy JSON
            </Button>
          )}
          {onDownloadJson && (
            <Button
              type="button"
              variant="ghost"
              className="w-full justify-start"
              onClick={handleDownload}
            >
              <Download className="h-4 w-4 mr-2" />
              Download JSON
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
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
  onDelete,
  isDragging: externalIsDragging,
}: {
  id: string;
  round: Round;
  index: number;
  roundHolders: Holder[];
  proRataHolders: Holder[];
  onEdit?: (index: number) => void;
  onDelete?: (index: number) => void;
  isDragging?: boolean;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: internalIsDragging,
  } = useSortable({ id });

  const isDragging = externalIsDragging || internalIsDragging;

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: isDragging ? undefined : transition,
    opacity: isDragging ? 0.4 : 1,
    zIndex: isDragging ? 50 : 1,
  };

  return (
    <div ref={setNodeRef} style={style}>
      <Card
        className={`p-3 border-border/50 shadow-none transition-all ${
          isDragging
            ? "shadow-lg border-primary/50 scale-105"
            : "hover:shadow-sm hover:border-border"
        }`}
      >
        <div className="space-y-2.5">
          <div className="flex items-start justify-between gap-2">
            <div
              {...attributes}
              {...listeners}
              className="cursor-grab active:cursor-grabbing p-0.5 text-muted-foreground hover:text-foreground touch-none"
            >
              <GripVertical className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-xs">
                {round.name || `Round ${index + 1}`}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5 mb-2">
                {round.round_date
                  ? new Date(round.round_date).toLocaleDateString()
                  : "No date"}
              </div>
              {roundHolders.length > 0 ? (
                <div className="space-y-1.5">
                  <div className="text-xs font-medium text-muted-foreground">
                    Holders ({roundHolders.length})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {roundHolders.map((holder) => (
                      <Badge
                        key={holder.name}
                        variant="outline"
                        className="text-xs py-0"
                      >
                        {holder.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">
                  No holders yet
                </div>
              )}

              {proRataHolders.length > 0 && (
                <div className="space-y-1.5 mt-2">
                  <div className="text-xs font-medium text-muted-foreground">
                    Pro-Rata ({proRataHolders.length})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {proRataHolders.map((holder) => (
                      <Badge
                        key={holder.name}
                        variant="secondary"
                        className="text-xs py-0"
                      >
                        {holder.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="flex gap-1 shrink-0">
              {onEdit && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0"
                  onClick={() => onEdit(index)}
                  title="Edit round"
                >
                  <Pencil className="h-2.5 w-2.5" />
                </Button>
              )}
              {onDelete && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 text-destructive hover:text-destructive"
                  onClick={() => onDelete(index)}
                  title="Delete round"
                >
                  <Trash2 className="h-2.5 w-2.5" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
