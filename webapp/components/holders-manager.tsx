"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Pencil, Users } from "lucide-react";
import type { Holder } from "@/types/cap-table";
import { HolderDialog } from "@/components/holder-dialog";

interface HoldersManagerProps {
  holders: Holder[];
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  usedGroups: string[];
}

export function HoldersManager({
  holders,
  onUpdateHolder,
  usedGroups,
}: HoldersManagerProps) {
  const [editingHolder, setEditingHolder] = React.useState<Holder | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);

  const handleEdit = (holder: Holder) => {
    setEditingHolder(holder);
    setDialogOpen(true);
  };

  const handleSave = (holder: Holder) => {
    if (editingHolder) {
      onUpdateHolder(editingHolder.name, holder);
      setDialogOpen(false);
      setEditingHolder(null);
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

    return { groups: Array.from(groups.entries()), ungrouped };
  }, [holders]);

  if (holders.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">
            No holders yet. Holders will be created as you add instruments.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            <CardTitle>Holders ({holders.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Grouped holders */}
            {groupedHolders.groups.map(([groupName, groupHolders]) => (
              <div key={groupName} className="space-y-2">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-sm">{groupName}</h4>
                  <Badge variant="secondary" className="text-xs">
                    {groupHolders.length}
                  </Badge>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {groupHolders.map((holder) => (
                    <div
                      key={holder.name}
                      className="flex items-center justify-between p-2 rounded-md border bg-muted/30 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{holder.name}</div>
                        {holder.description && (
                          <div className="text-xs text-muted-foreground truncate">
                            {holder.description}
                          </div>
                        )}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(holder)}
                        className="ml-2 shrink-0"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Ungrouped holders */}
            {groupedHolders.ungrouped.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-sm">Other</h4>
                  <Badge variant="secondary" className="text-xs">
                    {groupedHolders.ungrouped.length}
                  </Badge>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {groupedHolders.ungrouped.map((holder) => (
                    <div
                      key={holder.name}
                      className="flex items-center justify-between p-2 rounded-md border bg-muted/30 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{holder.name}</div>
                        {holder.description && (
                          <div className="text-xs text-muted-foreground truncate">
                            {holder.description}
                          </div>
                        )}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(holder)}
                        className="ml-2 shrink-0"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <HolderDialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) {
            setEditingHolder(null);
          }
        }}
        holder={editingHolder}
        existingHolders={holders}
        onSave={handleSave}
        usedGroups={usedGroups}
      />
    </>
  );
}

