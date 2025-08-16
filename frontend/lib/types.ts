// Types for API communication
export interface PromptInput {
  content: string;
  format_type: "auto" | "text" | "markdown" | "xml";
}

export interface Patch {
  id: string;
  type: "safe" | "risky";
  category: "clarity" | "structure" | "quality";
  description: string;
  original: string;
  improved: string;
  rationale: string;
  confidence: number;
}

export interface ClarifyQuestion {
  id: string;
  text: string;
  category: "scope" | "constraints" | "context" | "format";
  priority: "critical" | "important" | "optional";
}

export interface ClarifyAnswer {
  question_id: string;
  answer: string;
}

export interface SemanticEntropy {
  entropy: number;
  spread: number;
  clusters: number;
  samples: string[];
}

export interface MetricScore {
  score: number;
  rationale: string;
  details: Record<string, any>;
}

export interface Contradiction {
  type: "intra" | "inter";
  description: string;
  severity: "low" | "medium" | "high";
  locations: string[];
}

export interface MetricReport {
  prompt_id: string;
  original_prompt: string;
  analyzed_at: string;
  detected_language?: string;
  translated: boolean;
  format_valid: boolean;
  semantic_entropy?: SemanticEntropy;
  judge_score?: MetricScore;
  contradictions?: Contradiction[];
  complexity_score?: number;
  length_chars?: number;
  length_words?: number;
  overall_score?: number;
  improvement_priority?: "low" | "medium" | "high";
  patches: Patch[];
  clarify_questions: ClarifyQuestion[];
}

export interface AnalyzeResponse {
  report: MetricReport;
  patches: Patch[];
  questions: ClarifyQuestion[];
}

export interface PromptSession {
  id: string;
  originalPrompt: string;
  currentPrompt: string;
  analysis?: AnalyzeResponse;
  appliedPatches: string[];
  isAnalyzing: boolean;
  error?: string;
}
