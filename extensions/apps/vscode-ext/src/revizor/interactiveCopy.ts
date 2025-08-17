import * as vscode from 'vscode';
import { GrabResult } from './types';

export async function tryInteractiveCopy(): Promise<GrabResult> {
	const start = Date.now();
	await vscode.window.showInformationMessage('Revizor: Click into the chat input and press Copy (Ctrl/Cmd+C). When done, press OK.', { modal: true }, 'OK');
	await new Promise(r => setTimeout(r, 60));
	const text = await vscode.env.clipboard.readText();
	return { ok: text.trim().length > 0, method: 'interactiveCopy', text, elapsedMs: Date.now() - start, platform: process.platform };
}


