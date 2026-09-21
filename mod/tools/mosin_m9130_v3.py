#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""莫辛-纳甘 M91/30（v3，照用户给的蓝图重建）—— MC 1.20.1 / GeckoLib 真骨骼模型。

按用户要求重做（与 M1 加兰德 v2/v3 同一套做法）：

1. **枪管 = 圆形空洞枪管**：`tube_z()` 用 8 段斜置小盒拼出**八棱空心管**
   （前段外径 0.25 / 内孔 0.13），枪口正视就是一圈管壁 + 中间黑洞；
   孔底另有黑色八棱**膛底堵头**（透过枪管能看到一段膛）。
2. **弹仓看得见子弹**：莫辛**没有弹匣**，是**固定 5 发弹仓**（`magazine` 骨骼），
   子弹**一发一发**压进去（`round_in` = 手上那一发 / 最上一发）。
   `round_in` + `mag_r1..mag_r4` 一共 5 个位置**自上而下排**（弹簧把子弹顶在上口），
   枪机后拉（= 让开装填口）时才看得见；**拉完栓（闭锁）就被枪机体挡住** ⇒
   用户要的「弹仓可以看见子弹 / 拉完栓看不见弹仓里面子弹」。
3. **瞄准镜 = 圆型空心 + 透明玻璃 + 十字线**：`sc_tube` 是八棱空心镜筒（外 0.40 / 内 0.28），
   前后各一块**背景 alpha = 0 的镜片**（cutout 直接丢弃 ⇒ 看得穿），
   目镜那片刻上**十字分划**（+ 中心亮点），筒内偏前一块黑色挡板 ⇒ 看进去是「深色镜筒 + 十字」。
4. **枪身用方块堆出真枪的样子**：六棱机匣（含抛壳/装填口、机匣桥、铆钉、厂标钢印）、
   木托（托底 → 握颈 → 机匣两侧 → 弹仓开口）、前托 + 上护木、**两个枪箍 + 前帽 + 通条 + 背带环**、
   表尺（缺口顶 = 瞄准线）、带护罩的准星柱、扳机护圈（环形，看得见扳机）、
   下弯拉机柄 + 球形柄头、钢托底板。
5. **明显的换弹 / 栓动循环**（Java 程序化驱动，见 `MosinGeoModel`）：
   开栓 → 枪机后退把**空弹壳**带出来 → 抛向**射手右侧**翻滚飞出 →
   前推闭锁把**弹仓最上一发**顶进弹膛；换弹 = 开栓 → **一发一发**压进弹仓 → 闭栓。

★ 几何约定**不能动**（ADS 对准、弹道、手臂都靠它，见 `WeaponMount.MOSIN_*`）：
  - 前向 = −Z（枪口）、上 = +Y、原点 = 握把；**枪管轴线 `BORE = 1.75`**（与 AKM 同高）
  - 机瞄瞄准线 **`IRON_Y = 2.72`**（准星柱顶 = 表尺缺口顶，都在 X = 0）
  - 4 倍镜光轴 **`SCOPE_Y = 3.34`**（在机匣上方；比 M1 的觇孔高 0.62 —— 4 倍镜筒坐在支架上）
  - 枪口 `(0, 1.75, −17.35)`、抛壳口 `(0.62, 2.10, −1.95)`、托底 `z = 5.58`
  - 骨骼名（Java / WeaponMount 按名字取，不要改）：
    `root/move/body/barrel/handguard/bolt/magazine/round_in/trigger/scope/scope_elev/
     scope_wind/casing/camera` + 新增 `mag_r1..mag_r4`（弹仓里其余 4 发）
  - **move pivot 必须留在 (0, 1.75, 0)**（Java `MOVE_PY`）、bolt pivot `(0, 1.75, −1.85)`
    （Java `BOLT_P*`）；`casing` pivot 从 (0.62,2.10,−1.95) 挪到弹壳自己的中心（只是让抛壳
    翻滚绕自身转，`WeaponMount.MOSIN_EJECT` 那个**世界坐标**点不变）

输出（直接写进 resources，另在 build/ 留副本给 geo2bbmodel / bbpush）：
  `geo/mosin.geo.json`、`textures/models/mosin_geo.png`(+`_glowmask`)、
  `animations/mosin.animation.json`

用法::

    python tools/mosin_m9130_v3.py              # 出 geo / 贴图 / glowmask / 动画 + 自检
    python tools/_mosviews.py v3                # 离线出五个视角的图（不开游戏核对形状）
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
S = 12.0                       # 图集密度（1 单位 = S 像素）；main() 里逐档降级

# ------------------------------------------------------------------ 关键数值（Java 同步）
BORE = 1.75                 # ★ 枪管轴线（与 AKM 一致 ⇒ WeaponMount.MOSIN_T* 不变）
IRON_Y = 2.72               # ★ 机瞄瞄准线（准星柱顶 = 表尺缺口顶）
SCOPE_Y = 3.34              # ★ 4 倍镜光轴（WeaponMount.MOSIN_SCOPE_Y）—— 支架短一截（原 3.44）
MUZZLE_Z = -17.35           # 枪口端面（★ 用户：「枪管太短了稍微长一点」—— 前伸 0.57）
BUTT_Z = 5.58               # 托底板外表面
# 机匣
RCV_Z0, RCV_Z1 = -4.58, -0.62
RCV_HW = 0.38               # 机匣外半宽
RCV_IN = 0.26               # 内腔半宽（枪机体 r 0.24 在里头滑）
RCV_BOT = 1.30              # 机匣底面
RCV_TOP = 2.20              # 机匣顶面
PORT_Z0, PORT_Z1 = -3.40, -2.25   # ★ 装填/抛壳口（闭栓被枪机体挡住、后拉就让开）
# 枪机（pivot (0, 1.75, −1.85)，Java：BOLT_LIFT 90° / BOLT_BACK 1.75）
BOLT_Z0, BOLT_Z1 = -3.85, -1.10
BOLT_R = 0.24
BOLT_BACK = 1.75            # Java 同步；后拉这么多 ⇒ 枪机体完全让开装填口
BOLT_HANDLE = (0.95, -0.60)  # 柄头相对 pivot 的偏移（Java BOLT_GRIP_DX/DY）
# ★ 固定弹仓（没有弹匣！）
MAG_Z0, MAG_Z1 = -3.35, -2.05
MAG_HW = 0.36
MAG_Y0, MAG_Y1 = 0.34, 1.30    # ★ 照蓝图：弹仓只比木托腹线（0.70）低 0.36 ≈ 19mm
ROUND_CZ = -2.92            # 整发沿 z 的中心（弹体 z −3.27…−2.17）
ROUND_R = 0.095             # 弹壳半径（一发直径 0.19）
ROUND_TOP_Y = 1.26          # ★ 最上一发（round_in）中心高（顶 1.355 < 枪机体底 1.51）
ROUND_SP = 0.18             # 层间距（自上而下排：弹簧把子弹顶在上口）
# ★ 扳机护圈（照蓝图：一条**细长的弓**，从弹仓后壁一直伸到握颈下面；长 1.48 ≈ 79mm）
TG_Z0, TG_Z1 = -2.14, -0.66
# 4 倍镜
SC_Z0, SC_Z1 = -4.05, -0.65
SC_RO, SC_RI = 0.38, 0.27   # 镜筒外 / 内半径（外径收细 0.02 ⇒ 底下的支架更短）
SC_CZ = (SC_Z0 + SC_Z1) * 0.5
# 木托
FE_Z0, FE_Z1 = -15.30, -4.58   # 前托（从机匣前端一直到前帽；前帽又往回收了 0.38）
FE_HW = 0.48
WOOD_MID_Y1 = 1.30          # 机匣两侧木托的顶面（= 机匣底面，不穿模）

