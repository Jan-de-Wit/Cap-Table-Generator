/**
 * API client for backend communication
 */

import axios from 'axios';
import type { CapTable, Metrics } from '../types/captable.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8173';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ConfigResponse {
  provider: string;
  model: string;
}

export interface CapTableResponse {
  capTable?: CapTable | null;
  metrics?: Metrics | null;
}

/**
 * Get current LLM configuration
 */
export async function getConfig(): Promise<ConfigResponse> {
  const response = await api.get<ConfigResponse>('/api/config');
  return response.data;
}

/**
 * Get current cap table state
 */
export async function getCapTable(): Promise<CapTableResponse> {
  const response = await api.get<CapTableResponse>('/api/cap-table');
  return response.data;
}

/**
 * Download cap table as JSON
 */
export function downloadCapTableJSON() {
  window.open(`${API_BASE_URL}/api/cap-table/download?format=json`, '_blank');
}

/**
 * Download cap table as Excel
 */
export function downloadCapTableExcel() {
  window.open(`${API_BASE_URL}/api/cap-table/excel`, '_blank');
}

/**
 * Reset cap table to initial state
 */
export async function resetCapTable(): Promise<void> {
  await api.delete('/api/cap-table/reset');
}

/**
 * Chat with SSE streaming using fetch
 */
export async function chatStream(
  message: string,
  onMessage: (content: string) => void,
  onComplete: (data: CapTableResponse) => void,
  onError: (error: string) => void,
  conversationHistory?: Array<{ role: string; content: string }>,
  executionMode: 'auto' | 'approval' = 'auto',
  onToolProposal?: (proposal: any) => void,
  onToolResult?: (result: any) => void,
  onStatusMessage?: (message: any) => void
): Promise<() => void> {
  const controller = new AbortController();
  
  try {
    const body = conversationHistory 
      ? { messages: conversationHistory, execution_mode: executionMode } 
      : { message, execution_mode: executionMode };
    
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    
    if (!reader) {
      throw new Error('No response body');
    }
    
    let buffer = '';
    let completionHandled = false;
    let packetCount = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        // Process any remaining data in buffer
        if (buffer.trim()) {
          processEvent(buffer.trim());
        }
        // Stream is complete - call onComplete if not already called
        // This handles cases where the LLM response had no tool calls
        if (!completionHandled) {
          onComplete({ capTable: null, metrics: null });
        }
        break;
      }
      
      packetCount++;
      const chunk = decoder.decode(value, { stream: true });
      
      buffer += chunk;
      
      // Process complete events immediately, don't wait for stream to finish
      // Split by double newline to get complete events (handle both \n\n and \r\n\r\n)
      const parts = buffer.split(/\r\n\r\n|\n\n/);
      
      // Keep the last incomplete event in the buffer
      buffer = parts.pop() || '';
      
      // Process each complete event immediately
      for (const event of parts) {
        if (!event.trim()) continue;
        processEvent(event);
      }
    }
    
    function processEvent(event: string) {
      const lines = event.split('\n');
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;
        
        // SSE format: "data: {...}"
        if (trimmedLine.startsWith('data:')) {
          // Handle both "data: " and "data:" formats
          const data = trimmedLine.substring(trimmedLine.indexOf(':') + 1).trim();
          if (data === '[DONE]') {
            continue;
          }
          
          try {
            const parsed = JSON.parse(data);
            
            // Handle structured events
            if (parsed.event) {
              switch (parsed.event) {
                case 'content':
                  // Trigger immediate UI update for content chunks
                  onMessage(parsed.data);
                  break;
                case 'tool_proposal':
                  onToolProposal?.(parsed.data);
                  break;
                case 'tool_result':
                  onToolResult?.(parsed.data);
                  break;
                case 'cap_table_update':
                  completionHandled = true;
                  onComplete(parsed.data);
                  break;
                case 'error':
                  onError(parsed.data.error || 'Unknown error');
                  break;
                case 'thinking_start':
                case 'thinking_end':
                case 'tool_calls_start':
                case 'tool_execution_start':
                case 'tool_execution_complete':
                case 'tools_complete':
                case 'batch_start':
                case 'batch_complete':
                  // Forward status messages to the callback
                  onStatusMessage?.({ event: parsed.event, data: parsed.data });
                  break;
              }
            } else {
              // Legacy format support
              if (parsed.content) {
                onMessage(parsed.content);
              } else if (parsed.capTable && parsed.metrics) {
                completionHandled = true;
                onComplete(parsed);
              } else if (parsed.error) {
                onError(parsed.error);
              }
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    }
  } catch (error: any) {
    if (error.name !== 'AbortError') {
      onError(error.message || 'Connection error');
    }
  }
  
  return () => controller.abort();
}

/**
 * Approve pending tool calls
 */
export async function approveToolCalls(toolCallIds: string[]): Promise<any> {
  const response = await api.post('/api/tool/approve', toolCallIds);
  return response.data;
}

/**
 * Get pending tool calls
 */
export async function getPendingTools(): Promise<any[]> {
  const response = await api.get('/api/tool/pending');
  return response.data;
}

export default api;

