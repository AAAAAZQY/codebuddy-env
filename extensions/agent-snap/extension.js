// local.agent-snap 0.0.8 -- batch view of bridge edits.
// Snapshots are grouped into BATCHES by time gap; one diff per finished batch.
// Data source: <backupDir>/<timestamp>/manifest.json written by bridge-edit.py
// Only snapshots whose real_path is inside the current workspace are shown.
// NOTE: keep this file pure ASCII; Chinese strings use \uXXXX escapes.
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const SCHEME_SNAP = 'agentsnap';
const SCHEME_REAL = 'agentreal';

function sha256(buf) { return crypto.createHash('sha256').update(buf).digest('hex'); }

function gbkDecode(buf) {
    try { return new TextDecoder('gbk').decode(buf); }
    catch (e) { return buf.toString('latin1'); }
}

function cfg() { return vscode.workspace.getConfiguration('agentSnap'); }
function backupDir() { return cfg().get('backupDir', 'D:\\Codebuddy\\backup\\bridge-edit'); }
function batchGapMs() { const s = cfg().get('batchGapSec', 120); return Math.max(5, s) * 1000; }
function autoQuietMs() { const s = cfg().get('autoOpenQuietSec', 4); return Math.max(0, s) * 1000; }
function scopeToWorkspace() { return cfg().get('scopeToWorkspace', true) !== false; }

function normPath(p) {
    return path.resolve(String(p || '')).replace(/[\\/]+/g, '\\').toLowerCase();
}
function isInWorkspace(realPath) {
    if (!scopeToWorkspace()) return true;
    const roots = (vscode.workspace.workspaceFolders || []).map(w => normPath(w.uri.fsPath) + '\\');
    if (!roots.length) return true;   // no folder open: keep old behaviour
    const p = normPath(realPath);
    return roots.some(r => p.startsWith(r));
}
// fs.watch sees every project's snapshots; ignore the ones not in this workspace.
function snapEventInWorkspace(fname) {
    if (!scopeToWorkspace()) return true;
    const m = /^(\d{8}-\d{6}-[^\\/]+)/.exec(String(fname || ''));
    if (!m) return true;
    try {
        const man = JSON.parse(fs.readFileSync(path.join(backupDir(), m[1], 'manifest.json'), 'utf8'));
        return isInWorkspace(man.real_path);
    } catch (e) { return true; }   // manifest not written yet
}

// Scan snapshot dirs, return [{dir, manifest, snapFile, stamp}] sorted by stamp desc (newest first)
function listSnapshots() {
    const root = backupDir();
    const out = [];
    let ents;
    try { ents = fs.readdirSync(root); } catch (e) { return out; }
    for (const name of ents) {
        const dir = path.join(root, name);
        let st;
        try { st = fs.statSync(dir); } catch (e) { continue; }
        if (!st.isDirectory()) continue;
        const mf = path.join(dir, 'manifest.json');
        let man;
        try { man = JSON.parse(fs.readFileSync(mf, 'utf8')); } catch (e) { continue; }
        if (!man.real_path || !fs.existsSync(man.real_path)) continue;  // skip dangling: real file gone
        if (!isInWorkspace(man.real_path)) continue;                     // another project's snapshot
        const snapFile = (man.existed_before && man.base) ? path.join(dir, man.base) : null;
        if (man.existed_before && (!snapFile || !fs.existsSync(snapFile))) continue;
        out.push({ dir, manifest: man, snapFile, stamp: name });
    }
    out.sort((a, b) => (a.stamp < b.stamp ? 1 : -1));
    return out;
}

function stampToMs(stamp) {
    const m = /^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})(?:-e(\d+))?/.exec(String(stamp));
    if (!m) return 0;
    return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6], +(m[7] || 0)).getTime();
}

