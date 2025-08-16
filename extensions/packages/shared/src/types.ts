export type Severity = 'low' | 'medium' | 'high';

export interface Suggestion {
  title: string;
  description?: string;
  patchedText?: string;
}

export interface Finding {
  id: string;
  ruleId?: string;
  message: string;
  severity: Severity;
  suggestions?: Suggestion[];
  confidence?: number; // 0..1
  // origin/provider metadata
  provider?: string;
  model?: string;
}

export interface AnalysisRequest {
  text: string;
  metadata?: Record<string, unknown>;
}

export interface AnalysisResponse {
  findings: Finding[];
  suggestions?: Suggestion[];
  provider?: string;
  model?: string;
}

export interface Provider {
  id: string;
  name: string;
}

export interface Model {
  id: string;
  name: string;
}