# ------------------------------------------------------------------ 调色板（发蓝钢 + 桦木托）
WOOD = (208, 152, 86)       # 暖琥珀色木托（照蓝图：桦木托偏蜜色）
WOOD_D = (176, 118, 62)     # 下护木 / 内侧
BLUE = (66, 70, 78)         # 发蓝钢（枪管 / 机匣 / 弹仓）
BLUE_D = (46, 50, 58)       # 更暗（枪箍 / 表尺 / 护圈 / 托板 / 镜筒）
STEEL = (150, 152, 160)     # 抛光钢（枪机体 / 拉机柄 / 通条）
BRASS = (206, 162, 82)      # 黄铜弹壳
COPPER = (196, 126, 72)     # 铜被甲弹头
BLACK = (20, 22, 26)        # 内孔 / 膛底 / 镜筒挡板
GLASS = (86, 104, 120)      # 镜片外圈（贴图里只留一圈，背景透明）
GLASS_CROSS = (28, 30, 34)  # 十字分划
GLASS_DOT = (150, 160, 170)  # 分划中心亮点


# ------------------------------------------------------------------ ★ 桦木画法（顺纹）
def _birch(img, rect, rn, base, horiz):
    """木纹**沿长边**走，且是**长条状**而不是「一行一条」（前者像原木，后者像拼板）。

    做法：
      · 跨纹方向（沿短边 j）用一条**很慢的正弦**（振幅 ±2.5%）—— 只有很宽的衣服，不会一条一条；
      · 顺纹方向（沿长边 i）叠两条不同波长的正弦（±3.5% / ±2%）—— 长条纹随长度慢慢扭；
      · 偶发的深色纹线（2%）长度拉满整面（真木纹就是这么长）。
    """
    x, y, w, h = rect
    px = img.load()
    if horiz:
        for j in range(h):
            base_f = 1.0 + 0.025 * math.sin(j * 1.7 + 0.7)
            if rn.f() < 0.02:
                base_f *= 0.90
            for i in range(w):
                f = base_f * (1.0 + 0.035 * math.sin(i * 0.21 + j * 0.9)
                              + 0.02 * math.sin(i * 0.07 + 1.3))
                c = boxlib.sh(base, f * rn.r(0.997, 1.003))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
    else:
        for i in range(w):
            base_f = 1.0 + 0.025 * math.sin(i * 1.7 + 0.7)
            if rn.f() < 0.02:
                base_f *= 0.90
            for j in range(h):
                f = base_f * (1.0 + 0.035 * math.sin(j * 0.21 + i * 0.9)
                              + 0.02 * math.sin(j * 0.07 + 1.3))
                c = boxlib.sh(base, f * rn.r(0.997, 1.003))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)


boxlib.KINDS['birch'] = _birch


# ------------------------------------------------------------------ 几何辅助
def B(bone, name, x, y, z, mat, kind='metal', tag=None, rot=None, piv=None, curv=None):
    return cube(bone, name, x, y, z, mat, kind=kind, tag=tag, rot=rot, piv=piv, curv=curv)


