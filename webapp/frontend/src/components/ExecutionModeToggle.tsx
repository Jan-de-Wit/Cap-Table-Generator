/**
 * ExecutionModeToggle Component
 * Toggle between auto and approval execution modes
 */

import { Settings } from 'lucide-react';
import type { ExecutionMode } from '../types/captable.types';

interface ExecutionModeToggleProps {
  mode: ExecutionMode;
  onChange: (mode: ExecutionMode) => void;
}

export function ExecutionModeToggle({ mode, onChange }: ExecutionModeToggleProps) {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex items-center gap-2 text-sm text-gray-700">
        <Settings className="w-4 h-4" />
        <span className="font-medium">Execution Mode:</span>
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={() => onChange('auto')}
          className={`px-4 py-2 rounded transition-colors text-sm font-medium ${
            mode === 'auto'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          Auto
        </button>
        
        <button
          onClick={() => onChange('approval')}
          className={`px-4 py-2 rounded transition-colors text-sm font-medium ${
            mode === 'approval'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          Approval
        </button>
      </div>
      
      <p className="text-xs text-gray-500 ml-2">
        {mode === 'auto'
          ? 'Tools execute automatically'
          : 'Tools require approval before execution'}
      </p>
    </div>
  );
}

