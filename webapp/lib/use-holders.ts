/**
 * Custom hook for managing holders state and operations
 */

import { useCallback, useEffect } from "react";
import { toast } from "sonner";
import type { Holder, Round } from "@/types/cap-table";

interface UseHoldersReturn {
  holders: Holder[];
  setHolders: React.Dispatch<React.SetStateAction<Holder[]>>;
  addHolder: (holder: Holder) => void;
  updateHolder: (oldName: string, updatedHolder: Holder) => void;
  deleteHolder: (holderName: string) => void;
  moveHolderToGroup: (holderName: string, newGroup: string | undefined) => void;
  inferHoldersFromRounds: (rounds: Round[]) => void;
}

export function useHolders(
  holders: Holder[],
  setHolders: React.Dispatch<React.SetStateAction<Holder[]>>,
  rounds: Round[],
  setRounds: React.Dispatch<React.SetStateAction<Round[]>>
): UseHoldersReturn {
  // Infer new holders from rounds (only add if they don't exist)
  const inferHoldersFromRounds = useCallback(
    (roundsToCheck: Round[]) => {
      setHolders((prev) => {
        const holderNames = new Set(prev.map((h) => h.name));
        const newHolders: Holder[] = [];

        roundsToCheck.forEach((round) => {
          round.instruments.forEach((instrument) => {
            if ("holder_name" in instrument && instrument.holder_name) {
              if (!holderNames.has(instrument.holder_name)) {
                newHolders.push({
                  name: instrument.holder_name,
                });
                holderNames.add(instrument.holder_name);
              }
            }
          });
        });

        return newHolders.length > 0 ? [...prev, ...newHolders] : prev;
      });
    },
    [setHolders]
  );

  // Auto-infer holders when rounds change
  useEffect(() => {
    inferHoldersFromRounds(rounds);
  }, [rounds, inferHoldersFromRounds]);

  const addHolder = useCallback(
    (holder: Holder) => {
      setHolders((prev) => {
        if (!prev.find((h) => h.name === holder.name)) {
          toast.success("Holder added", {
            description: `"${holder.name}" has been created.`,
          });
          return [...prev, holder];
        }
        return prev;
      });
    },
    [setHolders]
  );

  const updateHolder = useCallback(
    (oldName: string, updatedHolder: Holder) => {
      // Update holder in the holders list
      setHolders((prev) =>
        prev.map((h) => (h.name === oldName ? updatedHolder : h))
      );

      // Update all references to this holder in rounds
      setRounds((prev) =>
        prev.map((round) => ({
          ...round,
          instruments: round.instruments.map((inst) => {
            if ("holder_name" in inst && inst.holder_name === oldName) {
              return { ...inst, holder_name: updatedHolder.name };
            }
            return inst;
          }),
        }))
      );
    },
    [setHolders, setRounds]
  );

  const deleteHolder = useCallback(
    (holderName: string) => {
      setHolders((prevHolders) => {
        const deletedHolder = prevHolders.find((h) => h.name === holderName);
        if (!deletedHolder) return prevHolders;

        // Store state for undo
        const previousHolders = [...prevHolders];
        setRounds((prevRounds) => {
          const previousRounds = prevRounds.map((round) => ({
            ...round,
            instruments: [...round.instruments],
          }));

          // Remove all instruments that reference this holder from all rounds
          const updatedRounds = prevRounds.map((round) => ({
            ...round,
            instruments: round.instruments.filter(
              (inst) =>
                !("holder_name" in inst && inst.holder_name === holderName)
            ),
          }));

          // Show toast with undo
          toast(`"${holderName}" has been removed.`, {
            description:
              "The holder and all associated instruments have been removed.",
            action: {
              label: "Undo",
              onClick: () => {
                setHolders(previousHolders);
                setRounds(previousRounds);
                toast.success("Holder restored", {
                  description: `"${holderName}" and all instruments have been restored.`,
                });
              },
            },
          });

          return updatedRounds;
        });

        // Remove holder from holders list
        return prevHolders.filter((h) => h.name !== holderName);
      });
    },
    [setHolders, setRounds]
  );

  const moveHolderToGroup = useCallback(
    (holderName: string, newGroup: string | undefined) => {
      setHolders((prev) => {
        const holder = prev.find((h) => h.name === holderName);
        if (holder) {
          // Update holder in the holders list
          return prev.map((h) =>
            h.name === holderName ? { ...holder, group: newGroup } : h
          );
        }
        return prev;
      });
    },
    [setHolders]
  );

  return {
    holders,
    setHolders,
    addHolder,
    updateHolder,
    deleteHolder,
    moveHolderToGroup,
    inferHoldersFromRounds,
  };
}