// Group consecutive snapshots (by time gap) into batches; newest batch first.
function buildBatches() {
    const asc = listSnapshots().slice().sort((a, b) => (a.stamp < b.stamp ? -1 : 1));
    const batches = [];
    let cur = null;
    let prev = null;
    for (const s of asc) {
        const ms = stampToMs(s.stamp);
        if (!cur || (prev !== null && ms - prev > batchGapMs())) { cur = { items: [] }; batches.push(cur); }
        cur.items.push(s);
        prev = ms;
    }
    for (const b of batches) {
        const map = new Map();
        for (const s of b.items) {
            const p = s.manifest.real_path;
            let a = map.get(p);
            if (!a) { a = []; map.set(p, a); }
            a.push(s);
        }
        b.files = Array.from(map.entries()).map(([p, items]) => ({ path: p, items, first: items[0], last: items[items.length - 1] }));
        b.startTime = b.items[0].manifest.time;
        b.endTime = b.items[b.items.length - 1].manifest.time;
        b.endStamp = b.items[b.items.length - 1].stamp;
    }
    return batches.reverse();
}

function nextNewerSnap(realPath, stamp) {
    const all = listSnapshots().filter(x => x.manifest.real_path === realPath);
    const i = all.findIndex(x => x.stamp === stamp);
    return i > 0 ? all[i - 1] : null;
}

function snapUri(absPath) { return vscode.Uri.parse(SCHEME_SNAP + ':' + encodeURIComponent(absPath)); }
function realUri(realPath, bust) { return vscode.Uri.parse(SCHEME_REAL + ':' + encodeURIComponent(realPath) + '?t=' + (bust || Date.now())); }
function pinUri(uri) { return decodeURIComponent(uri.path); }
function findSnapByUri(uri) { const p = pinUri(uri); return listSnapshots().find(s => s.snapFile === p) || null; }
// Frozen post-write bytes saved by bridge-edit.py; used when no newer snapshot exists.
function frozenAfterUri(man) { return (man && man.after_file && fs.existsSync(man.after_file)) ? snapUri(man.after_file) : null; }

function batchLabel(b) { return b.startTime === b.endTime ? b.startTime : (b.startTime + ' ~ ' + b.endTime); }

// state AFTER the batch's last write to this file = before the next newer write (same file), else current file
function afterOf(file) {
    const n = nextNewerSnap(file.path, file.last.stamp);
    if (n) return { uri: snapUri(n.snapFile), name: n.manifest.time + ' \u5feb\u7167' };
    const frozen = frozenAfterUri(file.last.manifest);
    return frozen ? { uri: frozen, name: '\u6539\u52a8\u540e' } : { uri: realUri(file.path), name: '\u5f53\u524d' };
}

class TextProvider {
    constructor(readFn) {
        this.readFn = readFn;
        this._emitter = new vscode.EventEmitter();
        this.onDidChange = this._emitter.event;
    }
    provideTextDocumentContent(uri) {
        try { return this.readFn(uri); }
        catch (e) { return '<< \u8bfb\u53d6\u5931\u8d25: ' + e.message + ' >>'; }
    }
}

// Batch diff for ONE file: before the batch's first write -> after the batch's last write.
function openBatchFileDiff(batch, file) {
    if (!file || !file.first || !file.first.snapFile) {
        vscode.window.showInformationMessage('\u65e0\u6cd5\u6bd4\u5bf9\uff08\u7f3a\u5c11\u6539\u524d\u5feb\u7167\uff09');
        return;
    }
    const left = snapUri(file.first.snapFile);
    const after = afterOf(file);
    const n = file.items.length;
    const title = path.basename(file.path) + '  \u672c\u6279\u6b21(' + n + '\u5904)  \u6539\u524d\u2192' + after.name;
    return vscode.commands.executeCommand('vscode.diff', left, after.uri, title, { preview: false });
}

// diff of a single write: before this write -> after this write
function openStepDiff(snap) {
    const m = snap.manifest;
    const n = nextNewerSnap(m.real_path, snap.stamp);
    const frozen = frozenAfterUri(m);
    const right = n ? snapUri(n.snapFile) : (frozen || realUri(m.real_path));
    const rightName = n ? (n.manifest.time + ' \u5feb\u7167') : (frozen ? '\u6539\u52a8\u540e' : '\u5f53\u524d');
    const kind = m.kind === 'redo' ? '\u56de\u9000\u70b9' : '\u6539\u52a8';
    const title = m.base + '  ' + m.time + ' \u7684' + kind + ' (\u6539\u524d \u2192 ' + rightName + ')';
    return vscode.commands.executeCommand('vscode.diff', snapUri(snap.snapFile), right, title, { preview: false });
}

