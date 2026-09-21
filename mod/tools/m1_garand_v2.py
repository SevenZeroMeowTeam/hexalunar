#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""M1 加兰德（M1 Garand，半自动、8 发漏夹）—— 方块体素版 GeckoLib 真骨骼模型 v2。

照用户给的照片逐件重建，并落实这几条硬要求：

1. **枪管 = 圆形空洞枪管**：`tube_z()` 用 8 段斜置小盒拼出**八棱空心管**
   （外半径 0.25 / 内孔 0.13），枪口正视就是一圈管壁 + 中间一个黑洞
   （孔底另有 `bore` 黑色八棱堵头，透过枪管能看到 4 个单位深的膛线孔）。
2. **漏夹看得见子弹**：`clip_in`（钢制漏夹壳）+ `clip_rounds`（**8 发黄铜子弹**，一层一发）。
   装填时整只漏夹被抬到机匣上方 ⇒ 看得见 8 发弹；压进去、弹夹盖合上后
   **`clip_rounds` 由 Java 隐藏** ⇒ 合起来看不见里面。
   ★ 加兰德是**漏夹供弹，机匣下方没有外露弹匣**（用户要求「弹匣不要露出来」）：
   `magazine` 骨骼留着但**不放方块**，漏夹整套压在机匣内部（底 1.88 ≥ 弹仓井底 1.55，
   顶 2.574 ≤ 枪机底 2.58），机匣底下什么都没有。
   ★ 也**没有拉栓 / 拉机柄**（用户要求）：枪机是导气杆推的，右侧只有一根贴管的细导气杆。
3. **瞄准镜（照门）= 圆形空心 + 透明玻璃 + 十字线**：`rs_ring` 是八棱空心环（觇孔），
   孔里嵌 `rs_glass` —— 这块方块的贴图**背景全透明**（alpha=0，cutout 直接丢弃），
   只画一圈淡蓝镜片边 + **深色十字分划** ⇒ 圆型空心、内部透明玻璃与十字线。
4. **弹夹盖（`cover`）**：机匣顶部那块盖板，**靠整体平行抬起打开（不转任何角度）** ——
   用户要求「漏匣上盖是平行的」「打开时也保持平行」。合上时与机匣顶 3.00 齐平、
   盖住漏夹口 ⇒ 看不见里面的子弹；每打一发枪机循环时先抬起再落下（**抛壳也走这条口子**），
   **打空不合上**（空仓挂机，盖板停在高位），装填完成自动落回合上。
5. 枪身其余部分用方块构建（与其它武器一致的 boxlib 图元）。

★ 几何约定**不能动**（ADS 对准、弹道、动画都靠它）：
  - 前向 = −Z（枪口）、上 = +Y、**原点 = 握把**；**枪管轴线 `BORE = 2.30`**（与 r108 相同，
    所以 `WeaponMount.M1_TX/TY/TZ` 一个字都不用改）
  - 机瞄瞄准线 **`IRON_Y = 3.44`**：照门觇孔圆心 = 准星片顶，都在 X = 0
    （r108 是 3.10，这轮把觇孔做成真圆环后抬到 3.44 —— 与 AKM/AWP/Kar98k/莫辛同一高度）
  - 枪口 `(0, 2.30, −13.60)`、抛壳口 `(0.33, 2.88, −1.05)`（要抄进 WeaponMount）
  - 骨骼名（Java / 动画 JSON 按名字取，不要改）：
    `root/move/body/handguard/barrel/cover/bolt/clip_in/clip_rounds/magazine/trigger/casing`

输出（直接写进 resources，另在 build/ 留副本给 geo2bbmodel / bbpush）：
  `geo/m1_garand.geo.json`、`textures/models/m1_garand_geo.png`(+`_glowmask`)、
  `animations/m1_garand.animation.json`
