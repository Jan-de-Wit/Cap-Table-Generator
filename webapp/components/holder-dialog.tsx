"use client";

import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import { FieldWithHelp } from "@/components/field-with-help";
import type { Holder } from "@/types/cap-table";
import { sortGroups } from "@/lib/utils";

interface HolderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  holder?: Holder | null;
  existingHolders: Holder[];
  onSave: (holder: Holder) => void;
  usedGroups: string[];
}

const COMMON_GROUPS = ["Founders", "ESOP", "Noteholders", "Investors"];

export function HolderDialog({
  open,
  onOpenChange,
  holder,
  existingHolders,
  onSave,
  usedGroups,
}: HolderDialogProps) {
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [group, setGroup] = React.useState<string>("");
  const [nameError, setNameError] = React.useState<string>("");

  // Initialize form when dialog opens or holder changes
  React.useEffect(() => {
    if (open) {
      if (holder) {
        setName(holder.name || "");
        setDescription(holder.description || "");
        setGroup(holder.group || "");
      } else {
        setName("");
        setDescription("");
        setGroup("");
      }
      setNameError("");
    }
  }, [open, holder]);

  // Real-time validation for duplicate holder names
  React.useEffect(() => {
    if (!open || !name.trim()) {
      setNameError("");
      return;
    }

    // Debounce validation
    const timeoutId = setTimeout(() => {
      const trimmedName = name.trim();
      
      // Check for duplicate names (excluding current holder if editing)
      const isDuplicate = existingHolders.some(
        (h) => 
          h.name.toLowerCase() === trimmedName.toLowerCase() && 
          h.name !== holder?.name
      );

      if (isDuplicate) {
        setNameError("A holder with this name already exists");
      } else {
        setNameError("");
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [name, existingHolders, holder, open]);

  // Get unique groups from existing holders and combine with common groups
  // Also include the currently typed group if it's a custom one
  const groupOptions = React.useMemo(() => {
    const allGroups = new Set<string>([
      ...COMMON_GROUPS,
      ...usedGroups,
      ...existingHolders
        .map((h) => h.group)
        .filter((g): g is string => !!g),
    ]);
    // Add the currently typed group if it's not empty and not already in the list
    if (group.trim() && !allGroups.has(group.trim())) {
      allGroups.add(group.trim());
    }
    // Sort groups in the specified order: Founders, ESOP, Noteholders, Investors, then custom groups alphabetically
    return sortGroups(Array.from(allGroups));
  }, [usedGroups, existingHolders, group]);

  const handleSave = () => {
    // Validate name
    if (!name.trim()) {
      setNameError("Holder name is required");
      return;
    }

    // Final check for duplicate names (excluding current holder if editing)
    const trimmedName = name.trim();
    const isDuplicate = existingHolders.some(
      (h) => 
        h.name.toLowerCase() === trimmedName.toLowerCase() && 
        h.name !== holder?.name
    );

    if (isDuplicate) {
      setNameError("A holder with this name already exists");
      return;
    }

    // Don't save if there's still an error
    if (nameError) {
      return;
    }

    const newHolder: Holder = {
      name: trimmedName,
      description: description.trim() || undefined,
      group: group.trim() || undefined,
    };

    onSave(newHolder);
    onOpenChange(false);
  };

  const isEditMode = !!holder;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "Edit Holder" : "Create New Holder"}
          </DialogTitle>
          <DialogDescription>
            {isEditMode
              ? "Update holder information. Changes will be reflected across all instruments using this holder."
              : "Add a new holder with optional description and group classification."}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <FieldWithHelp
            label="Holder Name"
            helpText="A unique identifier for this holder"
            required
            error={nameError}
            htmlFor="holder-name"
          >
            <Input
              id="holder-name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
              }}
              placeholder="e.g., John Doe, Acme Ventures"
              className={
                nameError
                  ? "border-destructive ring-destructive/20"
                  : "focus:ring-primary/20"
              }
              autoFocus
            />
          </FieldWithHelp>

          <FieldWithHelp
            label="Group"
            helpText="Optional classification for organizing holders (e.g., Founders, Investors, ESOP)"
            htmlFor="holder-group"
          >
            <Combobox
              options={groupOptions}
              value={group}
              onValueChange={setGroup}
              placeholder="Select or type a group..."
              searchPlaceholder="Search groups..."
              emptyText="No group found. Type to create a new one."
              allowCustom={true}
            />
          </FieldWithHelp>

          <FieldWithHelp
            label="Description"
            helpText="Optional additional information about this holder"
            htmlFor="holder-description"
          >
            <Textarea
              id="holder-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Co-founder and CEO"
              rows={3}
            />
          </FieldWithHelp>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="cursor-pointer">
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!name.trim() || !!nameError} className="cursor-pointer">
            {isEditMode ? "Save Changes" : "Create Holder"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