function openDiffVsCurrent(snap) {
    const m = snap.manifest;
    const kind = m.kind === 'redo' ? '\u56de\u9000\u70b9' : '\u5feb\u7167';
    const title = m.base + '  ' + m.time + ' ' + kind + ' (\u2190 \u5f53\u524d\u5bf9\u6bd4)';
    return vscode.commands.executeCommand('vscode.diff', snapUri(snap.snapFile), realUri(m.real_path), title, { preview: false });
}

// Snapshot dir created by the extension itself (rollback saves a "redo point").
function createSnapshot(realPath, preBytes, kind, note) {
    const t = new Date();
    const pad = (n, w) => String(n).padStart(w || 2, '0');
    const stamp = String(t.getFullYear()) + pad(t.getMonth() + 1) + pad(t.getDate()) + '-' +
        pad(t.getHours()) + pad(t.getMinutes()) + pad(t.getSeconds()) + '-e' + pad(t.getMilliseconds(), 3);
    const dir = path.join(backupDir(), stamp);
    fs.mkdirSync(dir, { recursive: true });
    const base = path.basename(realPath);
    fs.writeFileSync(path.join(dir, base), preBytes);
    const man = {
        version: 1, kind: kind, time: t.toLocaleString('sv-SE'), real_path: realPath, base: base,
        existed_before: true, note: note || '',
        sha_before: sha256(preBytes), sha_after: null,
        size_before: preBytes.length, size_after: null
    };
    fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(man));
    return { dir, manifest: man, snapFile: path.join(dir, base), stamp };
}

async function rollback(snap) {
    if (!snap) return;
    const m = snap.manifest;
    if (!m.existed_before || !snap.snapFile) {
        vscode.window.showWarningMessage('\u8be5\u5feb\u7167\u65e0\u6539\u524d\u5185\u5bb9\uff08\u65b0\u5efa\u6587\u4ef6\uff09\uff0c\u65e0\u6cd5\u56de\u9000');
        return;
    }
    let cur;
    try { cur = fs.readFileSync(m.real_path); }
    catch (e) { vscode.window.showErrorMessage('\u8bfb\u4e0d\u5230\u771f\u5b9e\u6587\u4ef6: ' + m.real_path); return; }
    const drifted = cur && m.sha_after && sha256(cur) !== m.sha_after;
    const pick = await vscode.window.showWarningMessage(
        '\u56de\u9000 ' + m.base + ' \u5230 ' + m.time + ' \u7684\u72b6\u6001\uff1f' +
        '\n\u5373\u64a4\u9500\u8be5\u6b21\u53ca\u5176\u4e4b\u540e\u7684\u6240\u6709\u7ecf\u6865\u6539\u52a8\u3002' +
        (drifted ? '\n\u6ce8\u610f\uff1a\u6587\u4ef6\u5728\u5feb\u7167\u4e4b\u540e\u53c8\u88ab\u975e\u6865\u65b9\u5f0f\u6539\u8fc7\uff0c\u56de\u9000\u4f1a\u8986\u76d6\u8fd9\u4e9b\u6539\u52a8\u3002' : '') +
        '\n\u5f53\u524d\u5185\u5bb9\u4f1a\u5148\u5b58\u4e3a\u300c\u56de\u9000\u70b9\u300d\uff0c\u53ef\u518d\u64a4\u9500\u3002',
        { modal: true }, '\u56de\u9000');
    if (pick !== '\u56de\u9000') return;
    createSnapshot(m.real_path, cur, 'redo', 'rollback of ' + snap.stamp);
    try { fs.writeFileSync(m.real_path, fs.readFileSync(snap.snapFile)); }
    catch (e) { vscode.window.showErrorMessage('\u56de\u9000\u5199\u5165\u5931\u8d25: ' + e.message); return; }
    refreshAll();
    vscode.window.showInformationMessage('\u5df2\u56de\u9000: ' + m.base + ' \u2190 ' + m.time +
        (drifted ? '\uff08\u8986\u76d6\u4e86\u5feb\u7167\u540e\u7684\u6539\u52a8\uff09' : ''));
}

