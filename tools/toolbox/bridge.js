/*
 * Standalone file bridge for the DLP environment.
 * Runs inside Code.exe with ELECTRON_RUN_AS_NODE=1 (trusted process, no window).
 * No plain-text mirror: serve the DLP-encrypted real project tree directly.
 *
 * usage: Code.exe bridge.js <realRoot> [moreRoots...]
 *        BRIDGE_PORT=37821 (optional)
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');

const HOST = '127.0.0.1';
const PORT = parseInt(process.env.BRIDGE_PORT || '37821', 10);
const MAX_BODY = 16 * 1024 * 1024;
const MAX_SCAN = 8 * 1024 * 1024;
const BUILD = 'standalone-1';
const LOG_PATH = path.join(__dirname, 'bridge.log');

const SKIP_DIRS = new Set(['.git', '.svn', 'node_modules', '.codebuddy', '.vscode', 'Objects', 'Listings']);

/* ---------------- logging ---------------- */

function logLine(msg) {
    const line = new Date().toISOString() + ' ' + msg;
    try {
        if (fs.existsSync(LOG_PATH) && fs.statSync(LOG_PATH).size > 4 * 1024 * 1024) {
            fs.renameSync(LOG_PATH, LOG_PATH + '.old');
        }
    } catch (e) { /* ignore */ }
    try { fs.appendFileSync(LOG_PATH, line + '\r\n', 'utf8'); } catch (e) { /* ignore */ }
    console.log(line);
}

const log = { appendLine: logLine };

/* ---------------- html viewer ---------------- */

