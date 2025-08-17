import * as vscode from 'vscode';

export class OverlayController {
  private button?: vscode.StatusBarItem; // using status bar as minimal visible affordance placeholder

  constructor(private readonly onClick: () => void) {}

  show() {
    if (!this.button) {
      this.button = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 10);
      this.button.text = '$(beaker) Analyze & Send';
      this.button.tooltip = 'Analyze and revise prompt, then (optionally) send';
      this.button.command = 'cursorAudit.analyzeAndSend';
    }
    this.button.show();
  }

  hide() {
    this.button?.hide();
  }
}


