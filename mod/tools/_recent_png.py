"""列出最近改动的图片（找用户粘贴的截图用）。

用法: python tools/_recent_png.py [分钟]
"""
import os
import sys
import time

ROOTS = [os.path.join(os.environ.get('APPDATA', ''), 'Code', 'User', 'workspaceStorage'),
         os.path.join(os.environ.get('TEMP', ''))]


def main(argv):
    mins = int(argv[1]) if len(argv) > 1 else 60
    cutoff = time.time() - mins * 60
    found = []
    for root in ROOTS:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                if not name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                p = os.path.join(dirpath, name)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if st.st_mtime >= cutoff:
                    found.append((st.st_mtime, st.st_size, p))
    found.sort(reverse=True)
    for mtime, size, p in found[:12]:
        print('%s  %8d B  %s' % (time.strftime('%H:%M:%S', time.localtime(mtime)), size, p))


if __name__ == '__main__':
    main(sys.argv)