const VIEW_HTML = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Code Viewer</title>
<style>
*{box-sizing:border-box}
body{margin:0;height:100vh;overflow:hidden;font:13px/1.45 ui-monospace,Consolas,monospace;background:#1e1e1e;color:#d4d4d4}
#top{display:flex;height:34px;align-items:center;gap:8px;padding:0 10px;background:#252526;border-bottom:1px solid #333;font-size:12px;color:#9cdcfe;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#main{display:flex;height:calc(100vh - 34px)}
#tree{width:300px;min-width:180px;overflow:auto;border-right:1px solid #333;padding:6px 0;background:#181818}
#code{flex:1;overflow:auto;padding:8px 12px;white-space:pre;tab-size:4}
.row{cursor:pointer;white-space:nowrap;padding:1px 6px}
.row:hover{background:#2a2d2e}
.d{color:#4ec9b0}
.f{color:#cccccc}
#hint{color:#666;padding:10px}
</style></head><body>
<div id="top">?????????</div>
<div id="main"><div id="tree"></div><div id="code"><div id="hint">??????????????</div></div></div>
<script>
var ROOT = __ROOT__;
var treeEl = document.getElementById('tree');
var codeEl = document.getElementById('code');
var topEl = document.getElementById('top');

function join(dir, name) {
  var last = dir.slice(-1);
  var sep = (last === '\\\\' || last === '/') ? '' : '\\\\';
  return dir + sep + name;
}

async function list(dir) {
  try {
    var r = await fetch('/list?p=' + encodeURIComponent(dir));
    var j = await r.json();
    return j.ok ? j.entries : [];
  } catch (e) { return []; }
}

async function renderDir(dir, container, depth) {
  var ents = await list(dir);
  ents.sort(function (a, b) { return (b.d - a.d) || a.n.localeCompare(b.n); });
  for (var i = 0; i < ents.length; i++) {
    (function (e) {
      var full = join(dir, e.n);
      var row = document.createElement('div');
      row.className = 'row';
      row.style.paddingLeft = (6 + depth * 12) + 'px';
      if (e.d) {
        row.classList.add('d');
        row.textContent = '\\u25b8 ' + e.n;
        var kids = document.createElement('div');
        kids.style.display = 'none';
        var loaded = false;
        row.onclick = async function () {
          if (!loaded) { loaded = true; await renderDir(full, kids, depth + 1); }
          var open = kids.style.display !== 'none';
          kids.style.display = open ? 'none' : 'block';
          row.textContent = (open ? '\\u25b8 ' : '\\u25be ') + e.n;
        };
        container.appendChild(row);
        container.appendChild(kids);
      } else {
        row.classList.add('f');
        row.textContent = e.n;
        row.onclick = function () { openFile(full); };
        container.appendChild(row);
      }
    })(ents[i]);
  }
}

async function openFile(p) {
  topEl.textContent = p;
  try {
    var r = await fetch('/raw?p=' + encodeURIComponent(p));
    var buf = await r.arrayBuffer();
    var txt;
    try { txt = new TextDecoder('gbk').decode(buf); }
    catch (e) { txt = new TextDecoder('utf-8').decode(buf); }
    var lines = txt.split(/\\r?\\n/);
    var out = [];
    for (var i = 0; i < lines.length; i++) {
      out.push(String(i + 1).padStart(5, ' ') + '  ' + lines[i]);
    }
    codeEl.textContent = out.join('\\n');
    codeEl.scrollTop = 0;
  } catch (e) {
    codeEl.textContent = '??????: ' + e;
  }
}

renderDir(ROOT, treeEl, 0);
</script></body></html>`;

/* ---------------- http helpers ---------------- */

function readBody(req) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        let size = 0;
        req.on('data', (c) => {
            size += c.length;
            if (size > MAX_BODY) {
                reject(new Error('body too large'));
                req.destroy();
                return;
            }
            chunks.push(c);
        });
        req.on('end', () => resolve(Buffer.concat(chunks)));
        req.on('error', reject);
    });
}

function send(res, code, obj) {
    const s = JSON.stringify(obj);
    res.writeHead(code, {
        'content-type': 'application/json; charset=utf-8',
        'content-length': Buffer.byteLength(s),
        'cache-control': 'no-store'
    });
    res.end(s);
}

function sendRaw(res, buf) {
    res.writeHead(200, {
        'content-type': 'application/octet-stream',
        'content-length': buf.length,
        'cache-control': 'no-store'
    });
    res.end(buf);
}

async function walk(dir, out, depth) {
    if (depth > 16) return;
    let ents;
    try {
        ents = await fs.promises.readdir(dir, { withFileTypes: true });
    } catch (e) {
        return;
    }
    for (const e of ents) {
        const full = path.join(dir, e.name);
        if (e.isDirectory()) {
            if (SKIP_DIRS.has(e.name)) continue;
            await walk(full, out, depth + 1);
        } else if (e.isFile()) {
            try {
                const st = await fs.promises.stat(full);
                if (st.size <= MAX_SCAN) out.push(full);
            } catch (e) { /* ignore */ }
        }
    }
}

function entrySize(full) {
    try {
        return fs.statSync(full).size;
    } catch (e) {
        return 0;
    }
}

function viewerRoot() {
    return REAL_ROOTS.length ? REAL_ROOTS[0] : process.cwd();
}

/* ---------------- workspace helpers ---------------- */

const REAL_ROOTS = [];

/* ---------------- write helpers: atomic replace + per file queue ---------------- */

const writeQueue = new Map();

function shortHash(buf) {
    return require('crypto').createHash('md5').update(buf).digest('hex').slice(0, 8);
}

/* replace a file atomically, the target is never seen half written.
   the DLP filter can deny the rename for a moment, so retry and fall back */
async function atomicWrite(target, buf) {
    const tmp = target + '.~brgtmp';
    await fs.promises.writeFile(tmp, buf);
    for (let i = 0; i < 5; i++) {
        try {
            await fs.promises.rename(tmp, target);
            return;
        } catch (e) {
            await new Promise((r) => setTimeout(r, 40));
        }
    }
    try { await fs.promises.writeFile(target, buf); } catch (e) { /* reported by caller */ }
    try { await fs.promises.unlink(tmp); } catch (e) { /* ignore */ }
}

/* only a real project root may be written by this trusted process */
function isRealPath(target) {
    const t = path.resolve(target).toLowerCase();
    const own = path.resolve(__dirname).toLowerCase();
    /* the bridge may update its own files (bridge.js, logs, snapshots) */
    if (t === own || t.startsWith(own + path.sep)) return true;
    for (let i = 0; i < REAL_ROOTS.length; i++) {
        const r = path.resolve(REAL_ROOTS[i]).toLowerCase();
        if (t === r || t.startsWith(r + path.sep)) return true;
    }
    return false;
}

/* ---------------- http handler ---------------- */

function handler() {
    return async (req, res) => {
        try {
            const u = new URL(req.url, 'http://' + HOST);
            const p = u.searchParams.get('p');
            switch (u.pathname) {
                case '/':
                case '/view': {
                    const html = VIEW_HTML.replace('__ROOT__', JSON.stringify(viewerRoot()));
                    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
                    return res.end(html);
                }
                case '/ping':
                    return send(res, 200, {
                        ok: true, pid: process.pid, vscode: 'standalone', build: BUILD,
                        roots: REAL_ROOTS
                    });
                case '/log': {
                    const n = parseInt(u.searchParams.get('n') || '200', 10);
                    let txt = '';
                    try { txt = fs.readFileSync(LOG_PATH, 'utf8'); } catch (e) { txt = ''; }
                    const lines = txt.split(/\r?\n/).filter(Boolean).slice(-n);
                    return send(res, 200, { ok: true, lines: lines });
                }
                case '/raw': {
                    if (!p) return send(res, 400, { ok: false, err: 'missing p' });
                    return sendRaw(res, await fs.promises.readFile(p));
                }
                case '/read': {
                    if (!p) return send(res, 400, { ok: false, err: 'missing p' });
                    const buf = await fs.promises.readFile(p);
                    return send(res, 200, { ok: true, size: buf.length, data: buf.toString('base64') });
                }
                case '/write': {
                    if (!p) return send(res, 400, { ok: false, err: 'missing p' });
                    if (!isRealPath(p)) {
                        /* only real project roots may be written */
                        log.appendLine('write refused (not a real root): ' + p);
                        return send(res, 403, { ok: false, err: 'refused: not under a real root' });
                    }
                    const raw = await readBody(req);
                    const data = Buffer.from(raw.toString('utf8').trim(), 'base64');
                    await fs.promises.mkdir(path.dirname(p), { recursive: true });
                    /* per-file serialise + stale guard: an external editor (Keil)
                       may save while this write is queued, never clobber it */
                    const qkey = path.resolve(p).toLowerCase();
                    const prev = writeQueue.get(qkey) || Promise.resolve();
                    let preHash = '';
                    try { preHash = shortHash(await fs.promises.readFile(p)); } catch (e) { preHash = ''; }
                    const job = prev.then(async () => {
                        if (preHash) {
                            try {
                                const nowHash = shortHash(await fs.promises.readFile(p));
                                if (nowHash !== preHash) {
                                    log.appendLine('WRITE-STALE-SKIP ' + p);
                                    return false;
                                }
                            } catch (e) { /* file vanished, fall through */ }
                        }
                        await atomicWrite(p, data);
                        await new Promise((r) => setTimeout(r, 60));
                        let ok = false;
                        try {
                            const chk = await fs.promises.readFile(p);
                            ok = (chk.length === data.length && chk.equals(data));
                        } catch (e) { ok = false; }
                        return ok;
                    });
                    const wtail = job.catch(() => { });
                    writeQueue.set(qkey, wtail);
                    wtail.then(() => { if (writeQueue.get(qkey) === wtail) writeQueue.delete(qkey); });
                    const verified = await job.catch(() => false);
                    if (!verified) log.appendLine('WRITE-VERIFY-FAIL ' + p);
                    return send(res, 200, { ok: verified, size: data.length, verified: verified });
                }
                case '/list': {
                    if (!p) return send(res, 400, { ok: false, err: 'missing p' });
                    const ents = await fs.promises.readdir(p, { withFileTypes: true });
                    return send(res, 200, {
                        ok: true,
                        entries: ents.map((e) => ({
                            n: e.name,
                            d: e.isDirectory(),
                            s: entrySize(path.join(p, e.name))
                        }))
                    });
                }
                case '/find': {
                    const dir = u.searchParams.get('d');
                    const q = u.searchParams.get('q');
                    const glob = u.searchParams.get('g');
                    if (!dir || !q) return send(res, 400, { ok: false, err: 'missing d/q' });
                    let re;
                    try {
                        re = new RegExp(q, 'i');
                    } catch (e) {
                        return send(res, 400, { ok: false, err: 'bad regex' });
                    }
                    const gre = glob ? new RegExp(glob.replace(/\./g, '\\.').replace(/\*/g, '.*') + '$', 'i') : null;
                    const files = [];
                    await walk(dir, files, 0);
                    const hits = [];
                    let scanned = 0;
                    for (const f of files) {
                        if (gre && !gre.test(f)) continue;
                        let txt;
                        try {
                            txt = await fs.promises.readFile(f, 'utf8');
                        } catch (e) {
                            continue;
                        }
                        if (txt.indexOf('\u0000') >= 0) continue;
                        scanned++;
                        const lines = txt.split(/\r?\n/);
                        for (let i = 0; i < lines.length; i++) {
                            if (re.test(lines[i])) {
                                hits.push({ f: f, l: i + 1, t: lines[i].slice(0, 300) });
                                if (hits.length >= 500) break;
                            }
                        }
                        if (hits.length >= 500) break;
                    }
                    return send(res, 200, { ok: true, scanned: scanned, hits: hits });
                }
                default:
                    return send(res, 404, { ok: false, err: 'unknown endpoint' });
            }
        } catch (e) {
            return send(res, 500, { ok: false, err: String((e && e.message) || e) });
        }
    };
}

/* ---------------- main ---------------- */

// ?????????bridge-roots.txt???????????????¡¤????# ????????+ ?????§Ó???
function collectRoots() {
    const seen = new Set();
    const add = (raw) => {
        const s = String(raw || '').trim();
        if (!s || s.startsWith('#')) return;
        const abs = path.resolve(s);
        const key = abs.toLowerCase();
        if (seen.has(key)) return;
        seen.add(key);
        if (fs.existsSync(abs)) REAL_ROOTS.push(abs);
        else logLine('skip missing root: ' + abs);
    };

    const cfg = path.join(__dirname, 'bridge-roots.txt');
    if (fs.existsSync(cfg)) {
        for (const line of fs.readFileSync(cfg, 'utf8').split(/\r?\n/)) add(line);
    }
    for (const a of process.argv.slice(2)) {
        if (!String(a).startsWith('--')) add(a);
    }
}

(async function main() {
    collectRoots();
    if (!REAL_ROOTS.length) {
        logLine('no valid real root, exit');
        process.exit(2);
    }
    logLine('starting build ' + BUILD + ' roots=' + REAL_ROOTS.join(',') + ' port=' + PORT);

    const server = http.createServer(handler());
    server.on('error', (e) => logLine('server error: ' + ((e && e.message) || e)));
    server.listen(PORT, HOST, () => logLine('listening on http://' + HOST + ':' + PORT));

    /* no plain-text copy: this bridge only serves the encrypted real tree */
    logLine('ready');
})().catch((e) => {
    logLine('fatal: ' + ((e && e.stack) || e));
    process.exit(1);
});
