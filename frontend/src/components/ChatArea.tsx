import React, { useState, useRef, useEffect } from 'react';
import type { Message } from '../types';

interface ChatAreaProps {
  messages: Message[];
  isStreaming: boolean;
  onAsk: (question: string) => void;
  onStop: () => void;
  onFeedback: (msgId: string, rating: number) => void;
}

const StarRating: React.FC<{ onRate: (r: number) => void }> = ({ onRate }) => {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex gap-1 bg-[var(--bg-glass-heavy)] p-1.5 rounded-lg border border-[var(--border)] overflow-hidden">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          onClick={() => onRate(star)}
          className={`transition-all ${star <= hover ? 'text-[var(--accent-amber)] scale-110' : 'text-[var(--text-dim)] hover:text-[var(--text-muted)]'}`}
        >
          <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
            <path d="M10 1l2.5 6h6.5l-5 4.5 2 6.5-6-4.5-6 4.5 2-6.5-5-4.5h6.5z" />
          </svg>
        </button>
      ))}
    </div>
  );
};

const ChatArea: React.FC<ChatAreaProps> = ({ messages, isStreaming, onAsk, onStop, onFeedback }) => {
  const [input, setInput] = useState('');
  const lastMsgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    lastMsgRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isStreaming) {
      onAsk(input);
      setInput('');
    }
  };

  return (
    <main className="main-chat-area flex flex-col h-full bg-[var(--bg-base)]">
      {/* Messages Window */}
      <div className="flex-1 overflow-y-auto p-6 md:p-12 space-y-8">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-40 max-w-lg mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] flex items-center justify-center mb-6 shadow-xl" style={{ width: '64px', height: '64px' }}>
              <svg className="w-8 h-8 text-white" width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
            </div>
            <h1 className="text-2xl font-bold mb-4">How can I help you?</h1>
            <p className="text-sm leading-relaxed">
              Upload documents like PDFs or research papers. I'll use multi-agent retrieval to answer your questions with high accuracy and source citations.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={msg.id} className="max-w-3xl mx-auto" ref={idx === messages.length - 1 ? lastMsgRef : null}>
              {/* User Message */}
              {msg.role === 'user' ? (
                <div className="flex flex-col items-end mb-4">
                  <div className="p-4 rounded-2xl bg-[var(--accent-primary)] text-white shadow-lg text-sm max-w-[80%]">
                    {msg.content}
                  </div>
                </div>
              ) : (
                /* Assistant Message */
                <div className="space-y-4">
                  <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-5 shadow-lg group relative">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] flex items-center justify-center">
                        <span className="text-[10px] text-white">AI</span>
                      </div>
                      <span className="text-xs font-bold uppercase tracking-wider text-[var(--accent-secondary)]">Search Result</span>
                    </div>

                    <div className="prose prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
                      {msg.content || (msg.isStreaming && <div className="w-1.5 h-4 bg-[var(--accent-secondary)] animate-pulse inline-block" />)}
                    </div>

                    {/* Sources Expansion */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-[var(--border)] space-y-2">
                        <p className="text-[10px] font-bold text-[var(--text-dim)] uppercase tracking-wider">Cited Sources</p>
                        <div className="flex flex-wrap gap-2">
                          {msg.sources.map((s, i) => (
                            <div key={i} className="px-2 py-1 rounded bg-[var(--bg-glass-heavy)] border border-[var(--border)] text-[10px] text-[var(--text-muted)] cursor-pointer hover:border-[var(--accent-secondary)] transition-all">
                              {s.source} <span className="opacity-50">#{s.chunk_id}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {!msg.isStreaming && msg.content && (
                      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        <StarRating onRate={(r) => onFeedback(msg.id, r)} />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-[var(--border)] bg-[var(--bg-base)]">
        <form onSubmit={handleSubmit} className="relative max-w-3xl mx-auto flex items-center gap-3">
          <div className="relative flex-1 group">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask a deep question about your documents..."
              rows={1}
              className="w-full bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)] rounded-xl py-3 px-4 focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-transparent outline-none transition-all resize-none text-sm group-hover:border-[var(--border-bright)]"
            />
            {isStreaming && (
              <button 
                type="button" 
                onClick={onStop}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-[var(--accent-red)] hover:bg-red-500/10 rounded-lg transition-all"
              >
                <div className="w-3 h-3 bg-current rounded-sm"></div>
              </button>
            )}
          </div>
          
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className={`p-3 rounded-xl transition-all shadow-lg ${
              !input.trim() || isStreaming 
                ? 'bg-[var(--bg-glass-heavy)] text-[var(--text-dim)] cursor-not-allowed opacity-50' 
                : 'bg-[var(--accent-primary)] text-white hover:shadow-[0_0_15px_rgba(124,58,237,0.4)]'
            }`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </button>
        </form>
        <p className="text-[10px] text-[var(--text-dim)] text-center mt-3 uppercase tracking-tighter">
          Powered by Distributed-AI Graph & Reflexion Agents
        </p>
      </div>
    </main>
  );
};

export default ChatArea;
