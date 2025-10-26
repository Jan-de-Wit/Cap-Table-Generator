/**
 * MessageList Component
 * Displays conversation history with user and assistant messages
 */

import { useEffect, useRef } from 'react';
import { Bot, User, Brain, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage } from '../../types/captable.types';
import { StatusMessage, type StatusMessageData } from './StatusMessage';

interface MessageListProps {
  messages: ChatMessage[];
  streamingContent?: string;
  statusMessages?: StatusMessageData[];
  thinkingStatus?: { isThinking: boolean; startTime: number } | null;
}

export function MessageList({ messages, streamingContent, statusMessages = [], thinkingStatus }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, statusMessages, thinkingStatus]);
  
  // Helper to check if streaming has started
  const hasStartedStreaming = () => {
    return streamingContent && streamingContent.length > 0;
  };
  
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && !streamingContent && !thinkingStatus && (
        <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
          <Bot className="w-16 h-16 mb-4 text-gray-300" />
          <p className="text-lg font-medium">Start a Conversation</p>
          <p className="text-sm mt-2 max-w-md">
            Ask me to create a cap table, add holders, rounds, or modify existing data.
            I'll use the cap_table_editor tool to make precise changes.
          </p>
        </div>
      )}
      
      {messages.map((msg, index) => (
        <div
          key={index}
          className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
        >
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-600'
          }`}>
            {msg.role === 'user' ? (
              <User className="w-5 h-5 text-white" />
            ) : (
              <Bot className="w-5 h-5 text-white" />
            )}
          </div>
          
          <div className={`flex-1 max-w-[80%] ${
            msg.role === 'user' ? 'text-right' : 'text-left'
          }`}>
            <div className={`inline-block px-4 py-2 rounded-lg ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}>
              <ReactMarkdown 
                className={`prose prose-sm max-w-none ${
                  msg.role === 'user'
                    ? 'prose-headings:text-white prose-p:text-white prose-strong:text-white prose-code:bg-white/20 prose-code:text-white'
                    : 'prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-code:text-blue-600 prose-code:bg-gray-200 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-pre:bg-gray-800 prose-pre:text-gray-100'
                }`}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      ))}
      
      {/* Show thinking indicator - only while actively thinking */}
      {thinkingStatus && !hasStartedStreaming() && (
        <div className="flex gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-blue-600">
            <Brain className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div className="flex-1 bg-gray-100 px-4 py-3 rounded-lg text-gray-700">
            <div className="flex items-center gap-2">
              <span>Analyzing your request</span>
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
          </div>
        </div>
      )}
      
      {/* Show streaming response with status messages combined */}
      {(streamingContent || statusMessages.length > 0) && (
        <div className="flex gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-600">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 max-w-[80%]">
            {/* Show status messages first */}
            {statusMessages.length > 0 && (
              <div className="space-y-2 mb-3">
                {statusMessages.map((msg, idx) => (
                  <StatusMessage key={idx} message={msg} />
                ))}
              </div>
            )}
            
            {/* Show streaming content */}
            {streamingContent && (
              <div className="inline-block px-4 py-2 rounded-lg bg-gray-100 text-gray-900">
                <ReactMarkdown 
                  className="prose prose-sm max-w-none
                    prose-headings:text-gray-900 
                    prose-p:text-gray-700 
                    prose-strong:text-gray-900 
                    prose-strong:font-semibold
                    prose-code:text-blue-600
                    prose-code:bg-gray-200
                    prose-code:px-1
                    prose-code:py-0.5
                    prose-code:rounded
                    prose-code:text-sm
                    prose-pre:bg-gray-800
                    prose-pre:text-gray-100
                    prose-pre:border
                    prose-pre:border-gray-700
                    prose-blockquote:border-l-4
                    prose-blockquote:border-gray-300
                    prose-blockquote:italic
                    prose-ul:text-gray-700
                    prose-ol:text-gray-700
                    prose-li:text-gray-700"
                >
                  {streamingContent}
                </ReactMarkdown>
                <span className="inline-block w-1 h-4 ml-1 bg-gray-600 animate-pulse" />
              </div>
            )}
          </div>
        </div>
      )}
      
      <div ref={bottomRef} />
    </div>
  );
}

