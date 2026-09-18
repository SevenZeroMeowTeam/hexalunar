#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""碎片手雷 v3：照 M67 参考照片重建（真骨骼 root/move/body/fuze/spoon/pin）。

参考照片逐项对应：
  - 弹体：**椭圆球**（15 层八边形截面 + 球面曲率阴影，看不出层）
  - 弹体钢印：上半个球面两行**金黄**字母（GRENADE HAND / FRAG DELAY），
    跟随球面分层**逐行裁切**贴出（一行字跨两层也不会断）
  - 腰部接缝：赤道一圈凹槽 + 下缘高光（照片里两半球压合那道线）
  - 引信：螺纹颈圈 → 引信头 → 顶盖 → 顶部螺栓（照片里那一小截螺柱）
  - 压把：从引信头贴着球面下兜到球底、末端外翘的**扁钢片**
  - 保险销：沿 Z 穿过引信颈，-Z 端小环挂一枚**大拉环**（照片里最醒目的一圈）
    —— Java 里整根 pin 骨骼沿 -Z 平移 = 拔销

★ 坐标 / 骨骼约定完全沿用 v2（原点 = 球心，球半径 2.0，骨骼名 root/move/body/fuze/
  spoon/pin；压把在 +Z 侧绕 X 弹开），GrenadeGeoModel 里
  `pin.setPosZ(-pull*1.05)` / `spoon.setRotX(-open*38°)` 的数学一个字都不用改。
