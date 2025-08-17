import * as vscode from 'vscode';
import { HelperManager } from './helperManager';
import { OverlayController } from './overlay';
import { grabNow } from './revizor/grabOrchestrator';
import { PreviewPanel } from './revizor/previewPanel';
import { DiagnosticsPanel } from './revizor/diagnosticsPanel';
import { applySimPasteFromClipboard, applySimSend } from './revizor/simCopy';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

// kept for future direct server calls via SDK
async function getClient() { return {}; }

export function activate(context: vscode.ExtensionContext) {
  const auditorOutput = vscode.window.createOutputChannel('AI Auditor');
  auditorOutput.appendLine('Extension activated');

  // log uncaught errors to output channel to avoid crashing the extension host
  try {
    process.on('uncaughtException', (err: any) => { try { auditorOutput.appendLine(`UncaughtException: ${err?.stack || err}`); } catch {} });
    process.on('unhandledRejection', (reason: any) => { try { auditorOutput.appendLine(`UnhandledRejection: ${String(reason)}`); } catch {} });
  } catch {}

  // ensure helper logs to the extension output
  const helper = new HelperManager(context, auditorOutput);
  helper.start().catch((e: any) => { auditorOutput.appendLine(`Helper start failed: ${e?.message || e}`); });

  // C6: status bar, cancellation, notifications
  const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.text = 'Auditor';
  statusBarItem.tooltip = 'AI Auditor — click to open findings';
  statusBarItem.command = 'auditor.openFindings';
  statusBarItem.show();
  let currentAnalysisCancellation: vscode.CancellationTokenSource | null = null;

  function notify(level: 'info'|'warn'|'error', message: string) {
    const mode = vscode.workspace.getConfiguration().get<string>('auditor.ui.notifications', 'all');
    if (mode === 'errorsOnly' && level !== 'error') return;
    if (mode === 'warnings' && level === 'info') return;
    if (level === 'info') vscode.window.showInformationMessage(message);
    if (level === 'warn') vscode.window.showWarningMessage(message);
    if (level === 'error') vscode.window.showErrorMessage(message);
  }

  function setStatusIdle() {
    const minimal = vscode.workspace.getConfiguration().get<boolean>('auditor.ui.statusBarMinimal', false);
    statusBarItem.text = minimal ? 'Auditor' : 'Auditor: Idle';
    statusBarItem.color = undefined;
  }

  function setStatusRunning(promptCount?: number, docCount?: number) {
    const minimal = vscode.workspace.getConfiguration().get<boolean>('auditor.ui.statusBarMinimal', false);
    const p = promptCount ?? 0;
    const d = docCount ?? 0;
    statusBarItem.text = minimal ? `Auditor: ${p}/${d}` : `Auditor: Analyzing ${p} prompts + ${d} docs...`;
    statusBarItem.color = new vscode.ThemeColor('statusBarItem.prominentForeground');
  }

  function setStatusDone(findings = 0) {
    const minimal = vscode.workspace.getConfiguration().get<boolean>('auditor.ui.statusBarMinimal', false);
    statusBarItem.text = minimal ? `Auditor: ${findings}` : `Auditor: Done — ${findings} findings`;
    statusBarItem.color = findings > 0 ? new vscode.ThemeColor('statusBarItem.warningBackground') : undefined;
  }

  const overlay = new OverlayController(() => vscode.commands.executeCommand('cursorAudit.analyzeAndSend'));
  try { overlay.show(); } catch (e: any) { auditorOutput.appendLine(`Overlay show failed: ${e?.message || e}`); }

  const disposable = vscode.commands.registerCommand('ai-auditor.analyze', async () => {
    const editor = vscode.window.activeTextEditor;
    const text = editor?.document.getText(editor.selection.isEmpty ? undefined : editor.selection) || '';
    try {
      // Call helper mock to get revised suggestion
      const baseUrl = helper.baseUrl;
      let revised = text;
      if (baseUrl) {
        const r = await fetch(`${baseUrl}/analyze`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ text }) });
        if (r.ok) {
          const j: any = await r.json(); revised = j.revised ?? text;
        }
      }
      const confirm = await vscode.window.showInformationMessage('Replace chat input with analyzed text?', 'Replace', 'Cancel');
      if (confirm === 'Replace' && editor) {
        await editor.edit((eb) => eb.replace(editor.selection.isEmpty ? new vscode.Range(0, 0, editor.document.lineCount, 0) : editor.selection, revised));
      }
    } catch (e: any) {
      vscode.window.showErrorMessage(`AI Auditor error: ${e?.message || e}`);
    }
  });
  context.subscriptions.push(disposable);

  // Revizor commands
  const preview = new PreviewPanel(context);
  const diag = new DiagnosticsPanel(context);
  // load FindingsPanel defensively — if require fails, use a no-op stub so extension still runs
  let findingsPanel: any;
  try {
    // prefer static import when possible; fallback to require for packed vs dev modes
    const mod = require('./revizor/findingsPanel');
    findingsPanel = new (mod.FindingsPanel)(context);
  } catch (e: any) {
    auditorOutput.appendLine(`FindingsPanel failed to load: ${e?.message || e}`);
    findingsPanel = { show: (_: any) => { vscode.window.showInformationMessage('Findings UI unavailable (see Output).'); } };
  }
  const diagnosticCollection = vscode.languages.createDiagnosticCollection('auditor');
  context.subscriptions.push(diagnosticCollection);
  const findingsByFile = new Map<string, any[]>();
  let lastGrab: { result: any, revised: string } | null = null;

  // Try to load core analyzer if available; fall back to simple local analysis
  async function analyzeText(text: string): Promise<{ revisedText: string; findings: Array<{ kind: string; message: string }> }> {
    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const core: any = require('@extensions/core');
      if (core && typeof core.runPromptAudit === 'function') {
        const analysis = core.runPromptAudit(text);
        const revisedText = String(text).replace(/\s+$/gm, '').trim();
        const findings = (analysis?.findings || []).map((f: any) => ({ kind: String(f.id || 'finding'), message: String(f.message || '') }));
        return { revisedText, findings };
      }
    } catch {}
    // Fallback: simple local heuristics
    const findings = [] as Array<{ kind: string; message: string }>;
    if (text.length > 4000) findings.push({ kind: 'length', message: 'Text is quite long; consider shortening.' });
    if (/password|api[_\- ]?key/i.test(text)) findings.push({ kind: 'pii', message: 'Potential secret-like token detected.' });
    const revisedText = text.replace(/\s+$/gm, '').trim();
    return { revisedText, findings };
  }

  // C5: Revise prompt flow (selection or whole file)
  async function revisePromptCommand() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showInformationMessage('Open a file or select a prompt section to revise.');
      return;
    }
    const doc = editor.document;
    const selection = editor.selection;
    const selectedText = selection.isEmpty ? doc.getText() : doc.getText(selection);

    const baseUrl = helper.baseUrl;
    if (!baseUrl) {
      vscode.window.showErrorMessage('No helper available to perform revise. Start the helper first.');
      return;
    }

    const source = {
      id: crypto.createHash('sha1').update(doc.uri.toString() + (selection.isEmpty ? '#full' : `#${selection.start.line}-${selection.end.line}`)).digest('hex'),
      fileUri: doc.uri.toString(),
      fileRelPath: vscode.workspace.asRelativePath(doc.uri),
      kind: 'file',
      section: selection.isEmpty ? 'full' : `lines:${selection.start.line}-${selection.end.line}`,
      title: path.basename(doc.uri.fsPath) + (selection.isEmpty ? '' : `#sel`),
      content: selectedText,
      contentHash: crypto.createHash('sha1').update(selectedText).digest('hex')
    };

    try {
      const r = await fetch(`${baseUrl}/revise`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ source, context: [] }) });
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      const j: any = await r.json() as any;
      const patches: any[] = j?.patches ?? (Array.isArray(j) ? j : []);
      if (!Array.isArray(patches) || patches.length === 0) {
        vscode.window.showInformationMessage('No patches suggested.');
        return;
      }

      // present quickpick for patches
      const items = patches.map((p, idx) => ({ label: `[${p.kind}] ${p.title || 'patch #' + (idx+1)}`, description: p.rationale || p.description || '', idx }));
      const picks = await vscode.window.showQuickPick(items, { canPickMany: true, placeHolder: 'Select patches to apply' });
      if (!picks || picks.length === 0) return;

      const toApply = picks.map(p => patches[p.idx]);

      // prepare WorkspaceEdit; to avoid offsets, apply edits per file sorted by start descending
      const editsByFile = new Map<string, Array<{ range: vscode.Range; newText: string }>>();
      for (const patch of toApply) {
        for (const e of patch.edits || []) {
          // expect RangeLC { start:{line,character}, end:{line,character} }
          const r = e.range;
          if (!r || !r.start) continue;
          const range = new vscode.Range(r.start.line, r.start.character, r.end.line, r.end.character);
          const list = editsByFile.get(source.fileUri) || [];
          list.push({ range, newText: e.newText });
          editsByFile.set(source.fileUri, list);
        }
      }

      // check document version
      const docVersion = doc.version;
      const wsEdit = new vscode.WorkspaceEdit();
      for (const [fileUri, edits] of editsByFile) {
        const uri = vscode.Uri.parse(fileUri);
        // sort descending
        edits.sort((a,b) => {
          if (a.range.start.line !== b.range.start.line) return b.range.start.line - a.range.start.line;
          return b.range.start.character - a.range.start.character;
        });
        for (const it of edits) wsEdit.replace(uri, it.range, it.newText);
      }

      // confirm and apply
      const confirm = await vscode.window.showInformationMessage(`Apply ${Array.from(editsByFile.values()).reduce((s,a)=>s+a.length,0)} edits as one undo?`, 'Apply', 'Cancel');
      if (confirm !== 'Apply') return;

      // re-check doc version
      const currentDoc = await vscode.workspace.openTextDocument(doc.uri);
      if (currentDoc.version !== docVersion) {
        const ok = await vscode.window.showWarningMessage('Document changed since patch generation. Re-run revise or proceed and risk conflicts.', 'Proceed', 'Cancel');
        if (ok !== 'Proceed') return;
      }

      const success = await vscode.workspace.applyEdit(wsEdit);
      if (success) {
        // store last applied for quick rollback
        await context.workspaceState.update('auditor.lastAppliedPatchSet', { file: doc.uri.toString(), patches: toApply, appliedAt: new Date().toISOString() });
        vscode.window.showInformationMessage('Patches applied.');
      } else {
        vscode.window.showErrorMessage('Failed to apply patches.');
      }

    } catch (e: any) {
      auditorOutput.appendLine(`Revise failed: ${e?.message || e}`);
      vscode.window.showErrorMessage(`Revise failed: ${e?.message || e}`);
    }
  }

  context.subscriptions.push(vscode.commands.registerCommand('revizor.grabNow', async () => {
    const res = await grabNow();
    diag.show(res);
    if (!res.ok || !res.text) {
      vscode.window.showWarningMessage(res.message || 'Revizor: No text captured. Ensure focus and permissions.');
      return;
    }
    // simple mock analysis
    const findings = [] as Array<{kind:string; message:string}>;
    if (res.text.length > 4000) findings.push({ kind: 'length', message: 'Text is quite long; consider shortening.' });
    if (/password|api[_\- ]?key/i.test(res.text)) findings.push({ kind: 'pii', message: 'Potential secret-like token detected.' });
    const revised = res.text.replace(/\s+$/gm, '').trim();
    lastGrab = { result: res, revised };
    const showPreview = vscode.workspace.getConfiguration().get<boolean>('revizor.ui.showPreview', true);
    if (showPreview) {
      preview.show(res.text, { revisedText: revised, findings }, async (rev) => {
        lastGrab = { result: res, revised: rev };
        await vscode.commands.executeCommand('revizor.applyRevised');
      });
    } else {
      await vscode.commands.executeCommand('revizor.applyRevised');
    }
  }));

  // C4: Analyze workspace for prompt artifacts and docs
  async function analyzeWorkspaceCommand() {
    const wsFolders = vscode.workspace.workspaceFolders ?? [];
    if (wsFolders.length === 0) {
      vscode.window.showInformationMessage('No workspace folder open.');
      return;
    }

    const pick = await vscode.window.showQuickPick([
      { label: 'Current File', id: 'current' },
      { label: 'Selected Folder', id: 'folder' },
      { label: 'Workspace Root(s)', id: 'roots' }
    ], { placeHolder: 'Select scope for prompt analysis' });
    if (!pick) return;

    // load config with defaults
    const cfg = vscode.workspace.getConfiguration();
    const cursorCfg = cfg.get<any>('auditor.cursorPrompt') || {};
    const docsCfg = cfg.get<any>('auditor.docs') || {};

    const searchFolders: string[] = cursorCfg.searchFolders || [
      '.cursor/prompts/', '.cursor/agents/', '.cursor/policies/', 'cursor/prompts/', 'cursor/agents/', 'prompts/', '_prompts/', '.prompts/'
    ];
    const extensions: string[] = cursorCfg.extensions || ['.prompt', '.cprompt', '.txt', '.md'];
    const filenameIncludes: string[] = (cursorCfg.filenameIncludes || ['prompt','system','persona','agent','policy']).map((s: string) => s.toLowerCase());
    const jsonPromptFields: string[] = cursorCfg.jsonPromptFields || ['systemPrompt','userPrompt','prompt','instructions','policy'];
    const excludeGlobs: string[] = cursorCfg.excludeGlobs || [];

    const docsFolders: string[] = docsCfg.searchFolders || ['docs/','documentation/','handbook/','knowledge/','wiki/',''];
    const maxPrompts = 500;
    const maxDocs = 2000;

    // build candidate files
    const promptUris = new Map<string, vscode.Uri>();
    const docUris = new Map<string, vscode.Uri>();

    // helper to normalize path
    const matchInclude = (filePath: string, folders: string[], includes: string[]) => {
      const p = filePath.replace(/\\/g, '/').toLowerCase();
      // folder match
      for (const f of folders) {
        const fn = (f || '').replace(/\\/g,'/').toLowerCase();
        if (!fn || fn === '') return true; // empty means include root
        if (p.includes(`/${fn}`) || p.includes(fn)) return true;
      }
      // filename includes
      const base = path.basename(p);
      for (const inc of includes) if (base.includes(inc)) return true;
      return false;
    };

    // gather files by extension across workspace, then filter by configured folders/includes
    currentAnalysisCancellation?.cancel();
    currentAnalysisCancellation = new vscode.CancellationTokenSource();
    const token = currentAnalysisCancellation.token;
    setStatusRunning();
    await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Collecting prompt artifacts', cancellable: true }, async (progress, uiToken) => {
      uiToken.onCancellationRequested(() => { currentAnalysisCancellation?.cancel(); });
      let totalFound = 0;
      for (const ws of wsFolders) {
        for (const ext of extensions) {
          if (token.isCancellationRequested) return;
          const pattern = `**/*${ext}`;
          const uris = await vscode.workspace.findFiles(pattern, undefined, 10000);
          for (const u of uris) {
            const p = u.fsPath.replace(/\\/g,'/');
            if (excludeGlobs.some((g: string) => g && p.includes(g))) continue;
            if (!matchInclude(p, searchFolders, filenameIncludes)) continue;
            promptUris.set(u.toString(), u);
            totalFound++;
            if (promptUris.size > maxPrompts) break;
          }
          progress.report({ message: `Found ${promptUris.size} prompt candidates` });
          if (promptUris.size > maxPrompts) break;
        }
        if (promptUris.size > maxPrompts) break;
      }

      // docs (.md)
      for (const ws of wsFolders) {
        if (token.isCancellationRequested) return;
        const uris = await vscode.workspace.findFiles('**/*.md', undefined, 20000);
        for (const u of uris) {
          const p = u.fsPath.replace(/\\/g,'/');
          if (excludeGlobs.some((g: string) => g && p.includes(g))) continue;
          if (!matchInclude(p, docsFolders, [])) continue;
          docUris.set(u.toString(), u);
          if (docUris.size > maxDocs) break;
        }
        progress.report({ message: `Found ${docUris.size} docs` });
        if (docUris.size > maxDocs) break;
      }
    });
    currentAnalysisCancellation = null;
    setStatusIdle();

    if (promptUris.size === 0 && docUris.size === 0) {
      vscode.window.showInformationMessage('No prompt artifacts or docs found with current configuration/scope.');
      return;
    }

    // read contents, extract JSON fields if necessary
    const promptSources: Array<any> = [];
    const docSources: Array<any> = [];

    for (const [k, uri] of promptUris) {
      try {
        const raw = await vscode.workspace.fs.readFile(uri);
        const content = Buffer.from(raw).toString('utf8');
        if (uri.fsPath.endsWith('.json')) {
          try {
            const j = JSON.parse(content);
            for (const fld of jsonPromptFields) {
              const v = j?.[fld];
              if (typeof v === 'string' && v.trim()) {
                const id = crypto.createHash('sha1').update(uri.toString() + '::' + fld).digest('hex');
                const ch = crypto.createHash('sha1').update(v).digest('hex');
                promptSources.push({ id, fileUri: uri.toString(), fileRelPath: vscode.workspace.asRelativePath(uri), kind: 'json', section: fld, title: `${path.basename(uri.fsPath)}#${fld}`, content: v, contentHash: ch, tags: [fld] });
              }
            }
          } catch { /* ignore invalid json */ }
        } else {
          const id = crypto.createHash('sha1').update(uri.toString()).digest('hex');
          const ch = crypto.createHash('sha1').update(content).digest('hex');
          promptSources.push({ id, fileUri: uri.toString(), fileRelPath: vscode.workspace.asRelativePath(uri), kind: 'file', title: path.basename(uri.fsPath), content, contentHash: ch, tags: [] });
        }
      } catch (e: any) {
        auditorOutput.appendLine(`Failed read ${uri.toString()}: ${e?.message || e}`);
      }
    }

    for (const [k, uri] of docUris) {
      try {
        const raw = await vscode.workspace.fs.readFile(uri);
        const content = Buffer.from(raw).toString('utf8');
        const id = crypto.createHash('sha1').update(uri.toString()).digest('hex');
        const ch = crypto.createHash('sha1').update(content).digest('hex');
        const titleMatch = content.match(/^#\s+(.+)$/m);
        const title = titleMatch ? titleMatch[1].trim() : path.basename(uri.fsPath);
        docSources.push({ id, fileUri: uri.toString(), fileRelPath: vscode.workspace.asRelativePath(uri), title, content, contentHash: ch });
      } catch (e: any) {
        auditorOutput.appendLine(`Failed read doc ${uri.toString()}: ${e?.message || e}`);
      }
    }

    // enforce limits
    if (promptSources.length > maxPrompts) {
      vscode.window.showErrorMessage(`Too many prompt candidates (${promptSources.length}). Narrow scope or increase limits.`);
      return;
    }
    if (docSources.length > maxDocs) {
      vscode.window.showErrorMessage(`Too many docs (${docSources.length}). Narrow scope or increase limits.`);
      return;
    }

    // build manifest
    const manifest = {
      workspaceRoot: wsFolders[0].uri.toString(),
      generatedAt: new Date().toISOString(),
      provider: cfg.get('auditor.provider', 'local'),
      model: cfg.get('auditor.model', 'default'),
      riskThreshold: cfg.get('auditor.riskThreshold', 0.5),
      prompts: promptSources.map((p: any) => ({ id: p.id, fileRelPath: p.fileRelPath, kind: p.kind, section: p.section, contentHash: p.contentHash })),
      docs: docSources.map((d: any) => ({ id: d.id, fileRelPath: d.fileRelPath, contentHash: d.contentHash })),
      stats: { promptCount: promptSources.length, docCount: docSources.length, totalChars: promptSources.reduce((s: number, p: any) => s + (p.content?.length || 0), 0) + docSources.reduce((s: number, d: any) => s + (d.content?.length || 0), 0) }
    };

    // send to helper server if available
    const baseUrl = helper.baseUrl;
    if (!baseUrl) {
      auditorOutput.appendLine('No local helper available — manifest generated but not sent');
      auditorOutput.appendLine(JSON.stringify(manifest, null, 2));
      vscode.window.showInformationMessage(`Collected ${promptSources.length} prompts and ${docSources.length} docs (manifest saved to Auditor output).`);
      return;
    }

    try {
      const send = async (pathSuffix: string, body: any) => {
        const r = await fetch(`${baseUrl}${pathSuffix}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json().catch(() => ({}));
      };
      await send('/analyze/manifest', manifest);
      // send in batches
      const batchSize = 50;
      for (let i = 0; i < promptSources.length; i += batchSize) {
        const batch = promptSources.slice(i, i + batchSize);
        await send('/analyze/prompts', batch);
      }
      for (let i = 0; i < docSources.length; i += 20) {
        const batch = docSources.slice(i, i + 20);
        await send('/analyze/docs', batch);
      }
      await send('/analyze/run', { manifestId: manifest.workspaceRoot });
      vscode.window.showInformationMessage(`Analysis sent: ${promptSources.length} prompts, ${docSources.length} docs.`);
      // try to fetch immediate findings summary if helper provides
      try {
        const summary: any = await fetch(`${baseUrl}/analyze/summary`, { method: 'GET' }).then(r => r.ok ? r.json().catch(() => null) : null) as any;
        const payload = {
          summary: summary?.summary ?? { prompts: promptSources.length, docs: docSources.length, total: 0, bySeverity: {} },
          files: summary?.files ?? []
        };
        findingsPanel.show(payload as any);
        // store findings for later actions
        (payload.files || []).forEach((f: any) => { if (f.fileUri) findingsByFile.set(f.fileUri, f.findings || []); });
        // populate diagnostics
        createDiagnosticsFromFindings(payload);
        setStatusDone(payload.summary.total || 0);
      } catch (err) {
        auditorOutput.appendLine('No immediate findings available.');
      }
    } catch (e: any) {
      auditorOutput.appendLine(`Failed to send analysis: ${e?.message || e}`);
      vscode.window.showErrorMessage(`Failed to send analysis: ${e?.message || e}`);
    }
  }

  function createDiagnosticsFromFindings(payload: any) {
    try {
      diagnosticCollection.clear();
      const entries: Array<[vscode.Uri, vscode.Diagnostic[]]> = [];
      for (const f of (payload.files || [])) {
        const uri = vscode.Uri.parse(f.fileUri);
        const diags: vscode.Diagnostic[] = [];
        for (const fi of (f.findings || [])) {
          if (!fi.range) continue;
          const r = fi.range;
          const range = new vscode.Range(r.start.line, r.start.character, r.end.line, r.end.character);
          const severity = fi.severity === 'error' ? vscode.DiagnosticSeverity.Error : fi.severity === 'warning' ? vscode.DiagnosticSeverity.Warning : vscode.DiagnosticSeverity.Information;
          const diag = new vscode.Diagnostic(range, fi.message || String(fi.kind || 'Auditor finding'), severity);
          diag.source = 'Auditor';
          // attach finding object for later lookup via message text
          (diag as any).finding = fi;
          diags.push(diag);
        }
        if (diags.length) entries.push([uri, diags]);
      }
      diagnosticCollection.set(entries);
    } catch (e: any) {
      auditorOutput.appendLine(`Diagnostics build error: ${e?.message || e}`);
    }
  }


  // Analyze & Send commands
  async function runAnalyzeAndMaybeSend(doSend: boolean) {
    const res = await grabNow();
    diag.show(res);
    if (!res.ok || !res.text) {
      vscode.window.showWarningMessage(res.message || 'Revizor: No text captured. Ensure focus and permissions.');
      return;
    }
    const analysis = await analyzeText(res.text);
    const revised = analysis.revisedText;
    const showPreview = vscode.workspace.getConfiguration().get<boolean>('revizor.ui.showPreview', true);
    if (showPreview) {
      const findings = analysis.findings.map(f => ({ kind: f.kind, message: f.message }));
      preview.show(res.text, { revisedText: revised, findings }, async (rev) => {
        await vscode.env.clipboard.writeText(rev);
        try {
          await applySimPasteFromClipboard();
          if (doSend) await applySimSend();
        } catch {
          vscode.window.showInformationMessage('Revised text copied. Paste (and press Enter) manually.');
        }
      });
      return;
    }
    await vscode.env.clipboard.writeText(revised);
    try {
      await applySimPasteFromClipboard();
      if (doSend) await applySimSend();
    } catch {
      vscode.window.showInformationMessage('Revised text copied. Paste (and press Enter) manually.');
    }
  }

  context.subscriptions.push(
    vscode.commands.registerCommand('cursorAudit.analyzeCurrentDraft', async () => runAnalyzeAndMaybeSend(false)),
    vscode.commands.registerCommand('cursorAudit.analyzeAndSend', async () => runAnalyzeAndMaybeSend(true)),
  );

  context.subscriptions.push(vscode.commands.registerCommand('revizor.applyRevised', async () => {
    if (!lastGrab) {
      vscode.window.showInformationMessage('Revizor: Nothing to apply. Use "Grab Chat Draft" first.');
      return;
    }
    const text = lastGrab.revised;
    if (process.platform === 'linux') {
      await vscode.env.clipboard.writeText(text);
      vscode.window.showInformationMessage('Revizor: Revised text copied. Switch to chat input and paste.');
      return;
    }
    await vscode.env.clipboard.writeText(text);
    try {
      await applySimPasteFromClipboard();
    } catch (e: any) {
      vscode.window.showWarningMessage('Revizor: Paste simulation failed. Text is in clipboard; paste manually.');
    }
  }));

  context.subscriptions.push(vscode.commands.registerCommand('revizor.diagnostics.open', async () => {
    diag.show(lastGrab?.result ?? null);
  }));

  // register C4/C5 commands
  context.subscriptions.push(
    vscode.commands.registerCommand('auditor.analyzeWorkspace', analyzeWorkspaceCommand),
    vscode.commands.registerCommand('auditor.revisePrompt', revisePromptCommand),
  );

  // apply safe fixes command
  context.subscriptions.push(vscode.commands.registerCommand('auditor.applySafeFixes', async (fileUri?: string) => {
    if (!fileUri) return vscode.window.showInformationMessage('No file specified for safe fixes.');
    const findings = findingsByFile.get(fileUri) || [];
    if (!findings.length) return vscode.window.showInformationMessage('No safe fixes available for this file.');

    const uri = vscode.Uri.parse(fileUri);
    const doc = await vscode.workspace.openTextDocument(uri);
    const editor = await vscode.window.showTextDocument(doc);

    // collect safe edits
    const safeEdits: Array<{ range: vscode.Range; newText: string }> = [];
    for (const f of findings) {
      if (f.kind === 'safeFix' || f.risk === 'safe' || f.kind === 'fix') {
        if (f.edits) {
          for (const e of f.edits) {
            if (!e.range) continue;
            const range = new vscode.Range(e.range.start.line, e.range.start.character, e.range.end.line, e.range.end.character);
            safeEdits.push({ range, newText: e.newText });
          }
        }
      }
    }
    if (!safeEdits.length) return vscode.window.showInformationMessage('No safe edits found for this file.');

    // sort descending and apply as single undo
    safeEdits.sort((a,b) => {
      if (a.range.start.line !== b.range.start.line) return b.range.start.line - a.range.start.line;
      return b.range.start.character - a.range.start.character;
    });

    const wsEdit = new vscode.WorkspaceEdit();
    for (const se of safeEdits) wsEdit.replace(uri, se.range, se.newText);
    const ok = await vscode.workspace.applyEdit(wsEdit);
    if (ok) {
      vscode.window.showInformationMessage(`Applied ${safeEdits.length} safe edits.`);
    } else {
      vscode.window.showErrorMessage('Failed to apply safe edits.');
    }
  }));

  // Findings open/cancel commands
  context.subscriptions.push(
    vscode.commands.registerCommand('auditor.openFindings', async () => {
      vscode.window.showInformationMessage('Open Findings panel (not implemented UI yet).');
    }),
    vscode.commands.registerCommand('auditor.cancelAnalysis', async () => {
      if (currentAnalysisCancellation) {
        currentAnalysisCancellation.cancel();
        notify('info', 'Analysis canceled');
        setStatusIdle();
      } else {
        vscode.window.showInformationMessage('No running analysis to cancel.');
      }
    })
  );

  // C8: CodeAction provider for Auditor findings
  class AuditorCodeActionProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [vscode.CodeActionKind.QuickFix];

    provideCodeActions(document: vscode.TextDocument, range: vscode.Range, context: vscode.CodeActionContext, token: vscode.CancellationToken): vscode.CodeAction[] | undefined {
      const actions: vscode.CodeAction[] = [];
      for (const diag of context.diagnostics) {
        if (diag.source !== 'Auditor') continue;
        const finding = (diag as any).finding;
        // Safe auto-fix action
        if (finding && finding.edits && Array.isArray(finding.edits) && finding.edits.length) {
          const wsEdit = new vscode.WorkspaceEdit();
          const uri = document.uri;
          // apply only edits for this file
          for (const e of finding.edits) {
            if (!e.range) continue;
            const r = new vscode.Range(e.range.start.line, e.range.start.character, e.range.end.line, e.range.end.character);
            wsEdit.replace(uri, r, e.newText);
          }
          const qa = new vscode.CodeAction('Apply Auditor safe fix', vscode.CodeActionKind.QuickFix);
          qa.edit = wsEdit;
          qa.diagnostics = [diag];
          actions.push(qa);
        }

        // Revise action (opens revise flow)
        const reviseAction = new vscode.CodeAction('Revise with Auditor...', vscode.CodeActionKind.QuickFix);
        reviseAction.command = { command: 'auditor.revisePrompt', title: 'Revise with Auditor', arguments: [] };
        reviseAction.diagnostics = [diag];
        actions.push(reviseAction);
      }
      return actions;
    }
  }

  context.subscriptions.push(vscode.languages.registerCodeActionsProvider({ scheme: 'file' }, new AuditorCodeActionProvider(), { providedCodeActionKinds: AuditorCodeActionProvider.providedCodeActionKinds }));
}

export function deactivate() {}



