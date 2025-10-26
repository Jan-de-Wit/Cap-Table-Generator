/**
 * Tools Slice
 * 
 * Manages tool execution state including pending calls and execution mode.
 */

import type { ToolCall, ExecutionMode } from '../../types/captable.types';

export interface ToolsState {
  pendingToolCalls: ToolCall[];
  executionMode: ExecutionMode;
  toolCallHistory: ToolCall[];
}

export interface ToolsActions {
  addPendingToolCall: (toolCall: ToolCall) => void;
  removePendingToolCall: (toolCallId: string) => void;
  setExecutionMode: (mode: ExecutionMode) => void;
  addToolCallToHistory: (toolCall: ToolCall) => void;
  clearPendingToolCalls: () => void;
}

export type ToolsSlice = ToolsState & ToolsActions;

export const initialToolsState: ToolsState = {
  pendingToolCalls: [],
  executionMode: 'auto',
  toolCallHistory: []
};

export const createToolsSlice = (set: any) => ({
  ...initialToolsState,
  
  addPendingToolCall: (toolCall: ToolCall) => 
    set((state: any) => ({
      pendingToolCalls: [...state.pendingToolCalls, toolCall]
    })),
    
  removePendingToolCall: (toolCallId: string) => 
    set((state: any) => ({
      pendingToolCalls: state.pendingToolCalls.filter((tc: ToolCall) => tc.id !== toolCallId)
    })),
    
  setExecutionMode: (mode: ExecutionMode) => 
    set({ executionMode: mode }),
    
  addToolCallToHistory: (toolCall: ToolCall) => 
    set((state: any) => ({
      toolCallHistory: [...state.toolCallHistory, toolCall]
    })),
    
  clearPendingToolCalls: () => 
    set({ pendingToolCalls: [] }),
});

