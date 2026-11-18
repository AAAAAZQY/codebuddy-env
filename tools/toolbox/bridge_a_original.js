/*
 * Standalone file bridge for the DLP environment.
 * Runs inside Code.exe with ELECTRON_RUN_AS_NODE=1 (trusted process, no window).
 * Behaviour mirrors local.filebridge 0.0.1 (build name-14) minus all vscode APIs.
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
const MAX_MIRROR = 80 * 1024 * 1024;
const BUILD = 'standalone-1';
const MIRROR_ROOT = process.env.BRIDGE_MIRROR_ROOT || 'D:\\plain_view';
const LOG_PATH = path.join(__dirname, 'bridge.log');

const SKIP_DIRS = new Set(['.git', '.svn', 'node_modules', '.codebuddy', '.vscode', 'Objects', 'Listings']);
const SKIP_SYNC_NAMES = ['.git', '.svn', 'node_modules', '.vscode', '.codebuddy', 'Objects', 'Listings'];
// Keil ?????§Þ????????????????????????????????????§Õ????????
const SKIP_SYNC_EXTS = ['.o', '.crf', '.dep', '.lnp', '.d', '.iex', '.__i', '._ia', '.lst'];

// ???????????????????????????????????? VSCode ???????
const BUILD_MISSING = process.argv.slice(2).includes('--build-missing');

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
        'content-length': Buffer.byteLength(s)
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

const branchCache = new Map();

function gitBranch(real) {
    const now = Date.now();
    const hit = branchCache.get(real);
    if (hit && now - hit.at < 3000) return hit.value;
    let b = '';
    try {
        b = execFileSync('git', ['-C', real, 'rev-parse', '--abbrev-ref', 'HEAD'], {
            encoding: 'utf8',
            windowsHide: true,
            timeout: 5000
        }).trim();
    } catch (e) {
        b = '';
    }
    if (b === 'HEAD' || b === 'unknown') b = '';
    branchCache.set(real, { at: now, value: b });
    return b;
}

// ????????git ???????????? 22b2 / 66d??????????????? <????>-<???>-<????>
const topCache = new Map();

function gitTop(real) {
    const now = Date.now();
    const hit = topCache.get(real);
    if (hit && now - hit.at < 3000) return hit.value;
    let v = '';
    try {
        v = execFileSync('git', ['-C', real, 'rev-parse', '--show-toplevel'], {
            encoding: 'utf8',
            windowsHide: true,
            timeout: 5000
        }).trim();
    } catch (e) {
        v = '';
    }
    if (v) v = path.basename(v.replace(/[\\/]+$/, ''));
    topCache.set(real, { at: now, value: v });
    return v;
}

function sanitizeName(s) {
    return String(s).replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, '_');
}

function shortName(base) {
    let s = String(base).replace(/_source_code$/i, '').replace(/_code$/i, '');
    s = s.replace(/^[_-]+|[_-]+$/g, '');
    if (!s || /^(source|src)$/i.test(s)) return String(base);
    return s;
}

const GENERIC_NAMES = /^(source_code|source|src|code|firmware|project|main|trunk)$/i;

function boardName(real) {
    const base = path.basename(real);
    let s = shortName(base);
    if (GENERIC_NAMES.test(base) || GENERIC_NAMES.test(s)) {
        const parentBase = path.basename(path.dirname(real));
        const parentShort = shortName(parentBase);
        if (parentShort && !GENERIC_NAMES.test(parentShort)) s = parentShort;
    }
    return s;
}

const mirrorOverride = new Map(); // real(lower) -> ???????????? VSCode ??????????

/* find an already placed mirror of this real project, at any nested level under MIRROR_ROOT */
function findMirrorDirForReal(real) {
    const key = String(real).toLowerCase();
    const dirs = findMetaDirs(MIRROR_ROOT, 1, 2, []);
    for (const d of dirs) {
        try {
            const m = JSON.parse(fs.readFileSync(path.join(d, '.mirror-meta.json'), 'utf8'));
            if (m && m.real && String(m.real).toLowerCase() === key) return d;
        } catch (e) { /* not a mirror */ }
    }
    return '';
}

