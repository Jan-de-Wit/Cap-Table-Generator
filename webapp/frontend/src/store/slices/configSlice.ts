/**
 * Config Slice
 * 
 * Manages model configuration and provider settings.
 */

export interface ConfigState {
  provider: string;
  model: string;
}

export interface ConfigActions {
  setModelConfig: (provider: string, model: string) => void;
}

export type ConfigSlice = ConfigState & ConfigActions;

export const initialConfigState: ConfigState = {
  provider: 'openai',
  model: 'gpt-4'
};

export const createConfigSlice = (set: any) => ({
  ...initialConfigState,
  
  setModelConfig: (provider: string, model: string) => 
    set({ provider, model }),
});

