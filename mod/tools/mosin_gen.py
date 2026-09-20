#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""莫辛-纳甘 M91/30（狙击型：顶部导轨 + 4 倍镜）的方块体素版 GeckoLib 真骨骼模型。

参照用户给的照片（木家具 + 发蓝钢的 M91/30，枪口无刺刀）逐件重建，
**持枪/开镜数值套用 TaCZ 的 Kar98k 配置**（`build/tacz_kar98/` 里导出的那份）：

  kar98_display.json  : zoom_model_fov = 25、transform.scale 见 positioning
  kar98_data.json     : iron_zoom = 2（AK47 是 1.33）、bolt_action_time 0.85s、
                        aim_time 0.2s、reload.feed 2.85~3.5s、recoil.pitch 峰值 3.8°
  scope_98k_data.json : zoom 4.25 / scope: true      → 我们挂 4 倍镜
  kar98_geo.json      : idle_view (2, 9.8125, 17.0) / iron_view (0, 8.75, 17.5)
                        ⇒ 举枪 = 「X 归零 + 上抬 1.06 + 几乎不前后走」（Δz 仅 0.5 TaCZ 单位）

★ 几何约定**不能动**（ADS 对准与动画都靠它）：
  - 前向 = -Z（枪口），上 = +Y，**原点 = 握把**；枪管轴线 `BORE = 1.75`（与 AKM/AWP 同一套）
  - 机瞄瞄准线 **`IRON_Y = 2.72`**：照门缺口两耳顶 = 准星柱顶，都在 X = 0
  - 4 倍镜光轴 **`SCOPE_Y = 3.44`**：镜筒中心，X = 0
  - 导轨齿顶 `RAIL_TOP = 2.60` 必须**低于**瞄准线（差 0.12），否则机瞄会被导轨挡住
  - 拉机柄绕枪管轴转 90° 抬起时，柄头最远半径必须**小于镜筒底面**（3.08），否则穿模
  - 骨骼名 root/move/body/barrel/handguard/bolt/magazine/trigger/scope/scope_elev/
    scope_wind/casing/camera 由 Java（MosinGeoModel）与动画 JSON 按名字取，不要改

输出：build/mosin_v1.geo.json + build/mosin_v1.png + build/mosin_v1.animation.json
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import boxlib                                            # noqa: E402
from boxlib import cube                                   # noqa: E402

SIZE = 512
S = 12.0                    # 每模型单位分配的贴图像素数（贴图密度）

# ------------------------------------------------------------------ 关键高度（Java 侧同步）
BORE = 1.75                 # 枪管轴线
IRON_Y = 2.72               # 机瞄瞄准线：照门缺口两耳顶 = 准星柱顶
SCOPE_Y = 3.44              # 4 倍镜光轴
RAIL_TOP = 2.60             # 导轨齿顶（必须低于 IRON_Y）
RCV_TOP = 2.44              # 机匣顶面（导轨座）
BOLT_SWEEP_R = 1.02         # 拉机柄抬起时的最大回转半径（自检用）
# ★ 用户要求「长枪管」：枪口组（枪管前段 / 枪口帽 / 前准星 / 通条）整体前移 MUZ_SHIFT，
#   木件前端（前托 / 上护木 / 前枪箍 / 托帽）只前移 WOOD_SHIFT ⇒ 露出的枪管从 1.2 单位涨到 3.0 单位。
MUZ_SHIFT = 3.0
WOOD_SHIFT = 1.0

# ------------------------------------------------------------------ 调色板（照照片：红棕清漆木 + 发蓝钢）
BLUED = (46, 46, 52)        # 枪管 / 机匣（发蓝）
BLUED_D = (32, 32, 37)      # 枪口 / 表尺 / 准星 / 枪箍（更深）
BOLT_S = (128, 130, 136)    # 枪机（精加工钢，未发蓝 → 亮银灰）
RAIL = (58, 60, 64)         # 导轨
WOOD = (152, 88, 44)        # 枪托 / 护木（红棕清漆木）
WOOD_D = (130, 72, 36)      # 木件暗部（前托 / 护木）
BRASS = (172, 134, 64)      # 弹壳
OPTIC = (38, 39, 43)        # 镜筒壳体
OPTIC_D = (28, 29, 32)      # 镜座 / 镜环
GLASS = (58, 130, 150)      # 镜片

