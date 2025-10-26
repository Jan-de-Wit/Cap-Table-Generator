/**
 * StatusMessage Component
 * Displays system status messages during AI processing
 * Matches the style from the reference image with inline code highlighting
 */

import { Brain, Wrench, CheckCircle, Loader, FileText } from 'lucide-react';

export interface StatusMessageData {
  event: string;
  data: any;
}

interface StatusMessageProps {
  message: StatusMessageData;
}

export function StatusMessage({ message }: StatusMessageProps) {
  const getStatusContent = () => {
    switch (message.event) {
      case 'thinking_end':
        const seconds = Math.round(message.data.duration_seconds || 0);
        return {
          icon: CheckCircle,
          title: `Thought for ${seconds}s`,
          description: null,
          className: 'text-gray-600',
          bgColor: 'bg-gray-50'
        };
      case 'tool_execution_start':
        try {
          const operation = JSON.parse(message.data.operation || '{}');
          const opType = operation.operation || 'unknown';
          const path = operation.path || '';
          
          // Parse path to create user-friendly description
          let action = '';
          if (opType === 'append') {
            if (path.includes('/holders')) {
              action = 'Adding holder to cap table';
            } else if (path.includes('/classes')) {
              action = 'Adding security class';
            } else if (path.includes('/instruments')) {
              action = 'Adding instrument';
            } else if (path.includes('/rounds')) {
              action = 'Adding financing round';
            } else if (path.includes('/terms')) {
              action = 'Adding terms package';
            } else {
              action = `Appending to ${path}`;
            }
          } else if (opType === 'replace') {
            action = `Updating ${path}`;
          } else if (opType === 'delete') {
            action = `Removing ${path}`;
          } else {
            action = `${opType} ${path}`;
          }
          
          return {
            icon: FileText,
            title: action,
            description: path ? `Path: ${path}` : null,
            className: 'text-blue-600',
            bgColor: 'bg-blue-50'
          };
        } catch (e) {
          return {
            icon: Loader,
            title: 'Processing cap table change...',
            description: null,
            className: 'text-orange-600',
            bgColor: 'bg-orange-50'
          };
        }
      case 'tool_execution_complete':
        return {
          icon: CheckCircle,
          title: message.data.status === 'success' ? 'Cap table change applied successfully' : 'Cap table change failed',
          description: null,
          className: message.data.status === 'success' ? 'text-green-600' : 'text-red-600',
          bgColor: message.data.status === 'success' ? 'bg-green-50' : 'bg-red-50'
        };
      case 'tools_complete':
        return {
          icon: CheckCircle,
          title: `Completed ${message.data.count} operation${message.data.count > 1 ? 's' : ''}`,
          description: 'All changes have been applied to the cap table',
          className: 'text-blue-600',
          bgColor: 'bg-blue-50'
        };
      default:
        return null;
    }
  };

  const status = getStatusContent();
  
  if (!status) return null;

  const Icon = status.icon;

  return (
    <div className={`px-3 py-2 rounded-lg ${status.bgColor} mb-2`}>
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${status.className} ${status.icon === Loader ? 'animate-spin' : ''}`} />
        <span className={`text-sm font-medium ${status.className}`}>
          {status.title}
        </span>
      </div>
      {status.description && (
        <div className="mt-1 ml-6">
          <span className="text-xs text-gray-600 font-mono bg-white px-2 py-1 rounded">
            {status.description}
          </span>
        </div>
      )}
    </div>
  );
}

