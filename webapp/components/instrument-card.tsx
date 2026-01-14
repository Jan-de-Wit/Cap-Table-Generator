"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Pencil,
  Trash2,
  User,
  Building2,
  DollarSign,
  Percent,
  Calendar,
  TrendingUp,
  FileText,
} from "lucide-react";
import type { Instrument, CalculationType } from "@/types/cap-table";
import type { RoundValidation } from "@/lib/validation";
import { getFieldError } from "@/lib/validation";
import {
  formatCurrency,
  formatNumber,
  decimalToPercentage,
} from "@/lib/formatters";

interface InstrumentCardProps {
  instrument: Instrument;
  calculationType: CalculationType;
  displayIndex: number;
  actualIndex: number;
  validation?: RoundValidation;
  onEdit: () => void;
  onDelete: () => void;
}

export function InstrumentCard({
  instrument,
  calculationType,
  displayIndex,
  actualIndex,
  validation,
  onEdit,
  onDelete,
}: InstrumentCardProps) {
  const hasError = getFieldError(
    validation?.errors ?? [],
    `instruments[${actualIndex}]`
  );

  const getInstrumentDetails = () => {
    const details: { label: string; value: string; icon: React.ReactNode }[] =
      [];

    if ("holder_name" in instrument && instrument.holder_name) {
      details.push({
        label: "Holder",
        value: instrument.holder_name,
        icon: <User className="h-3.5 w-3.5" />,
      });
    }
    if ("class_name" in instrument && instrument.class_name) {
      details.push({
        label: "Class",
        value: instrument.class_name,
        icon: <Building2 className="h-3.5 w-3.5" />,
      });
    }

    if (
      calculationType === "fixed_shares" &&
      "initial_quantity" in instrument
    ) {
      details.push({
        label: "Shares",
        value: formatNumber(instrument.initial_quantity),
        icon: <FileText className="h-3.5 w-3.5" />,
      });
    }

    if (
      calculationType === "target_percentage" &&
      "target_percentage" in instrument
    ) {
      const isTopUp = (instrument as any).target_is_top_up || false;
      details.push({
        label: isTopUp ? "Top-up" : "Target",
        value: `${decimalToPercentage(instrument.target_percentage).toFixed(
          2
        )}%`,
        icon: <Percent className="h-3.5 w-3.5" />,
      });
    }

    if (
      (calculationType === "valuation_based" ||
        calculationType === "convertible" ||
        calculationType === "safe") &&
      "investment_amount" in instrument
    ) {
      details.push({
        label: "Investment",
        value: formatCurrency(instrument.investment_amount),
        icon: <DollarSign className="h-3.5 w-3.5" />,
      });
    }

    if (calculationType === "convertible" && "interest_rate" in instrument) {
      details.push({
        label: "Interest Rate",
        value: `${decimalToPercentage(instrument.interest_rate).toFixed(2)}%`,
        icon: <Percent className="h-3.5 w-3.5" />,
      });
      if ("payment_date" in instrument && instrument.payment_date) {
        details.push({
          label: "Payment Date",
          value: new Date(instrument.payment_date).toLocaleDateString(),
          icon: <Calendar className="h-3.5 w-3.5" />,
        });
      }
      if (
        "expected_conversion_date" in instrument &&
        instrument.expected_conversion_date
      ) {
        details.push({
          label: "Conversion Date",
          value: new Date(
            instrument.expected_conversion_date
          ).toLocaleDateString(),
          icon: <Calendar className="h-3.5 w-3.5" />,
        });
      }
      if ("discount_rate" in instrument) {
        details.push({
          label: "Discount",
          value: `${decimalToPercentage(instrument.discount_rate ?? 0).toFixed(
            2
          )}%`,
          icon: <TrendingUp className="h-3.5 w-3.5" />,
        });
      }
    }

    if (
      calculationType === "safe" &&
      "expected_conversion_date" in instrument
    ) {
      if (instrument.expected_conversion_date) {
        details.push({
          label: "Conversion Date",
          value: new Date(
            instrument.expected_conversion_date
          ).toLocaleDateString(),
          icon: <Calendar className="h-3.5 w-3.5" />,
        });
      }
      if ("discount_rate" in instrument) {
        details.push({
          label: "Discount",
          value: `${decimalToPercentage(instrument.discount_rate ?? 0).toFixed(
            2
          )}%`,
          icon: <TrendingUp className="h-3.5 w-3.5" />,
        });
      }
    }

    return details;
  };

  const details = getInstrumentDetails();

  return (
    <Card
      className={`group hover:shadow-md transition-all border-border/50 ${
        hasError
          ? "border-destructive/50 bg-destructive/5"
          : "hover:border-primary/30"
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/10 text-primary font-semibold text-xs shrink-0">
                {displayIndex + 1}
              </div>
              <div className="flex items-center gap-2 flex-1">
                <h4 className="font-semibold text-sm text-foreground">
                  Instrument {displayIndex + 1}
                </h4>
                {hasError && (
                  <Badge variant="destructive" className="text-xs font-medium">
                    Error
                  </Badge>
                )}
              </div>
            </div>
            {details.length > 0 && (
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 pl-11">
                {details.map((detail, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <div className="text-muted-foreground flex items-center gap-1.5 shrink-0">
                      <span className="text-muted-foreground/70">
                        {detail.icon}
                      </span>
                      <span className="text-xs font-medium">
                        {detail.label}:
                      </span>
                    </div>
                    <span className="font-semibold text-foreground">
                      {detail.value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onEdit}
              className="h-8 w-8 p-0 hover:bg-accent"
              title="Edit instrument"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onDelete}
              className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
              title="Delete instrument"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