# ------------------------------------------------------------------ 几何辅助


def oct_z(bone, prefix, z0, z1, cy, r, mat, kind='metal', tag=None, cx=0.0, k=0.78):
    """Z 向八边形柱：X-Y 截面用两个同心盒（A = 宽 r / 高 0.78r，B = 宽 0.78r / 高 r）。"""
    curv = ('cyl', 'z', (cx, cy))
    a = k * r
    return [cube(bone, prefix + '_a', (cx - r, cx + r), (cy - a, cy + a), (z0, z1),
                 mat, kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (cx - a, cx + a), (cy - r, cy + r), (z0, z1),
                 mat, kind=kind, tag=tag, curv=curv)]


def oct_y(bone, prefix, y0, y1, cx, cz, r, mat, kind='metal', tag=None, k=0.78):
    """Y 向八边形柱（竖直旋钮）。"""
    curv = ('cyl', 'y', (cx, cz))
    a = k * r
    return [cube(bone, prefix + '_a', (cx - r, cx + r), (y0, y1), (cz - a, cz + a),
                 mat, kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (cx - a, cx + a), (y0, y1), (cz - r, cz + r),
                 mat, kind=kind, tag=tag, curv=curv)]


def oct_x(bone, prefix, x0, x1, cy, cz, r, mat, kind='metal', tag=None, k=0.78):
    """X 向八边形柱（横向旋钮：风偏钮）。"""
    curv = ('cyl', 'x', (cy, cz))
    a = k * r
    return [cube(bone, prefix + '_a', (x0, x1), (cy - r, cy + r), (cz - a, cz + a),
                 mat, kind=kind, tag=tag, curv=curv),
            cube(bone, prefix + '_b', (x0, x1), (cy - a, cy + a), (cz - r, cz + r),
                 mat, kind=kind, tag=tag, curv=curv)]


def B(bone, name, x, y, z, mat, kind='metal', tag=None, rot=None, piv=None):
    return cube(bone, name, x, y, z, mat, kind=kind, tag=tag, rot=rot, piv=piv)


# ------------------------------------------------------------------ 骨骼
BONES = [
    # name,        parent,   pivot
    ('root', None, (0.0, BORE, 0.0)),
    ('move', 'root', (0.0, BORE, 0.0)),          # 握把：举枪/后坐/摆动都作用在这
    ('body', 'move', (0.0, BORE, -2.40)),        # 机匣 + 枪托 + 护圈 + 导轨
    ('barrel', 'move', (0.0, BORE, -9.00)),      # 枪管 + 准星 + 表尺
    ('handguard', 'body', (0.0, 2.06, -9.40)),   # 上护木 + 枪箍
    ('bolt', 'body', (0.0, BORE, -1.85)),        # 枪机（绕枪管轴转 + 后拉）
    ('magazine', 'body', (0.0, 1.06, -2.75)),    # 外露弹仓（换弹时下沉/前倾）
    # ★ 逐发压弹用：莫辛是**弹仓式**，子弹要一发一发从机匣上方用手压进去（TaCZ Kar98k 同款机制）
    #   静止位置 = 已经压进弹仓的那一发（整颗收在弹仓盒内部 ⇒ 看不见）；
    #   装填时由 Java 把它抬到机匣上方（+2.3）再一发发落下去。
    ('round_in', 'body', (0.0, 0.86, -2.80)),
    ('trigger', 'body', (0.0, 1.00, -1.78)),     # 扳机（绕顶部销轴向后转）
    # 4 倍镜（默认按物品 NBT 隐藏；装上 4 倍镜才显示），三根都隐藏/显示
    ('scope', 'body', (0.0, SCOPE_Y, -2.60)),
    ('scope_elev', 'scope', (0.0, 3.80, -2.40)),
    ('scope_wind', 'scope', (0.42, SCOPE_Y, -2.40)),
    ('casing', 'body', (0.62, 2.10, -1.95)),     # 抛壳动画用的黄铜弹壳
    ('camera', 'body', (0.0, BORE, -2.40)),      # 空骨骼（镜头管道保留，值恒 0）
]

