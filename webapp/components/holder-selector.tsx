"use client";

import * as React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Plus, Pencil } from "lucide-react";
import type { Holder } from "@/types/cap-table";
import { HolderDialog } from "@/components/holder-dialog";

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
    if (editingHolder) {
      // Update existing holder
      onUpdateHolder(editingHolder.name, holder);
      // If the name changed, update the selected value
      if (editingHolder.name !== holder.name && value === editingHolder.name) {
        onChange(holder.name);
      }
    } else {
      // Create new holder
      onAddHolder(holder);
      onChange(holder.name);
    }
  };

  const selectedHolder = holders.find((h) => h.name === value);

  // If no holders exist, show a bigger "Add holder" button
  if (holders.length === 0 && allowCreate) {
    return (
      <>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-start h-9"
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

  return (
    <>
      <div className="flex gap-2">
        <Select value={value} onValueChange={onChange}>
          <SelectTrigger className="flex-1">
            <SelectValue placeholder={placeholder} />
          </SelectTrigger>
          <SelectContent>
            {holders.map((holder) => (
              <SelectItem key={holder.name} value={holder.name}>
                <div className="flex items-center justify-between w-full">
                  <span>
                    {holder.name}
                    {holder.group && (
                      <span className="text-muted-foreground ml-2">
                        ({holder.group})
                      </span>
                    )}
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedHolder && (
          <Button
            type="button"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handleEdit(selectedHolder.name);
            }}
            title="Edit holder"
          >
            <Pencil className="h-4 w-4" />
          </Button>
        )}
        {allowCreate && (
          <Button
            type="button"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handleCreateNew();
            }}
            title="Create new holder"
          >
            <Plus className="h-4 w-4" />
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
