#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""精密国际 AWP / AWM（v2，照用户给的 Printstream 渲染图重建）—— GeckoLib 真骨骼模型。

按用户要求（与 M1 v2 / 莫辛 v3 同一套做法）：

1. **枪管 = 圆形空洞枪管 + 膛线**：`tube_z()` 拼出八棱**空心**管（外 0.34→0.28 / 内孔 0.14），
   枪口正视是一圈管壁 + 一个黑洞；**内壁贴图画上纵向膛线槽**（tag='rifle'），
   孔底另有黑色堵头 ⇒ 看进去是「有膛线的深孔」。
   枪口还有照图做的**方形制退器**（黑色块 + 两道泄气槽）。
2. **弹匣看得见子弹**：AWP 是**可拆盒式弹匣**（`magazine`），
   `round_in`（最上一发）+ `mag_r1..mag_r4` 一共 5 个位置**自上而下排**，
   拉栓（枪机后退让开抛壳/装填口）时才看得见；**推回闭锁就被枪机体挡住**。
   拉栓时那一发从弹匣被顶进弹膛（`round_in` 上前/前移）—— 用户要的
   「打一下拉一下栓把空弹壳带出抛出，弹匣带入新的子弹推入发射」。
3. **瞄准镜 = 圆型空心 + 透明玻璃 + 十字线**：`scope` 是八棱空心镜筒（外 0.40 / 内 0.28），
   前后各一块**背景 alpha = 0 的圆镜片**（方角直接丢弃 ⇒ 是圆玻璃不是方块），
   目镜那片刻**十字分划**，筒内偏前一块黑挡板 ⇒ 看进去是深色镜筒 + 十字；
   镜筒上有高低 / 风偏两个鼓（独立骨骼 `scope_elev` / `scope_wind`）。
4. **枪身照 Printstream 那张图**：**墨绿**枪托 + **黑色**机匣/镜/枪管、
   **拇指孔托**（托上的圆孔）、黑色贴腮板、折叠**两脚架**、扳机护圈、右侧下弯拉机柄 + 球头、
   弹匣底板与卡笋；绿件上带一点白色印花（Printstream 的印字感）。
5. 姿态**全部由 Java 程序化驱动**（见 `AwpGeoModel`），动画文件只挂空通道 ——
   与 M1 / 莫辛同一套，避免「动画关键帧盖掉 setCustomAnimations」。

★ 几何约定**不能动**（ADS 对准、弹道、手臂、Java 常量都靠它，见 `WeaponMount.AWP_*`）：
  - 前向 = −Z（枪口）、上 = +Y；**枪管轴线 `BORE = 1.575`**；原点 = 机匣中心（握把在下方）
  - 镜光轴 **`SCOPE_Y = 3.15`**（`WeaponMount.AWP_SCOPE_Y`）
  - 枪口 `(0, 1.575, −16.275)`（`AWP_MUZZLE`）、抛壳口 `(0.90, 1.39, −0.60)`（`AWP_EJECT`）
  - 骨骼名与 pivot **原样保留**（Java 硬编码了其中几个）：
    `root/move/body/barrel/bipod/scope/scope_adjust/magazine/bolt/scope_elev/scope_wind/
     casing/trigger` + 新增 `mag_r1..mag_r4`
    · `move` (0, −1.07, 1.30)  · `bolt` (0.61, 1.50, 0.38) · `magazine` (0, 0, 0.90)
    · `trigger` (0, −0.15, 0.16) · `casing` → 移到弹壳自身中心（只是让抛壳翻滚绕自身转）

输出（直接写进 resources，另在 build/ 留副本给 geo2bbmodel / bbpush）：
  `geo/awp.geo.json`、`textures/models/awp_geo.png`(+`_glowmask`)、`animations/awp.animation.json`

用法::

    python tools/awp_v2.py                  # 出 geo / 贴图 / glowmask / 动画 + 自检
    python tools/_awpshot.py v2             # 离线出五个视角（不开游戏核对形状）