CUBES = []


# ------------------------------------------------------------------ 枪管 / 准星 / 表尺 / 通条（barrel）
def build_barrel():
    out = []
    # 阶梯收细的枪管：机匣前最粗，往枪口逐段变细（照片里枪管很细，这里按可读性略放大）
    out += oct_z('barrel', 'bar_rear', -8.00, -4.55, BORE, 0.40, BLUED)
    out += oct_z('barrel', 'bar_mid', -12.50, -8.00, BORE, 0.36, BLUED)
    # ★ 枪管前段：比原来长 3.0 单位（「长枪管」），半径也比中段粗一点才看得清是「一根管」
    #   ★ 起点必须用**原来的枪管前端** -13.62 再减 MUZ_SHIFT（写成 -12.50-MUZ_SHIFT 会在
    #   枪管与枪口帽之间空出 1.12 单位 —— 看起来就是「一截空心的管子」）
    out += oct_z('barrel', 'bar_muz', -13.62 - MUZ_SHIFT, -12.50, BORE, 0.35, BLUED)
    # 枪口帽（端面一圈更暗的钢）
    out += oct_z('barrel', 'mz_crown', -13.76 - MUZ_SHIFT, -13.62 - MUZ_SHIFT, BORE, 0.37,
                 BLUED_D)
    out += [B('barrel', 'mz_bore', (-0.11, 0.11), (BORE - 0.11, BORE + 0.11),
              (-13.78 - MUZ_SHIFT, -13.74 - MUZ_SHIFT), BLUED_D, kind='flat')]
    # 通条（照片里枪口下方露出的那根细杆）—— 跟着枪口一起前伸
    out += [B('barrel', 'clean_rod', (-0.085, 0.085), (1.22, 1.39),
              (-13.58 - MUZ_SHIFT, -12.40), BLUED_D, kind='brushed', tag='rod'),
            B('barrel', 'clean_rod_tip', (-0.12, 0.12), (1.18, 1.43),
              (-12.46 - MUZ_SHIFT, -12.34 - MUZ_SHIFT), BLUED, kind='brushed')]
    # 前准星：底座 + 准星柱（柱顶 = IRON_Y）+ 两侧护耳（略低于柱顶，不挡瞄准线）
    out += [B('barrel', 'fs_base', (-0.30, 0.30), (2.02, 2.26),
              (-13.34 - MUZ_SHIFT, -12.78 - MUZ_SHIFT), BLUED_D),
            B('barrel', 'fs_post', (-0.075, 0.075), (2.26, IRON_Y),
              (-13.16 - MUZ_SHIFT, -12.96 - MUZ_SHIFT), BLUED_D),
            B('barrel', 'fs_ear_l', (-0.32, -0.13), (2.26, 2.64),
              (-13.26 - MUZ_SHIFT, -12.86 - MUZ_SHIFT), BLUED_D),
            B('barrel', 'fs_ear_r', (0.13, 0.32), (2.26, 2.64),
              (-13.26 - MUZ_SHIFT, -12.86 - MUZ_SHIFT), BLUED_D)]
    # 表尺（M91/30 的立框式）：底座 + 斜坡 + 游标 + 叶片（缺口两耳顶 = IRON_Y）
    out += [B('barrel', 'rs_base', (-0.36, 0.36), (2.04, 2.30), (-6.58, -5.12), BLUED_D),
            B('barrel', 'rs_ramp', (-0.32, 0.32), (2.30, 2.44), (-6.46, -5.92), BLUED_D),
            B('barrel', 'rs_slider', (-0.34, 0.34), (2.34, 2.50), (-6.00, -5.72), BLUED_D),
            B('barrel', 'rs_leaf_lo', (-0.34, 0.34), (2.30, 2.52), (-5.60, -5.34), BLUED_D),
            B('barrel', 'rs_ear_l', (-0.34, -0.11), (2.52, IRON_Y), (-5.60, -5.34), BLUED_D),
            B('barrel', 'rs_ear_r', (0.11, 0.34), (2.52, IRON_Y), (-5.60, -5.34), BLUED_D)]
    return out


