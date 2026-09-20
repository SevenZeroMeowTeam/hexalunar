#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""莫辛-纳甘 M91/30（带长刺刀）v2 —— 按用户照片 + 追加要求重做。

v1（``mosin_m9130_gen.py``）是「方块外壳」版；v2 按用户要求改掉四件事：

  1. **枪管 = 圆形（八棱）且空心**：枪口是真正开孔的八棱环，往里是 1 单位深的黑膛，
     不是「贴一块黑方块冒充孔」
  2. **弹仓 = 空心、上口敞开**：里面看得见 **3 发** 黄铜弹（弹壳 + 铜弹头）
  3. **机匣 = 空心 + 顶部装填/抛壳口**；枪机体在机匣内腔里滑动 ——
     闭栓时机体正好盖住整个装填口 ⇒ **看不见弹仓里的子弹**；后拉 1.9 单位 ⇒ 子弹露出来
  4. **瞄准镜 = 圆型空心镜筒 + 前后半透明玻璃 + 内部十字分划**（镜筒/镜环全是八棱环）

动画（``build/mosin_m9130.animation.json``，同时写进 .bbmodel 与在线 Blockbench）：

  ``animation.mosin_m9130.bolt``       拉栓：抬柄 → 后拉（**空弹壳跟着退出来、看得见**）→
                                       抛壳（向右上翻滚飞走）→ 前推 → **把弹仓最上一发顶进弹膛**
  ``animation.mosin_m9130.bolt_open``  停在「开栓」姿态（hold）：看得见退出来的弹壳 + 弹仓里的子弹
  ``animation.mosin_m9130.reload``     换弹：开栓 → 连压 3 发进弹仓 → 闭栓
  ``animation.mosin_m9130.fire``       击发：扣扳机

规格（照照片量，1 模型像素 = 1/16 格 ≈ 6.25 cm）
--------------------------------------------------
    全长（含刺刀） 28.2 像素 ≈ 1.76 格    枪管轴线 BORE = 1.75（与 AKM/AWP 同一套）
    机瞄瞄准线 IRON_Y = 2.72（准星柱顶 = 表尺两耳顶）    机匣顶 RCV_TOP = 2.44
    枪口端面 z = -16.78（内孔底 -15.80，孔深 0.98 ≈ 6 cm）  托底 z = +5.60
    镜光轴 (x, y) = (-0.54, 3.24)（PU 式左侧镜筒：圆筒 r0.32 / 物镜 r0.38 / 目镜 r0.36）
    刺刀 = 套管（八棱环）+ 十字四鳍刀身（**中间留孔** ⇒ 从枪口一直能看进弹膛）
    装填/抛壳口 z −3.30..−2.45（宽 0.85）；枪机后拉 1.90 ⇒ 完全让开

用法
----
    python tools/mosin_m9130_v2.py          # 出 geo / 贴图 / glowmask / animation
    python tools/geo2bbmodel.py mosin_m9130 # 出 模型/hexalunar_mosin_m9130.bbmodel（含动画）
    python tools/_m9130check.py             # 数值自检：空心 / 子弹可见性 / 遮挡
