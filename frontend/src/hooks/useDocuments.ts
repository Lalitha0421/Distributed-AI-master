/**
 * useDocuments.ts — Custom hook to manage document listing and uploads.
 * Connects the UI to the backend storage and OCR pipeline.
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import type { DocumentInfo } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL ? (import.meta.env.VITE_API_URL.endsWith('/api') ? import.meta.env.VITE_API_URL : (import.meta.env.VITE_API_URL.endsWith('/') ? `${import.meta.env.VITE_API_URL}api` : `${import.meta.env.VITE_API_URL}/api`)) : 'http://localhost:8000/api';

export const useDocuments = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // 1. Fetch document list ───────────────────────────────────────────────────
  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/upload/list`);
      setDocuments(response.data.documents || []);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // 2. Upload file(s) ────────────────────────────────────────────────────────
  const uploadDocuments = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const response = await axios.post(`${API_BASE_URL}/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Refresh list after success
      await fetchDocuments();
      return response.data;
    } catch (err: any) {
      console.error("Upload failed:", err.response?.data || err.message);
      throw err;
    } finally {
      setIsUploading(false);
    }
  }, [fetchDocuments]);

  // 3. Delete document ──────────────────────────────────────────────────────
  const deleteDocument = useCallback(async (filename: string) => {
    // Optimistic update: remove from UI immediately
    setDocuments(prev => prev.filter(d => d.filename !== filename));
    
    setIsLoading(true);
    try {
      await axios.delete(`${API_BASE_URL}/upload/${filename}`);
      // Final sync with server
      await fetchDocuments();
    } catch (err) {
      console.error("Delete failed:", err);
      // Rollback on failure
      await fetchDocuments();
    } finally {
      setIsLoading(false);
    }
  }, [fetchDocuments]);

  return { documents, isLoading, isUploading, uploadDocuments, deleteDocument, refresh: fetchDocuments };
};
