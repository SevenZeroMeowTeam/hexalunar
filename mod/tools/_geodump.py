# -*- coding: utf-8 -*-
"""打印 geo 里指定前缀的方块（护圈 / 扳机 / 弹仓 / 木托）坐标，核对用。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEO = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'geo', 'mosin.geo.json')
PREF = tuple(sys.argv[1].split(',')) if len(sys.argv) > 1 else ('tg_', 'trg_')

out = []
g = json.load(io.open(GEO, encoding='utf-8'))
for b in g['minecraft:geometry'][0]['bones']:
    for c in b.get('cubes', []):
        nm = c.get('name') or ''
        if nm.startswith(PREF):
            o, s = c['origin'], c['size']
            out.append('%-12s %-10s x %6.2f..%6.2f  y %6.2f..%6.2f  z %6.2f..%6.2f'
                       % (b['name'], nm, o[0], o[0] + s[0], o[1], o[1] + s[1],
                          o[2], o[2] + s[2]))
io.open(os.path.join(ROOT, 'build', '_tg.txt'), 'w', encoding='utf-8').write(
    '\n'.join(out))
print('cubes=%d -> build/_tg.txt' % len(out))