"""
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import boxlib                                             # noqa: E402
import gen_glowmask                                       # noqa: E402
from boxlib import cube                                   # noqa: E402

RES = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
BUILD = os.path.join(ROOT, 'build')

SIZE = 512
S = 12.0                    # 每模型单位分配的贴图像素数

# ------------------------------------------------------------------ 关键数值（Java 同步）
BORE = 2.30                 # ★ 枪管轴线（与 r108 相同 ⇒ WeaponMount.M1_T* 不变）
IRON_Y = 3.44               # ★ 觇孔圆心 = 准星片顶（瞄准线）
MUZZLE_Z = -13.60           # 枪口
BT_Z0, BT_Z1 = -13.60, -9.48        # 圆管枪管
BT_RO, BT_RI = 0.21, 0.11           # 管外半径 / 内孔半径（空心）
AP_RO, AP_RI = 0.48, 0.31           # 觇孔环外/内半径（内孔 0.62 单位 ≈ 3.4cm）
AP_Z0, AP_Z1 = -0.58, -0.26         # 觇孔环的前后位置
# ★ r111c（用户：「枪身可以细一点，目前看起来有点粗」）：机匣 / 枪托 / 护木 / 枪管一起收窄约 23%，
#   轴线与瞄准线一点没动（BORE 2.30 / IRON_Y 3.44）⇒ WeaponMount 的对准数学不用改。
RCV_HW = 0.46                       # 机匣外半宽（原 0.60）
RCV_OPEN_HW = 0.20                  # 顶部漏夹口半宽（原 0.24）
STOCK_HW = 0.54                     # 枪托半宽（原 0.66）
GLASS_Z0, GLASS_Z1 = -0.45, -0.39   # 镜片（0.06 厚）
RS_TOP = 3.00                       # 机匣顶面 / 盖板顶面（★ 齐平：盖板不再凸出一块）
# ★★ r111d（用户：「漏匣上盖是平行的」「打开时也保持平行」+ 照视频照片的样式）：
#   盖板不再绕后缘翻转 55°，改成**整体平行抬起** LIFT 个单位（永远与机匣顶平行）。
#   为了让平行抬起不撞到照门座，机匣顶部**分了前后两段**：
#     · 前段 z −1.98…−0.78 = 可抬起的盖板（cover，漏夹就从这儿压进去）
#     · 后段 z −0.78…1.10 = **实体顶桥**（body，不动的金属，照门座坐在它上面）
#   这正是真枪的样子：弹夹口只在照门座**前面**，座子后面是实心机匣桥。
#   ⇒ 抬起时盖板只在照门座前方升起，不会碰到座子/觇孔环。
COVER_Z0, COVER_Z1 = -1.98, -0.78  # ★ 盖板覆盖的 z 区间（照门座在它后面）
BRIDGE_Z0, BRIDGE_Z1 = -0.78, 1.10  # ★ 实体顶桥（补上机匣顶部开口的后半段）
COVER_PIV = (0.0, 2.94, COVER_Z1)   # 盖板骨骼 pivot（平移用不到，只作定位）
COVER_LIFT = 0.40                   # ★ 打开时平行抬起的高度（Java 同步；模型像素）
#   ⇒ 打开后盖板底 3.28 与机匣顶 3.00 之间留出 0.28 的缝，正好够 0.20 粗的空壳抛出去
#     （用户「抛壳也如此」：抛壳走的就是这条被盖板让出来的口子，盖板全程保持平行）
CLIP_DROP = 1.75                    # 漏夹抬升量（Java 同步）（抬到 3.62…4.32 ⇒ 整只漏夹在机匣顶之上）
BOLT_BACK = 2.40                    # 枪机后座量（Java 同步）
CLIP_IY = 1.81                      # clip_in 骨骼 pivot（r108 的历史值，Java 里没用到）
# ★ 漏夹整套必须在**机匣内部**：机匣底 1.55…1.95（弹仓井底），膛内空间 1.95…3.00，
#   而枪机本体占 2.58…2.98 ⇒ 漏夹连子弹只能压在 1.95…2.58 这 0.63 里。
#   （r111 第一版把 CLIP_BOT 写成 1.00，漏夹下半截从机匣底下伸出来了 —— 用户看到就是「弹匣露出来」）
CLIP_FLOOR0, CLIP_FLOOR1 = 1.88, 1.97     # 漏夹底板
CLIP_WALL0, CLIP_WALL1 = 1.95, 2.18       # 漏夹两侧壁（只包住下半截，上面看得见弹）
# ★ 漏夹的 z 区间必须落在**盖板开口**（z −1.98…−0.78）内：不然抬高时会穿过实体桥
CLIP_Z0, CLIP_Z1 = -1.85, -0.95
ROUND_BOT = 1.97                          # 最下一发子弹的底面
ROUND_H = 0.0755                          # 单发高度（8 发 = 0.604 ⇒ 顶部 2.574，刚好压在枪机底面之下）

# ★ 以下 4 个数是**弹夹盖/抛壳的时序**，Java 里同名同值（M1GarandGeoModel）—— 自检 5b 用它们
#   复算空壳的飞行轨迹，确认**抛壳这一路也不会穿过盖板**（用户「抛壳也如此」）。
#   ★ 盖板先抬起、空壳后出现：抬起 0.22 后壳的顶面（2.96）才不会被盖板底（3.10）刮到。
COVER_OPEN_AT = 0.26        # 枪机后退到这个比例时盖板完全抬起，之后开始回落
CASE_T0, CASE_T1 = 0.14, 0.72     # 空壳在枪机循环里可见的窗口
CASE_VX, CASE_VY, CASE_G = 3.00, 1.80, 0.80   # 抛出初速：向右 +X / 向上 / 重力
CASE_BACK = 1.50            # 先被枪机抽出来的距离（+Z 向后）

# ------------------------------------------------------------------ 调色板（照照片：胡桃木 + 发蓝/磷化钢）
WOOD = (132, 84, 44)        # 胡桃木托 / 护木
WOOD_D = (110, 68, 34)      # 木件暗部
STEEL = (104, 106, 110)     # 机匣（发蓝钢）
PARK = (74, 76, 80)         # 磷化（漏夹 / 导气杆 / 枪口件）
PARK_D = (56, 58, 62)       # 更深的磷化件
BOLT = (140, 142, 146)      # 枪机（精加工钢，亮的）
BLACK = (34, 35, 38)        # 觇孔环 / 枪机耳
BRASS = (188, 150, 66)      # 子弹 / 弹壳
DARK = (14, 14, 16)         # 膛孔
GLASS = (74, 96, 112)       # 镜片外圈（贴图里只画一圈边，背景透明）
GLASS_CROSS = (30, 32, 36)  # 十字分划
GLASS_DOT = (150, 160, 170)  # 分划中心亮点


# ------------------------------------------------------------------ ★ 胡桃木画法（顺纹）
def _walnut(img, rect, rn, base, horiz):
    """木纹**沿长边**走（不用 boxlib 的 `_wood`：它按 UV 的行画横纹，
    长条面上一渲就是一截截「拼板」，枪身看着像一堆木板钉起来的）。

    horiz（w ≥ h）时长边是 U ⇒ 一行一条纹理；否则一列一条纹理。
    """
    x, y, w, h = rect
    px = img.load()
    if horiz:
        for j in range(h):
            f = rn.r(0.93, 1.07)
            if rn.f() < 0.13:
                f *= 0.85                                  # 深色纹线
            elif rn.f() < 0.08:
                f *= 1.11                                  # 亮色纹线
            tone = rn.r(0.99, 1.01)                        # 纹理内部还有细变化
            for i in range(w):
                fx = f * (1.0 + 0.02 * math.sin(i * 0.35 + j))
                c = boxlib.sh(base, fx * tone * rn.r(0.995, 1.005))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
    else:
        for i in range(w):
            f = rn.r(0.93, 1.07)
            if rn.f() < 0.13:
                f *= 0.85
            elif rn.f() < 0.08:
                f *= 1.11
            tone = rn.r(0.99, 1.01)
            for j in range(h):
                fy = f * (1.0 + 0.02 * math.sin(j * 0.35 + i))
                c = boxlib.sh(base, fy * tone * rn.r(0.995, 1.005))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)


boxlib.KINDS['walnut'] = _walnut


# ------------------------------------------------------------------ 几何辅助
def B(bone, name, x, y, z, mat, kind='metal', tag=None, rot=None, piv=None, curv=None):
    return cube(bone, name, x, y, z, mat, kind=kind, tag=tag, rot=rot, piv=piv, curv=curv)


def tube_z(bone, prefix, z0, z1, cy, r_out, r_in, mat, kind='metal', tag=None, seg=8,
           cx=0.0, overlap=1.35):
    """★ 空心圆管（轴 = Z）：`seg` 段「径向壁」小盒围成一圈。

    每段盒子中心放在中径 `(r_out+r_in)/2` 上，绕 Z 转该段的角度
    ⇒ 局部 X 变径向（厚 = r_out−r_in）、局部 Y 变切向（宽 = 弦长 × overlap，相邻段搭接）。
    `seg = 8` 就是八棱管；正视（沿 Z 看）看到的是「一圈管壁 + 中间空的洞」。
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
    """实心八棱柱（轴 = Z，用十字双盒）：导气筒这类不需要打孔的圆柱。"""
    a = k * r
    curv = ('cyl', 'z', (cx, cy))
    return [cube(bone, prefix + '_a', (cx - r, cx + r), (cy - a, cy + a), (z0, z1), mat,
                 kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (cx - a, cx + a), (cy - r, cy + r), (z0, z1), mat,
                 kind=kind, tag=tag, curv=curv)]