// ---- activity-bar tree: batch -> file -> single write ----
class HistoryProvider {
    constructor() {
        this._emitter = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._emitter.event;
        this._batches = [];
    }
    refresh() {
        this._batches = buildBatches();
        this._emitter.fire();
    }
    getTreeItem(el) {
        if (el.kind === 'batch') {
            const b = el.batch;
            let nchg = 0;
            for (const f of b.files) nchg += f.items.length;
            const ti = new vscode.TreeItem(batchLabel(b), vscode.TreeItemCollapsibleState.Collapsed);
            ti.description = b.files.length + ' \u6587\u4ef6 \u00b7 ' + nchg + ' \u5904';
            ti.tooltip = '\u6279\u6b21 ' + batchLabel(b) + '\n' + b.files.length + ' \u6587\u4ef6, ' + nchg + ' \u6b21\u6539\u52a8';
            ti.iconPath = new vscode.ThemeIcon('versions');
            ti.contextValue = 'batch';
            return ti;
        }
        if (el.kind === 'file') {
            const f = el.file;
            let delta = 0;
            for (const s of f.items) { const m = s.manifest; if (m.size_before != null && m.size_after != null) delta += (m.size_after - m.size_before); }
            const ti = new vscode.TreeItem(path.basename(f.path), vscode.TreeItemCollapsibleState.Collapsed);
            ti.description = f.items.length + ' \u5904' + (delta ? ('  ' + (delta > 0 ? '+' : '') + delta + 'B') : '');
            ti.tooltip = f.path;
            ti.iconPath = vscode.ThemeIcon.File;
            ti.contextValue = 'snapfile';
            ti.command = { command: 'agentSnap.openBatch', title: 'open batch diff', arguments: [el.batch, f] };
            return ti;
        }
        const snap = el.snap;
        const m = snap.manifest;
        const delta = (m.size_before != null && m.size_after != null) ? (m.size_after - m.size_before) : null;
        const desc = m.time + (m.kind === 'redo' ? ' [\u56de\u9000\u70b9]' : '') + (delta ? ('  ' + (delta > 0 ? '+' : '') + delta + 'B') : '');
        const ti = new vscode.TreeItem(m.time, vscode.TreeItemCollapsibleState.None);
        ti.description = desc;
        ti.tooltip = m.real_path + '\n' + m.time + '\n' + snap.dir;
        ti.contextValue = 'snap';
        ti.command = { command: 'agentSnap.openStep', title: 'open this change', arguments: [snap] };
        ti.iconPath = new vscode.ThemeIcon(m.kind === 'redo' ? 'history' : 'circle-filled');
        return ti;
    }
    getChildren(el) {
        if (!el) return this._batches.map(b => ({ kind: 'batch', batch: b }));
        if (el.kind === 'batch') return el.batch.files.map(f => ({ kind: 'file', file: f, batch: el.batch }));
        if (el.kind === 'file') return el.file.items.map(s => ({ kind: 'snap', snap: s }));
        return [];
    }
    getParent() { return null; }
}

let hist = null;
let statusItem = null;

function refreshAll() {
    const list = listSnapshots();
    if (hist) hist.refresh();
    if (statusItem) {
        statusItem.text = '$(history) \u5feb\u7167 ' + list.filter(i => i.manifest.kind !== 'redo').length;
        const roots = (vscode.workspace.workspaceFolders || []).map(w => w.name).join(', ');
        statusItem.tooltip = 'Agent \u6539\u52a8\u5386\u53f2' +
            (scopeToWorkspace() && roots ? ' \u00b7 \u4ec5 ' + roots : ' \u00b7 \u5168\u90e8\u5de5\u7a0b') +
            '\uff08\u70b9\u51fb\u6253\u5f00\u5386\u53f2\u9762\u677f\uff09';
    }
}

function resolveSnap(arg, items) {
    if (!arg && items && items.length) arg = items[0];
    if (arg && arg.snap) return arg.snap;
    if (arg && arg.manifest) return arg;
    if (arg && arg.resourceUri) return findSnapByUri(arg.resourceUri);
    if (arg instanceof vscode.Uri) return findSnapByUri(arg);
    return null;
}

