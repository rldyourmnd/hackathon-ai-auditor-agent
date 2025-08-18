export * from './types';
export * from './browser';
export const MSG = {
  ANALYZE_PROMPT: 'ANALYZE_PROMPT',
  ANALYZE_DONE: 'ANALYZE_DONE',
} as const;
export type AnalyzePromptMessage = {
  type: typeof MSG.ANALYZE_PROMPT,
  payload: import('@extensions/shared').AnalysisRequest,
};
export type AnalyzeDoneMessage = {
  type: typeof MSG.ANALYZE_DONE,
  payload: import('@extensions/shared').AnalysisResult,
};
export type AnyMessage = AnalyzePromptMessage | AnalyzeDoneMessage;


