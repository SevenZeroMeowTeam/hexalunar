# -*- coding: utf-8 -*-
"""从 jar 里抽一个文本文件打印（默认查 Q 版命名空间替换有没有漏）。

用法::

    python tools/_jarread.py <jar|最新> <jar 内路径> [关键字] [后几行]
"""
import glob
import io
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    jarp = sys.argv[1]
    if jarp in ('最新', 'latest'):
        js = sorted(glob.glob(os.path.join(ROOT, 'build', 'libs', '*.jar')),
                    key=os.path.getmtime)
        jarp = js[-1]
    inner = sys.argv[2]
    key = sys.argv[3] if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(jarp)
    names = [n for n in z.namelist() if inner in n]
    out = io.StringIO()
    out.write('%s\n' % os.path.basename(jarp))
    for n in names:
        out.write('--- %s\n' % n)
        txt = z.read(n).decode('utf-8', 'replace').splitlines()
        if key:
            hits = [i for i, l in enumerate(txt) if key in l]
            for i in hits[:20]:
                out.write('  %4d | %s\n' % (i + 1, txt[i].strip()))
        else:
            for i, l in enumerate(txt[:40]):
                out.write('  %4d | %s\n' % (i + 1, l))
    dst = os.path.join(ROOT, 'build', '_jarread.txt')
    with io.open(dst, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(out.getvalue())
    print('wrote build/_jarread.txt (%d files matched)' % len(names))


if __name__ == '__main__':
    main()
