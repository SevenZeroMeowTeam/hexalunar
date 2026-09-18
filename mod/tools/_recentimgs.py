"""列出最近改动的图片文件，写到 build/_imgs.txt（终端输出有时被吞，落盘更稳）。

用法: python tools\_recentimgs.py [分钟]
"""
import io
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT_MIN = 240


def main():
    mins = LIMIT_MIN
    now = time.time()
    roots = [os.environ.get('TEMP', ''), os.path.join(os.path.expanduser('~'), 'Pictures'),
             os.path.join(os.path.expanduser('~'), 'Desktop'),
             os.path.join(os.path.expanduser('~'), 'Downloads'),
             os.path.join(os.path.dirname(ROOT), 'build')]
    found = []
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                if not f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                p = os.path.join(dirpath, f)
                try:
                    m = os.path.getmtime(p)
                except OSError:
                    continue
                if now - m > mins * 60:
                    continue
                found.append((m, os.path.getsize(p), p))
    found.sort(reverse=True)
    with io.open(os.path.join(ROOT, 'build', '_imgs.txt'), 'w', encoding='utf-8') as fh:
        for m, size, p in found[:40]:
            fh.write('%s  %8d  %s\n' % (time.strftime('%H:%M:%S', time.localtime(m)), size, p))
    print('found %d' % len(found))


if __name__ == '__main__':
    main()
