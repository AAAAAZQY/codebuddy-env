/*
 * CD11 改动对比
 * 通过与基线仓库（--git-dir 指向 DLP 之外的仓库，--work-tree 指向当前副本）比较，
 * 列出改动文件并用内置 diff 视图打开。
 * 不读基线目录里的文件（那些文件会被 DLP 加密），基线内容一律通过 git show 获取，
 * 以虚拟文档形式交给 diff 视图，因此不受加密影响。不向副本写任何文件。
 */
const vscode = require('vscode');
const path = require('path');
const { execFile } = require('child_process');

const EXCLUDE_DIRS = new Set(['.git', '.vscode', '.codebuddy', 'Objects', 'Listings', 'List', 'DebugConfig', 'output']);
const EXCLUDE_FILES = new Set(['.mirror-meta.json', 'SMLinkM.ini', 'EventRecorderStub.scvd', 'Thumbs.db', 'desktop.ini']);
const EXCLUDE_EXT = new Set(['.o', '.d', '.crf', '.dep', '.lnp', '.map', '.hex', '.bin', '.axf', '.bak', '.uvguix', '.scvd', '.ini', '.iex', '.lst', '.plg', '.uvopt', '.uvproj']);

const SCHEME = 'cd11diff';

function getConfig() {
    const cfg = vscode.workspace.getConfiguration('cd11Diff');
    return {
        gitDir: cfg.get('gitDir'),
        workTree: cfg.get('workTree'),
        baselineRef: cfg.get('baselineRef') || 'HEAD'
    };
}

function gitArgs(extra) {
    const { gitDir, workTree } = getConfig();
    return ['--git-dir=' + gitDir, '--work-tree=' + workTree].concat(extra);
}

function runGit(extra) {
    return new Promise((resolve, reject) => {
        execFile('git', gitArgs(extra), { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 }, (err, stdout, stderr) => {
            if (err) {
                reject(new Error((stderr || err.message || '').trim()));
                return;
            }
            resolve(stdout);
        });
    });
}

function isExcludedPath(rel) {
    const parts = rel.split('/');
    if (parts.some((p) => EXCLUDE_DIRS.has(p))) {
        return true;
    }
    if (EXCLUDE_FILES.has(parts[parts.length - 1])) {
        return true;
    }
    const ext = path.extname(rel).toLowerCase();
    return EXCLUDE_EXT.has(ext);
}

/* 返回 [{rel, status, added, removed}] */
async function scanChanges() {
    const { baselineRef } = getConfig();
    const map = new Map();

    const numstat = await runGit(['diff', '--numstat', baselineRef]);
    for (const line of numstat.split('\n')) {
        if (!line.trim()) {
            continue;
        }
        const m = line.split('\t');
        if (m.length < 3) {
            continue;
        }
        const added = (m[0] === '-') ? 0 : parseInt(m[0], 10);
        const removed = (m[1] === '-') ? 0 : parseInt(m[1], 10);
        const rel = m[2].replace(/\\/g, '/');
        if (isExcludedPath(rel)) {
            continue;
        }
        map.set(rel, { rel, status: 'M', added, removed });
    }

    const others = await runGit(['ls-files', '--others', '--exclude-standard']);
    for (const line of others.split('\n')) {
        const rel = line.trim().replace(/\\/g, '/');
        if (!rel || isExcludedPath(rel)) {
            continue;
        }
        map.set(rel, { rel, status: 'A', added: 0, removed: 0 });
    }

    const list = Array.from(map.values());
    list.sort((a, b) => a.rel.localeCompare(b.rel));
    return list;
}

class BaselineContentProvider {
    provideTextDocumentContent(uri) {
        const rel = decodeURIComponent(uri.path.replace(/^\//, ''));
        const { baselineRef } = getConfig();
        return runGit(['show', baselineRef + ':' + rel]).catch((e) => '/* 无法读取基线内容: ' + e.message + ' */');
    }
}

class ChangeTreeProvider {
    constructor() {
        this.items = [];
        this.error = null;
        this.emitter = new vscode.EventEmitter();
        this.onDidChangeTreeData = this.emitter.event;
    }

    async refresh() {
        try {
            this.items = await scanChanges();
            this.error = null;
        } catch (e) {
            this.items = [];
            this.error = e.message;
        }
        this.emitter.fire();
        updateStatusBar(this.items.length, this.error);
    }

    getTreeItem(item) {
        if (item.rel === undefined) {
            return item;
        }
        const treeItem = new vscode.TreeItem(path.basename(item.rel), vscode.TreeItemCollapsibleState.None);
        const sign = (item.status === 'A') ? '(新增)' : `+${item.added} -${item.removed}`;
        treeItem.description = `${item.status} ${sign}`;
        treeItem.tooltip = item.rel;
        treeItem.command = { command: 'cd11Diff.openDiff', title: '打开差异', arguments: [item] };
        treeItem.iconPath = new vscode.ThemeIcon(item.status === 'A' ? 'diff-added' : 'diff-modified');
        return treeItem;
    }

    getChildren(element) {
        if (element) {
            return [];
        }
        if (this.items.length === 0) {
            const empty = new vscode.TreeItem(this.error ? ('读取失败: ' + this.error) : '没有改动（与最初版一致）', vscode.TreeItemCollapsibleState.None);
            empty.iconPath = new vscode.ThemeIcon(this.error ? 'error' : 'check');
            return [empty];
        }
        return this.items;
    }
}

let statusItem = null;

function updateStatusBar(count, error) {
    if (!statusItem) {
        return;
    }
    if (error) {
        statusItem.text = '$(error) CD11 改动 ?';
        statusItem.tooltip = error;
    } else {
        statusItem.text = `$(diff) CD11 改动 ${count}`;
        statusItem.tooltip = '点击刷新改动列表';
    }
    statusItem.show();
}

async function openDiff(item) {
    if (!item || !item.rel) {
        return;
    }
    const { workTree } = getConfig();
    const left = vscode.Uri.from({ scheme: SCHEME, path: '/' + encodeURIComponent(item.rel) });
    if (item.status === 'A') {
        const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(path.join(workTree, item.rel)));
        await vscode.window.showTextDocument(doc);
        vscode.window.setStatusBarMessage(`CD11: ${item.rel} 是新增文件（基线中不存在）`, 3000);
        return;
    }
    const right = vscode.Uri.file(path.join(workTree, item.rel));
    await vscode.commands.executeCommand('vscode.diff', left, right, `${item.rel}  (基线 ? 当前)`);
}

function activate(context) {
    const provider = new ChangeTreeProvider();
    const view = vscode.window.createTreeView('cd11Diff.files', { treeDataProvider: provider });
    statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusItem.command = 'cd11Diff.refresh';

    context.subscriptions.push(
        view,
        statusItem,
        vscode.workspace.registerTextDocumentContentProvider(SCHEME, new BaselineContentProvider()),
        vscode.commands.registerCommand('cd11Diff.refresh', () => provider.refresh()),
        vscode.commands.registerCommand('cd11Diff.openDiff', (item) => openDiff(item)),
        vscode.workspace.onDidSaveTextDocument(() => provider.refresh()),
        vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration('cd11Diff')) {
                provider.refresh();
            }
        })
    );

    provider.refresh();
    const timer = setInterval(() => provider.refresh(), 60000);
    context.subscriptions.push({ dispose: () => clearInterval(timer) });
}

function deactivate() { }

module.exports = { activate, deactivate };
