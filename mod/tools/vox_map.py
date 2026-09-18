#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打印参考 .bbmodel 的体素投影图，用来确定骨骼分区。

用法: python tools/vox_map.py <model.bbmodel> [out.txt] [step]
"""
import io
import math
import sys

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref, voxelize, rotate_tris, yaw_slope


def main(argv):
    path = argv[1] if len(argv) > 1 else '模型/akm.bbmodel'
    out_path = argv[2] if len(argv) > 2 else 'build/voxmap.txt'
    step = float(argv[3]) if len(argv) > 3 else 0.5
    verts, tris, tex, uv_w, uv_h = load_ref(path)
    print('%s: %d 顶点 / %d 三角面  UV %dx%d  贴图 %s' % (
        path, len(verts), len(tris), uv_w, uv_h, tex.size if tex else None))

    cells, lo, hi = voxelize(tris, step, uv_w, uv_h, quiet=True)
    s0 = yaw_slope(cells, lo, step)
    total = 0.0
    for _i in range(3):
        s = yaw_slope(cells, lo, step)
        if abs(s) < 0.003:
            break
        best = None
        for deg in (math.degrees(math.atan(s)), -math.degrees(math.atan(s))):
            t2 = rotate_tris(tris, total + deg)
            c2, l2, h2 = voxelize(t2, step, uv_w, uv_h, quiet=True)
            s2 = yaw_slope(c2, l2, step)
            if best is None or abs(s2) < abs(best[0]):
                best = (s2, total + deg, c2, l2, h2)
        _s, total, cells, lo, hi = best
    print('偏航 %.2f° -> %.2f°（旋转 %.2f°）  体素 %d' % (
        math.degrees(math.atan(s0)),
        math.degrees(math.atan(yaw_slope(cells, lo, step))), total, len(cells)))
    print('包围盒 x %.2f~%.2f  y %.2f~%.2f  z %.2f~%.2f' % (
        lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))

    pts = [((lo[0] + (ix + .5) * step), (lo[1] + (iy + .5) * step), (lo[2] + (iz + .5) * step))
           for (ix, iy, iz) in cells]
    out = []

    def grid(axis_h, axis_v, title, axis_x=None):
        idx = {}
        for p in pts:
            idx.setdefault((round(p[axis_h], 1), round(p[axis_v], 1)), []).append(
                round(p[axis_x], 1) if axis_x is not None else 0.0)
        hs = sorted(set(k[0] for k in idx))
        vs = sorted(set(k[1] for k in idx), reverse=True)
        out.append('== %s ==  %d x %d' % (title, len(hs), len(vs)))
        out.append('       ' + ''.join('%5.1f' % h for h in hs))
        for v in vs:
            out.append('%5.1f  %s' % (v, ''.join(
                '%5s' % ('#%d' % len(idx[(h, v)]) if (h, v) in idx else '.') for h in hs)))

    grid(2, 1, '侧视 (z 横 / y 纵)')
    grid(2, 0, '俯视 (z 横 / x 纵)')
    grid(0, 1, '后视 (x 横 / y 纵)')

    out.append('== 逐 z 层范围 ==')
    byz = {}
    for (ix, iy, iz) in cells:
        e = byz.setdefault(iz, [9e9, -9e9, 9e9, -9e9, 0])
        e[0] = min(e[0], iy); e[1] = max(e[1], iy)
        e[2] = min(e[2], ix); e[3] = max(e[3], ix); e[4] += 1
    for iz in sorted(byz):
        e = byz[iz]
        out.append('z=%6.2f  y %5.2f~%5.2f  x %5.2f~%5.2f  n=%3d' % (
            lo[2] + iz * step, lo[1] + e[0] * step, lo[1] + (e[1] + 1) * step,
            lo[0] + e[2] * step, lo[0] + (e[3] + 1) * step, e[4]))

    io.open(out_path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('written -> %s' % out_path)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
