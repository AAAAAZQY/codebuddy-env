const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

let ctx;

function snapsRoot() {
  const dir = path.join(ctx.globalStorageUri.fsPath, 'snaps');
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function indexFile() {
  return path.join(snapsRoot(), 'index.json');
}

function loadIndex() {
  try {
    return JSON.parse(fs.readFileSync(indexFile(), 'utf8'));
  } catch (e) {
    return {};
  }
}

function saveIndex(index) {
  fs.writeFileSync(indexFile(), JSON.stringify(index, null, 1), 'utf8');
}

function fileKey(uri) {
  return uri.fsPath.toLowerCase();
}

function fmtTime(ts) {
  const d = new Date(ts);
  const p = (n) => String(n).padStart(2, '0');
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

function keepCount() {
  const n = vscode.workspace.getConfiguration('diffSnap').get('keep', 5);
  return n && n > 0 ? n : 5;
}

/** 把磁盘上的当前内容存成一份"改动前"快照 */
function markActive() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('改动对比：没有打开的文件');
    return;
  }
  const doc = editor.document;
  if (doc.uri.scheme !== 'file') {
    vscode.window.showWarningMessage('改动对比：只支持本地文件');
    return;
  }

  const diskPath = doc.uri.fsPath;
  if (!fs.existsSync(diskPath)) {
    vscode.window.showWarningMessage('改动对比：文件还没落盘，先保存一次再打点');
    return;
  }

  const index = loadIndex();
  const key = fileKey(doc.uri);
  const dir = path.join(snapsRoot(), crypto.createHash('md5').update(key).digest('hex').slice(0, 12));
  fs.mkdirSync(dir, { recursive: true });

  const ts = Date.now();
  const snapPath = path.join(dir, `${ts}-${path.basename(diskPath)}`);
  fs.copyFileSync(diskPath, snapPath);

  const entry = index[key] || { fsPath: diskPath, name: path.basename(diskPath), snaps: [] };
  entry.fsPath = diskPath;
  entry.name = path.basename(diskPath);
  entry.snaps.push({ ts, path: snapPath });

  while (entry.snaps.length > keepCount()) {
    const old = entry.snaps.shift();
    try {
      if (fs.existsSync(old.path)) {
        fs.unlinkSync(old.path);
      }
    } catch (e) {
      /* 快照清理失败不影响主流程 */
    }
  }

  index[key] = entry;
  saveIndex(index);
  provider.refresh();
  vscode.window.setStatusBarMessage(`改动对比：已记录 ${entry.name}`, 2500);
}

/** 打开 diff：左=快照（改动前），右=当前文件（改动后），两侧均可编辑 */
async function openDiff(snapPath, targetPath, name) {
  if (!fs.existsSync(snapPath)) {
    vscode.window.showErrorMessage('改动对比：快照文件已不存在');
    return;
  }
  await vscode.commands.executeCommand(
    'vscode.diff',
    vscode.Uri.file(snapPath),
    vscode.Uri.file(targetPath),
    `${name}（改动前 ↔ 改动后）`
  );
}

function compareActive() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('改动对比：没有打开的文件');
    return;
  }
  const index = loadIndex();
  const entry = index[fileKey(editor.document.uri)];
  if (!entry || !entry.snaps.length) {
    vscode.window.showWarningMessage('改动对比：这个文件还没有打点，先执行“打点”');
    return;
  }
  const last = entry.snaps[entry.snaps.length - 1];
  openDiff(last.path, editor.document.uri.fsPath, entry.name);
}

function clearActive() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    return;
  }
  const key = fileKey(editor.document.uri);
  const index = loadIndex();
  const entry = index[key];
  if (!entry) {
    return;
  }
  entry.snaps.forEach((s) => {
    try {
      if (fs.existsSync(s.path)) {
        fs.unlinkSync(s.path);
      }
    } catch (e) {
      /* 忽略单个删除失败 */
    }
  });
  delete index[key];
  saveIndex(index);
  provider.refresh();
}

class SnapProvider {
  constructor() {
    this._emitter = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._emitter.event;
  }

  refresh() {
    this._emitter.fire();
  }

  getTreeItem(el) {
    return el;
  }

  getChildren(el) {
    const index = loadIndex();

    if (!el) {
      const items = [];
      for (const key of Object.keys(index)) {
        const entry = index[key];
        if (!entry.snaps.length) {
          continue;
        }
        const item = new vscode.TreeItem(entry.name, vscode.TreeItemCollapsibleState.Collapsed);
        item.description = `${entry.snaps.length} 个打点`;
        item.iconPath = new vscode.ThemeIcon('file');
        item.tooltip = entry.fsPath;
        item.contextValue = 'diffSnapFile';
        item.id = key;
        item.resourceUri = vscode.Uri.file(entry.fsPath);
        items.push(item);
      }
      items.sort((a, b) => String(a.label).localeCompare(String(b.label)));
      return items;
    }

    const entry = index[el.id];
    if (!entry) {
      return [];
    }
    const snaps = entry.snaps.slice().reverse();
    return snaps.map((s, i) => {
      const item = new vscode.TreeItem(fmtTime(s.ts), vscode.TreeItemCollapsibleState.None);
      item.description = i === 0 ? '最近一次' : '';
      item.iconPath = new vscode.ThemeIcon(i === 0 ? 'diff' : 'history');
      item.tooltip = `点击与当前文件并排对比\n${s.path}`;
      item.command = {
        command: 'diffSnap.openPair',
        title: '对比',
        arguments: [s.path, entry.fsPath, entry.name]
      };
      return item;
    });
  }
}

let provider;

function activate(context) {
  ctx = context;
  provider = new SnapProvider();

  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('diffSnapView', provider),
    vscode.commands.registerCommand('diffSnap.mark', markActive),
    vscode.commands.registerCommand('diffSnap.compare', compareActive),
    vscode.commands.registerCommand('diffSnap.clear', clearActive),
    vscode.commands.registerCommand('diffSnap.openPair', openDiff),
    vscode.commands.registerCommand('diffSnap.refresh', () => provider.refresh())
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