def oct_x(bone, prefix, x0, x1, cy, cz, r, mat, kind='metal', tag=None, k=0.414):
    """实心八棱盘（轴 = X）：照门的高低调节旋钮（真枪左侧那个圆盘）。"""
    a = k * r
    curv = ('cyl', 'x', (cy, cz))
    return [cube(bone, prefix + '_a', (x0, x1), (cy - r, cy + r), (cz - a, cz + a), mat,
                 kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (x0, x1), (cy - a, cy + a), (cz - r, cz + r), mat,
                 kind=kind, tag=tag, curv=curv)]


# ------------------------------------------------------------------ 骨骼
BONES = [
    # name,        parent,        pivot
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', (0.0, 1.30, 1.60)),          # 握把：举枪/后坐/摆动都作用在这
    ('body', 'move', (0.0, 1.80, 0.60)),          # 机匣 + 枪托 + 扳机组 + 照门
    ('handguard', 'body', (0.0, 2.20, -9.54)),    # 上下木护木 + 枪箍
    ('barrel', 'body', (0.0, BORE, -9.54)),       # ★ 空心圆管枪管 + 准星
    ('cover', 'body', COVER_PIV),                 # ★ 弹夹盖（平行抬起，不旋转）
    ('bolt', 'body', (0.0, 2.80, -1.60)),         # 枪机（气动，藏在机匣里；无拉机柄/导气杆）
    ('clip_in', 'body', (0.0, CLIP_IY, -0.90)),   # ★ 8 发漏夹壳
    ('clip_rounds', 'clip_in', (0.0, 1.56, -0.90)),  # ★ 漏夹里的 8 发子弹
    ('magazine', 'body', (0.0, 1.54, -0.30)),     # 弹仓底板（漏夹供弹，不可拆）
    ('trigger', 'body', (0.0, 1.58, 1.32)),       # 扳机（绕顶部销轴）
    ('casing', 'body', (0.20, 2.84, -1.40)),      # ★ r115：右侧抛壳口（右壁缺口 z −1.75…−0.45）
]

CUBES = []


# ------------------------------------------------------------------ 机匣 / 枪托 / 照门（body）
def build_body():
    c = []
    # ---- ★ 枪托：**与握把是一整块木头**（M1 没有独立握把 —— 托颈就是握把），
    #      剖面照真枪：细托颈（≈1.25 单位高）→ 逐渐加高到托底（≈2.2 单位）
    c.append(B('body', 'st_wrist', (-0.50, 0.50), (1.30, 2.70), (2.10, 3.70), WOOD, 'walnut'))
    c.append(B('body', 'st_s1', (-STOCK_HW, STOCK_HW), (0.95, 2.75), (3.70, 5.30), WOOD,
               'walnut'))
    c.append(B('body', 'st_s2', (-STOCK_HW, STOCK_HW), (0.60, 2.78), (5.30, 7.10), WOOD,
               'walnut'))
    c.append(B('body', 'st_bp', (-0.56, 0.56), (0.58, 2.80), (7.08, 7.30), PARK_D))
    c.append(B('body', 'st_swivel', (-0.09, 0.09), (0.30, 0.62), (5.60, 5.90), PARK_D))
    c.append(B('body', 'st_butt_scr', (-0.26, -0.14), (0.66, 0.80), (7.24, 7.36), PARK))
    # ---- 机匣：**空心**（顶部漏夹口 + 右侧抛壳口）
    c.append(B('body', 'rcv_floor', (-RCV_HW, RCV_HW), (1.55, 1.95), (-3.10, 2.10), STEEL))
    c.append(B('body', 'rcv_wall_l', (-RCV_HW, -RCV_OPEN_HW), (1.95, 3.00), (-3.10, 2.10),
               STEEL))
    c.append(B('body', 'rcv_wall_r', (RCV_OPEN_HW, RCV_HW), (1.95, 2.78), (-3.10, 2.10),
               STEEL, tag='stamp'))
    c.append(B('body', 'rcv_r_up_f', (RCV_OPEN_HW, RCV_HW), (2.78, 3.00), (-3.10, -1.75),
               STEEL))
    c.append(B('body', 'rcv_r_up_b', (RCV_OPEN_HW, RCV_HW), (2.78, 3.00), (-0.45, 2.10),
               STEEL))
    c.append(B('body', 'rcv_front', (-RCV_OPEN_HW, RCV_OPEN_HW), (1.95, 3.00),
               (-3.10, -1.90), STEEL))
    c.append(B('body', 'rcv_rear', (-RCV_OPEN_HW, RCV_OPEN_HW), (1.95, 3.00), (1.10, 2.10),
               STEEL))
    # ★ 机匣后段实体顶桥（照门座坐在它上面）：把顶部开口的后半段填实
    #   —— 真枪弹夹口就在照门座前面那一段；枪机（顶 2.86）从桥底下（2.88）滑过去
    c.append(B('body', 'rcv_bridge', (-RCV_OPEN_HW, RCV_OPEN_HW), (2.88, RS_TOP),
               (BRIDGE_Z0, BRIDGE_Z1), STEEL))
    # 机匣两侧的铆钉
    c += boxlib.bolt('body', 'rcv_rv_l', -RCV_HW, 2.60, 0.40, 0.09, 0.06, STEEL, axis='x',
                     kind='metal')
    c += boxlib.bolt('body', 'rcv_rv_l2', -RCV_HW, 2.60, -2.20, 0.09, 0.06, STEEL, axis='x',
                     kind='metal')
    # ---- 照门：座 + ★ 八棱空心觇孔环 + 透明镜片（十字线）
    c.append(B('body', 'rs_base', (-0.36, 0.36), (RS_TOP, 3.30), (-0.70, 0.14), STEEL))
    c += tube_z('body', 'ap', AP_Z0, AP_Z1, IRON_Y, AP_RO, AP_RI, BLACK, seg=8)
    c.append(B('body', 'rs_glass', GLASS_BOX[0], GLASS_BOX[1], GLASS_BOX[2],
               GLASS, 'flat', tag='lens'))
    # ★ 高低调节旋钮：照视频照片做成**左侧的圆盘**（八棱盘 + 一字槽 + 中心螺丝）
    c += oct_x('body', 'rs_knob', -0.48, -0.28, 3.14, -0.42, 0.15, PARK_D, kind='brushed')
    c.append(B('body', 'rs_knob_slot', (-0.50, -0.48), (3.10, 3.18), (-0.50, -0.34), BLACK,
               'flat'))
    c += boxlib.bolt('body', 'rs_knob_scr', -0.48, 3.14, -0.42, 0.05, -0.04, BLACK,
                     axis='x', kind='flat')
    # ---- 扳机护圈（三根梁组成的环，中间能看见扳机）
    c.append(B('body', 'tg_f', (-0.10, 0.10), (0.70, 1.62), (1.90, 2.30), PARK_D))
    c.append(B('body', 'tg_b', (-0.10, 0.10), (0.70, 1.62), (0.60, 0.95), PARK_D))
    c.append(B('body', 'tg_bot', (-0.12, 0.12), (0.70, 0.90), (0.60, 2.30), PARK_D))
    return c