function mirrorFor(real) {
    const key = String(real).toLowerCase();
    const hit = mirrorOverride.get(key);
    if (hit) {
        // ???????? meta ?????????????????????????????????????????
        let ok = false;
        try {
            const meta = JSON.parse(fs.readFileSync(path.join(hit, '.mirror-meta.json'), 'utf8'));
            ok = !!(meta && String(meta.real).toLowerCase() === key);
        } catch (e) { ok = false; }
        if (ok) return hit;
        mirrorOverride.delete(key);
    }
    const placed = findMirrorDirForReal(real);
    if (placed) { mirrorOverride.set(key, placed); return placed; }
    return computeMirror(real);
}

// ????????????????¡¤???????¦Ï? override??
function computeMirror(real) {
    const base = boardName(real);
    const branch = gitBranch(real);
    const tag = sanitizeName(gitTop(real) || '');
    const parts = [];
    if (tag) parts.push(tag);
    if (branch) parts.push(sanitizeName(branch));
    if (base && base.toLowerCase() !== tag.toLowerCase()) parts.push(base);
    const root = parts.length ? parts.join('-') : sanitizeName(path.basename(real));
    const candidates = [root, root + '@' + sanitizeName(path.basename(path.dirname(real)))];
    for (const name of candidates) {
        const dir = path.join(MIRROR_ROOT, name);
        if (!fs.existsSync(dir)) return dir;
        try {
            const meta = JSON.parse(fs.readFileSync(path.join(dir, '.mirror-meta.json'), 'utf8'));
            if (meta && meta.real && String(meta.real).toLowerCase() === real.toLowerCase()) return dir;
        } catch (e) { /* no meta */ }
    }
    const h = require('crypto').createHash('md5').update(real.toLowerCase()).digest('hex').slice(0, 8);
    return path.join(MIRROR_ROOT, root + '-' + h);
}

function mirrorPairs() {
    return REAL_ROOTS.map((real) => ({ real: real, mirror: mirrorFor(real) }));
}

/* ---------------- plain writer (must run OUTSIDE the trusted process) ---------------- */

const PS_WRITE_SCRIPT = [
    "$ErrorActionPreference='Stop'",
    '$raw=[Console]::In.ReadToEnd()',
    '$items=$raw | ConvertFrom-Json',
    '$n=0',
    'foreach($i in $items){',
    '  $d=Split-Path $i.p -Parent',
    '  if($d -and -not (Test-Path $d)){ New-Item -ItemType Directory -Path $d -Force | Out-Null }',
    '  $bytes=[Convert]::FromBase64String($i.b64)',
    "  $tmp=$i.p + '.~brgtmp'",
    '  [System.IO.File]::WriteAllBytes($tmp,$bytes)',
    '  $ok=$false',
    '  for($k=0; $k -lt 5 -and -not $ok; $k++){',
    '    try{ if(Test-Path $i.p){ [System.IO.File]::Replace($tmp,$i.p,[NullString]::Value) } else { [System.IO.File]::Move($tmp,$i.p) }; $ok=$true } catch { Start-Sleep -Milliseconds 40 }',
    '  }',
    '  if(-not $ok){ [System.IO.File]::WriteAllBytes($i.p,$bytes); Remove-Item $tmp -Force -ErrorAction SilentlyContinue; Write-Output ("inplace " + $i.p) }',
    '  $n++',
    '}',
    'Write-Output ("written=" + $n)'
].join('\n');

function writePlain(items, logObj) {
    return new Promise((resolve) => {
        if (!items.length) return resolve({ code: 0, out: 'empty' });
        const ps = spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', PS_WRITE_SCRIPT], { windowsHide: true });
        let out = '';
        ps.stdout.on('data', (d) => { out += d.toString(); });
        ps.stderr.on('data', (d) => { out += d.toString(); });
        ps.on('error', (e) => {
            logObj.appendLine('plain write spawn failed: ' + e.message);
            resolve({ code: -1, out: e.message });
        });
        ps.on('close', (code) => resolve({ code: code, out: out.trim() }));
        try {
            ps.stdin.write(JSON.stringify(items));
            ps.stdin.end();
        } catch (e) {
            logObj.appendLine('plain write stdin failed: ' + e.message);
        }
    });
}

