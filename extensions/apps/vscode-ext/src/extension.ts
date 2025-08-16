import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('ai-auditor.analyze', () => {
    vscode.window.showInformationMessage('AI Auditor: analyze command triggered (boilerplate)');
  });
  context.subscriptions.push(disposable);
}

export function deactivate() {}



