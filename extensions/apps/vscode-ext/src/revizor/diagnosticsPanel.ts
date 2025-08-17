import * as vscode from 'vscode';
import { GrabResult } from './types';

export class DiagnosticsPanel {
	private panel: vscode.WebviewPanel | null = null;

	constructor(private readonly context: vscode.ExtensionContext) {}

	show(result: GrabResult | null) {
		if (!this.panel) {
			this.panel = vscode.window.createWebviewPanel('revizorDiag', 'Revizor Diagnostics', vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
			this.panel.onDidDispose(() => { this.panel = null; });
		}
		this.panel.webview.html = this.renderHtml(result);
	}

	private renderHtml(result: GrabResult | null): string {
		const rows = [
			['Platform', process.platform],
			['Last method', result?.method ?? '—'],
			['Elapsed ms', String(result?.elapsedMs ?? '—')],
			['Text length', String(result?.text?.length ?? '—')],
			['Message', result?.message ?? '—'],
		];
		const table = rows.map(([k,v]) => `<tr><td><b>${k}</b></td><td>${v}</td></tr>`).join('');
		const macHelp = process.platform === 'darwin' ? `<p><b>macOS:</b> Grant Accessibility permissions to VS Code/Cursor in System Settings → Privacy & Security → Accessibility. Then retry.</p>` : '';
		const winHelp = process.platform === 'win32' ? `<p><b>Windows:</b> UI Automation may be blocked by policy. Ensure the chat input has focus; try Simulated Copy fallback.</p>` : '';
		return `<!DOCTYPE html><html><head><meta charset="UTF-8" /><style>body{font-family:var(--vscode-font-family);padding:12px;} table{border-collapse:collapse;} td{border:1px solid #555;padding:6px;}</style></head><body>
		<h3>Status</h3><table>${table}</table>
		<h3>Actions</h3>
		<ul>
			<li>Copy test: Select text and press Copy. Then run "Revizor: Grab Chat Draft".</li>
			<li>Paste test: Use "Revizor: Apply Revised Text" after copying sample text.</li>
			<li>Hint: Click inside the chat input to focus before running commands.</li>
		</ul>
		${macHelp}
		${winHelp}
		</body></html>`;
	}
}


