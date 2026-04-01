/**
 * index.ts — Centralized TypeScript interfaces for the React frontend.
 * Matches the backend Pydantic models.
 */

export interface ChunkResult {
  text: string;
  source: string;
  chunk_id?: number;
  score?: number;
}

export interface AgentTraceStep {
  agent: "Planner" | "Retriever" | "Generator" | "Grader";
  step_type?: string;                   // Optional override
  action: string;
  duration_ms: number;
  status: "running" | "done" | "retrying" | "failed";
  details?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: ChunkResult[];
  confidence?: "high" | "medium" | "low";
  trace?: AgentTraceStep[];
  isStreaming?: boolean;
}

export interface DailyMetric {
  date: string;
  avg_faithfulness: number;
  avg_relevance: number;
  total_questions: number;
  avg_rating: number;
}

export interface MetricsData {
  total_questions: number;
  avg_faithfulness: number;
  avg_relevance: number;
  avg_user_rating: number;
  avg_retry_count: number;
  last_updated: string;
  daily_history: DailyMetric[];
}

export interface DocumentInfo {
  filename: string;
  uploaded_at: string;
  chunks: number;
}
