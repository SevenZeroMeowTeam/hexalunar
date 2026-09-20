# -*- coding: utf-8 -*-
"""打印 TaCZ jar 里某个文本文件的内容（找定位组 / 枪械数据用）。

用法::

    python tools/_tacz_cat.py display/guns/ai_awp_display.json
    python tools/_tacz_cat.py data/tacz/ai_awp_data.json
"""
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'D:\mcmod\src\main\libs\tacz-1.20.1-1.1.8-hotfix.jar'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    key = sys.argv[1]
    pretty = '--raw' not in sys.argv
    with zipfile.ZipFile(JAR) as z:
        hit = [n for n in z.namelist() if n.endswith(key)]
        if not hit:
            raise SystemExit('jar 里没有 %s' % key)
        if len(hit) > 1:
            print('# 命中 %d 条，取第一条' % len(hit))
        raw = z.read(hit[0]).decode('utf-8', 'replace')
        path = hit[0]
    dst = os.path.join(ROOT, 'build', os.path.basename(path))
    with open(dst, 'w', encoding='utf-8') as fh:
        fh.write(raw)
    print('# %s  ->  %s' % (path, os.path.relpath(dst, ROOT)))
    if pretty:
        try:
            print(json.dumps(json.loads(raw), ensure_ascii=False, indent=1))
            return
        except ValueError:
            pass
    print(raw)


if __name__ == '__main__':
    main()
