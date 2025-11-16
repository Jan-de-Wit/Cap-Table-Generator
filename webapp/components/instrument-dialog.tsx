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
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { HolderSelector } from "@/components/holder-selector";
import { FieldWithHelp } from "@/components/field-with-help";
import { Combobox } from "@/components/ui/combobox";
import type {
  Instrument,
  Holder,
  CalculationType,
  InterestType,
  ProRataType,
} from "@/types/cap-table";
import {
  formatCurrency,
  formatNumber,
  decimalToPercentage,
  percentageToDecimal,
  parseFormattedNumber,
} from "@/lib/formatters";

interface InstrumentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  instrument: Instrument | null;
  calculationType: CalculationType;
  holders: Holder[];
  onSave: (instrument: Instrument) => void;
  onAddHolder: (holder: Holder) => void;
  onUpdateHolder: (oldName: string, holder: Holder) => void;
  usedGroups: string[];
  usedClassNames: string[];
  isProRata?: boolean;
}

export function InstrumentDialog({
  open,
  onOpenChange,
  instrument,
  calculationType,
  holders,
  onSave,
  onAddHolder,
  onUpdateHolder,
  usedGroups,
  usedClassNames,
  isProRata = false,
}: InstrumentDialogProps) {
  const [formData, setFormData] = React.useState<Partial<Instrument>>({});
  const [touchedFields, setTouchedFields] = React.useState<Set<string>>(new Set());
  const [className, setClassName] = React.useState<string>("");
  const classNameInputRef = React.useRef<HTMLInputElement>(null);

  // Initialize form when dialog opens
  React.useEffect(() => {
    if (open) {
      if (instrument) {
        setFormData(instrument);
        setClassName(instrument.class_name || "");
      } else {
        // Create empty instrument based on type
        if (isProRata) {
          setFormData({
            holder_name: "",
            class_name: "",
            pro_rata_type: "standard",
          });
        } else {
          setClassName("");
          const base: Partial<Instrument> = {
            holder_name: "",
            class_name: "",
          };
          switch (calculationType) {
            case "fixed_shares":
              setFormData({ ...base, initial_quantity: 0 });
              break;
            case "target_percentage":
              setFormData({ ...base, target_percentage: 0 });
              break;
            case "valuation_based":
              setFormData({ ...base, investment_amount: 0 });
              break;
            case "convertible":
              setFormData({
                ...base,
                investment_amount: 0,
                interest_rate: 0,
                payment_date: "",
                expected_conversion_date: "",
                interest_type: "simple",
                discount_rate: 0,
              });
              break;
            case "safe":
              setFormData({
                ...base,
                investment_amount: 0,
                expected_conversion_date: "",
                discount_rate: 0,
              });
              break;
          }
        }
      }
      setTouchedFields(new Set());
    }
  }, [open, instrument, calculationType, isProRata]);

  const updateField = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setTouchedFields((prev) => new Set([...prev, field]));
    if (field === "class_name") {
      setClassName(value || "");
    }
  };

  // Get class name options (used class names + currently typed value)
  const classNameOptions = React.useMemo(() => {
    const options = new Set<string>(usedClassNames);
    // Add the currently typed class name if it's not empty and not already in the list
    if (className.trim() && !options.has(className.trim())) {
      options.add(className.trim());
    }
    return Array.from(options).sort();
  }, [usedClassNames, className]);

  const handleSave = () => {
    if (!formData.holder_name || !formData.class_name) {
      return;
    }
    onSave(formData as Instrument);
    onOpenChange(false);
  };

  const isEditMode = !!instrument;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditMode
              ? isProRata
                ? "Edit Pro-Rata Allocation"
                : "Edit Instrument"
              : isProRata
              ? "Create Pro-Rata Allocation"
              : "Create Instrument"}
          </DialogTitle>
          <DialogDescription>
            {isEditMode
              ? "Update instrument details"
              : "Add a new instrument to this round"}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <FieldWithHelp
              label="Holder"
              helpText={
                isProRata
                  ? "Select a holder who has shares in previous rounds"
                  : "Select an existing holder or create a new one"
              }
              required
              htmlFor="instrument-holder"
            >
              <HolderSelector
                value={formData.holder_name || ""}
                onChange={(name) => updateField("holder_name", name)}
                holders={holders}
                onAddHolder={onAddHolder}
                onUpdateHolder={onUpdateHolder}
                usedGroups={usedGroups}
                allowCreate={!isProRata}
              />
            </FieldWithHelp>
            <FieldWithHelp
              label="Class Name"
              helpText="The security class name (e.g., 'Series A Preferred', 'Common Stock')"
              required
              htmlFor="instrument-class"
            >
              {usedClassNames.length === 0 ? (
                <>
                  <Input
                    ref={classNameInputRef}
                    id="instrument-class"
                    type="text"
                    value={className}
                    onChange={(e) => {
                      const value = e.target.value;
                      setClassName(value);
                      updateField("class_name", value);
                    }}
                    placeholder="Type a class name (e.g., 'Series A Preferred')"
                    onBlur={() =>
                      setTouchedFields((prev) => new Set([...prev, "class_name"]))
                    }
                  />
                </>
              ) : (
                <Combobox
                  options={classNameOptions}
                  value={className}
                  onValueChange={(value) => {
                    setClassName(value);
                    updateField("class_name", value);
                  }}
                  placeholder="Select or type a class name..."
                  searchPlaceholder="Search class names..."
                  emptyText="No class name found. Type to create a new one."
                  allowCustom={true}
                />
              )}
            </FieldWithHelp>
          </div>

          {isProRata ? (
            <>
              <FieldWithHelp
                label="Pro-Rata Type"
                helpText="Standard: maintain ownership. Super: can exceed ownership up to specified percentage."
                required
                htmlFor="pro-rata-type"
              >
                <Select
                  value={(formData as any).pro_rata_type || "standard"}
                  onValueChange={(value: ProRataType) => {
                    const updates: any = { pro_rata_type: value };
                    if (value !== "super") {
                      updates.pro_rata_percentage = undefined;
                    }
                    setFormData((prev) => ({ ...prev, ...updates }));
                    setTouchedFields((prev) => new Set([...prev, "pro_rata_type"]));
                  }}
                >
                  <SelectTrigger id="pro-rata-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="super">Super</SelectItem>
                  </SelectContent>
                </Select>
              </FieldWithHelp>
              {(formData as any).pro_rata_type === "super" && (
                <FieldWithHelp
                  label="Pro-Rata Percentage"
                  helpText="Maximum ownership percentage for super pro-rata (0-100%)"
                  required
                  htmlFor="pro-rata-percentage"
                >
                  <div className="flex items-center gap-2">
                    <Input
                      id="pro-rata-percentage"
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      value={
                        (formData as any).pro_rata_percentage
                          ? decimalToPercentage((formData as any).pro_rata_percentage)
                          : ""
                      }
                      onChange={(e) => {
                        const percentage = e.target.value ? parseFloat(e.target.value) : 0;
                        updateField(
                          "pro_rata_percentage",
                          percentageToDecimal(percentage)
                        );
                      }}
                      onBlur={() =>
                        setTouchedFields((prev) => new Set([...prev, "pro_rata_percentage"]))
                      }
                      placeholder="e.g., 15 for 15%"
                    />
                    <span className="text-muted-foreground">%</span>
                  </div>
                </FieldWithHelp>
              )}
            </>
          ) : (
            <>
              {calculationType === "fixed_shares" && (
                <FieldWithHelp
                  label="Initial Quantity"
                  helpText="The number of shares to issue"
                  required
                  htmlFor="initial-quantity"
                >
                  <Input
                    id="initial-quantity"
                    type="text"
                    value={
                      (formData as any).initial_quantity
                        ? formatNumber((formData as any).initial_quantity)
                        : ""
                    }
                    onChange={(e) => {
                      const parsed = parseFormattedNumber(e.target.value);
                      updateField("initial_quantity", parsed > 0 ? parsed : 0);
                    }}
                    onBlur={() =>
                      setTouchedFields((prev) => new Set([...prev, "initial_quantity"]))
                    }
                    placeholder="e.g., 1,000,000"
                  />
                </FieldWithHelp>
              )}

              {calculationType === "target_percentage" && (
                <FieldWithHelp
                  label="Target Percentage"
                  helpText="Target ownership percentage (0-100%)"
                  required
                  htmlFor="target-percentage"
                >
                  <div className="flex items-center gap-2">
                    <Input
                      id="target-percentage"
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      value={
                        (formData as any).target_percentage
                          ? decimalToPercentage((formData as any).target_percentage)
                          : ""
                      }
                      onChange={(e) => {
                        const percentage = e.target.value ? parseFloat(e.target.value) : 0;
                        updateField("target_percentage", percentageToDecimal(percentage));
                      }}
                      onBlur={() =>
                        setTouchedFields((prev) => new Set([...prev, "target_percentage"]))
                      }
                      placeholder="e.g., 20 for 20%"
                    />
                    <span className="text-muted-foreground">%</span>
                  </div>
                </FieldWithHelp>
              )}

              {calculationType === "valuation_based" && (
                <FieldWithHelp
                  label="Investment Amount"
                  helpText="The amount invested in this round"
                  required
                  htmlFor="investment-amount"
                >
                  <Input
                    id="investment-amount"
                    type="text"
                    value={
                      (formData as any).investment_amount
                        ? formatCurrency((formData as any).investment_amount)
                        : ""
                    }
                    onChange={(e) => {
                      const parsed = parseFormattedNumber(e.target.value);
                      updateField("investment_amount", parsed > 0 ? parsed : 0);
                    }}
                    onBlur={() =>
                      setTouchedFields((prev) => new Set([...prev, "investment_amount"]))
                    }
                    placeholder="e.g., $2,000,000"
                  />
                </FieldWithHelp>
              )}

              {calculationType === "convertible" && (
                <div className="grid grid-cols-2 gap-4">
                  <FieldWithHelp
                    label="Investment Amount"
                    helpText="Principal amount invested"
                    required
                    htmlFor="convertible-investment"
                  >
                    <Input
                      id="convertible-investment"
                      type="text"
                      value={
                        (formData as any).investment_amount
                          ? formatCurrency((formData as any).investment_amount)
                          : ""
                      }
                      onChange={(e) => {
                        const parsed = parseFormattedNumber(e.target.value);
                        updateField("investment_amount", parsed > 0 ? parsed : 0);
                      }}
                      onBlur={() =>
                        setTouchedFields((prev) => new Set([...prev, "investment_amount"]))
                      }
                    />
                  </FieldWithHelp>
                  <FieldWithHelp
                    label="Interest Rate"
                    helpText="Annual interest rate as percentage (0-100%)"
                    required
                    htmlFor="interest-rate"
                  >
                    <div className="flex items-center gap-2">
                      <Input
                        id="interest-rate"
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={
                          (formData as any).interest_rate
                            ? decimalToPercentage((formData as any).interest_rate)
                            : ""
                        }
                        onChange={(e) => {
                          const percentage = e.target.value ? parseFloat(e.target.value) : 0;
                          updateField("interest_rate", percentageToDecimal(percentage));
                        }}
                        onBlur={() =>
                          setTouchedFields((prev) => new Set([...prev, "interest_rate"]))
                        }
                        placeholder="e.g., 8 for 8%"
                      />
                      <span className="text-muted-foreground">%</span>
                    </div>
                  </FieldWithHelp>
                  <FieldWithHelp
                    label="Payment Date"
                    helpText="Date when the investment was made"
                    required
                    htmlFor="payment-date"
                  >
                    <Input
                      id="payment-date"
                      type="date"
                      value={(formData as any).payment_date || ""}
                      onChange={(e) => updateField("payment_date", e.target.value)}
                      onBlur={() =>
                        setTouchedFields((prev) => new Set([...prev, "payment_date"]))
                      }
                    />
                  </FieldWithHelp>
                  <FieldWithHelp
                    label="Expected Conversion Date"
                    helpText="Expected date when the convertible will convert"
                    required
                    htmlFor="expected-conversion-date"
                  >
                    <Input
                      id="expected-conversion-date"
                      type="date"
                      value={(formData as any).expected_conversion_date || ""}
                      onChange={(e) => updateField("expected_conversion_date", e.target.value)}
                      onBlur={() =>
                        setTouchedFields((prev) =>
                          new Set([...prev, "expected_conversion_date"])
                        )
                      }
                    />
                  </FieldWithHelp>
                  <FieldWithHelp
                    label="Interest Type"
                    helpText="How interest is calculated over time"
                    required
                    htmlFor="interest-type"
                  >
                    <Select
                      value={(formData as any).interest_type || "simple"}
                      onValueChange={(value: InterestType) => {
                        updateField("interest_type", value);
                        setTouchedFields((prev) => new Set([...prev, "interest_type"]));
                      }}
                    >
                      <SelectTrigger id="interest-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="simple">Simple</SelectItem>
                        <SelectItem value="compound_yearly">Compound Yearly</SelectItem>
                        <SelectItem value="compound_monthly">Compound Monthly</SelectItem>
                        <SelectItem value="compound_daily">Compound Daily</SelectItem>
                        <SelectItem value="no_interest">No Interest</SelectItem>
                      </SelectContent>
                    </Select>
                  </FieldWithHelp>
                  <FieldWithHelp
                    label="Discount Rate"
                    helpText="Discount percentage applied at conversion (0-100%)"
                    required
                    htmlFor="discount-rate"
                  >
                    <div className="flex items-center gap-2">
                      <Input
                        id="discount-rate"
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={
                          (formData as any).discount_rate
                            ? decimalToPercentage((formData as any).discount_rate)
                            : ""
                        }
                        onChange={(e) => {
                          const percentage = e.target.value ? parseFloat(e.target.value) : 0;
                          updateField("discount_rate", percentageToDecimal(percentage));
                        }}
                        onBlur={() =>
                          setTouchedFields((prev) => new Set([...prev, "discount_rate"]))
                        }
                        placeholder="e.g., 20 for 20%"
                      />
                      <span className="text-muted-foreground">%</span>
                    </div>
                  </FieldWithHelp>
                </div>
              )}

              {calculationType === "safe" && (
                <div className="grid grid-cols-2 gap-4">
                  <FieldWithHelp
                    label="Investment Amount"
                    helpText="Principal amount invested"
                    required
                    htmlFor="safe-investment"
                  >
                    <Input
                      id="safe-investment"
                      type="text"
                      value={
                        (formData as any).investment_amount
                          ? formatCurrency((formData as any).investment_amount)
                          : ""
                      }
                      onChange={(e) => {
                        const parsed = parseFormattedNumber(e.target.value);
                        updateField("investment_amount", parsed > 0 ? parsed : 0);
                      }}
                      onBlur={() =>
                        setTouchedFields((prev) => new Set([...prev, "investment_amount"]))
                      }
                    />
                  </FieldWithHelp>
                  <FieldWithHelp
                    label="Expected Conversion Date"
                    helpText="Expected date when the SAFE will convert"
                    required
                    htmlFor="safe-conversion-date"
                  >
                    <Input
                      id="safe-conversion-date"
                      type="date"
                      value={(formData as any).expected_conversion_date || ""}
                      onChange={(e) => updateField("expected_conversion_date", e.target.value)}
                      onBlur={() =>
                        setTouchedFields((prev) =>
                          new Set([...prev, "expected_conversion_date"])
                        )
                      }
                    />
                  </FieldWithHelp>
                  <FieldWithHelp
                    label="Discount Rate"
                    helpText="Discount percentage applied at conversion (0-100%)"
                    required
                    htmlFor="safe-discount-rate"
                  >
                    <div className="flex items-center gap-2">
                      <Input
                        id="safe-discount-rate"
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={
                          (formData as any).discount_rate
                            ? decimalToPercentage((formData as any).discount_rate)
                            : ""
                        }
                        onChange={(e) => {
                          const percentage = e.target.value ? parseFloat(e.target.value) : 0;
                          updateField("discount_rate", percentageToDecimal(percentage));
                        }}
                        onBlur={() =>
                          setTouchedFields((prev) => new Set([...prev, "discount_rate"]))
                        }
                        placeholder="e.g., 20 for 20%"
                      />
                      <span className="text-muted-foreground">%</span>
                    </div>
                  </FieldWithHelp>
                </div>
              )}

              {/* Pro-Rata Rights Field (for non-pro-rata instruments) */}
              {!isProRata && (
                <>
                  <FieldWithHelp
                    label="Pro-Rata Rights"
                    helpText="Does this shareholder receive pro-rata rights in future rounds?"
                    htmlFor="pro-rata-rights"
                  >
                    <Select
                      value={(formData as any).pro_rata_rights || "none"}
                      onValueChange={(value: "standard" | "super" | "none") => {
                        const updates: any = { pro_rata_rights: value === "none" ? undefined : value };
                        if (value !== "super") {
                          updates.pro_rata_percentage = undefined;
                        }
                        setFormData((prev) => ({ ...prev, ...updates }));
                      }}
                    >
                      <SelectTrigger id="pro-rata-rights">
                        <SelectValue placeholder="No pro-rata rights" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No pro-rata rights</SelectItem>
                        <SelectItem value="standard">Standard Pro-Rata</SelectItem>
                        <SelectItem value="super">Super Pro-Rata</SelectItem>
                      </SelectContent>
                    </Select>
                  </FieldWithHelp>
                  {(formData as any).pro_rata_rights === "super" && (
                    <FieldWithHelp
                      label="Super Pro-Rata Percentage"
                      helpText="Maximum ownership percentage for super pro-rata (0-100%)"
                      required
                      htmlFor="super-pro-rata-percentage"
                    >
                      <div className="flex items-center gap-2">
                        <Input
                          id="super-pro-rata-percentage"
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                          value={
                            (formData as any).pro_rata_percentage
                              ? decimalToPercentage((formData as any).pro_rata_percentage)
                              : ""
                          }
                          onChange={(e) => {
                            const percentage = e.target.value ? parseFloat(e.target.value) : 0;
                            updateField(
                              "pro_rata_percentage",
                              percentageToDecimal(percentage)
                            );
                          }}
                          onBlur={() =>
                            setTouchedFields((prev) => new Set([...prev, "pro_rata_percentage"]))
                          }
                          placeholder="e.g., 15 for 15%"
                        />
                        <span className="text-muted-foreground">%</span>
                      </div>
                    </FieldWithHelp>
                  )}
                </>
              )}
            </>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!formData.holder_name || !formData.class_name}
          >
            {isEditMode ? "Save Changes" : "Create Instrument"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

