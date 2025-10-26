/**
 * Global app state using Zustand
 * 
 * Composes slices for cap table, chat, tools, and config.
 */

import { create } from 'zustand';
import { 
  createCapTableSlice, 
  initialCapTableState,
  type CapTableSlice 
} from './slices/captableSlice';
import { 
  createChatSlice, 
  initialChatState,
  type ChatSlice 
} from './slices/chatSlice';
import { 
  createToolsSlice, 
  initialToolsState,
  type ToolsSlice 
} from './slices/toolsSlice';
import { 
  createConfigSlice, 
  initialConfigState,
  type ConfigSlice 
} from './slices/configSlice';

export type AppState = CapTableSlice & ChatSlice & ToolsSlice & ConfigSlice & {
  reset: () => void;
};

export const useAppStore = create<AppState>((set) => ({
  // Cap table slice
  ...createCapTableSlice(set),
  
  // Chat slice
  ...createChatSlice(set),
  
  // Tools slice
  ...createToolsSlice(set),
  
  // Config slice
  ...createConfigSlice(set),
  
  // Global reset
  reset: () => set({
    ...initialCapTableState,
    ...initialChatState,
    ...initialToolsState,
    ...initialConfigState
  })
}));
