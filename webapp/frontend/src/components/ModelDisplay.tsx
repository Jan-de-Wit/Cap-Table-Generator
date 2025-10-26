/**
 * ModelDisplay Component
 * Shows the active LLM model (read-only, server-configured)
 */

import { Bot } from 'lucide-react';

interface ModelDisplayProps {
  provider: string;
  model: string;
}

export function ModelDisplay({ provider, model }: ModelDisplayProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
      <Bot className="w-5 h-5 text-blue-600" />
      <span className="text-sm font-medium text-blue-900">
        Active Model: {provider}/{model}
      </span>
      <span className="text-xs text-blue-600 ml-2">(read-only)</span>
    </div>
  );
}

