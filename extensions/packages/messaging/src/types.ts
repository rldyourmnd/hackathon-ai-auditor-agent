import type { BrowserAnalysisRequest, BrowserAnalysisResult } from '@extensions/shared';

export const MessageTypes = {
  ANALYZE_PROMPT: 'ANALYZE_PROMPT',
  PING: 'PING',
  RUN_AUDIT: 'RUN_AUDIT',
  READY: 'READY',
} as const;
export type MessageType = typeof MessageTypes[keyof typeof MessageTypes];

export interface AnalyzePromptMessage {
  type: typeof MessageTypes.ANALYZE_PROMPT;
  payload: BrowserAnalysisRequest;
}

export interface PingMessage { type: typeof MessageTypes.PING }
export interface ReadyMessage { type: typeof MessageTypes.READY; ts: number }
export interface RunAuditMessage { type: typeof MessageTypes.RUN_AUDIT }

export type IncomingToBackground = AnalyzePromptMessage | PingMessage;
export type OutgoingFromBackground = ReadyMessage | { ok: true; result: BrowserAnalysisResult } | { ok: false; error: string };
export type BackgroundToContent = RunAuditMessage | ReadyMessage;


