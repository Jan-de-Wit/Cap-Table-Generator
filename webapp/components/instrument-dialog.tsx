"use client";

import * as React from "react";
import { useEffect, useRef } from "react";
import Lenis from "lenis";
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
import { Separator } from "@/components/ui/separator";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { Info } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type {
  Instrument,
  Holder,
  CalculationType,
  InterestType,
  ProRataType,
  DilutionMethod,
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
  editProRataOnly?: boolean;
  originalProRataInstrument?: Instrument | null;
  originalProRataRoundIndex?: number | null;
  originalProRataRoundName?: string | null;
  roundValuation?: number;
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
  editProRataOnly = false,
  originalProRataInstrument,
  originalProRataRoundIndex,
  originalProRataRoundName,
  roundValuation,
}: InstrumentDialogProps) {
  const [formData, setFormData] = React.useState<Partial<Instrument>>({});
  const [touchedFields, setTouchedFields] = React.useState<Set<string>>(
    new Set()
  );
  const [className, setClassName] = React.useState<string>("");
  const [valuationCapEnabled, setValuationCapEnabled] =
    React.useState<boolean>(false);
  const classNameInputRef = React.useRef<HTMLInputElement>(null);
  const previousInstrumentRef = React.useRef<Instrument | null>(null);
  const lenisWrapperRef = useRef<HTMLDivElement>(null);
  const lenisContentRef = useRef<HTMLDivElement>(null);
  const lenisRef = useRef<Lenis | null>(null);

  // Helper function to validate percentage
  const validatePercentage = (
    percentage: number,
    fieldName: string
  ): string | undefined => {
    if (percentage >= 100) {
      return `${fieldName} must be less than 100%`;
    }
    if (percentage < 0) {
      return `${fieldName} must be greater than or equal to 0%`;
    }
    return undefined;
  };

  // Initialize form when dialog opens or instrument changes
  React.useEffect(() => {
    if (open) {
      // Check if instrument has changed by comparing JSON stringified versions
      // This handles deep equality checks for nested objects
      const currentInstrumentStr = instrument
        ? JSON.stringify(instrument)
        : null;
      const previousInstrumentStr = previousInstrumentRef.current
        ? JSON.stringify(previousInstrumentRef.current)
        : null;
      const instrumentChanged = currentInstrumentStr !== previousInstrumentStr;

      // Always update form data when instrument changes, even if dialog is already open
      if (instrument) {
        // Only update if instrument actually changed to avoid unnecessary re-renders
        if (instrumentChanged) {
          previousInstrumentRef.current = instrument;
          const initialData: Partial<Instrument> = { ...instrument };
          // Ensure exercise_type defaults to "full" for pro-rata allocations
          if (isProRata && !("exercise_type" in initialData)) {
            (initialData as any).exercise_type = "full";
          }
          setFormData(initialData);
          setClassName(instrument.class_name || "");
          // Set valuation cap enabled state based on whether valuation_cap exists
          const hasValuationCap =
            (instrument as any).valuation_cap !== undefined &&
            (instrument as any).valuation_cap !== null;
          setValuationCapEnabled(hasValuationCap);

          // For convertible/SAFE without distinct valuation cap, clear pro-rata and dilution
          if (
            (calculationType === "convertible" || calculationType === "safe") &&
            !hasValuationCap
          ) {
            if ((initialData as any).pro_rata_rights !== undefined) {
              (initialData as any).pro_rata_rights = undefined;
            }
            if ((initialData as any).pro_rata_percentage !== undefined) {
              (initialData as any).pro_rata_percentage = undefined;
            }
            if ((initialData as any).dilution_method !== undefined) {
              (initialData as any).dilution_method = undefined;
            }
            setFormData(initialData);
          }

          // Reset touched fields when instrument changes
          setTouchedFields(new Set());
        }
      } else {
        // Only reset if we don't have a previous instrument (i.e., dialog just opened)
        if (!previousInstrumentRef.current) {
          previousInstrumentRef.current = null;
          // Create empty instrument based on type
          if (isProRata) {
            setFormData({
              holder_name: "",
              class_name: "",
              pro_rata_type: "standard",
              exercise_type: "full",
            });
          } else {
            setClassName("");
            setValuationCapEnabled(false);
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
      }
    } else {
      // Reset ref when dialog closes
      previousInstrumentRef.current = null;
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

  // Validation function
  const getValidationErrors = (): string[] => {
    const errors: string[] = [];

    // Required fields
    if (!formData.holder_name || !formData.holder_name.trim()) {
      errors.push("Holder name is required");
    }
    if (!formData.class_name || !formData.class_name.trim()) {
      errors.push("Class name is required");
    }

    // Pro-rata validation
    if (isProRata) {
      const proRataType = (formData as any).pro_rata_type;
      if (proRataType === "super") {
        const proRataPercentage = (formData as any).pro_rata_percentage;
        if (
          proRataPercentage === undefined ||
          proRataPercentage === null ||
          proRataPercentage === 0
        ) {
          errors.push("Pro-rata percentage is required for super pro-rata");
        } else {
          const percentageError = validatePercentage(
            decimalToPercentage(proRataPercentage),
            "Pro-rata percentage"
          );
          if (percentageError) {
            errors.push(percentageError);
          }
        }
      }

      // Validate exercise_type
      const exerciseType = (formData as any).exercise_type;
      if (
        !exerciseType ||
        (exerciseType !== "full" && exerciseType !== "partial")
      ) {
        errors.push(
          "Exercise type is required and must be 'full' or 'partial'"
        );
      }

      // Validate partial exercise fields
      if (exerciseType === "partial") {
        const partialAmount = (formData as any).partial_exercise_amount;
        const partialPercentage = (formData as any).partial_exercise_percentage;

        if (!partialAmount && !partialPercentage) {
          errors.push(
            "Either partial exercise amount or partial exercise percentage must be provided for partial exercise"
          );
        }

        if (partialAmount !== undefined && partialAmount <= 0) {
          errors.push("Partial exercise amount must be greater than 0");
        }

        if (
          partialPercentage !== undefined &&
          (partialPercentage <= 0 || partialPercentage >= 1)
        ) {
          const percentageError = validatePercentage(
            decimalToPercentage(partialPercentage),
            "Partial exercise percentage"
          );
          if (percentageError) {
            errors.push(percentageError);
          }
        }

        // Validate that partial exercise percentage is lower than super pro-rata percentage
        if (
          partialPercentage !== undefined &&
          proRataType === "super" &&
          (formData as any).pro_rata_percentage !== undefined
        ) {
          const proRataPercentage = (formData as any).pro_rata_percentage;
          if (partialPercentage >= proRataPercentage) {
            errors.push(
              "Partial exercise percentage must be lower than super pro-rata percentage"
            );
          }
        }
      }
    } else {
      // Non-pro-rata instruments: check pro-rata rights
      const proRataRights = (formData as any).pro_rata_rights;
      if (proRataRights === "super") {
        const proRataPercentage = (formData as any).pro_rata_percentage;
        if (
          proRataPercentage === undefined ||
          proRataPercentage === null ||
          proRataPercentage === 0
        ) {
          errors.push("Super pro-rata percentage is required");
        } else {
          const percentageError = validatePercentage(
            decimalToPercentage(proRataPercentage),
            "Super pro-rata percentage"
          );
          if (percentageError) {
            errors.push(percentageError);
          }
        }
      }

      // Calculation type specific validations
      switch (calculationType) {
        case "fixed_shares":
          if (
            (formData as any).initial_quantity === undefined ||
            (formData as any).initial_quantity === null ||
            (formData as any).initial_quantity <= 0
          ) {
            errors.push("Initial quantity must be greater than 0");
          }
          break;
        case "target_percentage":
          const targetPercentage = (formData as any).target_percentage;
          if (targetPercentage === undefined || targetPercentage === null) {
            errors.push("Target percentage is required");
          } else {
            const percentageError = validatePercentage(
              decimalToPercentage(targetPercentage),
              "Target percentage"
            );
            if (percentageError) {
              errors.push(percentageError);
            }
          }
          break;
        case "valuation_based":
          if (
            (formData as any).investment_amount === undefined ||
            (formData as any).investment_amount === null ||
            (formData as any).investment_amount <= 0
          ) {
            errors.push("Investment amount must be greater than 0");
          }
          break;
        case "convertible":
          if (
            (formData as any).investment_amount === undefined ||
            (formData as any).investment_amount === null ||
            (formData as any).investment_amount <= 0
          ) {
            errors.push("Investment amount must be greater than 0");
          }
          if (!(formData as any).payment_date) {
            errors.push("Payment date is required");
          }
          if (!(formData as any).expected_conversion_date) {
            errors.push("Expected conversion date is required");
          }
          const interestRate = (formData as any).interest_rate;
          if (interestRate === undefined || interestRate === null) {
            errors.push("Interest rate is required");
          } else {
            const percentageError = validatePercentage(
              decimalToPercentage(interestRate),
              "Interest rate"
            );
            if (percentageError) {
              errors.push(percentageError);
            }
          }
          const discountRate = (formData as any).discount_rate;
          if (discountRate === undefined || discountRate === null) {
            errors.push("Discount rate is required");
          } else {
            const percentageError = validatePercentage(
              decimalToPercentage(discountRate),
              "Discount rate"
            );
            if (percentageError) {
              errors.push(percentageError);
            }
          }
          break;
        case "safe":
          if (
            (formData as any).investment_amount === undefined ||
            (formData as any).investment_amount === null ||
            (formData as any).investment_amount <= 0
          ) {
            errors.push("Investment amount must be greater than 0");
          }
          if (!(formData as any).expected_conversion_date) {
            errors.push("Expected conversion date is required");
          }
          const safeDiscountRate = (formData as any).discount_rate;
          if (safeDiscountRate === undefined || safeDiscountRate === null) {
            errors.push("Discount rate is required");
          } else {
            const percentageError = validatePercentage(
              decimalToPercentage(safeDiscountRate),
              "Discount rate"
            );
            if (percentageError) {
              errors.push(percentageError);
            }
          }
          break;
      }
    }

    return errors;
  };

  const validationErrors = React.useMemo(
    () => getValidationErrors(),
    [formData, calculationType, isProRata]
  );

  // Initialize Lenis for smooth scrolling
  useEffect(() => {
    if (!open) {
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
      return;
    }

    // Small delay to ensure DOM is ready and dialog animation completes
    const timeoutId = setTimeout(() => {
      const wrapper = lenisWrapperRef.current;
      const content = lenisContentRef.current;

      if (!wrapper || !content) {
        return;
      }

      // Ensure elements have dimensions
      const wrapperHeight = wrapper.clientHeight;
      const contentHeight = content.scrollHeight;

      if (wrapperHeight === 0 || contentHeight === 0) {
        // Retry after a bit more time if dimensions aren't ready
        setTimeout(() => {
          if (!wrapper || !content) return;
          const lenis = new Lenis({
            wrapper: wrapper,
            content: content,
            lerp: 0.05,
            duration: 1.2,
            smoothWheel: true,
            syncTouch: false,
            touchMultiplier: 2,
            wheelMultiplier: 1,
            infinite: false,
            autoResize: true,
            orientation: "vertical",
            gestureOrientation: "vertical",
            anchors: false,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
          });

          lenisRef.current = lenis;

          function raf(time: number) {
            lenis.raf(time);
            requestAnimationFrame(raf);
          }

          requestAnimationFrame(raf);
        }, 100);
        return;
      }

      const lenis = new Lenis({
        wrapper: wrapper,
        content: content,
        lerp: 0.05,
        duration: 1.2,
        smoothWheel: true,
        syncTouch: false,
        touchMultiplier: 2,
        wheelMultiplier: 1,
        infinite: false,
        autoResize: true,
        orientation: "vertical",
        gestureOrientation: "vertical",
        anchors: false,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      });

      // Store lenis instance in ref
      lenisRef.current = lenis;

      function raf(time: number) {
        lenis.raf(time);
        requestAnimationFrame(raf);
      }

      requestAnimationFrame(raf);
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
    };
  }, [open]);

  const handleSave = () => {
    if (validationErrors.length > 0) {
      return;
    }

    // For convertible/SAFE without distinct valuation cap, clear pro-rata and dilution
    const dataToSave = { ...formData };
    if (
      (calculationType === "convertible" || calculationType === "safe") &&
      !valuationCapEnabled
    ) {
      (dataToSave as any).pro_rata_rights = undefined;
      (dataToSave as any).pro_rata_percentage = undefined;
      (dataToSave as any).dilution_method = undefined;
    }

    onSave(dataToSave as Instrument);
    onOpenChange(false);
  };

  const isEditMode = !!instrument;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] h-[80vh] flex flex-col p-0">
        <div className="flex flex-col h-full">
          <DialogHeader className="px-6 pt-6 pb-4 shrink-0">
            <DialogTitle>
              {isEditMode
                ? editProRataOnly
                  ? "Edit Pro-Rata Rights"
                  : isProRata
                  ? "Edit Pro-Rata Allocation"
                  : "Edit Instrument"
                : isProRata
                ? "Create Pro-Rata Allocation"
                : "Create Instrument"}
            </DialogTitle>
            <DialogDescription>
              {isEditMode
                ? editProRataOnly
                  ? "Update pro-rata rights allocation settings"
                  : "Update instrument details"
                : "Add a new instrument to this round"}
            </DialogDescription>
          </DialogHeader>
          <div
            ref={lenisWrapperRef}
            className="flex-1 overflow-hidden min-h-0"
            style={{ position: "relative" }}
          >
            <div
              ref={lenisContentRef}
              className="px-6 space-y-6 py-4"
              style={{ willChange: "transform" }}
            >
              {/* Basic Information Section - Only show if not editing pro-rata allocation or pro-rata only */}
              {!isProRata && !editProRataOnly && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground mb-1">
                      Basic Information
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Essential details about the instrument
                    </p>
                  </div>
                  <div className="space-y-4">
                    <FieldWithHelp
                      label="Holder"
                      helpText="Select an existing holder or create a new one"
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
                        allowCreate={true}
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
                              setTouchedFields(
                                (prev) => new Set([...prev, "class_name"])
                              )
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
                    {/* Only show dilution method for convertible/SAFE if distinct valuation cap is set */}
                    {(!["convertible", "safe"].includes(calculationType) ||
                      valuationCapEnabled) && (
                      <>
                        <FieldWithHelp
                          label="Dilution Method"
                          helpText="Optional: Method for protecting against dilution in future rounds"
                          htmlFor="dilution-method"
                        >
                          <Select
                            value={(formData as any).dilution_method || "none"}
                            onValueChange={(value: DilutionMethod | "none") => {
                              updateField(
                                "dilution_method",
                                value === "none" ? undefined : value
                              );
                            }}
                            disabled={
                              ["convertible", "safe"].includes(
                                calculationType
                              ) && !valuationCapEnabled
                            }
                          >
                            <SelectTrigger id="dilution-method">
                              <SelectValue placeholder="No dilution protection" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">
                                No Dilution Protection
                              </SelectItem>
                              <SelectItem value="full_ratchet">
                                Full Ratchet
                              </SelectItem>
                              <SelectItem value="narrow_based_weighted_average">
                                Narrow-Based Weighted Average
                              </SelectItem>
                              <SelectItem value="broad_based_weighted_average">
                                Broad-Based Weighted Average
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </FieldWithHelp>
                        {(formData as any).dilution_method && (
                          <p className="text-xs text-muted-foreground">
                            {(formData as any).dilution_method ===
                            "full_ratchet"
                              ? "Maximum protection - adjusts conversion price to new issuance price"
                              : (formData as any).dilution_method ===
                                "narrow_based_weighted_average"
                              ? "Considers only common stock in calculation"
                              : "Includes all fully diluted shares in calculation"}
                          </p>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Show read-only holder and class info when editing pro-rata rights only (not allocations) */}
              {editProRataOnly && !isProRata && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground mb-1">
                      Basic Information
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Holder and class information cannot be changed when
                      editing pro-rata rights
                    </p>
                  </div>
                  <div className="space-y-4">
                    <FieldWithHelp
                      label="Holder"
                      helpText="Holder name (read-only)"
                      htmlFor="instrument-holder-readonly"
                    >
                      <Input
                        id="instrument-holder-readonly"
                        type="text"
                        value={formData.holder_name || ""}
                        disabled
                        className="bg-muted cursor-not-allowed"
                      />
                    </FieldWithHelp>
                    <FieldWithHelp
                      label="Class Name"
                      helpText="Class name (read-only)"
                      htmlFor="instrument-class-readonly"
                    >
                      <Input
                        id="instrument-class-readonly"
                        type="text"
                        value={formData.class_name || ""}
                        disabled
                        className="bg-muted cursor-not-allowed"
                      />
                    </FieldWithHelp>
                  </div>
                </div>
              )}

              {isProRata ? (
                <>
                  <Separator />
                  {/* Pro-Rata Rights Section */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold text-foreground mb-1">
                        Pro-Rata Rights
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        Pro-rata rights are defined in the original instrument
                      </p>
                    </div>
                    <FieldWithHelp
                      label="Pro-Rata Rights"
                      helpText="Standard: maintain ownership. Super: can exceed ownership up to specified percentage."
                      htmlFor="pro-rata-rights"
                    >
                      <div className="flex items-center gap-2">
                        <Input
                          id="pro-rata-rights"
                          type="text"
                          value={
                            (formData as any).pro_rata_type === "super" &&
                            (formData as any).pro_rata_percentage !== undefined
                              ? `Super (${decimalToPercentage(
                                  (formData as any).pro_rata_percentage
                                ).toFixed(2)}%)`
                              : (formData as any).pro_rata_type === "standard"
                              ? "Standard"
                              : "Standard"
                          }
                          disabled
                          className="flex-1"
                        />
                        {originalProRataInstrument && (
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                className="h-10 cursor-pointer"
                                title="View original pro-rata settings"
                              >
                                <Info className="h-4 w-4 mr-1.5" />
                                View Original
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-80" align="end">
                              <div className="space-y-3">
                                <div>
                                  <h4 className="font-semibold text-sm mb-2">
                                    Original Pro-Rata Rights
                                  </h4>
                                  <p className="text-xs text-muted-foreground mb-3">
                                    These settings are defined in the original
                                    instrument and cannot be changed here.
                                  </p>
                                </div>
                                <div className="space-y-2 text-sm">
                                  {(originalProRataRoundName !== null &&
                                    originalProRataRoundName !== undefined) ||
                                  (originalProRataRoundIndex !== null &&
                                    originalProRataRoundIndex !== undefined) ? (
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">
                                        Round:
                                      </span>
                                      <span className="font-medium">
                                        {originalProRataRoundName ||
                                          (originalProRataRoundIndex !== null &&
                                          originalProRataRoundIndex !==
                                            undefined
                                            ? `Round ${
                                                originalProRataRoundIndex + 1
                                              }`
                                            : "—")}
                                      </span>
                                    </div>
                                  ) : null}
                                  {originalProRataInstrument &&
                                    "holder_name" in
                                      originalProRataInstrument &&
                                    originalProRataInstrument.holder_name && (
                                      <div className="flex justify-between">
                                        <span className="text-muted-foreground">
                                          Holder:
                                        </span>
                                        <span className="font-medium">
                                          {
                                            originalProRataInstrument.holder_name
                                          }
                                        </span>
                                      </div>
                                    )}
                                  {originalProRataInstrument &&
                                    "pro_rata_rights" in
                                      originalProRataInstrument && (
                                      <div className="flex justify-between">
                                        <span className="text-muted-foreground">
                                          Pro-Rata Rights:
                                        </span>
                                        <span className="font-medium">
                                          {originalProRataInstrument.pro_rata_rights ===
                                            "super" &&
                                          "pro_rata_percentage" in
                                            originalProRataInstrument &&
                                          originalProRataInstrument.pro_rata_percentage !==
                                            undefined
                                            ? `Super (${decimalToPercentage(
                                                originalProRataInstrument.pro_rata_percentage
                                              ).toFixed(2)}%)`
                                            : originalProRataInstrument.pro_rata_rights ===
                                              "standard"
                                            ? "Standard"
                                            : "None"}
                                        </span>
                                      </div>
                                    )}
                                </div>
                              </div>
                            </PopoverContent>
                          </Popover>
                        )}
                      </div>
                    </FieldWithHelp>
                  </div>

                  <Separator />
                  {/* Exercise Section */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold text-foreground mb-1">
                        Exercise
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        Configure how pro-rata rights are exercised
                      </p>
                    </div>
                    <FieldWithHelp
                      label="Exercise Type"
                      helpText="Full: exercise full rights. Partial: exercise rights up to a specified amount or percentage."
                      required
                      htmlFor="exercise-type"
                    >
                      <SegmentedControl
                        value={(formData as any).exercise_type || "full"}
                        onValueChange={(value: string) => {
                          const updates: any = { exercise_type: value };
                          if (value === "full") {
                            updates.partial_exercise_amount = undefined;
                            updates.partial_exercise_percentage = undefined;
                          }
                          setFormData((prev) => ({ ...prev, ...updates }));
                          setTouchedFields(
                            (prev) => new Set([...prev, "exercise_type"])
                          );
                        }}
                        options={[
                          { value: "full", label: "Full" },
                          { value: "partial", label: "Partial" },
                        ]}
                        className="w-full"
                      />
                    </FieldWithHelp>
                    {(formData as any).exercise_type === "partial" && (
                      <>
                        {roundValuation !== undefined &&
                          roundValuation !== null &&
                          roundValuation > 0 && (
                            <FieldWithHelp
                              label="Partial Exercise Amount"
                              helpText="Maximum investment amount for partial exercise (optional if percentage is provided)"
                              htmlFor="partial-exercise-amount"
                              error={
                                touchedFields.has("partial_exercise_amount") &&
                                (formData as any).partial_exercise_amount !==
                                  undefined &&
                                (formData as any).partial_exercise_amount <= 0
                                  ? "Partial exercise amount must be greater than 0"
                                  : undefined
                              }
                            >
                              <Input
                                id="partial-exercise-amount"
                                type="text"
                                value={
                                  (formData as any).partial_exercise_amount
                                    ? formatCurrency(
                                        (formData as any)
                                          .partial_exercise_amount
                                      )
                                    : ""
                                }
                                onChange={(e) => {
                                  const parsed = parseFormattedNumber(
                                    e.target.value
                                  );
                                  updateField(
                                    "partial_exercise_amount",
                                    parsed > 0 ? parsed : undefined
                                  );
                                }}
                                onBlur={() =>
                                  setTouchedFields(
                                    (prev) =>
                                      new Set([
                                        ...prev,
                                        "partial_exercise_amount",
                                      ])
                                  )
                                }
                                placeholder="e.g., $50,000"
                                className={
                                  touchedFields.has(
                                    "partial_exercise_amount"
                                  ) &&
                                  (formData as any).partial_exercise_amount !==
                                    undefined &&
                                  (formData as any).partial_exercise_amount <= 0
                                    ? "border-destructive ring-destructive/20"
                                    : ""
                                }
                              />
                            </FieldWithHelp>
                          )}
                        <FieldWithHelp
                          label="Partial Exercise Percentage"
                          helpText="Maximum ownership percentage for partial exercise (optional if amount is provided, 0-100%). Must be lower than super pro-rata percentage if set."
                          htmlFor="partial-exercise-percentage"
                          error={
                            touchedFields.has("partial_exercise_percentage") &&
                            (formData as any).partial_exercise_percentage !==
                              undefined
                              ? (() => {
                                  const percentageError = validatePercentage(
                                    decimalToPercentage(
                                      (formData as any)
                                        .partial_exercise_percentage
                                    ),
                                    "Partial exercise percentage"
                                  );
                                  if (percentageError) return percentageError;

                                  // Check if partial exercise percentage is lower than super pro-rata percentage
                                  const proRataType = (formData as any)
                                    .pro_rata_type;
                                  if (
                                    proRataType === "super" &&
                                    (formData as any).pro_rata_percentage !==
                                      undefined
                                  ) {
                                    const partialPercentage = (formData as any)
                                      .partial_exercise_percentage;
                                    const proRataPercentage = (formData as any)
                                      .pro_rata_percentage;
                                    if (
                                      partialPercentage >= proRataPercentage
                                    ) {
                                      return "Partial exercise percentage must be lower than super pro-rata percentage";
                                    }
                                  }
                                  return undefined;
                                })()
                              : undefined
                          }
                        >
                          <div className="flex items-center gap-2">
                            <Input
                              id="partial-exercise-percentage"
                              type="number"
                              step="0.01"
                              min="0"
                              max="100"
                              value={
                                (formData as any).partial_exercise_percentage
                                  ? decimalToPercentage(
                                      (formData as any)
                                        .partial_exercise_percentage
                                    )
                                  : ""
                              }
                              onChange={(e) => {
                                const percentage = e.target.value
                                  ? parseFloat(e.target.value)
                                  : 0;
                                updateField(
                                  "partial_exercise_percentage",
                                  percentage > 0
                                    ? percentageToDecimal(percentage)
                                    : undefined
                                );
                              }}
                              onBlur={() =>
                                setTouchedFields(
                                  (prev) =>
                                    new Set([
                                      ...prev,
                                      "partial_exercise_percentage",
                                    ])
                                )
                              }
                              className={
                                touchedFields.has(
                                  "partial_exercise_percentage"
                                ) &&
                                (formData as any)
                                  .partial_exercise_percentage !== undefined &&
                                (() => {
                                  const percentageError = validatePercentage(
                                    decimalToPercentage(
                                      (formData as any)
                                        .partial_exercise_percentage
                                    ),
                                    "Partial exercise percentage"
                                  );
                                  if (percentageError) return true;

                                  // Check if partial exercise percentage is lower than super pro-rata percentage
                                  const proRataType = (formData as any)
                                    .pro_rata_type;
                                  if (
                                    proRataType === "super" &&
                                    (formData as any).pro_rata_percentage !==
                                      undefined
                                  ) {
                                    const partialPercentage = (formData as any)
                                      .partial_exercise_percentage;
                                    const proRataPercentage = (formData as any)
                                      .pro_rata_percentage;
                                    if (
                                      partialPercentage >= proRataPercentage
                                    ) {
                                      return true;
                                    }
                                  }
                                  return false;
                                })()
                                  ? "border-destructive ring-destructive/20"
                                  : ""
                              }
                              placeholder="e.g., 10 for 10%"
                            />
                            <span className="text-muted-foreground">%</span>
                          </div>
                        </FieldWithHelp>
                      </>
                    )}
                  </div>
                </>
              ) : (
                <>
                  {!editProRataOnly &&
                    (calculationType === "fixed_shares" ||
                      calculationType === "target_percentage" ||
                      calculationType === "valuation_based") && (
                      <>
                        <Separator />
                        {/* Investment Details Section */}
                        <div className="space-y-4">
                          <div>
                            <h3 className="text-sm font-semibold text-foreground mb-1">
                              Investment Details
                            </h3>
                            <p className="text-xs text-muted-foreground">
                              {calculationType === "fixed_shares"
                                ? "Specify the number of shares to issue"
                                : calculationType === "target_percentage"
                                ? "Set the target ownership percentage"
                                : "Enter the investment amount"}
                            </p>
                          </div>
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
                                    ? formatNumber(
                                        (formData as any).initial_quantity
                                      )
                                    : ""
                                }
                                onChange={(e) => {
                                  const parsed = parseFormattedNumber(
                                    e.target.value
                                  );
                                  updateField(
                                    "initial_quantity",
                                    parsed > 0 ? parsed : 0
                                  );
                                }}
                                onBlur={() =>
                                  setTouchedFields(
                                    (prev) =>
                                      new Set([...prev, "initial_quantity"])
                                  )
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
                              error={
                                touchedFields.has("target_percentage") &&
                                (formData as any).target_percentage !==
                                  undefined
                                  ? validatePercentage(
                                      decimalToPercentage(
                                        (formData as any).target_percentage
                                      ),
                                      "Target percentage"
                                    )
                                  : undefined
                              }
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
                                      ? decimalToPercentage(
                                          (formData as any).target_percentage
                                        )
                                      : ""
                                  }
                                  onChange={(e) => {
                                    const percentage = e.target.value
                                      ? parseFloat(e.target.value)
                                      : 0;
                                    updateField(
                                      "target_percentage",
                                      percentageToDecimal(percentage)
                                    );
                                  }}
                                  onBlur={() =>
                                    setTouchedFields(
                                      (prev) =>
                                        new Set([...prev, "target_percentage"])
                                    )
                                  }
                                  className={
                                    touchedFields.has("target_percentage") &&
                                    (formData as any).target_percentage !==
                                      undefined &&
                                    validatePercentage(
                                      decimalToPercentage(
                                        (formData as any).target_percentage
                                      ),
                                      "Target percentage"
                                    )
                                      ? "border-destructive ring-destructive/20"
                                      : ""
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
                                    ? formatCurrency(
                                        (formData as any).investment_amount
                                      )
                                    : ""
                                }
                                onChange={(e) => {
                                  const parsed = parseFormattedNumber(
                                    e.target.value
                                  );
                                  updateField(
                                    "investment_amount",
                                    parsed > 0 ? parsed : 0
                                  );
                                }}
                                onBlur={() =>
                                  setTouchedFields(
                                    (prev) =>
                                      new Set([...prev, "investment_amount"])
                                  )
                                }
                                placeholder="e.g., $2,000,000"
                              />
                            </FieldWithHelp>
                          )}
                        </div>
                      </>
                    )}

                  {!editProRataOnly && calculationType === "convertible" && (
                    <>
                      <Separator />
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-semibold text-foreground mb-1">
                            Investment Details
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            Principal amount and payment information
                          </p>
                        </div>
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
                                  ? formatCurrency(
                                      (formData as any).investment_amount
                                    )
                                  : ""
                              }
                              onChange={(e) => {
                                const parsed = parseFormattedNumber(
                                  e.target.value
                                );
                                updateField(
                                  "investment_amount",
                                  parsed > 0 ? parsed : 0
                                );
                              }}
                              onBlur={() =>
                                setTouchedFields(
                                  (prev) =>
                                    new Set([...prev, "investment_amount"])
                                )
                              }
                            />
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
                              onChange={(e) =>
                                updateField("payment_date", e.target.value)
                              }
                              onBlur={() =>
                                setTouchedFields(
                                  (prev) => new Set([...prev, "payment_date"])
                                )
                              }
                            />
                          </FieldWithHelp>
                        </div>
                      </div>

                      <Separator />
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-semibold text-foreground mb-1">
                            Interest Terms
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            Configure how interest accrues on the investment
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <FieldWithHelp
                            label="Interest Rate"
                            helpText="Annual interest rate as percentage (0-100%)"
                            required
                            error={
                              touchedFields.has("interest_rate") &&
                              (formData as any).interest_rate !== undefined
                                ? validatePercentage(
                                    decimalToPercentage(
                                      (formData as any).interest_rate
                                    ),
                                    "Interest rate"
                                  )
                                : undefined
                            }
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
                                    ? decimalToPercentage(
                                        (formData as any).interest_rate
                                      )
                                    : ""
                                }
                                onChange={(e) => {
                                  const percentage = e.target.value
                                    ? parseFloat(e.target.value)
                                    : 0;
                                  updateField(
                                    "interest_rate",
                                    percentageToDecimal(percentage)
                                  );
                                }}
                                onBlur={() =>
                                  setTouchedFields(
                                    (prev) =>
                                      new Set([...prev, "interest_rate"])
                                  )
                                }
                                className={
                                  touchedFields.has("interest_rate") &&
                                  (formData as any).interest_rate !==
                                    undefined &&
                                  validatePercentage(
                                    decimalToPercentage(
                                      (formData as any).interest_rate
                                    ),
                                    "Interest rate"
                                  )
                                    ? "border-destructive ring-destructive/20"
                                    : ""
                                }
                                placeholder="e.g., 8 for 8%"
                              />
                              <span className="text-muted-foreground">%</span>
                            </div>
                          </FieldWithHelp>
                          <FieldWithHelp
                            label="Interest Type"
                            helpText="How interest is calculated over time"
                            required
                            htmlFor="interest-type"
                          >
                            <Select
                              value={
                                (formData as any).interest_type || "simple"
                              }
                              onValueChange={(value: InterestType) => {
                                updateField("interest_type", value);
                                setTouchedFields(
                                  (prev) => new Set([...prev, "interest_type"])
                                );
                              }}
                            >
                              <SelectTrigger id="interest-type">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="simple">
                                  Simple Interest
                                </SelectItem>
                                <SelectItem value="compound_yearly">
                                  Compounded Annually
                                </SelectItem>
                                <SelectItem value="compound_monthly">
                                  Compounded Monthly
                                </SelectItem>
                                <SelectItem value="compound_daily">
                                  Compounded Daily
                                </SelectItem>
                                <SelectItem value="no_interest">
                                  No Interest
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          </FieldWithHelp>
                        </div>
                      </div>

                      <Separator />
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-semibold text-foreground mb-1">
                            Conversion Terms
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            Terms for converting the instrument to equity
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <FieldWithHelp
                            label="Expected Conversion Date"
                            helpText="Expected date when the convertible will convert"
                            required
                            htmlFor="expected-conversion-date"
                          >
                            <Input
                              id="expected-conversion-date"
                              type="date"
                              value={
                                (formData as any).expected_conversion_date || ""
                              }
                              onChange={(e) =>
                                updateField(
                                  "expected_conversion_date",
                                  e.target.value
                                )
                              }
                              onBlur={() =>
                                setTouchedFields(
                                  (prev) =>
                                    new Set([
                                      ...prev,
                                      "expected_conversion_date",
                                    ])
                                )
                              }
                            />
                          </FieldWithHelp>
                          <FieldWithHelp
                            label="Discount Rate"
                            helpText="Discount percentage applied at conversion (0-100%)"
                            required
                            error={
                              touchedFields.has("discount_rate") &&
                              (formData as any).discount_rate !== undefined
                                ? validatePercentage(
                                    decimalToPercentage(
                                      (formData as any).discount_rate
                                    ),
                                    "Discount rate"
                                  )
                                : undefined
                            }
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
                                    ? decimalToPercentage(
                                        (formData as any).discount_rate
                                      )
                                    : ""
                                }
                                onChange={(e) => {
                                  const percentage = e.target.value
                                    ? parseFloat(e.target.value)
                                    : 0;
                                  updateField(
                                    "discount_rate",
                                    percentageToDecimal(percentage)
                                  );
                                }}
                                onBlur={() =>
                                  setTouchedFields(
                                    (prev) =>
                                      new Set([...prev, "discount_rate"])
                                  )
                                }
                                className={
                                  touchedFields.has("discount_rate") &&
                                  (formData as any).discount_rate !==
                                    undefined &&
                                  validatePercentage(
                                    decimalToPercentage(
                                      (formData as any).discount_rate
                                    ),
                                    "Discount rate"
                                  )
                                    ? "border-destructive ring-destructive/20"
                                    : ""
                                }
                                placeholder="e.g., 20 for 20%"
                              />
                              <span className="text-muted-foreground">%</span>
                            </div>
                          </FieldWithHelp>
                          <div className="space-y-4 w-full col-span-2">
                            <div className="space-y-1.5">
                              <div className="flex items-center gap-2">
                                <label
                                  htmlFor="valuation-cap-toggle"
                                  className="text-xs font-medium text-foreground"
                                >
                                  Valuation Cap
                                </label>
                              </div>
                              <SegmentedControl
                                value={
                                  valuationCapEnabled ? "enabled" : "disabled"
                                }
                                onValueChange={(value: string) => {
                                  const enabled = value === "enabled";
                                  setValuationCapEnabled(enabled);
                                  if (!enabled) {
                                    // When disabling, clear both valuation_cap and valuation_cap_type
                                    updateField("valuation_cap", undefined);
                                    updateField(
                                      "valuation_cap_type",
                                      undefined
                                    );
                                    // Also clear pro-rata rights and dilution method for convertible
                                    if (calculationType === "convertible") {
                                      updateField("pro_rata_rights", undefined);
                                      updateField(
                                        "pro_rata_percentage",
                                        undefined
                                      );
                                      updateField("dilution_method", undefined);
                                    }
                                  }
                                }}
                                options={[
                                  { value: "disabled", label: "Round Cap" },
                                  {
                                    value: "enabled",
                                    label: "Set Distinct Cap",
                                  },
                                ]}
                                className="w-full"
                              />
                            </div>
                            {valuationCapEnabled && (
                              <div className="space-y-4 w-full grid grid-cols-2 gap-4">
                                <FieldWithHelp
                                  label="Valuation Cap"
                                  helpText="Optional: Maximum valuation for conversion"
                                  htmlFor="valuation-cap"
                                >
                                  <Input
                                    id="valuation-cap"
                                    type="text"
                                    value={
                                      (formData as any).valuation_cap
                                        ? formatCurrency(
                                            (formData as any).valuation_cap
                                          )
                                        : ""
                                    }
                                    onChange={(e) => {
                                      const parsed = parseFormattedNumber(
                                        e.target.value
                                      );
                                      updateField(
                                        "valuation_cap",
                                        parsed > 0 ? parsed : undefined
                                      );
                                    }}
                                    onBlur={() =>
                                      setTouchedFields(
                                        (prev) =>
                                          new Set([...prev, "valuation_cap"])
                                      )
                                    }
                                    placeholder="e.g., $10,000,000"
                                    className="w-full"
                                  />
                                </FieldWithHelp>
                                <FieldWithHelp
                                  label="Valuation Cap Type"
                                  helpText="How the valuation cap is applied"
                                  htmlFor="valuation-cap-type"
                                >
                                  <Select
                                    value={
                                      (formData as any).valuation_cap_type ||
                                      "default"
                                    }
                                    onValueChange={(value: any) => {
                                      updateField("valuation_cap_type", value);
                                    }}
                                  >
                                    <SelectTrigger
                                      id="valuation-cap-type"
                                      className="w-full"
                                    >
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="default">
                                        Default
                                      </SelectItem>
                                      <SelectItem value="pre_conversion">
                                        Pre-Conversion
                                      </SelectItem>
                                      <SelectItem value="post_conversion_own">
                                        Post-Conversion (Own)
                                      </SelectItem>
                                      <SelectItem value="post_conversion_total">
                                        Post-Conversion (Total)
                                      </SelectItem>
                                    </SelectContent>
                                  </Select>
                                </FieldWithHelp>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {!editProRataOnly && calculationType === "safe" && (
                    <>
                      <Separator />
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-semibold text-foreground mb-1">
                            Investment Details
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            Principal amount and payment information
                          </p>
                        </div>
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
                                ? formatCurrency(
                                    (formData as any).investment_amount
                                  )
                                : ""
                            }
                            onChange={(e) => {
                              const parsed = parseFormattedNumber(
                                e.target.value
                              );
                              updateField(
                                "investment_amount",
                                parsed > 0 ? parsed : 0
                              );
                            }}
                            onBlur={() =>
                              setTouchedFields(
                                (prev) =>
                                  new Set([...prev, "investment_amount"])
                              )
                            }
                          />
                        </FieldWithHelp>
                      </div>

                      <Separator />
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-semibold text-foreground mb-1">
                            Conversion Terms
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            Terms for converting the SAFE to equity
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <FieldWithHelp
                            label="Expected Conversion Date"
                            helpText="Expected date when the SAFE will convert"
                            required
                            htmlFor="safe-conversion-date"
                          >
                            <Input
                              id="safe-conversion-date"
                              type="date"
                              value={
                                (formData as any).expected_conversion_date || ""
                              }
                              onChange={(e) =>
                                updateField(
                                  "expected_conversion_date",
                                  e.target.value
                                )
                              }
                              onBlur={() =>
                                setTouchedFields(
                                  (prev) =>
                                    new Set([
                                      ...prev,
                                      "expected_conversion_date",
                                    ])
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
                                    ? decimalToPercentage(
                                        (formData as any).discount_rate
                                      )
                                    : ""
                                }
                                onChange={(e) => {
                                  const percentage = e.target.value
                                    ? parseFloat(e.target.value)
                                    : 0;
                                  updateField(
                                    "discount_rate",
                                    percentageToDecimal(percentage)
                                  );
                                }}
                                onBlur={() =>
                                  setTouchedFields(
                                    (prev) =>
                                      new Set([...prev, "discount_rate"])
                                  )
                                }
                                placeholder="e.g., 20 for 20%"
                              />
                              <span className="text-muted-foreground">%</span>
                            </div>
                          </FieldWithHelp>
                          <div className="space-y-4 w-full col-span-2">
                            <div className="space-y-1.5">
                              <div className="flex items-center gap-2">
                                <label
                                  htmlFor="safe-valuation-cap-toggle"
                                  className="text-xs font-medium text-foreground"
                                >
                                  Valuation Cap
                                </label>
                              </div>
                              <SegmentedControl
                                value={
                                  valuationCapEnabled ? "enabled" : "disabled"
                                }
                                onValueChange={(value: string) => {
                                  const enabled = value === "enabled";
                                  setValuationCapEnabled(enabled);
                                  if (!enabled) {
                                    // When disabling, clear both valuation_cap and valuation_cap_type
                                    updateField("valuation_cap", undefined);
                                    updateField(
                                      "valuation_cap_type",
                                      undefined
                                    );
                                    // Also clear pro-rata rights and dilution method for SAFE
                                    if (calculationType === "safe") {
                                      updateField("pro_rata_rights", undefined);
                                      updateField(
                                        "pro_rata_percentage",
                                        undefined
                                      );
                                      updateField("dilution_method", undefined);
                                    }
                                  }
                                }}
                                options={[
                                  { value: "disabled", label: "Round Cap" },
                                  {
                                    value: "enabled",
                                    label: "Set Distinct Cap",
                                  },
                                ]}
                                className="w-full"
                              />
                            </div>
                            {valuationCapEnabled && (
                              <div className="space-y-4 w-full grid grid-cols-2 gap-4">
                                <FieldWithHelp
                                  label="Valuation Cap"
                                  helpText="Optional: Maximum valuation for conversion"
                                  htmlFor="safe-valuation-cap"
                                >
                                  <Input
                                    id="safe-valuation-cap"
                                    type="text"
                                    value={
                                      (formData as any).valuation_cap
                                        ? formatCurrency(
                                            (formData as any).valuation_cap
                                          )
                                        : ""
                                    }
                                    onChange={(e) => {
                                      const parsed = parseFormattedNumber(
                                        e.target.value
                                      );
                                      updateField(
                                        "valuation_cap",
                                        parsed > 0 ? parsed : undefined
                                      );
                                    }}
                                    onBlur={() =>
                                      setTouchedFields(
                                        (prev) =>
                                          new Set([...prev, "valuation_cap"])
                                      )
                                    }
                                    placeholder="e.g., $10,000,000"
                                    className="w-full"
                                  />
                                </FieldWithHelp>
                                <FieldWithHelp
                                  label="Valuation Cap Type"
                                  helpText="How the valuation cap is applied"
                                  htmlFor="safe-valuation-cap-type"
                                >
                                  <Select
                                    value={
                                      (formData as any).valuation_cap_type ||
                                      "default"
                                    }
                                    onValueChange={(value: any) => {
                                      updateField("valuation_cap_type", value);
                                    }}
                                  >
                                    <SelectTrigger
                                      id="safe-valuation-cap-type"
                                      className="w-full"
                                    >
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="default">
                                        Default
                                      </SelectItem>
                                      <SelectItem value="pre_conversion">
                                        Pre-Conversion
                                      </SelectItem>
                                      <SelectItem value="post_conversion_own">
                                        Post-Conversion (Own)
                                      </SelectItem>
                                      <SelectItem value="post_conversion_total">
                                        Post-Conversion (Total)
                                      </SelectItem>
                                    </SelectContent>
                                  </Select>
                                </FieldWithHelp>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Pro-Rata Rights Field (for non-pro-rata instruments or when editing pro-rata only) */}
                  {/* For convertible/SAFE, only show if distinct valuation cap is set */}
                  {(editProRataOnly ||
                    (!isProRata &&
                      ((calculationType !== "convertible" &&
                        calculationType !== "safe") ||
                        valuationCapEnabled))) && (
                    <>
                      <Separator />
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-semibold text-foreground mb-1">
                            Pro-Rata Rights
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            {editProRataOnly
                              ? "Update pro-rata rights allocation settings"
                              : "Optional: Grant pro-rata rights for future rounds"}
                          </p>
                        </div>
                        <FieldWithHelp
                          label="Pro-Rata Rights"
                          helpText="Does this shareholder receive pro-rata rights in future rounds?"
                          htmlFor="pro-rata-rights"
                        >
                          <Select
                            value={(formData as any).pro_rata_rights || "none"}
                            onValueChange={(
                              value: "standard" | "super" | "none"
                            ) => {
                              const updates: any = {
                                pro_rata_rights:
                                  value === "none" ? undefined : value,
                              };
                              if (value !== "super") {
                                updates.pro_rata_percentage = undefined;
                              }
                              setFormData((prev) => ({ ...prev, ...updates }));
                            }}
                            disabled={
                              (calculationType === "convertible" ||
                                calculationType === "safe") &&
                              !valuationCapEnabled
                            }
                          >
                            <SelectTrigger id="pro-rata-rights">
                              <SelectValue placeholder="No pro-rata rights" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">
                                No pro-rata rights
                              </SelectItem>
                              <SelectItem value="standard">
                                Standard Pro-Rata
                              </SelectItem>
                              <SelectItem value="super">
                                Super Pro-Rata
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </FieldWithHelp>
                        {(formData as any).pro_rata_rights === "super" && (
                          <FieldWithHelp
                            label="Super Pro-Rata Percentage"
                            helpText="Maximum ownership percentage for super pro-rata (0-100%)"
                            required
                            error={
                              touchedFields.has("pro_rata_percentage") &&
                              (formData as any).pro_rata_percentage !==
                                undefined
                                ? validatePercentage(
                                    decimalToPercentage(
                                      (formData as any).pro_rata_percentage
                                    ),
                                    "Super pro-rata percentage"
                                  )
                                : undefined
                            }
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
                                    ? decimalToPercentage(
                                        (formData as any).pro_rata_percentage
                                      )
                                    : ""
                                }
                                onChange={(e) => {
                                  const percentage = e.target.value
                                    ? parseFloat(e.target.value)
                                    : 0;
                                  updateField(
                                    "pro_rata_percentage",
                                    percentageToDecimal(percentage)
                                  );
                                }}
                                onBlur={() =>
                                  setTouchedFields(
                                    (prev) =>
                                      new Set([...prev, "pro_rata_percentage"])
                                  )
                                }
                                className={
                                  touchedFields.has("pro_rata_percentage") &&
                                  (formData as any).pro_rata_percentage !==
                                    undefined &&
                                  validatePercentage(
                                    decimalToPercentage(
                                      (formData as any).pro_rata_percentage
                                    ),
                                    "Super pro-rata percentage"
                                  )
                                    ? "border-destructive ring-destructive/20"
                                    : ""
                                }
                                placeholder="e.g., 15 for 15%"
                              />
                              <span className="text-muted-foreground">%</span>
                            </div>
                          </FieldWithHelp>
                        )}
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
          <DialogFooter className="px-6 pb-6 pt-4 shrink-0 border-t">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={validationErrors.length > 0}
              className="cursor-pointer"
            >
              {isEditMode ? "Save Changes" : "Create Instrument"}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}
