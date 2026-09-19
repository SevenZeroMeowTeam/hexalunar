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
TIP_X = 5.371          # 弦心到弓臂锚点的横向距离（生成器 TIP_X；r69 弓臂放大 2.05 倍后）
DRAW_DZ = 1.80         # 拉满时弦心后退距离（生成器 DRAW_DZ）
NOCK_Z0 = -5.20        # 弦面中心的 z（生成器 NOCK_Z0）
STRING_LEN = 6.221     # 弦段方块长度（= geo 里 string_left/right 的真实长度：5.371 + 0.85）
FLEX_DEG = 13.0        # ★ r85：8 → 13（弓臂内收更多 ⇒ 固定长度的弦能拉成深 V）
FLEX_BACK = 0.35       # ★ 拉满时两弓臂整体往射手方向滑的量（模型像素；只靠转的话外端主要只往内走）
FLEX_PX = 1.599        # 弓臂弯折支点 x = 贴导轨内端的中心（生成器打印）
FLEX_PZ = -8.697       # 弓臂弯折支点 z = 最前端（生成器打印）
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


def flex_disp(pivot, p, side, draw):
    """弓臂上一个点（相对支点）在 draw 下的总位移 = 绕支点转 + 整体后滑"""
    d = disp_about(pivot, p, sign_theta(draw, side))
    return (d[0], d[1] + draw * FLEX_BACK)


def string_phi(flex):
    """弦两段绕锚点的转角（弧度）：**由几何解出来**（与 Java 的 CrossbowGeoModel.stringPhi 同一份）。

    弦段长度固定，弓臂内收后锚点横向距离变成 x = TIP_X + δx ⇒ 能拉到的最深处
    depth = √(L² − x²)，转角 φ = atan2(depth, x)。
    """
    d = flex_disp((FLEX_PX, FLEX_PZ), (TIP_X, CAM_Z), 1, flex)
    x = TIP_X + d[0]
    depth = math.sqrt(max(0.0, STRING_LEN * STRING_LEN - x * x))
    return math.atan2(depth, x)


def nock_travel(flex, draw):
    """弦心相对初始的后退量 —— 与 Java 的 CrossbowGeoModel.nockTravel(flexAmt, draw) 同一份：
    锚点被弓臂带走的 z 位移（弓臂内收 flex）+ 弦绷直所需的后退（弦长固定，draw）。"""
    d = flex_disp((FLEX_PX, FLEX_PZ), (TIP_X, CAM_Z), 1, flex)
    return d[1] + STRING_LEN * math.sin(draw * string_phi(flex))


def nock_z(draw, flex=None):
    """弦心 z（flex 缺省 = 与 draw 同步；上膛时传 flex=1.0, draw=0.0）"""
    if flex is None:
        flex = draw
    return NOCK_Z0 + nock_travel(flex, draw)


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


# (弓臂内收 flex, 弦拉动 draw, 标签)：r73 起上膛后 draw **保持 1**（弦成 V、弦心在后位），
# 只有击发那一刻才弹回；所以「上膛」与「拉满」是同一个姿态。
STATES = [(0.0, 0.0, '张开'), (0.5, 0.5, '拉弦 50%'), (1.0, 1.0, '拉满/上膛')]