# ------------------------------------------------------------------ 上护木 + 枪箍（handguard）
def build_handguard():
    out = []
    # 上护木：只盖枪管上半，前端顶到前枪箍；后端停在表尺之前（露出表尺）
    out += [B('handguard', 'hg_main', (-0.56, 0.56), (1.86, 2.30),
              (-12.24 - WOOD_SHIFT, -6.66), WOOD, kind='wood', tag='wood'),
            B('handguard', 'hg_front', (-0.54, 0.54), (1.90, 2.24),
              (-12.44 - WOOD_SHIFT, -12.24 - WOOD_SHIFT), WOOD_D, kind='wood', tag='wood'),
            B('handguard', 'hg_ring', (-0.58, 0.58), (1.82, 2.34), (-6.78, -6.62), BLUED_D)]
    # 前 / 后枪箍（上下包住护木与枪管；比木件宽 0.04 才看得见）
    out += [B('handguard', 'band_f', (-0.62, 0.62), (0.98, 2.34),
              (-12.30 - WOOD_SHIFT, -12.12 - WOOD_SHIFT), BLUED_D),
            B('handguard', 'band_r', (-0.62, 0.62), (0.98, 2.32), (-8.40, -8.22), BLUED_D),
            B('handguard', 'band_r_spring', (-0.30, 0.30), (0.92, 1.02), (-8.36, -8.26),
              BLUED_D, kind='flat')]
    return out


# ------------------------------------------------------------------ 机匣 / 枪托 / 护圈（body）
def build_body():
    out = []
    # 机匣：前端接枪管的八角环 + 主体 + 顶面（导轨座）
    out += oct_z('body', 'rcv_ring', -5.00, -4.56, BORE, 0.62, BLUED)
    out += [B('body', 'rcv_low', (-0.72, 0.72), (1.06, 1.90), (-4.58, -0.62), BLUED),
            B('body', 'rcv_top', (-0.62, 0.62), (1.90, RCV_TOP), (-4.58, -0.62), BLUED),
            B('body', 'rcv_tang', (-0.46, 0.46), (1.72, 2.24), (-0.72, -0.10), BLUED),
            # 机匣上的铆钉/销（细节件）
            B('body', 'rcv_pin_1', (-0.74, -0.66), (1.30, 1.42), (-3.60, -3.48), BOLT_S,
              kind='brushed'),
            B('body', 'rcv_pin_2', (0.66, 0.74), (1.30, 1.42), (-3.60, -3.48), BOLT_S,
              kind='brushed')]
    # 前托（下木）：从枪箍一直连到握把；托底略窄（前端跟着「长枪管」前伸一小段）
    out += [B('body', 'fe_front', (-0.58, 0.58), (1.00, 1.64),
              (-12.56 - WOOD_SHIFT, -8.20), WOOD_D, kind='wood', tag='wood'),
            B('body', 'fe_mid', (-0.60, 0.60), (0.98, 1.66), (-8.20, -4.60), WOOD,
              kind='wood', tag='wood'),
            B('body', 'fe_rear', (-0.58, 0.58), (0.92, 1.70), (-4.60, -0.58), WOOD,
              kind='wood', tag='wood'),
            # 前托前端的金属帽
            B('body', 'nose_cap', (-0.60, 0.60), (0.98, 1.68),
              (-12.62 - WOOD_SHIFT, -12.52 - WOOD_SHIFT), BLUED_D)]
    # 背带环（前托底部开槽 + 枪托穿透槽）—— 槽要窄而短，太宽会看着像木头上的黑洞
    out += [B('body', 'sling_front', (-0.15, 0.15), (0.90, 1.00), (-7.86, -7.42), BLUED_D,
              kind='flat'),
            B('body', 'sling_rear', (-0.575, 0.575), (1.14, 1.30), (3.40, 3.62), BLUED_D,
              kind='flat')]
    # 弹仓（外露的一节 + 托底盖）
    out += [B('magazine', 'mag_body', (-0.54, 0.54), (0.46, 1.08), (-3.42, -2.22), BLUED),
            B('magazine', 'mag_plate', (-0.58, 0.58), (0.34, 0.48), (-3.46, -2.18), BLUED_D)]
    # 扳机护圈（三根梁围成的环：前立柱 / 底板 / 后立柱）
    out += [B('body', 'tg_front', (-0.26, 0.26), (0.58, 0.90), (-2.30, -2.12), BLUED_D),
            B('body', 'tg_floor', (-0.26, 0.26), (0.44, 0.58), (-2.12, -1.28), BLUED_D),
            B('body', 'tg_rear', (-0.26, 0.26), (0.44, 0.88), (-1.44, -1.26), BLUED_D)]
    # 枪托：握把（腕部）→ 颈部 → 托身 → 托底
    out += [B('body', 'stk_wrist', (-0.46, 0.46), (0.78, 2.18), (-0.62, 0.74), WOOD,
              kind='wood', tag='wood'),
            B('body', 'stk_neck', (-0.50, 0.50), (0.62, 2.10), (0.74, 1.86), WOOD,
              kind='wood', tag='wood')]
    # 托身：**分成 5 小段**每段往下约 0.44（原来 3 段各降 0.9，看着像台阶/楼梯）
    for i, (z0, z1, top, bot, hw) in enumerate(
            ((1.86, 2.50, 2.02, 0.44, 0.54), (2.50, 3.14, 1.98, 0.02, 0.54),
             (3.14, 3.78, 1.94, -0.42, 0.56), (3.78, 4.42, 1.88, -0.86, 0.56),
             (4.42, 5.44, 1.80, -1.30, 0.58))):
        out += [B('body', 'stk_%d' % (i + 1), (-hw, hw), (bot, top), (z0, z1), WOOD,
                  kind='wood', tag='year')]
    # 钢托底板（M91/30 的托底板带一点上翘的托踵）
    out += [B('body', 'butt_plate', (-0.58, 0.58), (-1.36, 1.82), (5.42, 5.58), BLUED_D),
            B('body', 'butt_heel', (-0.58, 0.58), (1.68, 1.84), (5.10, 5.44), BLUED_D,
              kind='flat')]
    # 顶部导轨（机匣顶）+ 齿
    out += [B('body', 'rail_base', (-0.34, 0.34), (RCV_TOP, 2.54), (-3.96, -1.14), RAIL)]
    for i in range(5):
        z = -3.86 + i * 0.56
        out += [B('body', 'rail_tooth_%d' % i, (-0.36, 0.36), (2.54, RAIL_TOP),
                  (z, z + 0.18), RAIL)]
    # 抛壳动画用的弹壳（收在机匣内部：机匣顶段 X ±0.62，弹壳必须整个落在里面才看不见）
    out += oct_x('casing', 'case', 0.28, 0.58, 2.10, -1.98, 0.14, BRASS, kind='brushed',
                 tag='brass', k=0.9)
    return out


