import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { GrabResult } from './types';

export async function tryWinUia(timeoutMs: number): Promise<GrabResult> {
	const start = Date.now();
	if (process.platform !== 'win32') {
		return { ok: false, method: 'uia', text: '', elapsedMs: 0, platform: process.platform, message: 'Not Windows' };
	}
	const extRoot = vscode.extensions.getExtension('your-publisher.ai-auditor-vscode')?.extensionPath || vscode.extensions.all.find(e => e.id.endsWith('ai-auditor-vscode'))?.extensionPath || '';
	const script = path.join(extRoot, 'scripts', 'grab-uia.ps1');
	return new Promise<GrabResult>((resolve) => {
		const ps = spawn('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script], { windowsHide: true });
		let out = '';
		let err = '';
		let settled = false;
		const done = (ok: boolean, msg?: string) => {
			if (settled) return; settled = true;
			const elapsedMs = Date.now() - start;
			resolve({ ok, method: 'uia', text: ok ? out.trim() : '', elapsedMs, platform: process.platform, message: msg || err.trim() });
		};
		const t = setTimeout(() => { try { ps.kill(); } catch {} done(false, 'Timeout'); }, timeoutMs);
		ps.stdout.setEncoding('utf8');
		ps.stdout.on('data', (d) => { out += String(d); });
		ps.stderr.on('data', (d) => { err += String(d); });
		ps.on('exit', (code) => {
			clearTimeout(t);
			if (code === 0 && out.trim().length > 0) done(true); else done(false, `Exit ${code}`);
		});
	});
}


