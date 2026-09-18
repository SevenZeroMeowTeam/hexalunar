"""打印 geo 里每根骨骼的包围盒（加细节件前先看坐标）。

用法: python tools/dump_bones.py <a.geo.json> [b.geo.json ...]
"""
import json
import os
import sys


def dump(path):
    g = json.load(open(path, encoding='utf-8'))['minecraft:geometry'][0]
    print('===== %s  （%d 骨骼）' % (os.path.basename(path), len(g['bones'])))
    for b in g['bones']:
        cs = b.get('cubes') or []
        if not cs:
            print('  %-14s (空) pivot=%s' % (b['name'], b['pivot']))
            continue
        xs = [(c['origin'][0], c['origin'][0] + c['size'][0]) for c in cs]
        ys = [(c['origin'][1], c['origin'][1] + c['size'][1]) for c in cs]
        zs = [(c['origin'][2], c['origin'][2] + c['size'][2]) for c in cs]
        print('  %-14s n=%2d  X %7.2f..%7.2f   Y %7.2f..%7.2f   Z %7.2f..%7.2f'
              % (b['name'], len(cs), min(a for a, _ in xs), max(b2 for _, b2 in xs),
                 min(a for a, _ in ys), max(b2 for _, b2 in ys),
                 min(a for a, _ in zs), max(b2 for _, b2 in zs)))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        dump(p)
