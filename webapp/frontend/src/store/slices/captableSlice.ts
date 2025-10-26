/**
 * Cap Table Slice
 * 
 * Manages cap table state, metrics, and diffs.
 */

import type { CapTable, Metrics, DiffItem } from '../../types/captable.types';

export interface CapTableState {
  capTable: CapTable | null;
  metrics: Metrics | null;
  lastDiff: DiffItem[];
}

export interface CapTableActions {
  setCapTable: (capTable: CapTable) => void;
  setMetrics: (metrics: Metrics) => void;
  setLastDiff: (diff: DiffItem[]) => void;
}

export type CapTableSlice = CapTableState & CapTableActions;

const initialCapTable: CapTable = {
  schema_version: '1.0',
  company: {
    name: 'Untitled Company'
  },
  holders: [],
  classes: [],
  instruments: []
};

const initialMetrics: Metrics = {
  totals: {
    authorized: 0,
    issued: 0,
    fullyDiluted: 0
  },
  ownership: [],
  pool: {
    size: 0,
    granted: 0,
    remaining: 0
  }
};

export const initialCapTableState: CapTableState = {
  capTable: initialCapTable,
  metrics: initialMetrics,
  lastDiff: []
};

export const createCapTableSlice = (set: any) => ({
  ...initialCapTableState,
  
  setCapTable: (capTable: CapTable) => 
    set({ capTable }),
    
  setMetrics: (metrics: Metrics) => 
    set({ metrics }),
    
  setLastDiff: (lastDiff: DiffItem[]) => 
    set({ lastDiff }),
});

