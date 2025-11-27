/**
 * Validation utilities for cap table data
 */

import type { Round, Instrument } from "@/types/cap-table";

export interface FieldError {
  field: string;
  message: string;
}

export interface RoundValidation {
  isValid: boolean;
  errors: FieldError[];
}

export function validateRound(
  round: Round,
  allRounds?: Round[],
  currentRoundIndex?: number
): RoundValidation {
  const errors: FieldError[] = [];

  if (!round.name || round.name.trim() === "") {
    errors.push({ field: "name", message: "Rounds must have a name" });
  } else if (allRounds && currentRoundIndex !== undefined) {
    // Check for duplicate round names (excluding current round)
    const duplicateIndex = allRounds.findIndex(
      (r, index) =>
        index !== currentRoundIndex &&
        r.name.trim().toLowerCase() === round.name.trim().toLowerCase()
    );
    if (duplicateIndex !== -1) {
      errors.push({ field: "name", message: "Rounds must have unique names" });
    }
  }

  if (!round.round_date) {
    errors.push({ field: "round_date", message: "Add a date for the round" });
  }

  if (!round.calculation_type) {
    errors.push({
      field: "calculation_type",
      message: "Choose a calculation type for the round",
    });
  }

  // Validate dilution_method on instruments if provided
  round.instruments.forEach((instrument, index) => {
    if (
      "dilution_method" in instrument &&
      instrument.dilution_method !== undefined &&
      instrument.dilution_method !== null
    ) {
      const validDilutionMethods = [
        "full_ratchet",
        "narrow_based_weighted_average",
        "broad_based_weighted_average",
      ];
      if (!validDilutionMethods.includes(instrument.dilution_method)) {
        errors.push({
          field: `instruments[${index}].dilution_method`,
          message: `Invalid dilution method. Must be one of: ${validDilutionMethods.join(", ")}`,
        });
      }
    }
  });

  const needsValuationBasis = [
    "valuation_based",
    "convertible",
    "safe",
  ].includes(round.calculation_type);

  if (needsValuationBasis) {
    if (!round.valuation_basis) {
      errors.push({
        field: "valuation_basis",
        message: "Add a valuation basis",
      });
    }
    if (!round.valuation || round.valuation <= 0) {
      errors.push({
        field: "valuation",
        message: "Valuation must be greater than 0",
      });
    }
  }

  // Check if round has any instruments or pro-rata allocations
  const regularInstruments = (round.instruments || []).filter(
    (inst) => !("pro_rata_type" in inst)
  );
  const proRataInstruments = (round.instruments || []).filter(
    (inst) => "pro_rata_type" in inst
  );

  if (regularInstruments.length === 0 && proRataInstruments.length === 0) {
    errors.push({
      field: "instruments",
      message:
        "Add at least one instrument or pro-rata allocation to the round",
    });
  }

  // Validate instruments
  (round.instruments || []).forEach((instrument, index) => {
    const prefix = `instruments[${index}]`;

    if (!("holder_name" in instrument) || !instrument.holder_name) {
      errors.push({
        field: `${prefix}.holder_name`,
        message: "Add a holder",
      });
    }

    if (!("class_name" in instrument) || !instrument.class_name) {
      errors.push({
        field: `${prefix}.class_name`,
        message: "Add a class name",
      });
    }

    // Type-specific validation
    if ("initial_quantity" in instrument && instrument.initial_quantity <= 0) {
      errors.push({
        field: `${prefix}.initial_quantity`,
        message: "Initial quantity must be greater than 0",
      });
    }

    if ("target_percentage" in instrument) {
      if (
        instrument.target_percentage <= 0 ||
        instrument.target_percentage >= 1
      ) {
        errors.push({
          field: `${prefix}.target_percentage`,
          message: "Target percentage must be between 0 and 100%",
        });
      }
    }

    if (
      "investment_amount" in instrument &&
      instrument.investment_amount <= 0
    ) {
      errors.push({
        field: `${prefix}.investment_amount`,
        message: "Investment amount must be greater than 0",
      });
    }

    // Validate pro_rata_rights on regular instruments (not pro-rata allocations)
    if (!("pro_rata_type" in instrument)) {
      const proRataRights = (instrument as any).pro_rata_rights;
      if (proRataRights === "super") {
        const proRataPercentage = (instrument as any).pro_rata_percentage;
        if (
          !proRataPercentage ||
          proRataPercentage <= 0 ||
          proRataPercentage >= 1
        ) {
          errors.push({
            field: `${prefix}.pro_rata_percentage`,
            message:
              "Pro-rata percentage must be between 0 and 100% when pro-rata rights is 'super'",
          });
        }
      }
    }

    // Validate pro-rata allocation fields
    if ("pro_rata_type" in instrument) {
      if (instrument.pro_rata_type === "super") {
        if (
          !instrument.pro_rata_percentage ||
          instrument.pro_rata_percentage <= 0 ||
          instrument.pro_rata_percentage >= 1
        ) {
          errors.push({
            field: `${prefix}.pro_rata_percentage`,
            message:
              "Pro-rata percentage must be between 0 and 100% for super pro-rata",
          });
        }
      }

      // Validate exercise_type
      const exerciseType = (instrument as any).exercise_type;
      if (
        !exerciseType ||
        (exerciseType !== "full" && exerciseType !== "partial")
      ) {
        errors.push({
          field: `${prefix}.exercise_type`,
          message: "Choose an exercise type for the pro-rata allocation",
        });
      }

      // Validate based on exercise type
      if (exerciseType === "full") {
        // For full exercise, partial exercise fields should not be provided
        const partialAmount = (instrument as any).partial_exercise_amount;
        const partialPercentage = (instrument as any)
          .partial_exercise_percentage;

        if (partialAmount !== undefined && partialAmount !== null) {
          errors.push({
            field: `${prefix}.partial_exercise_amount`,
            message:
              "Partial exercise amount should not be provided when exercise type is 'full'",
          });
        }

        if (partialPercentage !== undefined && partialPercentage !== null) {
          errors.push({
            field: `${prefix}.partial_exercise_percentage`,
            message:
              "Partial exercise percentage should not be provided when exercise type is 'full'",
          });
        }
      } else if (exerciseType === "partial") {
        // For partial exercise, at least one partial exercise field must be provided
        const partialAmount = (instrument as any).partial_exercise_amount;
        const partialPercentage = (instrument as any)
          .partial_exercise_percentage;

        if (
          (partialAmount === undefined || partialAmount === null) &&
          (partialPercentage === undefined || partialPercentage === null)
        ) {
          errors.push({
            field: `${prefix}.partial_exercise`,
            message:
              "Either partial_exercise_amount or partial_exercise_percentage must be provided for partial exercise",
          });
        }

        // Validate partial_exercise_amount if provided
        if (partialAmount !== undefined && partialAmount !== null) {
          if (partialAmount <= 0) {
            errors.push({
              field: `${prefix}.partial_exercise_amount`,
              message: "Partial exercise amount must be greater than 0",
            });
          }
        }

        // Validate partial_exercise_percentage if provided
        if (partialPercentage !== undefined && partialPercentage !== null) {
          if (partialPercentage <= 0 || partialPercentage >= 1) {
            errors.push({
              field: `${prefix}.partial_exercise_percentage`,
              message:
                "Partial exercise percentage must be greater than 0 and less than 100%",
            });
          }

          // For super pro-rata, validate that partial exercise percentage is lower than super pro-rata percentage
          if (
            instrument.pro_rata_type === "super" &&
            instrument.pro_rata_percentage !== undefined
          ) {
            if (partialPercentage >= instrument.pro_rata_percentage) {
              errors.push({
                field: `${prefix}.partial_exercise_percentage`,
                message:
                  "Partial exercise percentage must be lower than super pro-rata percentage",
              });
            }
          }
        }
      }
    }

    if ("interest_rate" in instrument) {
      if (instrument.interest_rate < 0 || instrument.interest_rate >= 1) {
        errors.push({
          field: `${prefix}.interest_rate`,
          message: "Interest rate must be between 0 and 100%",
        });
      }
    }

    if ("discount_rate" in instrument) {
      if (instrument.discount_rate < 0 || instrument.discount_rate >= 1) {
        errors.push({
          field: `${prefix}.discount_rate`,
          message: "Discount rate must be between 0 and 100%",
        });
      }
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
  };
}

export function getFieldError(
  errors: FieldError[],
  field: string
): string | undefined {
  return errors.find((e) => e.field === field)?.message;
}