"""
import io
import json
import os
import sys

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, 'build')
KEEP = os.path.join(ROOT, '模型', 'mosin_m9130')
GEO_NAME = 'mosin_m9130'

TEX = 256
BAND_W = 64
# ------------------------------------------------------------------ 调色板（照照片 + 透明玻璃）
BANDS = {
    'wood':     (0,   (198, 142, 92), 255),   # 亮胡桃木（照片里的托/护木）
    'wood_d':   (16,  (166, 110, 62), 255),   # 木纹暗部
    'wood_dd':  (32,  (138, 88, 48), 255),    # 枪背带槽 / 凹处
    'steel':    (48,  (168, 172, 182), 255),  # 抛光钢（刺刀/枪机/通条）
    'steel_d':  (64,  (72, 78, 92), 255),     # 深钢（枪管/机匣）
    'steel_dd': (80,  (46, 50, 62), 255),     # 更暗（准星座/表尺/托板/扳机）
    'brass':    (96,  (208, 164, 82), 255),   # 黄铜（枪箍/弹仓/弹壳）
    'copper':   (112, (198, 126, 72), 255),   # 铜被甲弹头
    'optic':    (128, (52, 54, 60), 255),     # 镜筒壳体
    'optic_d':  (144, (34, 36, 42), 255),     # 镜环 / 镜座
    'black':    (160, (22, 24, 30), 255),     # 枪管内孔 / 内壁
    'glass':    (176, (150, 205, 225), 72),   # ★ 半透明镜片
    'reticle':  (192, (14, 14, 16), 255),     # ★ 十字分划
}
PAT = {k: (0, v[0], BAND_W, 10) for k, v in BANDS.items()}
GLOW_BANDS = ('steel', 'brass', 'glass')

# ------------------------------------------------------------------ 必须守住的锚点
BORE = 1.75                 # 枪管轴线
IRON_Y = 2.72               # 机瞄瞄准线（准星柱顶 = 表尺两耳顶）
RCV_TOP = 2.44              # 机匣顶面（必须低于 IRON_Y）
MUZZLE_Z = -16.78           # 枪管前端面（弹丸出膛点）
MUZZLE_IN = -15.80          # 内孔底（孔深 0.98 ≈ 6 cm）
SCOPE_X = -0.54             # ★ 镜光轴横向偏移（PU 镜在机匣**左侧** ⇒ 装填口上方不被镜座挡住）
SCOPE_Y = 3.24              # 镜筒光轴高度
SCOPE_R = 0.32              # 镜筒外半径（壁厚 0.12 ⇒ 内孔 ∅0.40）
EJECT = (0.62, 2.10, -1.95)  # 抛壳口（照旧，只作参考点）
CHAMBER_REAR = -3.40        # 弹膛里那发子弹的弹尾 z（整发 −3.40..−4.27，全在机匣前桥里）
CHAMBER = (0.0, BORE, -3.835)  # 弹膛中心（弹壳 / 待压入的那发静止时藏在这里）
STACK_REAR = -2.42          # 弹仓里横躺那几发的弹尾 z（整发 −2.42..−3.29）
MAG_PIVOT = (0.0, 1.06, -2.75)
ROUNDS_PIVOT = (0.0, 1.12, -2.70)
ROUND_TOP_PIVOT = (0.0, 1.30, -2.855)
ROUND_TOP_C = (0.0, 1.30, -2.855)   # 弹仓最上一发的中心（拉栓时它被顶进弹膛）
ABOVE_PORT_C = (0.0, 3.05, -2.70)   # 压弹时子弹出现在装填口正上方
HANDGUARD = (0.0, 2.06, -9.40)
BUTT_Z = 5.60
BAYONET_TIP = -22.40
BORE_HOLE = 0.115           # 枪口内孔 / 刺刀刀身中心留孔半径（≥ 实际内孔才能看穿）
# ★ 机匣内腔 / 装填口（这三组数是「看得见/看不见子弹」的硬约束，改之前先看 _m9130check.py）
RCV_X = 0.40                # 机匣外壁
RCV_IN = 0.215              # 机匣内壁（= 枪机体半宽 ⇒ 闭栓无侧缝）
PORT_Z = (-3.30, -2.45)     # 装填/抛壳口
MAG_MOUTH = 1.40            # 弹仓上口（= 机匣底）
SLOT_X = 0.10               # 后桥上的拉机柄槽（半宽）


def uv_for(name):
    u, v, w, h = PAT[name]
    return {f: {'uv': [u, v], 'uv_size': [w, h]}
            for f in ('north', 'east', 'south', 'west', 'up', 'down')}


def box(x0, x1, y0, y1, z0, z1, tex):
    return {
        'origin': [round(min(x0, x1), 4), round(min(y0, y1), 4), round(min(z0, z1), 4)],
        'size': [round(abs(x1 - x0), 4), round(abs(y1 - y0), 4), round(abs(z1 - z0), 4)],
        'uv': uv_for(tex),
    }


def oct_z(z0, z1, cy, r, mat, cx=0.0, k=0.78):
    """Z 向八棱柱（两个正交盒 → 截面是八边形 = 「圆」）：枪管 / 镜筒底座用。"""
    a = k * r
    return [box(cx - r, cx + r, cy - a, cy + a, z0, z1, mat),
            box(cx - a, cx + a, cy - r, cy + r, z0, z1, mat)]


def ring_z(z0, z1, cx, cy, r, t, mat, k=0.73):
    """Z 向八棱**环**（4 根壁条 ⇒ 外轮廓八边形、中间是真孔）。

    上/下壁条只占 ±k·r 宽，左/右壁条只占 ±k·r 高 ⇒ 四个角被切掉（八边形），
    中间留下的方孔边长 2(r−t)。
    """
    return [box(cx - k * r, cx + k * r, cy + r - t, cy + r, z0, z1, mat),   # 上
            box(cx - k * r, cx + k * r, cy - r, cy - r + t, z0, z1, mat),   # 下
            box(cx - r, cx - r + t, cy - k * r, cy + k * r, z0, z1, mat),   # 左
            box(cx + r - t, cx + r, cy - k * r, cy + k * r, z0, z1, mat)]   # 右


def oct_y(y0, y1, cx, cz, r, mat, k=0.78):
    """Y 向八棱柱（竖直旋钮）。"""
    a = k * r
    return [box(cx - r, cx + r, y0, y1, cz - a, cz + a, mat),
            box(cx - a, cx + a, y0, y1, cz - r, cz + r, mat)]


def oct_x(x0, x1, cy, cz, r, mat, k=0.78):
    """X 向八棱柱（横向旋钮）。"""
    a = k * r
    return [box(x0, x1, cy - r, cy + r, cz - a, cz + a, mat),
            box(x0, x1, cy - a, cy + a, cz - r, cz + r, mat)]


CASE_LEN = 0.56        # 弹壳长
NECK_LEN = 0.05        # 收口长
TIP_LEN = 0.26         # 弹头长
ROUND_LEN = CASE_LEN + NECK_LEN + TIP_LEN


def round_range(z_rear):
    """一发子弹的三段 z（弹尾 / 收口 / 弹尖）—— 子弹沿 −Z 指向前方。"""
    z_sh = z_rear - CASE_LEN
    return z_rear, z_sh, z_sh - TIP_LEN


def round_boxes(y0, y1, z_rear, case='brass', tip='copper'):
    """一发子弹：弹壳 + 收口 + 铜被甲弹头（沿 −Z 指向前方）。y0..y1 = 弹壳外径。"""
    cy = (y0 + y1) / 2.0
    rc = (y1 - y0) / 2.0
    rt = rc * 0.78
    z_rear, z_sh, z_tip = round_range(z_rear)
    return [box(-rc, rc, y0, y1, z_sh, z_rear, case),                    # 弹壳体
            box(-rc * 0.56, rc * 0.56, cy - rc * 0.56, cy + rc * 0.56,
                z_sh - NECK_LEN, z_sh, tip),                            # 收口
            box(-rt, rt, cy - rt, cy + rt, z_tip, z_sh - NECK_LEN, tip)]  # 弹头


def bone(name, pivot, parent, cubes=None):
    b = {'name': name, 'pivot': [round(v, 4) for v in pivot], 'cubes': cubes or []}
    if parent:
        b['parent'] = parent
    return b


# ==================================================================== 骨骼
def build_bones():
    B = []

    # ---------------- bayonet：★套管（环，不堵弹道）+ 固定螺钉 + 十字带孔长刺刀 ----------------
    bay = []
    # 套管：4 壁条的八棱环 —— 中间是通的，从前方能一直看进枪管
    bay += ring_z(-17.35, -16.60, 0.0, BORE, 0.34, 0.16, 'steel')
    bay += [box(0.34, 0.48, 1.68, 1.86, -17.22, -17.00, 'steel_dd')]      # 固定螺钉
    # ★ 刀身：十字形四片鳍（中心固定留孔 ∅0.23 —— 比枪口内孔还大 ⇒ 从枪口一直看得进去）
    for z0, z1, r in ((-19.20, -17.35, 0.30), (-21.20, -19.20, 0.20),
                      (-22.40, -21.20, 0.13), (-22.70, -22.40, 0.07)):
        g = min(BORE_HOLE, r - 0.012)              # 中心留孔半径（子弹通道）
        bay += [box(-0.035, 0.035, BORE + g, BORE + r, z0, z1, 'steel'),    # 上鳍
                box(-0.035, 0.035, BORE - r, BORE - g, z0, z1, 'steel'),    # 下鳍
                box(-r, -g, BORE - 0.035, BORE + 0.035, z0, z1, 'steel'),   # 左鳍
                box(g, r, BORE - 0.035, BORE + 0.035, z0, z1, 'steel')]     # 右鳍
    B.append(bone('bayonet', (0.0, BORE, MUZZLE_Z), 'barrel', bay))

    # ---------------- barrel：八棱空心枪管 + 准星 + 立框表尺 + 通条 ----------------
    bar = []
    # ★ 阶梯八棱枪管（两个正交盒 ⇒ 圆：不再是一个方盒）
    bar += oct_z(-6.20, -4.30, BORE, 0.34, 'steel_d')
    bar += oct_z(-12.60, -6.20, BORE, 0.30, 'steel_d')
    bar += oct_z(MUZZLE_IN, -12.60, BORE, 0.26, 'steel_d')
    # ★★ 空心枪口：八棱环（4 壁条，中间是真孔）+ 孔内发黑内壁 + 深处的黑膛底
    bar += ring_z(MUZZLE_Z, MUZZLE_IN, 0.0, BORE, 0.28, 0.16, 'steel')
    bar += ring_z(MUZZLE_Z + 0.03, MUZZLE_IN - 0.02, 0.0, BORE, 0.125, 0.022, 'black')
    bar += [box(-0.115, 0.115, BORE - 0.115, BORE + 0.115,
                MUZZLE_IN, MUZZLE_IN + 0.18, 'black')]
    # 通条（照片里枪管下方那根细杆）
    bar += [box(-0.07, 0.07, 1.15, 1.29, -16.40, -5.60, 'steel'),
            box(-0.10, 0.10, 1.13, 1.31, -16.55, -16.40, 'steel_dd')]
    # 前准星：底座 + 柱（柱顶 = IRON_Y）+ 两片护耳（低于柱顶）
    bar += [box(-0.28, 0.28, 2.02, 2.26, -15.70, -15.15, 'steel_dd'),
            box(-0.075, 0.075, 2.26, IRON_Y, -15.55, -15.30, 'steel_dd'),
            box(-0.30, -0.13, 2.26, 2.62, -15.65, -15.20, 'steel_dd'),
            box(0.13, 0.30, 2.26, 2.62, -15.65, -15.20, 'steel_dd')]
    # 立框式表尺（M91/30 招牌件）：底座 + 斜坡 + 游标 + 缺口两耳（耳顶 = IRON_Y）
    bar += [box(-0.34, 0.34, 2.02, 2.28, -5.60, -4.30, 'steel_dd'),
            box(-0.30, 0.30, 2.28, 2.40, -5.50, -5.00, 'steel_dd'),
            box(-0.32, 0.32, 2.34, 2.48, -5.06, -4.80, 'steel_dd'),
            box(-0.32, -0.10, 2.48, IRON_Y, -5.62, -5.34, 'steel_dd'),
            box(0.10, 0.32, 2.48, IRON_Y, -5.62, -5.34, 'steel_dd')]
    B.append(bone('barrel', (0.0, BORE, -9.00), 'move', bar))

    # ---------------- handguard：上护木 + 两道黄铜枪箍 ----------------
    hg = [
        box(-0.42, 0.42, 2.02, 2.32, -13.40, -6.70, 'wood'),
        box(-0.40, 0.40, 1.98, 2.30, -14.10, -13.40, 'wood_d'),
        box(-0.46, 0.46, 1.20, 2.34, -13.30, -12.90, 'brass'),
        box(-0.48, 0.48, 1.16, 2.36, -8.90, -8.50, 'brass'),
        box(-0.50, 0.50, 1.14, 1.20, -13.30, -12.90, 'steel_dd'),
        box(-0.52, 0.52, 1.10, 1.16, -8.90, -8.50, 'steel_dd'),
    ]
    B.append(bone('handguard', HANDGUARD, 'body', hg))

    # ---------------- body：木托 + ★空心机匣（带装填口） + 扳机护圈 ----------------
    body = [
        # 前托（枪口方向渐薄）
        box(-0.42, 0.42, 1.16, 1.98, -14.60, -13.40, 'wood_d'),
        box(-0.50, 0.50, 1.14, 2.06, -13.40, -6.60, 'wood'),
        box(-0.52, 0.52, 1.10, 2.10, -6.60, -4.30, 'wood'),
        # ★ 机匣座木托：只包到机匣下方与两侧 —— **绝不能填进机匣内腔**（否则弹仓里看不见子弹）
        box(-0.56, 0.56, 1.40, 1.58, -4.30, -3.30, 'wood'),
        box(-0.56, 0.56, 1.40, 1.58, -2.45, 0.60, 'wood'),
        box(-0.56, 0.56, 0.60, 1.40, -4.30, -3.52, 'wood'),      # 弹仓前
        box(-0.56, -0.40, 0.60, 1.40, -3.52, -2.08, 'wood'),     # 弹仓左
        box(0.40, 0.56, 0.60, 1.40, -3.52, -2.08, 'wood'),       # 弹仓右
        # ★★ 弹仓后：托腹抬高到 y1.06 —— 让扳机护圈吊在托腹**下面**，
        #    护圈里的扳机片从左右两侧都看得见（之前这里是一整块木头，扳机被埋了）
        box(-0.56, 0.56, 1.06, 1.40, -2.10, 0.62, 'wood'),
        box(-0.56, -0.40, 1.45, 2.02, -4.30, -2.60, 'wood_d'),   # 左頰
        box(0.40, 0.56, 1.45, 2.02, -4.30, -2.60, 'wood_d'),     # 右頰
        # ★ 握把（腕部）：比托身窄一圈、下探 —— 侧视能看出「脖子」
        box(-0.42, 0.42, 0.62, 1.92, 0.62, 2.70, 'wood_d'),
        box(-0.52, 0.52, 0.40, 2.30, 2.60, 4.20, 'wood'),
        box(-0.52, 0.52, 0.40, 2.06, 4.20, BUTT_Z, 'wood'),
        box(-0.54, 0.54, 0.36, 2.34, BUTT_Z - 0.16, BUTT_Z, 'steel_dd'),
        box(-0.58, -0.50, 1.28, 1.52, 3.70, 4.30, 'wood_dd'),
        box(-0.58, -0.50, 1.34, 1.58, -1.60, -1.10, 'wood_dd'),
        box(0.50, 0.58, 1.32, 1.56, 3.80, 4.20, 'brass'),
        # ★★ 机匣（空心：底 / 两壁 / 前桥=弹膛段 / 后桥（中间留拉机柄槽）/ 顶盖）
        box(-RCV_X, RCV_X, 1.40, 1.58, -4.30, PORT_Z[0], 'steel_d'),      # 底（前）
        box(-RCV_X, RCV_X, 1.40, 1.58, PORT_Z[1], -0.30, 'steel_d'),      # 底（后）
        box(-RCV_X, -RCV_IN, 1.58, RCV_TOP, -4.30, -0.30, 'steel_d'),     # 左壁
        box(RCV_IN, RCV_X, 1.58, RCV_TOP, -4.30, -0.30, 'steel_d'),       # 右壁
        box(-RCV_IN, RCV_IN, 1.58, RCV_TOP, -4.30, PORT_Z[0], 'steel_d'),  # 前桥（弹膛）
        box(-RCV_IN, -SLOT_X, 1.58, RCV_TOP, PORT_Z[1], -0.30, 'steel_d'),  # 后桥左
        box(SLOT_X, RCV_IN, 1.58, RCV_TOP, PORT_Z[1], -0.30, 'steel_d'),    # 后桥右
        box(-0.34, 0.34, RCV_TOP, RCV_TOP + 0.06, -4.10, PORT_Z[0], 'steel'),   # 顶盖前
        box(-0.34, -SLOT_X, RCV_TOP, RCV_TOP + 0.06, PORT_Z[1], -0.50, 'steel'),  # 顶盖后左
        box(SLOT_X, 0.34, RCV_TOP, RCV_TOP + 0.06, PORT_Z[1], -0.50, 'steel'),    # 顶盖后右
        # ★ 扳机护圈（前立柱 + 底梁 + 后立柱）：吊在托腹（y1.06）下面，左右通透
        box(-0.26, 0.26, 0.44, 1.12, -2.06, -1.94, 'steel_dd'),
        box(-0.22, 0.22, 0.36, 0.46, -2.06, -1.12, 'steel_dd'),
        box(-0.26, 0.26, 0.36, 1.12, -1.24, -1.12, 'steel_dd'),
    ]
    B.append(bone('body', (0.0, BORE, -2.40), 'move', body))

    # ---------------- bolt：机体（闭栓时正好盖住装填口）+ 机尾 + 直拉球头柄 ----------------
    bolt = [
        box(-RCV_IN, RCV_IN, 1.60, 1.90, -3.60, -1.10, 'steel'),   # ★ 机体：闭栓盖住 PORT_Z
        box(-0.24, 0.24, 1.54, 1.96, -1.10, -0.46, 'steel'),       # 机尾（后桥里）
        box(-0.20, 0.20, 1.60, 1.90, -0.46, -0.18, 'steel_d'),     # 机尾末端（露在机匣外）
        box(RCV_IN, 0.90, 1.65, 1.81, -1.90, -1.62, 'steel'),      # 拉机柄（穿出右壁）
        box(0.86, 1.04, 1.55, 1.73, -1.94, -1.58, 'steel_d'),      # 下弯球头
    ]
    B.append(bone('bolt', (0.0, BORE, -1.85), 'body', bolt))

    # ---------------- magazine：★空心弹仓（黄铜壁，上口敞开）+ 钢底板 ----------------
    # ★ 侧壁一路包到机匣底（y 1.58）：否则 y 1.40~1.58 会留出一条侧缝，
    #   从侧面能瞥见里面的子弹（射线自检会 FAIL）
    mag = [
        box(-0.40, -0.22, 0.50, 1.58, -3.50, -2.10, 'brass'),        # 左壁
        box(0.22, 0.40, 0.50, 1.58, -3.50, -2.10, 'brass'),          # 右壁
        box(-0.22, 0.22, 0.50, 1.58, -3.50, -3.36, 'brass'),         # 前壁
        box(-0.22, 0.22, 0.50, 1.58, -2.24, -2.10, 'brass'),         # 后壁
        box(-0.38, 0.38, 0.34, 0.50, -3.54, -2.06, 'steel_dd'),      # 钢底板
        box(-0.30, 0.30, 0.30, 0.36, -3.20, -2.40, 'steel_dd'),      # 底板卡榫
    ]
    B.append(bone('magazine', MAG_PIVOT, 'body', mag))

    # ---------------- rounds：弹仓里**下两发**（横躺的子弹，看得见） ----------------
    rounds = []
    rounds += round_boxes(0.86, 1.02, STACK_REAR)
    rounds += round_boxes(1.04, 1.20, STACK_REAR)
    B.append(bone('rounds', ROUNDS_PIVOT, 'body', rounds))

    # ---------------- round_top：弹仓最上一发（拉栓前推时被顶进弹膛的那发） ----------------
    top = round_boxes(1.22, 1.38, STACK_REAR)
    B.append(bone('round_top', ROUND_TOP_PIVOT, 'body', top))

    # ---------------- round_in：换弹时用手压进弹仓的那发（静止时收在弹膛里，看不见） ----------------
    rin = round_boxes(BORE - 0.075, BORE + 0.075, CHAMBER_REAR)
    B.append(bone('round_in', CHAMBER, 'body', rin))

    # ---------------- trigger：★扳机片（挂在护圈里，两侧都看得见；绕顶部销轴后转） ----------------
    B.append(bone('trigger', (0.0, 1.12, -1.73), 'body',
                  [box(-0.075, 0.075, 0.60, 1.16, -1.84, -1.66, 'steel_dd'),   # 扳机片
                   box(-0.075, 0.075, 0.60, 0.68, -1.90, -1.66, 'steel'),      # 指尖（略弯）
                   box(-0.09, 0.09, 1.16, 1.30, -1.80, -1.62, 'steel_dd')]))   # 上座（顶进托腹）

    # ---------------- casing：空弹壳（静止时在弹膛里 = 看不见；拉栓时被抽出来） ----------------
    z_rear, z_sh, z_tip = round_range(CHAMBER_REAR)
    cas = [box(-0.075, 0.075, BORE - 0.075, BORE + 0.075, z_sh, z_rear, 'brass'),
           box(-0.043, 0.043, BORE - 0.043, BORE + 0.043, z_sh - NECK_LEN, z_sh, 'copper')]
    B.append(bone('casing', (0.0, BORE, (z_rear + z_sh) / 2.0), 'body', cas))

    # ---------------- scope：★圆型空心镜筒 + 玻璃 + 十字分划 + PU 式**左侧**镜座 ----------------
    #   ★ 镜座必须挪到机匣左侧：装在正上方会把装填口挡死（玩家从上往下看不见弹仓里的子弹）
    sc = []
    r = SCOPE_R
    sc += ring_z(-3.34, -1.28, SCOPE_X, SCOPE_Y, r, 0.12, 'optic')          # 镜筒（空心）
    sc += ring_z(-3.94, -3.34, SCOPE_X, SCOPE_Y, r + 0.06, 0.13, 'optic')   # 物镜筒
    sc += ring_z(-1.28, -0.62, SCOPE_X, SCOPE_Y, r + 0.04, 0.12, 'optic')   # 目镜筒
    sc += ring_z(-4.02, -3.88, SCOPE_X, SCOPE_Y, r + 0.09, 0.09, 'optic_d')  # 物镜圈
    sc += ring_z(-0.74, -0.60, SCOPE_X, SCOPE_Y, r + 0.07, 0.09, 'optic_d')  # 目镜圈
    # ★ 玻璃（半透明）：前镜片（物镜内圆）+ 后镜片（目镜内圆）
    gi = r - 0.12                                                          # 内孔半宽
    sc += [box(SCOPE_X - gi, SCOPE_X + gi, SCOPE_Y - gi, SCOPE_Y + gi,
               -3.90, -3.84, 'glass'),
           box(SCOPE_X - gi, SCOPE_X + gi, SCOPE_Y - gi, SCOPE_Y + gi,
               -0.70, -0.64, 'glass')]
    # ★ 十字分划（镜筒内部、目镜前，透过玻璃能看见）
    sc += [box(SCOPE_X - 0.028, SCOPE_X + 0.028, SCOPE_Y - gi, SCOPE_Y + gi,
               -0.96, -0.93, 'reticle'),
           box(SCOPE_X - gi, SCOPE_X + gi, SCOPE_Y - 0.028, SCOPE_Y + 0.028,
               -0.96, -0.93, 'reticle'),
           box(SCOPE_X - 0.05, SCOPE_X + 0.05, SCOPE_Y - 0.05, SCOPE_Y + 0.05,
               -0.99, -0.90, 'reticle')]
    # 镜环 ×2（套在镜筒外的圆环）+ 左侧导轨 + 两条支臂（把镜筒撑到机匣左边）
    sc += ring_z(-3.10, -2.86, SCOPE_X, SCOPE_Y, r + 0.04, 0.09, 'optic_d')
    sc += ring_z(-2.06, -1.82, SCOPE_X, SCOPE_Y, r + 0.04, 0.09, 'optic_d')
    sc += [box(-0.58, -0.42, 2.02, 2.32, -3.30, -1.60, 'optic_d'),                # 导轨
           box(-0.60, -0.44, 2.32, SCOPE_Y - 0.28, -3.10, -2.86, 'optic_d'),      # 前支臂
           box(-0.60, -0.44, 2.32, SCOPE_Y - 0.28, -2.06, -1.82, 'optic_d')]      # 后支臂
    B.append(bone('scope', (SCOPE_X, SCOPE_Y, -2.60), 'body', sc))
    B.append(bone('scope_elev', (SCOPE_X, SCOPE_Y + r, -2.40), 'scope',
                  oct_y(SCOPE_Y + r - 0.02, SCOPE_Y + r + 0.34, SCOPE_X, -2.40, 0.16,
                        'optic_d')
                  + [box(SCOPE_X - 0.20, SCOPE_X + 0.20, SCOPE_Y + r + 0.34,
                         SCOPE_Y + r + 0.42, -2.60, -2.20, 'optic')]))
    B.append(bone('scope_wind', (SCOPE_X - r, SCOPE_Y, -2.40), 'scope',
                  oct_x(SCOPE_X - r - 0.34, SCOPE_X - r + 0.02, SCOPE_Y, -2.40, 0.16,
                        'optic_d')
                  + [box(SCOPE_X - r - 0.42, SCOPE_X - r - 0.34, SCOPE_Y - 0.20,
                         SCOPE_Y + 0.20, -2.60, -2.20, 'optic')]))

    # ---------------- 与 v1 同名的空骨骼（以后想接进游戏可以直接掉包） ----------------
    B.append(bone('camera', (0.0, BORE, -2.40), 'body', []))
    B.append(bone('move', (0.0, BORE, 0.0), 'root', []))
    B.append(bone('root', (0.0, BORE, 0.0), None, []))
    return B


def build_geo():
    return {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.mosin_m9130',
                'texture_width': TEX,
                'texture_height': TEX,
                'visible_bounds_width': 8,
                'visible_bounds_height': 4,
                'visible_bounds_offset': [0, 1.5, -4],
            },
            'bones': build_bones(),
        }],
    }


# ==================================================================== 动画
BOLT_LIFT = 88.0        # 拉机柄抬起角（绕枪管轴）
BOLT_BACK = 1.90        # 机体后拉量
CASE_EXTRACT = 1.05     # 抽壳行程（弹壳退到装填口正下方 ⇒ 从上面看得见）
CASE_RISE = 0.85        # 抬出装填口
# round_in 的两个关键位（相对静止位「弹膛中心」的偏移，由中心坐标自动换算）
ABOVE_PORT = tuple(round(ABOVE_PORT_C[i] - CHAMBER[i], 4) for i in range(3))
SEATED = tuple(round(ROUND_TOP_C[i] - CHAMBER[i], 4) for i in range(3))
# round_top 被顶进弹膛的偏移（弹仓最上一发 → 弹膛）
FEED = tuple(round(CHAMBER[i] - ROUND_TOP_C[i], 4) for i in range(3))


def _kf(t, **kw):
    return (t, {k: tuple(float(x) for x in v) for k, v in kw.items()})


def _bedrock(bones):
    """[(t, {通道: 值})] → Bedrock/GeckoLib 的 {骨骼: {通道: {时刻: [x,y,z]}}}

    ★ 嵌套顺序不能写反（仓库里 awp/mosin 的动画文件就是这个顺序）：
      骨骼 → rotation|position|scale → 时间字符串 → 值
    """
    out = {}
    for bone, kfs in bones.items():
        ch_out = {}
        for t, ch in kfs:
            key = ('%.4f' % t).rstrip('0').rstrip('.') or '0'
            for k, v in ch.items():
                ch_out.setdefault(k, {})[key] = [round(float(x), 4) for x in v]
        out[bone] = ch_out
    return out


def anim_bolt(name, loop, open_hold=False):
    """拉栓：抬柄 → 后拉（弹壳被抽出、看得见）→ 抛壳 → 前推（把弹仓最上一发顶进弹膛）。"""
    if open_hold:
        return name, {'loop': 'hold_on_last_frame', 'animation_length': 0.60, 'bones': _bedrock({
            'bolt': [_kf(0.00, rotation=(0, 0, 0), position=(0, 0, 0)),
                     _kf(0.16, rotation=(0, 0, BOLT_LIFT)),
                     _kf(0.40, position=(0, 0, BOLT_BACK))],
            'casing': [_kf(0.00, position=(0, 0, 0)),
                       _kf(0.40, position=(0, 0, CASE_EXTRACT))],
        })}
    return name, {'loop': loop, 'animation_length': 1.20, 'bones': _bedrock({
        'bolt': [_kf(0.00, rotation=(0, 0, 0), position=(0, 0, 0)),
                 _kf(0.16, rotation=(0, 0, BOLT_LIFT)),
                 _kf(0.34, position=(0, 0, BOLT_BACK)),
                 _kf(0.60, position=(0, 0, BOLT_BACK)),
                 _kf(0.92, position=(0, 0, 0)),
                 _kf(1.12, rotation=(0, 0, 0))],
        # 空弹壳：跟着机体后退（在装填口里看得见）→ 抬出 → 往右上翻滚抛走 → 缩没
        'casing': [_kf(0.00, position=(0, 0, 0), rotation=(0, 0, 0)),
                   _kf(0.34, position=(0, 0, CASE_EXTRACT)),
                   _kf(0.44, position=(0, CASE_RISE, CASE_EXTRACT), rotation=(25, 0, 0)),
                   _kf(0.54, position=(0.68, 1.55, CASE_EXTRACT), rotation=(150, 60, 30)),
                   _kf(0.66, position=(1.45, 0.95, CASE_EXTRACT), rotation=(330, 180, 90)),
                   _kf(0.76, position=(2.05, 0.30, CASE_EXTRACT), rotation=(520, 300, 150),
                       scale=(0.6, 0.6, 0.6)),
                   _kf(0.82, position=(2.15, 0.18, CASE_EXTRACT), rotation=(560, 320, 160),
                       scale=(0, 0, 0))],
        # ★ 弹仓最上一发被机体顶着往前、顺着弹膛坡上进膛（进膛后藏在机匣前桥里 ⇒ 自动看不见）
        'round_top': [_kf(0.00, position=(0, 0, 0)),
                      _kf(0.74, position=(0, 0, 0)),
                      _kf(0.80, position=(0, FEED[1] * 0.62, FEED[2] * 0.23)),
                      _kf(0.86, position=(0, FEED[1] * 0.93, FEED[2] * 0.66)),
                      _kf(0.94, position=FEED),
                      _kf(1.20, position=FEED)],
    })}


def anim_reload():
    """换弹：开栓 → 连压 3 发进弹仓 → 闭栓。"""
    bones = {
        'bolt': [_kf(0.00, rotation=(0, 0, 0), position=(0, 0, 0)),
                 _kf(0.18, rotation=(0, 0, BOLT_LIFT)),
                 _kf(0.42, position=(0, 0, BOLT_BACK)),
                 _kf(1.86, position=(0, 0, BOLT_BACK)),
                 _kf(2.10, position=(0, 0, 0)),
                 _kf(2.28, rotation=(0, 0, 0))],
    }
    rin = []
    t0 = 0.55
    for i in range(3):
        t = t0 + i * 0.42
        rin += [_kf(t + 0.00, position=ABOVE_PORT, scale=(0, 0, 0)),
                _kf(t + 0.04, position=ABOVE_PORT, scale=(1, 1, 1)),
                _kf(t + 0.16, position=ABOVE_PORT, scale=(1, 1, 1)),
                _kf(t + 0.34, position=SEATED, scale=(1, 1, 1)),
                _kf(t + 0.40, position=SEATED, scale=(0, 0, 0))]
    bones['round_in'] = rin
    return 'animation.mosin_m9130.reload', {'loop': False, 'animation_length': 2.40,
                                            'bones': _bedrock(bones)}


def build_anims():
    out = []
    out.append(anim_bolt('animation.mosin_m9130.bolt', False))
    out.append(anim_bolt('animation.mosin_m9130.bolt_open', 'hold_on_last_frame',
                         open_hold=True))
    out.append(anim_reload())
    out.append(('animation.mosin_m9130.fire', {
        'loop': False, 'animation_length': 0.30, 'bones': _bedrock({
            'trigger': [_kf(0.00, rotation=(0, 0, 0)),
                        _kf(0.07, rotation=(-12, 0, 0)),
                        _kf(0.22, rotation=(0, 0, 0))]})}))
    return {'format_version': '1.10.0', 'animations': {k: v for k, v in out}}


# ==================================================================== 贴图
def _jitter(x, y, rgb):
    k = 1 + ((x * 7 + y * 13) % 5 - 2) * 0.025
    return tuple(min(255, int(c * k)) for c in rgb)


def _paint(bands):
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name in bands:
        y, rgb, alpha = BANDS[name]
        for x in range(BAND_W):
            d.line([(x, y), (x, y + 9)], fill=_jitter(x, y, rgb) + (alpha,))
    d.rectangle([0, 0, TEX - 1, TEX - 1], outline=(0, 0, 0, 255))
    return img


# ==================================================================== 自检
def _inside(cubes, p, pad=0.0):
    for c in cubes:
        o, s = c['origin'], c['size']
        if all(o[i] - pad <= p[i] <= o[i] + s[i] + pad for i in range(3)):
            return True
    return False


def _top(bones, name):
    return max(c['origin'][1] + c['size'][1] for c in bones[name]['cubes'])


def main():
    geo = build_geo()
    anims = build_anims()
    bones = {b['name']: b for b in geo['minecraft:geometry'][0]['bones']}
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(KEEP, exist_ok=True)
    for d in (BUILD, KEEP):
        with io.open(os.path.join(d, GEO_NAME + '.geo.json'), 'w',
                     encoding='utf-8', newline='\n') as f:
            json.dump(geo, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with io.open(os.path.join(d, GEO_NAME + '.animation.json'), 'w',
                     encoding='utf-8', newline='\n') as f:
            json.dump(anims, f, ensure_ascii=False, indent=1)
            f.write('\n')
        _paint(BANDS).save(os.path.join(d, GEO_NAME + '.png'))
        _paint(GLOW_BANDS).save(os.path.join(d, GEO_NAME + '_glowmask.png'))

    ncube = sum(len(b['cubes']) for b in bones.values())
    print('莫辛纳甘 M91/30 v2：骨骼 %d / 方块 %d / 动画 %d'
          % (len(bones), ncube, len(anims['animations'])))
    zs = [c['origin'][2] + c['size'][2] for b in bones.values() for c in b['cubes']]
    z0 = [c['origin'][2] for b in bones.values() for c in b['cubes']]
    print('  bbox z[%.2f, %.2f]  全长 %.2f 像素 = %.2f 格（刺刀伸出枪口 %.2f 像素 = %.2f 格）'
          % (min(z0), max(zs), max(zs) - min(z0), (max(zs) - min(z0)) / 16.0,
             MUZZLE_Z - BAYONET_TIP, (MUZZLE_Z - BAYONET_TIP) / 16.0))
    print()
    print('★ 锚点自检：')
    print('  枪管轴线 y = %.2f（要求 %.2f）' % (BORE, BORE))
    print('  准星柱顶 / 表尺耳顶 y = %.2f（要求 %.2f）%s'
          % (_top(bones, 'barrel'), IRON_Y,
             'OK' if abs(_top(bones, 'barrel') - IRON_Y) < 1e-6 else '??'))
    print('  机匣顶 %.2f < 机瞄线 %.2f：%s' % (RCV_TOP, IRON_Y,
                                             'OK' if RCV_TOP < IRON_Y else '!! 挡住机瞄'))
    print('  枪口端面 %s 在枪口环里（空心 ⇒ 轴线上为 False 才对）：%s'
          % (MUZZLE_Z, _inside(bones['barrel']['cubes'], (0, BORE, MUZZLE_Z + 0.05))))
    print('  弹仓 pivot %s 在弹仓内腔（空心 ⇒ False 才对）：%s'
          % (MAG_PIVOT, _inside(bones['magazine']['cubes'], MAG_PIVOT)))
    print('  弹膛 %s 在 body 内（弹壳/待压弹静止时不可见）：%s'
          % (CHAMBER, _inside(bones['body']['cubes'], CHAMBER)))
    print('  左手护木锚点 %s 在 handguard 内：%s'
          % (HANDGUARD, _inside(bones['handguard']['cubes'], HANDGUARD)))
    print()
    print('★ v2 三项新要求自检：')
    # 1) 空心枪管：枪口环里必须是空的（除了发黑内壁）
    muz_cu = [c for c in bones['barrel']['cubes']
              if c['origin'][2] + c['size'][2] <= MUZZLE_IN + 1e-6]
    blocked = [p for p in [(0, BORE, MUZZLE_Z + 0.15), (0.07, BORE, MUZZLE_Z + 0.40),
                           (-0.07, BORE - 0.07, MUZZLE_Z + 0.70),
                           (0, BORE, MUZZLE_Z + 0.92)] if _inside(muz_cu, p)]
    print('  ① 圆形空心枪管：枪口内孔 ∅%.2f、孔深 %.2f（≈%.1f cm）；轴线上无实心块：%s'
          % (2 * (0.28 - 0.16), MUZZLE_IN - MUZZLE_Z,
             (MUZZLE_IN - MUZZLE_Z) * 6.25, 'OK' if not blocked else '?? %s' % blocked))
    # 2) 弹仓可见：装填口上方必须没有 body 的方块挡着
    over_port = [c for c in bones['body']['cubes']
                 if c['origin'][0] < RCV_IN and c['origin'][0] + c['size'][0] > -RCV_IN
                 and c['origin'][2] < PORT_Z[1] and c['origin'][2] + c['size'][2] > PORT_Z[0]
                 and c['origin'][1] + c['size'][1] > 1.90]
    print('  ② 弹仓可见子弹：装填口 z %.2f..%.2f、宽 %.2f；口上方遮挡块 %d 个（应为 0）'
          % (PORT_Z[0], PORT_Z[1], 2 * RCV_IN, len(over_port)))
    print('     机匣内半宽 %.3f == 枪机体半宽 %.3f（闭栓无侧缝）：%s'
          % (RCV_IN, RCV_IN, 'OK'))
    print('     闭栓时机体 %.2f..%.2f ⊃ 装填口 %.2f..%.2f：%s'
          % (-3.60, -1.10, PORT_Z[0], PORT_Z[1],
             'OK' if -3.60 <= PORT_Z[0] and -1.10 >= PORT_Z[1] else '!! 露缝'))
    print('     后拉 %.2f 后机体：%.2f..%.2f（完全让开装填口）：%s'
          % (BOLT_BACK, -3.60 + BOLT_BACK, -1.10 + BOLT_BACK,
             'OK' if -3.60 + BOLT_BACK > PORT_Z[1] else '??'))
    print('     弹仓内 3 发弹 y 0.86..1.38（上口 %.2f）+ 1 发在弹膛（静止不可见）'
          % MAG_MOUTH)
    # 3) 镜筒空心 + 玻璃 + 十字线
    holes = [(SCOPE_X, SCOPE_Y, -3.70), (SCOPE_X, SCOPE_Y, -3.00),
             (SCOPE_X, SCOPE_Y, -2.50), (SCOPE_X, SCOPE_Y, -1.60),
             (SCOPE_X, SCOPE_Y, -1.05), (SCOPE_X, SCOPE_Y, -0.80)]
    hits = []
    for p in holes:
        for c in bones['scope']['cubes']:
            if _inside([c], p):
                hits.append((p[2], c['uv']['up']['uv'][1]))
    only_glass = all(v == BANDS['glass'][0] for _, v in hits)
    print('  ③ 圆型空心镜筒：光轴 (%.2f, %.2f)；轴线上只碰到玻璃（%s）：%s'
          % (SCOPE_X, SCOPE_Y, 'OK' if only_glass else '??', hits))
    cnt_glass = len([c for c in bones['scope']['cubes']
                     if c['uv']['up']['uv'][1] == BANDS['glass'][0]])
    cnt_ret = len([c for c in bones['scope']['cubes']
                   if c['uv']['up']['uv'][1] == BANDS['reticle'][0]])
    print('     玻璃 %.0f 片 / 十字分划 %d 件（都在镜筒内部）' % (cnt_glass, cnt_ret))
    print()
    print('骨骼层级：')
    for n in ('root', 'move', 'body', 'barrel', 'bayonet', 'handguard', 'bolt', 'magazine',
              'rounds', 'round_top', 'round_in', 'trigger', 'casing', 'scope',
              'scope_elev', 'scope_wind', 'camera'):
        b = bones[n]
        print('  %-11s parent=%-10s pivot=%-24s cubes=%d'
              % (n, b.get('parent', '-'), '[%.2f,%.2f,%.2f]' % tuple(b['pivot']),
                 len(b['cubes'])))
    print()
    print('动画：')
    for k, a in anims['animations'].items():
        print('  %-34s loop=%-18s length=%.2fs  bones=%s'
              % (k, a['loop'], a['animation_length'], ','.join(a['bones'])))
    print()
    for d in (BUILD, KEEP):
        print('  ->', os.path.relpath(os.path.join(d, GEO_NAME + '.geo.json'), ROOT))
    print('  接着跑：python tools/geo2bbmodel.py mosin_m9130   '
          '→ 模型/hexalunar_%s.bbmodel（含动画）' % GEO_NAME)


if __name__ == '__main__':
    main()
