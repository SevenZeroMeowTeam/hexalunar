# -*- coding: utf-8 -*-
"""在 TaCZ jar 里按关键字找条目（找某把枪的动画 / 数据 / 定位组用）。

用法::

    python tools/_tacz_find.py awm
    python tools/_tacz_find.py ai_aw     # 精密国际 AWM
    python tools/_tacz_find.py animation # 所有动画文件
"""
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'D:\mcmod\src\main\libs\tacz-1.20.1-1.1.8-hotfix.jar'


def main():
    key = (sys.argv[1] if len(sys.argv) > 1 else '').lower()
    with zipfile.ZipFile(JAR) as z:
        names = [n for n in z.namelist() if key in n.lower()]
        for n in sorted(names):
            info = z.getinfo(n)
            print('%9d  %s' % (info.file_size, n))
    print('共 %d 条（关键字 %r）' % (len(names), key))


if __name__ == '__main__':
    main()
