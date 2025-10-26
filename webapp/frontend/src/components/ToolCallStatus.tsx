/**
 * ToolCallStatus Component
 * Shows status indicators for tool calls
 */

import { Loader, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

interface ToolCallStatusProps {
  status: 'pending' | 'approved' | 'executing' | 'success' | 'rejected' | 'failed';
  message?: string;
}

export function ToolCallStatus({ status, message }: ToolCallStatusProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return {
          icon: Clock,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          label: 'Pending Approval'
        };
      case 'approved':
        return {
          icon: CheckCircle,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          label: 'Approved'
        };
      case 'executing':
        return {
          icon: Loader,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200',
          label: 'Executing'
        };
      case 'success':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          label: 'Success'
        };
      case 'rejected':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          label: 'Rejected'
        };
      case 'failed':
        return {
          icon: AlertCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          label: 'Failed'
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          label: 'Unknown'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
      <Icon className={`w-4 h-4 ${config.color} ${status === 'executing' ? 'animate-spin' : ''}`} />
      <span className={`text-sm font-medium ${config.color}`}>
        {config.label}
      </span>
      {message && (
        <span className="text-xs text-gray-600 ml-2">{message}</span>
      )}
    </div>
  );
}