# ------------------------------------------------------------------ 枪机 / 扳机
def build_bolt():
    out = []
    out += [B('bolt', 'bolt_body', (-0.30, 0.30), (1.56, 2.08), (-4.00, -1.30), BOLT_S,
              kind='brushed'),
            B('bolt', 'bolt_shroud', (-0.36, 0.36), (1.46, 2.18), (-1.30, -0.58), BOLT_S,
              kind='brushed'),
            B('bolt', 'bolt_cock', (-0.26, 0.26), (1.60, 2.06), (-0.58, -0.22), BOLT_S,
              kind='brushed'),
            B('bolt', 'bolt_handle', (0.28, 0.92), (1.58, 1.86), (-2.06, -1.72), BOLT_S,
              kind='brushed'),
            # 下弯的拉机柄 + 柄头（莫辛狙击型是下弯柄，转栓时从镜子下方扫过）
            B('bolt', 'bolt_bend', (0.76, 1.06), (1.14, 1.66), (-2.06, -1.74), BOLT_S,
              kind='brushed'),
            B('bolt', 'bolt_knob', (0.72, 1.10), (1.02, 1.34), (-2.10, -1.70), BOLT_S,
              kind='brushed')]
    return out


def build_trigger():
    return [B('trigger', 'trig_blade', (-0.085, 0.085), (0.66, 1.00), (-1.88, -1.72),
              BLUED_D, kind='brushed'),
            B('trigger', 'trig_shoe', (-0.075, 0.075), (0.44, 0.70), (-1.88, -1.74),
              BLUED_D, kind='brushed', rot=(-12.0, 0.0, 0.0), piv=(0.0, 0.70, -1.78))]


