# -*- coding: utf-8 -*-
"""列出 TaCZ jar 里的动画文件 / 打印某个动画文件的骨骼通道极值。

用法::

    python tools/_tacz_animlist.py                 # 列出 jar 内 animations/*.json
    python tools/_tacz_animlist.py kar98k          # 只看名字里含 kar98k 的
"""
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JAR = r'D:\mcmod\src\main\libs\tacz-1.20.1-1.1.8-hotfix.jar'


def main():
    key = sys.argv[1].lower() if len(sys.argv) > 1 else ''
    if not os.path.exists(JAR):
        raise SystemExit('找不到 TaCZ jar: %s' % JAR)
    with zipfile.ZipFile(JAR) as z:
        names = [n for n in z.namelist()
                 if n.startswith('assets/tacz/animations/') and n.endswith('.json')]
    for n in sorted(names):
        if key and key not in n.lower():
            continue
        print('%8d  %s' % (0, n))
    print('共 %d 个（过滤 %r）' % (len(names), key))


if __name__ == '__main__':
    main()
