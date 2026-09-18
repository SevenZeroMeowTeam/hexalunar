#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断：参考贴图与 UV 的对应关系（缩放/翻转），按部件平均色判断。"""
import io
import sys

from PIL import Image

sys.path.insert(0, 'tools')
from akm_voxel_gen import (load_ref, voxelize, rotate_tris, yaw_slope, region_vox, TEX_OUT)
import math

verts, tris, tex, uv_w, uv_h = load_ref()
cells0, lo0, hi0 = voxelize(tris, 0.5, uv_w, uv_h, quiet=True)
s0 = yaw_slope(cells0, lo0, 0.5)
best = None
for deg in (math.degrees(math.atan(s0)), -math.degrees(math.atan(s0))):
    t2 = rotate_tris(tris, deg)
    c2, l2, h2 = voxelize(t2, 0.5, uv_w, uv_h, quiet=True)
    s2 = yaw_slope(c2, l2, 0.5)
    if best is None or abs(s2) < abs(best[0]):
        best = (s2, c2, l2)
_cells, lo = best[1], best[2]

im = Image.open(TEX_OUT).convert('RGB')
out = ['UV 空间 %dx%d  贴图 %s' % (uv_w, uv_h, im.size)]

for name, su, sv, flip in (('uv*32 (当前)', 512 / 16.0, 512 / 16.0, False),
                           ('uv*32 + V翻转', 512 / 16.0, 512 / 16.0, True),
                           ('uv*0.25', 512 / 2048.0, 512 / 2048.0, False),
                           ('uv*1', 1.0, 1.0, False)):
    acc = {}
    for (ix, iy, iz), (u, v) in _cells.items():
        cx = lo[0] + (ix + .5) * .5
        cy = lo[1] + (iy + .5) * .5
        cz = lo[2] + (iz + .5) * .5
        r = region_vox(cx, cy, cz)
        px = int(u * su) % 512
        py = int(v * sv) % 512
        if flip:
            py = 511 - py
        c = im.getpixel((px, py))
        a = acc.setdefault(r, [0, 0, 0, 0])
        a[0] += c[0]; a[1] += c[1]; a[2] += c[2]; a[3] += 1
    line = ['%-14s' % name]
    for r in sorted(acc):
        a = acc[r]
        line.append('%s=(%d,%d,%d)' % (r[:4], a[0] // a[3], a[1] // a[3], a[2] // a[3]))
    out.append('  '.join(line))

io.open('build/uvdiag.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('written')
