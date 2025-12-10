import * as React from "react";
import type { Round, Holder } from "@/types/cap-table";

interface HistoryState {
  rounds: Round[];
  holders: Holder[];
  selectedRoundIndex: number | null;
}

interface UseUndoRedoOptions {
  maxHistorySize?: number;
  debounceMs?: number;
}

interface UseUndoRedoReturn {
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  clearHistory: () => void;
  saveState: (state: HistoryState) => void;
}

const DEFAULT_MAX_HISTORY_SIZE = 50;
const DEFAULT_DEBOUNCE_MS = 300;

export function useUndoRedo(
  currentState: HistoryState,
  onStateChange: (state: HistoryState) => void,
  options: UseUndoRedoOptions = {}
): UseUndoRedoReturn {
  const { maxHistorySize = DEFAULT_MAX_HISTORY_SIZE, debounceMs = DEFAULT_DEBOUNCE_MS } = options;

  // History stack
  const [history, setHistory] = React.useState<HistoryState[]>([currentState]);
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const currentIndexRef = React.useRef(0);
  const isUndoRedoRef = React.useRef(false);
  const [isUndoRedo, setIsUndoRedo] = React.useState(false);
  const debounceTimerRef = React.useRef<NodeJS.Timeout | null>(null);

  // Keep refs in sync with state
  React.useEffect(() => {
    currentIndexRef.current = currentIndex;
  }, [currentIndex]);

  React.useEffect(() => {
    isUndoRedoRef.current = isUndoRedo;
  }, [isUndoRedo]);

  // Deep clone state to avoid reference issues
  const deepCloneState = React.useCallback((state: HistoryState): HistoryState => {
    return {
      rounds: state.rounds.map((round) => ({
        ...round,
        instruments: round.instruments.map((inst) => ({ ...inst })),
      })),
      holders: state.holders.map((holder) => ({ ...holder })),
      selectedRoundIndex: state.selectedRoundIndex,
    };
  }, []);

  // Save state to history
  const saveState = React.useCallback(
    (state: HistoryState) => {
      // Don't save if we're in the middle of undo/redo (check both state and ref for reliability)
      if (isUndoRedo || isUndoRedoRef.current) {
        return;
      }

      // Clear debounce timer if it exists
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = null;
      }

      // Debounce state saves to avoid too many history entries
      debounceTimerRef.current = setTimeout(() => {
        // Double-check we're not in undo/redo (race condition protection)
        if (isUndoRedoRef.current) {
          debounceTimerRef.current = null;
          return;
        }
        
        setHistory((prevHistory) => {
          // Triple-check we're not in undo/redo (extra protection)
          if (isUndoRedoRef.current) {
            return prevHistory;
          }
          
          const newState = deepCloneState(state);
          const prevIndex = currentIndexRef.current;
          
          // Slice history up to current index (removes any future history if we've undone)
          const newHistory = prevHistory.slice(0, prevIndex + 1);
          
          // Don't save if state hasn't changed
          const lastState = newHistory[newHistory.length - 1];
          if (
            lastState &&
            JSON.stringify(lastState.rounds) === JSON.stringify(newState.rounds) &&
            JSON.stringify(lastState.holders) === JSON.stringify(newState.holders) &&
            lastState.selectedRoundIndex === newState.selectedRoundIndex
          ) {
            return prevHistory; // No change, keep existing history
          }

          newHistory.push(newState);

          // Limit history size
          let newIndex = prevIndex + 1;
          if (newHistory.length > maxHistorySize) {
            newHistory.shift();
            newIndex = prevIndex; // Index stays same if we removed from front
          }

          // Update index
          setCurrentIndex(newIndex);
          
          return newHistory;
        });
        
        debounceTimerRef.current = null;
      }, debounceMs);
    },
    [isUndoRedo, maxHistorySize, debounceMs, deepCloneState]
  );

  // Undo function
  const undo = React.useCallback(() => {
    setHistory((prevHistory) => {
      if (currentIndex > 0) {
        const newIndex = currentIndex - 1;
        const stateToRestore = deepCloneState(prevHistory[newIndex]);
        
        // Set flag before state change
        isUndoRedoRef.current = true;
        setIsUndoRedo(true);
        setCurrentIndex(newIndex);
        onStateChange(stateToRestore);
        
        // Reset undo/redo flag after a short delay to ensure state updates complete
        setTimeout(() => {
          isUndoRedoRef.current = false;
          setIsUndoRedo(false);
        }, 100);
        
        return prevHistory;
      }
      return prevHistory;
    });
  }, [currentIndex, onStateChange, deepCloneState]);

  // Redo function
  const redo = React.useCallback(() => {
    setHistory((prevHistory) => {
      if (currentIndex < prevHistory.length - 1) {
        const newIndex = currentIndex + 1;
        const stateToRestore = deepCloneState(prevHistory[newIndex]);
        
        // Set flag before state change
        isUndoRedoRef.current = true;
        setIsUndoRedo(true);
        setCurrentIndex(newIndex);
        onStateChange(stateToRestore);
        
        // Reset undo/redo flag after a short delay to ensure state updates complete
        setTimeout(() => {
          isUndoRedoRef.current = false;
          setIsUndoRedo(false);
        }, 100);
        
        return prevHistory;
      }
      return prevHistory;
    });
  }, [currentIndex, onStateChange, deepCloneState]);

  // Clear history
  const clearHistory = React.useCallback(() => {
    setHistory([deepCloneState(currentState)]);
    setCurrentIndex(0);
  }, [currentState, deepCloneState]);

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Z or Cmd+Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        if (currentIndex > 0) {
          undo();
        }
      }
      // Ctrl+Shift+Z or Ctrl+Y or Cmd+Shift+Z or Cmd+Y for redo
      else if (
        ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "z") ||
        ((e.ctrlKey || e.metaKey) && e.key === "y")
      ) {
        e.preventDefault();
        if (currentIndex < history.length - 1) {
          redo();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, history.length, undo, redo]);

  // Cleanup debounce timer on unmount
  React.useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    canUndo: currentIndex > 0,
    canRedo: currentIndex < history.length - 1,
    undo,
    redo,
    clearHistory,
    saveState,
  };
}