def check():
    print('常数 FLEX_DEG=%.1f  FLEX_BACK=%.2f  TIP_X=%.2f  DRAW_DZ=%.2f  NOCK_Z0=%.2f  L=%.3f'
          % (FLEX_DEG, FLEX_BACK, TIP_X, DRAW_DZ, NOCK_Z0, STRING_LEN))
    for name, side, piv in (('prod_right', 1, (FLEX_PX, FLEX_PZ)),
                            ('prod_left', -1, (-FLEX_PX, FLEX_PZ))):
        inn, out, z0, z1, outer = limb_extents(name, side)
        print('== %-11s 支点=(%+.2f,%+.2f)  方块 x[%.2f,%.2f] z[%.2f,%.2f] 外端≈(%+.2f,%+.2f)'
              % (name, piv[0], piv[1], inn, out, z0, z1, outer[0], outer[1]))
        for flex, draw, label in STATES:
            th = sign_theta(flex, side)
            do = flex_disp(piv, outer, side, flex)
            print('   %-14s flex=%.1f θ=%+5.2f°  外端 (%+.2f,%+.2f) → (%+.2f,%+.2f)  Δ=(%+.2f,%+.2f) 向内%s 向后%s'
                  % (label, flex, th, outer[0], outer[1], outer[0] + do[0], outer[1] + do[1],
                     do[0], do[1],
                     'OK' if do[0] * side < 0 or flex == 0.0 else 'BAD',
                     'OK' if do[1] >= 0 else 'BAD'))
    print('== 弦锚点 / 弦内端（flex = 弓臂内收，draw = 弦拉动；上膛后 flex=1 但 draw=0）')
    print('   状态           | flex |  θ(右)  | 锚点Δ=(dx,dz)   | 弦内端         | 弦心        | 偏差')
    for flex, draw, label in STATES:
        th = sign_theta(flex, 1)
        a = (TIP_X, CAM_Z)
        d = flex_disp((FLEX_PX, FLEX_PZ), a, 1, flex)
        phi = draw * math.degrees(string_phi(flex))
        # 游戏里的弦内端 = (锚点 pivot + 平移 δ) + R(φ)·(−L, 0)
        r = roty(phi)
        off = r(-STRING_LEN, 0.0)
        e = (a[0] + d[0] + off[0], a[1] + d[1] + off[1])
        nz = nock_z(draw, flex)
        flag = '  OK' if abs(e[0]) <= 1.0 and abs(e[1] - nz) <= NOCK_HALF_Z else '  BAD'
        print('   %-14s | %.1f  | %+5.2f° | (%+.2f,%+.2f) | (%+.2f,%+.2f) | (0.00,%+.2f) | (%.2f,%.2f)%s'
              % (label, flex, th, d[0], d[1], e[0], e[1], nz, e[0], e[1] - nz, flag))
    print('★ 判据：两段弦的内端要**跨过中线**（搭接在一起，|x| ≤ 1.0 且内外交错）且落在弦心方块厚度内（|z| ≤ %.2f）'
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


def bake(draw, flex=None, out=None):
    """把 (flex, draw) 姿态烘焙成一份 geo，给 geo_texview.py 出图（flex 缺省 = draw）。

    预览器只认「pivot + rotation（绕 pivot）」，没有 GeckoLib 的 pos（平移）通道，所以：
      · 弓臂：把 pivot 挪到弯折支点、方块不动 + rotation ⇒ 等价于「绕支点转」
      · 弦 / 凸轮 / 弦心 / 弩箭：方块与 pivot 一起平移 +（弦还需）rotation
    """
    geo = load()
    bs = bone_map(geo)
    if flex is None:
        flex = draw
    phi = draw * math.degrees(string_phi(flex))
    pivots = {}
    shifts = {}
    rots = {}
    for side, limb, cam, string in ((1, 'prod_right', 'cam_right', 'string_right'),
                                    (-1, 'prod_left', 'cam_left', 'string_left')):
        piv = (FLEX_PX * side, FLEX_PZ)
        th = sign_theta(flex, side)
        back = flex * FLEX_BACK
        # 弓臂：绕支点转 + 整体后滑 back ⇒ 预览器上等价于「pivot 与方块一起后挪 back + 绕新 pivot 转」
        pivots[limb] = (piv[0], bs[limb]['pivot'][1], piv[1] + back, th)
        shifts[limb] = (0.0, 0.0, back)
        a = (TIP_X * side, CAM_Z)
        d = flex_disp(piv, a, side, flex)
        shifts[cam] = (d[0], 0.0, d[1])
        shifts[string] = (d[0], 0.0, d[1])
        rots[string] = (0.0, side * phi, 0.0)        # ★ 符号必须与 Java 的 setRotY 一致
                                                     #   （Java：左 -draw*phi、右 +draw*phi；
                                                     #    以前这里写成 -side*phi，烘焙出来的预览图
                                                     #    把弦扭到了另一侧，误导了 r86 的验收）
    travel = nock_travel(flex, draw)
    shifts['nock'] = (0.0, 0.0, travel)
    shifts['bolt'] = (0.0, 0.0, travel)

    for b in geo['minecraft:geometry'][0]['bones']:
        name = b['name']
        if name in pivots:
            px, py, pz, th = pivots[name]
            b['pivot'] = [round(px, 4), round(py, 4), round(pz, 4)]
            b['rotation'] = [0.0, round(th, 4), 0.0]
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
                              'cb_flex_%s%s.geo.json' % (
                                  str(flex).replace('.', 'p'),
                                  '' if abs(flex - draw) < 1e-9 else '_d%s' % str(draw).replace('.', 'p')))
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
    ap.add_argument('--flex', type=float, default=None,
                    help='烘焙时的弓臂内收量（默认 = draw；上膛姿态：--bake 0 --flex 1）')
    a = ap.parse_args()
    check()
    if a.bake is not None:
        bake(a.bake, a.flex)


if __name__ == '__main__':
    main()
