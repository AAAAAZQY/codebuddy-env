// local.codejump 0.0.1 -- jump from a copied CodeBuddy reference to file:line.
// The editor process is DLP-trusted, so openTextDocument returns plaintext.
// Keep this file pure ASCII.
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

function cfg() { return vscode.workspace.getConfiguration('codejump'); }
function extraRoots() { return cfg().get('roots', []) || []; }

// Supported clipboard forms:
//   motor.c L491-L506        (CodeBuddy citation card title)
//   motor.c:491
//   source_code/application/motor.c L491-L506
//   491:506:source_code/application/motor.c
function parseRef(text) {
    const s = String(text || '').trim();
    if(!s) return null;
    let m = /^(\d+):(\d+):(.+)$/.exec(s);
    if(m) return { file: m[3].trim(), line: parseInt(m[1], 10) };
    m = /^(.+?)\s+L(\d+)(?:\s*-\s*L?(\d+))?$/.exec(s);
    if(m) return { file: m[1].trim(), line: parseInt(m[2], 10) };
    m = /^(.+?):(\d+)$/.exec(s);
    if(m) return { file: m[1].trim(), line: parseInt(m[2], 10) };
    return null;
}

function baseName(p) {
    return String(p).replace(/\\/g, '/').split('/').pop();
}

function findFileSync(dir, name, depth) {
    if(depth > 10) return null;
    try {
        for(const it of fs.readdirSync(dir, { withFileTypes: true })) {
            if(it.isFile() && it.name === name) return path.join(dir, it.name);
        }
    } catch(e) {}
    try {
        for(const it of fs.readdirSync(dir, { withFileTypes: true })) {
            if(it.isDirectory() && it.name !== 'node_modules' && it.name !== '.git') {
                const r = findFileSync(path.join(dir, it.name), name, depth + 1);
                if(r) return r;
            }
        }
    } catch(e) {}
    return null;
}

async function resolveFile(ref) {
    const name = baseName(ref.file);
    const roots = [];
    for(const w of (vscode.workspace.workspaceFolders || [])) roots.push(w.uri.fsPath);
    for(const r of extraRoots()) roots.push(r);
    for(const root of roots) {
        const hit = findFileSync(root, name, 0);
        if(hit) return vscode.Uri.file(hit);
    }
    return null;
}

async function jump() {
    let text;
    try { text = await vscode.env.clipboard.readText(); }
    catch(e) { vscode.window.showErrorMessage('CodeJump: clipboard read failed: ' + e.message); return; }

    const ref = parseRef(text);
    if(!ref) {
        vscode.window.showWarningMessage('CodeJump: clipboard is not a reference (expected e.g. motor.c L491-L506).');
        return;
    }

    const uri = await resolveFile(ref);
    if(!uri) {
        vscode.window.showWarningMessage('CodeJump: file not found in roots: ' + ref.file);
        return;
    }

    try {
        const doc = await vscode.workspace.openTextDocument(uri);
        const ed = await vscode.window.showTextDocument(doc, { preview: true });
        const maxLine = Math.max(0, doc.lineCount - 1);
        const line = Math.max(0, Math.min(ref.line - 1, maxLine));
        const pos = new vscode.Position(line, 0);
        ed.selection = new vscode.Selection(pos, pos);
        ed.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
    } catch(e) {
        vscode.window.showErrorMessage('CodeJump: open failed: ' + e.message);
    }
}

function activate(context) {
    context.subscriptions.push(vscode.commands.registerCommand('codejump.jump', jump));
}
function deactivate() {}
module.exports = { activate, deactivate };
