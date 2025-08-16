import * as vscode from 'vscode';

async function getClient() {
  const mod = await import('@extensions/client-sdk');
  const { createClient } = mod as any;
  const version = vscode.extensions.getExtension('your-publisher.ai-auditor-vscode')?.packageJSON?.version || '0.0.0';
  return createClient({
    baseUrl: 'http://localhost:8000/api',
    getApiKey: async () => {
      const key = await vscode.workspace.getConfiguration('aiAuditor').get<string>('apiKey');
      return key ?? null;
    },
    envMetaProvider: () => ({ env: 'vscode', extensionVersion: version, os: process.platform }),
    fetchLike: (globalThis as any).fetch,
    idempotency: { enabled: true },
    timeoutMs: 20000,
  });
}

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('ai-auditor.analyze', async () => {
    const editor = vscode.window.activeTextEditor;
    const text = editor?.document.getText(editor.selection.isEmpty ? undefined : editor.selection) || '';
    try {
      const client = await getClient();
      const res = await client.analyze({ text, lang: 'ru' });
      vscode.window.showInformationMessage(`AI Auditor: ${res.findings.length} findings`);
    } catch (e: any) {
      vscode.window.showErrorMessage(`AI Auditor error: ${e?.message || e}`);
    }
  });
  context.subscriptions.push(disposable);
}

export function deactivate() {}