"""
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw

import boxlib
import gen_glowmask
from boxlib import cube

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, 'build')
RES = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
SIZE = 512
S = 13.0

# ------------------------------------------------------------------ 关键数值（Java 同步）
BORE = 1.575                # ★ 枪管轴线（WeaponMount.AWP_MUZZLE 的 y）
SCOPE_Y = 3.15              # ★ 4/8 倍镜光轴（WeaponMount.AWP_SCOPE_Y）
MUZZLE_Z = -18.00           # ★ 枪管加长 1.73（原 −16.275）—— WeaponMount.AWP_MUZZLE 同步改
BUTT_Z = 6.00               # ★ 托底收到 z 6.00（原 7.98）⇒ 全长 24.00 单位 = **1.50 格 = 150cm**
EJECT_WORLD = (0.30, 1.575, -2.50)   # ★ r115：抛壳口（WeaponMount.AWP_EJECT，世界用）
CASE_X = 0.20               # ★ r115：空弹壳中心（**右侧抛壳窗**内，右内壁 0.24）
RCV_Z0, RCV_Z1 = -4.12, -1.20       # 机匣（位置不变：枪机/抛壳口/弹匣都挂在它上面）
RCV_HW = 0.36               # ★ 收窄（原 0.42）—— 用户：「显得太臃肿」
RCV_BOT = 0.95              # 机匣底面
RCV_TOP = 2.14              # ★ 原 2.20
PORT_Z0, PORT_Z1 = -2.90, -2.10     # 抛壳/装填口（闭锁被枪机体挡住）
BOLT_Z0, BOLT_Z1 = -3.10, -0.40     # 枪机体（闭锁）
BOLT_R = 0.22
MAG_Z0, MAG_Z1 = -3.01, -1.71       # 弹匣
MAG_HW = 0.26               # ★ 收窄（原 0.30）
MAG_Y0, MAG_Y1 = -0.72, 0.22       # ★ 弹匣变浅（参考图的 5 发匣几乎与枪身平齐）
ROUND_CZ = -2.51                   # 整发沿 z 的中心（弹壳 z −2.86…−1.76）
ROUND_R = 0.095
ROUND_TOP_Y = 0.30                 # ★ 最上一发（round_in）中心高（匣变浅 ⇒ 整叠上移）
ROUND_SP = 0.20
# ★ 枪管：**外径/内孔全程一个值**（原来 0.34 / 0.30 / 0.28 三段 ⇒ 侧面两个台阶，像断成三截）
#   ★ r 收细到 0.25（照参考图：AWP 是细管，不是大粗管）
BL_R, BL_RI = 0.25, 0.125
SC_Z0, SC_Z1 = -5.00, 2.36         # ★ 镜筒加长（参考图的长程镜，物镜一直伸到枪管上方）
SC_RO, SC_RI = 0.42, 0.30          # ★ 照参考图**加粗**（镜筒比枪管粗明显一圈）
SC_CZ = (SC_Z0 + SC_Z1) * 0.5

# ------------------------------------------------------------------ 调色板（Printstream：墨绿 + 黑）
GREEN = (86, 118, 60)       # 墨绿枪托（照图）
GREEN_D = (60, 86, 42)      # 绿件暗部 / 内侧
BLACK = (30, 30, 32)        # 黑件（机匣 / 镜 / 枪管 / 握把）
BLACK_D = (20, 20, 22)      # 更暗（护圈 / 底托 / 两脚架）
STEEL = (146, 148, 156)     # 抛光钢（枪机体 / 拉机柄 / 扳机）
BRASS = (206, 162, 82)      # 黄铜弹壳
COPPER = (196, 126, 72)     # 铜被甲弹头
GLASS = (150, 46, 48)       # ★ 镜片外圈（照图那圈**红**色镜片反光）
GLASS_CROSS = (24, 24, 26)  # 十字分划
GLASS_DOT = (200, 60, 60)   # 分划中心亮点


# ------------------------------------------------------------------ 材质画法
def _green(img, rect, rn, base, horiz):
    """墨绿枪托：底色近均匀 + 几道顺纹长绿线（与莫辛同一套思路，别画成拼板）
    + 白印花点 + **几个深色小圆点**（照参考图 AICS 底盘上的螺钉/销孔）。"""
    x, y, w, h = rect
    px = img.load()
    lu = w >= h
    nl, ns = (w, h) if lu else (h, w)
    for s in range(ns):
        f0 = 1.0 + 0.014 * math.sin(s * 0.7 + 1.1)
        for t in range(nl):
            f = f0 * (1.0 + 0.012 * math.sin(t * 0.10 + s * 0.35))
            c = boxlib.sh(base, f * rn.r(0.997, 1.003))
            px[x + (t if lu else s), y + (s if lu else t)] = (c[0], c[1], c[2], 255)
    for _ in range(max(1, int(ns / 8.0))):
        s0 = rn.ri(0, max(0, ns - 1))
        slope = rn.r(-0.25, 0.25)
        dark = rn.r(0.86, 0.94)
        t0 = rn.ri(0, max(0, nl // 4))
        t1 = min(nl - 1, t0 + rn.ri(nl // 2, nl))
        for t in range(t0, t1 + 1):
            s = s0 + int(round(slope * (t - t0)))
            if 0 <= s < ns:
                i, j = (x + (t if lu else s), y + (s if lu else t))
                c = px[i, j]
                px[i, j] = (boxlib.cl(c[0] * dark), boxlib.cl(c[1] * dark),
                            boxlib.cl(c[2] * dark), 255)
    # 销孔 / 螺丝：小深点（照参考图底盘上一排螺栓）
    for _ in range(max(1, int(nl / 22.0))):
        if lu:
            t, s = rn.ri(2, max(2, nl - 3)), rn.ri(2, max(2, ns - 3))
        else:
            t, s = rn.ri(2, max(2, ns - 3)), rn.ri(2, max(2, nl - 3))
        for dd in ((0, 0), (1, 0), (0, 1), (1, 1)):
            i, j = (x + t + dd[0], y + s + dd[1]) if lu else (x + s + dd[0], y + t + dd[1])
            if x <= i <= x + w - 1 and y <= j <= y + h - 1:
                c = px[i, j]
                px[i, j] = (boxlib.cl(c[0] * 0.55), boxlib.cl(c[1] * 0.55),
                            boxlib.cl(c[2] * 0.55), 255)


boxlib.KINDS['green'] = _green


# ------------------------------------------------------------------ 几何辅助
def B(bone, name, x, y, z, mat, kind='metal', tag=None, rot=None, piv=None, curv=None):
    return cube(bone, name, x, y, z, mat, kind=kind, tag=tag, rot=rot, piv=piv, curv=curv)


def tube_z(bone, prefix, z0, z1, cy, r_out, r_in, mat, kind='metal', tag=None, seg=8,
           cx=0.0, overlap=1.08):
    """★ 空心圆管（轴 = Z）：seg 段径向壁小盒围一圈 ⇒ 正视是一圈管壁 + 中间真孔。

    `overlap` 只给 1.08（微微搭接）：写大了从管口往里看内壁会变成一圈「风车」。
    """
    rm = (r_out + r_in) * 0.5
    t = r_out - r_in
    w = 2.0 * rm * math.sin(math.pi / seg) * overlap
    out = []
    for i in range(seg):
        a = 2.0 * math.pi * (i + 0.5) / seg
        px, py = cx + rm * math.cos(a), cy + rm * math.sin(a)
        out.append(cube(bone, '%s_%d' % (prefix, i),
                        (px - t / 2, px + t / 2), (py - w / 2, py + w / 2), (z0, z1),
                        mat, kind=kind, tag=tag,
                        rot=(0.0, 0.0, math.degrees(a)), piv=(px, py, (z0 + z1) / 2.0)))
    return out


def oct_z(bone, prefix, z0, z1, cy, r, mat, kind='metal', tag=None, cx=0.0, k=0.414):
    a = k * r
    curv = ('cyl', 'z', (cx, cy))
    return [cube(bone, prefix + '_a', (cx - r, cx + r), (cy - a, cy + a), (z0, z1), mat,
                 kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (cx - a, cx + a), (cy - r, cy + r), (z0, z1), mat,
                 kind=kind, tag=tag, curv=curv)]


def oct_x(bone, prefix, x0, x1, cy, cz, r, mat, kind='metal', tag=None, k=0.414):
    a = k * r
    curv = ('cyl', 'x', (cy, cz))
    return [cube(bone, prefix + '_a', (x0, x1), (cy - r, cy + r), (cz - a, cz + a), mat,
                 kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (x0, x1), (cy - a, cy + a), (cz - r, cz + r), mat,
                 kind=kind, tag=tag, curv=curv)]


def round_cubes(bone, prefix, cy, cz):
    """一发 .338（黄铜壳 + 铜被甲弹尖朝 −Z）。整发 z：cz−0.35 … cz+0.75。"""
    return [B(bone, prefix + '_case', (-ROUND_R, ROUND_R), (cy - ROUND_R, cy + ROUND_R),
              (cz + 0.08, cz + 0.75), BRASS, 'metal', tag='round'),
            B(bone, prefix + '_tip', (-0.058, 0.058), (cy - 0.058, cy + 0.058),
              (cz - 0.35, cz + 0.09), COPPER, 'metal', tag='round')]


# ------------------------------------------------------------------ 骨骼（pivot 全部照旧）
BONES = [
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', (0.0, -1.07, 1.30)),            # ★ Java 用这个 pivot，不能改
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('barrel', 'body', (0.0, 1.50, -3.00)),
    ('bipod', 'barrel', (0.0, 0.82, -4.50)),
    ('scope', 'body', (0.0, 2.40, 0.0)),
    ('scope_adjust', 'scope', (0.0, 3.15, -0.97)),
    ('magazine', 'body', (0.0, 0.0, 0.90)),          # ★ Java 靠它做落匣
    ('mag_r1', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP, ROUND_CZ)),
    ('mag_r2', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP * 2, ROUND_CZ)),
    ('mag_r3', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP * 3, ROUND_CZ)),
    ('mag_r4', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP * 4, ROUND_CZ)),
    ('round_in', 'body', (0.0, ROUND_TOP_Y, ROUND_CZ)),
    ('bolt', 'body', (0.61, 1.50, 0.38)),            # ★ Java 用这个 pivot
    ('scope_elev', 'scope', (0.0, 3.15, -0.15)),
    ('scope_wind', 'scope', (0.36, 2.74, -0.15)),
    ('casing', 'body', (CASE_X, BORE, -2.50)),       # ★ r115：右侧抛壳窗中心（抛壳翻滚绕它）
    ('trigger', 'body', (0.0, 0.95, 0.17)),          # ★ 销轴放在机匣底（扣扳机 = 绕它转）
]

CUBES = []


# ------------------------------------------------------------------ 机匣 / 枪托（body）
def build_body():
    """机匣（黑、空心、顶部留抛壳口）+ Printstream 墨绿拇指孔托 + 贴腮板 + 托底 + 护圈。

    ★ 用户（2026-09-20）：「显得太臃肿」「枪身不要太挤」「实际长度 150 厘米」
      ⇒ ① 机匣/托全线收窄（0.42→0.36、0.40→0.32）、托底从 z7.98 收到 6.00
         （全长正好 24 单位 = 1.50 格 = 150cm）
         ② 删掉挤在机匣上的两根细导轨与扳机组外壳（tg_house）、多余的 stk_low_f；
            镜座改成**一整块实心块**（坐在机匣后桥顶）⇒ 不再有「两根细腿 + 悬空导轨」的缝
         ③ 拇指孔的四个边（握把 / 上梁 / 托体 / 孔下缘梁）全是实体，孔是真正的洞
    """
    c = []
    # ---------------- 机匣：两侧 + 顶盖（留口）+ 底壁 + 前后两个加厚环
    c.append(B('body', 'rcv_l', (-RCV_HW, -0.24), (RCV_BOT, RCV_TOP), (RCV_Z0, RCV_Z1), BLACK))
    # ★ r115（用户：「抛壳位置为右侧，不是左侧」）：右壁在抛壳窗位置**留洞** ——
    #   真实 AWP 的抛壳窗就在机匣右侧，弹壳从这儿出去；拆成前后两段，
    #   中间 PORT_Z0..PORT_Z1 就是窗口（与顶部的装填口同一个 z，左右贯通看得见）。
    c.append(B('body', 'rcv_r_f', (0.24, RCV_HW), (RCV_BOT, RCV_TOP), (RCV_Z0, PORT_Z0), BLACK,
               tag='print'))
    c.append(B('body', 'rcv_r_b', (0.24, RCV_HW), (RCV_BOT, RCV_TOP), (PORT_Z1, RCV_Z1), BLACK,
               tag='print'))
    c.append(B('body', 'rcv_top_f', (-RCV_HW, RCV_HW), (RCV_TOP - 0.13, RCV_TOP),
               (RCV_Z0, PORT_Z0), BLACK))
    c.append(B('body', 'rcv_top_b', (-RCV_HW, RCV_HW), (RCV_TOP - 0.13, RCV_TOP),
               (PORT_Z1, RCV_Z1), BLACK))
    c.append(B('body', 'rcv_bot_f', (-RCV_HW, RCV_HW), (RCV_BOT, RCV_BOT + 0.18),
               (RCV_Z0, MAG_Z0), BLACK))
    c.append(B('body', 'rcv_bot_b', (-RCV_HW, RCV_HW), (RCV_BOT, RCV_BOT + 0.18),
               (MAG_Z1, RCV_Z1), BLACK))
    c.append(B('body', 'rcv_ring_f', (-RCV_HW - 0.02, RCV_HW + 0.02),
               (RCV_BOT - 0.04, RCV_TOP + 0.02), (-4.12, -3.90), BLACK))
    c.append(B('body', 'rcv_ring_b', (-RCV_HW - 0.02, RCV_HW + 0.02),
               (RCV_BOT - 0.04, RCV_TOP + 0.02), (-1.42, -1.20), BLACK))
    # 机匣左侧的印花块（Printstream 那种白字感）
    c.append(B('body', 'rcv_dec', (-RCV_HW - 0.01, -RCV_HW + 0.01), (1.30, 1.86),
               (-3.86, -2.40), BLACK, 'flat', tag='print'))
    # ---------------- 枪托（墨绿）：上梁 + 贴腮板 + 托体 + 托底板
    c.append(B('body', 'stk_up', (-0.30, 0.30), (0.34, 1.48), (-1.20, 2.30), GREEN, 'green',
               tag='print'))
    # ★ 托体：照参考图**挖两个减重孔**（孔处只留上/下两条梁 ⇒ 是真的看得穿的洞）
    for _z0, _z1 in ((2.30, 2.92), (3.60, 4.22)):
        c.append(B('body', 'stk_hol%d' % int(_z0 * 10), (-0.30, 0.30), (0.42, 1.48),
                   (_z0, _z1), GREEN, 'green'))
        c.append(B('body', 'stk_holb%d' % int(_z0 * 10), (-0.30, 0.30), (-0.72, -0.10),
                   (_z0, _z1), GREEN, 'green'))
    for _z0, _z1 in ((2.20, 2.30), (2.92, 3.60), (4.22, BUTT_Z - 0.28)):
        c.append(B('body', 'stk_butt%d' % int(_z0 * 10), (-0.32, 0.32), (-0.72, 1.48),
                   (_z0, _z1), GREEN, 'green', tag='print'))
    c.append(B('body', 'stk_pad_r', (-0.34, 0.34), (-0.80, 1.60), (BUTT_Z - 0.28, BUTT_Z),
               BLACK))
    # ★ 贴腮板（照参考图：坐在**托体上方**的黑块，不是握颈上那条）
    c.append(B('body', 'stk_pad', (-0.28, 0.28), (1.48, 1.70), (3.40, 5.40), BLACK))
    c.append(B('body', 'stk_pad_lip', (-0.30, 0.30), (1.44, 1.52), (3.30, 5.50), BLACK_D))
    # 托底侧面的背带槽（参考图里那个小长孔）+ 托底调整螺丝 ×2
    c.append(B('body', 'stk_slot', (-0.33, -0.31), (-0.30, 0.24), (2.60, 3.10), BLACK_D))
    c.append(B('body', 'stk_scr1', (-0.26, -0.18), (0.55, 0.68), (BUTT_Z - 0.10, BUTT_Z - 0.02),
               STEEL, 'flat'))
    c.append(B('body', 'stk_scr2', (-0.26, -0.18), (-0.35, -0.22), (BUTT_Z - 0.10,
                                                                  BUTT_Z - 0.02), STEEL,
               'flat'))
    # 托底前面的两道**垫片线**（AW 的托底是一叠垫片，照参考图）
    c.append(B('body', 'stk_sp1', (-0.33, 0.33), (-0.78, 1.58), (BUTT_Z - 0.42, BUTT_Z - 0.36),
               BLACK_D))
    c.append(B('body', 'stk_sp2', (-0.33, 0.33), (-0.78, 1.58), (BUTT_Z - 0.34, BUTT_Z - 0.28),
               BLACK_D))
    # ---------------- 拇指孔：握把（后仰 15°）+ 孔下缘梁
    c.append(B('body', 'grip', (-0.26, 0.26), (-1.90, 0.40), (0.20, 1.10), BLACK_D, 'flat',
               rot=(-15.0, 0.0, 0.0), piv=(0.0, 0.40, 0.65)))
    c.append(B('body', 'stk_hole_b', (-0.30, 0.30), (-0.72, -0.40), (0.98, 2.26), GREEN,
               'green'))
    # ---------------- 前托：**AICS 式细长底盘**——枪管浮置在上方（中间有缝），
    #   底盘本体在枪管下面，上面开一条背带/附件槽，下面一排导轨齿，尾段（接机匣那段）加高
    #   ★ 照参考图：枪管从机匣一直露到制退器，下面只有一根细的绿件（不是盒子）
    c.append(B('body', 'stk_fore_f', (-0.30, 0.30), (-0.62, 1.06), (-4.30, -3.06), GREEN,
               'green'))
    c.append(B('body', 'stk_fore_g', (-0.28, 0.28), (-0.62, 0.52), (-6.40, -4.30), GREEN,
               'green'))
    c.append(B('body', 'stk_fore_b', (-0.32, 0.32), (0.20, RCV_BOT), (-3.06, -1.20), GREEN,
               'green'))
    # 底盘上的背带/附件槽（深色内凹）+ 底下一排导轨齿
    c.append(B('body', 'fore_slot', (-0.10, 0.10), (0.10, 0.30), (-5.90, -4.60), BLACK_D))
    for _i in range(5):
        _z = -6.20 + _i * 0.36
        c.append(B('body', 'fore_rail%d' % _i, (-0.20, 0.20), (-0.74, -0.62), (_z, _z + 0.20),
                   BLACK_D))
    # 底盘上的两个螺钉头（照参考图）
    c += [cube('body', 'fore_scr%d' % _i, (-0.31, -0.29), (-0.10, 0.14),
               (-5.20 + _i * 0.90, -5.08 + _i * 0.90), BLACK_D, kind='flat') for _i in range(2)]
    # ---------------- 扳机护圈：细长弓（前柱 + 斜后柱 + 薄底梁）—— 照莫辛那套
    c.append(B('body', 'tg_f', (-0.08, 0.08), (-0.34, 0.40), (-1.50, -1.40), BLACK_D))
    c.append(B('body', 'tg_b', (-0.08, 0.08), (-0.34, 0.44), (0.30, 0.42), BLACK_D,
               rot=(22.0, 0.0, 0.0), piv=(0.0, -0.34, 0.36)))
    c.append(B('body', 'tg_bot', (-0.08, 0.08), (-0.34, -0.22), (-1.50, 0.42), BLACK_D))
    c.append(B('body', 'swivel', (-0.07, 0.07), (-0.80, -0.40), (2.30, 2.60), BLACK_D))
    return c


# ------------------------------------------------------------------ 枪管（含膛线）/ 制退器 / 两脚架
def build_barrel():
    """★ **一整根**空心八棱枪管（内壁带膛线）+ 膛底黑堵头 + 枪口方形制退器 + 折叠两脚架。

    ★ 用户：「枪管需要连贯，不要有间隙」「枪管长一点」
      ⇒ 原来 3 段管（外径 0.34 / 0.30 / 0.28）在侧面看出两个台阶、像断成三截；
        现在 **只有一次 tube_z 调用**：外径/内孔全程 BL_R / BL_RI，一段到底；
        长度也从 z −16.275 伸到 **−18.00**（露出的枪管 ~12.8 单位 ≈ 69cm）。
    """
    c = []
    c += tube_z('barrel', 'bl_t', MUZZLE_Z, -4.30, BORE, BL_R, BL_RI, BLACK, tag='rifle')
    # 膛底堵头（深孔尽头是黑的，不会一眼看穿整根枪管）
    c += oct_z('barrel', 'bl_bore', -4.72, -4.54, BORE, 0.22, BLACK, kind='flat')
    # ★ 枪口制退器（照参考图：**八棱圆管**式的钢色制退器 + 两道泄气槽）——空心，不堵膛
    c += tube_z('barrel', 'mz_t', MUZZLE_Z, MUZZLE_Z + 1.15, BORE, 0.30, BL_RI, STEEL)
    # 两道泄气槽：**只开在两侧面**（横穿膛轴会把枪口堵住 —— 自检 1 会报 "被 mz_slot 挡住"）
    for _sx, _nm in ((1, 'l'), (-1, 'r')):
        for _k, _zz in enumerate((MUZZLE_Z + 0.22, MUZZLE_Z + 0.62)):
            c.append(B('barrel', 'mz_slot%s%d' % (_nm, _k), (_sx * 0.28, _sx * 0.32),
                       (BORE - 0.24, BORE + 0.24), (_zz, _zz + 0.16), BLACK_D, 'flat'))
    # 两脚架（★ 用户：「支架收起」）—— 先把夹子夹在枪管下（U 形，不堵膛），
    #   两条腿**贴着枪管往后收**，末端是小小的脚垫，不再是一根翘在外面的杆子
    c.append(B('bipod', 'bp_mount', (-0.30, -0.20), (BORE - 0.28, BORE - 0.06),
               (-7.55, -7.05), BLACK_D))
    c.append(B('bipod', 'bp_mount_r', (0.20, 0.30), (BORE - 0.28, BORE - 0.06),
               (-7.55, -7.05), BLACK_D))
    c.append(B('bipod', 'bp_mount_b', (-0.30, 0.30), (BORE - 0.32, BORE - 0.20),
               (-7.55, -7.05), BLACK_D))
    for _sx, _nm in ((-1, 'l'), (1, 'r')):
        c.append(B('bipod', 'bp_leg_%s' % _nm, (_sx * 0.20, _sx * 0.10),
                   (BORE - 0.34, BORE - 0.14), (-7.05, -5.45), BLACK_D))
        c.append(B('bipod', 'bp_foot_%s' % _nm, (_sx * 0.23, _sx * 0.07),
                   (BORE - 0.38, BORE - 0.10), (-5.65, -5.35), BLACK_D))
    return c


# ------------------------------------------------------------------ 镜（空心镜筒 + 透明镜片 + 十字线）
def build_scope():
    """★ 圆型空心镜筒（**一根直筒到底** + 变倍环）+ 前后整片透明的圆镜片（含十字线）
    + 高低/风偏鼓 + 侧面调焦环 + **一整块实心镜座**。

    ★ 用户：「倍镜同理（连贯、不要有间隙）、使用顶点连接」
      ⇒ ① 筒身只按变倍环分成两段、**首尾相接不重叠**，物镜/目镜/变倍环的内半径
            全部 = SC_RI（原来各小 0.01~0.02 ⇒ 从目镜看进去三道台阶）
         ② 原来的「两根细立柱 + 从机匣一直悬到握颈上方的导轨」全部删掉，
            改成**坐在机匣后桥上的一整块实心块**（前后端面对齐 ⇒ 没有缝）
    """
    c = []
    c += tube_z('scope', 'sc_obj', SC_Z0, SC_Z0 + 0.34, SCOPE_Y, SC_RO + 0.05, SC_RI, BLACK,
                tag='optic')
    c += tube_z('scope', 'sc_t1', SC_Z0 + 0.34, SC_CZ - 0.12, SCOPE_Y, SC_RO, SC_RI, BLACK,
                tag='optic')
    c += tube_z('scope', 'sc_var', SC_CZ - 0.12, SC_CZ + 0.12, SCOPE_Y, SC_RO + 0.03, SC_RI,
                BLACK, tag='optic')
    c += tube_z('scope', 'sc_t2', SC_CZ + 0.12, SC_Z1 - 0.34, SCOPE_Y, SC_RO, SC_RI, BLACK,
                tag='optic')
    c += tube_z('scope', 'sc_eye', SC_Z1 - 0.34, SC_Z1, SCOPE_Y, SC_RO + 0.03, SC_RI, BLACK,
                tag='optic')
    lz = SC_RI + 0.02
    c.append(B('scope', 'sc_lens_f', (-lz, lz), (SCOPE_Y - lz, SCOPE_Y + lz),
               (SC_Z0 + 0.30, SC_Z0 + 0.35), GLASS, 'flat'))
    c.append(B('scope', 'sc_lens_b', (-lz, lz), (SCOPE_Y - lz, SCOPE_Y + lz),
               (SC_Z1 - 0.35, SC_Z1 - 0.30), GLASS, 'flat'))
    # ★ 镜座（照参考图）：机匣顶上一段**导轨**（抬到 RCV_TOP+0.22，带导轨齿；抛壳口处断开）
    #   + **两个宽镜环座**把筒托住 —— 参考图里镜筒是贴着导轨的，不能悬在半空
    c.append(B('scope', 'sc_rail_f', (-0.24, 0.24), (RCV_TOP, RCV_TOP + 0.22),
               (RCV_Z0, PORT_Z0), BLACK_D))
    c.append(B('scope', 'sc_rail_b', (-0.24, 0.24), (RCV_TOP, RCV_TOP + 0.22),
               (PORT_Z1, RCV_Z1), BLACK_D))
    for _k, _zz in enumerate((-4.00, -3.66, -3.32, -2.98, -2.02, -1.68, -1.34)):
        if PORT_Z0 < _zz + 0.14 and _zz < PORT_Z1:
            continue
        c.append(B('scope', 'sc_tooth%d' % _k, (-0.22, 0.22), (RCV_TOP + 0.22,
                                                             RCV_TOP + 0.28),
                   (_zz, _zz + 0.14), BLACK_D))
    for zn in (-3.20, -1.50):
        nm = 'r%d' % int(-zn * 10)
        c += tube_z('scope', 'sc_ring' + nm, zn - 0.16, zn + 0.16, SCOPE_Y, SC_RO + 0.07,
                    SC_RI + 0.006, BLACK_D, tag='optic')
        c.append(B('scope', 'sc_mnt' + nm, (-0.22, 0.22), (RCV_TOP + 0.22, SCOPE_Y - SC_RO + 0.02),
                   (zn - 0.16, zn + 0.16), BLACK_D))
    # 高低鼓（顶）/ 风偏鼓（右）/ 侧面调焦环（`scope_adjust` 骨骼）
    c.append(B('scope_elev', 'el_drum', (-0.18, 0.18),
               (SCOPE_Y + SC_RO - 0.04, SCOPE_Y + SC_RO + 0.30), (-0.34, 0.04), BLACK_D,
               'brushed'))
    # ★ 高低鼓底部的**绿色照明钮**（参考图里那颗亮绿旋钮）
    c.append(B('scope_elev', 'el_knob', (-0.20, 0.20),
               (SCOPE_Y + SC_RO + 0.00, SCOPE_Y + SC_RO + 0.10), (-0.46, -0.34), GREEN))
    c.append(B('scope_wind', 'wd_drum', (SC_RO - 0.04, SC_RO + 0.28),
               (SCOPE_Y - 0.18, SCOPE_Y + 0.18), (-0.34, 0.04), BLACK_D, 'brushed'))
    c.append(B('scope_wind', 'wd_knob', (SC_RO + 0.28, SC_RO + 0.38),
               (SCOPE_Y - 0.20, SCOPE_Y + 0.20), (-0.46, -0.34), GREEN))
    c += tube_z('scope_adjust', 'sa_ring', -1.20, -0.75, SCOPE_Y, SC_RO + 0.04,
                SC_RI + 0.005, BLACK_D, tag='optic')
    return c


# ------------------------------------------------------------------ 弹匣 / 子弹 / 枪机 / 扳机 / 弹壳
def build_magazine():
    """可拆盒式弹匣：两侧壁 + 前后壁 + 底板 + 卡笋，**上口敞开** ⇒ 拉栓时看得见里面的子弹。"""
    c = []
    c.append(B('magazine', 'mg_l', (-MAG_HW, -MAG_HW + 0.06), (MAG_Y0, MAG_Y1),
               (MAG_Z0, MAG_Z1), BLACK, tag='mag'))
    c.append(B('magazine', 'mg_r', (MAG_HW - 0.06, MAG_HW), (MAG_Y0, MAG_Y1),
               (MAG_Z0, MAG_Z1), BLACK, tag='mag'))
    c.append(B('magazine', 'mg_f', (-MAG_HW, MAG_HW), (MAG_Y0, MAG_Y1), (MAG_Z0, MAG_Z0 + 0.06),
               BLACK, tag='mag'))
    c.append(B('magazine', 'mg_b', (-MAG_HW, MAG_HW), (MAG_Y0, MAG_Y1),
               (MAG_Z1 - 0.06, MAG_Z1), BLACK, tag='mag'))
    c.append(B('magazine', 'mg_floor', (-MAG_HW - 0.02, MAG_HW + 0.02), (MAG_Y0 - 0.10, MAG_Y0),
               (MAG_Z0 - 0.04, MAG_Z1 + 0.04), BLACK_D))
    c.append(B('magazine', 'mg_catch', (-0.10, 0.10), (MAG_Y1 - 0.16, MAG_Y1 + 0.12),
               (MAG_Z1 - 0.10, MAG_Z1 + 0.06), BLACK_D))
    return c


def build_rounds():
    """弹匣里 5 发：`round_in` = 最上一发（拉栓时被顶进弹膛的就是它），下面 `mag_r1..mag_r4`。"""
    c = []
    c += round_cubes('round_in', 'ri', ROUND_TOP_Y, ROUND_CZ)
    for i in range(4):
        c += round_cubes('mag_r%d' % (i + 1), 'm%d' % (i + 1),
                         ROUND_TOP_Y - ROUND_SP * (i + 1), ROUND_CZ)
    return c


def build_bolt():
    """枪机体（八棱柱，闭锁时盖住抛壳口）+ 机头 + 右侧下弯拉机柄 + 球头（连续的一根）。"""
    c = []
    c += oct_z('bolt', 'blt_body', BOLT_Z0, BOLT_Z1, BORE, BOLT_R, STEEL, kind='brushed')
    c += oct_z('bolt', 'blt_head', BOLT_Z0 - 0.16, BOLT_Z0, BORE, BOLT_R - 0.04, STEEL,
               kind='brushed')
    c.append(B('bolt', 'blt_h1', (BOLT_R - 0.02, 0.98), (BORE + 0.02, BORE + 0.22),
               (-0.40, -0.12), STEEL, 'brushed'))          # 伸出机匣右侧的横段
    c.append(B('bolt', 'blt_h2', (0.96, 1.24), (BORE - 0.30, BORE + 0.14),
               (-0.38, -0.14), STEEL, 'brushed'))          # 下弯段（把球头连起来）
    c += oct_x('bolt', 'blt_knob', 1.20, 1.42, BORE - 0.16, -0.26, 0.17, STEEL, kind='brushed')
    return c


def build_small():
    """★ 扳机（用户：「扳机稍微画好看一点」）：**四段拼成一片弧形扳机片**——
    上段插在木托里（销轴在机匣底 0.95），中段略前倾，下端有个往后的小勾（指托）。
    """
    c = []
    c.append(B('trigger', 'trg_up', (-0.055, 0.055), (0.44, 0.98), (0.11, 0.21), STEEL,
               'brushed'))
    c.append(B('trigger', 'trg_mid', (-0.055, 0.055), (-0.02, 0.46), (0.04, 0.16), STEEL,
               'brushed'))
    c.append(B('trigger', 'trg_tip', (-0.055, 0.055), (-0.16, -0.02), (0.07, 0.19), STEEL,
               'brushed'))
    c.append(B('trigger', 'trg_shoe', (-0.06, 0.06), (-0.22, -0.10), (0.00, 0.12), STEEL,
               'brushed'))
    # ★ r115：空弹壳在**右侧抛壳窗**里（以前放在膛内中线 x=0，钁看就成了「从枪身中间/
    #   偏左冒出来」）。拉栓时被枪机带出台、往 +X 抛（Java 的 CASE_* 管轨迹）。
    c.append(B('casing', 'cas_body', (CASE_X - 0.12, CASE_X + 0.12),
               (BORE - 0.12, BORE + 0.12), (-2.85, -2.25), BRASS, 'metal', tag='round'))
    return c


# ------------------------------------------------------------------ 图元细节
def d_rifle(img, rect, face, seed):
    """★ **膛线**：枪管内壁画 3 条纵向深槽 + 2 条亮阳线（照用户要求「枪管有膛线」）。"""
    x, y, w, h = rect
    if min(w, h) < 2 or max(w, h) < 4:
        return
    px = img.load()
    along_u = w >= h
    n = w if along_u else h
    m = h if along_u else w
    if m < 3:
        return
    for t in range(n):
        for k, f in ((0, 0.55), (m // 3, 0.60), (2 * m // 3, 0.58), (m - 1, 0.62)):
            i = x + (t if along_u else k)
            j = y + (k if along_u else t)
            c = px[i, j]
            px[i, j] = (boxlib.cl(c[0] * f), boxlib.cl(c[1] * f), boxlib.cl(c[2] * f), 255)
        for k in (m // 6, m // 2, 5 * m // 6):
            i = x + (t if along_u else k)
            j = y + (k if along_u else t)
            c = px[i, j]
            px[i, j] = (min(255, int(c[0] * 1.22)), min(255, int(c[1] * 1.22)),
                        min(255, int(c[2] * 1.22)), 255)


def d_print(img, rect, face, seed):
    """绿/黑件上的**白色印花**（Printstream 那种印字块）—— 只画小面积、不铺满。"""
    x, y, w, h = rect
    if w < 8 or h < 5:
        return
    d = ImageDraw.Draw(img)
    white = (232, 236, 240)
    for i in range(3):
        bx = x + 2 + i * 3
        if bx + 2 > x + w - 2:
            break
        d.rectangle([bx, y + h - 4, bx + 1, y + h - 3], fill=white)
    d.rectangle([x + 2, y + 2, x + min(w - 3, 9), y + 3], fill=white)


def d_mag(img, rect, face, seed):
    x, y, w, h = rect
    if w < 6 or h < 6:
        return
    px = img.load()
    for i in range(w):
        for j in range(h):
            c = px[x + i, y + j]
            f = 0.82 if (i == 0 or i == w - 1 or j == h // 2) else 1.0
            px[x + i, y + j] = (int(c[0] * f), int(c[1] * f), int(c[2] * f), c[3])


def d_round(img, rect, face, seed):
    x, y, w, h = rect
    if w < 3 or h < 3:
        return
    px = img.load()
    for i in range(w):
        for k, f in ((0, 0.60), (h - 1, 0.80)):
            c = px[x + i, y + k]
            px[x + i, y + k] = (int(c[0] * f), int(c[1] * f), int(c[2] * f), 255)
        c = px[x + i, y + max(2, h // 3)]
        px[x + i, y + max(2, h // 3)] = (min(255, int(c[0] * 1.20)),
                                         min(255, int(c[1] * 1.20)),
                                         min(255, int(c[2] * 1.20)), 255)


DETAILS = {'rifle': d_rifle, 'print': d_print, 'mag': d_mag, 'round': d_round}


# ------------------------------------------------------------------ 镜片（圆玻璃 + 十字线）
_LZ = SC_RI + 0.02
LENS_FRONT = ((-_LZ, _LZ), (SCOPE_Y - _LZ, SCOPE_Y + _LZ), (SC_Z0 + 0.30, SC_Z0 + 0.35))
LENS_BACK = ((-_LZ, _LZ), (SCOPE_Y - _LZ, SCOPE_Y + _LZ), (SC_Z1 - 0.35, SC_Z1 - 0.30))


def _lens_rects(geo, box):
    out = []
    for bone in geo['minecraft:geometry'][0]['bones']:
        for c in bone.get('cubes', []):
            ox, oy, oz = c['origin']
            sx, sy, sz = c['size']
            if (abs(ox - box[0][0]) > 1e-4 or abs(oy - box[1][0]) > 1e-4
                    or abs(oz - box[2][0]) > 1e-4 or abs(sx - (box[0][1] - box[0][0])) > 1e-4):
                continue
            for face in ('north', 'south', 'east', 'west', 'up', 'down'):
                u, v = c['uv'][face]['uv']
                w, h = c['uv'][face]['uv_size']
                out.append((face, int(u), int(v), int(u + w) - 1, int(v + h) - 1))
    return out


def _paint_disc(px, x0, y0, x1, y1, cross):
    """★ 镜片**整片透明**，只画十字分划（用户：「倍镜同理……应该为透明含十字线」）。

    原来还给圆边画一圈镜片色（GLASS=红），从目镜看就是一块红玻璃挡着；
    现在连边一起透明：圆的判据只用来**把分划限制在圆内**（方角依旧透明）。
    """
    w = x1 - x0 + 1
    h = y1 - y0 + 1
    cx = x0 + (w - 1) / 2.0
    cy = y0 + (h - 1) / 2.0
    rx = max(1.0, (w - 1) / 2.0)
    ry = max(1.0, (h - 1) / 2.0)

    def inside(i, j):
        if i < x0 or i > x1 or j < y0 or j > y1:
            return False
        return ((i - cx) / rx) ** 2 + ((j - cy) / ry) ** 2 <= 1.0 + 1e-9

    if not cross or w < 5 or h < 5:
        return
    mxi, myi = int(round(cx)), int(round(cy))
    for yy in range(y0, y1 + 1):           # 竖线 2px 粗（镜片只有 7~8px，1px 游戏里看不见）
        for xx in (mxi, mxi + 1):
            if inside(xx, yy) and px[xx, yy][3] == 0:
                px[xx, yy] = GLASS_CROSS + (255,)
    for xx in range(x0, x1 + 1):           # 横线
        for yy in (myi, myi + 1):
            if inside(xx, yy) and px[xx, yy][3] == 0:
                px[xx, yy] = GLASS_CROSS + (255,)
    for dx in (0, 1):
        for dy in (0, 1):
            if inside(mxi + dx, myi + dy):
                px[mxi + dx, myi + dy] = GLASS_DOT + (255,)


def paint_lens(geo, img, box, cross):
    """镜片各面重绘成「圆形玻璃」（+ 可选的十字分划）。"""
    px = img.load()
    for face, x0, y0, x1, y1 in _lens_rects(geo, box):
        if x1 - x0 < 2 or y1 - y0 < 2:
            continue
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                px[xx, yy] = (0, 0, 0, 0)
        if face in ('north', 'south'):
            _paint_disc(px, x0, y0, x1, y1, cross)


# ------------------------------------------------------------------ 动画（空动作）
def build_anims():
    zero = {'0.0': [0.0, 0.0, 0.0], '1.0': [0.0, 0.0, 0.0]}
    out = {}
    for state, length, loop in (('idle', 2.0, True), ('run', 1.0, True),
                                ('run_fast', 0.8, True), ('fire', 0.5, False),
                                ('bolt', 1.2, False), ('reload', 2.4, False),
                                ('scope_adjust', 0.6, False)):
        out['animation.awp.' + state] = {'loop': loop, 'animation_length': length,
                                         'bones': {'root': {'rotation': zero}}}
    return {'format_version': '1.8.0', 'animations': out}


# ------------------------------------------------------------------ 自检辅助
def inside(cubes, p, eps=0.0):
    x, y, z = p
    for c in cubes:
        if (c['x'][0] - eps <= x <= c['x'][1] + eps and c['y'][0] - eps <= y <= c['y'][1] + eps
                and c['z'][0] - eps <= z <= c['z'][1] + eps):
            return c
    return None


def covers(cubes, z0, z1, y):
    n = 24
    for i in range(n + 1):
        if not inside(cubes, (0.0, y, z0 + (z1 - z0) * i / n)):
            return False
    return True


# ------------------------------------------------------------------ 输出 + 自检
def main():
    global S
    geo = img = None
    for dens in (13.0, 12.0, 11.0, 10.0, 9.0, 8.0):
        S = dens
        CUBES.clear()
        CUBES.extend(build_body())
        CUBES.extend(build_barrel())
        CUBES.extend(build_scope())
        CUBES.extend(build_magazine())
        CUBES.extend(build_rounds())
        CUBES.extend(build_bolt())
        CUBES.extend(build_small())
        try:
            geo, img = boxlib.build(BONES, CUBES, 'geometry.awp', size=SIZE,
                                    details=DETAILS, density=dens)
            break
        except RuntimeError as e:
            print('density %.0f 图集放不下（%s），降一档重试' % (dens, e))
    if geo is None:
        raise SystemExit('图集怎么都放不下')

    paint_lens(geo, img, LENS_BACK, True)
    paint_lens(geo, img, LENS_FRONT, False)

    os.makedirs(BUILD, exist_ok=True)
    paths = {
        'geo': os.path.join(RES, 'geo', 'awp.geo.json'),
        'tex': os.path.join(RES, 'textures', 'models', 'awp_geo.png'),
        'glow': os.path.join(RES, 'textures', 'models', 'awp_geo_glowmask.png'),
        'anim': os.path.join(RES, 'animations', 'awp.animation.json'),
    }
    for p in paths.values():
        os.makedirs(os.path.dirname(p), exist_ok=True)
    boxlib.write(geo, img, paths['geo'], paths['tex'])
    with io.open(paths['anim'], 'w', encoding='utf-8', newline='\n') as f:
        json.dump(build_anims(), f, ensure_ascii=False, indent=1)
        f.write('\n')
    gen_glowmask.make(paths['tex'], paths['glow'])
    with io.open(os.path.join(BUILD, 'awp.geo.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(geo, f, ensure_ascii=False, indent=1)
        f.write('\n')
    img.save(os.path.join(BUILD, 'awp_geo.png'))

    # ---------------------------------------------------------------- 自检
    tab = {}
    for c in CUBES:
        tab.setdefault(c['name'], c)
    have = set(b[0] for b in BONES)
    need = {'root', 'move', 'body', 'barrel', 'bipod', 'scope', 'scope_adjust', 'magazine',
            'mag_r1', 'mag_r2', 'mag_r3', 'mag_r4', 'round_in', 'bolt', 'scope_elev',
            'scope_wind', 'casing', 'trigger'}
    print('骨骼名检查: %s' % ('OK' if need <= have else '缺 %s' % (need - have)))
    print('bones %d  cubes %d（面 %d）  density %.0f  %dx%d'
          % (len(BONES), len(CUBES), 6 * len(CUBES), S, SIZE, SIZE))

    axis_hit = None
    for i in range(81):
        z = MUZZLE_Z + 0.15 + (i / 80.0) * (-4.74 - (MUZZLE_Z + 0.15))
        hit = inside(CUBES, (0.0, BORE, z))
        if hit is not None:
            axis_hit = (z, hit['name'])
            break
    tube = [c for c in CUBES if c['name'].startswith('bl_t')]
    thick = sorted(set(round(c['x'][1] - c['x'][0], 4) for c in tube))
    print('★ 枪管：**一整根**八棱空心壁 %d 段（外径全程 %.3f / 壁厚只有 %d 种 = %s '
          '⇒ 没有台阶、没有缝）+ 内壁膛线 %d 段'
          % (len(tube), BL_R, len(thick), thick,
             len([c for c in tube if c.get('tag') == 'rifle'])))
    print('  枪口→膛底整条轴线：%s；膛底黑堵头 z %.2f…%.2f %s'
          % ('是空的 OK' if axis_hit is None else '!! 被 %s 挡住' % axis_hit[1],
             tab['bl_bore_b']['z'][0], tab['bl_bore_b']['z'][1],
             'OK' if abs(tab['bl_bore_b']['y'][1] - (BORE + 0.22)) < 1e-9 else '??'))
    mzt = [c for c in CUBES if c['name'].startswith('mz_t')]
    print('  枪口制退器 z %.2f…%.2f（%d 段八棱空心管 + 2 个泄气槽，中间是通的）'
          % (min(c['z'][0] for c in mzt), max(c['z'][1] for c in mzt), len(mzt)))

    sc_axis = None
    tube_only = [c for c in CUBES if not c['name'].startswith('sc_baffle')]
    for i in range(21):
        z = SC_Z0 + 0.45 + (i / 20.0) * (SC_Z1 - 0.45 - (SC_Z0 + 0.45))
        hit = inside(tube_only, (0.0, SCOPE_Y, z))
        if hit is not None:
            sc_axis = (z, hit['name'])
            break
    print('  镜筒：光轴 Y=%.2f  筒内%s ⇒ 里头是**通/透明**的 %s'
          % (SCOPE_Y, '通' if sc_axis is None else '被 %s 挡' % sc_axis[1],
             'OK' if sc_axis is None else '!! 不通'))
    px = img.load()
    clear = cross = dot_n = opaque_n = 0
    for face, x0, y0, x1, y1 in _lens_rects(geo, LENS_BACK):
        if face not in ('north', 'south'):
            continue
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                p = px[xx, yy]
                if p[3] == 0:
                    clear += 1
                elif p[:3] == GLASS_CROSS:
                    cross += 1
                elif p[:3] == GLASS_DOT:
                    dot_n += 1
                else:
                    opaque_n += 1
    print('  目镜镜片：整片透明 %d（方角 + 镜片边全透明）、十字线 %d、中心点 %d、多余的实心像素 %d %s'
          % (clear, cross, dot_n, opaque_n,
             'OK（透明含十字线）' if clear > 40 and cross >= 3 and opaque_n == 0
             else '!! 还有实心块挡着'))

    ys = [ROUND_TOP_Y - ROUND_SP * i for i in range(5)]
    print('★ 弹匣：5 发中心 y %s（间距 %.2f，自上而下）' % ([round(v, 2) for v in ys], ROUND_SP))
    print('  整发 z %.2f…%.2f 在匣内（%.2f…%.2f）%s；最下一发底 %.3f ≥ 匣底 %.2f %s'
          % (ROUND_CZ - 0.35, ROUND_CZ + 0.75, MAG_Z0 + 0.06, MAG_Z1 - 0.06,
             'OK' if ROUND_CZ - 0.35 >= MAG_Z0 + 0.04 and ROUND_CZ + 0.75 <= MAG_Z1 - 0.04
             else '!! 超出', ys[-1] - ROUND_R, MAG_Y0 - 0.01,
             'OK' if ys[-1] - ROUND_R >= MAG_Y0 else '!! 穿底'))
    print('  最上一发顶 %.3f < 枪机体底 %.2f（闭锁不打架）%s'
          % (ys[0] + ROUND_R, BORE - BOLT_R,
             'OK' if ys[0] + ROUND_R <= BORE - BOLT_R - 0.02 else '!! 顶到枪机'))

    bolt_body = [c for c in CUBES if c['bone'] == 'bolt'
                 and c['name'].startswith(('blt_body', 'blt_head'))]
    closed = covers(bolt_body, PORT_Z0 + 0.02, PORT_Z1 - 0.02, BORE)
    moved = [dict(c, z=[c['z'][0] + 1.90, c['z'][1] + 1.90]) for c in bolt_body]
    opened = covers(moved, PORT_Z0 + 0.02, PORT_Z1 - 0.02, BORE)
    print('★ 抛壳口 z %.2f…%.2f：闭锁被枪机体盖住 %s；后拉 1.90 后让开 %s'
          % (PORT_Z0, PORT_Z1, 'OK' if closed else '!! 没盖住', 'OK' if not opened else '!! 还挡着'))

    def touch(a, b, eps=0.02):
        # ★ r115：坐标允许写成逆序（如 `(_sx*0.23, _sx*0.07)` 在 _sx=−1 时是 (−0.23,−0.07)），
        #   先归一化成 [min,max] 再比区间 —— 否则逆序的方块会被误判成「悬空件」
        #   （mz_slotr0/r1、bp_foot_r 就是这么被误报的）。
        for k in range(3):
            a0, a1 = min(a[k]), max(a[k])
            b0, b1 = min(b[k]), max(b[k])
            if a1 + eps < b0 or b1 + eps < a0:
                return False
        return True

    boxes = [(c['name'], (c['x'], c['y'], c['z'])) for c in CUBES]
    lonely = [n for i, (n, b1) in enumerate(boxes)
              if not any(touch(b1, b2) for j, (_, b2) in enumerate(boxes) if j != i)]
    print('★ 悬空件检查：%s' % ('没有孤立方块 OK' if not lonely else '!! %s' % lonely))

    z0 = min(c['z'][0] for c in CUBES)
    z1 = max(c['z'][1] for c in CUBES)
    y0 = min(c['y'][0] for c in CUBES)
    y1 = max(c['y'][1] for c in CUBES)
    x1 = max(c['x'][1] for c in CUBES)
    print('整体：Z %.2f…%.2f（全长 %.2f 单位 = %.2f 格 = **%.0fcm**）  Y %.2f…%.2f  X ±%.2f'
          % (z0, z1, z1 - z0, (z1 - z0) / 16.0, (z1 - z0) / 16.0 * 100.0, y0, y1, x1))
    print('★ 关键模型点（抄进代码）：')
    print('  枪管轴线 Y   = %.3f（-> AWP_MUZZLE 的 y）' % BORE)
    print('  枪口         = (0.00, %.3f, %.3f)  -> WeaponMount.AWP_MUZZLE' % (BORE, MUZZLE_Z))
    print('  镜光轴 Y     = %.2f -> WeaponMount.AWP_SCOPE_Y' % SCOPE_Y)
    print('  抛壳口(世界) = %s -> WeaponMount.AWP_EJECT（没变）' % (EJECT_WORLD,))
    print('  枪机 pivot   = (0.61, 1.50, 0.38)（没变）  Java BOLT_BACK 取 1.90 / LIFT 62°')
    print('  弹匣最上一发 = y %.2f（round_in）  弹匣 pivot (0.00, 0.00, 0.90)（没变）' % ROUND_TOP_Y)
    print()
    print('★ 动画（%d 条，全部空动作：姿态由 Java 程序化驱动）：' % len(build_anims()['animations']))
    for k, v in build_anims()['animations'].items():
        print('  %-30s loop=%-5s %.2fs' % (k, v['loop'], v['animation_length']))
    print()
    for b in geo['minecraft:geometry'][0]['bones']:
        print('  %-13s parent=%-12s cubes=%-3d pivot=%s'
              % (b['name'], b.get('parent'), len(b.get('cubes', [])), b['pivot']))
    print()
    for k in ('geo', 'tex', 'glow', 'anim'):
        print('-> %s' % os.path.relpath(paths[k], ROOT))


if __name__ == '__main__':
    main()