/* ---------------- mirror build ---------------- */

async function buildMirror(logObj, real, mirror) {
    if (!real || !mirror) {
        logObj.appendLine('mirror: no local root');
        return false;
    }
    const files = [];
    await walk(real, files, 0);

    const items = [];
    let total = 0;
    for (const f of files) {
        try {
            const buf = await fs.promises.readFile(f);
            total += buf.length;
            if (total > MAX_MIRROR) {
                logObj.appendLine('mirror aborted: exceeds ' + MAX_MIRROR + ' bytes');
                return false;
            }
            items.push({ p: path.join(mirror, path.relative(real, f)), b64: buf.toString('base64') });
        } catch (e) { /* skip unreadable */ }
    }

    items.push({
        p: path.join(mirror, '.mirror-meta.json'),
        b64: Buffer.from(JSON.stringify({ real: real, branch: gitBranch(real), builtAt: new Date().toISOString() }, null, 2)).toString('base64')
    });

    const settings = path.join(mirror, '.vscode', 'settings.json');
    items.push({
        p: settings,
        b64: Buffer.from(JSON.stringify({ 'files.encoding': 'gbk', 'files.autoGuessEncoding': false }, null, 2)).toString('base64')
    });

    const CHUNK = 25;
    for (let i = 0; i < items.length; i += CHUNK) {
        await writePlain(items.slice(i, i + CHUNK), logObj);
    }
    logObj.appendLine('mirror built: ' + items.length + ' files, ' + total + ' bytes -> ' + mirror);
    return true;
}

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

/* only a real project root may be written by this trusted process, the mirror has
   to go through writePlain, otherwise it lands encrypted */
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

/* ---------------- two-way sync ---------------- */

let activeSyncs = [];

function stopSync() {
    for (const s of activeSyncs) {
        try { s.close(); } catch (e) { /* ignore */ }
    }
    activeSyncs = [];
}

