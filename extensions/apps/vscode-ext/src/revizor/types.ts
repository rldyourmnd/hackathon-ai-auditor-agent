export type GrabMethod = 'uia' | 'simCopy' | 'interactiveCopy';

export interface GrabResult {
	ok: boolean;
	method: GrabMethod | null;
	text: string;
	elapsedMs: number;
	platform: NodeJS.Platform;
	message?: string;
}

export interface AnalyzeResultMock {
	revisedText: string;
	findings: Array<{ kind: string; message: string }>;
}


