import * as vscode from 'vscode';
import { tryWinUia } from './winUia';
import { trySimCopyCopy } from './simCopy';
import { tryInteractiveCopy } from './interactiveCopy';
import { GrabMethod, GrabResult } from './types';

function isEnabled(method: GrabMethod, enabled: GrabMethod[], noClipboard: boolean): boolean {
	if (!enabled.includes(method)) return false;
	if (noClipboard && (method === 'simCopy' || method === 'interactiveCopy')) return false;
	return true;
}

export async function grabNow(): Promise<GrabResult> {
	const enabled = vscode.workspace.getConfiguration().get<GrabMethod[]>('revizor.methods.enabled', ['uia','simCopy','interactiveCopy']);
	const noClipboard = vscode.workspace.getConfiguration().get<boolean>('revizor.privacy.noClipboard', false);

	const steps: Array<() => Promise<GrabResult>> = [];
	if (isEnabled('uia', enabled, noClipboard)) steps.push(() => tryWinUia(4000));
	if (isEnabled('simCopy', enabled, noClipboard)) steps.push(() => trySimCopyCopy(500));
	if (isEnabled('interactiveCopy', enabled, noClipboard)) steps.push(() => tryInteractiveCopy());

	for (const step of steps) {
		try {
			const res = await step();
			if (res.ok && res.text.trim().length > 0) return res;
		} catch {}
	}

	return { ok: false, method: null, text: '', elapsedMs: 0, platform: process.platform, message: 'No method succeeded. Ensure focus and permissions.' };
}


