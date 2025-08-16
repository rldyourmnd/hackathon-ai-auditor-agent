import { Finding } from '@extensions/shared';

const emailRe = /[\w.-]+@[\w.-]+\.[A-Za-z]{2,6}/g;
const phoneRe = /(?:\+\d{1,3}[ -]?)?\d{10,14}/g;

export function runPiiDetector(text: string): Finding[] {
  const findings: Finding[] = [];
  const emails = text.match(emailRe) || [];
  const phones = text.match(phoneRe) || [];
  if (emails.length) {
    findings.push({
      id: 'pii-email',
      message: `Contains email-like patterns: ${emails.slice(0,3).join(', ')}`,
      severity: 'high',
      confidence: 0.9,
    });
  }
  if (phones.length) {
    findings.push({
      id: 'pii-phone',
      message: `Contains phone-like patterns: ${phones.slice(0,3).join(', ')}`,
      severity: 'high',
      confidence: 0.9,
    });
  }
  return findings;
}


