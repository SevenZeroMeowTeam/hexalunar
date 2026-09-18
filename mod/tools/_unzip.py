"""从 jar 里导出单个条目（看第三方库/原版源码用）。

用法: python tools\_unzip.py <jar> <条目名含的片段> [输出名]
"""
import io
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    jar = argv[1]
    if not os.path.isabs(jar):
        jar = os.path.join(ROOT, jar)
    needle = argv[2]
    with zipfile.ZipFile(jar) as z:
        names = [n for n in z.namelist() if needle in n]
        for n in names:
            print('  命中:', n)
        if not names:
            return
        if len(names) > 1 and len(argv) < 3:
            return
        n = names[0]
        out = os.path.join(ROOT, 'build', argv[3] if len(argv) > 3 else os.path.basename(n))
        with io.open(out, 'w', encoding='utf-8', errors='replace') as fh:
            fh.write(z.read(n).decode('utf-8', 'replace'))
        print('  ->', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main(sys.argv)
