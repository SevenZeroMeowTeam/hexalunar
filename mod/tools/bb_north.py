#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析 / 转正 bbmodel：让模型的「前方(枪口)」指向 -Z（北），上方向朝 +Y。

Blockbench 里 N = -Z。已有的几个旧模型是「MC 剑式斜置」（长轴斜在 Y-Z 平面里），
所以要先算出主轴，再整体旋转到 -Z。

用法:
  python tools/bb_north.py --info  <a.bbmodel> [...]            # 只看分析
  python tools/bb_north.py --apply --front pz <a.bbmodel> ...   # 转正并保存（自动备份）
      --front 指定「前端现在在哪个方向」，取值: pz/nz/py/ny/px/nx (正/负 X/Y/Z)
      --out-suffix ''（默认原地覆盖，备份到 build/backup_bbmodel_north/）
"""
import json
import math
import os
import shutil
import sys

BACKUP = 'build/backup_bbmodel_north'


# ---------- 向量/矩阵 ----------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    n = math.sqrt(dot(a, a))
    return mul(a, 1.0 / n) if n > 1e-12 else (0.0, 0.0, 0.0)


def mat_from_cols(c0, c1, c2):
    return [[c0[0], c1[0], c2[0]], [c0[1], c1[1], c2[1]], [c0[2], c1[2], c2[2]]]


def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_t(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]


def mat_vec(A, v):
    return (A[0][0] * v[0] + A[0][1] * v[1] + A[0][2] * v[2],
            A[1][0] * v[0] + A[1][1] * v[1] + A[1][2] * v[2],
            A[2][0] * v[0] + A[2][1] * v[1] + A[2][2] * v[2])


def mat_id():
    return [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]


def rot_axis(axis, deg):
    x, y, z = norm(axis)
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    t = 1 - c
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


# ---------- bbmodel ----------
def load(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def elem_local_to_world(el, v):
    """元素局部坐标 -> 工程坐标（元素自身 rotation 绕 origin）。"""
    r = el.get('rotation') or [0, 0, 0]
    if not any(abs(x) > 1e-9 for x in r):
        return v
    o = el.get('origin') or [0, 0, 0]
    M = mat_id()
    # Blockbench 元素旋转顺序: Z, Y, X（各自绕原轴）
    for axis, deg in (((0, 0, 1), r[2]), ((0, 1, 0), r[1]), ((1, 0, 0), r[0])):
        M = mat_mul(M, rot_axis(axis, deg))
    return add(o, mat_vec(M, sub(v, o)))


def world_verts(data):
    out = []
    for el in data.get('elements', []):
        for v in el.get('vertices', {}).values():
            out.append((el, tuple(v)))
    return out


def principal_axis(pts):
    """粗到细搜索最大方差方向。"""
    vs = [mat_vec(mat_from_cols((1, 0, 0), (0, 1, 0), (0, 0, 1)), p) for p in pts]
    best = (None, -1.0)
    step = 6
    while step >= 0.05:
        if best[0] is None:
            cand = []
            for i in range(int(180 / step) + 1):
                th = math.radians(i * step)
                for j in range(int(360 / step)):
                    ph = math.radians(j * step)
                    cand.append((math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)))
        else:
            b = best[0]
            cand = []
            # 在 best 附近用轴角扰动
            tmp = (0, 1, 0) if abs(b[1]) < 0.9 else (1, 0, 0)
            t1 = norm(cross(b, tmp))
            t2 = norm(cross(b, t1))
            for di in range(-4, 5):
                for dj in range(-4, 5):
                    dd = add(mul(t1, di * step), mul(t2, dj * step))
                    cand.append(norm(add(b, dd)))
        for d in cand:
            var = sum(dot(d, p) ** 2 for p in vs) / len(vs) - (sum(dot(d, p) for p in vs) / len(vs)) ** 2
            if var > best[1]:
                best = (d, var)
        step /= 5.0
    u = best[0]
    # 主轴符号统一：让 +Y 分量为正（前端符号由 --front 决定，不在这里猜）
    if u[1] < 0 and abs(u[1]) > 1e-9:
        pass
    return u


DIRS = {'px': (1, 0, 0), 'nx': (-1, 0, 0), 'py': (0, 1, 0), 'ny': (0, -1, 0),
        'pz': (0, 0, 1), 'nz': (0, 0, -1)}


def build_rot(u_front, up_ref=(0, 1, 0)):
    """返回把 u_front 转到 -Z、up_ref 转到尽量 +Y 的旋转矩阵。"""
    u = norm(u_front)
    w = sub(up_ref, mul(u, dot(up_ref, u)))
    if math.sqrt(dot(w, w)) < 0.15:          # 主轴几乎平行参考上方向
        alt = (1, 0, 0) if abs(u[0]) < 0.9 else (0, 0, 1)
        w = sub(alt, mul(u, dot(alt, u)))
    w = norm(w)
    s = cross(u, w)                          # u x w = s（右手系）
    M_src = mat_from_cols(u, w, s)
    M_dst = mat_from_cols((0, 0, -1), (0, 1, 0), (1, 0, 0))
    return mat_mul(M_dst, mat_t(M_src))


def apply_rot(data, R):
    """把工程坐标系整体旋转 R（绕原点）。返回被改动过的元素数。"""
    n = 0
    for el in data.get('elements', []):
        r = el.get('rotation') or [0, 0, 0]
        o = tuple(el.get('origin') or [0, 0, 0])
        if any(abs(x) > 1e-9 for x in r):
            M = mat_id()
            for axis, deg in (((0, 0, 1), r[2]), ((0, 1, 0), r[1]), ((1, 0, 0), r[0])):
                M = mat_mul(M, rot_axis(axis, deg))
            for k, v in el['vertices'].items():
                world = add(o, mat_vec(M, sub(tuple(v), o)))
                el['vertices'][k] = list(mat_vec(R, world))
            n += 1
        else:
            for k, v in el['vertices'].items():
                el['vertices'][k] = list(mat_vec(R, tuple(v)))
            n += 1
    return n


def info(path):
    data = load(path)
    els = data.get('elements', [])
    raw = []
    for el, v in world_verts(data):
        raw.append(elem_local_to_world(el, v))
    xs = [p[0] for p in raw]
    ys = [p[1] for p in raw]
    zs = [p[2] for p in raw]
    u = principal_axis(raw)
    if u[1] < 0:
        pass
    ang = math.degrees(math.acos(max(-1.0, min(1.0, dot(norm(u), (0, 0, 1))))))
    angn = math.degrees(math.acos(max(-1.0, min(1.0, dot(norm(u), (0, 0, -1))))))
    print('%-16s els=%2d  元素rotation=%s' % (os.path.basename(path), len(els),
                                              [el.get('rotation') for el in els[:3]]))
    print('     bbox  X[%.2f..%.2f] Y[%.2f..%.2f] Z[%.2f..%.2f]  (%.2f x %.2f x %.2f)'
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    print('     主轴 u=(%+.3f, %+.3f, %+.3f)  与 +Z 夹角 %.2f°  与 -Z 夹角 %.2f°'
          % (u[0], u[1], u[2], ang, angn))
    return u


def main(argv):
    mode = '--info' if '--info' in argv else ('--apply' if '--apply' in argv else None)
    if mode is None:
        print(__doc__)
        return 2
    front = None
    if '--front' in argv:
        front = DIRS[argv[argv.index('--front') + 1]]
    paths = [a for a in argv[1:] if a.endswith('.bbmodel')]
    for p in paths:
        u = info(p)
        if mode == '--apply':
            if front is None:
                print('    (需要 --front 指明前端方向，跳过)')
                continue
            # 主轴符号按 --front 方向取：与 front 同侧的那一端
            uu = u if dot(u, front) >= 0 else mul(u, -1.0)
            R = build_rot(uu)
            data = load(p)
            n = apply_rot(data, R)
            if not os.path.isdir(BACKUP):
                os.makedirs(BACKUP)
            bak = os.path.join(BACKUP, os.path.basename(p))
            if not os.path.exists(bak):
                shutil.copy2(p, bak)
            with open(p, 'w', encoding='utf-8') as fh:
                json.dump(data, fh, ensure_ascii=False)
            print('    -> 已转正（%d 个元素），备份 %s' % (n, bak))
            info(p)
        print('')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
