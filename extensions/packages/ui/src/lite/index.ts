// Minimal vanilla UI helpers for findings rendering
import type { BrowserAnalysisResult, BrowserFinding } from '@extensions/shared';

export function renderFindingsList(container: HTMLElement, result: BrowserAnalysisResult | undefined) {
  container.innerHTML = '';
  if (!result) {
    container.textContent = 'No data yet.';
    return;
  }
  if (result.ok) {
    const ul = document.createElement('ul');
    for (const f of result.findings) ul.appendChild(renderFindingItem(f));
    container.appendChild(ul);
  } else {
    const div = document.createElement('div');
    div.textContent = `Error: ${result.error}`;
    container.appendChild(div);
  }
}

export function renderFindingItem(f: BrowserFinding): HTMLLIElement {
  const li = document.createElement('li');
  li.textContent = `[${f.severity}] ${f.message}${f.hint ? ' – ' + f.hint : ''}`;
  return li;
}