# ------------------------------------------------------------------ 护木（handguard）
def build_handguard():
    c = []
    c.append(B('handguard', 'hg_top', (-0.42, 0.42), (2.35, 2.85), (-9.54, -3.06), WOOD,
               'walnut'))
    c.append(B('handguard', 'hg_bot', (-0.46, 0.46), (1.55, 2.45), (-9.54, -3.06), WOOD_D,
               'walnut'))
    c.append(B('handguard', 'hg_cap', (-0.44, 0.44), (1.60, 2.90), (-9.95, -9.54), PARK_D))
    c.append(B('handguard', 'hg_band', (-0.48, 0.48), (1.50, 2.50), (-7.45, -7.05), PARK_D))
    c.append(B('handguard', 'hg_swivel', (-0.09, 0.09), (1.20, 1.52), (-7.45, -7.15), PARK_D))
    return c


# ------------------------------------------------------------------ 枪管（barrel）：圆管空心
def build_barrel():
    c = []
    # ★ 外露枪管 = 八棱空心管（内孔 0.26 直径：从枪口看进去是个黑洞）
    c += tube_z('barrel', 'bar_tube', BT_Z0, BT_Z1, BORE, BT_RO, BT_RI, PARK, seg=8)
    # 孔底堵头（八棱，纯黑）：让「洞」有深度（不做的话能一直看到机匣里）
    c += oct_z('barrel', 'bar_bore', BT_Z1 - 0.18, BT_Z1, BORE, BT_RI - 0.005, DARK,
               kind='flat')
    # 导气筒（枪管下方那根细管）+ 导气箍
    c += oct_z('barrel', 'bar_gas', -13.05, -10.55, 1.94, 0.10, PARK_D)
    c.append(B('barrel', 'bar_gblock', (-0.26, 0.26), (1.70, 2.12), (-12.86, -11.24), PARK_D))
    # 准星座 + 准星片（顶 = IRON_Y）+ 两侧护耳
    c.append(B('barrel', 'fs_base', (-0.18, 0.18), (2.52, 2.86), (-13.44, -13.06), PARK_D))
    c.append(B('barrel', 'fs_blade', (-0.06, 0.06), (2.86, IRON_Y), (-13.32, -13.16), PARK_D))
    c.append(B('barrel', 'fs_ear_l', (-0.24, -0.15), (2.86, 3.32), (-13.36, -13.10), PARK_D))
    c.append(B('barrel', 'fs_ear_r', (0.15, 0.24), (2.86, 3.32), (-13.36, -13.10), PARK_D))
    return c


# ------------------------------------------------------------------ ★ 弹夹盖（cover）
def build_cover():
    """★ 弹夹盖：**平行抬起**（不旋转）—— 用户要求「打开时也是平行的」。

    盖板只盖住漏夹口的前段（z −1.98…−0.78），后面是实体顶桥（照门座坐在桥上）
    ⇒ 抬起时不会撞到照门座/觇孔环；合上时与机匣顶 3.00 平齐，看着是一个平面。
    Java 侧：`cover.setPosY(open * COVER_LIFT)`，三个角度恒为 0。
    """
    c = []
    c.append(B('cover', 'cv_lid', (-RCV_HW, RCV_HW), (2.88, RS_TOP), (COVER_Z0, COVER_Z1),
               STEEL))
    return c


# ------------------------------------------------------------------ 枪机 / 导气杆（bolt）
def build_bolt():
    """★ r111b/c（按用户两次标注）：M1 是气动，**没有拉栓、也没有露在外面的导气杆**。

    原来右侧那根长导气杆（{@code blt_oprod}，z −13.0…−2.4）+ 后段（{@code blt_oprod_rear}）
    以及更早那个凸出的拉机柄全删了 —— 用户看到的就是「枪管边上一根多余的细杆」。
    现在侧边干净的只有木材与枪管，枪机本体留在机匣内部（盖住漏夹口 + 向后抽出弹壳）。
    ★ 顶面压到 **2.86**：要能从实体顶桥（2.92 起）下面滑过去，不能穿模。
    """
    c = []
    c.append(B('bolt', 'blt_body', (-RCV_OPEN_HW, RCV_OPEN_HW), (2.58, 2.86), (-2.60, 0.60),
               BOLT))
    c.append(B('bolt', 'blt_lug', (RCV_OPEN_HW, 0.36), (2.60, 2.84), (-1.80, -0.90), BLACK))
    return c


