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
}

export function RoundParametersSection({
  round,
  touchedFields,
  validation,
  onUpdate,
  onFieldTouched,
}: RoundParametersSectionProps) {
  const needsValuationBasis = [
    "valuation_based",
    "convertible",
    "safe",
  ].includes(round.calculation_type);

  return (
    <div className="space-y-6">
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
            id="round-name"
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
            id="round-date"
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

      <FieldWithHelp
        label="Calculation Type"
        helpText="Determines how share quantities are calculated for instruments in this round"
        required
        htmlFor="calculation-type"
      >
        <Select
          value={round.calculation_type}
          onValueChange={(value: CalculationType) => {
            const updates: Partial<Round> = { calculation_type: value };
            // Clear instruments when changing calculation type
            if (round.calculation_type !== value) {
              updates.instruments = [];
            }
            // Clear valuation fields if not needed
            if (!["valuation_based", "convertible", "safe"].includes(value)) {
              updates.valuation_basis = undefined;
              updates.valuation = undefined;
            }
            onUpdate(updates);
            onFieldTouched("calculation_type");
          }}
        >
          <SelectTrigger
            id="calculation-type"
            className="focus:ring-primary/20"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fixed_shares">Fixed Shares</SelectItem>
            <SelectItem value="target_percentage">Target Percentage</SelectItem>
            <SelectItem value="valuation_based">Valuation Based</SelectItem>
            <SelectItem value="convertible">Convertible</SelectItem>
            <SelectItem value="safe">SAFE</SelectItem>
          </SelectContent>
        </Select>
      </FieldWithHelp>

      {needsValuationBasis && (
        <div className="grid grid-cols-2 gap-6">
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
              id="valuation"
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
                id="valuation-basis"
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
