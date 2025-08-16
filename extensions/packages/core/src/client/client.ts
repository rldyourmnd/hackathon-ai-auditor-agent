import { AnalysisRequest, AnalysisResponse } from '@extensions/shared';

export type AnalyzeOptions = {
  timeoutMs?: number;
  signal?: AbortSignal;
};

export interface Client {
  analyze(req: AnalysisRequest, opts?: AnalyzeOptions): Promise<AnalysisResponse>;
  revise(req: AnalysisRequest, opts?: AnalyzeOptions): Promise<AnalysisResponse>;
}

export function createOfflineClient(): Client {
  return {
    async analyze(req) {
      // deterministic sample response
      return {
        findings: [
          {
            id: 'sample-1',
            message: 'Sample finding: text too long',
            severity: 'low',
            provider: 'offline',
            confidence: 0.5,
          },
        ],
        suggestions: [],
        provider: 'offline',
      };
    },
    async revise(req) {
      return {
        findings: [],
        suggestions: [
          {
            title: 'No-op',
            description: 'Offline stub does not revise',
          },
        ],
        provider: 'offline',
      };
    },
  };
}


