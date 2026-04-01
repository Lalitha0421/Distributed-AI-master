/**
 * useMetrics.ts — Custom hook to query the system performance and health metrics.
 * Fetches from GET /api/feedback/metrics to populate health indicators.
 */

import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import type { MetricsData } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const useMetrics = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 1. Fetch overall metrics ──────────────────────────────────────────────────
  const fetchMetrics = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/feedback/metrics`);
      setMetrics(response.data);
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchMetrics, 60000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  // 2. Submit user feedback ───────────────────────────────────────────────────
  const submitFeedback = useCallback(async (msgId: string, question: string, answer: string, rating: number) => {
    try {
      await axios.post(`${API_BASE_URL}/feedback/`, {
        session_id: "default",
        message_id: msgId,
        question,
        answer,
        rating
      });
      // Refresh metrics after feedback
      fetchMetrics();
    } catch (err) {
      console.error("Feedback failed:", err);
    }
  }, [fetchMetrics]);

  return { metrics, isLoading, submitFeedback, refresh: fetchMetrics };
};
