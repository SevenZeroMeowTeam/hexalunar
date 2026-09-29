# -*- coding: utf-8 -*-
"""打印 geo 里指定骨骼的方块坐标（护圈 / 扳机 / 弹仓 / 木托），核对用。

用法::  python tools/_geodump2.py body,trigger
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEO = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'geo', 'mosin.geo.json')
BONES = set((sys.argv[1] if len(sys.argv) > 1 else 'body,trigger').split(','))

out = []
g = json.load(io.open(GEO, encoding='utf-8'))
for b in g['minecraft:geometry'][0]['bones']:
    if b['name'] not in BONES:
        continue
    out.append('=== bone %s  pivot=%s  cubes=%d  keys=%s'
               % (b['name'], b['pivot'], len(b.get('cubes', [])),
                  sorted(b['cubes'][0].keys()) if b.get('cubes') else []))
    for c in b.get('cubes', []):
        o, s = c['origin'], c['size']
        out.append('    %-12s x %6.2f..%6.2f  y %6.2f..%6.2f  z %6.2f..%6.2f  rot=%s'
                   % (c.get('name', ''), o[0], o[0] + s[0], o[1], o[1] + s[1],
                      o[2], o[2] + s[2], c.get('rotation')))
io.open(os.path.join(ROOT, 'build', '_tg.txt'), 'w', encoding='utf-8').write(
    '\n'.join(out))
print('lines=%d -> build/_tg.txt' % len(out))
