import * as vscode from 'vscode';
import { GrabMethod, GrabResult } from './types';

export async function grabNow(): Promise<GrabResult> {
	const noClipboard = vscode.workspace.getConfiguration().get<boolean>('revizor.privacy.noClipboard', false);

	// Simple workflow: Just read current clipboard content (user copies text manually)
	if (!noClipboard) {
		try {
			const clipboardResult = await trySimpleClipboardGrab();
			if (clipboardResult.ok && clipboardResult.text.trim().length > 0) {
				return clipboardResult;
			}
		} catch {}
	}

	return { ok: false, method: null, text: '', elapsedMs: 0, platform: process.platform, message: 'Please select and copy text (Ctrl+C) first, then click Grab Cursor.' };
}

async function trySimpleClipboardGrab(): Promise<GrabResult> {
	const start = Date.now();
	if (process.platform !== 'win32') {
		return { ok: false, method: 'clipboard', text: '', elapsedMs: 0, platform: process.platform, message: 'Simple clipboard method only supports Windows' };
	}

	const extRoot = vscode.extensions.getExtension('your-publisher.ai-auditor-vscode')?.extensionPath || 
		vscode.extensions.all.find(e => e.id.endsWith('ai-auditor-vscode'))?.extensionPath || '';
	const script = require('path').join(extRoot, 'scripts', 'grab-clipboard-simple.ps1');

	return new Promise<GrabResult>((resolve) => {
		const { spawn } = require('child_process');
		const ps = spawn('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script], { windowsHide: true });
		let out = '';
		let err = '';
		let settled = false;
		
		const done = (ok: boolean, msg?: string) => {
			if (settled) return; 
			settled = true;
			const elapsedMs = Date.now() - start;
			resolve({ 
				ok, 
				method: 'clipboard', 
				text: ok ? out.trim() : '', 
				elapsedMs, 
				platform: process.platform, 
				message: msg || err.trim() 
			});
		};

		const timeout = setTimeout(() => { 
			try { ps.kill(); } catch {} 
			done(false, 'Simple clipboard grab timeout'); 
		}, 1000);

		ps.stdout.setEncoding('utf8');
		ps.stdout.on('data', (d: any) => { out += String(d); });
		ps.stderr.on('data', (d: any) => { err += String(d); });
		ps.on('exit', (code: number) => {
			clearTimeout(timeout);
			if (code === 0 && out.trim().length > 0) {
				done(true);
			} else {
				done(false, `Exit ${code}`);
			}
		});
	});
}