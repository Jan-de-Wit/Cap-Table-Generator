"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Plus, Pencil } from "lucide-react";
import type { Holder } from "@/types/cap-table";
import { HolderDialog } from "@/components/holder-dialog";
import { sortGroups } from "@/lib/utils";
import { Combobox } from "@/components/ui/combobox";

interface HolderSelectorProps {
  value: string;
  onChange: (holderName: string) => void;
  holders: Holder[];
  onAddHolder: (holder: Holder) => void;
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  usedGroups: string[];
  placeholder?: string;
  allowCreate?: boolean;
}

export function HolderSelector({
  value,
  onChange,
  holders,
  onAddHolder,
  onUpdateHolder,
  usedGroups,
  placeholder = "Select or create holder",
  allowCreate = true,
}: HolderSelectorProps) {
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editingHolder, setEditingHolder] = React.useState<Holder | null>(null);

  const handleCreateNew = () => {
    setEditingHolder(null);
    setDialogOpen(true);
  };

  const handleEdit = (holderName: string) => {
    const holder = holders.find((h) => h.name === holderName);
    if (holder) {
      setEditingHolder(holder);
      setDialogOpen(true);
    }
  };

  const handleSave = (holder: Holder) => {
    // Check if this holder actually exists in the holders array
    const existingHolder = holders.find((h) => h.name === editingHolder?.name);

    if (editingHolder && existingHolder) {
      // Update existing holder
      onUpdateHolder(editingHolder.name, holder);
      // If the name changed, update the selected value
      if (editingHolder.name !== holder.name && value === editingHolder.name) {
        onChange(holder.name);
      }
    } else {
      // Create new holder (either no editingHolder or holder doesn't exist in array)
      onAddHolder(holder);
      onChange(holder.name);
    }
  };

  const selectedHolder = holders.find((h) => h.name === value);

  // Sort holders by group order, then alphabetically within each group, with ungrouped at the end
  const sortedHolders = React.useMemo(() => {
    const grouped = new Map<string, Holder[]>();
    const ungrouped: Holder[] = [];

    holders.forEach((holder) => {
      if (holder.group) {
        if (!grouped.has(holder.group)) {
          grouped.set(holder.group, []);
        }
        grouped.get(holder.group)!.push(holder);
      } else {
        ungrouped.push(holder);
      }
    });

    // Sort holders alphabetically within each group
    grouped.forEach((groupHolders) => {
      groupHolders.sort((a, b) => a.name.localeCompare(b.name));
    });

    // Sort ungrouped holders alphabetically
    ungrouped.sort((a, b) => a.name.localeCompare(b.name));

    // Sort groups in the specified order
    const groupEntries = Array.from(grouped.entries());
    const sortedGroupNames = sortGroups(groupEntries.map(([name]) => name));
    const sortedGroupedHolders: Holder[] = [];

    sortedGroupNames.forEach((groupName) => {
      const entry = groupEntries.find(([name]) => name === groupName);
      if (entry) {
        sortedGroupedHolders.push(...entry[1]);
      }
    });

    // Add ungrouped holders at the end
    return [...sortedGroupedHolders, ...ungrouped];
  }, [holders]);

  // Format holder options for Combobox
  const holderOptions = React.useMemo(() => {
    return sortedHolders.map((holder) => {
      const displayName = holder.group
        ? `${holder.name} (${holder.group})`
        : holder.name;
      return displayName;
    });
  }, [sortedHolders]);

  // Get the display value for the combobox
  const displayValue = React.useMemo(() => {
    const holder = sortedHolders.find((h) => h.name === value);
    if (!holder) return "";
    return holder.group ? `${holder.name} (${holder.group})` : holder.name;
  }, [value, sortedHolders]);

  // If no holders exist, show a bigger "Add holder" button
  if (holders.length === 0 && allowCreate) {
    return (
      <>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start h-9 cursor-pointer"
          onClick={(e) => {
            e.stopPropagation();
            handleCreateNew();
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Holder
        </Button>
        <HolderDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          holder={editingHolder}
          existingHolders={holders}
          onSave={handleSave}
          usedGroups={usedGroups}
        />
      </>
    );
  }

  const handleValueChange = (selectedDisplayValue: string) => {
    // Extract the holder name from the display value (remove group if present)
    const holderName = selectedDisplayValue.split(" (")[0];

    // Check if this is a new holder (not in existing holders)
    const existingHolder = holders.find((h) => h.name === holderName);

    if (!existingHolder && allowCreate) {
      // This is a new holder - create it and open the dialog for editing
      const newHolder: Holder = {
        name: holderName,
      };
      setEditingHolder(newHolder);
      setDialogOpen(true);
    } else {
      // Existing holder - just update the value
      onChange(holderName);
    }
  };

  return (
    <>
      <div className="flex gap-2">
        <div className="flex-1 min-w-0">
          <Combobox
            options={holderOptions}
            value={displayValue}
            onValueChange={handleValueChange}
            placeholder={placeholder}
            searchPlaceholder="Search holders..."
            emptyText="No holder found. Press Enter to create a new one."
            allowCustom={allowCreate}
          />
        </div>
        {selectedHolder && (
          <Button
            type="button"
            variant="outline"
            className="h-10 cursor-pointer shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              handleEdit(selectedHolder.name);
            }}
            title="Edit holder"
          >
            <Pencil className="h-4 w-4" />
          </Button>
        )}
      </div>
      <HolderDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        holder={editingHolder}
        existingHolders={holders}
        onSave={handleSave}
        usedGroups={usedGroups}
      />
    </>
  );
}
