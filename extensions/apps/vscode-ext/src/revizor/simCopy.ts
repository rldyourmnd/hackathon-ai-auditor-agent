import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { GrabResult } from './types';

function runSimAction(action: 'copy' | 'paste' | 'send' | 'pasteAndSend'): Promise<void> {
	return new Promise((resolve, reject) => {
		const ext = vscode.extensions.getExtension('your-publisher.ai-auditor-vscode') || vscode.extensions.all.find(e => e.id.endsWith('ai-auditor-vscode'));
		if (!ext) return reject(new Error('Extension root not found'));
		const root = ext.extensionPath;
		if (process.platform === 'win32') {
			const script = path.join(root, 'scripts', 'sim-copy.ps1');
			const ps = spawn('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script, action], { windowsHide: true });
			ps.on('exit', (code) => code === 0 ? resolve() : reject(new Error(`sim-copy.ps1 exit ${code}`)));
		} else if (process.platform === 'darwin') {
			const script = path.join(root, 'scripts', 'sim-copy.applescript');
			const osa = spawn('osascript', [script, action]);
			osa.on('exit', (code) => code === 0 ? resolve() : reject(new Error(`osascript exit ${code}`)));
		} else {
			const script = path.join(root, 'scripts', 'sim-copy.sh');
			const sh = spawn('/bin/bash', [script, action]);
			sh.on('exit', (code) => code === 0 ? resolve() : reject(new Error(`sim-copy.sh exit ${code}`)));
		}
	});
}

export async function trySimCopyCopy(timeoutMs: number): Promise<GrabResult> {
	const start = Date.now();
	try {
		await runSimAction('copy');
		await new Promise(r => setTimeout(r, 60));
		const text = await vscode.env.clipboard.readText();
		return { ok: text.trim().length > 0, method: 'simCopy', text, elapsedMs: Date.now() - start, platform: process.platform };
	} catch (e: any) {
		return { ok: false, method: 'simCopy', text: '', elapsedMs: Date.now() - start, platform: process.platform, message: e?.message || String(e) };
	}
}

export async function applySimPasteFromClipboard(): Promise<void> {
	await runSimAction('paste');
}

export async function applySimSend(): Promise<void> {
	await runSimAction('send');
}

export async function applySimPasteAndSend(): Promise<void> {
	await runSimAction('pasteAndSend');
}


