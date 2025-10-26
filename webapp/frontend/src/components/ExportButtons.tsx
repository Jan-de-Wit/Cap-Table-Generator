/**
 * ExportButtons Component
 * Provides buttons for JSON/Excel export and showing diff
 */

import { Download, FileJson, FileSpreadsheet, GitCompare } from 'lucide-react';
import { downloadCapTableJSON, downloadCapTableExcel } from '../services/api';

interface ExportButtonsProps {
  onShowDiff: () => void;
}

export function ExportButtons({ onShowDiff }: ExportButtonsProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={downloadCapTableJSON}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        title="Export as JSON"
      >
        <FileJson className="w-4 h-4" />
        JSON
      </button>
      
      <button
        onClick={downloadCapTableExcel}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        title="Export as Excel"
      >
        <FileSpreadsheet className="w-4 h-4" />
        Excel
      </button>
      
      <button
        onClick={onShowDiff}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-300 rounded-lg hover:bg-purple-100 transition-colors"
        title="Show last changes"
      >
        <GitCompare className="w-4 h-4" />
        Show Diff
      </button>
    </div>
  );
}