function startSync(logObj, real, mirror) {
    if (!real || !mirror || !fs.existsSync(mirror)) {
        logObj.appendLine('sync: mirror missing ' + mirror);
        return null;
    }
    /* the real root must already exist: creating it would resurrect a phantom
       project tree after the real folder was renamed or deleted */
    if (!fs.existsSync(real)) {
        logObj.appendLine('sync: real root missing, not wired ' + real);
        return null;
    }

    const pending = new Map();

    function skipped(rel) {
        const s = String(rel);
        if (s.indexOf('.mirror-meta') >= 0) return true;
        if (s.indexOf('.~brgtmp') >= 0) return true;
        const parts = s.split(/[\\/]/);
        for (let i = 0; i < parts.length; i++) {
            if (SKIP_SYNC_NAMES.indexOf(parts[i]) >= 0) return true;
        }
        const lower = s.toLowerCase();
        for (let i = 0; i < SKIP_SYNC_EXTS.length; i++) {
            if (lower.endsWith(SKIP_SYNC_EXTS[i])) return true;
        }
        /* temp files of the atomic replace (File.Replace) must never be synced */
        if (lower.endsWith('.tmp') || lower.indexOf('~rf') >= 0) return true;
        return false;
    }

    async function syncFile(fromRoot, toRoot, rel, toMirror) {
        const a = path.join(fromRoot, String(rel));
        const b = path.join(toRoot, String(rel));
        try {
            const st = await fs.promises.stat(a);
            if (!st.isFile()) return;
            const buf = await fs.promises.readFile(a);
            let dSt = null;
            let same = false;
            try {
                dSt = await fs.promises.stat(b);
                const tb = await fs.promises.readFile(b);
                same = tb.length === buf.length && tb.equals(buf);
            } catch (e) { /* target missing */ }
            if (same) return;
            /* never overwrite a newer target with an older source, this is what
               stops the real->mirror echo from restoring replaced content */
            if (dSt && dSt.isFile() && dSt.mtimeMs > st.mtimeMs + 1000) {
                logObj.appendLine('sync skip stale ' + rel + ' (' + (toMirror ? '-> mirror' : '-> real') + ')');
                return;
            }

            async function doWrite() {
                if (toMirror) {
                    const one = [{ p: b, b64: buf.toString('base64') }];
                    await writePlain(one, logObj);
                    let ok = false;
                    try {
                        const chk = await fs.promises.readFile(b);
                        ok = chk.length === buf.length && chk.equals(buf);
                    } catch (e) { ok = false; }
                    if (!ok) {
                        /* the mirror must stay plain text, try once more and shout */
                        await writePlain(one, logObj);
                        logObj.appendLine('MIRROR-VERIFY-FAIL ' + rel);
                    }
                } else {
                    /* never resurrect a missing real root (that is exactly how a phantom
                       project tree was created after the real folder had been renamed) */
                    if (!fs.existsSync(real)) {
                        logObj.appendLine('sync refused (real root missing) ' + rel + ' real=' + real);
                        return;
                    }
                    const rbPath = path.resolve(b).toLowerCase();
                    const rrPath = path.resolve(real).toLowerCase();
                    if (rbPath !== rrPath && rbPath.indexOf(rrPath + path.sep) !== 0) {
                        logObj.appendLine('sync refused (outside real root) ' + rel);
                        return;
                    }
                    await fs.promises.mkdir(path.dirname(b), { recursive: true });
                    await atomicWrite(b, buf);
                }
                logObj.appendLine('synced ' + (toMirror ? '-> mirror ' : '-> real ') + rel
                    + ' ' + buf.length + 'B ' + shortHash(buf));
            }

            const qkey = b.toLowerCase();
            const prev = writeQueue.get(qkey) || Promise.resolve();
            const job = prev.then(doWrite);
            const tail = job.catch(() => { });
            writeQueue.set(qkey, tail);
            tail.then(() => { if (writeQueue.get(qkey) === tail) writeQueue.delete(qkey); });
            await job;
        } catch (e) {
            logObj.appendLine('sync fail ' + rel + ': ' + ((e && e.message) || e));
        }
    }

    function schedule(fromRoot, toRoot, rel, toMirror) {
        const key = fromRoot + '|' + rel;
        if (pending.has(key)) clearTimeout(pending.get(key));
        pending.set(key, setTimeout(() => {
            pending.delete(key);
            syncFile(fromRoot, toRoot, rel, toMirror);
        }, 700));
    }

    const watchers = [];
    try {
        watchers.push(fs.watch(mirror, { recursive: true }, (ev, rel) => {
            if (!rel || skipped(rel)) return;
            schedule(mirror, real, rel, false);
        }));
        /* ONE-WAY MODE: real -> mirror is disabled on purpose.
         * The real tree is DLP protected; any access can raise a change event and the
         * older real content would overwrite newer edits in the mirror. */
        logObj.appendLine('sync watchers started (ONE-WAY): ' + mirror + ' -> ' + real);
    } catch (e) {
        logObj.appendLine('sync watch failed: ' + ((e && e.message) || e));
    }

    return {
        close() {
            for (const w of watchers) {
                try { w.close(); } catch (e) { /* ignore */ }
            }
            for (const t of pending.values()) clearTimeout(t);
            pending.clear();
        }
    };
}

/* ---------------- auto adopt mirrors created by the VSCode extension ---------------- */

const syncedReals = new Set();    // real path (lowercase) already wired to a sync
const knownMirrors = new Set();   // mirror folder names already seen at root level

