/**
 * Global app state using Zustand
 */

import { create } from 'zustand';
import type { CapTable, Metrics, DiffItem, ChatMessage, ToolCall, ExecutionMode } from '../types/captable.types';

interface AppState {
  // Cap table state
  capTable: CapTable | null;
  metrics: Metrics | null;
  lastDiff: DiffItem[];
  
  // Chat state
  messages: ChatMessage[];
  isStreaming: boolean;
  
  // Tool orchestration state
  pendingToolCalls: ToolCall[];
  executionMode: ExecutionMode;
  toolCallHistory: ToolCall[];
  
  // Model config
  provider: string;
  model: string;
  
  // Actions
  setCapTable: (capTable: CapTable) => void;
  setMetrics: (metrics: Metrics) => void;
  setLastDiff: (diff: DiffItem[]) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setIsStreaming: (streaming: boolean) => void;
  setModelConfig: (provider: string, model: string) => void;
  reset: () => void;
  addPendingToolCall: (toolCall: ToolCall) => void;
  removePendingToolCall: (toolCallId: string) => void;
  setExecutionMode: (mode: ExecutionMode) => void;
  addToolCallToHistory: (toolCall: ToolCall) => void;
}

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

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  capTable: initialCapTable,
  metrics: initialMetrics,
  lastDiff: [],
  messages: [],
  isStreaming: false,
  pendingToolCalls: [],
  executionMode: 'auto',
  toolCallHistory: [],
  provider: 'openai',
  model: 'gpt-4',
  
  // Actions
  setCapTable: (capTable) => set({ capTable }),
  setMetrics: (metrics) => set({ metrics }),
  setLastDiff: (lastDiff) => set({ lastDiff }),
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  setMessages: (messages) => set({ messages }),
  setIsStreaming: (isStreaming) => set({ isStreaming }),
  setModelConfig: (provider, model) => set({ provider, model }),
  reset: () => set({
    capTable: initialCapTable,
    metrics: initialMetrics,
    lastDiff: [],
    messages: [],
    isStreaming: false,
    pendingToolCalls: [],
    toolCallHistory: []
  }),
  addPendingToolCall: (toolCall) => set((state) => ({
    pendingToolCalls: [...state.pendingToolCalls, toolCall]
  })),
  removePendingToolCall: (toolCallId) => set((state) => ({
    pendingToolCalls: state.pendingToolCalls.filter(tc => tc.id !== toolCallId)
  })),
  setExecutionMode: (mode) => set({ executionMode: mode }),
  addToolCallToHistory: (toolCall) => set((state) => ({
    toolCallHistory: [...state.toolCallHistory, toolCall]
  }))
}));

