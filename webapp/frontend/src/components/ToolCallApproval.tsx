/**
 * ToolCallApproval Component
 * Shows pending tool calls with preview and approval/rejection options
 */

import { Check, X } from 'lucide-react';
import type { ToolCall } from '../types/captable.types';

interface ToolCallApprovalProps {
  toolCall: ToolCall;
  preview?: any;
  validationErrors: string[];
  onApprove: () => void;
  onReject: () => void;
}

export function ToolCallApproval({
  toolCall,
  preview,
  validationErrors,
  onApprove,
  onReject
}: ToolCallApprovalProps) {
  const operation = toolCall.arguments.operation || 'unknown';
  const path = toolCall.arguments.path || 'N/A';
  
  // Extract description from preview
  const diff = preview?.diff || [];
  const hasValidationErrors = validationErrors.length > 0;
  
  return (
    <div className="border border-blue-200 bg-blue-50 rounded-lg p-4 my-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold text-blue-900">
            Tool Call: {toolCall.name}
          </h4>
          <p className="text-sm text-blue-700 mt-1">
            Operation: <code className="bg-blue-100 px-1 rounded">{operation}</code>
          </p>
          <p className="text-sm text-blue-700">
            Path: <code className="bg-blue-100 px-1 rounded">{path}</code>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onApprove}
            className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
            disabled={hasValidationErrors}
          >
            <Check className="w-4 h-4" />
            Approve
          </button>
          <button
            onClick={onReject}
            className="flex items-center gap-2 px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
          >
            <X className="w-4 h-4" />
            Reject
          </button>
        </div>
      </div>
      
      {hasValidationErrors && (
        <div className="mt-3 p-3 bg-red-100 border border-red-300 rounded">
          <p className="font-semibold text-red-800 text-sm mb-2">Validation Errors:</p>
          <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
            {validationErrors.map((error, idx) => (
              <li key={idx}>{error}</li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-red-600">
            This tool call cannot be approved due to validation errors.
          </p>
        </div>
      )}
      
      {diff.length > 0 && !hasValidationErrors && (
        <div className="mt-3 p-3 bg-white border border-blue-200 rounded">
          <p className="font-semibold text-blue-900 text-sm mb-2">Proposed Changes:</p>
          <ul className="space-y-1">
            {diff.map((item: any, idx: number) => (
              <li key={idx} className="text-sm text-gray-700">
                {item.description || `${item.op} at ${item.path}`}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {preview && preview.ok && (
        <div className="mt-3 p-2 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600">
          Preview generated successfully
        </div>
      )}
    </div>
  );
}

