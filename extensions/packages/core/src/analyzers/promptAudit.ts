/**
 * Anchor: prompt-audit analyzer
 * Aggregates simple local checks to produce findings for a prompt.
 */
import { AnalysisResponse, Finding } from '@extensions/shared';
import { runSelfCheck } from './selfCheck';
import { runLengthDetector } from '../detectors/lengthDetector';
import { runPiiDetector } from '../detectors/piiDetector';

export function runPromptAudit(text: string): AnalysisResponse {
  const findings: Finding[] = [];

  const self = runSelfCheck(text);
  if (!self.ok) {
    findings.push({ id: 'empty', message: 'Empty input', severity: 'low', confidence: 0.9 });
  }

  const lengthFindings = runLengthDetector(text);
  findings.push(...lengthFindings);

  const piiFindings = runPiiDetector(text);
  findings.push(...piiFindings);

  return {
    findings,
    suggestions: [],
    provider: 'local',
  };
}


