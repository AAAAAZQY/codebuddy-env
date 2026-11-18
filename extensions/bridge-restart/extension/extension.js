'use strict';

const vscode = require('vscode');
const cp = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const net = require('net');

let statusItem = null;
let output = null;
let pollTimer = null;
let busy = false;
let lastOnline = null;
let lastAction = '尚未执行';
let lastAutoAttempt = 0;
let rootCount = 0;

function cfg() {
    const c = vscode.workspace.getConfiguration('bridgeRestart');
    const home = os.homedir();
    return {
        codeExe: c.get('codeExe') || process.execPath || 'D:\\Vscode\\Microsoft VS Code\\Code.exe',
        bridgeJs: c.get('bridgeJs') || path.join(home, '.codebuddy-bridge', 'bridge-oneway.js'),
        mirrorRoot: c.get('mirrorRoot') || 'D:\\plain_view',
        port: c.get('port') || 37821,
        pollMs: Math.max(3000, c.get('pollIntervalMs') || 15000),
        extraRoots: c.get('extraRoots') || [],
        autoRestart: !!c.get('autoRestart')
    };
}

function log(msg) {
    if (output) {
        output.appendLine('[' + new Date().toLocaleTimeString() + '] ' + msg);
    }
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/* TCP connect is enough to tell whether the bridge is alive; no HTTP route needed. */
function probe(port, timeoutMs) {
    return new Promise((resolve) => {
        const sock = new net.Socket();
        let done = false;
        const finish = (value) => {
            if (done) { return; }
            done = true;
            try { sock.destroy(); } catch (e) { /* ignore */ }
            resolve(value);
        };
        sock.setTimeout(timeoutMs || 600);
        sock.once('connect', () => finish(true));
        sock.once('timeout', () => finish(false));
        sock.once('error', () => finish(false));
        sock.connect(port, '127.0.0.1');
    });
}

/* Collect real roots from bridge-roots.txt plus every .mirror-meta.json under
 * the mirror root (top level and two nested levels), so no project is missed
 * and the bridge never starts with an empty REAL_ROOTS. */
function collectRoots(c) {
    const found = [];
    const push = (p) => {
        if (!p) { return; }
        const abs = path.resolve(p);
        try {
            if (!fs.existsSync(abs)) { return; }
            if (!fs.statSync(abs).isDirectory()) { return; }
        } catch (e) { return; }
        if (found.some((x) => x.toLowerCase() === abs.toLowerCase())) { return; }
        found.push(abs);
    };

    const cfgFile = path.join(path.dirname(c.bridgeJs), 'bridge-roots.txt');
    try {
        if (fs.existsSync(cfgFile)) {
            for (const line of fs.readFileSync(cfgFile, 'utf8').split(/\r?\n/)) {
                const s = line.trim();
                if (s !== '' && !s.startsWith('#')) { push(s); }
            }
        }
    } catch (e) { log('read bridge-roots.txt failed: ' + e.message); }

    const walk = (dir, depth) => {
        if (depth > 2) { return; }
        let ents;
        try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
        const meta = path.join(dir, '.mirror-meta.json');
        if (fs.existsSync(meta)) {
            try {
                const j = JSON.parse(fs.readFileSync(meta, 'utf8'));
                if (j.real) { push(j.real); }
            } catch (e) { log('bad meta: ' + meta + ' ' + e.message); }
        }
        for (const ent of ents) {
            if (ent.isDirectory() && ent.name !== 'node_modules' && !ent.name.startsWith('.')) {
                walk(path.join(dir, ent.name), depth + 1);
            }
        }
    };
    walk(c.mirrorRoot, 0);
    for (const r of c.extraRoots) { push(r); }
    return found;
}

/* Stop only the bridge process: a Code.exe whose command line mentions
 * bridge(.js|-oneway.js). The extension host itself never matches. */
function stopBridge() {
    const script = [
        "$ErrorActionPreference = 'SilentlyContinue'",
        "$k = 0",
        "Get-CimInstance Win32_Process -Filter \"Name='Code.exe'\" | ForEach-Object {",
        "  if ($_.CommandLine -and $_.CommandLine -match 'bridge(?:-oneway)?\\.js') {",
        "    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue",
        "    $k++",
        "  }",
        "}",
        "Write-Output $k"
    ].join('\n');
    return new Promise((resolve) => {
        cp.execFile(
            'powershell.exe',
            ['-NoProfile', '-NonInteractive', '-Command', script],
            { windowsHide: true, timeout: 8000 },
            (err, stdout) => {
                if (err) { log('stop warning: ' + err.message); }
                resolve(String(stdout || '').trim());
            }
        );
    });
}

function startBridge(c, roots) {
    const env = Object.assign({}, process.env, {
        ELECTRON_RUN_AS_NODE: '1',
        BRIDGE_PORT: String(c.port)
    });
    const args = [c.bridgeJs].concat(roots);
    const child = cp.spawn(c.codeExe, args, {
        env: env,
        cwd: path.dirname(c.bridgeJs),
        detached: true,
        stdio: 'ignore',
        windowsHide: true
    });
    child.once('error', (e) => log('spawn error: ' + e.message));
    child.unref();
    return child.pid;
}

function render() {
    if (!statusItem) { return; }
    if (busy) {
        statusItem.text = '$(sync~spin) BRIDGE';
        statusItem.color = new vscode.ThemeColor('statusBarItem.warningForeground');
        statusItem.backgroundColor = undefined;
    } else if (lastOnline === true) {
        statusItem.text = '$(radio-tower) BRIDGE';
        statusItem.color = undefined;
        statusItem.backgroundColor = undefined;
    } else if (lastOnline === false) {
        statusItem.text = '$(debug-disconnect) BRIDGE OFF';
        statusItem.color = new vscode.ThemeColor('statusBarItem.errorForeground');
        statusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    } else {
        statusItem.text = '$(question) BRIDGE';
        statusItem.color = undefined;
        statusItem.backgroundColor = undefined;
    }
    const tip = new vscode.MarkdownString('', true);
    tip.isTrusted = true;
    tip.appendMarkdown('**FileBridge 重启**\n\n');
    tip.appendMarkdown('- 状态：' + (busy ? '重启中…' : (lastOnline === true ? '在线' : (lastOnline === false ? '**断开**' : '未知'))) + '\n\n');
    tip.appendMarkdown('- 端口：`' + cfg().port + '`\n\n');
    tip.appendMarkdown('- 工程根：' + rootCount + ' 个\n\n');
    tip.appendMarkdown('- 上次动作：' + lastAction + '\n\n');
    tip.appendMarkdown('单击按钮 = 立即重启桥；命令面板另有「查看桥状态与日志」。');
    statusItem.tooltip = tip;
}

async function doRestart(notify) {
    if (busy) {
        if (notify) { vscode.window.showInformationMessage('桥正在重启中…'); }
        return false;
    }
    busy = true;
    render();
    const c = cfg();
    let ok = false;
    try {
        if (!fs.existsSync(c.bridgeJs)) { throw new Error('找不到桥脚本：' + c.bridgeJs); }
        if (!fs.existsSync(c.codeExe)) { throw new Error('找不到 Code.exe：' + c.codeExe); }

        const roots = collectRoots(c);
        rootCount = roots.length;
        if (roots.length === 0) {
            throw new Error('没有有效的 real 工程根（检查 bridge-roots.txt 和 .mirror-meta.json）');
        }

        log('=== restart begin ===');
        log('codeExe  = ' + c.codeExe);
        log('bridgeJs = ' + c.bridgeJs);
        log('roots    = ' + roots.length);
        const killed = await stopBridge();
        log('stopped  = ' + (killed || '0') + ' process(es)');

        await sleep(350);
        if (await probe(c.port, 400)) {
            log('port still busy after stop, waiting');
            await sleep(600);
        }

        const pid = startBridge(c, roots);
        log('spawned  = pid ' + pid);

        /* cold start scans every mirror; measured ~11 s for 12 projects */
        for (let i = 0; i < 60; i++) {
            await sleep(500);
            if (await probe(c.port, 500)) { ok = true; break; }
        }
        lastOnline = ok;
        lastAction = ok
            ? '重启成功（停 ' + (killed || '0') + ' 个，起 pid ' + pid + '，' + roots.length + ' 个工程）'
            : '重启后端口 ' + c.port + ' 仍未就绪';
        log(lastAction);
        if (notify) {
            if (ok) {
                vscode.window.showInformationMessage('FileBridge 已重启，端口 ' + c.port + ' 就绪（' + roots.length + ' 个工程）');
            } else {
                vscode.window.showErrorMessage('FileBridge 启动超时，点状态栏「查看桥状态与日志」排查');
            }
        }
    } catch (e) {
        lastOnline = false;
        lastAction = '失败：' + e.message;
        log('ERROR ' + e.message);
        if (notify) { vscode.window.showErrorMessage('重启桥失败：' + e.message); }
    } finally {
        busy = false;
        render();
    }
    return ok;
}

async function poll() {
    if (busy) { return; }
    const c = cfg();
    const alive = await probe(c.port, 700);
    lastOnline = alive;
    render();
    if (!alive && c.autoRestart && (Date.now() - lastAutoAttempt) > 60000) {
        lastAutoAttempt = Date.now();
        log('autoRestart triggered');
        doRestart(false);
    }
}

function showStatus() {
    if (output) { output.show(true); }
    const c = cfg();
    const lines = [
        '端口 ' + c.port + '：' + (lastOnline === true ? '在线' : (lastOnline === false ? '断开' : '未知')),
        '工程根：' + rootCount + ' 个',
        '上次动作：' + lastAction,
        'Code.exe：' + c.codeExe,
        'bridgeJs：' + c.bridgeJs,
        '副本根：' + c.mirrorRoot
    ];
    vscode.window.showInformationMessage('FileBridge：' + lines[0], { detail: lines.join('\n'), modal: false });
}

function activate(context) {
    output = vscode.window.createOutputChannel('FileBridge Restart');
    context.subscriptions.push(output);
    log('extension activated');

    statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 89);
    statusItem.command = 'bridgeRestart.restart';
    statusItem.show();
    context.subscriptions.push(statusItem);

    context.subscriptions.push(
        vscode.commands.registerCommand('bridgeRestart.restart', () => {
            return vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: '正在重启 FileBridge',
                    cancellable: false
                },
                () => doRestart(true)
            );
        }),
        vscode.commands.registerCommand('bridgeRestart.status', showStatus)
    );

    try { rootCount = collectRoots(cfg()).length; } catch (e) { log('collectRoots: ' + e.message); }
    render();
    poll();
    pollTimer = setInterval(poll, cfg().pollMs);
    context.subscriptions.push({ dispose: () => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } } });
}

function deactivate() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

module.exports = { activate, deactivate };