# ------------------------------------------------------------------ ★ 漏夹 + 8 发子弹
def build_clip():
    """★ 8 发漏夹：**整只都在机匣内部**（子弹顶 2.574 < 枪机底 2.58），
    从外面只能看到铜子弹的**上半截**（侧壁只包到 2.18）—— 用户要的「可以看见子弹」，
    同时又「弹匣不要露出来」（机匣底以下什么都没有）。
    """
    c = []
    c.append(B('clip_in', 'cl_l', (-0.18, -0.13), (CLIP_WALL0, CLIP_WALL1),
               (CLIP_Z0, CLIP_Z1), PARK))
    c.append(B('clip_in', 'cl_r', (0.13, 0.18), (CLIP_WALL0, CLIP_WALL1), (CLIP_Z0, CLIP_Z1),
               PARK))
    c.append(B('clip_in', 'cl_floor', (-0.18, 0.18), (CLIP_FLOOR0, CLIP_FLOOR1),
               (CLIP_Z0, CLIP_Z1), PARK))
    # ★ 8 发子弹（一发一层，弹尖朝前三分之二 + 弹壳三分之一）
    for i in range(8):
        y0 = ROUND_BOT + i * ROUND_H
        c.append(B('clip_rounds', 'rd_%d' % i, (-0.125, 0.125), (y0, y0 + ROUND_H),
                   (CLIP_Z0 + 0.09, CLIP_Z1 - 0.08), BRASS, 'metal', tag='round'))
    return c


# ------------------------------------------------------------------ 图元细节
def d_stamp(img, rect, face, seed):
    """机匣右侧的钢印 `U.S.` / `M1`（两行小字，占机匣后半段）。

    ★ 贴图密度只有 12 px/单位 ⇒ 3x5 点阵字在这块 62x10 的面上就是「半人高」的大字，
    所以只印两个短串、且贴在**后半段**（照照片，真枪的钢印也在机匣侧面）。
    """
    if face != 'east':
        return
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    if w < 26 or h < 10:
        return
    boxlib.text(d, x + w - 20, y + 1, 'U.S.', (40, 42, 46), 4, y + 1, y + 6)
    boxlib.text(d, x + w - 16, y + 6, 'M1', (40, 42, 46), 4, y + 6, y + 11)


