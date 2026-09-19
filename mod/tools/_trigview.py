# -*- coding: utf-8 -*-
"""只渲染「握把 + 护圈 + 扳机」这一小块（放大核对扳机/护圈形状）。

用法: python tools\_trigview.py [geo] [png]
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, 'build', 'awp_v1.geo.json')
TEX = os.path.join(ROOT, 'build', 'awp_v1.png')
SUB = os.path.join(ROOT, 'build', '_trig.geo.json')

data = json.load(open(GEO, encoding='utf-8'))
for b in data['minecraft:geometry'][0]['bones']:
    keep = []
    for c in b.get('cubes') or []:
        x, y = float(c['origin'][0]), float(c['origin'][1])
        if b['name'] == 'trigger' or (b['name'] == 'body' and y < 0.3 and x > -2.2):
            keep.append(c)
    b['cubes'] = keep
json.dump(data, open(SUB, 'w', encoding='utf-8'), ensure_ascii=False)

VIEWS = [('side', 90.0, 4.0, 2.4), ('front', 0.0, 4.0, 2.4), ('iso', 215.0, 20.0, 2.0)]
for name, yaw, pitch, zoom in VIEWS:
    out = os.path.join(ROOT, 'build', '_trig_%s.png' % name)
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'geo_texview.py'),
                    SUB, TEX, out, '--yaw', str(yaw), '--pitch', str(pitch),
                    '--zoom', str(zoom), '--size', '800'], check=True,
                   stdout=subprocess.DEVNULL)
    print('wrote build\\_trig_%s.png' % name)
