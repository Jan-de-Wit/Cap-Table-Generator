/**
 * Custom hook for managing rounds state and operations
 */

import { useCallback, useRef } from "react";
import { toast } from "sonner";
import type { Round } from "@/types/cap-table";

// Helper function to find the next valuation-based round after a given round index
const findNextValuationBasedRound = (
  rounds: Round[],
  currentIndex: number
): Round | null => {
  for (let i = currentIndex + 1; i < rounds.length; i++) {
    if (rounds[i].calculation_type === "valuation_based") {
      return rounds[i];
    }
  }
  return null;
};

// Helper function to update conversion_round_ref for all convertible/SAFE rounds
const updateConversionRoundRefs = (roundsToUpdate: Round[]): Round[] => {
  return roundsToUpdate.map((round, index) => {
    // Only process convertible and SAFE rounds
    if (
      round.calculation_type !== "convertible" &&
      round.calculation_type !== "safe"
    ) {
      return round;
    }

    // Find the next valuation-based round
    const nextValuationRound = findNextValuationBasedRound(
      roundsToUpdate,
      index
    );

    // If a next valuation-based round exists, set conversion_round_ref
    if (nextValuationRound && nextValuationRound.name) {
      // Only update if not already set correctly
      if (round.conversion_round_ref !== nextValuationRound.name) {
        return {
          ...round,
          conversion_round_ref: nextValuationRound.name,
        };
      }
    } else if (round.conversion_round_ref) {
      // If there's no next valuation-based round but conversion_round_ref is set,
      // check if the referenced round still exists
      const referencedRound = roundsToUpdate.find(
        (r) => r.name === round.conversion_round_ref
      );
      if (!referencedRound) {
        return {
          ...round,
          conversion_round_ref: undefined,
        };
      }
    }

    return round;
  });
};

interface UseRoundsReturn {
  rounds: Round[];
  setRounds: React.Dispatch<React.SetStateAction<Round[]>>;
  addRound: () => void;
  updateRound: (index: number, round: Round) => void;
  deleteRound: (index: number) => void;
  reorderRounds: (startIndex: number, endIndex: number) => void;
  updateConversionRefs: (rounds: Round[]) => Round[];
}

