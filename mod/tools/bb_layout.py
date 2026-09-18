#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 bbmodel 网格绕 Y 轴旋转到长轴对齐 +Z，再沿轴分箱统计，得到真实部件的布局与比例。

用法: python tools/bb_layout.py <model.bbmodel> [yaw_deg]
输出：对齐后的包围盒 + 沿 +Z 分 20 箱的 X/Y 范围（可看清哪儿是弓臂、哪儿是枪托/握把/镜子）
"""
import json
import math
import sys


def load_verts(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    el = data['elements'][0]
    verts = list(el['vertices'].values())
    faces = el.get('faces') or {}
    return verts, faces


def yaw_of(verts):
    n = len(verts)
    mx = sum(v[0] for v in verts) / n
    mz = sum(v[2] for v in verts) / n
    sxx = sxz = szz = 0.0
    for v in verts:
        dx = v[0] - mx
        dz = v[2] - mz
        sxx += dx * dx
        sxz += dx * dz
        szz += dz * dz
    # 主轴 = 最大特征值方向（与 bb_axis_check 的 PCA 等价）
    tr = sxx + szz
    det = sxx * szz - sxz * sxz
    l1 = tr / 2 + math.sqrt(max(0.0, tr * tr / 4 - det))
    if abs(sxz) < 1e-9:
        ang = 0.0 if sxx >= szz else 90.0
    else:
        ang = math.degrees(math.atan2(l1 - sxx, sxz))
    return ang


def main(path, yaw=None):
    verts, faces = load_verts(path)
    if yaw is None:
        yaw = yaw_of(verts)
    else:
        yaw = float(yaw)
    a = math.radians(-yaw)  # 反向旋转，使长轴落到 +Z
    ca, sa = math.cos(a), math.sin(a)
    rot = []
    for x, y, z in verts:
        rot.append((x * ca + z * sa, y, -x * sa + z * ca))
    lo = [min(v[i] for v in rot) for i in range(3)]
    hi = [max(v[i] for v in rot) for i in range(3)]
    print('yaw used = %.3f deg (把网格转正的角度)' % yaw)
    print('aligned bbox min=[%.3f, %.3f, %.3f] max=[%.3f, %.3f, %.3f]' % (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))
    print('size: X=%.3f  Y=%.3f  Z=%.3f  (16 单位 = 1 方块)' % (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    bins = 20
    step = (hi[2] - lo[2]) / bins
    print('%-4s %-14s %6s %9s %9s %9s %9s' % ('bin', 'Z range', 'verts', 'X min', 'X max', 'Y min', 'Y max'))
    for b in range(bins):
        z0 = lo[2] + b * step
        z1 = z0 + step
        sel = [v for v in rot if (z0 <= v[2] < z1) or (b == bins - 1 and v[2] >= z1)]
        if not sel:
            print('%-4d %-14s %6d' % (b, '%.2f..%.2f' % (z0, z1), 0))
            continue
        print('%-4d %-14s %6d %9.2f %9.2f %9.2f %9.2f' % (
            b, '%.2f..%.2f' % (z0, z1), len(sel),
            min(v[0] for v in sel), max(v[0] for v in sel),
            min(v[1] for v in sel), max(v[1] for v in sel)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
