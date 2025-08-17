import { create } from 'zustand';
import { PromptSession, AnalyzeResponse, ClarifyAnswer } from './types';

interface AppState {
  // Current session
  currentSession: PromptSession | null;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setCurrentSession: (session: PromptSession) => void;
  updateAnalysis: (analysis: AnalyzeResponse) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  applyPatches: (patchIds: string[]) => void;
  resetSession: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  currentSession: null,
  isLoading: false,
  error: null,

  setCurrentSession: (session) => {
    set({ currentSession: session });
  },

  updateAnalysis: (analysis) => {
    const currentSession = get().currentSession;
    if (currentSession) {
      set({
        currentSession: {
          ...currentSession,
          analysis,
          isAnalyzing: false,
        },
      });
    }
  },

  setLoading: (loading) => {
    set({ isLoading: loading });
  },

  setError: (error) => {
    set({ error });
  },

  applyPatches: (patchIds) => {
    const currentSession = get().currentSession;
    if (currentSession) {
      set({
        currentSession: {
          ...currentSession,
          appliedPatches: [...currentSession.appliedPatches, ...patchIds],
        },
      });
    }
  },

  resetSession: () => {
    set({
      currentSession: null,
      isLoading: false,
      error: null,
    });
  },
}));

// API service
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export class ApiService {
  static async analyzePrompt(prompt: string): Promise<AnalyzeResponse> {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: {
          content: prompt,
          format_type: 'auto',
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async applyPatches(promptId: string, patchIds: string[]): Promise<{ improved_prompt: string }> {
    const response = await fetch(`${API_BASE}/apply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt_id: promptId,
        patch_ids: patchIds,
      }),
    });

    if (!response.ok) {
      throw new Error(`Apply patches failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async clarifyPrompt(promptId: string, answers: ClarifyAnswer[]): Promise<AnalyzeResponse> {
    const response = await fetch(`${API_BASE}/clarify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt_id: promptId,
        answers,
      }),
    });

    if (!response.ok) {
      throw new Error(`Clarification failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE}/healthz`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }
}