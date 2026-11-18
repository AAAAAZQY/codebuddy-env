/*
 * seed-snap-66t.js —— 用「备份（改动前）」字节直接写入 CodeBuddy「改动对比」快照
 * 用法: node seed-snap-66t.js <backupRoot> <mirrorRoot>
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const backupRoot = process.argv[2];
const mirrorRoot = process.argv[3];
if (!backupRoot || !mirrorRoot) {
  console.log('usage: node seed-snap-66t.js <backupRoot> <mirrorRoot>');
  process.exit(1);
}

const snapsRoot = path.join(process.env.APPDATA, 'CodeBuddy CN', 'User', 'globalStorage', 'local.diff-snap', 'snaps');
fs.mkdirSync(snapsRoot, { recursive: true });
const indexPath = path.join(snapsRoot, 'index.json');

let index = {};
if (fs.existsSync(indexPath)) {
  try { index = JSON.parse(fs.readFileSync(indexPath, 'utf8')); } catch (e) { index = {}; }
}

function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (/\.(c|h|s)$/i.test(e.name)) out.push(p);
  }
  return out;
}

const files = walk(backupRoot, []);
const ts = Date.now();
let seed = 0;
for (const bak of files) {
  const rel = path.relative(backupRoot, bak);
  const mirror = path.join(mirrorRoot, rel);
  if (!fs.existsSync(mirror)) { console.log('skip(no mirror): ' + rel); continue; }
  const key = mirror.toLowerCase();
  const dir = path.join(snapsRoot, crypto.createHash('md5').update(key).digest('hex').slice(0, 12));
  fs.mkdirSync(dir, { recursive: true });
  const sTs = ts + seed++;
  const snapPath = path.join(dir, sTs + '-' + path.basename(mirror));
  fs.writeFileSync(snapPath, fs.readFileSync(bak));
  const prev = index[key];
  const snaps = (prev && Array.isArray(prev.snaps)) ? prev.snaps : [];
  snaps.push({ ts: sTs, path: snapPath });
  index[key] = { fsPath: mirror, name: path.basename(mirror), snaps };
  console.log('seed ' + rel + ' -> ' + snapPath);
}
fs.writeFileSync(indexPath, JSON.stringify(index, null, 1), 'utf8');
console.log('index entries: ' + Object.keys(index).length);
