import * as vscode from 'vscode';

type FindingUI = any;
type FindingsPayload = {
  summary: { prompts: number; docs: number; total: number; bySeverity: Record<string, number> };
  files: Array<{
    fileRelPath: string;
    fileUri: string;
    sourceKind: 'prompt' | 'doc' | 'cross';
    findings: FindingUI[];
  }>;
};

export class FindingsPanel {
  private panel: vscode.WebviewPanel | null = null;

  constructor(private readonly context: vscode.ExtensionContext) {}

  show(payload: FindingsPayload) {
    if (!this.panel) {
      this.panel = vscode.window.createWebviewPanel('auditorFindings', 'Auditor Findings', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
      this.panel.onDidDispose(() => { this.panel = null; });
      this.panel.webview.onDidReceiveMessage((msg) => this.onMessage(msg));
    }
    this.panel.webview.html = this.renderHtml(payload);
  }

  private onMessage(msg: any) {
    if (!msg || !msg.type) return;
    if (msg.type === 'open') {
      const uri = vscode.Uri.parse(msg.fileUri);
      vscode.workspace.openTextDocument(uri).then(doc => {
        vscode.window.showTextDocument(doc).then(ed => {
          if (msg.range) {
            const r = new vscode.Range(msg.range.start.line, msg.range.start.character, msg.range.end.line, msg.range.end.character);
            ed.revealRange(r, vscode.TextEditorRevealType.InCenter);
            ed.selection = new vscode.Selection(r.start, r.end);
          }
        });
      });
    }
    if (msg.type === 'applySafe') {
      vscode.commands.executeCommand('auditor.applySafeFixes', msg.fileUri).then(() => {}, () => {});
    }
    if (msg.type === 'revise') {
      // open file and run revise command
      vscode.workspace.openTextDocument(vscode.Uri.parse(msg.fileUri)).then(doc => {
        vscode.window.showTextDocument(doc).then(() => {
          vscode.commands.executeCommand('auditor.revisePrompt');
        });
      });
    }
  }

  private renderHtml(payload: FindingsPayload) {
    const esc = (s: string) => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const filesHtml = payload.files.map(f => {
      const findingsList = (f.findings || []).map((fi: any, i: number) => `<li><strong>${esc(fi.severity || fi.kind || 'info')}</strong>: ${esc(fi.message || '')}</li>`).join('');
      return `<div class="file">
        <h4>${esc(f.fileRelPath)}</h4>
        <div class="actions"><button data-uri="${esc(f.fileUri)}" class="open">Open</button> <button data-uri="${esc(f.fileUri)}" class="apply">Apply safe fixes</button> <button data-uri="${esc(f.fileUri)}" class="revise">Revise</button></div>
        <div class="findings"><ul>${findingsList}</ul></div>
      </div>`;
    }).join('');

    return `<!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8" />
    <style>
    body{font-family:var(--vscode-font-family);padding:12px;color:var(--vscode-editor-foreground);}
    .file{border:1px solid var(--vscode-editorWidget-border);padding:8px;border-radius:6px;margin:8px 0}
    .actions{margin-bottom:6px}
    button{margin-right:6px}
    </style>
    </head>
    <body>
    <h3>Findings — ${payload.summary.total} total</h3>
    <div id="files">${filesHtml}</div>
    <script>
    const vscode = acquireVsCodeApi();
    document.querySelectorAll('button.open').forEach(b=>b.addEventListener('click',()=>vscode.postMessage({type:'open', fileUri: b.getAttribute('data-uri')})));
    document.querySelectorAll('button.apply').forEach(b=>b.addEventListener('click',()=>vscode.postMessage({type:'applySafe', fileUri: b.getAttribute('data-uri')})));
    document.querySelectorAll('button.revise').forEach(b=>b.addEventListener('click',()=>vscode.postMessage({type:'revise', fileUri: b.getAttribute('data-uri')})));
    </script>
    </body>
    </html>`;
  }
}


