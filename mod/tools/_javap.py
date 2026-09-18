"""反编译查看 GeckoLib(1.20.1-4.8.4) 的接口签名。

用法: python tools/_javap.py <类全名> [...]
"""
import glob
import os
import subprocess
import sys

BASE = os.path.expanduser('~/.gradle/caches/modules-2/files-2.1/software.bernie.geckolib')
JAVAP = r'D:\java\bin\javap.exe'


def jar_of(pattern):
    hits = [p for p in glob.glob(os.path.join(BASE, '**', '*.jar'), recursive=True)
            if pattern in os.path.basename(p)]
    if not hits:
        raise SystemExit('找不到 jar: %s' % pattern)
    return hits[0]


def main(argv):
    jar = jar_of('geckolib-forge-1.20.1-4.8.4')
    print('JAR %s' % jar)
    for cls in argv[1:]:
        print('=' * 60)
        print(cls)
        subprocess.run([JAVAP, '-classpath', jar, cls])


if __name__ == '__main__':
    main(sys.argv)