export function useRounds(
  rounds: Round[],
  setRounds: React.Dispatch<React.SetStateAction<Round[]>>,
  selectedRoundIndex: number | null,
  setSelectedRoundIndex: React.Dispatch<React.SetStateAction<number | null>>
): UseRoundsReturn {
  const roundsRef = useRef(rounds);
  roundsRef.current = rounds;

  const updateConversionRefs = useCallback(
    (roundsToUpdate: Round[]) => updateConversionRoundRefs(roundsToUpdate),
    []
  );

  const addRound = useCallback(() => {
    const newRound: Round = {
      name: "",
      round_date: new Date().toISOString().split("T")[0],
      calculation_type: "fixed_shares",
      instruments: [],
    };
    setRounds((prev) => {
      const newIndex = prev.length;
      const updatedRounds = updateConversionRoundRefs([...prev, newRound]);
      setSelectedRoundIndex(newIndex);
      toast.success("Round added", {
        description: `Round ${newIndex + 1} has been created.`,
      });
      return updatedRounds;
    });
  }, [setRounds, setSelectedRoundIndex]);

  const updateRound = useCallback(
    (index: number, round: Round) => {
      setRounds((prev) => {
        const updated = [...prev];
        updated[index] = round;
        return updateConversionRoundRefs(updated);
      });
    },
    [setRounds]
  );

  const deleteRound = useCallback(
    (index: number) => {
      setRounds((prev) => {
        const deletedRound = prev[index];
        const roundName = deletedRound.name || `Round ${index + 1}`;

        // Store state for undo - create deep copies to avoid closure issues
        const previousRounds = prev.map((round) => ({
          ...round,
          instruments: round.instruments.map((inst) => ({ ...inst })),
        }));
        const previousSelectedIndex = selectedRoundIndex;

        // Perform deletion
        const filteredRounds = prev.filter((_, i) => i !== index);
        const updatedWithRefs = updateConversionRoundRefs(filteredRounds);

        // Update selected round index
        if (selectedRoundIndex === index) {
          // If we deleted the selected round, select the previous one or first one
          if (prev.length > 1) {
            setSelectedRoundIndex(index > 0 ? index - 1 : 0);
          } else {
            setSelectedRoundIndex(null);
          }
        } else if (selectedRoundIndex !== null && selectedRoundIndex > index) {
          // If we deleted a round before the selected one, adjust the index
          setSelectedRoundIndex(selectedRoundIndex - 1);
        }

        // Show toast with undo - capture values in closure with deep copies
        const undoRounds = previousRounds.map((round) => ({
          ...round,
          instruments: round.instruments.map((inst) => ({ ...inst })),
        }));
        const undoSelectedIndex = previousSelectedIndex;
        
        toast(`"${roundName}" has been removed.`, {
          description: 'Accident? Hit "Undo" to restore.',
          action: {
            label: "Undo",
            onClick: () => {
              setRounds(undoRounds);
              setSelectedRoundIndex(undoSelectedIndex);
              toast.success("Round restored", {
                description: `"${roundName}" has been restored.`,
              });
            },
          },
        });

        return updatedWithRefs;
      });
    },
    [setRounds, selectedRoundIndex, setSelectedRoundIndex]
  );

  const reorderRounds = useCallback(
    (startIndex: number, endIndex: number) => {
      if (startIndex === endIndex) return;

      setRounds((prev) => {
        const newRounds = Array.from(prev);
        const [removed] = newRounds.splice(startIndex, 1);
        newRounds.splice(endIndex, 0, removed);

        // Remove invalid pro-rata allocations after reordering
        // A pro-rata allocation is invalid if the holder doesn't have shares in previous rounds
        const cleanedRounds = newRounds.map((round, roundIndex) => {
          // Check if there are previous rounds
          if (roundIndex === 0) {
            // First round can't have pro-rata allocations
            return {
              ...round,
              instruments: round.instruments.filter(
                (inst) => !("pro_rata_type" in inst)
              ),
            };
          }

          // Collect all holders who have shares in previous rounds
          const holdersWithShares = new Set<string>();
          for (let i = 0; i < roundIndex; i++) {
            newRounds[i]?.instruments.forEach((instrument) => {
              // Only count regular instruments, not pro-rata allocations
              if (
                "holder_name" in instrument &&
                instrument.holder_name &&
                !("pro_rata_type" in instrument)
              ) {
                holdersWithShares.add(instrument.holder_name);
              }
            });
          }

          // Filter out pro-rata allocations for holders without shares in previous rounds
          const validInstruments = round.instruments.filter((instrument) => {
            // Keep all non-pro-rata instruments
            if (!("pro_rata_type" in instrument)) {
              return true;
            }

            // For pro-rata allocations, check if holder has shares in previous rounds
            if ("holder_name" in instrument && instrument.holder_name) {
              return holdersWithShares.has(instrument.holder_name);
            }

            return false;
          });

          return {
            ...round,
            instruments: validInstruments,
          };
        });

        const updatedWithRefs = updateConversionRoundRefs(cleanedRounds);

        // Update selected round index after reordering
        setSelectedRoundIndex((prevIndex) => {
          if (prevIndex === startIndex) {
            return endIndex;
          } else if (prevIndex !== null) {
            // Adjust selected index if it's affected by the reorder
            if (startIndex < prevIndex && endIndex >= prevIndex) {
              return prevIndex - 1;
            } else if (startIndex > prevIndex && endIndex <= prevIndex) {
              return prevIndex + 1;
            }
          }
          return prevIndex;
        });

        return updatedWithRefs;
      });
    },
    [setRounds, setSelectedRoundIndex]
  );

  return {
    rounds,
    setRounds,
    addRound,
    updateRound,
    deleteRound,
    reorderRounds,
    updateConversionRefs: updateConversionRefs,
  };
}

