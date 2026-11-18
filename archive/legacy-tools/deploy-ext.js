/* �����ν��̲�����չ���﷨У�� -> ���ݾ��ļ� -> д�밲װĿ¼ -> ����У�� */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const SRC = 'D:\\Codebuddy\\tools\\ext-name15-fixed.js';
const DST = 'C:\\Users\\myages2026\\.vscode\\extensions\\local.filebridge-0.0.1\\extension.js';
const LOG = 'D:\\Codebuddy\\tools\\deploy-ext.log';
const lines = [];
function log(s) { lines.push(s); }

function md5(buf) { return crypto.createHash('md5').update(buf).digest('hex'); }

try {
  const srcBuf = fs.readFileSync(SRC);
  const srcText = srcBuf.toString('utf8');
  log('src=' + SRC + ' bytes=' + srcBuf.length + ' md5=' + md5(srcBuf));

  // �﷨У�飺�����ݴ��뵱�������������ִ��
  let syntaxOk = true;
  try {
    new Function(srcText);
  } catch (e) {
    syntaxOk = false;
    log('SYNTAX-ERROR: ' + ((e && e.message) || e));
  }
  log('syntax=' + (syntaxOk ? 'OK' : 'FAIL'));
  if (!syntaxOk) {
    log('aborted');
  } else {
    // ���ݾ��ļ��������ν��̶����������ģ�
    if (fs.existsSync(DST)) {
      const oldBuf = fs.readFileSync(DST);
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      const bak = path.join(path.dirname(SRC), 'extension.js.bak-' + stamp);
      fs.writeFileSync(bak, oldBuf);
      log('backup=' + bak + ' bytes=' + oldBuf.length + ' md5=' + md5(oldBuf));
    }
    fs.writeFileSync(DST, srcBuf);
    const backBuf = fs.readFileSync(DST);
    const same = backBuf.length === srcBuf.length && md5(backBuf) === md5(srcBuf);
    log('dst=' + DST + ' bytes=' + backBuf.length + ' md5=' + md5(backBuf));
    log('roundtrip-same=' + same);
    log(same ? 'DEPLOY-OK' : 'DEPLOY-MISMATCH');
  }
} catch (e) {
  log('EXCEPTION: ' + ((e && e.stack) || e));
}
fs.writeFileSync(LOG, lines.join('\r\n'), 'utf8');