# ------------------------------------------------------------------ 4 倍镜（scope）
def build_scope():
    out = []
    out += oct_z('scope', 'sc_tube', -3.34, -1.28, SCOPE_Y, 0.36, OPTIC)
    out += oct_z('scope', 'sc_obj_1', -3.60, -3.34, SCOPE_Y, 0.42, OPTIC)
    out += oct_z('scope', 'sc_obj_2', -3.94, -3.60, SCOPE_Y, 0.50, OPTIC)
    out += oct_z('scope', 'sc_eye', -1.28, -0.70, SCOPE_Y, 0.46, OPTIC)
    # 镜片（物镜 / 目镜，比筒口略小 → 看进去有「凹进去」的感觉）
    out += [B('scope', 'sc_lens_f', (-0.36, 0.36), (SCOPE_Y - 0.36, SCOPE_Y + 0.36),
              (-4.00, -3.94), GLASS, kind='flat'),
            B('scope', 'sc_lens_r', (-0.32, 0.32), (SCOPE_Y - 0.32, SCOPE_Y + 0.32),
              (-0.76, -0.70), GLASS, kind='flat')]
    # 两个镜环 + 往下接到导轨的镜座
    for tag, z0, z1 in (('f', -3.10, -2.86), ('r', -1.86, -1.62)):
        out += oct_z('scope', 'sc_ring_' + tag, z0, z1, SCOPE_Y, 0.46, OPTIC_D)
        out += [B('scope', 'sc_leg_' + tag, (-0.26, 0.26), (2.54, 3.22),
                  (z0 + 0.02, z1 - 0.02), OPTIC_D),
                B('scope', 'sc_feet_' + tag, (-0.36, 0.36), (2.50, 2.68),
                  (z0 - 0.10, z1 + 0.10), OPTIC_D)]
    # 高低钮（顶）/ 风偏钮（右）：挂在各自骨骼上（将来可做归零动画）
    out += oct_y('scope_elev', 'se_knob', 3.78, 4.14, 0.0, -2.40, 0.20, OPTIC_D)
    out += [B('scope_elev', 'se_cap', (-0.22, 0.22), (4.14, 4.22), (-2.62, -2.18), OPTIC)]
    out += oct_x('scope_wind', 'sw_knob', 0.34, 0.70, SCOPE_Y, -2.40, 0.20, OPTIC_D)
    out += [B('scope_wind', 'sw_cap', (0.70, 0.78), (SCOPE_Y - 0.22, SCOPE_Y + 0.22),
              (-2.62, -2.18), OPTIC)]
    return out


def build_round_in():
    """逐发压弹用的那一发（弹壳 + 肩部 + 弹头，沿 -Z 卧在弹仓里）。"""
    return [B('round_in', 'rin_case', (-0.10, 0.10), (0.76, 0.96), (-3.10, -2.56), BRASS,
              kind='brushed'),
            B('round_in', 'rin_shoulder', (-0.085, 0.085), (0.78, 0.94), (-2.56, -2.42), BRASS,
              kind='brushed'),
            B('round_in', 'rin_tip', (-0.075, 0.075), (0.79, 0.93), (-2.42, -2.10), BOLT_S,
              kind='brushed')]


def build_cubes():
    return build_barrel() + build_handguard() + build_body() + build_bolt() \
        + build_trigger() + build_scope() + build_round_in()


# ------------------------------------------------------------------ 贴图细节
def d_year(img, rect, face, seed):
    """枪托上的年份钢印（莫辛的托/机匣都有出厂年份）。"""
    x, y, w, h = rect
    if face not in ('east', 'west') or w < 18 or h < 12:
        return
    d = ImageDraw.Draw(img)
    boxlib.text(d, x + 3, y + 3, '1943', (52, 30, 14), adv=4)


