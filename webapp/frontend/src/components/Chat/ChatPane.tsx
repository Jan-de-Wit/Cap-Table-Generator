/**
 * ChatPane Component
 * Main chat interface with message history and input
 */

import { useState, useCallback, useRef } from 'react';
import { flushSync } from 'react-dom';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ToolCallApproval } from '../ToolCallApproval';
import type { StatusMessageData } from './StatusMessage';
import { useAppStore } from '../../store/appStore';
import { chatStream, approveToolCalls } from '../../services/api';

export function ChatPane() {
  const { 
    messages, 
    isStreaming, 
    addMessage, 
    setIsStreaming, 
    setCapTable, 
    setMetrics, 
    setLastDiff,
    pendingToolCalls,
    executionMode,
    addPendingToolCall,
    removePendingToolCall
  } = useAppStore();
  const [streamingContent, setStreamingContent] = useState('');
  const streamingRef = useRef('');
  const [statusMessages, setStatusMessages] = useState<StatusMessageData[]>([]);
  const [thinkingStatus, setThinkingStatus] = useState<{ isThinking: boolean; startTime: number } | null>(null);
  
  const handleSendMessage = useCallback(async (content: string) => {
    // Add user message
    addMessage({ role: 'user', content, timestamp: Date.now() });
    
    // Build conversation history for context
    const conversationHistory = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.content }));
    
    // Add current message to history
    conversationHistory.push({ role: 'user', content });
    
    // Start streaming
    setIsStreaming(true);
    setStreamingContent('');
    streamingRef.current = '';
    setStatusMessages([]);
    setThinkingStatus({ isThinking: true, startTime: Date.now() });
    
    let fullResponse = '';
    let currentSegment = '';
    
    try {
      await chatStream(
        content,
        // onMessage
        (chunk) => {
          fullResponse += chunk;
          currentSegment += chunk;
          streamingRef.current = currentSegment;
          // Use flushSync to force immediate DOM update for streaming
          flushSync(() => {
            setStreamingContent(currentSegment);
          });
        },
        // onComplete
        (data) => {
          // Add final segment if there's any content left
          if (currentSegment.trim()) {
            addMessage({ role: 'assistant', content: currentSegment, timestamp: Date.now() });
          }
          
          setStreamingContent('');
          streamingRef.current = '';
          setIsStreaming(false);
          
          // Update cap table state if provided
          if (data.capTable && data.metrics) {
            setCapTable(data.capTable);
            setMetrics(data.metrics);
          }
        },
        // onError
        (error) => {
          // If we have partial response, save it
          if (currentSegment.trim()) {
            addMessage({ role: 'assistant', content: currentSegment, timestamp: Date.now() });
          }
          
          // Show error as a separate message
          const errorMsg = error.includes('finish_reason') 
            ? 'The response was blocked by content safety filters. Please try rephrasing your request.'
            : `Error: ${error}`;
          
          addMessage({
            role: 'assistant',
            content: errorMsg,
            timestamp: Date.now()
          });
          
          setStreamingContent('');
          streamingRef.current = '';
          setIsStreaming(false);
        },
        conversationHistory,
        executionMode,
        // onToolProposal
        (proposal) => {
          console.log('Tool proposal received:', proposal);
          // Create tool call object from proposal data
          const toolCall = {
            id: proposal.tool_call_id,
            name: proposal.name,
            arguments: proposal.arguments,
            status: 'pending'
          };
          flushSync(() => {
            addPendingToolCall(toolCall as any);
          });
        },
        // onToolResult
        (result) => {
          console.log('Tool result received:', result);
          console.log('Result structure check:', {
            status: result.status,
            hasResult: !!result.result,
            resultOk: result.result?.ok,
            hasCapTable: !!result.result?.capTable,
            hasMetrics: !!result.result?.metrics,
            resultKeys: result.result ? Object.keys(result.result) : []
          });
          
          flushSync(() => {
            // Always try to update cap table if we have the data
            if (result.result && result.result.capTable && result.result.metrics) {
              console.log('Updating cap table with result data');
              setCapTable(result.result.capTable);
              setMetrics(result.result.metrics);
              if (result.result.diff) {
                setLastDiff(result.result.diff);
              }
            }
            
            // Remove from pending after execution
            if (result.tool_call_id) {
              removePendingToolCall(result.tool_call_id);
            }
          });
        },
    // onStatusMessage
    (statusMessage) => {
      // Handle thinking status
      if (statusMessage.event === 'thinking_start') {
        flushSync(() => {
          setThinkingStatus({ isThinking: true, startTime: Date.now() });
        });
      } else if (statusMessage.event === 'thinking_end') {
        flushSync(() => {
          setThinkingStatus(null);
        });
      }
      
      // When tool calls start, save current content segment as a message
      if (statusMessage.event === 'tool_calls_start') {
        flushSync(() => {
          // Save the current streaming content as a complete message
          if (currentSegment.trim()) {
            addMessage({ role: 'assistant', content: currentSegment, timestamp: Date.now() });
          }
          // Clear current segment for post-tool content
          currentSegment = '';
          setStreamingContent('');
        });
      }
      
      // When tools complete, clear status messages so they don't show up in next segment
      if (statusMessage.event === 'tools_complete') {
        flushSync(() => {
          setStatusMessages([]);
        });
      }
      
      // Add status message to the list (filter out thinking_start as we show it separately)
      if (statusMessage.event !== 'thinking_start') {
        flushSync(() => {
          setStatusMessages(prev => [...prev, statusMessage]);
        });
      }
    }
  );
    } catch (error) {
      // If we have partial response, save it
      if (currentSegment.trim()) {
        addMessage({ role: 'assistant', content: currentSegment, timestamp: Date.now() });
      }
      
      addMessage({
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: Date.now()
      });
      setStreamingContent('');
      streamingRef.current = '';
      setIsStreaming(false);
    }
  }, [messages, addMessage, setIsStreaming, setCapTable, setMetrics, executionMode, addPendingToolCall, removePendingToolCall]);
  
  const handleApproveTool = useCallback(async (toolCall: any) => {
    try {
      const result = await approveToolCalls([toolCall.id]);
      removePendingToolCall(toolCall.id);
      
      // Update cap table if successful
      if (result.results && result.results[0] && result.results[0].result) {
        const toolResult = result.results[0].result;
        if (toolResult.ok && toolResult.capTable && toolResult.metrics) {
          setCapTable(toolResult.capTable);
          setMetrics(toolResult.metrics);
          setLastDiff(toolResult.diff || []);
        }
      }
    } catch (error) {
      console.error('Failed to approve tool:', error);
    }
  }, [removePendingToolCall, setCapTable, setMetrics, setLastDiff]);
  
  const handleRejectTool = useCallback((toolCall: any) => {
    removePendingToolCall(toolCall.id);
  }, [removePendingToolCall]);
  
  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex-shrink-0 p-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
        <p className="text-sm text-gray-500">Describe your cap table or ask for changes</p>
      </div>
      
      {/* Show pending tool calls */}
      {pendingToolCalls.length > 0 && (
        <div className="flex-shrink-0 p-4 border-b bg-yellow-50">
          {pendingToolCalls.map((toolCall) => (
            <ToolCallApproval
              key={toolCall.id}
              toolCall={toolCall as any}
              preview={undefined}
              validationErrors={[]}
              onApprove={() => handleApproveTool(toolCall)}
              onReject={() => handleRejectTool(toolCall)}
            />
          ))}
        </div>
      )}
      
      <MessageList 
        messages={messages} 
        streamingContent={streamingContent}
        statusMessages={statusMessages}
        thinkingStatus={thinkingStatus}
      />
      
      <div className="flex-shrink-0 p-4 border-t">
        <MessageInput onSend={handleSendMessage} disabled={isStreaming} />
      </div>
    </div>
  );
}

