#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按模型网格的朝向变化，重算物品模型 json 里 display 的旋转，保证游戏内姿态不变。

模型网格从 R_y(φ_old) 变到 R_y(φ_new) 时（φ = 工程系里相对 +Z 的偏航），
display 旋转要右乘 R_y(φ_old - φ_new)：R_new = R_old · R_y(φ_old - φ_new)。

MC 的 display 旋转按 Rx(rx)·Ry(ry)·Rz(rz) 作用；当 rz = 0 时等价于 ry += delta。
rz ≠ 0 时用完整矩阵分解。

用法:
  python tools/retarget_display.py --delta -208.5 <item.json> [more.json ...]
  python tools/retarget_display.py --delta -208.5 --dry <...>
"""
import json
import math
import os
import shutil
import sys


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def decompose(m):
    """把旋转矩阵拆成 Rx(rx)·Ry(ry)·Rz(rz)（度）——MC 的 display 就是按这个顺序作用。"""
    sb = max(-1.0, min(1.0, m[0][2]))
    ry = math.asin(sb)
    cb = math.cos(ry)
    if abs(cb) > 1e-6:
        rx = math.atan2(-m[1][2], m[2][2])
        rz = math.atan2(-m[0][1], m[0][0])
    else:
        rx = math.atan2(m[2][1], m[1][1])
        rz = 0.0
    return [math.degrees(rx), math.degrees(ry), math.degrees(rz)]


def norm(a):
    a = ((a + 180) % 360) - 180
    return 0.0 if abs(a) < 1e-9 else round(a, 3)


def close(a, b, eps=1e-6):
    return all(abs(a[i][j] - b[i][j]) < eps for i in range(3) for j in range(3))


def retarget(path, delta, dry=False, scale=1.0):
    with open(path, 'r', encoding='utf-8') as fh:
        spec = json.load(fh)
    disp = spec.get('display') or {}
    changed = []
    for slot, v in disp.items():
        rot = v.get('rotation') or [0, 0, 0]
        rx, ry, rz = (math.radians(a) for a in rot)
        r_old = mat_mul(mat_mul(rot_x(rx), rot_y(ry)), rot_z(rz))
        r_new = mat_mul(r_old, rot_y(math.radians(delta)))
        nr = [norm(x) for x in decompose(r_new)]
        # 能用“单纯绕 Y 转”或“单纯绕 X 转”表示时，取更好读的形式
        beta = math.degrees(math.atan2(r_new[0][2], r_new[2][2]))
        if close(r_new, rot_y(math.radians(beta))):
            nr = [0.0, norm(beta), 0.0]
        else:
            alpha = math.degrees(math.atan2(r_new[2][1], r_new[1][1]))
            if close(r_new, rot_x(math.radians(alpha))):
                nr = [norm(alpha), 0.0, 0.0]
        sc = v.get('scale')
        nsc = None
        if sc and abs(scale - 1.0) > 1e-9:
            nsc = [round(s * scale, 4) for s in sc]
            v['scale'] = nsc
        if nr != [norm(x) for x in rot] or nsc:
            changed.append((slot, rot, nr, sc, nsc))
            v['rotation'] = nr
    print('%s  改动 %d 个 slot%s' % (os.path.basename(path), len(changed),
                                    '' if abs(scale - 1.0) < 1e-9 else '  缩放 x%.3f' % scale))
    for slot, old, new, sc, nsc in changed:
        if sc and nsc:
            print('   %-22s rot %s -> %s   scale %s -> %s' % (slot, old, new, sc, nsc))
        else:
            print('   %-22s rot %s -> %s' % (slot, old, new))
    if dry:
        return
    if os.path.exists(path) and not os.path.exists(path + '.dispbak'):
        shutil.copy2(path, path + '.dispbak')
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(spec, fh, indent=1, ensure_ascii=False)
        fh.write('\n')


if __name__ == '__main__':
    args = sys.argv[1:]
    dry = '--dry' in args
    args = [a for a in args if a != '--dry']
    scale = float(args[args.index('--scale') + 1]) if '--scale' in args else 1.0
    if '--scale' in args:
        i = args.index('--scale')
        args = args[:i] + args[i + 2:]
    delta = float(args[args.index('--delta') + 1])
    files = args[args.index('--delta') + 2:]
    for f in files:
        retarget(f, delta, dry, scale)
