const vscode = require('vscode');
const fs = require('fs');

let lastText = null;
let timer = null;

function outPath() {
    const cfg = vscode.workspace.getConfiguration('clipfile');
    return cfg.get('filePath') || 'D:\\Codebuddy\\toolbox\\clipboard\\clip.txt';
}

function exportNow() {
    return vscode.env.clipboard.readText().then(function (t) {
        if (t && t.length > 0) {
            try {
                fs.writeFileSync(outPath(), t, 'utf8');
                lastText = t;
                vscode.window.setStatusBarMessage('ClipFile: exported ' + t.length + ' chars', 3000);
            } catch (e) {
                vscode.window.showErrorMessage('ClipFile write failed: ' + e.message);
            }
        }
    }, function () { });
}

function activate(context) {
    context.subscriptions.push(vscode.commands.registerCommand('clipfile.exportNow', exportNow));

    timer = setInterval(function () {
        // only export while a VS Code window has focus, so copies made
        // in other apps are not hijacked by the Ctrl+V hook
        if (!vscode.window.state.focused) { return; }
        vscode.env.clipboard.readText().then(function (t) {
            if (t && t.length > 0 && t !== lastText) {
                try {
                    fs.writeFileSync(outPath(), t, 'utf8');
                    lastText = t;
                } catch (e) { }
            }
        }, function () { });
    }, 800);

    context.subscriptions.push({ dispose: function () { clearInterval(timer); } });
}

function deactivate() { }

module.exports = { activate, deactivate };
