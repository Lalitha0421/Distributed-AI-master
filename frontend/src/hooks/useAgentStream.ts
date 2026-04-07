/**
 * useAgentStream.ts — Custom hook to handle SSE-based agent communication.
 * Parses streamed tokens and real-time agent trace events.
 */

import { useState, useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type { Message, AgentTraceStep, ChunkResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

export const useAgentStream = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentTrace, setCurrentTrace] = useState<AgentTraceStep[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  const askQuestion = useCallback(async (
    question: string, 
    sessionId: string = 'default', 
    source?: string,
    onFinish?: () => void
  ) => {
    if (!question.trim() || isStreaming) return;

    // Reset current trace and setup abort controller
    setCurrentTrace([]);
    setIsStreaming(true);
    abortControllerRef.current = new AbortController();

    // 1. Create and add user message
    const userMsg: Message = {
      id: uuidv4(),
      role: 'user',
      content: question,
      timestamp: new Date().toISOString()
    };
    
    // 2. Create and add initial placeholder for assistant
    const assistantId = uuidv4();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
      trace: []
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/ask/?session_id=${sessionId}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ question, source }),
        signal: abortControllerRef.current.signal
      });

      if (!response.body) throw new Error('No readable stream');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // SSE formatting is usually "data: [EVENT]PAYLOAD\n\n"
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep partial line for next chunk

        for (const line of lines) {
          const rawData = line.replace(/^data: /, '').trim();
          if (!rawData) continue;

          // ── Handle [TOKEN] ────────────────────────────────────────────────
          if (rawData.startsWith('[TOKEN]')) {
            try {
              // Now we JSON.parse the token because the backend is escaping newlines
              const tokenValue = JSON.parse(rawData.substring(7));
              setMessages(prev => prev.map(m => 
                m.id === assistantId ? { ...m, content: tokenValue } : m
              ));
            } catch (e) {
              // Fallback for non-JSON or partial tokens
              const tokenValue = rawData.substring(7);
              setMessages(prev => prev.map(m => 
                m.id === assistantId ? { ...m, content: m.content + tokenValue } : m
              ));
            }
          }

          // ── Handle [AGENT_TRACE] ──────────────────────────────────────────
          else if (rawData.startsWith('[AGENT_TRACE]')) {
            try {
              const traceItem = JSON.parse(rawData.substring(13)) as AgentTraceStep;
              setCurrentTrace(prev => [...prev, traceItem]);
              setMessages(prev => prev.map(m => 
                m.id === assistantId ? { ...m, trace: [...(m.trace || []), traceItem] } : m
              ));
            } catch (e) { console.error("Trace parse error:", e); }
          }

          // ── Handle [SOURCES] ──────────────────────────────────────────────
          else if (rawData.startsWith('[SOURCES]')) {
            try {
              const sources = JSON.parse(rawData.substring(9)) as ChunkResult[];
              setMessages(prev => prev.map(m => 
                m.id === assistantId ? { ...m, sources } : m
              ));
            } catch (e) { console.error("Source parse error:", e); }
          }

          // ── Handle [DONE] ─────────────────────────────────────────────────
          else if (rawData.startsWith('[DONE]')) {
            setMessages(prev => prev.map(m => 
              m.id === assistantId ? { ...m, isStreaming: false } : m
            ));
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.error('Generation failed:', err);
      setMessages(prev => prev.map(m => 
        m.id === assistantId ? { ...m, content: "⚠️ Connection to AI assistant failed.", isStreaming: false } : m
      ));
    } finally {
      setIsStreaming(false);
      if (onFinish) onFinish();
    }
  }, [isStreaming]);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  return { messages, isStreaming, currentTrace, askQuestion, stopStreaming };
};
