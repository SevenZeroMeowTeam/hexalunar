#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minecraft 第一人称手持模型预览模拟器（无第三方依赖）。

复刻 MC 的物品渲染数学，用来在进游戏前核对"朝向 / 比例 / 位置"：

  1. 显示变换（模型 JSON 的 display 节点）
        v' = T + R(x,y,z) * S * (v_obj / 16)      # T 按 MC 规则除以 16（方块）
     其中旋转矩阵按 MC 的 compose 顺序：R = Rx * Ry * Rz（即先转 Z，再 Y，再 X）
  2. 手持偏移（ItemInHandRenderer.applyItemArmTransform）
        第一人称：右手 (+0.56, -0.52, -0.72) 方块；左手 x 取负
  3. 副手镜像：ItemRenderer 对 leftHand 会先 scale(-1, 1, 1)
  4. 相机：位于原点、朝 -Z 看，垂直 FOV 70°，默认 16:9

用法示例：
  python fp_preview.py --json akm.json --obj akm.obj --ctx firstperson_righthand --out fp_right.png
  python fp_preview.py --json akm.json --obj akm.obj --ctx firstperson_lefthand --arm left --mirror --out fp_offhand.png
  python fp_preview.py --json akm.json --obj akm.obj --ctx gui --out gui.png