def d_round(img, rect, face, seed):
    """黄铜子弹：底部一圈抽壳沟（暗）、中段一道弹肩亮线、前段弹头压暗。"""
    x, y, w, h = rect
    if w < 3 or h < 5:
        return
    px = img.load()
    for i in range(w):
        for k, f in ((0, 0.62), (1, 0.74), (h - 1, 0.82)):
            c = px[x + i, y + k]
            px[x + i, y + k] = (int(c[0] * f), int(c[1] * f), int(c[2] * f), 255)
        c = px[x + i, y + max(2, h // 3)]
        px[x + i, y + max(2, h // 3)] = (min(255, int(c[0] * 1.22)),
                                         min(255, int(c[1] * 1.22)),
                                         min(255, int(c[2] * 1.22)), 255)


DETAILS = {'stamp': d_stamp, 'round': d_round}


# ------------------------------------------------------------------ ★ 镜片：透明玻璃 + 十字线
GLASS_BOX = ((-0.29, 0.29), (3.15, 3.73), (GLASS_Z0, GLASS_Z1))


def paint_lens(geo, img):
    """把镜片（{@link #GLASS_BOX}）各面的贴图矩形**重绘成透明玻璃 + 深色十字线**。

    boxlib 的 paint() 会把每个像素写成不透明，所以镜片只能在 build() 之后按
    UV 矩形重绘：背景 alpha = 0（`entityCutout` 直接丢弃 ⇒ 看得穿），
    只留一圈淡蓝镜片边 + 1px 深色十字分划（+ 中心亮点）。

    ★ bedrock geo 里**没有方块名**，只能用 origin/size 认出镜片那一块
    （踩过一次：忘了这层判断 ⇒ 整张图集被擦成全透明，模型渲出来全黑只有蓝边）。
    """
    px = img.load()
    for bone in geo['minecraft:geometry'][0]['bones']:
        for c in bone.get('cubes', []):
            if not c.get('uv'):
                continue
            ox, oy, oz = c['origin']
            sx, sy, sz = c['size']
            if (abs(ox - GLASS_BOX[0][0]) > 1e-4 or abs(oy - GLASS_BOX[1][0]) > 1e-4
                    or abs(oz - GLASS_BOX[2][0]) > 1e-4
                    or abs(sx - (GLASS_BOX[0][1] - GLASS_BOX[0][0])) > 1e-4):
                continue
            for face in ('north', 'south', 'east', 'west', 'up', 'down'):
                u, v = c['uv'][face]['uv']
                w, h = c['uv'][face]['uv_size']
                x0, y0, x1, y1 = int(u), int(v), int(u + w) - 1, int(v + h) - 1
                if x1 - x0 < 2 or y1 - y0 < 2:
                    continue
                for yy in range(y0, y1 + 1):
                    for xx in range(x0, x1 + 1):
                        px[xx, yy] = (0, 0, 0, 0)
                if face not in ('north', 'south'):
                    continue
                # 镜片外圈：暗蓝细环（留 1px 边距）
                ring = GLASS + (255,)
                for xx in range(x0 + 1, x1):
                    px[xx, y0 + 1] = ring
                    px[xx, y1 - 1] = ring
                for yy in range(y0 + 1, y1):
                    px[x0 + 1, yy] = ring
                    px[x1 - 1, yy] = ring
                # 十字分划：穿过中心的 1px 竖线 + 横线（深色，不透明）
                mx, my = (x0 + x1) // 2, (y0 + y1) // 2
                for yy in range(y0 + 2, y1 - 1):
                    px[mx, yy] = GLASS_CROSS + (255,)
                for xx in range(x0 + 2, x1 - 1):
                    px[xx, my] = GLASS_CROSS + (255,)
                px[mx, my] = GLASS_DOT + (255,)             # 中心亮点


# ------------------------------------------------------------------ 动画（全部空动作）
def build_anims():
    """六个状态，**只挂一条恒为 0 的 root 通道**。

    ★ 枪的姿态（举枪 / 后坐 / 枪机 / 弹夹盖 / 漏夹 / 抛壳）全部由 Java 程序化驱动
    （见 `M1GarandGeoModel`），动画里**一个关键帧都不写** —— 这样就不会再踩
    「动画关键帧盖掉 setCustomAnimations 里写的值」那个老坑（AKM 的换弹下沉就是这么来的）。
    """
    zero = {'0.0': [0.0, 0.0, 0.0], '1.0': [0.0, 0.0, 0.0]}
    out = {}
    for state, length, loop in (('idle', 2.0, True), ('run', 1.0, True),
                                ('run_fast', 0.8, True), ('fire', 0.5, False),
                                ('bolt', 0.5, False), ('reload', 1.6, False)):
        out['animation.m1_garand.' + state] = {
            'loop': loop, 'animation_length': length,
            'bones': {'root': {'rotation': zero}}}
    return {'format_version': '1.8.0', 'animations': out}


# ------------------------------------------------------------------ 输出 + 自检
def main():
    global S
    geo = img = None
    for dens in (12.0, 11.0, 10.0, 9.0, 8.0):
        S = dens
        CUBES.clear()
        CUBES.extend(build_body())
        CUBES.extend(build_handguard())
        CUBES.extend(build_barrel())
        CUBES.extend(build_cover())
        CUBES.extend(build_bolt())
        CUBES.extend(build_clip())
        # ★ 弹匣：加兰德是**漏夹供弹、机匣下方没有外露弹匣**（用户要求「弹匣不要露出来」）
        #   ⇒ `magazine` 骨骼保留（Java 按名字取，有 null 保护）但**不放方块**。
        CUBES.append(B('trigger', 'trg_blade', (-0.08, 0.08), (0.90, 1.58), (1.20, 1.45),
                       STEEL))
        # ★ r115（用户：「抛壳位置为右侧，不是左侧」）：空壳挪到**右侧抛壳口**里 ——
        #   以前在膛内中线（x=0, z−2.50…−2.00），斜看就是「从枪身中间/偏左冒出来」。
        CUBES.append(B('casing', 'cas_body', (0.10, 0.30), (2.72, 2.96), (-1.65, -1.15),
                       BRASS, tag='round'))
        try:
            geo, img = boxlib.build(BONES, CUBES, 'geometry.m1_garand', size=SIZE,
                                    details=DETAILS, density=dens)
            break
        except RuntimeError as e:
            print('density %.0f 图集放不下（%s），降一档重试' % (dens, e))

    if geo is None:
        raise SystemExit('图集怎么都放不下')

    paint_lens(geo, img)

    os.makedirs(BUILD, exist_ok=True)
    paths = {
        'geo': os.path.join(RES, 'geo', 'm1_garand.geo.json'),
        'tex': os.path.join(RES, 'textures', 'models', 'm1_garand_geo.png'),
        'glow': os.path.join(RES, 'textures', 'models', 'm1_garand_geo_glowmask.png'),
        'anim': os.path.join(RES, 'animations', 'm1_garand.animation.json'),
    }
    for p in paths.values():
        os.makedirs(os.path.dirname(p), exist_ok=True)

    boxlib.write(geo, img, paths['geo'], paths['tex'])
    with io.open(paths['anim'], 'w', encoding='utf-8', newline='\n') as f:
        json.dump(build_anims(), f, ensure_ascii=False, indent=1)
        f.write('\n')
    gen_glowmask.make(paths['tex'], paths['glow'])
    # build/ 副本（geo2bbmodel / bbpush 从 build 取）
    boxlib.write(geo, img, os.path.join(BUILD, 'm1_garand.geo.json'),
                 os.path.join(BUILD, 'm1_garand.png'), quiet=True)
    with io.open(os.path.join(BUILD, 'm1_garand.animation.json'), 'w', encoding='utf-8',
                 newline='\n') as f:
        json.dump(build_anims(), f, ensure_ascii=False, indent=1)
        f.write('\n')

    nb = sum(len(b.get('cubes', [])) for b in geo['minecraft:geometry'][0]['bones'])
    print('bones %d  cubes %d（面 %d）  density %.0f'
          % (len(geo['minecraft:geometry'][0]['bones']), nb, nb * 6, S))
    for p in paths.values():
        print('wrote', os.path.relpath(p, ROOT))

    # ---------------- 自检 1：骨骼名（Java / 动画 JSON 按名字取）
    need = {'root', 'move', 'body', 'handguard', 'barrel', 'cover', 'bolt', 'clip_in',
            'clip_rounds', 'magazine', 'trigger', 'casing'}
    have = set(b[0] for b in BONES)
    print('骨骼名检查: %s' % ('OK' if need <= have else '缺 %s' % (need - have)))

    tab = {}
    for c in CUBES:
        tab.setdefault(c['name'], c)

    # ---------------- 自检 2：★ 枪管是「圆管 + 空心」
    tube = [c for c in CUBES if c['name'].startswith('bar_tube_')]
    radii = set()
    for c in tube:
        cx = (c['x'][0] + c['x'][1]) / 2.0
        cy = (c['y'][0] + c['y'][1]) / 2.0
        radii.add(round(math.hypot(cx - 0.0, cy - BORE), 3))
    inner = BORE + BT_RI
    print('★ 枪管：%d 段八棱壁  中径 %.3f（外 %.2f / 内孔 %.2f，孔 %.2f 单位 ≈ %.1fmm）'
          % (len(tube), sorted(radii)[0], BT_RO, BT_RI, BT_RI * 2, BT_RI * 2 * 2200 / 20.9))
    print('  轴线 Y = %.2f（与 r108 相同 ⇒ WeaponMount.M1_T* 不改）  管口 z = %.2f'
          % (BORE, BT_Z0))
    bore = tab['bar_bore_a']
    print('  孔底堵头 y %.2f…%.2f（要在内孔 %.2f…%.2f 之内）%s'
          % (bore['y'][0], bore['y'][1], BORE - BT_RI, BORE + BT_RI,
             'OK' if bore['y'][1] <= inner + 0.01 and bore['y'][0] >= BORE - BT_RI - 0.01
             else '!! 堵头比孔大'))

    # ---------------- 自检 3：★ 觇孔（圆环）+ 镜片（透明玻璃 + 十字线）
    ring = [c for c in CUBES if c['name'].startswith('ap_')]
    glass = tab['rs_glass']
    gcy = (glass['y'][0] + glass['y'][1]) / 2.0
    fs = tab['fs_blade']
    print('★ 觇孔：%d 段空心环  孔心 Y=%.2f  内孔半径 %.2f（孔 %.2f 单位）'
          % (len(ring), IRON_Y, AP_RI, AP_RI * 2))
    print('  镜片中心 Y=%.2f（要对上孔心 %.2f）  准星片顶 Y=%.2f（= 瞄准线）%s'
          % (gcy, IRON_Y, fs['y'][1],
             'OK' if abs(gcy - IRON_Y) < 0.01 and abs(fs['y'][1] - IRON_Y) < 0.01
             else '!! 瞄准线不共线'))
    print('  镜片尺寸 %.2f×%.2f → 贴图像素 %.0f×%.0f（十字线要看得见，≥6px）'
          % (glass['x'][1] - glass['x'][0], glass['y'][1] - glass['y'][0],
             (glass['x'][1] - glass['x'][0]) * S, (glass['y'][1] - glass['y'][0]) * S))
    print('  孔下沿 Y=%.2f  照门座顶 Y=%.2f ⇒ 孔的下沿比座顶高 %.2f（≥0 才不被挡）%s'
          % (IRON_Y - AP_RI, RS_TOP, (IRON_Y - AP_RI) - RS_TOP,
             'OK' if IRON_Y - AP_RI >= RS_TOP - 0.02 else '!! 照门座挡住孔的下半'))

    # ---------------- 自检 4：★ 漏夹 8 发子弹 / 合上看不见 / **不许露在机匣外**
    rounds = [c for c in CUBES if c['name'].startswith('rd_')]
    rtop = max(c['y'][1] for c in rounds)
    rbot = min(c['y'][0] for c in rounds)
    lid = tab['cv_lid']
    floor = tab['rcv_floor']
    bolt_body = tab['blt_body']
    print('★ 漏夹：8 发子弹 y %.2f…%.2f（一发 %.4f）  漏夹壁 y %.2f…%.2f'
          % (rbot, rtop, ROUND_H, CLIP_WALL0, CLIP_WALL1))
    print('  整只漏夹都在机匣内部：底 %.2f ≥ 弹仓井底 %.2f %s；顶 %.2f ≤ 枪机底 %.2f %s'
          % (CLIP_FLOOR0, floor['y'][0], 'OK' if CLIP_FLOOR0 >= floor['y'][0] - 1e-6 else '!! 伸到机匣底下',
             rtop, bolt_body['y'][0], 'OK' if rtop <= bolt_body['y'][0] + 1e-6 else '!! 顶到枪机'))
    # 机匣那一带（z −3.10…2.10）不许有东西垂到护圈底下 —— 就是「弹匣不要露出来」那条
    under = [c for c in CUBES if c['z'][0] < 2.10 and c['z'][1] > -3.10]
    low = min(c['y'][0] for c in under)
    low_name = [c['name'] for c in under if c['y'][0] == low][0]
    print('  机匣一带最低点 y=%.2f（%s）⇒ 护圈底 %.2f 之下没有外露弹匣 %s'
          % (low, low_name, tab['tg_bot']['y'][0],
             'OK' if low >= tab['tg_bot']['y'][0] - 1e-6 else '!! 有东西垂到护圈以下'))
    print('  合上时盖板 y %.2f…%.2f、x ±%.2f、z %.2f…%.2f ⇒ 盖住漏夹口（|x|<%.2f, z −1.90…1.10）%s'
          % (lid['y'][0], lid['y'][1], lid['x'][1], lid['z'][0], lid['z'][1], RCV_OPEN_HW,
             'OK' if lid['y'][0] >= 2.86 and lid['x'][1] >= RCV_OPEN_HW + 0.2
             and lid['z'][0] <= -1.96 and lid['z'][1] >= BRIDGE_Z0 else '!! 盖板没盖住漏夹口'))
    print('  ★ 开口由盖板（z %.2f…%.2f，可抬起）+ 实体顶桥（z %.2f…%.2f，不动）拼起来，%s'
          % (lid['z'][0], lid['z'][1], BRIDGE_Z0, BRIDGE_Z1,
             '两者齐平且无缝隙 OK' if abs(lid['z'][1] - BRIDGE_Z0) < 1e-6
             and abs(tab['rcv_bridge']['y'][1] - lid['y'][1]) < 1e-6 else '!! 盖板与桥不齐/有缝'))
    print('  抬升 %.2f 后漏夹 y=%.2f…%.2f（机匣顶 %.2f 之上 ⇒ 装填时整只看得见）'
          % (CLIP_DROP, CLIP_FLOOR0 + CLIP_DROP, rtop + CLIP_DROP, RS_TOP))

    # ---------------- 自检 5：★ 弹夹盖「平行抬起」—— 不转角度、不撞照门、抛壳口留够缝
    rs_z = (-0.70, 0.14)          # 照门座占的 z 区间（在盖板后面）
    open_y0 = lid['y'][0] + COVER_LIFT
    open_y1 = lid['y'][1] + COVER_LIFT
    print('★ 弹夹盖：平行抬起 %.2f（三轴角度恒为 0）⇒ 打开后 y %.2f…%.2f（与合上时同形，永远平行）'
          % (COVER_LIFT, open_y0, open_y1))
    print('  盖板 z %.2f…%.2f 与照门座 z %.2f…%.2f %s（抬起是纯竖直运动 ⇒ 只在座子前面升降）'
          % (lid['z'][0], lid['z'][1], rs_z[0], rs_z[1],
             '完全不重叠 OK' if lid['z'][1] <= rs_z[0] else '!! 与照门座重叠'))
    gap = open_y0 - RS_TOP
    print('  打开后盖板底 %.2f 与机匣顶 %.2f 之间留缝 %.2f（空壳直径 0.20）%s'
          % (open_y0, RS_TOP, gap, 'OK 抛得出壳' if gap > 0.20 else '!! 缝太小抛不出壳'))
    print('  漏夹 z %.2f…%.2f 落在盖板开口 z %.2f…%.2f 内 %s（抬起即可见/可压）'
          % (CLIP_Z0, CLIP_Z1, lid['z'][0], lid['z'][1],
             'OK' if CLIP_Z0 >= lid['z'][0] - 1e-6 and CLIP_Z1 <= lid['z'][1] + 1e-6
             else '!! 漏夹超出开口'))
    print('  打开后盖板顶 %.2f ≤ 觇孔环顶 %.2f %s（不会挡住瞄准线）'
          % (open_y1, IRON_Y + AP_RO, 'OK' if open_y1 <= IRON_Y + AP_RO else '!! 挡住瞄准线'))

    # ---------------- 自检 5b：★ 抛壳（Java 同一套公式）也不能穿过盖板
    #   cover 抬起量 = COVER_LIFT * smoothstep(枪机进度)（与 Java coverOpenAt 击发分支一致）
    #   空壳位置   = 抽出 CASE_BACK*out 后向右 CASE_VX*fly、向上 CASE_VY*fly − CASE_G*fly²
    cas = tab['cas_body']
    worst = None
    N = 400
    for i in range(N + 1):
        b = i / float(N)
        f = b / COVER_OPEN_AT if b < COVER_OPEN_AT else 1.0 - (b - COVER_OPEN_AT) / (1.0 - COVER_OPEN_AT)
        f = min(1.0, max(0.0, f))
        lift = COVER_LIFT * (f * f * (3.0 - 2.0 * f))
        cy0, cy1 = lid['y'][0] + lift, lid['y'][1] + lift
        if b < CASE_T0 or b > CASE_T1:
            continue
        c = (b - CASE_T0) / (CASE_T1 - CASE_T0)
        out = min(1.0, c / 0.22)
        fly = min(1.0, max(0.0, (c - 0.22) / 0.78))
        cx0, cx1 = cas['x'][0] + CASE_VX * fly, cas['x'][1] + CASE_VX * fly
        ky0 = cas['y'][0] + CASE_VY * fly - CASE_G * fly * fly
        ky1 = cas['y'][1] + CASE_VY * fly - CASE_G * fly * fly
        kz0 = cas['z'][0] + CASE_BACK * out - 0.6 * fly
        kz1 = cas['z'][1] + CASE_BACK * out - 0.6 * fly
        if (cx0 < lid['x'][1] - 1e-6 and cx1 > lid['x'][0] + 1e-6
                and ky0 < cy1 - 1e-6 and ky1 > cy0 + 1e-6
                and kz0 < lid['z'][1] - 1e-6 and kz1 > lid['z'][0] + 1e-6):
            worst = (b, ky0, ky1, cy0, cy1, kz0, kz1, cx0)
            break
    if worst is None:
        print('★ 抛壳：空壳沿**右侧（+X）**抛出（VX %.2f / VY %.2f / G %.2f / 抽 %.2f），'
              '全程躲开盖板（x ±%.2f、z %.2f…%.2f）OK'
              % (CASE_VX, CASE_VY, CASE_G, CASE_BACK, lid['x'][1], lid['z'][0], lid['z'][1]))
    else:
        print('★ 抛壳：!! 枪机进度 %.2f 时空壳 y %.2f…%.2f 撞上盖板 y %.2f…%.2f（z %.2f…%.2f / x≥%.2f）'
              % (worst[0], worst[1], worst[2], worst[3], worst[4], worst[5], worst[6], worst[7]))

    # ---------------- 自检 6：整体尺寸 + 关键模型点（抄进 WeaponMount / GeoModel）
    z0 = min(c['z'][0] for c in CUBES)
    z1 = max(c['z'][1] for c in CUBES)
    y0 = min(c['y'][0] for c in CUBES)
    y1 = max(c['y'][1] for c in CUBES)
    x1 = max(c['x'][1] for c in CUBES)
    print('整体：Z %.2f…%.2f（全长 %.2f 单位 = %.2f 格 = %.0fmm）  Y %.2f…%.2f  X ±%.2f'
          % (z0, z1, z1 - z0, (z1 - z0) / 16.0, (z1 - z0) * 1103 / 20.9, y0, y1, x1))
    print('★ 关键模型点（抄进代码）：')
    print('  枪管轴线 Y   = %.2f' % BORE)
    print('  枪口         = (0.00, %.2f, %.2f)   -> WeaponMount.M1_MUZZLE' % (BORE, MUZZLE_Z))
    print('  瞄准线 Y     = %.2f（觇孔圆心 = 准星片顶）-> WeaponMount.M1_IRON_Y' % IRON_Y)
    print('  抛壳口       = (0.33, 2.88, -1.05)       -> WeaponMount.M1_EJECT')
    print('  握把（右手） = (0.00, 1.45, 2.55)        -> M1GarandGeoModel.ARM_GRIP'
          '（托颈 = 握把，与枪托一体）')
    print('  前托（左手） = (0.00, 1.40, -6.20)        -> M1GarandGeoModel.ARM_SUPPORT')
    print('  压漏夹（右手）= (0.00, 4.06, %.2f) → 压到 1.88 -> ARM_CLIP / CLIP_DROP'
          % ((CLIP_Z0 + CLIP_Z1) * 0.5))
    print('  枪机后座量   = %.2f  弹夹盖平行抬起 = %.2f  盖板 pivot = (%.2f, %.2f, %.2f)'
          % (BOLT_BACK, COVER_LIFT, COVER_PIV[0], COVER_PIV[1], COVER_PIV[2]))
    print()
    print('★ 动画（%d 条，全部空动作：姿态由 Java 程序化驱动）：' % len(build_anims()['animations']))
    for k, v in build_anims()['animations'].items():
        print('  %-32s loop=%-5s %.2fs' % (k, v['loop'], v['animation_length']))
    print()
    for b in geo['minecraft:geometry'][0]['bones']:
        print('  %-12s parent=%-12s cubes=%-3d pivot=%s'
              % (b['name'], b.get('parent'), len(b.get('cubes', [])), b['pivot']))


if __name__ == '__main__':
    main()
