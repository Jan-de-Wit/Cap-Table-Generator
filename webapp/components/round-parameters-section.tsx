"use client";

import * as React from "react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FieldWithHelp } from "@/components/field-with-help";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Round, CalculationType, ValuationBasis } from "@/types/cap-table";
import type { RoundValidation } from "@/lib/validation";
import { getFieldError } from "@/lib/validation";
import { formatCurrency, parseFormattedNumber } from "@/lib/formatters";

interface RoundParametersSectionProps {
  round: Round;
  touchedFields: Set<string>;
  validation?: RoundValidation;
  onUpdate: (updates: Partial<Round>) => void;
  onFieldTouched: (field: string) => void;
  roundIndex?: number;
}

export function RoundParametersSection({
  round,
  touchedFields,
  validation,
  onUpdate,
  onFieldTouched,
  roundIndex,
}: RoundParametersSectionProps) {
  const needsValuationBasis = [
    "valuation_based",
    "convertible",
    "safe",
  ].includes(round.calculation_type);

  const calculationTypeOptions = [
    { value: "fixed_shares", label: "Fixed Shares" },
    { value: "valuation_based", label: "Valuation-Based" },
    { value: "target_percentage", label: "Target %" },
    { value: "convertible", label: "Convertible" },
    { value: "safe", label: "SAFE" },
  ];

  const calculationTypeHelpText = {
    fixed_shares:
      "Shares are allocated directly with a fixed number of shares per instrument.",
    target_percentage:
      "Shares are calculated to achieve a target diluted ownership percentage.",
    valuation_based:
      "Shares are calculated based on investment amount and valuation.",
    convertible:
      "Convertible instruments that convert to equity at a future date with interest and discounts.",
    safe: "Simple Agreement for Future Equity - converts to equity at a future financing round.",
  };

  return (
    <div className="space-y-8">
      {/* Round Name and Date */}
      <div className="grid grid-cols-2 gap-6">
        <FieldWithHelp
          label="Round Name"
          helpText="A descriptive name for this financing round (e.g., 'Seed Round', 'Series A')"
          required
          error={
            touchedFields.has("name")
              ? getFieldError(validation?.errors ?? [], "name")
              : undefined
          }
          htmlFor="round-name"
        >
          <Input
            id={
              roundIndex !== undefined
                ? `round-${roundIndex}-name`
                : "round-name"
            }
            value={round.name}
            onChange={(e) => onUpdate({ name: e.target.value })}
            onBlur={() => onFieldTouched("name")}
            placeholder="e.g., Seed Round"
            className={`font-medium ${
              touchedFields.has("name") &&
              getFieldError(validation?.errors ?? [], "name")
                ? "border-destructive ring-destructive/20"
                : "focus:ring-primary/20"
            }`}
          />
        </FieldWithHelp>
        <FieldWithHelp
          label="Round Date"
          helpText="The closing date of this financing round"
          required
          error={
            touchedFields.has("round_date")
              ? getFieldError(validation?.errors ?? [], "round_date")
              : undefined
          }
          htmlFor="round-date"
        >
          <Input
            id={
              roundIndex !== undefined
                ? `round-${roundIndex}-round_date`
                : "round-date"
            }
            type="date"
            value={round.round_date}
            onChange={(e) => onUpdate({ round_date: e.target.value })}
            onBlur={() => onFieldTouched("round_date")}
            className={
              touchedFields.has("round_date") &&
              getFieldError(validation?.errors ?? [], "round_date")
                ? "border-destructive ring-destructive/20"
                : "focus:ring-primary/20"
            }
          />
        </FieldWithHelp>
      </div>

      {/* Calculation Type as Segmented Control */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <label
            htmlFor="calculation-type"
            className="text-xs font-medium text-foreground"
          >
            Round Type
            <span className="text-destructive ml-1.5 font-bold">*</span>
          </label>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help hover:text-foreground transition-colors" />
              </TooltipTrigger>
              <TooltipContent className="max-w-sm">
                <p className="font-medium mb-1.5">
                  How share quantities are calculated
                </p>
                <p className="text-sm">
                  {calculationTypeHelpText[round.calculation_type] ||
                    "Determines how share quantities are calculated for instruments in this round."}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div
          id={
            roundIndex !== undefined
              ? `round-${roundIndex}-calculation-type`
              : undefined
          }
        >
          <SegmentedControl
            value={round.calculation_type}
            onValueChange={(value: string) => {
              const updates: Partial<Round> = {
                calculation_type: value as CalculationType,
              };
              // Clear instruments when changing calculation type
              if (round.calculation_type !== value) {
                updates.instruments = [];
              }
              // Clear valuation fields if not needed
              if (!["valuation_based", "convertible", "safe"].includes(value)) {
                updates.valuation_basis = undefined;
                updates.valuation = undefined;
              } else {
                // Set default valuation_basis to pre_money if not already set
                if (!round.valuation_basis) {
                  updates.valuation_basis = "pre_money";
                }
              }
              onUpdate(updates);
              onFieldTouched("calculation_type");
            }}
            options={calculationTypeOptions}
            className="w-full"
          />
        </div>
        {touchedFields.has("calculation_type") &&
          getFieldError(validation?.errors ?? [], "calculation_type") && (
            <p className="text-sm font-medium text-destructive">
              {getFieldError(validation?.errors ?? [], "calculation_type")}
            </p>
          )}
      </div>

      {needsValuationBasis && (
        <div className="grid grid-cols-3 gap-6 pt-2">
         
          <div className="col-span-2">
            <FieldWithHelp
              label="Valuation"
              helpText="The company valuation amount in dollars"
              required
              error={
                touchedFields.has("valuation")
                  ? getFieldError(validation?.errors ?? [], "valuation")
                  : undefined
              }
              htmlFor="valuation"
            >
              <Input
                id={
                  roundIndex !== undefined
                    ? `round-${roundIndex}-valuation`
                    : "valuation"
                }
                type="text"
                value={round.valuation ? formatCurrency(round.valuation) : ""}
                onChange={(e) => {
                  const parsed = parseFormattedNumber(e.target.value);
                  onUpdate({
                    valuation: parsed > 0 ? parsed : undefined,
                  });
                }}
                onBlur={() => onFieldTouched("valuation")}
                placeholder="e.g., $10,000,000"
                className={`font-semibold ${
                  touchedFields.has("valuation") &&
                  getFieldError(validation?.errors ?? [], "valuation")
                    ? "border-destructive ring-destructive/20"
                    : "focus:ring-primary/20"
                }`}
              />
            </FieldWithHelp>
          </div>
          <FieldWithHelp
            label="Valuation Basis"
            helpText="Pre-money: valuation before investment. Post-money: valuation after investment."
            required
            error={
              touchedFields.has("valuation_basis")
                ? getFieldError(validation?.errors ?? [], "valuation_basis")
                : undefined
            }
            htmlFor="valuation-basis"
          >
            <Select
              value={round.valuation_basis || "pre_money"}
              onValueChange={(value: ValuationBasis) => {
                onUpdate({ valuation_basis: value });
                onFieldTouched("valuation_basis");
              }}
            >
              <SelectTrigger
                id={
                  roundIndex !== undefined
                    ? `round-${roundIndex}-valuation-basis`
                    : "valuation-basis"
                }
                className="focus:ring-primary/20"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pre_money">Pre-Money</SelectItem>
                <SelectItem value="post_money">Post-Money</SelectItem>
              </SelectContent>
            </Select>
          </FieldWithHelp>
        </div>
      )}
    </div>
  );
}
