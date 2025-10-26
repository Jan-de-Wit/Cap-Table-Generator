/**
 * Chat Slice
 * 
 * Manages chat messages and streaming state.
 */

import type { ChatMessage } from '../../types/captable.types';

export interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export interface ChatActions {
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setIsStreaming: (streaming: boolean) => void;
}

export type ChatSlice = ChatState & ChatActions;

export const initialChatState: ChatState = {
  messages: [],
  isStreaming: false
};

export const createChatSlice = (set: any) => ({
  ...initialChatState,
  
  addMessage: (message: ChatMessage) => 
    set((state: any) => ({ 
      messages: [...state.messages, message] 
    })),
    
  setMessages: (messages: ChatMessage[]) => 
    set({ messages }),
    
  setIsStreaming: (isStreaming: boolean) => 
    set({ isStreaming }),
});

