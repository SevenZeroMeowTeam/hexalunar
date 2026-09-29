"""打印 AKM / AWP geo 里与「拉栓 + 抛壳」相关骨骼的 pivot 与方块范围（模型像素）。

用法：python tools/_bone_probe.py [akm|awp|all]
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(ROOT, '..', 'src', 'main', 'resources', 'assets',
                   'hexalunar_calamity', 'geo')

KEYS = ('casing', 'bolt', 'charging', 'handle', 'trigger', 'magazine', 'move', 'body')


def probe(geo_name, want):
    path = os.path.join(GEO, geo_name)
    with io.open(path, encoding='utf-8') as fh:
        g = json.load(fh)
    bones = g['minecraft:geometry'][0]['bones']
    print('=' * 70)
    print('%s  (%d bones)' % (geo_name, len(bones)))
    for b in bones:
        name = b.get('name', '?')
        if want not in name:
            continue
        piv = b.get('pivot', [0, 0, 0])
        cubes = b.get('cubes') or []
        if cubes:
            x0 = min(c['origin'][0] for c in cubes)
            x1 = max(c['origin'][0] + c['size'][0] for c in cubes)
            y0 = min(c['origin'][1] for c in cubes)
            y1 = max(c['origin'][1] + c['size'][1] for c in cubes)
            z0 = min(c['origin'][2] for c in cubes)
            z1 = max(c['origin'][2] + c['size'][2] for c in cubes)
            geom = 'x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f' % (x0, x1, y0, y1, z0, z1)
        else:
            geom = '(empty bone)'
        print('  %-14s pivot=(%7.3f, %7.3f, %7.3f)  %s'
              % (name, piv[0], piv[1], piv[2], geom))


for want in KEYS:
    pass

targets = sys.argv[1] if len(sys.argv) > 1 else 'all'
if targets in ('akm', 'all'):
    for k in KEYS:
        probe('akm.geo.json', k)
if targets in ('awp', 'all'):
    for k in KEYS:
        probe('awp.geo.json', k)
