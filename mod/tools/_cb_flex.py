# -*- coding: utf-8 -*-
"""r63：十字弩「拉弦时弓臂向内收缩」的离线验算 + 姿态烘焙。

跑法：
    python tools/_cb_flex.py                # 只打印数值自检
    python tools/_cb_flex.py --bake 1.0     # 再烘焙 build/cb_flex_1p0.geo.json（给 geo_texview 出图）

坐标：模型像素，弩头朝 -Z。右弓臂是「内端 (1.3, z-8.6) → 外端 (3.5, z-4.6)」的斜杆，
所以绕**内端（贴导轨那头）转负角**时外端往 −x（向内）+z（向后）走 —— 正是「向内收缩」。

Java 侧同一份数学在 client/CrossbowGeoModel.flexLimb()，常数必须一致（FLEX_DEG / FLEX_PX / FLEX_PZ）。
★ GeckoLib 的骨骼变换 = pivot + pos + R(rot)·(p − pivot)：
  · 绕任意点 P 转 ⇒ pos = (P − pivot) − R·(P − pivot)
  · 整段平移 δ   ⇒ pos = δ
★ 预览器 geo_texview 只认「pivot + rotation」，没有 pos 通道，所以 bake() 用
  「弓臂把 pivot 挪到弯折支点、方块不动」「弦/凸轮把方块与 pivot 一起平移」来等价表达。
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(HERE, '..', 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'geo', 'crossbow_geo.geo.json')

# ---- 与 CrossbowGeoModel 必须一致的常数 --------------------------------------
TIP_X = 2.62           # 弦心到弓臂锚点的横向距离（生成器 TIP_X）
DRAW_DZ = 1.80         # 拉满时弦心后退距离（生成器 DRAW_DZ）
NOCK_Z0 = -5.20        # 弦面中心的 z（生成器 NOCK_Z0）
STRING_LEN = 3.18      # 弦段方块长度（生成器按 hypot(2.62,1.80)=3.179 生成）
FLEX_DEG = 9.0         # ★ 拉满时弓臂内收角（度）
FLEX_PX = 1.50         # 弓臂弯折支点 x = 贴导轨内端的中心
FLEX_PZ = -8.60        # 弓臂弯折支点 z = 最前端
CAM_Z = -5.20          # cam / 弦锚点的 z（= 这两个骨骼 pivot 的 z）
NOCK_HALF_X = 0.60     # 弦心方块半宽（判据用）
NOCK_HALF_Z = 0.26     # 弦心方块半深


def load(path=GEO):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def bone_map(geo):
    return {b['name']: b for b in geo['minecraft:geometry'][0]['bones']}


def roty(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return lambda x, z: (x * c + z * s, -x * s + z * c)


def rot_about(pivot, p, deg):
    """点 (x,z) 绕 pivot 转 deg（绕 Y 轴）→ 新坐标"""
    r = roty(deg)
    x, z = r(p[0] - pivot[0], p[1] - pivot[1])
    return (x + pivot[0], z + pivot[1])


def disp_about(pivot, p, deg):
    """绕 pivot 转 deg 的位移（新 − 旧）"""
    n = rot_about(pivot, p, deg)
    return (n[0] - p[0], n[1] - p[1])


def limb_extents(name, side):
    b = bone_map(load())[name]

    def xr(c):
        a = c['origin'][0]
        return (min(a, a + c['size'][0]), max(a, a + c['size'][0]))

    xs = [xr(c) for c in b['cubes']]
    zs = [(c['origin'][2], c['origin'][2] + c['size'][2]) for c in b['cubes']]
    inn = min(a for a, _ in xs) if side > 0 else max(bb for _, bb in xs)
    out = max(bb for _, bb in xs) if side > 0 else min(a for a, _ in xs)
    # 取「最外那一列」方块的 z 中心，当作「外端」
    if side > 0:
        far = [c for c in b['cubes'] if xr(c)[1] >= out - 0.3]
    else:
        far = [c for c in b['cubes'] if xr(c)[0] <= out + 0.3]
    outer = (out + (0.225 if side > 0 else -0.225),
             sum(c['origin'][2] + c['size'][2] / 2.0 for c in far) / len(far))
    return inn, out, min(a for a, _ in zs), max(bb for _, bb in zs), outer


def sign_theta(draw, side):
    return -side * FLEX_DEG * draw


def check():
    print('常数 FLEX_DEG=%.1f  TIP_X=%.2f  DRAW_DZ=%.2f  NOCK_Z0=%.2f  L=%.3f'
          % (FLEX_DEG, TIP_X, DRAW_DZ, NOCK_Z0, STRING_LEN))
    for name, side, piv in (('prod_right', 1, (FLEX_PX, FLEX_PZ)),
                            ('prod_left', -1, (-FLEX_PX, FLEX_PZ))):
        inn, out, z0, z1, outer = limb_extents(name, side)
        print('== %-11s 支点=(%+.2f,%+.2f)  方块 x[%.2f,%.2f] z[%.2f,%.2f] 外端≈(%+.2f,%+.2f)'
              % (name, piv[0], piv[1], inn, out, z0, z1, outer[0], outer[1]))
        for draw in (0.5, 1.0):
            th = sign_theta(draw, side)
            do = disp_about(piv, outer, th)
            print('   draw=%.1f θ=%+5.2f°  外端 (%+.2f,%+.2f) → (%+.2f,%+.2f)  Δ=(%+.2f,%+.2f) %s'
                  % (draw, th, outer[0], outer[1], outer[0] + do[0], outer[1] + do[1],
                     do[0], do[1], '向内 OK' if do[0] * side < 0 else '向外 BAD'))
    print('== 弦锚点 / 弦内端（弦心 = (0, NOCK_Z0 + draw·DRAW_DZ)）')
    print('   draw |  θ(右)  | 锚点Δ=(dx,dz)   | 弦内端         | 弦心        | 偏差')
    for draw in (0.0, 0.5, 1.0):
        th = sign_theta(draw, 1)
        a = (TIP_X, CAM_Z)
        d = disp_about((FLEX_PX, FLEX_PZ), a, th)
        phi = draw * math.degrees(math.atan2(DRAW_DZ, TIP_X))
        # 游戏里的弦内端 = (锚点 pivot + 平移 δ) + R(φ)·(−L, 0)
        r = roty(phi)
        off = r(-STRING_LEN, 0.0)
        e = (a[0] + d[0] + off[0], a[1] + d[1] + off[1])
        nz = NOCK_Z0 + draw * DRAW_DZ
        flag = '  OK' if abs(e[0]) <= 0.75 and abs(e[1] - nz) <= NOCK_HALF_Z else '  BAD'
        print('   %.1f  | %+5.2f° | (%+.2f,%+.2f) | (%+.2f,%+.2f) | (0.00,%+.2f) | (%.2f,%.2f)%s'
              % (draw, th, d[0], d[1], e[0], e[1], nz, e[0], e[1] - nz, flag))
    print('★ 判据：两段弦在弦心附近要**交叠**（|x| ≤ 0.75，本身就是刻意的搭接）且不落在弦心方块外（|z| ≤ %.2f）'
          % NOCK_HALF_Z)
    a = os.path.join(HERE, '..', 'build', 'cb_flex_0p0.geo.json')
    b = os.path.join(HERE, '..', 'build', 'cb_flex_1p0.geo.json')
    if os.path.exists(a) and os.path.exists(b):
        sa, sb = span(a), span(b)
        print('== 整体宽度（弓臂外缘，模型像素）：draw=0 → %.2f，draw=1 → %.2f（收 %.2f，%.0f%%）'
              % (sa * 2, sb * 2, (sa - sb) * 2, (sa - sb) / sa * 100.0))


def span(path):
    """按预览器（geo_texview.rot_mat）的约定量「弓臂外缘」的最大 |x|"""
    sys.path.insert(0, HERE)
    import geo_texview as gv
    mx = 0.0
    for bone in load(path)['minecraft:geometry'][0]['bones']:
        piv = bone.get('pivot', [0, 0, 0])
        M = gv.rot_mat(bone['rotation']) if bone.get('rotation') else None
        for c in bone.get('cubes', []):
            o, s = c['origin'], c['size']
            for k in range(8):
                p = [o[i] + (s[i] if (k >> i) & 1 else 0) for i in range(3)]
                if M is not None:
                    d = [p[i] - piv[i] for i in range(3)]
                    p = [sum(M[i][j] * d[j] for j in range(3)) + piv[i] for i in range(3)]
                mx = max(mx, abs(p[0]))
    return mx


def bake(draw, out=None):
    """把 draw 姿态烘焙成一份 geo，给 geo_texview.py 出图。

    预览器只认「pivot + rotation（绕 pivot）」，没有 GeckoLib 的 pos（平移）通道，所以：
      · 弓臂：把 pivot 挪到弯折支点、方块不动 + rotation ⇒ 等价于「绕支点转」
      · 弦 / 凸轮 / 弦心 / 弩箭：方块与 pivot 一起平移 +（弦还需）rotation
    """
    geo = load()
    bs = bone_map(geo)
    phi = draw * math.degrees(math.atan2(DRAW_DZ, TIP_X))
    pivots = {}
    shifts = {}
    rots = {}
    for side, limb, cam, string in ((1, 'prod_right', 'cam_right', 'string_right'),
                                    (-1, 'prod_left', 'cam_left', 'string_left')):
        piv = (FLEX_PX * side, FLEX_PZ)
        th = sign_theta(draw, side)
        pivots[limb] = (piv[0], bs[limb]['pivot'][1], piv[1], th)
        a = (TIP_X * side, CAM_Z)
        d = disp_about(piv, a, th)
        shifts[cam] = (d[0], 0.0, d[1])
        shifts[string] = (d[0], 0.0, d[1])
        rots[string] = (0.0, -side * phi, 0.0)
    shifts['nock'] = (0.0, 0.0, draw * DRAW_DZ)
    shifts['bolt'] = (0.0, 0.0, draw * DRAW_DZ)

    for b in geo['minecraft:geometry'][0]['bones']:
        name = b['name']
        if name in pivots:
            px, py, pz, th = pivots[name]
            b['pivot'] = [round(px, 4), round(py, 4), round(pz, 4)]
            b['rotation'] = [0.0, round(th, 4), 0.0]
            continue
        d = shifts.get(name)
        if d is not None:
            b['pivot'] = [round(b['pivot'][0] + d[0], 4), round(b['pivot'][1] + d[1], 4),
                          round(b['pivot'][2] + d[2], 4)]
            for c in b.get('cubes', []):
                c['origin'] = [round(c['origin'][0] + d[0], 4), round(c['origin'][1] + d[1], 4),
                               round(c['origin'][2] + d[2], 4)]
        r = rots.get(name)
        if r and any(abs(v) > 1e-9 for v in r):
            b['rotation'] = [round(v, 4) for v in r]
    out = out or os.path.join(HERE, '..', 'build',
                              'cb_flex_%s.geo.json' % str(draw).replace('.', 'p'))
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, separators=(',', ':'))
    print('wrote', out)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument('--bake', type=float, default=None, help='烘焙该 draw 的姿态')
    a = ap.parse_args()
    check()
    if a.bake is not None:
        bake(a.bake)


if __name__ == '__main__':
    main()
