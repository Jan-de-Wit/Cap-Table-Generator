/**
 * Custom hook for localStorage persistence with automatic save/load
 */

import { useEffect, useRef } from "react";
import type { CapTableData } from "@/types/cap-table";

const STORAGE_KEY = "cap-table-data";
const STORAGE_VERSION_KEY = "cap-table-version";
const CURRENT_VERSION = "2.0";

interface UseLocalStorageOptions {
  enabled?: boolean;
  debounceMs?: number;
}

export function useLocalStoragePersistence(
  data: CapTableData | null,
  options: UseLocalStorageOptions = {}
) {
  const { enabled = true, debounceMs = 500 } = options;
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialLoadRef = useRef(true);

  // Save data to localStorage with debouncing
  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    if (isInitialLoadRef.current) {
      isInitialLoadRef.current = false;
      return; // Don't save on initial load
    }
    if (!data || (data.rounds.length === 0 && data.holders.length === 0)) {
      // Clear storage if data is empty
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(STORAGE_VERSION_KEY);
      return;
    }

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Debounce save operation
    saveTimeoutRef.current = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
      } catch (error) {
        console.warn("Failed to save to localStorage:", error);
        // Handle quota exceeded error
        if (
          error instanceof DOMException &&
          error.name === "QuotaExceededError"
        ) {
          console.error(
            "LocalStorage quota exceeded. Consider clearing old data."
          );
        }
      }
    }, debounceMs);

    // Cleanup timeout on unmount
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [data, enabled, debounceMs]);

  // Function to clear stored data
  const clearStorage = () => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_VERSION_KEY);
  };

  return { clearStorage };
}

/**
 * Load initial data from localStorage
 */
export function loadFromLocalStorage(): CapTableData | null {
  if (typeof window === "undefined") return null;

  try {
    const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
    const storedData = localStorage.getItem(STORAGE_KEY);

    if (storedData && storedVersion === CURRENT_VERSION) {
      const parsed = JSON.parse(storedData);
      if (
        parsed &&
        typeof parsed === "object" &&
        Array.isArray(parsed.holders) &&
        Array.isArray(parsed.rounds)
      ) {
        return parsed as CapTableData;
      }
    }
  } catch (error) {
    console.warn("Failed to load from localStorage:", error);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_VERSION_KEY);
  }

  return null;
}

/**
 * Clear localStorage data
 */
export function clearLocalStorage() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(STORAGE_VERSION_KEY);
}