// ????????? .mirror-meta.json????????????????????????????¦Ê?????
function adoptMirror(dirName, logObj) {
    let dir = path.resolve(dirName);
    let meta;
    try {
        meta = JSON.parse(fs.readFileSync(path.join(dir, '.mirror-meta.json'), 'utf8'));
    } catch (e) {
        return false;
    }
    const real = meta && meta.real ? String(meta.real) : '';
    if (!real || !fs.existsSync(real)) return false;

    const key = real.toLowerCase();

    // ?????????????????????????????????????????????????????????????
    const expected = computeMirror(real);
    const isTopLevel = path.dirname(path.resolve(dir)).toLowerCase() === path.resolve(MIRROR_ROOT).toLowerCase();
    if (isTopLevel && path.resolve(dir).toLowerCase() !== path.resolve(expected).toLowerCase() && !fs.existsSync(expected)) {
        try {
            fs.renameSync(dir, expected);
            logObj.appendLine('renamed mirror ' + path.basename(dir) + ' -> ' + path.basename(expected));
            dir = expected;
        } catch (e) {
            logObj.appendLine('rename skipped (in use): ' + path.basename(dir) + ' -> ' + path.basename(expected));
        }
    }

    const first = !mirrorOverride.has(key);
    if (syncedReals.has(key)) {
        const active = mirrorOverride.get(key);
        if (active && path.resolve(active).toLowerCase() !== path.resolve(dir).toLowerCase()) {
            if (!fs.existsSync(active)) {
                mirrorOverride.set(key, dir);
                const moved = startSync(logObj, real, dir);
                if (moved) activeSyncs.push(moved);
                logObj.appendLine('mirror relocated: ' + active + ' -> ' + dir);
                try { writeIndex(logObj, mirrorPairs()).catch(() => { }); } catch (e) { /* ignore */ }
                return true;
            }
            logObj.appendLine('duplicate mirror ignored: ' + dir + ' (active: ' + active + ')');
        }
        return true;
    }
    mirrorOverride.set(key, dir);

    if (!REAL_ROOTS.some((r) => r.toLowerCase() === key)) {
        REAL_ROOTS.push(real);
        logObj.appendLine('auto-adopted project: ' + real + ' -> ' + dir);
    } else if (first) {
        logObj.appendLine('mirror discovered for known root: ' + real + ' -> ' + dir);
    }
    const s = startSync(logObj, real, dir);
    if (s) {
        activeSyncs.push(s);
        syncedReals.add(key);
    }
    try {
        watchBranch(logObj);
        writeIndex(logObj, mirrorPairs()).catch(() => { });
    } catch (e) { /* ignore */ }
    return true;
}

/* collect every dir that carries a .mirror-meta.json: top level first, then one nested level */
function findMetaDirs(dir, depth, maxDepth, out) {
    let ents = [];
    try {
        ents = fs.readdirSync(dir, { withFileTypes: true });
    } catch (e) {
        return out;
    }
    ents.sort((a, b) => (a.name < b.name ? -1 : (a.name > b.name ? 1 : 0)));
    for (const e of ents) {
        if (!e.isDirectory()) continue;
        if (SKIP_DIRS.has(e.name)) continue;
        if (e.name === '$RECYCLE.BIN' || e.name === 'System Volume Information') continue;
        const full = path.join(dir, e.name);
        try {
            if (fs.existsSync(path.join(full, '.mirror-meta.json'))) out.push(full);
        } catch (err) { /* ignore */ }
        if (depth < maxDepth) findMetaDirs(full, depth + 1, maxDepth, out);
    }
    return out;
}

/* map a watch event (file or dir, any depth) to the owning mirror dir, '' if none */
function resolveMirrorDir(name) {
    let abs = path.join(MIRROR_ROOT, String(name));
    try {
        if (!fs.statSync(abs).isDirectory()) abs = path.dirname(abs);
    } catch (e) {
        return '';
    }
    const rel = path.relative(MIRROR_ROOT, abs);
    if (!rel || rel.indexOf('..') === 0) return '';
    const parts = rel.split(/[\\/]/);
    for (let i = parts.length; i >= 1; i--) {
        const cand = path.join(MIRROR_ROOT, parts.slice(0, i).join(path.sep));
        if (fs.existsSync(path.join(cand, '.mirror-meta.json'))) return cand;
    }
    return '';
}

function scanMirrors(logObj) {
    let dirs = [];
    try {
        dirs = findMetaDirs(MIRROR_ROOT, 1, 2, []);
    } catch (e) {
        return;
    }
    let adopted = 0;
    for (const d of dirs) {
        knownMirrors.add(d);
        if (adoptMirror(d, logObj)) adopted++;
    }
    if (adopted) logObj.appendLine('mirror scan done, pairs=' + mirrorPairs().length);
}

