"""在某个源码 jar 里全文搜一个关键词，打印命中行（读第三方源码用）。

用法: python tools\_jargrep.py <jar> <关键词> [最多命中数]
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    jar = argv[1]
    needle = argv[2]
    limit = int(argv[3]) if len(argv) > 3 else 40
    hits = 0
    with zipfile.ZipFile(os.path.join(ROOT, jar) if not os.path.isabs(jar) else jar) as z:
        for n in z.namelist():
            if not n.endswith('.java'):
                continue
            text = z.read(n).decode('utf-8', 'replace')
            if needle not in text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if needle in line:
                    print('%s:%d: %s' % (n, i, line.strip()))
                    hits += 1
                    if hits >= limit:
                        return
    print('命中 %d' % hits)


if __name__ == '__main__':
    main(sys.argv)
