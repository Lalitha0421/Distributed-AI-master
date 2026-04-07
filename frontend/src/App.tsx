/**
 * App.tsx — Final 3-Panel Distributed Multi-Agent AI System UI.
 * Integrates Chat, Real-Time Agent Tracing, and System Metrics.
 */

import React, { useCallback } from 'react';

// ── Components ──────────────────────────────────────────────────────────────
import ChatArea from './components/ChatArea';
import DocumentSidebar from './components/DocumentSidebar';
import AgentTracePanel from './components/AgentTracePanel';
import MetricsDashboard from './components/MetricsDashboard';
import Login from './components/Login';
import { AnimatePresence } from 'framer-motion';

// ── Hooks ───────────────────────────────────────────────────────────────────
import { useAgentStream } from './hooks/useAgentStream';
import { useDocuments } from './hooks/useDocuments';
import { useMetrics } from './hooks/useMetrics';

const App: React.FC = () => {
  const [selectedDoc, setSelectedDoc] = React.useState<string | null>(null);
  const [isDashboardOpen, setIsDashboardOpen] = React.useState(false);
  const [isAuthenticated, setIsAuthenticated] = React.useState(!!localStorage.getItem('access_token'));

  const handleLoginSuccess = (token: string) => {
    localStorage.setItem('access_token', token);
    setIsAuthenticated(true);
    // Reload metrics when user logs in
    refreshMetrics();
  };

  // Logic hooks
  const { 
    messages, 
    isStreaming, 
    currentTrace, 
    askQuestion, 
    stopStreaming 
  } = useAgentStream();
  
  const { 
    documents, 
    isUploading, 
    uploadDocuments,
    deleteDocument,
    syncDocuments 
  } = useDocuments();
  
  const { 
    metrics, 
    improvements,
    submitFeedback,
    refresh: refreshMetrics
  } = useMetrics();

  // Handlers
  const handleAsk = useCallback((question: string) => {
    // Pass the selected document as the source filter
    askQuestion(question, 'default', selectedDoc || undefined, () => {
      // Small delay to allow background eval on server to start/finish
      setTimeout(refreshMetrics, 3000);
    });
  }, [askQuestion, selectedDoc, refreshMetrics]);

  const handleUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      uploadDocuments(files);
    }
  }, [uploadDocuments]);

  const handleFeedback = useCallback((msgId: string, rating: number) => {
    // Find message to get content for evaluation context
    const msg = messages.find(m => m.id === msgId);
    if (!msg) return;

    // Find the user prompt preceding this AI answer
    const userMsgIdx = messages.findIndex(m => m.id === msgId) - 1;
    const userMsg = userMsgIdx >= 0 ? messages[userMsgIdx] : null;

    submitFeedback(
      msgId, 
      userMsg?.content || "Unknown prompt", 
      msg.content, 
      rating
    );
  }, [messages, submitFeedback]);

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="layout-container bg-[#080c14] overflow-hidden">
      {/* ── Left Panel: Sidebar & Metrics ────────────────────────────────────── */}
      <DocumentSidebar 
        documents={documents}
        metrics={metrics}
        improvements={improvements}
        onUpload={handleUpload}
        onDelete={deleteDocument}
        onSync={syncDocuments}
        isUploading={isUploading}
        selectedDoc={selectedDoc}
        onSelectDoc={setSelectedDoc}
        onOpenDashboard={() => setIsDashboardOpen(true)}
      />

      {/* ── Center Panel: Conversational AI Window ────────────────────────────── */}
      <ChatArea 
        messages={messages}
        isStreaming={isStreaming}
        onAsk={handleAsk}
        onStop={stopStreaming}
        onFeedback={handleFeedback}
      />

      {/* ── Right Panel: Real-Time Agent Diagnostics ─────────────────────────── */}
      <AgentTracePanel 
        trace={currentTrace}
        isStreaming={isStreaming}
      />

      <AnimatePresence>
        {isDashboardOpen && (
          <MetricsDashboard 
            metrics={metrics} 
            improvements={improvements}
            onClose={() => setIsDashboardOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default App;