def tube_z(bone, prefix, z0, z1, cy, r_out, r_in, mat, kind='metal', tag=None, seg=8,
           cx=0.0, overlap=1.08):
    """★ 空心圆管（轴 = Z）：seg 段径向壁小盒围成一圈 ⇒ 正视是一圈管壁 + 中间真孔。

    `overlap` 只给 1.08（微微搭接）：写大了相邻段会互相压过去，从管口往里看内壁
    会变成一圈「风车」而不是一个整圆的孔（用户指出过：镜筒里面应该是透明的 + 十字线）。
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
    """实心八棱柱（轴 = Z，十字双盒 + 圆柱曲率明暗）：枪机体 / 膛底堵头用。"""
    a = k * r
    curv = ('cyl', 'z', (cx, cy))
    return [cube(bone, prefix + '_a', (cx - r, cx + r), (cy - a, cy + a), (z0, z1), mat,
                 kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (cx - a, cx + a), (cy - r, cy + r), (z0, z1), mat,
                 kind=kind, tag=tag, curv=curv)]


def oct_x(bone, prefix, x0, x1, cy, cz, r, mat, kind='metal', tag=None, k=0.414):
    """实心八棱盘（轴 = X）：拉机柄球头用。"""
    a = k * r
    curv = ('cyl', 'x', (cy, cz))
    return [cube(bone, prefix + '_a', (x0, x1), (cy - r, cy + r), (cz - a, cz + a), mat,
                 kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (x0, x1), (cy - a, cy + a), (cz - r, cz + r), mat,
                 kind=kind, tag=tag, curv=curv)]


def round_cubes(bone, prefix, cy, cz):
    """一发 7.62x54R（黄铜弹壳 + 铜被甲弹头，弹尖朝 −Z）。整发 z：cz−0.35 … cz+0.75。"""
    return [B(bone, prefix + '_case', (-ROUND_R, ROUND_R), (cy - ROUND_R, cy + ROUND_R),
              (cz + 0.08, cz + 0.75), BRASS, 'metal', tag='round'),
            B(bone, prefix + '_tip', (-0.060, 0.060), (cy - 0.060, cy + 0.060),
              (cz - 0.35, cz + 0.09), COPPER, 'metal', tag='round')]


# ------------------------------------------------------------------ 骨骼
BONES = [
    # name,        parent,        pivot
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', (0.0, BORE, 0.0)),              # ★ Java MOVE_PY = 1.75，不能改
    ('body', 'move', (0.0, BORE, -2.40)),            # 机匣 + 枪托 + 扳机组
    ('barrel', 'move', (0.0, BORE, -9.00)),          # ★ 空心圆管枪管 + 准星 + 表尺
    ('handguard', 'body', (0.0, 2.06, -9.40)),       # 前托 + 上护木 + 枪箍 + 通条
    ('bolt', 'body', (0.0, BORE, -1.85)),            # ★ 枪机（Java BOLT_PY / BOLT_PZ）
    ('magazine', 'body', (0.0, 1.06, -2.75)),        # ★ 固定弹仓（没有弹匣）
    ('mag_r1', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP, ROUND_CZ)),      # 自上而下 2..5 发
    ('mag_r2', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP * 2, ROUND_CZ)),
    ('mag_r3', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP * 3, ROUND_CZ)),
    ('mag_r4', 'magazine', (0.0, ROUND_TOP_Y - ROUND_SP * 4, ROUND_CZ)),
    ('round_in', 'body', (0.0, 0.86, -2.80)),        # ★ 手上那一发 / 弹仓最上一发
    ('trigger', 'body', (0.0, 1.28, -1.36)),         # 扳机（销轴在机匣底、柄根正下方）
    ('scope', 'body', (0.0, SCOPE_Y, -2.60)),        # ★ 空心镜筒 + 透明镜片 + 十字线
    ('scope_elev', 'scope', (0.0, 3.80, -2.40)),     # 高低鼓
    ('scope_wind', 'scope', (0.42, SCOPE_Y, -2.40)),  # 风偏鼓
    ('casing', 'body', (0.13, BORE, -2.48)),         # ★ r115：右侧抛壳窗内（贴右内壁，绕自身翻滚）
    ('camera', 'body', (0.0, BORE, -2.40)),
]

CUBES = []


# ------------------------------------------------------------------ 机匣（body）
def build_receiver():
    """六棱机匣：两侧平面 + 上下四条棱线；**空心**（内腔 |x| ≤ RCV_IN）且顶部留装填口。"""
    c = []
    c.append(B('body', 'rcv_l', (-RCV_HW, -RCV_IN), (RCV_BOT, RCV_TOP), (RCV_Z0, RCV_Z1),
               BLUE, tag='stamp'))
    # ★ r115（用户：「抛壳位置为右侧，不是左侧」）：右壁在抛壳窗位置**留洞** ——
    #   真实栓动步枪的抛壳窗就在机匣右侧，弹壳从这儿出去（与 AWP 同一改法）。
    c.append(B('body', 'rcv_r_f', (RCV_IN, RCV_HW), (RCV_BOT, RCV_TOP), (RCV_Z0, PORT_Z0),
               BLUE))
    c.append(B('body', 'rcv_r_b', (RCV_IN, RCV_HW), (RCV_BOT, RCV_TOP), (PORT_Z1, RCV_Z1),
               BLUE))
    # 顶盖：装填口前 / 后两段（口子 z PORT_Z0…PORT_Z1）
    c.append(B('body', 'rcv_top_f', (-RCV_HW, RCV_HW), (RCV_TOP - 0.14, RCV_TOP),
               (RCV_Z0, PORT_Z0), BLUE))
    c.append(B('body', 'rcv_top_b', (-RCV_HW, RCV_HW), (RCV_TOP - 0.14, RCV_TOP),
               (PORT_Z1, RCV_Z1), BLUE))
    # 底壁：弹仓开口前 / 后两段
    c.append(B('body', 'rcv_bot_f', (-RCV_HW, RCV_HW), (RCV_BOT, RCV_BOT + 0.18),
               (RCV_Z0, MAG_Z0), BLUE))
    c.append(B('body', 'rcv_bot_b', (-RCV_HW, RCV_HW), (RCV_BOT, RCV_BOT + 0.18),
               (MAG_Z1, RCV_Z1), BLUE))
    # 六棱的上下四条棱线（比两侧壁略凸 0.02，给一点「六棱机匣」的体积感）
    for sx, nm in ((-1.0, 'l'), (1.0, 'r')):
        c.append(B('body', 'rcv_bev_u' + nm, (sx * RCV_HW, sx * (RCV_HW + 0.02)),
                   (RCV_TOP - 0.16, RCV_TOP), (RCV_Z0, RCV_Z1), BLUE_D))
        c.append(B('body', 'rcv_bev_d' + nm, (sx * RCV_HW, sx * (RCV_HW + 0.02)),
                   (RCV_BOT, RCV_BOT + 0.16), (RCV_Z0, RCV_Z1), BLUE_D))
    # 机匣前后环 + 后座凸榫（插进木托里）
    c.append(B('body', 'rcv_ring_f', (-RCV_HW - 0.02, RCV_HW + 0.02),
               (RCV_BOT - 0.04, RCV_TOP + 0.02), (-4.56, -4.36), BLUE))
    c.append(B('body', 'rcv_ring_b', (-RCV_HW - 0.02, RCV_HW + 0.02),
               (RCV_BOT - 0.04, RCV_TOP + 0.02), (-0.88, -0.60), BLUE))
    c.append(B('body', 'rcv_tang', (-0.16, 0.16), (1.34, 1.58), (RCV_Z1, 0.34), BLUE))
    # 机匣左侧两颗螺钉（照蓝图）
    c += boxlib.bolt('body', 'rcv_scr1', -RCV_HW - 0.01, 1.68, -3.95, 0.07, 0.05, STEEL,
                     axis='x', kind='metal')
    c += boxlib.bolt('body', 'rcv_scr2', -RCV_HW - 0.01, 1.68, -1.35, 0.07, 0.05, STEEL,
                     axis='x', kind='metal')
    return c


# ------------------------------------------------------------------ 木托 / 护圈（body）
def _lerp(a, b, t):
    return a + (b - a) * t


def build_stock():
    """木托：托底（最高、最厚）→ 握颈，**剖面按线性插值拆成 8 段**（台阶小到 1px，
    看着就是一条连续的托背线）；**托背线在握颈处降到枪机之下（1.46）**，
    否则枪机后拉时会插进木头里。
    """
    c = []
    n = 8
    z_butt, z_wrist = 5.30, 0.30
    for i in range(n):
        t0, t1 = i / float(n), (i + 1) / float(n)
        z1 = _lerp(z_butt, z_wrist, t0)
        z0 = _lerp(z_butt, z_wrist, t1)
        hw = _lerp(0.50, 0.44, (t0 + t1) / 2)
        top = max(_lerp(2.05, 1.46, t0), _lerp(2.05, 1.46, t1))
        bot = min(_lerp(-0.30, 0.55, t0), _lerp(-0.30, 0.55, t1))
        c.append(B('body', 'st_%d' % i, (-hw, hw), (bot, top), (z0, z1), WOOD, 'birch'))
    c.append(B('body', 'st_w2', (-0.44, 0.44), (0.55, 1.46), (0.30, 1.52), WOOD, 'birch'))
    # ★ 握颈前那段托腹：照蓝图应该是一条**斜线**下来（原来是平的 0.70 然后一步降到 0.44，
    #   侧面看像缺了一块）⇒ 拆成 3 小阶：0.70 → 0.60 → 0.50，接上 st_0 的 0.44
    for _i, (_z0, _z1, _bot) in enumerate(((-0.70, -0.28, 0.70), (-0.28, 0.04, 0.60),
                                           (0.04, 0.32, 0.50))):
        c.append(B('body', 'st_tang%d' % _i, (-0.42, 0.42), (_bot, 1.46), (_z0, _z1), WOOD,
                   'birch'))
    # 机匣下方：弹仓前后两段 + 弹仓两侧的窄木条（弹仓比木托开口窄 0.02 ⇒ 不穿模）
    c.append(B('body', 'st_mid_f', (-0.44, 0.44), (0.70, WOOD_MID_Y1), (-2.10, -0.68), WOOD,
               'birch'))
    c.append(B('body', 'st_mid_c', (-0.44, 0.44), (0.70, WOOD_MID_Y1), (RCV_Z0, -3.35), WOOD,
               'birch'))
    c.append(B('body', 'st_mag_l', (-0.44, -MAG_HW - 0.02), (0.70, WOOD_MID_Y1),
               (-3.35, -2.10), WOOD, 'birch'))
    c.append(B('body', 'st_mag_r', (MAG_HW + 0.02, 0.44), (0.70, WOOD_MID_Y1),
               (-3.35, -2.10), WOOD, 'birch'))
    # 托底板（钢）+ 螺丝 + 托底背带槽；(st_plt_*) 两块把托底上下角倒圆（照蓝图）
    c.append(B('body', 'st_plate', (-0.52, 0.52), (-0.32, 2.08), (5.30, BUTT_Z), BLUE_D))
    c.append(B('body', 'st_heel', (-0.48, 0.48), (1.88, 2.06), (4.30, 5.32), WOOD, 'birch'))
    c.append(B('body', 'st_toe', (-0.48, 0.48), (-0.32, -0.12), (4.60, 5.32), WOOD, 'birch'))
    c += boxlib.bolt('body', 'st_plate_scr1', 0.0, 1.80, 5.44, 0.06, 0.06, STEEL, axis='z',
                     kind='metal')
    c += boxlib.bolt('body', 'st_plate_scr2', 0.0, 0.10, 5.44, 0.06, 0.06, STEEL, axis='z',
                     kind='metal')
    c.append(B('body', 'st_sling', (-0.10, 0.10), (0.05, 0.38), (3.92, 4.32), BLUE_D))
    return c


def build_trigger():
    """扳机护圈（照蓝图：**一条细长的弓**，不是个小方框）+ 弹仓卡笋。

    ★ 用户（对着多视图蓝图）：「这个位置不对，与参考图对比差太远了」⇒
      真枪 M91/30 的护圈弓有 ~79mm 长（1.48 单位）：
        · 弓的前立柱顶进**弹仓后壁**（z −2.14…−2.04，y 0.30…0.72）
        · 弓的后立柱顶进**握颈木托底**（z −0.76…−0.66，y 0.30…0.74）
        · 底梁很薄（y 0.30…0.42 ≈ 6px），只比弹仓底（0.34）低一点点 ⇒
          侧面看：弹仓→护圈→握颈 是**连续的一条**，不再是「弹仓下挂个小方框」
      ★ 挂在前护圈下面那两片（原来的弹仓卡笋 + 前背带环）全部撤掉：
        卡笋改到弓口里面（坐在底梁上、贴着前立柱），背带环本来前托上就有一个。
    """
    c = []
    c.append(B('body', 'tg_f', (-0.09, 0.09), (0.30, 0.72), (TG_Z0, TG_Z0 + 0.10), BLUE_D))
    # ★ 用户标注（蓝线）：「方框那位置应该是倾斜的」⇒ 后立柱改成**斜插进握颈**的斜柱
    #   （不是一根竖柱子）：绕 X 转 26° ⇒ 柱头往后上方走 0.20，顶面 y≈0.71 正好顶进木托腹
    c.append(B('body', 'tg_b', (-0.09, 0.09), (0.30, 0.76), (TG_Z1 - 0.06, TG_Z1 + 0.04), BLUE_D,
               rot=(26.0, 0.0, 0.0), piv=(0.0, 0.30, TG_Z1 - 0.01)))
    c.append(B('body', 'tg_bot', (-0.09, 0.09), (0.30, 0.42), (TG_Z0, TG_Z1), BLUE_D))
    # ★ 用户标注（绿箭头）：「这个位置多余的」⇒ 原来挂在弓前段的那片弹仓卡笋（tg_latch）
    #   已删掉：弓口里现在只有一根扳机，看出去是透的
    return c


# ------------------------------------------------------------------ 固定弹仓（magazine）+ 5 发子弹
def build_magazine():
    """★ 莫辛**没有弹匣**：机匣下方是**固定 5 发弹仓**，木托只留一个开口。

    弹仓 = 两侧壁 + 前后壁 + 底板（前铰链 / 后卡笋），**上口敞开** ⇒ 枪机后拉时
    从装填口能看见里面的黄铜子弹；闭锁时枪机体正好盖住装填口 ⇒ 看不见。
    """
    c = []
    c.append(B('magazine', 'mg_l', (-MAG_HW, -MAG_HW + 0.07), (MAG_Y0, MAG_Y1),
               (MAG_Z0, MAG_Z1), BLUE, tag='mag'))
    c.append(B('magazine', 'mg_r', (MAG_HW - 0.07, MAG_HW), (MAG_Y0, MAG_Y1),
               (MAG_Z0, MAG_Z1), BLUE, tag='mag'))
    c.append(B('magazine', 'mg_f', (-MAG_HW, MAG_HW), (MAG_Y0, MAG_Y1), (MAG_Z0, MAG_Z0 + 0.07),
               BLUE, tag='mag'))
    c.append(B('magazine', 'mg_b', (-MAG_HW, MAG_HW), (MAG_Y0, MAG_Y1), (MAG_Z1 - 0.07, MAG_Z1),
               BLUE, tag='mag'))
    c.append(B('magazine', 'mg_floor', (-MAG_HW, MAG_HW), (MAG_Y0, MAG_Y0 + 0.09),
               (MAG_Z0, MAG_Z1), BLUE_D, tag='mag'))
    c.append(B('magazine', 'mg_hinge', (-0.12, 0.12), (MAG_Y0 - 0.06, MAG_Y0 + 0.10),
               (MAG_Z0 - 0.06, MAG_Z0 + 0.06), BLUE_D))
    c.append(B('magazine', 'mg_catch', (-0.12, 0.12), (MAG_Y0 - 0.02, MAG_Y0 + 0.14),
               (MAG_Z1 - 0.10, MAG_Z1 + 0.04), BLUE_D))
    # 弹仓底部倒圆（照蓝图：仓底是个圆润的凸起，不是尖角方盒）
    c.append(B('magazine', 'mg_roundf', (-MAG_HW + 0.06, MAG_HW - 0.06), (MAG_Y0 - 0.04, MAG_Y0 + 0.08),
               (MAG_Z0 - 0.04, MAG_Z0 + 0.06), BLUE_D))
    c.append(B('magazine', 'mg_roundb', (-MAG_HW + 0.06, MAG_HW - 0.06), (MAG_Y0 - 0.04, MAG_Y0 + 0.08),
               (MAG_Z1 - 0.06, MAG_Z1 + 0.04), BLUE_D))
    return c


def build_rounds():
    """★ 弹仓里那 5 发：`round_in` = 最上一发（装填时从机匣上方压进来的就是它），
    `mag_r1..mag_r4` = 下面 4 发。**自上而下排**（弹簧把子弹顶在上口，真枪如此）。"""
    c = []
    c += round_cubes('round_in', 'ri', ROUND_TOP_Y, ROUND_CZ)
    for i in range(4):
        c += round_cubes('mag_r%d' % (i + 1), 'm%d' % (i + 1),
                         ROUND_TOP_Y - ROUND_SP * (i + 1), ROUND_CZ)
    return c


# ------------------------------------------------------------------ 枪机（bolt）
def build_bolt():
    """★ 枪机：机体（八棱柱，闭锁时正好盖住装填口）+ 机头 + 待击体 + **下弯拉机柄 + 球头**。

    Java 侧：`bolt.setRotZ(lift * 90°)`（抬柄）+ `setPosZ(back * BOLT_BACK)`（后退）。
    柄头位置 (0.95, −0.60) 相对 pivot 与 Java 的 `BOLT_GRIP_DX/DY` 一致 ⇒ 右手抓得准。
    """
    c = []
    c += oct_z('bolt', 'blt_body', BOLT_Z0, BOLT_Z1, BORE, BOLT_R, STEEL, kind='brushed')
    c += oct_z('bolt', 'blt_head', BOLT_Z0 - 0.16, BOLT_Z0, BORE, BOLT_R - 0.03, STEEL,
               kind='brushed')
    c.append(B('bolt', 'blt_cock', (-0.14, 0.14), (BORE + 0.06, BORE + 0.30),
               (BOLT_Z1, BOLT_Z1 + 0.22), STEEL, 'brushed'))
    # ★ 拉机柄必须**连续的一根**：横段 → 拐角 → 下弯段 → 球头，相邻块都要接触
    #   （用户指出过「柄头与柄身是分开的」：下弯段就是补上那一段）
    c.append(B('bolt', 'blt_h1', (BOLT_R - 0.02, 0.62), (BORE - 0.22, BORE - 0.02),
               (-1.46, -1.18), STEEL, 'brushed'))
    c.append(B('bolt', 'blt_h2', (0.60, 0.86), (BORE - 0.34, BORE - 0.06),
               (-1.44, -1.20), STEEL, 'brushed'))
    c.append(B('bolt', 'blt_h3', (0.68, 0.88), (BORE + BOLT_HANDLE[1] + 0.09, BORE - 0.15),
               (-1.42, -1.22), STEEL, 'brushed'))
    c += oct_x('bolt', 'blt_knob', 0.80, 1.02, BORE + BOLT_HANDLE[1], -1.32, 0.15, STEEL,
               kind='brushed')
    return c


# ------------------------------------------------------------------ 枪管 / 表尺 / 准星（barrel）
def build_barrel():
    """★ 空心圆管枪管（八棱壁）+ 膛底黑堵头 + 表尺（缺口顶 = 瞄准线）+ 带护罩的准星柱。"""
    c = []
    c += tube_z('barrel', 'bl_t1', -9.60, -4.62, BORE, 0.30, 0.13, BLUE)
    c += tube_z('barrel', 'bl_t2', -13.40, -9.60, BORE, 0.275, 0.13, BLUE)
    # ★ 用户：「枪管连贯不要有分叉」⇒ 内孔半径全部取 0.13（原来前段 0.125、枪口帽
    #   0.12，从枪口看进去是两个台阶）；枪口帽内孔不再比枪管小
    c += tube_z('barrel', 'bl_t3', MUZZLE_Z, -13.40, BORE, 0.25, 0.13, BLUE)
    # ★ 膛底堵头：从枪口看进去是「管壁 + 黑洞」，深处封住（不然会一眼看穿整根枪管）
    c += oct_z('barrel', 'bl_bore', -4.95, -4.80, BORE, 0.235, BLACK, kind='flat')
    # 枪口帽（前段加厚一圈，照蓝图）
    c += tube_z('barrel', 'bl_muz', MUZZLE_Z, MUZZLE_Z + 0.22, BORE, 0.29, 0.13, BLUE)
    # ---------------- 表尺（缺口顶 = IRON_Y）：底座 + 表尺板 + 两耳 + 游标
    c.append(B('barrel', 'rs_base', (-0.24, 0.24), (BORE + 0.22, 2.22), (-6.10, -4.72),
               BLUE_D))
    c.append(B('barrel', 'rs_leaf', (-0.20, 0.20), (2.22, 2.46), (-5.98, -4.86), BLUE_D))
    c.append(B('barrel', 'rs_ear_l', (-0.20, -0.09), (2.46, IRON_Y), (-4.96, -4.74), BLUE_D))
    c.append(B('barrel', 'rs_ear_r', (0.09, 0.20), (2.46, IRON_Y), (-4.96, -4.74), BLUE_D))
    c.append(B('barrel', 'rs_slide', (-0.06, 0.06), (2.46, 2.60), (-5.60, -5.44), STEEL))
    # ---------------- 准星：底座 + 柱（柱顶 = IRON_Y）+ 护罩两侧板 + 顶梁
    #   ★ z 全部相对枪口写，改枪管长度（MUZZLE_Z）时准星自动跟着走
    c.append(B('barrel', 'fs_base', (-0.20, 0.20), (BORE + 0.18, 2.34),
               (MUZZLE_Z + 0.08, MUZZLE_Z + 0.48), BLUE_D))
    c.append(B('barrel', 'fs_post', (-0.055, 0.055), (2.34, IRON_Y),
               (MUZZLE_Z + 0.22, MUZZLE_Z + 0.36), BLUE_D))
    c.append(B('barrel', 'fs_hood_l', (-0.20, -0.14), (2.20, 2.86),
               (MUZZLE_Z + 0.10, MUZZLE_Z + 0.46), BLUE_D))
    c.append(B('barrel', 'fs_hood_r', (0.14, 0.20), (2.20, 2.86),
               (MUZZLE_Z + 0.10, MUZZLE_Z + 0.46), BLUE_D))
    c.append(B('barrel', 'fs_hood_t', (-0.20, 0.20), (2.80, 2.90),
               (MUZZLE_Z + 0.10, MUZZLE_Z + 0.46), BLUE_D))
    # 刺刀座（91/30 前帽下面那圈）—— 顶面伸进枪口帽/枪管里，别悬空；
    #   ★ 做**小一号**（原来往下伸 0.62，侧面看像从枪管里叉出一根）
    c.append(B('barrel', 'bay_lug', (-0.13, 0.13), (BORE - 0.50, BORE - 0.18),
               (MUZZLE_Z + 0.14, MUZZLE_Z + 0.34), BLUE_D))
    return c


# ------------------------------------------------------------------ 前托 / 上护木 / 枪箍 / 通条（handguard）
def build_handguard():
    """前托（包住枪管下半圈、中间留通条槽、**前细后粗**）+ 上护木 + 两个枪箍 + 前帽 + 通条。"""
    c = []
    #  段：z 区间 / 半宽 / 底面 y / 顶面 y（往枪口方向逐步收窄收浅 ⇒ 前细后粗的锥度）
    #  ★ 照蓝图：前托比枪管只粗一圈（底面 1.18，深约 0.85），不是一大块厚木
    bands = ((-9.20, FE_Z1, 0.48, 1.18, 2.06),
             (-12.60, -9.20, 0.44, 1.22, 2.02),
             (FE_Z0, -12.60, 0.40, 1.26, 1.98))
    for n, (z0, z1, hw, y0, y1) in enumerate(bands):
        # ★ 用户：「枪管连贯不要有分叉」⇒ 前托底面做成**一整块**：
        #   原来中间留了 ±0.10 的通条槽，俯视/仰视看木托被一条黑缝劈成两半，很像分叉
        c.append(B('handguard', 'fe_bot%d' % n, (-hw, hw), (y0, 1.46), (z0, z1), WOOD_D,
                   'birch'))
        c.append(B('handguard', 'fe_s%dl' % n, (-hw, -0.32), (1.46, y1), (z0, z1), WOOD,
                   'birch'))
        c.append(B('handguard', 'fe_s%dr' % n, (0.32, hw), (1.46, y1), (z0, z1), WOOD,
                   'birch'))
        # ★ 上护木跟同一段前托的**顶面齐平**（底面 = y1）⇒ 护木与前托之间不再有
        #   那条透出枪管的黑缝（也是「分叉」的来源）；宽度统一 ±0.34
        c.append(B('handguard', 'hg_top%d' % n, (-0.34, 0.34), (y1, y1 + 0.32), (z0, z1),
                   WOOD, 'birch'))
        # 枪箍：**整圈包住前托 + 上护木**（侧板顶到护木顶面，上下箍条把整圈封上）
        for nm2, zz0, zz1 in (('b', -7.92, -7.74), ('f', -13.50, -13.32)):
            if not (zz0 >= z0 - 1e-9 and zz1 <= z1 + 1e-9):
                continue
            hw2 = hw + 0.02
            c.append(B('handguard', 'band_%s_l' % nm2, (-hw2, -0.32), (1.16, y1 + 0.42),
                       (zz0, zz1), BLUE_D))
            c.append(B('handguard', 'band_%s_r' % nm2, (0.32, hw2), (1.16, y1 + 0.42),
                       (zz0, zz1), BLUE_D))
            c.append(B('handguard', 'band_%s_b' % nm2, (-hw2, hw2), (1.16, 1.26), (zz0, zz1),
                       BLUE_D))
            c.append(B('handguard', 'band_%s_t' % nm2, (-hw2, hw2), (y1 + 0.32, y1 + 0.42),
                       (zz0, zz1), BLUE_D))
    # 前帽（枪口前那圈钢帽）—— ★ 同样必须**空心**（只做两侧 + 上下箍条）
    c.append(B('handguard', 'cap_l', (-0.44, -0.30), (1.18, 2.10), (-15.38, -15.00), BLUE_D))
    c.append(B('handguard', 'cap_r', (0.30, 0.44), (1.18, 2.10), (-15.38, -15.00), BLUE_D))
    c.append(B('handguard', 'cap_b', (-0.44, 0.44), (1.18, 1.28), (-15.38, -15.00), BLUE_D))
    c.append(B('handguard', 'cap_t', (-0.44, 0.44), (1.96, 2.06), (-15.38, -15.00), BLUE_D))
    # 前背带槽（后箍后面）+ 背带环
    c.append(B('handguard', 'sling_slot', (-0.10, 0.10), (1.20, 1.38), (-7.66, -7.50),
               BLUE_D))
    c.append(B('handguard', 'sling_sw', (-0.09, 0.09), (0.86, 1.24), (-7.62, -7.52), BLUE_D))
    return c


# ------------------------------------------------------------------ 4 倍镜（空心镜筒 + 镜片 + 十字线）
def build_scope():
    """★ 圆型空心镜筒（八棱壁）+ 前后透明镜片 + 目镜十字分划 + 底座 + 高低/风偏鼓。

    镜筒内偏前一块黑色挡板 ⇒ 从目镜看进去是「深色筒壁 + 十字线」，不会看穿整个世界。
    """
    c = []
    # ★ 用户：「倍镜也一样（不要分叉）」⇒ 筒内壁**一根直筒到底**：原来物镜/目镜/变倍环
    #   的内半径都比筒壁小 0.01~0.02，从目镜看进去是三道台阶（像被堵了几道）；
    #   现在三段内半径统一 = SC_RI，而且**在 z 上首尾相接、不重叠**（重叠会 z-fighting）
    c += tube_z('scope', 'sc_tube1', SC_Z0 + 0.32, SC_CZ - 0.10, SCOPE_Y, SC_RO, SC_RI,
                BLUE_D, tag='optic')
    c += tube_z('scope', 'sc_tube2', SC_CZ + 0.10, SC_Z1 - 0.32, SCOPE_Y, SC_RO, SC_RI,
                BLUE_D, tag='optic')
    c += tube_z('scope', 'sc_obj', SC_Z0, SC_Z0 + 0.32, SCOPE_Y, SC_RO + 0.05, SC_RI,
                BLUE_D, tag='optic')
    c += tube_z('scope', 'sc_eye', SC_Z1 - 0.32, SC_Z1, SCOPE_Y, SC_RO + 0.03, SC_RI,
                BLUE_D, tag='optic')
    c += tube_z('scope', 'sc_var', SC_CZ - 0.10, SC_CZ + 0.10, SCOPE_Y, SC_RO + 0.03,
                SC_RI, BLUE_D, tag='optic')
    # ★ 镜片：物镜（前）+ 目镜（后，带十字线）—— 贴图里按**圆形**画（方角全透明）
    #   块子比内孔略大 0.02，让圆盘正好填满镜筒内孔（四角被筒壁挡住）
    lz = SC_RI + 0.02
    c.append(B('scope', 'sc_lens_f', (-lz, lz), (SCOPE_Y - lz, SCOPE_Y + lz),
               (SC_Z0 + 0.28, SC_Z0 + 0.33), GLASS, 'flat'))
    c.append(B('scope', 'sc_lens_b', (-lz, lz), (SCOPE_Y - lz, SCOPE_Y + lz),
               (SC_Z1 - 0.33, SC_Z1 - 0.28), GLASS, 'flat'))
    # ★ 筒内**不放挡板**：用户要求「里面应该是透明的带十字线」⇒
    #   从目镜看进去要看得到东西（挡板会把筒子封成黑的） ;
    # ★ 用户：「不留间隙，使用顶点连接」⇒ 支架做成**与机匣同宽、端面与机匣面对齐**：
    #   x ±0.38 与机匣侧壁外表面共面、底面 = 机匣顶面 2.20、前/后端面 = 装填口后缘/
    #   机匣后端面 ⇒ 侧面看支架和机匣是一整块，不再有凹槽
    c.append(B('scope', 'sc_mnt', (-RCV_HW, RCV_HW), (RCV_TOP + 0.02, SCOPE_Y - SC_RO + 0.06),
               (PORT_Z1, RCV_Z1), BLUE_D))
    # ★ r117（用户截图：「**倍镜有明显间隙修复它**」）：原来**只有装填口之后**有支架，
    #   镜筒在机匣前半那一大段下面是空的（那里只有一条矮导轨，顶到 2.34，离镜筒底 2.96
    #   还差 0.62）⇒ 玩家那个斜下视角能看到一条穿过枪身的缝。
    #   现在把装填口**之前**那段也托到镜筒底（与机匣同宽、与后段支架同高）。
    #   装填口（PORT_Z0…PORT_Z1）上方仍然开敞 —— 压弹那一发要从那儿垂直落进弹仓，不能堵。
    c.append(B('scope', 'sc_mnt_f', (-RCV_HW, RCV_HW), (RCV_TOP + 0.02, SCOPE_Y - SC_RO + 0.06),
               (SC_Z0 + 0.05, PORT_Z0), BLUE_D))
    # 高低鼓（镜筒顶）/ 风偏鼓（镜筒右侧）—— 各自独立骨骼，Java 或动画可以单独动
    c.append(B('scope_elev', 'el_drum', (-0.17, 0.17),
               (SCOPE_Y + SC_RO - 0.04, SCOPE_Y + SC_RO + 0.34), (-2.57, -2.23), BLUE_D,
               'brushed'))
    c.append(B('scope_wind', 'wd_drum', (SC_RO - 0.02, SC_RO + 0.34),
               (SCOPE_Y - 0.17, SCOPE_Y + 0.17), (-2.57, -2.23), BLUE_D, 'brushed'))
    return c


# ------------------------------------------------------------------ 扳机 / 空弹壳
def build_small():
    c = []
    # ★ 扳机：正姡姡在**枪机柄根（z −1.46…−1.18）正下方**（真枪就这么装的），
    #   上面一截插在木托里（销轴在机匣底 1.30），下面一截露出木托底
    #   （0.70 → 0.44，露 0.26 ≈ 14mm）⇒ 侧面能看见护圈弓口里的扳机片
    c.append(B('trigger', 'trg_blade', (-0.07, 0.07), (0.44, WOOD_MID_Y1 + 0.04), (-1.42, -1.30),
               STEEL, 'brushed'))
    # ★ r115（用户：「抛壳位置为右侧，不是左侧」）：空弹壳贴在**右侧抛壳窗**里 ——
    #   以前在膛内中线（x=0），斜看就是「从枪身中间/偏左冒出来」。
    #   拉栓时被枪机带出来、往 +X 抛（Java 的 CASE_* 管轨迹）。
    c.append(B('casing', 'cas_body', (0.00, 0.26), (BORE - 0.13, BORE + 0.13),
               (-2.80, -2.15), BRASS, 'metal', tag='round'))
    return c


# ------------------------------------------------------------------ 图元细节
def d_stamp(img, rect, face, seed):
    """机匣左侧的厂标钢印（年份 + 型号），照蓝图那块平整的机匣侧面。"""
    if face != 'east':
        return
    x, y, w, h = rect
    if w < 22 or h < 12:
        return
    d = ImageDraw.Draw(img)
    col = (34, 36, 40)
    boxlib.text(d, x + 3, y + 2, '1943', col, 4, y + 2, y + 8)
    boxlib.text(d, x + 3, y + 9, 'M91/30', col, 3, y + 9, y + 14)


def d_mag(img, rect, face, seed):
    """弹仓侧壁：一道加强筋 + 边缘压暗（真枪弹仓是冲压件）。"""
    x, y, w, h = rect
    if w < 6 or h < 6:
        return
    px = img.load()
    for i in range(w):
        for j in range(h):
            c = px[x + i, y + j]
            f = 0.80 if (j == h // 2 or i == 0 or i == w - 1) else 1.0
            px[x + i, y + j] = (int(c[0] * f), int(c[1] * f), int(c[2] * f), c[3])


def d_round(img, rect, face, seed):
    """黄铜子弹：底部抽壳沟（暗）+ 弹肩亮线 + 弹尖压暗。"""
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


DETAILS = {'stamp': d_stamp, 'mag': d_mag, 'round': d_round}


# ------------------------------------------------------------------ ★ 镜片：圆玻璃 + 十字线
_LZ = SC_RI + 0.02
LENS_FRONT = ((-_LZ, _LZ), (SCOPE_Y - _LZ, SCOPE_Y + _LZ), (SC_Z0 + 0.28, SC_Z0 + 0.33))
LENS_BACK = ((-_LZ, _LZ), (SCOPE_Y - _LZ, SCOPE_Y + _LZ), (SC_Z1 - 0.33, SC_Z1 - 0.28))


def _lens_rects(geo, box):
    """按 origin/size 找出镜片那块的六个面 UV 矩形（bedrock geo **没有方块名**）。"""
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


def paint_lens(geo, img, box, cross):
    """把镜片上下的贴图矩形**重绘成「圆玻璃」（+ 可选的十字分划）**。

    boxlib 的 paint() 每个像素都写 alpha=255，所以镜片只能在 build() **之后**按 UV 矩形重绘：
      · **方角全部 alpha = 0**（cutout 直接丢弃）⇒ 看到的是一块**圆形**玻璃，而不是方块；
      · 只画一圈镜片边（像素圆的外圈）+（目镜）1px 深色十字分划 + 中心亮点。
    ★ 忘了「只处理镜片那一块」的判断 ⇒ 整张图集被擦成全透明（M1 踩过一次）。
    """
    px = img.load()
    for face, x0, y0, x1, y1 in _lens_rects(geo, box):
        if x1 - x0 < 2 or y1 - y0 < 2:
            continue
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                px[xx, yy] = (0, 0, 0, 0)
        if face not in ('north', 'south'):
            continue
        _paint_disc(px, x0, y0, x1, y1, cross)


def _paint_disc(px, x0, y0, x1, y1, cross):
    """★ 镜片**整片透明**，只画十字分划（用户：「应该为透明含十字线」）。

    原来还画了一圈镜片边（GLASS 色）—— 从目镜往里看就是一圈灰环，被当成「玻璃挡住了」。
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
    for yy in range(y0, y1 + 1):           # 竖线（2px 粗：镜片只有 7~8px，1px 在游戏里看不见）
        for xx in (mxi, mxi + 1):
            if inside(xx, yy) and px[xx, yy][3] == 0:
                px[xx, yy] = GLASS_CROSS + (255,)
    for xx in range(x0, x1 + 1):           # 横线
        for yy in (myi, myi + 1):
            if inside(xx, yy) and px[xx, yy][3] == 0:
                px[xx, yy] = GLASS_CROSS + (255,)
    for dx in (0, 1):                      # 中心亮点 2x2
        for dy in (0, 1):
            if inside(mxi + dx, myi + dy):
                px[mxi + dx, myi + dy] = GLASS_DOT + (255,)


