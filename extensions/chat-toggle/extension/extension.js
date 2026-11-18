const vscode = require('vscode');

const COMMANDS = {
  auxiliary: 'workbench.action.toggleAuxiliaryBar',
  primary: 'workbench.action.toggleSidebarVisibility'
};

function currentTarget() {
  const t = vscode.workspace.getConfiguration('chatToggle').get('target', 'auxiliary');
  return (t === 'both' || COMMANDS[t]) ? t : 'auxiliary';
}

async function toggle() {
  const target = currentTarget();
  if (target === 'both') {
    await vscode.commands.executeCommand(COMMANDS.primary);
    await vscode.commands.executeCommand(COMMANDS.auxiliary);
    return;
  }
  await vscode.commands.executeCommand(COMMANDS[target] || COMMANDS.auxiliary);
}

class ToggleProvider {
  constructor() {
    this._emitter = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._emitter.event;
  }

  refresh() {
    this._emitter.fire();
  }

  getTreeItem(element) {
    return element;
  }

  getChildren() {
    const target = currentTarget();
    const label = target === 'both' ? '两栏一起切换' : (target === 'primary' ? '主侧边栏' : '辅助侧边栏（对话）');

    const main = new vscode.TreeItem('切换对话面板', vscode.TreeItemCollapsibleState.None);
    main.iconPath = new vscode.ThemeIcon('comment-discussion');
    main.description = label;
    main.tooltip = '点击显示/隐藏对话面板。若点错栏，改设置 chatToggle.target 为 auxiliary / primary / both';
    main.command = { command: 'chatToggle.toggle', title: '切换对话面板' };

    const hint = new vscode.TreeItem('当前目标：' + label, vscode.TreeItemCollapsibleState.None);
    hint.iconPath = new vscode.ThemeIcon('gear');
    hint.tooltip = '修改 chatToggle.target 可切换目标栏';
    hint.command = {
      command: 'workbench.action.openSettings',
      title: '打开设置',
      arguments: ['chatToggle.target']
    };

    return [main, hint];
  }
}

function activate(context) {
  context.subscriptions.push(vscode.commands.registerCommand('chatToggle.toggle', toggle));

  const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 90);
  statusItem.text = '$(comment-discussion) 对话';
  statusItem.tooltip = '显示/隐藏对话面板（对话开关）';
  statusItem.command = 'chatToggle.toggle';
  statusItem.show();
  context.subscriptions.push(statusItem);

  const provider = new ToggleProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('chatToggleView', provider),
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration('chatToggle.target')) {
        provider.refresh();
      }
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
