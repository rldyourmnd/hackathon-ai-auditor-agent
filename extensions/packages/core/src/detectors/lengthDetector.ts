import { Finding } from '@extensions/shared';

export function runLengthDetector(text: string): Finding[] {
  const findings: Finding[] = [];
  if (text.length > 1000) {
    findings.push({
      id: 'length-1',
      message: 'Text is very long (>1000 chars)',
      severity: 'medium',
      confidence: 0.8,
    });
  } else if (text.length > 500) {
    findings.push({
      id: 'length-2',
      message: 'Text is long (>500 chars)',
      severity: 'low',
      confidence: 0.6,
    });
  }
  return findings;
}