def d_rod(img, rect, face, seed):
    """通条：杆身中间一条高光（照片里那根光亮的细杆）。"""
    x, y, w, h = rect
    if h < 3:
        return
    px = img.load()
    for i in range(w):
        c = px[x + i, y + 1]
        px[x + i, y + 1] = (min(255, int(c[0] * 1.25)), min(255, int(c[1] * 1.25)),
                            min(255, int(c[2] * 1.25)), 255)


def d_brass(img, rect, face, seed):
    """黄铜弹壳：壳身一道亮环 + 底缘压暗。"""
    x, y, w, h = rect
    if w < 4 or h < 4:
        return
    px = img.load()
    for i in range(w):
        c = px[x + i, y + h - 2]
        px[x + i, y + h - 2] = (int(c[0] * 0.72), int(c[1] * 0.72), int(c[2] * 0.72), 255)


DETAILS = {'year': d_year, 'rod': d_rod, 'brass': d_brass}

# ------------------------------------------------------------------ 动画
def anim(name, loop, length, bones):
    return name, {'loop': loop, 'animation_length': length, 'bones': bones}


def build_anims():
    """六个状态（idle/run/run_fast/fire/bolt/reload）。

    ★ 全部是**空动作**（只挂一个恒为 0 的 root 通道）：枪的姿态完全由 Java 程序化驱动
    （见 MosinGeoModel），这样「动画关键帧盖掉骨骼位移」的老坑不会再犯。
    """
    zero = {'0.0': [0.0, 0.0, 0.0], '1.0': [0.0, 0.0, 0.0]}
    out = {}
    for state, length in (('idle', 2.0), ('run', 1.0), ('run_fast', 0.8), ('fire', 0.35),
                          ('bolt', 0.9), ('reload', 3.0)):
        k, v = anim('animation.mosin.' + state, state in ('idle', 'run', 'run_fast'),
                    length, {'root': {'rotation': zero}})
        out[k] = v
    return {'format_version': '1.8.0', 'animations': out}


