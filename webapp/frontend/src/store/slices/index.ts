/**
 * Store Slices
 * 
 * Centralized export for all Zustand slices.
 */

export { 
  createCapTableSlice, 
  initialCapTableState,
  type CapTableSlice,
  type CapTableState,
  type CapTableActions
} from './captableSlice';

export { 
  createChatSlice, 
  initialChatState,
  type ChatSlice,
  type ChatState,
  type ChatActions
} from './chatSlice';

export { 
  createToolsSlice, 
  initialToolsState,
  type ToolsSlice,
  type ToolsState,
  type ToolsActions
} from './toolsSlice';

export { 
  createConfigSlice, 
  initialConfigState,
  type ConfigSlice,
  type ConfigState,
  type ConfigActions
} from './configSlice';