# ------------------------------------------------------------------ 动画（全部空动作）
def build_anims():
    """六个状态，**只挂一条恒为 0 的 root 通道**。

    ★ 枪的姿态（举枪 / 后坐 / 枪机 / 抛壳 / 压弹）全部由 Java 程序化驱动
    （见 `MosinGeoModel`），动画里**一个关键帧都不写** —— 不会再踩
    「动画关键帧盖掉 setCustomAnimations 里写的值」那个老坑。
    """
    zero = {'0.0': [0.0, 0.0, 0.0], '1.0': [0.0, 0.0, 0.0]}
    out = {}
    for state, length, loop in (('idle', 2.0, True), ('run', 1.0, True),
                                ('run_fast', 0.8, True), ('fire', 0.5, False),
                                ('bolt', 0.9, False), ('reload', 3.0, False)):
        out['animation.mosin.' + state] = {
            'loop': loop, 'animation_length': length,
            'bones': {'root': {'rotation': zero}}}
    return {'format_version': '1.8.0', 'animations': out}


# ------------------------------------------------------------------ 自检辅助
def inside(cubes, p, eps=0.0):
    """点是否落在某个方块内部（用于「空心 / 挡住 / 不穿模」的数值自检）。"""
    x, y, z = p
    for c in cubes:
        x0, x1 = c['x']
        y0, y1 = c['y']
        z0, z1 = c['z']
        if (x0 - eps <= x <= x1 + eps and y0 - eps <= y <= y1 + eps
                and z0 - eps <= z <= z1 + eps):
            return c
    return None