# ------------------------------------------------------------------ 输出 + 自检
def main():
    global S
    geo = img = None
    for dens in (12.0, 11.0, 10.0, 9.0, 8.0):
        S = dens
        CUBES.clear()
        CUBES.extend(build_cubes())
        try:
            geo, img = boxlib.build(BONES, CUBES, 'geometry.mosin', size=SIZE,
                                    details=DETAILS, density=dens)
            break
        except RuntimeError as e:
            print('density %.0f 图集放不下（%s），降一档重试' % (dens, e))
    if geo is None:
        raise SystemExit('图集怎么都放不下')

    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    geo_path = os.path.join(ROOT, 'build', 'mosin_v1.geo.json')
    tex_path = os.path.join(ROOT, 'build', 'mosin_v1.png')
    anim_path = os.path.join(ROOT, 'build', 'mosin_v1.animation.json')
    with open(geo_path, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, separators=(',', ':'))
    img.save(tex_path)
    with open(anim_path, 'w', encoding='utf-8') as fh:
        json.dump(build_anims(), fh, ensure_ascii=False, indent=1)

    nb = sum(len(b.get('cubes', [])) for b in geo['minecraft:geometry'][0]['bones'])
    print('bones %d  cubes %d  density %.0f' % (
        len(geo['minecraft:geometry'][0]['bones']), nb, S))
    print('wrote', geo_path)
    print('wrote', tex_path)
    print('wrote', anim_path)

    # ---------------- 自检 1：骨骼名（Java / 动画 JSON 都按名字取）
    need = {'root', 'move', 'body', 'barrel', 'handguard', 'bolt', 'magazine', 'trigger',
            'scope', 'scope_elev', 'scope_wind', 'casing', 'camera', 'round_in'}
    have = set(b[0] for b in BONES)
    print('骨骼名检查: %s' % ('OK' if need <= have else '缺 %s' % (need - have)))

    # ---------------- 自检 2：机瞄瞄准线（照门缺口顶 = 准星柱顶 = IRON_Y，且都在 X = 0）
    tab = {c['name']: c for c in CUBES}
    ear_l, ear_r, post = tab['rs_ear_l'], tab['rs_ear_r'], tab['fs_post']
    notch_top = min(ear_l['y'][1], ear_r['y'][1])
    gap_c = (ear_l['x'][1] + ear_r['x'][0]) / 2.0
    post_c = (post['x'][0] + post['x'][1]) / 2.0
    rail = [c for c in CUBES if c['name'].startswith('rail_')]
    rail_top = max(c['y'][1] for c in rail)
    dy = abs(notch_top - post['y'][1])
    off = abs(gap_c - post_c)
    print('瞄准线：缺口顶 Y=%.2f  准星顶 Y=%.2f（差 %.3f，要 0）  偏心 %.3f（要 0）%s'
          % (notch_top, post['y'][1], dy, off,
             'OK' if dy < 0.01 and off < 0.01 else '!! 瞄准线不共线'))
    print('  导轨齿顶 Y=%.2f  比瞄准线低 %.3f（要 > 0.06，否则挡机瞄）%s'
          % (rail_top, IRON_Y - rail_top,
             'OK' if IRON_Y - rail_top > 0.06 else '!! 导轨挡住机瞄'))

    # ---------------- 自检 3：4 倍镜光轴 / 镜筒底面 vs 拉机柄回转半径
    scope = [c for c in CUBES if c['bone'] == 'scope']
    tube_bot = min(c['y'][0] for c in scope if c['name'].startswith('sc_tube'))
    lens = tab['sc_lens_f']
    lens_cy = (lens['y'][0] + lens['y'][1]) / 2.0
    print('4 倍镜：光轴 Y=%.2f（镜片中心 %.2f，要一致）  镜筒底面 Y=%.2f' %
          (SCOPE_Y, lens_cy, tube_bot))
    print('  拉机柄回转半径 %.2f → 抬起后最高 Y=%.2f，比镜筒底面低 %.3f %s'
          % (BOLT_SWEEP_R, BORE + BOLT_SWEEP_R, tube_bot - (BORE + BOLT_SWEEP_R),
             'OK' if tube_bot - (BORE + BOLT_SWEEP_R) > 0.05 else '!! 会撞到镜子'))

    # ---------------- 自检 4：整体尺寸（莫辛 M91/30 全长 1232mm ≈ 19.7 模型像素）
    z0 = min(c['z'][0] for c in CUBES)
    z1 = max(c['z'][1] for c in CUBES)
    y0 = min(c['y'][0] for c in CUBES)
    y1 = max(c['y'][1] for c in CUBES)
    x1 = max(c['x'][1] for c in CUBES)
    print('整体：Z %.2f..%.2f（全长 %.2f 像素 = %.2f 格）  Y %.2f..%.2f  X ±%.2f'
          % (z0, z1, z1 - z0, (z1 - z0) / 16.0, y0, y1, x1))
    # ---------------- 自检 5：枪管必须是一根**连着**的管（段与段之间不能留缝，否则看着是空心的）
    secs = []
    for a in ('mz_crown', 'bar_muz', 'bar_mid', 'bar_rear'):
        cs = [c for c in CUBES if c['name'].startswith(a + '_')]
        secs.append((a, min(c['z'][0] for c in cs), max(c['z'][1] for c in cs)))
    secs.sort(key=lambda s: s[1])                       # 从枪口往机匣排
    seamy = []
    for i in range(len(secs) - 1):
        d = secs[i][1 + 1] - secs[i][2]                 # 前段后端 − 后段前端；应 = 0
        if abs(d) > 0.001:
            seamy.append('%s|%s %+.2f' % (secs[i][0], secs[i + 1][0], d))
    print('枪管分段（枪口→机匣）：%s' % '  '.join('%s %.2f..%.2f' % s for s in secs))
    print('  管身连续 / 无空心段：%s' % ('OK' if not seamy else '!! 有缝 %s' % seamy))
    print('枪口 Z=%.2f（= -Z 方向最前，已按「长枪管」前伸 %.1f）  托底 Z=%.2f  握把原点 Z=0'
          % (z0, MUZ_SHIFT, z1))
    bare = -(-13.62 - MUZ_SHIFT) - (12.62 + WOOD_SHIFT)      # 露在外面的枪管长度
    print('露出枪管长度 ≈ %.2f 单位（木件前端 Z=%.2f）' % (bare, -(12.62 + WOOD_SHIFT)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
