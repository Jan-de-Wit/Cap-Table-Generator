/**
 * Custom hook for managing validation state with incremental updates
 */

import { useMemo, useRef } from "react";
import type { Round } from "@/types/cap-table";
import { validateRound, type RoundValidation } from "@/lib/validation";

interface UseValidationOptions {
  /**
   * Enable incremental validation (only validate changed rounds)
   * @default true
   */
  incremental?: boolean;
}

/**
 * Custom hook for managing round validations with performance optimizations
 */
export function useValidation(
  rounds: Round[],
  options: UseValidationOptions = {}
) {
  const { incremental = true } = options;
  const previousRoundsRef = useRef<Round[]>([]);
  const validationCacheRef = useRef<Map<number, RoundValidation>>(new Map());

  const validations = useMemo(() => {
    // If not incremental, validate all rounds
    if (!incremental) {
      const allValidations = rounds.map((round, index) =>
        validateRound(round, rounds, index)
      );
      validationCacheRef.current.clear();
      allValidations.forEach((validation, index) => {
        validationCacheRef.current.set(index, validation);
      });
      previousRoundsRef.current = rounds;
      return allValidations;
    }

    // Incremental validation: only validate changed rounds
    const currentValidations: RoundValidation[] = [];
    const previousRounds = previousRoundsRef.current;

    for (let i = 0; i < rounds.length; i++) {
      const currentRound = rounds[i];
      const previousRound = previousRounds[i];

      // Check if round has changed
      const roundChanged =
        !previousRound ||
        JSON.stringify(previousRound) !== JSON.stringify(currentRound) ||
        previousRounds.length !== rounds.length;

      if (roundChanged) {
        // Round changed, validate it
        const validation = validateRound(currentRound, rounds, i);
        validationCacheRef.current.set(i, validation);
        currentValidations[i] = validation;
      } else {
        // Round unchanged, use cached validation
        const cached = validationCacheRef.current.get(i);
        if (cached) {
          currentValidations[i] = cached;
        } else {
          // Fallback: validate if cache miss
          const validation = validateRound(currentRound, rounds, i);
          validationCacheRef.current.set(i, validation);
          currentValidations[i] = validation;
        }
      }
    }

    // Clean up cache for removed rounds
    if (rounds.length < previousRounds.length) {
      for (let i = rounds.length; i < previousRounds.length; i++) {
        validationCacheRef.current.delete(i);
      }
    }

    previousRoundsRef.current = rounds;
    return currentValidations;
  }, [rounds, incremental]);

  // Computed validation summary
  const validationSummary = useMemo(() => {
    const totalRounds = validations.length;
    const validRounds = validations.filter((v) => v.isValid).length;
    const invalidRounds = totalRounds - validRounds;
    const totalErrors = validations.reduce(
      (sum, v) => sum + v.errors.length,
      0
    );

    return {
      totalRounds,
      validRounds,
      invalidRounds,
      totalErrors,
      isValid: invalidRounds === 0 && totalRounds > 0,
    };
  }, [validations]);

  // Get validation for a specific round
  const getRoundValidation = (index: number): RoundValidation | undefined => {
    return validations[index];
  };

  // Get errors for a specific field
  const getFieldErrors = (roundIndex: number, field: string): string[] => {
    const validation = validations[roundIndex];
    if (!validation) return [];

    return validation.errors
      .filter((error) => error.field === field)
      .map((error) => error.message);
  };

  // Check if a specific round is valid
  const isRoundValid = (index: number): boolean => {
    return validations[index]?.isValid ?? false;
  };

  // Clear validation cache (useful for forced re-validation)
  const clearCache = () => {
    validationCacheRef.current.clear();
    previousRoundsRef.current = [];
  };

  return {
    validations,
    validationSummary,
    getRoundValidation,
    getFieldErrors,
    isRoundValid,
    clearCache,
  };
}





