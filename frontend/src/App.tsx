/**
 * App.tsx — Final 3-Panel Distributed Multi-Agent AI System UI.
 * Integrates Chat, Real-Time Agent Tracing, and System Metrics.
 */

import React, { useCallback } from 'react';

// ── Components ──────────────────────────────────────────────────────────────
import ChatArea from './components/ChatArea';
import DocumentSidebar from './components/DocumentSidebar';
import AgentTracePanel from './components/AgentTracePanel';

// ── Hooks ───────────────────────────────────────────────────────────────────
import { useAgentStream } from './hooks/useAgentStream';
import { useDocuments } from './hooks/useDocuments';
import { useMetrics } from './hooks/useMetrics';

const App: React.FC = () => {
  const [selectedDoc, setSelectedDoc] = React.useState<string | null>(null);

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
    deleteDocument 
  } = useDocuments();
  
  const { 
    metrics, 
    submitFeedback 
  } = useMetrics();

  // Handlers
  const handleAsk = useCallback((question: string) => {
    // Pass the selected document as the source filter
    askQuestion(question, 'default', selectedDoc || undefined);
  }, [askQuestion, selectedDoc]);

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

  return (
    <div className="layout-container bg-[#080c14] overflow-hidden">
      {/* ── Left Panel: Sidebar & Metrics ────────────────────────────────────── */}
      <DocumentSidebar 
        documents={documents}
        metrics={metrics}
        onUpload={handleUpload}
        onDelete={deleteDocument}
        isUploading={isUploading}
        selectedDoc={selectedDoc}
        onSelectDoc={setSelectedDoc}
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
    </div>
  );
};

export default App;