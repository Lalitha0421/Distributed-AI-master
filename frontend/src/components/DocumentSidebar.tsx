import React from 'react';
import type { MetricsData, DocumentInfo, ImprovementsData } from '../types';

interface DocumentSidebarProps {
  documents: DocumentInfo[];
  metrics: MetricsData | null;
  improvements: ImprovementsData | null;
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDelete: (filename: string) => void;
  onSync: () => void;
  isUploading: boolean;
  selectedDoc: string | null;
  onSelectDoc: (filename: string | null) => void;
  onOpenDashboard: () => void;
}

const DocumentSidebar: React.FC<DocumentSidebarProps> = ({ 
  documents, 
  metrics, 
  improvements,
  onUpload, 
  onDelete,
  onSync,
  isUploading,
  selectedDoc,
  onSelectDoc,
  onOpenDashboard
}) => {
  return (
    <nav className="sidebar-panel border-r border-[var(--border)] bg-[var(--bg-glass)] backdrop-blur-xl flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-[var(--border)]">
        <h1 className="text-xl font-bold bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)] bg-clip-text text-transparent">
          AI Knowledge Base
        </h1>
        <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-widest mt-1">
          Distributed Multi-Agent RAG
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin">
        {/* Documents Section */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                Documents
              </h3>
              <button 
                onClick={onSync}
                className="p-1 rounded hover:bg-white/10 text-[var(--text-dim)] hover:text-[var(--accent-secondary)] transition-all"
                title="Sync with filesystem"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
              </button>
            </div>
            <label className="cursor-pointer group">
              <input type="file" className="hidden" onChange={onUpload} accept=".pdf,.docx,.txt,.md" multiple />
              <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[var(--bg-glass-heavy)] border border-[var(--border)] group-hover:bg-[var(--accent-primary)] group-hover:text-white transition-all text-xs">
                {isUploading ? <span className="animate-spin w-3 h-3 border-2 border-current border-t-transparent rounded-full" /> : <span>+</span>}
                Upload
              </div>
            </label>
          </div>

          <div className="space-y-2">
            {documents.length === 0 ? (
              <div className="p-3 rounded-lg border border-dashed border-[var(--border)] text-center text-xs text-[var(--text-dim)]">
                No documents uploaded yet.
              </div>
            ) : (
              <>
                {/* All Docs Option */}
                <div 
                  onClick={() => onSelectDoc(null)}
                  className={`group p-2.5 rounded-lg border transition-all cursor-pointer ${
                    selectedDoc === null 
                    ? 'bg-[var(--accent-primary)] border-[var(--accent-primary)] shadow-lg glow-indigo' 
                    : 'bg-[var(--bg-glass-heavy)] border-[var(--border)] hover:border-[var(--text-muted)]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-black/40 flex items-center justify-center text-white text-xs font-bold">ALL</div>
                    <div className="text-sm font-medium">All Knowledge Base</div>
                  </div>
                </div>

                {documents.map((doc, idx) => (
                  <div 
                    key={idx} 
                    onClick={() => onSelectDoc(doc.filename)}
                    className={`group relative p-2.5 rounded-lg border transition-all cursor-pointer ${
                      selectedDoc === doc.filename 
                      ? 'bg-[var(--accent-primary)] border-[var(--accent-primary)] shadow-lg glow-indigo scale-[1.01]' 
                      : 'bg-[var(--bg-glass-heavy)] border-[var(--border)] hover:border-[var(--accent-secondary)]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-black/40 flex items-center justify-center text-[var(--accent-secondary)] text-sm font-bold border border-white/5">
                        {doc.filename.split('.').pop()?.toUpperCase() || '??'}
                      </div>
                      <div className="flex-1 min-w-0 pr-6">
                        <div className={`text-[13px] font-medium truncate ${selectedDoc === doc.filename ? 'text-white' : 'text-[var(--text-primary)]'}`}>
                          {doc.filename}
                        </div>
                        <div className={`text-[10px] flex items-center gap-2 mt-0.5 ${selectedDoc === doc.filename ? 'text-white/70' : 'text-[var(--text-dim)]'}`}>
                          <span>{doc.chunks} pieces</span>
                          <span>•</span>
                          <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    {/* Delete Toggle */}
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Delete ${doc.filename}?`)) {
                          onDelete(doc.filename);
                        }
                      }}
                      className="absolute top-2.5 right-2 opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-red-500/20 hover:text-red-400 transition-all text-[var(--text-muted)]"
                      title="Delete document"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                    </button>
                  </div>
                ))}
              </>
            )}
          </div>
        </section>

        {/* Metrics Section */}
        {metrics && (
          <section className="space-y-3 pt-6 border-t border-[var(--border)]">
            <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              System Health
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-black/30 border border-white/5">
                <div className="text-[10px] text-[var(--text-dim)]">Faithfulness</div>
                <div className="text-lg font-bold text-[var(--accent-green)]">
                  {Math.round(metrics.avg_faithfulness * 100)}%
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-black/30 border border-white/5">
                <div className="text-[10px] text-[var(--text-dim)]">Relevance</div>
                <div className="text-lg font-bold text-[var(--accent-secondary)]">
                  {Math.round(metrics.avg_relevance * 100)}%
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-black/30 border border-white/5">
                <div className="text-[10px] text-[var(--text-dim)]">Avg. Rating</div>
                <div className="text-lg font-bold text-[var(--accent-amber)]">
                  {metrics.avg_user_rating} <span className="text-xs font-normal">/ 5</span>
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-black/30 border border-white/5">
                <div className="text-[10px] text-[var(--text-dim)]">Retries</div>
                <div className="text-lg font-bold text-white">
                  {metrics.avg_retry_count}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Improvements Section — New Phase 5 Feature */}
        {improvements && improvements.insights.length > 0 && (
          <section className="space-y-4 pt-6 border-t border-[var(--border)]">
            <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider">
              Self-Improvement Insights
            </h3>
            <div className="space-y-3">
              {improvements.insights.map((insight, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-[var(--bg-glass-heavy)] border border-[var(--border)] group/insight hover:border-[var(--accent-primary)] transition-all">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold uppercase text-[var(--text-dim)]">{insight.metric.replace('_', ' ')}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase transition-all ${
                      insight.trend === 'improving' ? 'bg-green-500/20 text-green-400' :
                      insight.trend === 'declining' ? 'bg-red-500/20 text-red-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {insight.trend}
                    </span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-[var(--text-primary)]">
                    {insight.suggestion}
                  </p>
                  {insight.auto_applied && (
                    <div className="mt-2 flex items-center gap-1.5 text-[9px] text-[var(--accent-green)] font-medium">
                      <div className="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></div>
                      Auto-applied fix
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      <div className="p-4 border-t border-[var(--border)] bg-black/40">
        <button 
          onClick={onOpenDashboard}
          className="w-full mb-6 p-3 rounded-xl bg-gradient-to-r from-[var(--accent-primary)]/20 to-[var(--accent-secondary)]/20 border border-[var(--accent-primary)]/30 hover:border-[var(--accent-primary)] transition-all flex items-center justify-between group/btn"
        >
          <div className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--accent-primary)]"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            <span className="text-sm font-bold text-white">Full Analytics</span>
          </div>
          <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-[var(--accent-primary)] font-bold group-hover/btn:scale-110 transition-transform">GO →</span>
        </button>

        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] group">
          <div className="w-2 h-2 rounded-full bg-[var(--accent-green)] shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
          Status: <span className="text-[var(--text-primary)]">System Healthy</span>
        </div>
      </div>
    </nav>
  );
};

export default DocumentSidebar;
