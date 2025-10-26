/**
 * DiffViewer Component
 * Displays human-readable diff of last changes
 */

import { X } from 'lucide-react';
import type { DiffItem } from '../types/captable.types';

interface DiffViewerProps {
  diff: DiffItem[];
  isOpen: boolean;
  onClose: () => void;
}

export function DiffViewer({ diff, isOpen, onClose }: DiffViewerProps) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            Last Changes
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {diff.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No changes yet. Start by chatting with the assistant!
            </div>
          ) : (
            <ul className="space-y-2">
              {diff.map((item, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <span className={`flex-shrink-0 mt-0.5 w-2 h-2 rounded-full ${
                    item.op === 'add' ? 'bg-green-500' :
                    item.op === 'remove' ? 'bg-red-500' :
                    'bg-blue-500'
                  }`} />
                  <div className="flex-1">
                    {item.description ? (
                      <p className="text-sm text-gray-900">{item.description}</p>
                    ) : (
                      <div className="text-sm text-gray-900">
                        <span className="font-medium">{item.op}</span>{' '}
                        <span className="text-gray-600">{item.path}</span>
                        {item.from !== undefined && item.to !== undefined && (
                          <div className="mt-1 text-xs">
                            <span className="text-red-600">- {JSON.stringify(item.from)}</span>
                            <br />
                            <span className="text-green-600">+ {JSON.stringify(item.to)}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

