import { z } from 'zod';

// UI-focused severities used by popup/content
export const UiSeverityEnum = z.enum(['info', 'warn', 'error']);
export type UiSeverity = z.infer<typeof UiSeverityEnum>;

export const BrowserAnalysisRequestSchema = z.object({
  text: z.string().min(1),
  source: z.literal('chatgpt'),
  url: z.string().url(),
  ts: z.number().int().nonnegative(),
  meta: z.record(z.unknown()).optional(),
});
export type BrowserAnalysisRequest = z.infer<typeof BrowserAnalysisRequestSchema>;

export const BrowserFindingSchema = z.object({
  severity: UiSeverityEnum,
  message: z.string(),
  hint: z.string().optional(),
  start: z.number().int().nonnegative().optional(),
  end: z.number().int().nonnegative().optional(),
});
export type BrowserFinding = z.infer<typeof BrowserFindingSchema>;

export const BrowserAnalysisResponseOkSchema = z.object({
  ok: z.literal(true),
  findings: z.array(BrowserFindingSchema),
  revisedText: z.string().optional(),
});
export type BrowserAnalysisResponseOk = z.infer<typeof BrowserAnalysisResponseOkSchema>;

export const BrowserAnalysisResponseErrSchema = z.object({
  ok: z.literal(false),
  error: z.string(),
});
export type BrowserAnalysisResponseErr = z.infer<typeof BrowserAnalysisResponseErrSchema>;

export const BrowserAnalysisResultSchema = z.union([
  BrowserAnalysisResponseOkSchema,
  BrowserAnalysisResponseErrSchema,
]);
export type BrowserAnalysisResult = z.infer<typeof BrowserAnalysisResultSchema>;

// Mapping helpers from core severities to UI severities
export type CoreSeverity = 'low' | 'medium' | 'high';
export function mapCoreSeverityToUi(sev: CoreSeverity): UiSeverity {
  if (sev === 'high') return 'error';
  if (sev === 'medium') return 'warn';
  return 'info';
}


