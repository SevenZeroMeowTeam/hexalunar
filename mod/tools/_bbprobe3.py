# -*- coding: utf-8 -*-
"""扫描仓库里所有 .bbmodel，逐个体检：元素数 / 类型（cube 还是 mesh）/ 分组名 / 贴图。

用法: python tools\\_bbprobe3.py [关键子串]
"""
import io
import json
import os
import sys

ROOT = r'D:\做一个_Minecraft_1_20_1_的_F'


def summarize(path):
    data = json.loads(io.open(path, encoding='utf-8').read())
    elems = data.get('elements', [])
    kinds = {}
    for e in elems:
        t = e.get('type', 'cube')
        kinds[t] = kinds.get(t, 0) + 1
    groups = []

    def walk(items, depth):
        for it in items:
            if not isinstance(it, dict):
                continue
            groups.append('%s%s' % ('  ' * depth, it.get('name')))
            walk(it.get('children', []), depth + 1)

    walk(data.get('outliner', []), 0)
    res = data.get('resolution', {})
    print('%9d  %s' % (os.path.getsize(path), os.path.basename(path)))
    print('           format=%s model_format=%s res=%sx%s 贴图=%d 元素=%d %s' % (
        data.get('meta', {}).get('format_version'), data.get('model_format'),
        res.get('width'), res.get('height'), len(data.get('textures', [])), len(elems), kinds))
    print('           组: %s' % ('  '.join(groups) if groups else '(无)'))


def main(argv):
    want = argv[1].lower() if len(argv) > 1 else ''
    found = []
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'build', 'run', 'logs', 'node_modules')]
        for f in files:
            if f.lower().endswith('.bbmodel'):
                p = os.path.join(dirpath, f)
                found.append((os.path.getsize(p), p))
    found.sort()
    print('== %d 个 bbmodel ==' % len(found))
    for _size, p in found:
        if want and want not in os.path.basename(p).lower():
            continue
        try:
            summarize(p)
        except Exception as exc:                                  # noqa: BLE001
            print('  !! %s -> %s' % (p, exc))
        print()


if __name__ == '__main__':
    main(sys.argv)