function activate(ctx) {
    const snapProv = new TextProvider(uri => gbkDecode(fs.readFileSync(pinUri(uri))));
    const realProv = new TextProvider(uri => gbkDecode(fs.readFileSync(pinUri(uri))));
    ctx.subscriptions.push(
        vscode.workspace.registerTextDocumentContentProvider(SCHEME_SNAP, snapProv),
        vscode.workspace.registerTextDocumentContentProvider(SCHEME_REAL, realProv)
    );

    hist = new HistoryProvider();
    ctx.subscriptions.push(vscode.window.registerTreeDataProvider('agentSnapHistory', hist));

    statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 200);
    statusItem.command = 'agentSnap.showPanel';
    ctx.subscriptions.push(statusItem);
    statusItem.show();

    ctx.subscriptions.push(vscode.commands.registerCommand('agentSnap.refresh', refreshAll));
    ctx.subscriptions.push(vscode.commands.registerCommand('agentSnap.showPanel', () => {
        vscode.commands.executeCommand('workbench.view.extension.agentSnap');
    }));
    ctx.subscriptions.push(vscode.commands.registerCommand('agentSnap.openBatch', (batch, file) => {
        if (batch && file) return openBatchFileDiff(batch, file);
        const bs = buildBatches();
        if (bs.length && bs[0].files.length) return openBatchFileDiff(bs[0], bs[0].files[0]);
        vscode.window.showInformationMessage('\u6682\u65e0\u5feb\u7167\u8bb0\u5f55');
    }));
    ctx.subscriptions.push(vscode.commands.registerCommand('agentSnap.openStep', (item, items) => {
        const snap = resolveSnap(item, items);
        if (snap) return openStepDiff(snap);
        const list = listSnapshots();
        if (list.length) return openStepDiff(list[0]);
        vscode.window.showInformationMessage('\u6682\u65e0\u5feb\u7167\u8bb0\u5f55');
    }));
    ctx.subscriptions.push(vscode.commands.registerCommand('agentSnap.openDiff', (item, items) => {
        const snap = resolveSnap(item, items);
        if (snap) return openDiffVsCurrent(snap);
        const list = listSnapshots();
        if (list.length) return openDiffVsCurrent(list[0]);
        vscode.window.showInformationMessage('\u6682\u65e0\u5feb\u7167\u8bb0\u5f55');
    }));
    ctx.subscriptions.push(vscode.commands.registerCommand('agentSnap.rollback', (item, items) => {
        return rollback(resolveSnap(item, items));
    }));
    ctx.subscriptions.push(vscode.commands.registerCommand('agentSnap.rollbackLast', () => {
        const list = listSnapshots();
        if (list.length) return rollback(list[0]);
        vscode.window.showInformationMessage('\u6682\u65e0\u5feb\u7167\u8bb0\u5f55');
    }));

    try { fs.mkdirSync(backupDir(), { recursive: true }); } catch (e) { }

    // fs.watch: on new snapshot, just refresh + RESTART a quiet timer.
    // When the batch goes quiet (no new snapshot for autoQuietSec), show ONE diff for the finished batch.
    let watcher = null;
    let quiet = null;
    let lastAuto = null;
    try { watcher = fs.watch(backupDir(), { persistent: false }); } catch (e) { watcher = null; }
    if (watcher) {
        watcher.on('change', (_ev, fname) => {
            const f = String(fname || '');
            if (!f.includes('manifest') && !/^\d{8}-\d{6}-/.test(f)) return;
            if (!snapEventInWorkspace(f)) return;
            refreshAll();
            const qms = autoQuietMs();
            if (qms <= 0) return;
            clearTimeout(quiet);
            quiet = setTimeout(() => {
                const bs = buildBatches();
                if (!bs.length) return;
                const b = bs[0];
                if (lastAuto === b.endStamp) return;
                lastAuto = b.endStamp;
                if (b.files.length === 1) { openBatchFileDiff(b, b.files[0]); }
                else { vscode.window.showInformationMessage('\u672c\u6279\u6b21\u6d89\u53ca ' + b.files.length + ' \u4e2a\u6587\u4ef6\uff0c\u89c1\u4fa7\u680f'); }
            }, qms);
        });
    }
    ctx.subscriptions.push({ dispose: () => { if (watcher) watcher.close(); } });

    refreshAll();
}

function deactivate() { }

module.exports = { activate, deactivate };
