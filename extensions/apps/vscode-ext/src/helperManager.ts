import * as vscode from 'vscode';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

type HelperStatus = 'stopped' | 'starting' | 'ready' | 'error';

export class HelperManager {
  private proc: ChildProcessWithoutNullStreams | null = null;
  private status: HelperStatus = 'stopped';
  private port: number | null = null;
  private tempDir: string | null = null;

  constructor(private readonly context: vscode.ExtensionContext, private readonly output?: vscode.OutputChannel) {}

  get baseUrl(): string | null {
    return this.port ? `http://127.0.0.1:${this.port}` : null;
  }

  async start(): Promise<void> {
    if (this.proc) return;
    this.status = 'starting';
    const extRoot = this.context.extensionPath;
    const helperSrc = path.join(extRoot, 'helper', 'index.js');
    if (!fs.existsSync(helperSrc)) {
      this.status = 'error';
      vscode.window.showErrorMessage('Helper script missing');
      return;
    }
    this.tempDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'ai-auditor-helper-'));
    const helperDest = path.join(this.tempDir, 'index.js');
    fs.copyFileSync(helperSrc, helperDest);

    // random free-ish port (not guaranteed)
    this.port = 43000 + Math.floor(Math.random() * 1000);

    const args = [helperDest, String(this.port)];
    const nodeExec = process.execPath; // use Electron's node
    this.proc = spawn(nodeExec, args, { stdio: 'pipe' });
    this.proc.stdout.on('data', (d) => { try { this.output?.appendLine(String(d).trim()); } catch {} });
    this.proc.stderr.on('data', (d) => { try { this.output?.appendLine(String(d).trim()); } catch {} });
    this.proc.on('exit', (code) => {
      this.output?.appendLine(`Helper exited ${code}`);
      this.proc = null;
      this.status = 'stopped';
    });

    const ok = await this.waitHealthy(5000);
    this.status = ok ? 'ready' : 'error';
    if (!ok) {
      vscode.window.showWarningMessage('Helper failed health-check');
      this.output?.appendLine('Helper failed health-check');
    }
  }

  async stop(): Promise<void> {
    if (this.proc) {
      this.proc.kill();
      this.proc = null;
    }
    this.status = 'stopped';
    try {
      if (this.tempDir && fs.existsSync(this.tempDir)) fs.rmSync(this.tempDir, { recursive: true, force: true });
    } catch {}
  }

  private async waitHealthy(timeoutMs: number): Promise<boolean> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const res = await fetch(`${this.baseUrl}/health`).then(r => r.ok);
        if (res) return true;
      } catch {}
      await new Promise(r => setTimeout(r, 100));
    }
    return false;
  }
}