"""
import argparse
import json
import math
import os
import struct
import zlib

FOV = 70.0          # 垂直视野
NEAR = 0.02         # 近平面（方块）


# ---------------------------------------------------------------- 数学工具
def matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
                 for i in range(3))


def apply(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


def rot_matrix(rx, ry, rz):
    """MC 的 display.rotation：R = Rx * Ry * Rz（先 Z，再 Y，最后 X）。"""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    mx = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    my = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    mz = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    return matmul(mx, matmul(my, mz))


# ---------------------------------------------------------------- 资源读取
def load_obj(path):
    verts, faces = [], []
    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            if line.startswith('v '):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith('f '):
                idx = []
                for tok in line.split()[1:]:
                    n = int(tok.split('/')[0])
                    idx.append(n - 1 if n > 0 else len(verts) + n)
                if len(idx) >= 3:
                    faces.append(idx)
    return verts, faces


def load_display(path, ctx):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    node = data.get('display', {}).get(ctx)
    if node is None:
        raise SystemExit('模型 %s 没有 display.%s' % (os.path.basename(path), ctx))
    rot = node.get('rotation', [0, 0, 0])
    tra = node.get('translation', [0, 0, 0])
    scl = node.get('scale', [1, 1, 1])
    return rot, tra, scl


# ---------------------------------------------------------------- 光栅化
def fill_triangle(img, zbuf, tri, color, w, h):
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = tri
    minx = max(int(min(x0, x1, x2)), 0)
    maxx = min(int(max(x0, x1, x2)) + 1, w - 1)
    miny = max(int(min(y0, y1, y2)), 0)
    maxy = min(int(max(y0, y1, y2)) + 1, h - 1)
    if minx > maxx or miny > maxy:
        return
    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(area) < 1e-9:
        return
    for py in range(miny, maxy + 1):
        for px in range(minx, maxx + 1):
            cx, cy = px + 0.5, py + 0.5
            w0 = (x1 - x0) * (cy - y0) - (cx - x0) * (y1 - y0)
            w1 = (x2 - x1) * (cy - y1) - (cx - x1) * (y2 - y1)
            w2 = (x0 - x2) * (cy - y2) - (cx - x2) * (y0 - y2)
            if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                l0, l1, l2 = w1 / area, w2 / area, w0 / area
                z = l0 * z0 + l1 * z1 + l2 * z2
                if z < zbuf[py][px]:
                    zbuf[py][px] = z
                    img[py][px] = color


def write_png(path, img, w, h):
    raw = b''.join(b'\x00' + bytes(v for px in row for v in px) for row in img)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))

    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 6))
           + chunk(b'IEND', b''))
    with open(path, 'wb') as fh:
        fh.write(png)


def draw_reference(img, w, h, label_points):
    """屏幕边框 + 中心准星 + 几个位置标记（下中 / 右下角）。"""
    def px(x, y, color):
        if 0 <= x < w and 0 <= y < h:
            img[y][x] = color

    for x in range(w):
        px(x, 0, (200, 200, 200))
        px(x, h - 1, (200, 200, 200))
    for y in range(h):
        px(0, y, (200, 200, 200))
        px(w - 1, y, (200, 200, 200))
    # 准星
    for d in range(-6, 7):
        px(w // 2 + d, h // 2, (170, 170, 170))
        px(w // 2, h // 2 + d, (170, 170, 170))
    # 参考标记
    for tx, ty, col in label_points:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                px(tx + dx, ty + dy, col)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', required=True)
    ap.add_argument('--obj', required=True)
    ap.add_argument('--ctx', default='firstperson_righthand')
    ap.add_argument('--arm', default='right', choices=['right', 'left'])
    ap.add_argument('--mirror', action='store_true', help='副手渲染时会做 scale(-1,1,1)')
    ap.add_argument('--out', default='preview.png')
    ap.add_argument('--w', type=int, default=854)
    ap.add_argument('--h', type=int, default=480)
    ap.add_argument('--rot', help='覆盖 rotation，如 0,30,0')
    ap.add_argument('--trans', help='覆盖 translation（JSON 单位），如 -10.4,3.3,1.2')
    ap.add_argument('--scale', type=float, help='覆盖 scale')
    args = ap.parse_args()

    verts, faces = load_obj(args.obj)
    rot, tra, scl = load_display(args.json, args.ctx)
    if args.rot:
        rot = [float(x) for x in args.rot.split(',')]
    if args.trans:
        tra = [float(x) for x in args.trans.split(',')]
    if args.scale is not None:
        scl = [args.scale] * 3
    rm = rot_matrix(*rot)

    hand = (0.56 if args.arm == 'right' else -0.56, -0.52, -0.72)
    if args.ctx.startswith('gui'):
        hand = (0.0, 0.0, 0.0)

    def to_camera(v):
        # 模型坐标已是【方块】单位（Forge OBJ 直接用 OBJ 坐标），只有 display 的 translation 要除以 16
        p = (v[0] * scl[0], v[1] * scl[1], v[2] * scl[2])
        p = apply(rm, p)
        p = (p[0] + tra[0] / 16.0, p[1] + tra[1] / 16.0, p[2] + tra[2] / 16.0)
        if args.mirror:
            p = (-p[0], p[1], p[2])
        return (p[0] + hand[0], p[1] + hand[1], p[2] + hand[2])

    cam = [to_camera(v) for v in verts]

    w, h = args.w, args.h
    bg = (238, 240, 244)
    img = [[bg] * w for _ in range(h)]
    zbuf = [[float('inf')] * w for _ in range(h)]

    gui = args.ctx.startswith('gui')
    tan_half = math.tan(math.radians(FOV) / 2.0)
    aspect = w / float(h)

    def project(p):
        if gui:                       # 物品栏图标：正交投影，格子 16 单位
            off = (-0.5, -0.5, -0.5)
            scale = min(w, h) / 16.0 * 0.45
            return (w / 2.0 + (p[0] + off[0]) * scale,
                    h / 2.0 - (p[1] + off[1]) * scale,
                    -(p[2] + off[2]))
        z = -p[2]
        ndc_x = (p[0] / z) / (tan_half * aspect)
        ndc_y = (p[1] / z) / tan_half
        return ((ndc_x + 1.0) * 0.5 * w, (1.0 - ndc_y) * 0.5 * h, z)

    drawn = 0
    for face in faces:
        pts = [cam[i] for i in face]
        if not gui and any(p[2] > -NEAR for p in pts):
            continue
        proj = [project(p) for p in pts]
        a, b, c = pts[0], pts[min(1, len(pts) - 1)], pts[min(2, len(pts) - 1)]
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * v2[2] - u[2] * v2[1],
             u[2] * v2[0] - u[0] * v2[2],
             u[0] * v2[1] - u[1] * v2[0])
        ln = math.sqrt(sum(k * k for k in n)) or 1.0
        n = (n[0] / ln, n[1] / ln, n[2] / ln)
        lit = 0.45 + 0.55 * abs(n[2])          # 朝镜头稍亮
        color = (int(96 * lit), int(134 * lit), int(72 * lit))
        for k in range(1, len(proj) - 1):
            fill_triangle(img, zbuf, [proj[0], proj[k], proj[k + 1]], color, w, h)
        drawn += 1

    # 位置统计：画面上可见部分的包围盒（像素）
    xs, ys = [], []
    for face in faces:
        pts = [cam[i] for i in face]
        if any(p[2] > -NEAR for p in pts):
            continue
        for p in pts:
            sx, sy, _ = project(p)
            if -2000 < sx < w + 2000:
                xs.append(sx)
                ys.append(sy)

    draw_reference(img, w, h, [(w // 2, h - 1, (60, 120, 220)),
                               (w - 1, h // 2, (60, 120, 220))])
    write_png(args.out, img, w, h)

    if xs:
        cxs = [p[0] for p in cam if p[2] < -NEAR]
        cys = [p[1] for p in cam if p[2] < -NEAR]
        czs = [p[2] for p in cam if p[2] < -NEAR]
        print('ctx=%s arm=%s mirror=%s rot=%s trans=%s scale=%s'
              % (args.ctx, args.arm, args.mirror, rot, tra, scl))
        print('  faces drawn = %d' % drawn)
        if czs:
            print('  相机空间(方块) x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f'
                  % (min(cxs), max(cxs), min(cys), max(cys), min(czs), max(czs)))
        print('  屏幕像素包围盒: x %.0f..%.0f   y %.0f..%.0f  (画布 %dx%d)'
              % (min(xs), max(xs), min(ys), max(ys), w, h))
        print('  可见性: %s' % ('可见' if (min(xs) < w and max(xs) > 0
                                        and min(ys) < h and max(ys) > 0) else '不可见'))
    print('  -> %s' % args.out)


if __name__ == '__main__':
    main()
