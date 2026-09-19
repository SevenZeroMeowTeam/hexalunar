# -*- coding: utf-8 -*-
"""把 geo + 基岩版/GeckoLib 动画在若干时刻的姿态烘焙成静态 geo，再调 geo_texview 出图。

用法:
  python tools\\_awpanim.py <geo.json> <anim.json> <animation_name> <t1,t2,...>
         [--yaw 90] [--pitch 0] [--zoom 1.15] [--prefix build\\_anim]

姿态规则与基岩版一致（父骨骼依次叠加）：
    p' = pivot + pos + R(rot) · (S · (p − pivot))
烘焙方式：旋转写到骨骼的 `rotation`（geo_texview 会按 pivot 合成父子链）；
平移把该骨骼**及其后代**的方块整体挪走；缩放按 pivot 缩放方块的 origin/size，
缩到 0 的方块直接丢掉（= 基岩版用 scale 0 表示“看不见”）。
"""
import copy
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_texview   # noqa: E402


def rot_mat(deg):
    rx, ry, rz = (math.radians(float(d)) for d in deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return [
        [cy * cz, cz * sx * sy - cx * sz, cx * cz * sy + sx * sz],
        [cy * sz, cx * cz + sx * sy * sz, -cz * sx + cx * sy * sz],
        [-sy, cy * sx, cx * cy],
    ]


def mv(R, v):
    return [sum(R[i][j] * v[j] for j in range(3)) for i in range(3)]


def add(a, b):
    return [a[i] + b[i] for i in range(3)]


def mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


ZERO = {'rot': [0, 0, 0], 'pos': [0, 0, 0], 'scale': [1, 1, 1]}


def sample(chan, t):
    """线性插值一条通道；单关键帧 = 常量。"""
    if not chan:
        return None
    keys = sorted((float(k), v) for k, v in chan.items())
    if t <= keys[0][0]:
        return list(keys[0][1])
    if t >= keys[-1][0]:
        return list(keys[-1][1])
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return [v0[i] + (v1[i] - v0[i]) * f for i in range(3)]
    return list(keys[-1][1])


def pose_of(anim, t):
    out = {}
    for bone, ch in (anim.get('bones') or {}).items():
        out[bone] = {
            'rot': sample(ch.get('rotation'), t) or [0, 0, 0],
            'pos': sample(ch.get('position'), t) or [0, 0, 0],
            'scale': sample(ch.get('scale'), t) or [1, 1, 1],
        }
    return out


def bake(geo, pose):
    """把姿态烘焙进 geo 的副本（geo_texview 只认 pivot + rotation，其余自己算）。"""
    g = copy.deepcopy(geo)['minecraft:geometry'][0]
    by_name = {b['name']: b for b in g['bones']}

    shift_cache = {}

    def acc(bone):
        """返回 (位移累加, 从根到该骨骼的旋转矩阵) —— 骨骼的 pos 在**父级坐标系**里，
        所以要乘上从根到父级的旋转才换算成世界位移。"""
        if bone['name'] in shift_cache:
            return shift_cache[bone['name']]
        pv = pose.get(bone['name']) or ZERO
        R = rot_mat(pv['rot'])
        p = bone.get('parent')
        if p and p in by_name:
            sp, Rp = acc(by_name[p])
            res = (add(sp, mv(Rp, pv['pos'])), mul(Rp, R))
        else:
            res = (list(pv['pos']), R)
        shift_cache[bone['name']] = res
        return res

    for b in g['bones']:
        pv = pose.get(b['name']) or ZERO
        piv = [float(v) for v in b.get('pivot', [0, 0, 0])]
        off = acc(b)[0]
        scl = pv['scale']
        keep = []
        for c in b.get('cubes', []):
            o = [float(v) for v in c['origin']]
            s = [float(v) for v in c['size']]
            if min(abs(x) for x in scl) < 1e-4:
                continue                      # scale 0 = 隐藏
            n = copy.deepcopy(c)
            n['origin'] = [round(piv[i] + (o[i] - piv[i]) * scl[i] + off[i], 4) for i in range(3)]
            n['size'] = [round(s[i] * scl[i], 4) for i in range(3)]
            keep.append(n)
        b['cubes'] = keep
        if any(abs(v) > 1e-6 for v in pv['rot']):
            b['rotation'] = [float(v) for v in pv['rot']]
    # pivot 跟着**祖先**的位移走（父级动了，子的旋转中心也得动）
    for b in g['bones']:
        piv = [float(v) for v in b.get('pivot', [0, 0, 0])]
        p = b.get('parent')
        off = acc(by_name[p])[0] if (p and p in by_name) else [0.0, 0.0, 0.0]
        b['pivot'] = [round(piv[i] + off[i], 4) for i in range(3)]
    return {'format_version': geo.get('format_version', '1.12.0'), 'minecraft:geometry': [g]}


def main(argv):
    geo_path, anim_path, aname = argv[1], argv[2], argv[3]
    times = [float(x) for x in argv[4].split(',')]

    def opt(n, dv):
        return float(argv[argv.index(n) + 1]) if n in argv else dv

    yaw, pitch = opt('--yaw', -90.0), opt('--pitch', 0.0)
    zoom = opt('--zoom', 1.15)
    prefix = argv[argv.index('--prefix') + 1] if '--prefix' in argv else os.path.join(
        os.path.dirname(geo_path), '_anim')

    geo = json.load(open(geo_path, encoding='utf-8'))
    anim = json.load(open(anim_path, encoding='utf-8'))['animations'][aname]
    tex_path = geo_path.replace('.geo.json', '.png')

    print('动画 %s  时长 %s  loop=%s' % (aname, anim.get('animation_length'), anim.get('loop')))
    for t in times:
        pose = pose_of(anim, t)
        posed = bake(geo, pose)
        tmp = os.path.join(os.path.dirname(geo_path), '_pose_%0.2f.geo.json' % t)
        json.dump(posed, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
        out = '%s_%0.2f.png' % (prefix, t)
        geo_texview.render(tmp, tex_path, out, yaw=yaw, pitch=pitch, zoom=zoom)
        cs = pose.get('casing')
        bt = pose.get('bolt')
        if cs:
            print('   t=%.2f  弹壳 rot=%s pos=%s scale=%s | 枪机 pos=%s'
                  % (t, [round(v) for v in cs['rot']], [round(v, 2) for v in cs['pos']],
                     [round(v, 2) for v in cs['scale']],
                     [round(v, 2) for v in (bt['pos'] if bt else [0, 0, 0])]))


if __name__ == '__main__':
    main(sys.argv)
