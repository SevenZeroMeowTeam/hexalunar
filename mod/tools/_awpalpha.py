# -*- coding: utf-8 -*-
"""检查参考贴图与成品贴图的 alpha 通道（半透明/全透明的区域会让模型透出棋盘格）。

用法: python tools\_awpalpha.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for tag, path in (('源', os.path.join(ROOT, '模型', 'AWP_Printstream_Minecraft', 'awp_printstream.png')),
                  ('成品', os.path.join(ROOT, 'build', 'awp_v1.png'))):
    img = Image.open(path).convert('RGBA')
    a = np.asarray(img)[:, :, 3]
    print('%-4s %-28s %dx%d  alpha<255 = %d / %d  (透明 %.1f%%)  最小值 %d'
          % (tag, os.path.basename(path), img.width, img.height,
             int((a < 255).sum()), a.size, (a < 255).mean() * 100.0, int(a.min())))

# 成品贴图里：每个面矩形内有没有半透明像素
geo = json.load(open(os.path.join(ROOT, 'build', 'awp_v1.geo.json'), encoding='utf-8'))
g = geo['minecraft:geometry'][0]
out = np.asarray(Image.open(os.path.join(ROOT, 'build', 'awp_v1.png')).convert('RGBA'))[:, :, 3]
bad = []
for b in g['bones']:
    for i, c in enumerate(b.get('cubes') or []):
        for face, spec in (c.get('uv') or {}).items():
            x0, y0 = int(spec['uv'][0]), int(spec['uv'][1])
            w, h = int(spec['uv_size'][0]), int(spec['uv_size'][1])
            sub = out[y0:y0 + max(1, h), x0:x0 + max(1, w)]
            semi = int((sub < 255).sum())
            if semi:
                bad.append((b['name'], i, face, x0, y0, w, h, semi, sub.size))
print('\n含半透明像素的面：%d 个' % len(bad))
for row in bad[:20]:
    print('  %-12s cube%-2d %-6s uv=(%d,%d) %dx%d  %d/%d' % row)