"""
import math
import os
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxlib as B  # noqa: E402

C = B.cube
E = B.edge

OLIVE = (98, 112, 68)        # 弹体军绿
FUZE = (84, 86, 84)          # 引信深灰钢
SPOON = (58, 60, 58)         # 压把黑钢
PIN = (134, 136, 140)        # 保险销银灰
RING = (128, 130, 134)       # 拉环
STEEL = (146, 148, 152)      # 螺栓 / 高光钢
GOLD = (200, 172, 76, 255)   # 钢印字（照片里是金黄色）

R = 2.0                      # 弹体半径
NSLAB = 24                   # 球体分层数（非均匀，见 BOUNDS）
Y_PIN = 2.68                 # 保险销高度（穿过引信颈）
RING_Y, RING_Z, RING_R = 2.24, -1.70, 0.80   # 大拉环圆心与半径

BONES = [
    ('root', None, (0.0, -1.9, -2.052)),
    ('move', 'root', (0.0, 0.0, 0.0)),
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('fuze', 'body', (0.0, 2.128, 0.0)),
    ('spoon', 'fuze', (0.0, 3.24, 1.10)),
    ('pin', 'fuze', (0.0, Y_PIN, 0.0)),
]

CUBES = []
DETAILS = {}
DENS = 18.0


def rad_at(y):
    """球面在高度 y 处的水平半径。"""
    t = min(1.0, abs(y) / R)
    return R * math.sqrt(max(0.0, 1.0 - t * t))


SLABS = B.sphere_slabs(R, 0.0, NSLAB, shrink=1.0)

# ★ 改用**非均匀分层**：钢印字所在的那三层做成粗层（一层正好装下一整行 5px 字，
#   不会把字母拦腰截成两半），其他地方用细层（球面台阶小、看不出“棒棒糖”）。
BOUNDS = [-2.00, -1.86, -1.72, -1.58, -1.44, -1.30, -1.16, -1.02, -0.88, -0.74,
          -0.60, -0.46, -0.32, -0.18, -0.04, 0.14, 0.46, 0.79, 1.12,
          1.26, 1.40, 1.54, 1.67, 1.79, 1.90, 2.00]
SLABS = [(a, b, max(R * 0.16, rad_at((a + b) / 2.0) * 0.985))
         for a, b in zip(BOUNDS, BOUNDS[1:])]
NSLAB = len(SLABS)

# ================================================================ 弹体钢印字
# ★ 只能印在**轴向窄面**（宽 0.828r）上：十字双盒八棱柱的宽面（宽 2r）中线被
#   另一根盒子埋住，在那上面印字只会从两侧倒角缝里漏出碎片。所以一行不能太长，
#   拆成 3 行短字（照片上是一行长字，但窄面只有 ~26px）。
#   y 取粗层中心：0.30 / 0.625 / 0.955
TXT = [(0.955, 'GRENADE'), (0.625, 'HAND FRAG'), (0.30, 'DELAY')]


def make_text(sy0, sy1):
    """给某一层球壳贴跨层文字：只画落在本层高度内的那几行像素。

    窄面里长串放不下就把字距从 4px 收到 3px；再放不下就跳过（宁缺勿糊）。
    """
    def fn(img, rect, face, seed):
        if face in ('up', 'down'):
            return
        x, y, w, h = rect
        if w / DENS > 2.2:
            return                 # 宽面（倒角条）中线被埋，印了也是碎片
        d = ImageDraw.Draw(img)
        for ly, s in TXT:
            adv = 4 if B.text_w(s, 4) <= w - 2 else 3
            if B.text_w(s, adv) > w - 2:
                continue
            t = (sy1 - ly) / (sy1 - sy0)          # 行中心在本面里的比例（0 = 面顶）
            py = y + t * h - 2.0                  # 5px 字高，按中心对齐
            B.text(d, x + (w - B.text_w(s, adv)) / 2.0, py, s, GOLD, adv=adv,
                   ytop=y, ybot=y + h)
    return fn


def detail_seam(img, rect, face, seed):
    """腰部接缝：暗槽 + 下缘高光。"""
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.line([(x, y + h // 2), (x + w - 1, y + h // 2)], fill=(34, 38, 26, 255))
    d.line([(x, y + h // 2 + 1), (x + w - 1, y + h // 2 + 1)], fill=B.sh(OLIVE, 1.32))


def detail_fuze(img, rect, face, seed):
    """引信颈：一圈圈螺纹。"""
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    for i in range(0, h, 2):
        d.line([(x + 1, y + i), (x + w - 2, y + i)], fill=B.sh(FUZE, 0.88))
    d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(FUZE, 1.22))
    d.line([(x, y + h - 1), (x + w - 1, y + h - 1)], fill=B.sh(FUZE, 0.70))


def detail_cap(img, rect, face, seed):
    """引信头 / 顶盖：方形铸造面 + 上盖中心一圈亮环。"""
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.rectangle([x + 1, y + 1, x + w - 2, y + h - 2], outline=B.sh(FUZE, 0.68))
    if face == 'up':
        cx, cy = x + w / 2.0, y + h / 2.0
        rr = min(w, h) * 0.28
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=B.sh(FUZE, 1.30))


def detail_steel(img, rect, face, seed):
    """钢件：上沿亮 / 下沿暗（车削反光）。"""
    x, y, w, h = rect
    px = img.load()
    for i in range(w):
        for k, f in ((y, 1.22), (y + 1, 1.10), (y + h - 2, 0.86), (y + h - 1, 0.74)):
            if y <= k < y + h:
                c = px[i, k]
                px[i, k] = (B.cl(c[0] * f), B.cl(c[1] * f), B.cl(c[2] * f), 255)


def detail_spoon(img, rect, face, seed):
    """压把扁钢：上下沿一亮一暗，中间一道纵向压筋。"""
    x, y, w, h = rect
    E(img, rect, 1.22, 0.76)
    px = img.load()
    cx = x + w * 0.5
    for j in range(y + 1, y + h - 1):
        c = px[int(cx), j]
        px[int(cx), j] = (B.cl(c[0] * 1.12), B.cl(c[1] * 1.12), B.cl(c[2] * 1.12), 255)


# ================================================================ 弹体（球）
# ★ 不画层间边线：每层上下沿一明一暗会把这颗球切成“蛋糕层”。球面明暗完全交给
#   curv=('sphere') 的手工逐面烘，相邻层的台阶就看不出来了。
for _i, (_y0, _y1, _r) in enumerate(SLABS):
    _tag = None
    if _y1 > TXT[-1][0] - 0.25 and _y0 < TXT[0][0] + 0.25:
        _tag = 'txt%d' % _i
        DETAILS[_tag] = make_text(_y0, _y1)
    CUBES += B.cross_boxes('body', 'sphere_%d' % _i, _y0, _y1, _r * 0.985, 0.0, 0.0,
                           B.sh(OLIVE, 0.94) if _i < NSLAB / 2 else OLIVE,
                           'metal', tag=_tag, curv=('sphere', (0.0, 0.0, 0.0)))

# 腰部接缝（赤道一圈，比球面略凸）
CUBES += B.cross_boxes('body', 'seam', -0.09, 0.09, R * 1.014, 0.0, 0.0,
                       B.sh(OLIVE, 0.86), 'flat', tag='seam')

# ================================================================ 引信
CUBES += B.cross_boxes('fuze', 'fx_collar', 1.72, 2.26, 0.90, 0.0, 0.0, FUZE,
                       'metal', tag='fuze')
CUBES += B.cross_boxes('fuze', 'fx_neck', 2.26, 2.76, 0.74, 0.0, 0.0, B.sh(FUZE, 1.08),
                       'metal', tag='fuze')
CUBES += B.cross_boxes('fuze', 'fx_head', 2.76, 3.14, 0.88, 0.0, 0.0, FUZE,
                       'metal', tag='cap')
CUBES += B.cross_boxes('fuze', 'fx_cap', 3.14, 3.32, 0.76, 0.0, 0.0, B.sh(FUZE, 1.14),
                       'metal', tag='cap')
CUBES += B.cross_boxes('fuze', 'fx_bolt', 3.32, 3.62, 0.42, 0.0, 0.0, STEEL,
                       'metal', tag='steel')
CUBES.append(C('fuze', 'fx_bolt_slot', (-0.28, 0.28), (3.62, 3.66), (-0.06, 0.06),
               (40, 42, 44), kind='flat'))
CUBES += B.ring('fuze', 'fx_thread', 0.0, 2.50, 0.0, 0.80, 0.09, (42, 44, 40),
                'metal', axis='y', seg=12)

# ================================================================ 压把（+Z 侧，贴着球面）
SPOON_PATH = [(3.16, 0.78), (2.84, 0.92), (2.40, 1.02), (1.98, 1.14),
              (1.56, 1.46), (0.95, 1.98), (0.16, 2.20), (-0.70, 2.10),
              (-1.45, 1.72), (-2.10, 1.24), (-2.50, 0.74)]
CUBES += B.arc_boxes('spoon', 'spoon', SPOON_PATH, thick=0.18, half_w=0.32,
                     mat=SPOON, kind='flat', tag='spoon', plane='yz', offset=0.0)
CUBES.append(C('spoon', 'spoon_hinge', (-0.34, 0.34), (3.00, 3.34), (0.36, 1.04),
               SPOON, kind='flat', tag='spoon'))
CUBES.append(C('spoon', 'spoon_tip', (-0.30, 0.30), (-2.66, -2.36), (0.52, 1.06),
               B.sh(SPOON, 1.18), kind='flat', tag='spoon'))

# ================================================================ 保险销 + 大拉环
CUBES.append(C('pin', 'pin_rod', (-0.12, 0.12), (Y_PIN - 0.12, Y_PIN + 0.12),
               (-1.72, 0.92), PIN, kind='brushed', tag='steel'))
CUBES.append(C('pin', 'pin_leg', (-0.12, 0.12), (Y_PIN - 0.21, Y_PIN - 0.09),
               (-1.72, 0.92), B.sh(PIN, 0.80), kind='brushed', tag='steel'))
CUBES += B.ring('pin', 'pin_eye', 0.0, Y_PIN, RING_Z + 0.05, 0.20, 0.13, PIN,
                'brushed', axis='z', seg=8)
CUBES += B.ring('pin', 'pin_head', 0.0, Y_PIN, 0.96, 0.17, 0.12, PIN,
                'brushed', axis='x', seg=8)
CUBES += B.ring('pin', 'big_ring', 0.0, RING_Y, RING_Z, RING_R, 0.17, RING,
                'brushed', axis='x', seg=10)

DETAILS.update({'seam': detail_seam, 'fuze': detail_fuze, 'cap': detail_cap,
                'steel': detail_steel, 'spoon': detail_spoon})


def main():
    global DENS
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    need = {'root', 'move', 'body', 'fuze', 'spoon', 'pin'}
    have = set(b[0] for b in BONES)
    print('骨骼名检查: %s' % ('OK' if need <= have else '缺 %s' % (need - have)))

    geo = img = None
    used = None
    for dens in (18.0, 16.0, 14.0, 12.0):
        DENS = dens          # 逐面细节里的字距/宽面判据都依赖它
        try:
            geo, img = B.build(BONES, CUBES, 'geometry.mud', details=DETAILS,
                               density=dens)
            used = dens
            break
        except RuntimeError as e:
            print('density %.1f 图集放不下（%s），降一档重试' % (dens, e))
    B.write(geo, img, os.path.join(root, 'build', 'grenade_v3.geo.json'),
            os.path.join(root, 'build', 'grenade_v3.png'), quiet=True)
    n = sum(len(b.get('cubes', [])) for b in geo['minecraft:geometry'][0]['bones'])
    print('bones %d  cubes %d  density %.1f' % (len(BONES), n, used))
    print('wrote build/grenade_v3.geo.json / .png')

    # ---- 自检 1：大拉环最靠近球心的那一点必须在球面之外（否则环会被球埋掉半圈）
    near = math.hypot(RING_Y, RING_Z) - RING_R
    print('拉环最近处距球心 %.3f  球半径 %.2f  %s'
          % (near, R, 'OK' if near > R else '!! 环插进弹体'))
    # ---- 自检 2：每行钢印字都要落在球腰上，且所在层的**轴向窄面**放得下
    for ly, s in TXT:
        slab = None
        for (y0, y1, r) in SLABS:
            if y0 <= ly <= y1:
                slab = (y0, y1, r)
        if slab is None:
            print('字行 %-10s y=%+.2f  !! 没有对应球壳层' % (s, ly))
            continue
        face_w = math.ceil(0.828 * slab[2] * 0.985 * (used or 18.0))  # 轴向窄面宽
        face_w -= 2           # build() 里还留了 2px 余量
        adv = 4 if B.text_w(s, 4) <= face_w else 3
        print('字行 %-10s y=%+.2f  层半径 %.2f  窄面可用 %.0fpx  需要 %dpx(adv=%d)  %s'
              % (s, ly, slab[2], face_w, B.text_w(s, adv), adv,
                 'OK' if B.text_w(s, adv) <= face_w else '!! 放不下'))
    # ---- 自检 3：压把始终贴在球面之外（不能陷进球里）
    worst, worst_p = 9.9, None
    for (py, pz) in SPOON_PATH:
        gap = math.hypot(py, pz) - R
        if gap < worst:
            worst, worst_p = gap, (py, pz)
    print('压把离球面最小间隙 %.3f @ %s  %s'
          % (worst, worst_p, 'OK' if worst > -0.05 else '!! 陷进球里'))
    print('销 z 范围 -1.72 .. 0.92（Java 拔销沿 -Z 平移 %.2f）' % 1.05)
    print('球径 %.2f  引信顶 %.2f  (体+引信)高/径 %.2f'
          % (2 * R, 3.66, (3.66 + R) / (2 * R)))


if __name__ == '__main__':
    main()