def covers(cubes, z0, z1, y, r):
    """给定 z 区间里是否**每个 z 都被挡住**（用于「闭栓盖住装填口」）。"""
    n = 24
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        if not inside(cubes, (0.0, y, z)):
            return False
    return True


# ------------------------------------------------------------------ 输出 + 自检
def main():
    global S
    geo = img = None
    for dens in (13.0, 12.0, 11.0, 10.0, 9.0, 8.0):
        S = dens
        CUBES.clear()
        CUBES.extend(build_receiver())
        CUBES.extend(build_stock())
        CUBES.extend(build_trigger())
        CUBES.extend(build_handguard())
        CUBES.extend(build_barrel())
        CUBES.extend(build_bolt())
        CUBES.extend(build_magazine())
        CUBES.extend(build_rounds())
        CUBES.extend(build_scope())
        CUBES.extend(build_small())
        try:
            geo, img = boxlib.build(BONES, CUBES, 'geometry.mosin', size=SIZE,
                                    details=DETAILS, density=dens)
            break
        except RuntimeError as e:
            print('density %.0f 图集放不下（%s），降一档重试' % (dens, e))

    if geo is None:
        raise SystemExit('图集怎么都放不下')

    paint_lens(geo, img, LENS_BACK, True)          # 目镜：透明玻璃 + 十字线
    paint_lens(geo, img, LENS_FRONT, False)        # 物镜：透明玻璃

    os.makedirs(BUILD, exist_ok=True)
    paths = {
        'geo': os.path.join(RES, 'geo', 'mosin.geo.json'),
        'tex': os.path.join(RES, 'textures', 'models', 'mosin_geo.png'),
        'glow': os.path.join(RES, 'textures', 'models', 'mosin_geo_glowmask.png'),
        'anim': os.path.join(RES, 'animations', 'mosin.animation.json'),
    }
    for p in paths.values():
        os.makedirs(os.path.dirname(p), exist_ok=True)

    boxlib.write(geo, img, paths['geo'], paths['tex'])
    with io.open(paths['anim'], 'w', encoding='utf-8', newline='\n') as f:
        json.dump(build_anims(), f, ensure_ascii=False, indent=1)
        f.write('\n')
    gen_glowmask.make(paths['tex'], paths['glow'])

    # build/ 留一份副本给 geo2bbmodel / bbpush（那套脚本吃的是相对路径）
    with io.open(os.path.join(BUILD, 'mosin.geo.json'), 'w', encoding='utf-8',
                 newline='\n') as f:
        json.dump(geo, f, ensure_ascii=False, indent=1)
        f.write('\n')
    img.save(os.path.join(BUILD, 'mosin_geo.png'))

    # ---------------------------------------------------------------- 自检
    tab = {}
    for c in CUBES:
        tab.setdefault(c['name'], c)
    have = set(b[0] for b in BONES)
    need = {'root', 'move', 'body', 'barrel', 'handguard', 'bolt', 'magazine', 'round_in',
            'mag_r1', 'mag_r2', 'mag_r3', 'mag_r4', 'trigger', 'scope', 'scope_elev',
            'scope_wind', 'casing', 'camera'}
    print('骨骼名检查: %s' % ('OK' if need <= have else '缺 %s' % (need - have)))
    print('bones %d  cubes %d（面 %d）  density %.0f  %dx%d'
          % (len(BONES), len(CUBES), 6 * len(CUBES), S, SIZE, SIZE))

    # ---- 自检 1：★ 枪管是空心圆管（轴线上没有方块）+ 膛底有黑堵头
    axis_hit = None
    for i in range(41):
        z = MUZZLE_Z + 0.15 + (i / 40.0) * (-5.10 - (MUZZLE_Z + 0.15))
        hit = inside(CUBES, (0.0, BORE, z))
        if hit is not None:
            axis_hit = (z, hit['name'])
            break
    tube = [c for c in CUBES if c['name'].startswith('bl_t')]
    plug = tab['bl_bore_b']
    print('★ 枪管：%d 段八棱壁（外径 %.2f→%.2f / 内孔 0.26 单位 ≈ %.1fmm）'
          % (len(tube), 0.25, 0.30, 0.26 * 1103 / 20.9))
    print('  枪口到膛底整条轴线：%s；膛底黑堵头 z %.2f…%.2f、直径 %.2f %s'
          % ('是空的 OK' if axis_hit is None else '!! 被 %s 挡住' % axis_hit[1],
             plug['z'][0], plug['z'][1], plug['y'][1] - plug['y'][0],
             'OK' if abs(plug['y'][1] - (BORE + 0.235)) < 1e-9 else '??'))

    # ---- 自检 2：瞄准线（准星柱顶 = 表尺耳顶 = IRON_Y）+ 镜筒光轴 + 镜片贴图
    fs, ear = tab['fs_post'], tab['rs_ear_l']
    print('★ 瞄准线：准星柱顶 %.2f  表尺耳顶 %.2f（IRON_Y %.2f）%s'
          % (fs['y'][1], ear['y'][1], IRON_Y,
             'OK' if abs(fs['y'][1] - IRON_Y) < 1e-9 and abs(ear['y'][1] - IRON_Y) < 1e-9
             else '!! 与 IRON_Y 不一致'))
    sc_axis = None
    for i in range(21):
        z = SC_Z0 + 0.40 + (i / 20.0) * (SC_Z1 - 0.40 - (SC_Z0 + 0.40))
        hit = inside(CUBES, (0.0, SCOPE_Y, z))
        if hit is not None:
            sc_axis = (z, hit['name'])
            break
    print('  镜筒：%d+%d+%d 段八棱壁  光轴 Y=%.2f  筒内%s ⇒ 里头是**通/透明**的 %s'
          % (len([c for c in CUBES if c['name'].startswith('sc_tube')]),
             len([c for c in CUBES if c['name'].startswith('sc_obj')]),
             len([c for c in CUBES if c['name'].startswith('sc_eye')]), SCOPE_Y,
             '通' if sc_axis is None else '被 %s 挡' % sc_axis[1],
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
    print('  目镜镜片：整片透明 %d 个（方角 + 镜片边全透明）、十字线 %d 个、中心点 %d 个、'
          '多余的实心像素 %d 个 %s'
          % (clear, cross, dot_n, opaque_n,
             'OK（透明含十字线）' if clear > 40 and cross >= 3 and opaque_n == 0
             else '!! 还有实心块挡着'))

    # ---- 自检 3：★ 弹仓 5 发（自上而下）都在仓里、最上一发在枪机体下方
    ys = [ROUND_TOP_Y - ROUND_SP * i for i in range(5)]
    print('★ 固定弹仓：5 发中心 y %s（间距 %.2f，自上而下）'
          % ([round(v, 2) for v in ys], ROUND_SP))
    print('  整发 z %.2f…%.2f 在弹仓内（%.2f…%.2f）%s；最下一发底 %.3f ≥ 仓底 %.2f %s'
          % (ROUND_CZ - 0.35, ROUND_CZ + 0.75, MAG_Z0 + 0.07, MAG_Z1 - 0.07,
             'OK' if ROUND_CZ - 0.35 >= MAG_Z0 + 0.05 and ROUND_CZ + 0.75 <= MAG_Z1 - 0.05
             else '!! 超出', ys[-1] - ROUND_R, MAG_Y0 + 0.09,
             'OK' if ys[-1] - ROUND_R >= MAG_Y0 + 0.06 else '!! 穿底'))
    print('  最上一发顶 %.3f < 枪机体底 %.2f（闭锁不打架）%s；弹仓壁半宽 %.2f ⊂ 木托开口 %.2f %s'
          % (ys[0] + ROUND_R, BORE - BOLT_R,
             'OK' if ys[0] + ROUND_R <= BORE - BOLT_R - 0.02 else '!! 顶到枪机',
             MAG_HW, tab['st_mag_r']['x'][0],
             'OK' if tab['st_mag_r']['x'][0] >= MAG_HW else '!! 木托压进弹仓'))

    # ---- 自检 4：★ 闭栓时枪机体盖住装填口；后拉 BOLT_BACK 后让开
    body_bolt = [c for c in CUBES if c['bone'] == 'bolt'
                 and c['name'].startswith(('blt_body', 'blt_head'))]
    closed = covers(body_bolt, PORT_Z0 + 0.02, PORT_Z1 - 0.02, BORE, BOLT_R)
    moved = [dict(c, z=[c['z'][0] + BOLT_BACK, c['z'][1] + BOLT_BACK]) for c in body_bolt]
    opened = covers(moved, PORT_Z0 + 0.02, PORT_Z1 - 0.02, BORE, BOLT_R)
    # ---- 自检 3b：★ 扳机组（照蓝图：细长的护圈弓 + 露在木托下面的扳机）
    bow_l = TG_Z1 - TG_Z0
    bow_top = tab['tg_bot']['y'][1]
    trg = tab['trg_blade']
    wood_bot = tab['st_mid_f']['y'][0]
    exposed = wood_bot - trg['y'][0]
    print('★ 扳机组：护圈弓 z %.2f…%.2f（长 %.2f 单位 ≈ %.0fmm，真枪 ~79mm）%s'
          % (TG_Z0, TG_Z1, bow_l, bow_l * 53.7,
             'OK' if 1.20 <= bow_l <= 1.75 else '!! 太短/太长'))
    print('  弓口 %.2f…%.2f（%.2f ≈ %.0fmm）里看得见扳机：露出木托底 %.2f 单位 ≈ %.0fmm %s'
          % (bow_top, wood_bot, wood_bot - bow_top, (wood_bot - bow_top) * 53.7,
             exposed, exposed * 53.7,
             'OK' if 0.18 <= exposed <= 0.40 and trg['y'][0] > bow_top else '!! 扳机没露出来'))
    print('  弓前柱顶 y %.2f ⊂ 弹仓后壁、后柱（斜 26°）顶 y %.2f ≥ 木托底 %.2f ⇒ 两端都插进件里（不悬空）'
          % (tab['tg_f']['y'][1], tab['tg_b']['y'][1], wood_bot))

    print('★ 装填口 z %.2f…%.2f：闭栓时被枪机体盖住 %s；后拉 %.2f 后让开 %s'
          % (PORT_Z0, PORT_Z1, 'OK' if closed else '!! 没盖住', BOLT_BACK,
             'OK' if not opened else '!! 还挡着'))
    print('  后拉后枪机体尾端 z=%.2f；握颈顶面 %.2f、枪机体底 %.2f ⇒ %s'
          % (BOLT_Z1 + BOLT_BACK, tab['st_w2']['y'][1], BORE - BOLT_R,
             '不穿木托 OK' if BORE - BOLT_R >= tab['st_w2']['y'][1] - 1e-9 else '!! 插进木托'))
    knob_top = BORE + BOLT_HANDLE[0] + 0.15     # 绕 pivot 转 +90°：(x,y) → (−y, x)
    print('  拉机柄抬 90° 后柄头顶 y≈%.2f < 镜筒底 %.2f %s'
          % (knob_top, SCOPE_Y - SC_RO, 'OK' if knob_top < SCOPE_Y - SC_RO else '!! 撞镜子'))

    # ---- 自检 4b：★ 不许有「悬空件」（与任何方块都不接触）—— 用户指出过柄头是分开的
    def touch(a, b, eps=0.02):
        for k in range(3):
            if a[k][1] + eps < b[k][0] or b[k][1] + eps < a[k][0]:
                return False
        return True

    boxes = [(c['name'], (c['x'], c['y'], c['z'])) for c in CUBES]
    lonely = []
    for i, (n1, b1) in enumerate(boxes):
        if not any(touch(b1, b2) for j, (_, b2) in enumerate(boxes) if j != i):
            lonely.append(n1)
    print('★ 悬空件检查：%s' % ('没有孤立方块 OK' if not lonely else '!! %s' % lonely))

    # ---- 自检 5：整体尺寸 + 关键模型点（抄进 WeaponMount / GeoModel）
    z0 = min(c['z'][0] for c in CUBES)
    z1 = max(c['z'][1] for c in CUBES)
    y0 = min(c['y'][0] for c in CUBES)
    y1 = max(c['y'][1] for c in CUBES)
    x1 = max(c['x'][1] for c in CUBES)
    print('整体：Z %.2f…%.2f（全长 %.2f 单位 = %.2f 格 ≈ %.0fmm，比例照着真枪 1232mm）  '
          'Y %.2f…%.2f  X ±%.2f'
          % (z0, z1, z1 - z0, (z1 - z0) / 16.0, (z1 - z0) * 1232 / 22.93, y0, y1, x1))
    print('★ 关键模型点（抄进代码）：')
    print('  枪管轴线 Y   = %.2f（与 AKM 同高）' % BORE)
    print('  枪口         = (0.00, %.2f, %.2f)   -> WeaponMount.MOSIN_MUZZLE' % (BORE, MUZZLE_Z))
    print('  裸露钢管长   = %.2f 单位（前托前帽 %.2f → 枪口 %.2f）'
          % (-15.38 - MUZZLE_Z, -15.38, MUZZLE_Z))
    print('  机瞄瞄准线 Y = %.2f -> WeaponMount.MOSIN_IRON_Y' % IRON_Y)
    print('  4 倍镜光轴 Y = %.2f -> WeaponMount.MOSIN_SCOPE_Y（支架高 %.2f）'
          % (SCOPE_Y, SCOPE_Y - SC_RO - RCV_TOP))
    print('  抛壳口       = (0.62, 2.10, -1.95)  -> WeaponMount.MOSIN_EJECT（不变）')
    print('  枪机 pivot   = (0.00, %.2f, -1.85)  BOLT_BACK = %.2f' % (BORE, BOLT_BACK))
    print('  弹仓最上一发 = y %.2f（round_in，装填时抬到 2.55 = 机匣上方）' % ROUND_TOP_Y)
    print()
    print('★ 动画（%d 条，全部空动作：姿态由 Java 程序化驱动）：' % len(build_anims()['animations']))
    for k, v in build_anims()['animations'].items():
        print('  %-30s loop=%-5s %.2fs' % (k, v['loop'], v['animation_length']))
    print()
    for b in geo['minecraft:geometry'][0]['bones']:
        print('  %-12s parent=%-12s cubes=%-3d pivot=%s'
              % (b['name'], b.get('parent'), len(b.get('cubes', [])), b['pivot']))
    print()
    for k in ('geo', 'tex', 'glow', 'anim'):
        print('-> %s' % os.path.relpath(paths[k], ROOT))
    print('   接着：python tools/geo2bbmodel.py mosin && python tools/bbpush.py '
          'build/mosin.geo.json build/mosin_geo.png hexalunar_mosin_m9130')


if __name__ == '__main__':
    main()
