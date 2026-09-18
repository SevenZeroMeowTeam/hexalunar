"""在 Gradle 缓存里找「包含某个 .java 源码条目」的 jar（用来读原版/第三方源码）。

用法: python tools\_findsrc.py ItemInHandRenderer.java [搜索根目录]
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ROOT = os.path.join(os.path.expanduser('~'), '.gradle', 'caches')


def main(argv):
    needle = argv[1]
    base = argv[2] if len(argv) > 2 else DEFAULT_ROOT
    hits = 0
    for dirpath, _dirs, files in os.walk(base):
        for f in files:
            if not f.endswith('.jar'):
                continue
            path = os.path.join(dirpath, f)
            try:
                with zipfile.ZipFile(path) as z:
                    for n in z.namelist():
                        if n.endswith(needle) or n.endswith('/' + needle):
                            print(path)
                            print('   ', n)
                            hits += 1
                            break
            except Exception:
                pass
    print('命中 %d 个 jar' % hits)


if __name__ == '__main__':
    main(sys.argv)
