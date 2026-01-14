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
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type Currency = "USD" | "EUR";

interface CurrencyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (currency: Currency) => void;
}

export function CurrencyDialog({
  open,
  onOpenChange,
  onConfirm,
}: CurrencyDialogProps) {
  const [selectedCurrency, setSelectedCurrency] =
    React.useState<Currency>("EUR");

  const handleConfirm = () => {
    onConfirm(selectedCurrency);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Select Currency Format</DialogTitle>
          <DialogDescription>
            Choose the currency format for the Excel export. This will affect
            how monetary values are displayed in the generated file.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <Select
            value={selectedCurrency}
            onValueChange={(value) => setSelectedCurrency(value as Currency)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select currency" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="EUR">EUR (€) - Euros</SelectItem>
              <SelectItem value="USD">USD ($) - US Dollars</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleConfirm}>Download</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
