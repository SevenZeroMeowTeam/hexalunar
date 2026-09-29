# -*- coding: utf-8 -*-
"""扫 `mod/logs` 的现场日志：按 GBK/UTF-8 自动解码，筛出**本模组**相关的行与异常。

用法::

    python tools/_scanlog.py [关键词]            # 默认关键词 hexalunar
    python tools/_scanlog.py hexalunar --gz      # 连 .gz 归档一起扫
    python tools/_scanlog.py "" --all            # 不做关键词过滤（只列 ERROR/Exception 行）
"""
import gzip
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, 'logs')

BAD = re.compile(r'(Exception|Error|error|ERROR|Caused by|FAILED|failed|崩溃|Unable|'
                 r'NoSuch|NullPointer|ClassCast|IllegalState|Missing|missing|not found)')


def read(path):
    raw = open(path, 'rb').read()
    if path.endswith('.gz'):
        raw = gzip.decompress(raw)
    for enc in ('utf-8', 'gbk', 'cp936', 'latin-1'):
        try:
            return raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return []


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else 'hexalunar'
    if key.startswith('--'):
        key = ''
    files = []
    for f in sorted(os.listdir(LOGS)):
        if f.endswith('.log') or (f.endswith('.gz') and '--gz' in sys.argv):
            files.append(os.path.join(LOGS, f))
    out = io.StringIO()
    out.write('scanning %d files, keyword=%r\n' % (len(files), key))
    for path in files:
        lines = read(path)
        hits = []
        for i, ln in enumerate(lines):
            if key:
                if key.lower() not in ln.lower():
                    continue
                # 带关键词但不含错误字样：仍收（可能是 mod 自身的告警/信息）
                if not BAD.search(ln) and 'WARN' not in ln:
                    continue
            elif not BAD.search(ln):
                continue
            hits.append((i + 1, ln))
        if not hits:
            continue
        out.write('\n===== %s  (%d 行命中 / 共 %d 行)\n'
                  % (os.path.basename(path), len(hits), len(lines)))
        for n, ln in hits[:400]:
            out.write('%6d | %s\n' % (n, ln[:400]))
    dst = os.path.join(ROOT, 'build', '_scan.txt')
    with io.open(dst, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(out.getvalue())
    print('wrote build/_scan.txt  (%d bytes)' % len(out.getvalue()))


if __name__ == '__main__':
    main()
