import { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileText, Bot, Clock, CheckCircle, Activity } from 'lucide-react';
import axios from 'axios';

interface AgentStep {
  agent: string;
  action: string;
  duration_ms: number;
  details?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  trace?: AgentStep[];
}

const API_BASE = 'http://127.0.0.1:8000/api';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState<string[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [currentTraces, setCurrentTraces] = useState<AgentStep[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE}/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      alert(`✅ Uploaded: ${file.name} (${res.data.chunks_stored || 0} chunks)`);
      if (!documents.includes(file.name)) {
        setDocuments(prev => [...prev, file.name]);
      }
      setSelectedDocument(file.name);
    } catch (err: any) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setCurrentTraces([]);

    const currentQuestion = input;
    setInput('');
    setIsLoading(true);

    try {
      const url = selectedDocument 
        ? `${API_BASE}/ask/?session_id=default&source=${encodeURIComponent(selectedDocument)}`
        : `${API_BASE}/ask/?session_id=default`;

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: currentQuestion })
      });

      if (!response.ok) throw new Error('Failed to get response');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let sources: any[] = [];
      let traces: AgentStep[] = [];

      const assistantMsg: Message = { role: 'assistant', content: '' };
      setMessages(prev => [...prev, assistantMsg]);

      // State update for the current assistant message
      const updateLastMessage = (content: string, src: any[], trc: AgentStep[]) => {
        setMessages(prev => {
          const updated = [...prev];
          if (updated.length > 0) {
            updated[updated.length - 1] = {
              role: 'assistant',
              content: content,
              sources: src.length > 0 ? src : undefined,
              trace: trc
            };
          }
          return updated;
        });
      };

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            
            // CRITICAL: Do not .trim() the entire string, as it removes the leading [TAG]
            // but also do not .trim() the content tokens which contain spaces!
            const rawData = line.slice(6);
            
            if (rawData.startsWith('[DONE]')) continue;

            if (rawData.startsWith('[AGENT_TRACE]')) {
              try {
                const trace = JSON.parse(rawData.slice(13));
                traces.push(trace);
                setCurrentTraces([...traces]);
                updateLastMessage(assistantContent, sources, traces);
              } catch (e) {}
            } else if (rawData.startsWith('[SOURCES]')) {
              try {
                sources = JSON.parse(rawData.slice(9));
                updateLastMessage(assistantContent, sources, traces);
              } catch (e) {}
            } else if (rawData.startsWith('[TOKEN]')) {
              const token = rawData.slice(7);
              assistantContent += token;
              updateLastMessage(assistantContent, sources, traces);
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-[#080b12] text-zinc-100 overflow-hidden font-sans">
      {/* 1. Sidebar - Document Management */}
      <div className="w-80 border-r border-zinc-800/40 bg-[#0c111c] flex flex-col">
        <div className="p-8 border-b border-zinc-800/40">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-500/20">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div className="space-y-0.5">
              <h1 className="text-sm font-black tracking-widest text-white">AI KNOWLEDGE</h1>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_#22c55e]" />
                <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Neural Engine L3</span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full bg-[#161e2e] hover:bg-[#1c263d] border border-zinc-800/50 py-3 rounded-xl flex items-center justify-center gap-3 text-xs font-bold transition-all text-zinc-300 hover:text-white hover:border-blue-500/30 group"
          >
            <Upload className="w-4 h-4 text-zinc-500 group-hover:text-blue-400 group-hover:scale-110 transition-all" />
            UPLOAD SOURCE
          </button>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.txt,.docx"
            onChange={(e) => e.target.files && uploadFile(e.target.files[0])}
          />
        </div>

        <div className="px-8 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 mb-4 mt-2">Active Library</div>
        <div className="flex-1 overflow-auto px-4 space-y-1.5 scrollbar-hide">
          {documents.length === 0 ? (
            <div className="px-4 py-8 text-center border border-zinc-800/20 rounded-2xl mx-2 bg-white/5 opacity-30">
                <p className="text-[11px] font-medium tracking-tighter">Awaiting Context</p>
            </div>
          ) : (
            documents.map((filename, i) => (
              <div 
                key={i} 
                className={`group flex items-center gap-3 px-4 py-3.5 rounded-2xl text-xs transition-all cursor-pointer border ${
                  selectedDocument === filename 
                    ? 'bg-blue-600/5 text-blue-400 border-blue-500/40 shadow-[0_0_20px_rgba(37,99,235,0.05)]' 
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-[#161e2e] border-transparent'
                }`}
                onClick={() => setSelectedDocument(filename)}
              >
                <FileText className="w-4 h-4 flex-shrink-0" />
                <span className="truncate font-semibold tracking-wide flex-1">{filename}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 2. Main Chat Area */}
      <div className="flex-1 flex flex-col bg-[#080b12] relative">
        <div className="h-20 px-8 border-b border-zinc-800/40 flex items-center justify-between bg-[#080b12]/80 backdrop-blur-xl sticky top-0 z-20">
          <div className="space-y-1">
             <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-blue-500/80 underline decoration-blue-500/30 underline-offset-4">Reasoning Session</h2>
             <p className="text-xs font-bold text-zinc-500 truncate max-w-md">
               {selectedDocument ? `Document Source: ${selectedDocument}` : 'Standby Mode'}
             </p>
          </div>
          <div className="flex items-center gap-6">
             <div className="flex flex-col items-end">
                <span className="text-[9px] uppercase font-black text-zinc-700 tracking-widest">Latency</span>
                <span className="text-[10px] font-bold text-zinc-500">{currentTraces.reduce((acc, s) => acc + s.duration_ms, 0)}ms</span>
             </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-8 space-y-10">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center space-y-8 opacity-10 mt-[-60px]">
              <div className="p-10 border-2 border-dashed border-zinc-800 rounded-full">
                <Bot className="w-24 h-24" />
              </div>
              <p className="text-[10px] font-black uppercase tracking-[0.4em]">Initialize Connection</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] rounded-[1.5rem] p-6 shadow-2xl ${msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-tr-none' 
                : 'bg-[#111827] border border-zinc-800/50 text-zinc-200 rounded-tl-none shadow-blue-900/5'}`}>
                <p className="whitespace-pre-wrap leading-[1.8] text-[15px] font-medium">{msg.content}</p>
                {msg.sources && (
                  <div className="mt-8 pt-5 border-t border-white/5 flex flex-wrap gap-2.5">
                    {msg.sources.map((s, i) => (
                      <span key={i} className="px-3 py-1.5 bg-zinc-950/60 border border-white/5 rounded-xl text-[9px] text-zinc-500 font-black tracking-tighter uppercase whitespace-nowrap">
                        REF: {s.source}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && messages[messages.length-1]?.role === 'user' && (
            <div className="flex justify-start">
               <div className="bg-[#111827] border border-zinc-800/50 rounded-2xl px-8 py-5 flex items-center gap-4">
                  <div className="flex gap-2">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" />
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:200ms]" />
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:400ms]" />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-[0.2em] text-zinc-600">Processing Knowledge</span>
               </div>
            </div>
          )}
          <div ref={chatEndRef} className="h-10" />
        </div>

        <div className="p-8">
          <div className="max-w-4xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Inject query into Neural Brain..."
              className="w-full bg-[#111827] border border-zinc-800/80 rounded-[2rem] pl-8 pr-16 py-6 text-sm focus:outline-none focus:border-blue-500/50 shadow-2xl placeholder:text-zinc-800 font-medium"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="absolute right-3 top-3 p-4 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 text-white rounded-full transition-all shadow-xl active:scale-90"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* 3. Agent Trace Panel - Timeline UI */}
      <div className="w-[28rem] border-l border-zinc-800/40 bg-[#0c111c] flex flex-col shadow-[-20px_0_40px_rgba(0,0,0,0.4)] relative z-30">
        <div className="p-8 border-b border-zinc-800/40">
           <div className="flex items-center gap-3">
              <Activity className="w-4 h-4 text-blue-500" />
              <h3 className="text-[11px] font-black uppercase tracking-[0.3em] text-zinc-500">Agent Trace</h3>
           </div>
        </div>
        
        <div className="flex-1 overflow-auto p-8 space-y-8 scrollbar-hide">
          {currentTraces.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 space-y-6 opacity-10 grayscale">
              <Activity className="w-16 h-16" />
              <p className="text-[10px] font-black uppercase tracking-[0.4em]">STANDBY</p>
            </div>
          ) : (
            currentTraces.map((step, i) => (
              <div key={i} className="relative pl-10 animation-slide-up">
                {/* Visual Connector Line */}
                {i < currentTraces.length - 1 && (
                  <div className="absolute left-[11px] top-[26px] bottom-[-36px] w-[2px] bg-gradient-to-b from-blue-600 to-transparent opacity-20" />
                )}
                
                {/* Timeline Dot */}
                <div className="absolute left-0 top-0.5 z-10">
                   <div className="w-[24px] h-[24px] bg-blue-600/10 border border-blue-500/40 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(37,99,235,0.2)]">
                      <div className="w-[8px] h-[8px] bg-blue-500 rounded-full animate-pulse shadow-[0_0_8px_#3b82f6]" />
                   </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-baseline">
                    <span className="text-[10px] font-black uppercase text-blue-500 tracking-[0.2em]">{step.agent}</span>
                    <span className="text-[10px] font-black text-zinc-700">{step.duration_ms}MS</span>
                  </div>
                  
                  <div className="bg-[#111827] border border-zinc-800/80 rounded-[1.25rem] p-5 shadow-2xl hover:border-blue-500/40 transition-all group">
                     <p className="text-[13px] font-bold text-zinc-100 mb-3 group-hover:text-blue-200">{step.action}</p>
                     {step.details && (
                       <div className="bg-[#080b12] border border-zinc-800/60 rounded-xl p-4">
                         <p className="text-[11px] text-zinc-500 leading-relaxed font-medium italic">
                           "{step.details}"
                         </p>
                       </div>
                     )}
                  </div>
                </div>
              </div>
            ))
          )}
          {isLoading && currentTraces.length < 4 && (
            <div className="flex items-center gap-5 pl-1.5 opacity-40">
               <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
               <span className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600">Syncing Agent...</span>
            </div>
          )}
        </div>
        
        <div className="p-8 border-t border-zinc-800/60 bg-[#080b12]/50">
           <div className="flex justify-between items-center">
              <span className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Neural Load</span>
              <span className="text-xl font-black text-zinc-100 tracking-tighter">{currentTraces.length}/4 Nodes</span>
           </div>
        </div>
      </div>
    </div>
  );
}

export default App;