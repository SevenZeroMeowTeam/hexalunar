#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把参考网格的三角面直接投影成 ASCII 图（不体素化），用来看真实轮廓与部件分布。

用法: python tools/mesh_proj.py <model.bbmodel> [out.txt] [res] [--yaw deg]
"""
import io
import math
import sys

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref, rotate_tris


def raster(tris, ha, va, res):
    """把三角面投影到 (ha, va) 两轴，返回占用的格子集合（0.5 采样 + 边采样）。"""
    cells = set()
    for t in tris:
        pts = [t[0], t[1], t[2]]
        # 重心网格采样 + 顶点
        for i in range(0, 9):
            for j in range(0, 9 - i):
                k = 8 - i - j
                p = [(pts[0][q] * i + pts[1][q] * j + pts[2][q] * k) / 8.0 for q in range(3)]
                cells.add((math.floor(p[ha] / res), math.floor(p[va] / res)))
        # 把每条边细分补上，避免细杆漏格
        for a, b in ((0, 1), (1, 2), (2, 0)):
            for s in range(21):
                f = s / 20.0
                p = [pts[a][q] * (1 - f) + pts[b][q] * f for q in range(3)]
                cells.add((math.floor(p[ha] / res), math.floor(p[va] / res)))
    return cells


def main(argv):
    path = argv[1] if len(argv) > 1 else '模型/复合弓.bbmodel'
    out_path = argv[2] if len(argv) > 2 else 'build/proj.txt'
    res = float(argv[3]) if len(argv) > 3 else 0.5
    yaw = 0.0
    if '--yaw' in argv:
        yaw = float(argv[argv.index('--yaw') + 1])

    verts, tris, tex, uv_w, uv_h = load_ref(path)
    if yaw:
        tris = rotate_tris(tris, yaw)
    xs = [t[i][0] for t in tris for i in range(3)]
    ys = [t[i][1] for t in tris for i in range(3)]
    zs = [t[i][2] for t in tris for i in range(3)]
    print('%s: %d 三角面  包围盒 x %.2f~%.2f y %.2f~%.2f z %.2f~%.2f' % (
        path, len(tris), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

    out = []
    for ha, va, title in ((2, 1, '侧视 (z 横 / y 纵)'), (2, 0, '俯视 (z 横 / x 纵)'),
                          (0, 1, '后视 (x 横 / y 纵)')):
        cells = raster(tris, ha, va, res)
        hs = sorted(set(c[0] for c in cells))
        vs = sorted(set(c[1] for c in cells), reverse=True)
        out.append('== %s ==  %d x %d' % (title, len(hs), len(vs)))
        out.append('      ' + ''.join('%4.1f' % (h * res) for h in hs))
        for v in vs:
            out.append('%5.1f ' % (v * res) + ''.join(
                '  # ' if (h, v) in cells else '  . ' for h in hs))
    io.open(out_path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('written -> %s' % out_path)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
