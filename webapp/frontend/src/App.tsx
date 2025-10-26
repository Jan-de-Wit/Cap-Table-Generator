/**
 * Main App Component
 * Two-column layout with cap table preview and chat
 */

import { useEffect, useState } from 'react';
import { ModelDisplay } from './components/ModelDisplay';
import { ExportButtons } from './components/ExportButtons';
import { DiffViewer } from './components/DiffViewer';
import { ChatPane } from './components/Chat/ChatPane';
import { CapTablePreview } from './components/CapTable/CapTablePreview';
import { useAppStore } from './store/appStore';
import { getConfig, getCapTable } from './services/api';

function App() {
  const { 
    provider, 
    model, 
    lastDiff,
    setModelConfig, 
    setCapTable, 
    setMetrics 
  } = useAppStore();
  
  const [isDiffViewerOpen, setIsDiffViewerOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Load initial config and cap table state
    Promise.all([
      getConfig(),
      getCapTable()
    ])
      .then(([config, capTableData]) => {
        setModelConfig(config.provider, config.model);
        setCapTable(capTableData.capTable);
        setMetrics(capTableData.metrics);
      })
      .catch((error) => {
        console.error('Error loading initial data:', error);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [setModelConfig, setCapTable, setMetrics]);
  
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Top Bar */}
      <header className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-gray-900">
              Cap Table Generator
            </h1>
            <ModelDisplay provider={provider} model={model} />
          </div>
          <ExportButtons onShowDiff={() => setIsDiffViewerOpen(true)} />
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Cap Table Preview - Left (60%) */}
        <div className="w-[60%] border-r border-gray-200 bg-white">
          <CapTablePreview />
        </div>
        
        {/* Chat Pane - Right (40%) */}
        <div className="w-[40%] bg-white">
          <ChatPane />
        </div>
      </main>
      
      {/* Diff Viewer Modal */}
      <DiffViewer
        diff={lastDiff}
        isOpen={isDiffViewerOpen}
        onClose={() => setIsDiffViewerOpen(false)}
      />
    </div>
  );
}

export default App;
