/*
 * diffsnap-seed.js —— 把「改动前」内容写入 CodeBuddy「改动对比」扩展的快照索引
 *
 * 用法（受信任进程运行，保证读到明文）：
 *   Code.exe diffsnap-seed.js <文件绝对路径> [更多文件...] [--from-disk]
 *
 * 默认从 git HEAD 取「改动前」内容；加 --from-disk 则用磁盘当前内容
 * （--from-disk 必须在修改文件之前调用）。
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 镜像目录 -> 真实工程（git 仓库根）
const PAIRS = [
  { mirror: 'd:\\plain_view\\66d-main-ptz', repo: 'D:\\aMyProject\\Project\\66D\\main\\66d\\ptz_source_code' },
  { mirror: 'd:\\plain_view\\22b2-gx-ptz', repo: 'd:\\aMyProject\\Project\\22b2\\GX\\new\\22b2\\ptz_source_code' }
];

const argv = process.argv.slice(2);
const fromDisk = argv.includes('--from-disk');
const files = argv.filter((a) => !a.startsWith('--'));

if (!files.length) {
  console.log('用法: diffsnap-seed.js <文件...> [--from-disk]');
  process.exit(1);
}

const snapsRoot = path.join(process.env.APPDATA, 'CodeBuddy CN', 'User', 'globalStorage', 'local.diff-snap', 'snaps');
fs.mkdirSync(snapsRoot, { recursive: true });
const indexPath = path.join(snapsRoot, 'index.json');

let index = {};
if (fs.existsSync(indexPath)) {
  try { index = JSON.parse(fs.readFileSync(indexPath, 'utf8')); } catch (e) { index = {}; }
}

function resolveRepo(file) {
  const low = file.toLowerCase();
  for (const p of PAIRS) {
    if (low.startsWith(p.mirror + '\\')) {
      return { repo: p.repo, rel: path.relative(p.mirror, file).split(path.sep).join('/') };
    }
  }
  return null;
}

for (const file of files) {
  if (!fs.existsSync(file)) {
    console.log('跳过(不存在): ' + file);
    continue;
  }
  const key = file.toLowerCase();
  const dir = path.join(snapsRoot, crypto.createHash('md5').update(key).digest('hex').slice(0, 12));
  fs.mkdirSync(dir, { recursive: true });

  let content = null;
  let source = '';
  if (!fromDisk) {
    const r = resolveRepo(file);
    if (r) {
      // git 仓库根可能在镜像根的上一级（如 ptz_source_code\source_code\...）
      const candidates = [r.rel, 'ptz_source_code/' + r.rel];
      for (const rel of candidates) {
        try {
          content = execFileSync('git', ['-C', r.repo, 'show', 'HEAD:' + rel], { maxBuffer: 64 * 1024 * 1024 });
          source = 'git HEAD';
          break;
        } catch (e) {
          content = null;
        }
      }
    }
  }
  if (!content) {
    content = fs.readFileSync(file);
    source = 'disk';
  }

  const ts = Date.now() + Math.floor(Math.random() * 1000);
  const base = path.basename(file);
  const snapPath = path.join(dir, ts + '-' + base);
  const text = content.toString('latin1').replace(/\r\n/g, '\n').replace(/\n/g, '\r\n');
  fs.writeFileSync(snapPath, Buffer.from(text, 'latin1'));

  index[key] = { fsPath: file, name: base, snaps: [{ ts, path: snapPath }] };
  console.log('已记录 [' + source + '] ' + base + ' -> ' + snapPath);
}

fs.writeFileSync(indexPath, JSON.stringify(index, null, 1), 'utf8');
console.log('索引条目数: ' + Object.keys(index).length);