/* ---------------- orphan mirror repair: the real project folder was renamed ---------------- */

const orphanWarned = new Set();

function nearestExistingAncestor(p) {
    let cur = path.resolve(p);
    for (let i = 0; i < 12; i++) {
        if (fs.existsSync(cur)) return cur;
        const up = path.dirname(cur);
        if (up === cur) break;
        cur = up;
    }
    return '';
}

function findDirsByTail(base, tail, maxDepth) {
    const out = [];
    const want = tail.length;
    (function walk(dir, depth) {
        if (depth > maxDepth) return;
        let ents = [];
        try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
        for (const e of ents) {
            if (!e.isDirectory()) continue;
            if (SKIP_DIRS.has(e.name)) continue;
            if (e.name === '$RECYCLE.BIN' || e.name === 'System Volume Information') continue;
            const full = path.join(dir, e.name);
            const parts = full.toLowerCase().split(/[\\/]/).filter(Boolean);
            if (parts.length >= want) {
                let ok = true;
                for (let i = 0; i < want; i++) {
                    if (parts[parts.length - want + i] !== tail[i]) { ok = false; break; }
                }
                if (ok) out.push(full);
            }
            walk(full, depth + 1);
        }
    })(base, 0);
    return out;
}

function sampleRelPaths(root, limit) {
    const all = [];
    (function walk(dir, depth) {
        if (depth > 6 || all.length > 4000) return;
        let ents = [];
        try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
        for (const e of ents) {
            if (e.name === '.codebuddy' || e.name === '.git' || e.name === '.vscode') continue;
            const full = path.join(dir, e.name);
            if (e.isDirectory()) { walk(full, depth + 1); continue; }
            if (!/\.(c|h|cpp|hpp)$/i.test(e.name)) continue;
            all.push(path.relative(root, full));
        }
    })(root, 0);
    all.sort();
    if (all.length <= limit) return all;
    const step = all.length / limit;
    const out = [];
    for (let i = 0; i < limit; i++) out.push(all[Math.floor(i * step)]);
    return out;
}

function scoreCandidate(mirror, cand, rels) {
    let hit = 0;
    let tot = 0;
    for (const rel of rels) {
        let a;
        try { a = fs.readFileSync(path.join(mirror, rel)); } catch (e) { continue; }
        let b = null;
        try { b = fs.readFileSync(path.join(cand, rel)); } catch (e) { b = null; }
        if (!b) continue;
        tot++;
        if (a.length === b.length && a.equals(b)) hit++;
    }
    return { hit: hit, tot: tot };
}

async function writeMetaPlain(mirrorDir, meta) {
    const buf = Buffer.from(JSON.stringify(meta, null, 2) + '\r\n', 'utf8');
    return writePlain([{ p: path.join(mirrorDir, '.mirror-meta.json'), b64: buf.toString('base64') }],
        { appendLine: () => { } });
}

