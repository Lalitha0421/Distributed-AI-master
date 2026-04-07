/**
 * useMetrics.ts — Custom hook to query the system performance and health metrics.
 * Fetches from GET /api/feedback/metrics to populate health indicators.
 */

import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import type { MetricsData, ImprovementsData } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

export const useMetrics = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [improvements, setImprovements] = useState<ImprovementsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 1. Fetch overall metrics ──────────────────────────────────────────────────
  const fetchMetrics = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    setIsLoading(true);
    try {
      const [metricsRes, improvementsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/feedback/metrics`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_BASE_URL}/feedback/improvements`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setMetrics(metricsRes.data);
      setImprovements(improvementsRes.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
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

  return { metrics, improvements, isLoading, submitFeedback, refresh: fetchMetrics };
};
