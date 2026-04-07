import React from 'react';
import type { AgentTraceStep } from '../types';

interface AgentTracePanelProps {
  trace: AgentTraceStep[];
  isStreaming: boolean;
}

const AgentTracePanel: React.FC<AgentTracePanelProps> = ({ trace, isStreaming }) => {
  return (
    <aside className="trace-panel border-l border-[var(--border)] bg-[var(--bg-glass)] backdrop-blur-xl flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-[var(--border)] flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-dim)]">
          Live Agent Trace
        </h2>
        {isStreaming && (
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-secondary)] animate-pulse"></span>
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-secondary)] animate-pulse delay-75"></span>
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-secondary)] animate-pulse delay-150"></span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {trace.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
            <div className="w-12 h-12 rounded-full border-2 border-dashed border-[var(--border)] mb-4"></div>
            <p className="text-sm">Wait for a question to see agent reasoning...</p>
          </div>
        ) : (
          trace.map((step, idx) => (
            <div 
              key={idx} 
              className={`p-3 rounded-lg border border-[var(--border)] bg-[var(--bg-glass-heavy)] animate-in slide-in-from-right duration-300`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    step.status === 'done' ? 'bg-[var(--accent-green)]' : 
                    step.status === 'retrying' ? 'bg-[var(--accent-amber)]' : 
                    'bg-[var(--accent-secondary)]'
                  }`}></span>
                  <span className="font-bold text-xs uppercase text-[var(--text-primary)]">
                    {step.step_type || step.agent}
                  </span>
                </div>
                <span className="text-[10px] text-[var(--text-dim)] font-mono">
                  {step.duration_ms}ms
                </span>
              </div>
              <p className="text-sm text-[var(--text-muted)] italic">
                "{step.action}"
              </p>
              {step.details && (
                <div className="mt-2 text-[10px] text-[var(--text-dim)] font-mono bg-black/20 p-1.5 rounded border border-white/5 whitespace-pre-wrap">
                  {step.details}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t border-[var(--border)] bg-black/20 text-[10px] text-[var(--text-dim)] font-mono">
        Total reasoning time: {trace.reduce((acc, step) => acc + step.duration_ms, 0)}ms
      </div>
    </aside>
  );
};

export default AgentTracePanel;