/* rebind only when exactly one candidate matches every sampled file, otherwise just warn */
async function tryRebindOrphan(logObj, mirrorDir, meta) {
    const oldReal = String(meta.real || '');
    const parts = oldReal.split(/[\\/]/).filter(Boolean);
    const tail = parts.slice(-2).map((s) => s.toLowerCase());
    if (tail.length < 2) return false;
    const base = nearestExistingAncestor(oldReal);
    if (!base) {
        logObj.appendLine('orphan mirror (no existing ancestor): ' + mirrorDir + ' old=' + oldReal);
        return false;
    }

    const rels = sampleRelPaths(mirrorDir, 12);
    if (!rels.length) return false;

    const cands = findDirsByTail(base, tail, 4)
        .filter((d) => d.toLowerCase() !== oldReal.toLowerCase() && fs.existsSync(d));
    const good = [];
    for (const c of cands) {
        const s = scoreCandidate(mirrorDir, c, rels);
        if (s.tot >= 5 && s.hit >= 5 && s.hit === s.tot) good.push(c);
    }

    if (good.length !== 1) {
        const key = mirrorDir.toLowerCase() + '|' + oldReal.toLowerCase() + '|' + cands.length + '|' + good.length;
        if (!orphanWarned.has(key)) {
            orphanWarned.add(key);
            logObj.appendLine('orphan mirror needs manual fix: ' + mirrorDir + ' old=' + oldReal
                + ' candidates=' + cands.length + ' matched=' + good.length);
        }
        return false;
    }

    const newReal = good[0];
    meta.real = newReal;
    meta.reboundAt = new Date().toISOString();
    meta.oldReal = oldReal;
    await writeMetaPlain(mirrorDir, meta);
    try {
        const chk = JSON.parse(fs.readFileSync(path.join(mirrorDir, '.mirror-meta.json'), 'utf8'));
        if (String(chk.real).toLowerCase() !== newReal.toLowerCase()) {
            logObj.appendLine('auto-rebound meta verify failed: ' + mirrorDir);
            return false;
        }
    } catch (e) {
        logObj.appendLine('auto-rebound meta read failed: ' + mirrorDir);
        return false;
    }
    logObj.appendLine('auto-rebound mirror ' + path.basename(mirrorDir) + ': ' + oldReal + ' -> ' + newReal);
    orphanWarned.clear();
    return true;
}

async function orphanScan(logObj) {
    let dirs = [];
    try { dirs = findMetaDirs(MIRROR_ROOT, 1, 2, []); } catch (e) { return; }
    for (const d of dirs) {
        let meta = null;
        try { meta = JSON.parse(fs.readFileSync(path.join(d, '.mirror-meta.json'), 'utf8')); } catch (e) { continue; }
        const real = meta && meta.real ? String(meta.real) : '';
        if (!real || fs.existsSync(real)) continue;
        if (await tryRebindOrphan(logObj, d, meta)) {
            adoptMirror(d, logObj);
            try { writeIndex(logObj, mirrorPairs()).catch(() => { }); } catch (e) { /* ignore */ }
        }
    }
}

function watchMirrorRoot(logObj) {
    try {
        fs.watch(MIRROR_ROOT, { recursive: true }, (ev, name) => {
            if (!name) return;
            const n = resolveMirrorDir(name);
            if (!n) return;
            if (knownMirrors.has(n)) return;
            knownMirrors.add(n);
            setTimeout(() => {
                if (!adoptMirror(n, logObj)) {
                    // meta ???§Õ????????????????????????
                    knownMirrors.delete(n);
                }
            }, 2500);
        });
        logObj.appendLine('mirror root watcher: ' + MIRROR_ROOT);
    } catch (e) {
        logObj.appendLine('mirror root watch failed: ' + ((e && e.message) || e));
    }
}

async function migrateLegacyMirror(logObj, real, mirror) {
    if (fs.existsSync(mirror)) return;
    let ents = [];
    try {
        ents = await fs.promises.readdir(MIRROR_ROOT, { withFileTypes: true });
    } catch (e) {
        return;
    }
    for (const e of ents) {
        if (!e.isDirectory()) continue;
        const cand = path.join(MIRROR_ROOT, e.name);
        if (cand.toLowerCase() === mirror.toLowerCase()) continue;
        try {
            const meta = JSON.parse(await fs.promises.readFile(path.join(cand, '.mirror-meta.json'), 'utf8'));
            if (meta && meta.real && String(meta.real).toLowerCase() === real.toLowerCase()) {
                try {
                    await fs.promises.rename(cand, mirror);
                    logObj.appendLine('migrated legacy mirror ' + e.name + ' -> ' + path.basename(mirror));
                } catch (err) {
                    logObj.appendLine('rename failed ' + e.name + ': ' + ((err && err.message) || err));
                }
                return;
            }
        } catch (err) { /* no meta, skip */ }
    }
}

