import type { AnalysisResult, Finding } from './types';
import { renderFindingsList } from '@extensions/ui';
import { MessageTypes } from '@extensions/messaging';

const $summary = document.getElementById('summary')!;
const $list = document.getElementById('list')!;
const $reanalyze = document.getElementById('reanalyze') as HTMLButtonElement | null;

(async function init() {
  const { lastResult, lastRequest } = await chrome.storage.local.get(['lastResult', 'lastRequest']);
  render(lastResult as AnalysisResult | undefined);
  if ($reanalyze && lastRequest) {
    $reanalyze.addEventListener('click', async () => {
      $reanalyze.disabled = true;
      try {
        const res = await chrome.runtime.sendMessage({ type: MessageTypes.ANALYZE_PROMPT, payload: lastRequest });
        render(res?.result as AnalysisResult | undefined);
      } finally {
        $reanalyze.disabled = false;
      }
    });
  } else if ($reanalyze) {
    $reanalyze.disabled = true;
  }
})();

function render(res?: AnalysisResult) {
  if (!res) { $summary.textContent = 'No data yet.'; $list.innerHTML = ''; return; }
  if (res.ok) {
    $summary.textContent = `Findings: ${res.findings.length}`;
  } else {
    $summary.textContent = `Error: ${res.error}`;
  }
  renderFindingsList($list, res as any);
}


