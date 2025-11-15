"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { HolderSelector } from "@/components/holder-selector";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Trash2 } from "lucide-react";
import type {
  Round,
  Holder,
  Instrument,
  CalculationType,
  ValuationBasis,
  ProRataType,
  InterestType,
} from "@/types/cap-table";

interface RoundFormProps {
  round: Round;
  holders: Holder[];
  onUpdate: (round: Round) => void;
  onAddHolder: (name: string) => void;
  onDelete?: () => void;
}

export function RoundForm({
  round,
  holders,
  onUpdate,
  onAddHolder,
  onDelete,
}: RoundFormProps) {
  const updateRound = (updates: Partial<Round>) => {
    onUpdate({ ...round, ...updates });
  };

  const addInstrument = (instrument: Instrument) => {
    updateRound({
      instruments: [...round.instruments, instrument],
    });
  };

  const removeInstrument = (index: number) => {
    updateRound({
      instruments: round.instruments.filter((_, i) => i !== index),
    });
  };

  const updateInstrument = (index: number, updates: Partial<Instrument>) => {
    const updated = round.instruments.map((inst, i) =>
      i === index ? { ...inst, ...updates } : inst
    );
    updateRound({ instruments: updated });
  };

  const needsValuationBasis = ["valuation_based", "convertible", "safe"].includes(
    round.calculation_type
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Round: {round.name || "New Round"}</CardTitle>
          {onDelete && (
            <Button type="button" variant="outline" size="sm" onClick={onDelete}>
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Round Parameters */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="round-name">Round Name</Label>
            <Input
              id="round-name"
              value={round.name}
              onChange={(e) => updateRound({ name: e.target.value })}
              placeholder="e.g., Seed Round"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="round-date">Round Date</Label>
            <Input
              id="round-date"
              type="date"
              value={round.round_date}
              onChange={(e) => updateRound({ round_date: e.target.value })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="calculation-type">Calculation Type</Label>
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
              updateRound(updates);
            }}
          >
            <SelectTrigger id="calculation-type">
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
        </div>

        {needsValuationBasis && (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="valuation-basis">Valuation Basis</Label>
              <Select
                value={round.valuation_basis || "pre_money"}
                onValueChange={(value: ValuationBasis) =>
                  updateRound({ valuation_basis: value })
                }
              >
                <SelectTrigger id="valuation-basis">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pre_money">Pre-Money</SelectItem>
                  <SelectItem value="post_money">Post-Money</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="valuation">Valuation ($)</Label>
              <Input
                id="valuation"
                type="number"
                value={round.valuation || ""}
                onChange={(e) =>
                  updateRound({
                    valuation: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                placeholder="e.g., 10000000"
              />
            </div>
          </div>
        )}

        {round.calculation_type === "valuation_based" && (
          <div className="space-y-2">
            <Label htmlFor="price-per-share">Price Per Share (optional)</Label>
            <Input
              id="price-per-share"
              type="number"
              step="0.01"
              value={round.price_per_share || ""}
              onChange={(e) =>
                updateRound({
                  price_per_share: e.target.value
                    ? parseFloat(e.target.value)
                    : undefined,
                })
              }
              placeholder="e.g., 1.50"
            />
          </div>
        )}

        {/* Instruments */}
        <Tabs defaultValue="instruments" className="w-full">
          <TabsList>
            <TabsTrigger value="instruments">Round Instruments</TabsTrigger>
            <TabsTrigger value="pro-rata">Pro-Rata Allocations</TabsTrigger>
          </TabsList>

          <TabsContent value="instruments" className="space-y-4">
            <div className="space-y-4">
              {round.instruments
                .filter((inst) => !("pro_rata_type" in inst))
                .map((instrument, index) => (
                  <InstrumentForm
                    key={index}
                    instrument={instrument}
                    calculationType={round.calculation_type}
                    holders={holders}
                    onUpdate={(updates) => updateInstrument(index, updates)}
                    onDelete={() => removeInstrument(index)}
                    onAddHolder={onAddHolder}
                  />
                ))}
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  const newInstrument = createEmptyInstrument(round.calculation_type);
                  addInstrument(newInstrument);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Instrument
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="pro-rata" className="space-y-4">
            <div className="space-y-4">
              {round.instruments
                .filter((inst) => "pro_rata_type" in inst)
                .map((instrument, index) => {
                  const actualIndex = round.instruments.findIndex(
                    (inst) => inst === instrument
                  );
                  return (
                    <ProRataForm
                      key={actualIndex}
                      instrument={instrument as any}
                      holders={holders}
                      onUpdate={(updates) => updateInstrument(actualIndex, updates)}
                      onDelete={() => removeInstrument(actualIndex)}
                      onAddHolder={onAddHolder}
                    />
                  );
                })}
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  addInstrument({
                    holder_name: "",
                    class_name: "",
                    pro_rata_type: "standard",
                  });
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Pro-Rata Allocation
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

function InstrumentForm({
  instrument,
  calculationType,
  holders,
  onUpdate,
  onDelete,
  onAddHolder,
}: {
  instrument: Instrument;
  calculationType: CalculationType;
  holders: Holder[];
  onUpdate: (updates: Partial<Instrument>) => void;
  onDelete: () => void;
  onAddHolder: (name: string) => void;
}) {
  return (
    <Card className="bg-muted/50">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <h4 className="font-semibold">Instrument</h4>
          <Button type="button" variant="ghost" size="sm" onClick={onDelete}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Holder</Label>
              <HolderSelector
                value={
                  "holder_name" in instrument ? instrument.holder_name : ""
                }
                onChange={(name) => onUpdate({ holder_name: name })}
                holders={holders}
                onAddHolder={onAddHolder}
              />
            </div>
            <div className="space-y-2">
              <Label>Class Name</Label>
              <Input
                value={"class_name" in instrument ? instrument.class_name : ""}
                onChange={(e) => onUpdate({ class_name: e.target.value })}
                placeholder="e.g., Series A Preferred"
              />
            </div>
          </div>

          {calculationType === "fixed_shares" && (
            <div className="space-y-2">
              <Label>Initial Quantity</Label>
              <Input
                type="number"
                value={
                  "initial_quantity" in instrument
                    ? instrument.initial_quantity
                    : ""
                }
                onChange={(e) =>
                  onUpdate({
                    initial_quantity: e.target.value
                      ? parseFloat(e.target.value)
                      : 0,
                  })
                }
                placeholder="e.g., 1000000"
              />
            </div>
          )}

          {calculationType === "target_percentage" && (
            <div className="space-y-2">
              <Label>Target Percentage (0-1)</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={
                  "target_percentage" in instrument
                    ? instrument.target_percentage
                    : ""
                }
                onChange={(e) =>
                  onUpdate({
                    target_percentage: e.target.value
                      ? parseFloat(e.target.value)
                      : 0,
                  })
                }
                placeholder="e.g., 0.20 for 20%"
              />
            </div>
          )}

          {calculationType === "valuation_based" && (
            <div className="space-y-2">
              <Label>Investment Amount ($)</Label>
              <Input
                type="number"
                value={
                  "investment_amount" in instrument
                    ? instrument.investment_amount
                    : ""
                }
                onChange={(e) =>
                  onUpdate({
                    investment_amount: e.target.value
                      ? parseFloat(e.target.value)
                      : 0,
                  })
                }
                placeholder="e.g., 2000000"
              />
            </div>
          )}

          {calculationType === "convertible" && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Investment Amount ($)</Label>
                <Input
                  type="number"
                  value={
                    "investment_amount" in instrument
                      ? instrument.investment_amount
                      : ""
                  }
                  onChange={(e) =>
                    onUpdate({
                      investment_amount: e.target.value
                        ? parseFloat(e.target.value)
                        : 0,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Interest Rate (0-1)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={
                    "interest_rate" in instrument ? instrument.interest_rate : ""
                  }
                  onChange={(e) =>
                    onUpdate({
                      interest_rate: e.target.value
                        ? parseFloat(e.target.value)
                        : 0,
                    })
                  }
                  placeholder="e.g., 0.08 for 8%"
                />
              </div>
              <div className="space-y-2">
                <Label>Payment Date</Label>
                <Input
                  type="date"
                  value={
                    "payment_date" in instrument ? instrument.payment_date : ""
                  }
                  onChange={(e) => onUpdate({ payment_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Expected Conversion Date</Label>
                <Input
                  type="date"
                  value={
                    "expected_conversion_date" in instrument
                      ? instrument.expected_conversion_date
                      : ""
                  }
                  onChange={(e) =>
                    onUpdate({ expected_conversion_date: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Interest Type</Label>
                <Select
                  value={
                    "interest_type" in instrument
                      ? instrument.interest_type
                      : "simple"
                  }
                  onValueChange={(value: InterestType) =>
                    onUpdate({ interest_type: value })
                  }
                >
                  <SelectTrigger>
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
              </div>
              <div className="space-y-2">
                <Label>Discount Rate (0-1)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={
                    "discount_rate" in instrument ? instrument.discount_rate : ""
                  }
                  onChange={(e) =>
                    onUpdate({
                      discount_rate: e.target.value
                        ? parseFloat(e.target.value)
                        : 0,
                    })
                  }
                  placeholder="e.g., 0.20 for 20%"
                />
              </div>
            </div>
          )}

          {calculationType === "safe" && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Investment Amount ($)</Label>
                <Input
                  type="number"
                  value={
                    "investment_amount" in instrument
                      ? instrument.investment_amount
                      : ""
                  }
                  onChange={(e) =>
                    onUpdate({
                      investment_amount: e.target.value
                        ? parseFloat(e.target.value)
                        : 0,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Expected Conversion Date</Label>
                <Input
                  type="date"
                  value={
                    "expected_conversion_date" in instrument
                      ? instrument.expected_conversion_date
                      : ""
                  }
                  onChange={(e) =>
                    onUpdate({ expected_conversion_date: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Discount Rate (0-1)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={
                    "discount_rate" in instrument ? instrument.discount_rate : ""
                  }
                  onChange={(e) =>
                    onUpdate({
                      discount_rate: e.target.value
                        ? parseFloat(e.target.value)
                        : 0,
                    })
                  }
                  placeholder="e.g., 0.20 for 20%"
                />
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ProRataForm({
  instrument,
  holders,
  onUpdate,
  onDelete,
  onAddHolder,
}: {
  instrument: any;
  holders: Holder[];
  onUpdate: (updates: Partial<any>) => void;
  onDelete: () => void;
  onAddHolder: (name: string) => void;
}) {
  return (
    <Card className="bg-muted/50">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <h4 className="font-semibold">Pro-Rata Allocation</h4>
          <Button type="button" variant="ghost" size="sm" onClick={onDelete}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Holder</Label>
              <HolderSelector
                value={instrument.holder_name || ""}
                onChange={(name) => onUpdate({ holder_name: name })}
                holders={holders}
                onAddHolder={onAddHolder}
              />
            </div>
            <div className="space-y-2">
              <Label>Class Name</Label>
              <Input
                value={instrument.class_name || ""}
                onChange={(e) => onUpdate({ class_name: e.target.value })}
                placeholder="e.g., Common Stock"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Pro-Rata Type</Label>
            <Select
              value={instrument.pro_rata_type || "standard"}
              onValueChange={(value: ProRataType) => {
                const updates: any = { pro_rata_type: value };
                if (value !== "super") {
                  updates.pro_rata_percentage = undefined;
                }
                onUpdate(updates);
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="standard">Standard</SelectItem>
                <SelectItem value="super">Super</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {instrument.pro_rata_type === "super" && (
            <div className="space-y-2">
              <Label>Pro-Rata Percentage (0-1)</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={instrument.pro_rata_percentage || ""}
                onChange={(e) =>
                  onUpdate({
                    pro_rata_percentage: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  })
                }
                placeholder="e.g., 0.15 for 15%"
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function createEmptyInstrument(
  calculationType: CalculationType
): Instrument {
  switch (calculationType) {
    case "fixed_shares":
      return {
        holder_name: "",
        class_name: "",
        initial_quantity: 0,
      };
    case "target_percentage":
      return {
        holder_name: "",
        class_name: "",
        target_percentage: 0,
      };
    case "valuation_based":
      return {
        holder_name: "",
        class_name: "",
        investment_amount: 0,
      };
    case "convertible":
      return {
        holder_name: "",
        class_name: "",
        investment_amount: 0,
        interest_rate: 0,
        payment_date: "",
        expected_conversion_date: "",
        interest_type: "simple",
        discount_rate: 0,
      };
    case "safe":
      return {
        holder_name: "",
        class_name: "",
        investment_amount: 0,
        expected_conversion_date: "",
        discount_rate: 0,
      };
  }
}

