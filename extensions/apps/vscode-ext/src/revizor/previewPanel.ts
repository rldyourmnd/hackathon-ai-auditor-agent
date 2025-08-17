import * as vscode from 'vscode';
import { AnalyzeResultMock } from './types';

export class PreviewPanel {
	private panel: vscode.WebviewPanel | null = null;

	constructor(private readonly context: vscode.ExtensionContext) {}

	show(originalText: string, analysis: AnalyzeResultMock, onApply: (revised: string) => void) {
		if (!this.panel) {
			this.panel = vscode.window.createWebviewPanel('revizorPreview', 'Revizor Preview', vscode.ViewColumn.Active, { enableScripts: true, retainContextWhenHidden: true });
			this.panel.onDidDispose(() => { this.panel = null; });
			this.panel.webview.onDidReceiveMessage((msg) => {
				if (msg?.type === 'apply') { onApply(String(msg.text || '')); }
			});
		}
		this.panel.webview.html = this.renderHtml(originalText, analysis);
	}

	dispose() { this.panel?.dispose(); this.panel = null; }

	private renderHtml(originalText: string, analysis: AnalyzeResultMock): string {
		const esc = (s: string) => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
		const revised = analysis.revisedText;
		const findings = analysis.findings.map(f => `<li><strong>${esc(f.kind)}</strong>: ${esc(f.message)}</li>`).join('');
		return `<!DOCTYPE html>
		<html>
		<head>
		<meta charset="UTF-8" />
		<style>
		body{font-family:var(--vscode-font-family);padding:12px;}
		textarea{width:100%;height:180px;}
		.findings{background:#1e1e1e22;padding:8px;border-radius:6px;margin:8px 0;}
		</style>
		</head>
		<body>
		<h3>Original</h3>
		<textarea readonly>${esc(originalText)}</textarea>
		<div class="findings"><ul>${findings}</ul></div>
		<h3>Revised</h3>
		<textarea id="rev">${esc(revised)}</textarea>
		<div>
			<button id="apply">Insert revised</button>
			<button id="copy">Copy revised</button>
		</div>
		<script>
		const vscode = acquireVsCodeApi();
		document.getElementById('apply').addEventListener('click', ()=>{
			const v = (document.getElementById('rev')).value;
			vscode.postMessage({type:'apply', text:v});
		});
		document.getElementById('copy').addEventListener('click', ()=>{
			navigator.clipboard.writeText((document.getElementById('rev')).value);
			alert('Copied. Use Paste in chat.');
		});
		</script>
		</body>
		</html>`;
	}
}