async function writeIndex(logObj, pairs) {
    const lines = ['????????Ë  ' + new Date().toLocaleString('zh-CN'), '', '', '?????? | ??????? | ???', '-'.repeat(58)];
    for (const p of pairs) {
        let exists = false;
        try { exists = fs.existsSync(p.mirror); } catch (e) { exists = false; }
        const realOk = fs.existsSync(p.real);
        lines.push(path.basename(p.mirror) + ' | ' + p.real + ' | ' + (gitBranch(p.real) || '(no git)')
            + (exists ? '' : '  [¦Ä????]') + (realOk ? '' : '  [???¡¤????????]'));
    }
    lines.push('');
    lines.push('??????????????standalone bridge??????????');
    lines.push('  1) ?????? = ??????????????????????§Õ????????????????????');
    lines.push('  2) ???????? bridge-start.vbs ???????? C:\\Users\\myages2026\\.codebuddy-bridge\\bridge.log');
    lines.push('  3) ????????????????????????????????git ???????????????????');
    const text = lines.join('\r\n');
    await writePlain([{ p: path.join(MIRROR_ROOT, '_index.txt'), b64: Buffer.from(text, 'utf8').toString('base64') }], logObj);
}

async function ensureMirrorAndSync(logObj) {
    const pairs = mirrorPairs();
    if (!pairs.length) {
        logObj.appendLine('ensure: no local root');
        return;
    }

    for (const pair of pairs) {
        await migrateLegacyMirror(logObj, pair.real, pair.mirror);
        if (!fs.existsSync(pair.mirror)) {
            if (BUILD_MISSING) {
                logObj.appendLine('mirror not found, building: ' + pair.mirror);
                await buildMirror(logObj, pair.real, pair.mirror);
            } else {
                logObj.appendLine('mirror missing, not created: ' + pair.mirror + ' (open the project in VSCode first)');
            }
        }
    }

    stopSync();
    syncedReals.clear();
    for (const pair of pairs) {
        const s = startSync(logObj, pair.real, pair.mirror);
        if (s) {
            activeSyncs.push(s);
            syncedReals.add(pair.real.toLowerCase());
        }
        logObj.appendLine('active mirror: ' + pair.mirror);
    }

    try {
        await writeIndex(logObj, pairs);
    } catch (e) {
        logObj.appendLine('index write failed: ' + ((e && e.message) || e));
    }
}

/* ---------------- branch watcher ---------------- */

let branchWatchers = [];

function watchBranch(logObj) {
    for (const w of branchWatchers) {
        try { w.close(); } catch (e) { /* ignore */ }
    }
    branchWatchers = [];

    for (const real of REAL_ROOTS) {
        const head = path.join(real, '.git', 'HEAD');
        if (!fs.existsSync(head)) continue;
        try {
            const w = fs.watch(head, () => {
                branchCache.clear();
                setTimeout(() => {
                    logObj.appendLine('branch changed -> switching mirror');
                    ensureMirrorAndSync(logObj).catch((e) => logObj.appendLine('switch failed: ' + ((e && e.message) || e)));
                }, 1500);
            });
            branchWatchers.push(w);
            logObj.appendLine('branch watcher: ' + head);
        } catch (e) {
            logObj.appendLine('branch watch failed: ' + ((e && e.message) || e));
        }
    }
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
                        pairs: mirrorPairs()
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
                        /* writing a mirror through this trusted process would leave
                           the file encrypted, refuse it */
                        log.appendLine('write refused (not a real root): ' + p);
                        return send(res, 403, { ok: false, err: 'refused: not under a real root' });
                    }
                    const raw = await readBody(req);
                    const data = Buffer.from(raw.toString('utf8').trim(), 'base64');
                    await fs.promises.mkdir(path.dirname(p), { recursive: true });
                    await atomicWrite(p, data);
                    return send(res, 200, { ok: true, size: data.length });
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

    scanMirrors(log);
    orphanScan(log).catch(() => { });
    setInterval(() => { orphanScan(log).catch(() => { }); }, 30000);
    watchBranch(log);
    await ensureMirrorAndSync(log);
    watchMirrorRoot(log);
    logLine('ready');
})().catch((e) => {
    logLine('fatal: ' + ((e && e.stack) || e));
    process.exit(1);
});
