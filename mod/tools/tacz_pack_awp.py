#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把我们的 AWP 转成一个 TaCZ 枪包（试点）。

TaCZ 枪包 = 「资源包 + 数据包」的结合体，根目录下必须有 gunpack.meta.json：
    <根目录>/
      gunpack.meta.json                 {"namespace":"hexalunar","dependencies":{"tacz":"[1.1.4,)"}}
      assets/<ns>/                      ← 客户端资产（标准资源包）
        gunpack_info.json               枪包信息（工作台里展示）
        geo_models/gun/awp_geo.json     基岩版模型（逐面 UV，TaCZ 官方全是这套）
        textures/gun/uv/awp.png         模型贴图
        textures/gun/slot/awp.png       背包/快捷栏 2D 贴图（32x32）
        display/guns/awp_display.json   显示与音效配置
        lang/zh_cn.json  lang/en_us.json
        tacz_sounds/awp/*.ogg           音效（不能塞进原版 sounds/）
      data/<ns>/                        ← 服务端数据（标准数据包）
        index/guns/awp.json             定义一把枪（物品 id = 文件名）
        data/guns/awp_data.json         数值（弹药/伤害/后坐/装填）
        recipes/gun/awp.json            枪械工作台配方

硬性组名（TaCZ 源码里的字面量，大小写敏感，缺了功能就失效）：
    root / righthand_pos / lefthand_pos / muzzle_flash / shell /
    magazine(→ mag_standard, mag_extended_1..3) / bullet_in_mag / bullet_in_barrel /
    iron_view / idle_view / ground / fixed / thirdperson_hand / camera / constraint
★ TaCZ 认的是 `magazine`；官方 ai_awp 里的 `magzine` 是笔误（代码里没有这个串）。
★ `gun_pos` / `muzzle_pos` / `positioning` / `views` 只是建模分组，TaCZ 不识别，随便用。
★ 定位组的 pivot 一律写「模型空间绝对坐标」—— TaCZ 直接读 pivot 值。
★★ 但**仅靠 pivot 不够**：TaCZ 的手是「挂在 righthand_pos / lefthand_pos 上的固定尺寸
  手臂模型」（setFunctionalRenderer + RightHandRender / LeftHandRender），手臂长短不随枪缩放
  ⇒ 想让官方的持枪姿态 1:1 生效，必须**把枪也搬进官方的坐标空间**（见 build_geo 上方
  S_GUN / T() 那整段注释与本文件顶部说明）。
★ 手臂手骨里那个 4x12x4 方块是官方的占位块（说明手模从 pivot 往 +Y 伸 12 模型单位），
  已原样照抄。
"""
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))          # mod/tools
MOD = os.path.dirname(HERE)                                 # mod
SRC = os.path.join(MOD, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
OUT = os.path.join(MOD, 'tacz_pack', 'hexalunar_gun_pack')
MC = r'C:\Users\Administrator\Desktop\.minecraft'
# ★ 这个实例开了「版本隔离」：真正的游戏目录是 versions/<版本>/，
#   TaCZ 扫的也是 versions/<版本>/tacz —— 实测日志：
#   [tacz/GunPackFinder]: Start scanning for gun packs in ...\versions\1.20.1-Forge_47.4.23-2\tacz
#   放错到 .minecraft/tacz 会**一句日志都不报**，表现就是「枪根本没出现」。
INSTANCE = os.path.join(MC, 'versions', '1.20.1-Forge_47.4.23-2')
DEPLOY = os.path.join(INSTANCE, 'tacz')

NS = 'hexalunar'
GUN = 'awp'

# ── 我们模型里的锚点（模型像素；原点 = 机匣中心，枪口朝 -Z，上 = +Y）──────────
P_GRIP = [0.0, -1.07, 1.31]      # 握把 —— 右手（AwpGeoModel.ARM_GRIP）
P_SUPPORT = [0.0, -0.55, -3.30]  # 护木 —— 左手（AwpGeoModel.ARM_SUPPORT）
P_MAG = [0.0, 0.00, 0.90]        # 弹匣（AwpGeoModel.MAG_PZ / magazine pivot）
P_BOLT = [0.615, 1.50, 0.375]    # 枪机 / 拉机柄（BOLT_PX/PY/PZ）
P_SHELL = [0.20, 1.57, -2.50]    # 抛壳口（原 casing pivot）
P_MUZZLE = [0.0, 1.575, -18.20]  # 枪口（barrel 体素末端 z=-18，膛轴 y=1.575）
P_BORE = [0.0, 1.575, -3.20]     # 膛内弹位置
# ★★ 眼球位置必须退到模型**外面**：太近就把相机插进枪身，屏幕上是一大块全黑
#   （实测踩过：枪真出来了、HUD/名字都对，但第一人称是一坨黑）。
#
# ★★★ 坐标按官方三把枪（ai_awp / ak47 / kar98）实测规律反推：
#   · iron_view.x **永远 = 0** —— 机瞷时视线就在枪轴正上方，偏了准心就歪；
#   · idle_view.x **有 2~3 的偏移** —— 就是靠它把枪推到屏幕一角；
#     两把枪都设 x=0 的话，相机卡在枪轴线上往前看，枪会缩成一根正对的竖条（踩过）。
#   · iron_view.y ≈ 枪轴 + 1.2~2.3；idle_view.y ≈ 枪轴 + 2.25~3.45
#   · iron_view.z ≈ 枪口 z 再往后 1.15 倍“枪口→枪尾”长度
#     我们：枪口 z=−18.2、枪尾 z=+6.0 ⇒ −18.2 + 24.2×1.15 ≈ **9.6**
#   · camera 的 pivot 与 idle_view 完全相同（官方三把枪都是这样）
# ★★★ 决定「枪在屏幕上躺得有多平」的是**离轴角** = atan(偏移 / (相机到枪尾的距离))：
#   官方 ai_awp：x 3.03 / y 2.48 / 距离 4.5 ⇒ **x 角 34°、y 角 29°**
#   （角度太小 ⇒ 相机几乎在枪轴正后方 ⇒ 枪会正对着你「立」在屏幕中间，实测踩过）
#   我们：相机到枪尾 3.6 ⇒ x = 3.6·tan34° ≈ 2.4、y = 枪轴 1.575 + 3.6·tan29° ≈ 3.6
P_SCOPE_EYE = [0.0, 2.82, 9.60]   # 机瞷：x 必须 0；y 角 ~19°（官方 iron 1.55/4.5）
P_HIP_EYE = [2.40, 3.60, 9.60]    # 腰射：x 角 34° / y 角 29°，与官方一致
P_GROUND = [0.0, -1.90, 0.00]    # 掉落物：模型正下方（body 最低 y = -1.90）

# ★★★ 两只手的角度/位移，照抄官方 ai_awp 的 `static_idle`（原封不动）。
#   手臂模型是 TaCZ 自己那套**固定尺寸**的手模，坐标系与枪模型无关 ⇒ 数值可直接用。
ROT_HAND_R = [99.92205, 19.38449, -168.50279]
POS_HAND_R = [-6.8, -15.825, 0.45]
ROT_HAND_L = [107.0152, -378.11296, -163.85497]
POS_HAND_L = [8.375, -15.0, -12.0]
SCALE_HAND = [1.0, 1.5, 1.0]

# ★★★★★ 「直接套用精密国际 AWM 的持枪」—— 实测定案（2026-09-21）★★★★★
#
# TaCZ 的手是**挂在 `righthand_pos` / `lefthand_pos` 上的固定尺寸手臂模型**：
#   `BedrockAnimatedModel.setFunctionalRenderer("righthand_pos", RightHandRender::new)`
#   （左手续 `LeftHandRender`），渲染时只把当前骨骼变换压进矩阵，再画它自己那个手模。
#   官方 ai_awp 里这两个骨骼内就摆着一个 **4x12x4 的占位方块**，说明手模就是
#   「从手骨 pivot 起、往 +Y 伸 12 模型单位」。
# ★ 关键推论：**手模的长短粗细是固定的，不随枪的大小缩** ⇒ 枪与手的比例完全
#   由「枪在模型空间里占多少单位」决定：
#     · 官方 ai_awp：枪长 54.4 单位（z −33.07 .. +21.34）、膛轴 y=8
#     · 我们的枪：　枪长 24.0 单位（z −18.20 .. +6.00）、膛轴 y=1.575
#   ⇒ 我们的模型密度只有官方的一半。于是：
#     · 照抄官方 pivot → 手跑到枪后 40 单位外，手臂被拉成一大片粉色楔子（实测踩过）
#     · 只抄旋转、不动 pivot → 手竖在握把上、方向也不对（实测踩过）
# ★ 唯一正确的做法：**把我们的几何整体缩放/平移，搬进官方 ai_awp 的坐标空间**，
#   这样官方的手骨 pivot / `static_idle` / display 数值才能 1:1 生效。
#
# 变换（以「握把 → 枪口」对齐官方：官方握把 z=8、枪口 z=−33.225）：
#   s = (8 − (−33.225)) / (1.31 − (−18.20)) = 2.113
#   x' = s·x
#   y' = s·y + (8 − s·1.575)          ← 膛轴 1.575 → 8
#   z' = s·(z − 1.31) + 8             ← 握把 1.31 → 8，枪口 −18.2 → −33.23（正好落在官方枪口）
S_GUN = 2.113
GRIP_Z_OUR = 1.31
GRIP_Z_OFF = 8.0
AXIS_Y_OUR = 1.575
AXIS_Y_OFF = 8.0
DY_GUN = AXIS_Y_OFF - S_GUN * AXIS_Y_OUR          # 4.672

# ★★★★★ X 要镜像（2026-09-21 用官方四把枪交叉验证）★★★★★
# TaCZ 模型空间的「射手右侧」是 **−X**，而我们自己（以及自己模组里已验证的那套）是 **+X**：
#   · ai_awp  `bolt_rotate` −2.39..−0.16、`ball`（拉机柄球）−2.84..−1.59  → 真枪 AWP 拉机柄在右
#   · ak47    `bolt`（拉机柄）−2.18..0.69                                   → 真枪 AK 拉机柄在右
#   · hk416d  `416d_bolt` −1.46..0.56                                       → 真枪 HK416 拉机柄在右
#   · m4a1    `bolt_release` **+0.51..+0.86**                               → AR 的枪机挂机柄在**左**
# ⇒ 不镜像的话，我们的拉机柄 / 抛壳口 / 风偏钮全跑到左边（用户截图圈出过）。
# 手部那 6 个骨骼与 `views` / `camera` 的 x **不镜像**（它们已经是官方的值/官方语义）。
MIRROR_X = -1.0


def T(p):
    """我们模型空间的点 -> 官方 ai_awp 模型空间（含 X 镜像）。"""
    return [round(MIRROR_X * p[0] * S_GUN, 5),
            round(p[1] * S_GUN + DY_GUN, 5),
            round((p[2] - GRIP_Z_OUR) * S_GUN + GRIP_Z_OFF, 5)]


def TC(c):
    """我们模型里的一个方块 -> 官方模型空间（UV 不动，缩放/镜像不影响逐面 UV）。

    镜像时要把盒子折过来：x 区间 [x0, x0+w] → [−(x0+w), −x0]。
    """
    x0, w = c['origin'][0], c['size'][0]
    nx = -(x0 + w) * S_GUN if MIRROR_X < 0 else x0 * S_GUN
    return {'origin': [round(nx, 5),
                       round(c['origin'][1] * S_GUN + DY_GUN, 5),
                       round((c['origin'][2] - GRIP_Z_OUR) * S_GUN + GRIP_Z_OFF, 5)],
            'size': [round(abs(w) * S_GUN, 5),
                     round(c['size'][1] * S_GUN, 5),
                     round(c['size'][2] * S_GUN, 5)],
            'uv': c['uv']}


def TCS(cubes):
    return [TC(c) for c in (cubes or [])]


def TV(p):
    """视图/相机专用：与 T 相同但**不做 X 镜像**。

    `idle_view` / `iron_view` / `camera` 的 x 在 TaCZ 里是「屏幕构图」语义
    （官方 ai_awp 的 idle_view.x = **+3.03** ⇒ 枪落在屏幕右下），
    跟枪自身几何的左右约定（−X = 射手右侧）不是一回事 ⇒ 不能跟着镜像。
    """
    return [round(p[0] * S_GUN, 5),
            round(p[1] * S_GUN + DY_GUN, 5),
            round((p[2] - GRIP_Z_OUR) * S_GUN + GRIP_Z_OFF, 5)]


# ★ 手部骨架 6 个容器 + 2 个手骨，pivot **原样照抄官方 ai_awp**（已搬进同一坐标空间）。
#   `righthand_pos` 与 `lefthand_pos` 的 pivot 完全相同 (0,8,8)，但一个挂右手、
#   一个挂左手 —— 两只手的区分靠父链，所以这 6 个容器必须成套用官方的值。
P_GH_R = [0.0, 5.0, 8.0]         # gun_and_righthand
P_RH = [6.0, 19.0, 8.0]          # righthand
P_RHP = [0.0, 8.0, 8.0]          # righthand_pos
P_GL = [0.0, 5.35, 2.175]        # mag_and_lefthand
P_LH = [-6.0, 19.0, 8.0]         # lefthand
P_LHP = [0.0, 8.0, 8.0]          # lefthand_pos

# 官方手骨里那个 4x12x4 占位方块的逐面 UV —— 连这个都照抄，行为与官方 100% 一致。
HAND_UV = {
    'north': {'uv': [0, 0], 'uv_size': [4, 12]},
    'east': {'uv': [4, 0], 'uv_size': [4, 12]},
    'south': {'uv': [8, 0], 'uv_size': [4, 12]},
    'west': {'uv': [0, 12], 'uv_size': [4, 12]},
    'up': {'uv': [12, 0], 'uv_size': [4, 4]},
    'down': {'uv': [4, 16], 'uv_size': [4, -4]},
}
HAND_CUBE_R = {'origin': [4.0, 8.0, 6.0], 'size': [3.0, 12.0, 4.0], 'uv': HAND_UV}
HAND_CUBE_L = {'origin': [-7.0, 8.0, 6.0], 'size': [3.0, 12.0, 4.0], 'uv': HAND_UV}

# 倍镜装配点（官方坐标空间）：我们导轨顶在 y 9.24、镜筒中段在 z 2.45。
# x 必须 0（正中间）—— 这是把 `AttachmentType.SCOPE` 的镜子挂到导轨上的那个点。
SCOPE_POS = [0.0, 9.395, 2.45]

CUBES_NONE = []                  # 纯定位组（无方块）


def load_src_geo():
    with open(os.path.join(SRC, 'geo', 'awp.geo.json'), encoding='utf-8') as f:
        return json.load(f)


def bone(name, pivot, parent, cubes=None, rotation=None):
    b = {'name': name, 'pivot': [round(float(v), 5) for v in pivot], 'cubes': list(cubes or [])}
    if parent:
        b['parent'] = parent
    if rotation:
        b['rotation'] = [round(float(v), 5) for v in rotation]
    return b


def build_geo():
    """把我们 18 骨骼的 AWP 重组成 TaCZ 结构，并把几何搬进官方 ai_awp 的坐标空间。"""
    src = load_src_geo()
    sgeo = src['minecraft:geometry'][0]
    old = {b['name']: b for b in sgeo['bones']}

    # 原骨骼 -> 新位置。映射规则：
    #   casing  -> shell（TaCZ 抛壳定位组；它自己的立方体丢掉，TaCZ 会自己抛）
    #   bolt    -> bolt_fix（保留方块），外面套 bolt_group -> bolt_rotate
    #   magazine-> mag_standard（保留方块），外面套 magazine
    #   mag_r*/round_in -> bullet_in_mag 的子级（TaCZ 弹容 0 时自动隐藏）
    direct = ['body', 'barrel', 'bipod', 'trigger']
    # 镜筒 + 三个调节钮：整棵挂到 `scope_default` 下 ——
    # TaCZ 的名字约定是 `<配件类型>_default` = 枪自带的那个零件，装了同类配件就会被隐藏
    # （`GunModelConstant.DEFAULT_ATTACHMENT_SUFFIX = "_default"` + `scopeHiddenRender`）。
    scope_kids = ['scope_adjust', 'scope_elev', 'scope_wind']
    mag_rounds = ['round_in', 'mag_r1', 'mag_r2', 'mag_r3', 'mag_r4']

    bones = []

    def add(*a, **kw):
        bones.append(bone(*a, **kw))

    # 根与顶层
    add('root', [0, 0, 0], None)
    add(NS + '_' + GUN, [0, 0, 0], 'root')
    top = NS + '_' + GUN

    # 右手链（pivot 全部照抄官方 ai_awp，见上方 P_GH_R/P_RH/P_RHP 注释）
    add('gun_and_righthand', P_GH_R, top)
    add('righthand', P_RH, 'gun_and_righthand')
    add('righthand_pos', P_RHP, 'righthand', cubes=[HAND_CUBE_R])

    # 枪本体（★ 直接挂顶层：不放进手部容器，免得以后调手骨时把整个模型带偏）
    add('awp_body', [0, 0, 0], top)
    add('gun_pos', [0, 0, 0], 'awp_body')
    for n in direct:
        if n in old:
            add(n, T(old[n]['pivot']), 'gun_pos', cubes=TCS(old[n].get('cubes')))

    # 枪自带的镜子（装了倍镜配件后 TaCZ 会自动把它藏起来）
    if 'scope' in old:
        add('scope_default', T(old['scope']['pivot']), 'gun_pos',
            cubes=TCS(old['scope'].get('cubes')))
        for n in scope_kids:
            if n in old:
                add(n, T(old[n]['pivot']), 'scope_default', cubes=TCS(old[n].get('cubes')))

    # ★ 倍镜挂点：TaCZ 把 `<配件类型>_pos` 当作装配点（`scopePosPath` →
    #   `AttachmentRender.renderAttachment(...)`）。官方 ai_awp 的 `scope_pos` 在
    #   导轨顶 y 8.67 上方 0.155、z 取机匣中部；我们同理取导轨顶 9.24 + 0.155、z 取镜子中段。
    add('scope_pos', SCOPE_POS, 'gun_pos')

    # 左手链（同上，pivot 照抄官方）+ 手骨占位方块
    add('mag_and_lefthand', P_GL, top)
    add('lefthand', P_LH, 'mag_and_lefthand')
    add('lefthand_pos', P_LHP, 'lefthand', cubes=[HAND_CUBE_L])

    # 弹匣（★ 直接挂顶层，位置由我们自己的模型变换得到）
    add('magazine', T(P_MAG), top)
    add('mag_standard', T(P_MAG), 'magazine',
        cubes=TCS(old['magazine'].get('cubes')) if 'magazine' in old else [])
    add('bullet_in_mag', T(P_MAG), 'magazine')
    for n in mag_rounds:
        if n in old:
            add(n, T(old[n]['pivot']), 'bullet_in_mag', cubes=TCS(old[n].get('cubes')))

    # 枪机（TaCZ 的手动枪机动画会驱动 bolt_group / bolt_rotate）
    #   ★ `bolt_rotate` 的 pivot 放在**膛轴**（x=0, y=8）上：拉机柄是绕枪管轴抬起来的，
    #     放在拉机柄自己身上会变成「绕柄自转」，看着像枪机没动。
    add('bolt_group', T([P_BOLT[0], AXIS_Y_OUR, P_BOLT[2]]), 'gun_pos')
    add('bolt_rotate', T([0.0, AXIS_Y_OUR, P_BOLT[2]]), 'bolt_group')
    add('bolt_fix', T(P_BOLT), 'bolt_rotate',
        cubes=TCS(old['bolt'].get('cubes')) if 'bolt' in old else [])

    # 抛壳时**看得见的空弹壳**（TaCZ 的 bolt / reload 动画会驱动 `bullet_shell`，
    # 平时用 scale 0 藏起来；世界里那枚由 TaCZ 的 popShellFrom(0) 自己抛）
    if 'casing' in old:
        add('bullet_shell', T(old['casing']['pivot']), 'gun_pos',
            cubes=TCS(old['casing'].get('cubes')))

    # 枪口 / 抛壳 / 膛内弹
    add('muzzle_flash', T(P_MUZZLE), 'gun_pos')
    add('shell', T(P_SHELL), 'gun_pos')
    add('bullet_in_barrel', T(P_BORE), 'awp_body')

    # 配件 / 锚点组
    add('camera', TV(P_HIP_EYE), top)      # 官方三把枪的 camera 都与 idle_view 完全一致（不镜像 x）
    add('constraint', T([0.0, AXIS_Y_OUR, -5.0]), 'awp_body')
    add('sight', [0, 0, 0], 'awp_body')
    # ★ 不写 `attachment_adapter`：官方 ai_awp 就没有这个骨骼，TaCZ 自己有默认的挂点。
    #   以前给它写了 (0,0,0) —— 那是模型原点（机匣下方），装上镜子会跑到枪身底下去。

    # 视觉定位组（TaCZ 硬性要求 5 个）
    add('positioning', [0, 0, 0], top)
    add('ground', T(P_GROUND), 'positioning')
    add('thirdperson_hand', T(P_GRIP), 'positioning', rotation=[0, 15, 0])
    add('fixed', [0, 0, 0], 'positioning', rotation=[0, 90, 0])
    add('views', [0, 0, 0], top)
    add('iron_view', TV(P_SCOPE_EYE), 'views')
    add('idle_view', TV(P_HIP_EYE), 'views')

    return {
        'format_version': src.get('format_version', '1.12.0'),
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.%s_%s' % (NS, GUN),
                'texture_width': sgeo['description']['texture_width'],
                'texture_height': sgeo['description']['texture_height'],
                # 搬进官方坐标空间后模型尺寸与官方同级（枪长 ~54 单位）⇒ 边界值照官方 ai_awp
                'visible_bounds_width': 5,
                'visible_bounds_height': 3,
                'visible_bounds_offset': [0, 0.5, 0],
            },
            'bones': bones,
        }],
    }


# ── 其余文件内容 ─────────────────────────────────────────────────────────────
def index_json():
    return {
        'name': '%s.gun.%s.name' % (NS, GUN),
        'display': '%s:%s_display' % (NS, GUN),
        'data': '%s:%s_data' % (NS, GUN),
        'tooltip': '%s.gun.%s.desc' % (NS, GUN),
        'type': 'sniper',
        'sort': 1,
    }


def data_json():
    """数值：弹药沿用 TaCZ 自带的 .338；伤害/装填时长照我们 AwpRifleItem 的常量。"""
    return {
        'ammo': 'tacz:338',
        'ammo_amount': 5,                      # MAG_SIZE
        'extended_mag_ammo_amount': [6, 7, 8],
        'bolt': 'manual_action',               # 栓动
        'rpm': 43,                             # 1000ms / CYCLE_TICKS 28
        'bullet': {
            'life': 0.9,
            'bullet_amount': 1,
            'damage': 24,                      # 我们 AWP 单发 24 点
            'tracer_count_interval': 0,
            'extra_damage': {
                'armor_ignore': 0.60,
                'head_shot_multiplier': 2,
                'damage_adjust': [
                    {'distance': 80, 'damage': 24},
                    {'distance': 160, 'damage': 21},
                    {'distance': 'infinite', 'damage': 15},
                ],
            },
            'speed': 575,
            'gravity': 0.15,
            'knockback': 0,
            'friction': 0.015,
            'ignite': False,
            'pierce': 4,
            'explosion': {'explode': False, 'damage': 60, 'radius': 1.25,
                          'knockback': True, 'delay': 1},
        },
        'reload': {
            'type': 'magazine',
            'feed': {'empty': 3.30, 'tactical': 2.20},     # (RELOAD_TICKS+BOLT_TICKS)/20
            'cooldown': {'empty': 3.70, 'tactical': 2.60},
        },
        'draw_time': 0.5,
        'put_away_time': 0.75,
        'aim_time': 0.25,
        'sprint_time': 0.2,
        'bolt_action_time': 1.1,                          # BOLT_TICKS 22 / 20
        'weight': 6.9,
        'movement_speed': {'base': 0.0, 'aim': -0.4, 'reload': -0.2},
        'crawl_recoil_multiplier': 1.5,
        'fire_mode': ['semi'],
        'recoil': {
            'pitch': [
                {'time': 0, 'value': [1.75, 1.75]},
                {'time': 0.08, 'value': [-0.9, -0.9]},
                {'time': 0.17, 'value': [0.55, 0.55]},
                {'time': 0.28, 'value': [-0.2, -0.2]},
                {'time': 0.5, 'value': [0, 0]},
                {'time': 0.8, 'value': [0, 0]},
            ],
            'yaw': [
                {'time': 0, 'value': [-0.75, -0.75]},
                {'time': 0.08, 'value': [0.6, 0.6]},
                {'time': 0.17, 'value': [-0.35, -0.35]},
                {'time': 0.28, 'value': [0.25, 0.25]},
                {'time': 0.5, 'value': [0, 0]},
                {'time': 0.8, 'value': [0, 0]},
            ],
        },
        'inaccuracy': {'stand': 5, 'move': 5.5, 'sneak': 3, 'lie': 2.5, 'aim': 0.05},
        'melee': {
            'distance': 1,
            'cooldown': 1.0,
            'default': {'animation_type': 'melee_stock', 'distance': 1.25,
                        'range_angle': 30, 'damage': 5, 'knockback': 1, 'prep': 0.1},
        },
        'allow_attachment_types': ['extended_mag', 'scope', 'muzzle'],
    }


def display_json():
    return {
        'model': '%s:gun/%s_geo' % (NS, GUN),
        'texture': '%s:gun/uv/%s' % (NS, GUN),
        'slot': '%s:gun/slot/%s' % (NS, GUN),
        'hud': '%s:gun/hud/%s' % (NS, GUN),
        'animation': '%s:%s' % (NS, GUN),
        'state_machine': 'tacz:manual_action_state_machine',   # TaCZ 自带栓动状态机
        # 状态机会在这个时刻调 popShellFrom(0) 抛壳 ⇒ 必须与动画里空壳出现的 SHELL_POP_T 对齐
        'state_machine_param': {'bolt_shell_ejecting_time': SHELL_POP_T},
        'use_default_animation': 'rifle',                      # TaCZ 内置步枪动画
        'transform': {
            'scale': {'thirdperson': [0.6, 0.6, 0.6],
                      'ground': [0.6, 0.6, 0.6],
                      'fixed': [1.2, 1.2, 1.2]},
        },
        'muzzle_flash': {'texture': 'tacz:flash/common_muzzle_flash', 'scale': 1},
        # ★★★ `iron_zoom` 只是**机瞷**的轻微放大 —— TaCZ 官方没有一把枪超过 2：
        #   ai_awp 1.5 / ak47 1.33 / kar98 2。真正的「倍镜」是**配件**：
        #   镜子自己的 display json 里写着 `"scope": true, "zoom": [8], "fov": ...`，
        #   TaCZ 会把相机换到它的 `scope_view` 骨骼并叠一层分划遮罩。
        #   我们一开始照自己模组写了 8.0 ⇒ 世界被放大 8 倍却**没有镜筒也没有分划**，
        #   枪身直接糊住整屏（症状：右键「没有正常打开倍镜」）。
        #   现在用官方 ai_awp 的 1.5，8 倍留给配件镜子（见 tacz_tags/allow_attachments）。
        'iron_zoom': IRON_ZOOM,
        'zoom_model_fov': 35,
        'shell': {
            'initial_velocity': [8, 2, -3.5],
            'random_velocity': [2, 1, 3],
            'acceleration': [0.0, -20, 0.0],
            'angular_velocity': [360, -1200, 90],
            'living_time': 1.0,
        },
        'sounds': {
            'shoot': '%s:%s/%s_shoot' % (NS, GUN, GUN),
            'reload_empty': '%s:%s/%s_reload_empty' % (NS, GUN, GUN),
            'reload_tactical': '%s:%s/%s_reload_tactical' % (NS, GUN, GUN),
            'bolt': '%s:%s/%s_bolt' % (NS, GUN, GUN),
        },
    }


def recipe_json():
    """枪械工作台配方。result.id 指向我们自己的枪 —— 这就是「借用 TaCZ 合成台」的关键。"""
    return {
        'materials': [
            {'item': {'tag': 'forge:ingots/iron'}, 'count': 120},
            {'item': {'tag': 'forge:ingots/gold'}, 'count': 40},
            {'item': {'tag': 'forge:gems/diamond'}, 'count': 8},
            {'item': {'tag': 'forge:rods/blaze'}, 'count': 4},
        ],
        'result': {'type': 'gun', 'id': '%s:%s' % (NS, GUN), 'attachments': {}},
        'type': 'tacz:gun_smith_table_crafting',
    }


def attachments_tag_json():
    """可装配件白名单（真正管附件的是这张标签，不是 data 里的 allow_attachment_types）。

    路径：`data/<ns>/tacz_tags/attachments/allow_attachments/<枪 id>.json`，内容是物品标签列表。
    ★ 这就是「右键正常开倍镜」的另一半：不给这张表的话，TaCZ 的倍镜根本装不上去，
      而只靠 `iron_zoom` 是永远开不出带分划的镜筒视野的。
    """
    return ['#tacz:scope', '#tacz:sniper_extended_mag', '#tacz:muzzle_silencer',
            '#tacz:ammo_mod', '#tacz:scope_lowsight']


def pack_info_json():
    return {
        'version': '1.0.0',
        'name': '六相月灾枪包',
        'description': '把「六相月灾」的 AWP 栓动狙击枪接进 TaCZ（试点）',
        'license': 'ARR',
        'authors': ['SevenZeroMeow'],
        'date': '2026-09-21',
        'url': 'https://github.com/SevenZeroMeowTeam/hexalunar',
    }


# ── 动画 ─────────────────────────────────────────────────────────────────────
# ★★ 踩过的坑（2026-09-21）：枪包一开始**只写了 static_idle**，`bolt` 还是从我们模组自己那份
#   被挖空的动画里抄来的（r88 为了不让动画盖掉代码姿态，把 awp.bolt 的骨骼通道全删了）
#   ⇒ 游戏里「换弹、拉栓一点动作都没有」。TaCZ 认的动画名（从 `GunAnimationConstant`
#   与官方 ai_awp 的动画文件交叉核对得到）：
#     static_idle / static_bolt_caught / draw / put_away / shoot /
#     bolt / reload_tactical / reload_empty / inspect / inspect_empty
#   其中 bolt 由状态机 `manual_action_state_machine` 的 `runAnimation("bolt", ...)` 调用，
#   reload_tactical / reload_empty 对应 data 里 `reload.feed.{tactical,empty}` 两种换弹。
#   idle / walk / run / aim 那套交给 TaCZ 内置的 `use_default_animation: rifle`。
# ★ 下面的数值**全部是我们自己的**（不是抄 TaCZ 的）：抬柄 62°、枪机后退 4.0 单位，
#   来自我们模组自己的 `AwpGeoModel.BOLT_LIFT = 62°` / `BOLT_BACK = 1.90 模型像素`（×2.113）。
#  ★★ 镜像 X 之后，**绕 Y / Z 的旋转方向也要跟着翻**（否则拉机柄会往下压）：
#     镜像 M = diag(−1,1,1) 下 M·R_z(θ)·M = R_z(−θ)、M·R_y(θ)·M = R_y(−θ)，而 R_x 不受影响。
#     所以下面所有旋转的 y/z 分量都取了反号（x 分量不动）；平移只有 x 分量要翻。
BOLT_LIFT = -62.0       # 拉机柄抬起角（度，绕枪管轴；负号 = 柄往枪身上方抬）
BOLT_BACK = 4.0         # 枪机后退（模型单位）
MAG_DROP = 11.0         # 换弹时弹匣下坠
MAG_TILT = 45.0         # 换弹时弹匣翻转角
# ★★ 换弹时整枪的姿态 —— 照官方 ai_awp 的 `reload_*`：它的 root 稳定在
#    rotX ≈ −10.4 / rotY ≈ −2.9 / rotZ ≈ −20~−23（枪口略低 + 枪身向外侧倒）。
#    我们原来写的是 `[0, 0, +16]`（只转 Z、而且符号相反）⇒ 游戏里看着是**向里侧倒**，
#    用户反馈「换弹枪身应该外倾不是内倾」⇒ 现在直接采用官方那一组符号与幅值。
RELOAD_TILT = (-10.0, -3.0, -20.0)
# ★★ 拉栓时序（秒，相对动作开始的时刻）—— 用户要求的表现是：
#    手抬起抓住拉机柄 → **向上翻腕** → 跟着枪机往后拉 → 再推回去。
#    所以时间线是「手先到位（grab）→ 翻腕的同时把柄抬起来（lift）→ 跟着一起后退（back）
#    → 停一下（hold）→ 推回（fwd）→ 压柄（close）」，手比枪机先动。
BOLT_T = {'grab': 0.20, 'lift': 0.38, 'back': 0.56,
          'hold': 0.70, 'fwd': 0.86, 'close': 0.96}
# 膛里那颗空壳出现的时刻：**必须等于** display 里的 `bolt_shell_ejecting_time`
# （状态机到点会调 popShellFrom(0) 抛一颗世界空间的壳，两边不对齐就会「先响后飞」）
SHELL_POP_T = 0.56
RECOIL_PITCH = 4.0      # 开火：+X 旋转 = 枪口向上
RECOIL_BACK = 3.0       # 开火：+Z = 向射手方向后座

# ★★★ 机瞷放大倍率 —— 只能给**轻微**的（TaCZ 官方最高 2：ai_awp 1.5 / ak47 1.33 / kar98 2）。
#   真正的「倍镜」是**配件**（镜子的 display json 里写 `"scope": true, "zoom": [8]`，
#   TaCZ 会把相机换到它的 `scope_view` 骨骼 + 叠一层分划遮罩）。
#   一开始我们照自己模组写了 8.0 ⇒ 世界放大 8 倍却既无镜筒也无分划，枪身糊住整屏。
IRON_ZOOM = 1.5


def _t(t):
    """0.30 -> '0.3'（关键帧的时间键，与 _k 同一套写法）"""
    s = ('%.4f' % float(t)).rstrip('0').rstrip('.')
    return s if s else '0'


def _k(seq):
    """[(t, [x, y, z]), ...] -> {"0": [...], "0.12": [...]}"""
    return {_t(t): [round(float(x), 5) for x in v] for t, v in seq}


def _hand(rot0, pos0, seq):
    """手骨关键帧。seq = [(t, Δ位置, Δ旋转), ...]，增量相对**持枪姿态**（{@link _hands}）。

    用增量写：三个五位小数不用抄来抄去，而且一眼能看出「这一刻手离握把多远」。
    """
    rot, pos = {}, {}
    for t, dp, dr in seq:
        rot[_t(t)] = [round(rot0[i] + dr[i], 5) for i in range(3)]
        pos[_t(t)] = [round(pos0[i] + dp[i], 5) for i in range(3)]
    return {'rotation': rot, 'position': pos, 'scale': list(SCALE_HAND)}


def _shift(seq, dt):
    """把动作表的时刻整体后移 dt 秒。

    前面（0 ~ dt）没有任何关键帧 ⇒ TaCZ 用第一帧的值填充 = 保持持枪姿态，不用额外补零帧。
    """
    return [(round(t + dt, 4), a, b) for t, a, b in seq]


def _bolt_keys(dt):
    """拉栓时**枪身**的关键帧：抬柄 → 退枪机 → 停 → 推回 → 压柄（空壳在退壳时出现）。

    时序完全跟 BOLT_T / BOLT_HAND_R 一致：手先到位，枪机跟着手的动作走。
    """
    g, l, b, h, f, c = (round(BOLT_T[k] + dt, 4) for k in
                        ('grab', 'lift', 'back', 'hold', 'fwd', 'close'))
    s = round(SHELL_POP_T + dt, 4)
    return {
        'bolt_rotate': {'rotation': _k([(0.0, [0, 0, 0]), (g, [0, 0, 0]),
                                        (l, [0, 0, BOLT_LIFT]),
                                        (f, [0, 0, BOLT_LIFT]),
                                        (c, [0, 0, 0])])},
        'bolt_group': {'position': _k([(0.0, [0, 0, 0]), (l, [0, 0, 0]),
                                       (b, [0, 0, BOLT_BACK]),
                                       (h, [0, 0, BOLT_BACK]),
                                       (f, [0, 0, 0])])},
        'bullet_shell': {'scale': _k([(0.0, [0, 0, 0]),
                                      (round(s - 0.01, 4), [0, 0, 0]),
                                      (s, [1, 1, 1]),
                                      (round(s + 0.16, 4), [1, 1, 1]),
                                      (round(s + 0.18, 4), [0, 0, 0])]),
                         'position': _k([(s, [0, 0, 0]),
                                         (round(s + 0.10, 4), [-5, 4, 2]),
                                         (round(s + 0.18, 4), [-9, 1, 5])]),
                         'rotation': _k([(s, [0, 0, 0]),
                                         (round(s + 0.18, 4), [220, -180, -120])])},
    }


# ★★★ 手部动作表（Δ 相对持枪姿态；时间单位是我们自己动画里的秒）
#
# 事实基础（2026-09-19 从官方 ai_awp 的动画 json 里量出来的）：
#   · 官方 `shoot` **完全不写手**；`bolt` / `reload_*` / `draw` / `put_away` / `inspect`
#     全都写手 —— 因为 TaCZ 的手是挂在 `righthand_pos` / `lefthand_pos` 上的固定尺寸
#     手臂模型，换弹、拉栓想让手真的动，只能靠这两根手骨。
#   · 官方 `bolt` 的右手：抬手 **y +4.9**、往前 **z -3.9**（够到拉机柄），翻腕 **+64~+76°**
#     （绕局部 X），然后跟着枪机退到 **z +1.2**；**左手全程不动**。
#   · 官方 `reload` 的左手：向弹匣下探 **z +6.7 / y -2.3**、手腕转 **+46°**，
#     接过新匣时加到 **+62°**，临末回到护木。
# 幅度按官方这组数取（同一套手模、同一坐标系 ⇒ 手真的能落在拉机柄 / 弹匣上），
# 时间按我们自己枪的弹匣、枪机事件重排。

# 右手：离开握把 → 向前上方够到拉机柄 → **向上翻腕**把柄抬起来 → 跟着枪机往后退
#       → 停一下 → 手腕转回来推回闭锁 → 松手回握把
# 数值照官方 ai_awp 的 bolt 右手（同一套手模、同一坐标系）：抬手 y+4.9、向前 z-3.9 够到柄，
# 翻腕 +95~+100°（绕局部 X；官方峰值才 +76，用户要「翻腕更明显」所以加到了近一倍），退壳时 z 回到 +0.6~+1.2（跟着枪机走），再推回去。
BOLT_HAND_R = [
    (0.00, (0.0, 0.0, 0.0), (0, 0, 0)),
    (0.08, (-0.8, 0.2, -0.1), (-3, -2, 2)),        # 手离开握把
    (0.16, (-1.7, 0.5, -1.7), (-8, -9, -15)),      # 往上、往枪机那边伸
    (0.20, (-2.0, 1.1, -2.6), (-3, -12, -21)),     # 手搭到拉机柄下部
    (0.28, (-2.4, 3.0, -3.4), (20, -13, -8)),     # 开始**向上翻腕**
    (0.38, (-2.6, 5.0, -3.9), (95, -13, 14)),      # ★ 一记赶腕翻到顶（柄被压下来）
    (0.46, (-2.6, 5.1, -3.5), (100, -13, 4)),      # 一小下回弹（看着有弹性）
    (0.56, (-2.6, 5.3, 0.6), (92, -13, -2)),       # 跟着枪机退到底（抽壳）
    (0.70, (-2.6, 5.4, 1.2), (92, -13, -2)),       # 退到底停一下
    (0.78, (-2.7, 4.6, 2.0), (54, -31, 18)),       # 手腕转回来、开始往前推
    (0.86, (-2.7, 3.0, -2.9), (1, -64, 67)),       # 推到位、松手
    (0.93, (-1.6, -0.5, -1.6), (7, -32, 7)),       # 手离开拉机柄
    (1.00, (0.0, 0.0, 0.0), (0, 0, 0)),            # 回到握把
]

# 打空换弹收尾的那一次拉栓：同样的动作整体后移 1.92s（对齐它的枪机时序）
RELOAD_EMPTY_HAND_R = _shift(BOLT_HAND_R, 1.92)

# 左手（战术换弹）：下探抓旧匣 → 抽掉 → 在下面接新匣 → 推上弹匣井 → 回护木
RELOAD_HAND_L = [
    (0.00, (0.0, 0.0, 0.0), (0, 0, 0)),
    (0.10, (-0.7, -2.0, 2.9), (-3, -2, 12)),
    (0.20, (-1.3, -2.3, 6.7), (-11, -5, 46)),      # 手到弹匣下方
    (0.50, (-1.3, -2.3, 6.7), (-11, -5, 46)),      # 抽旧匣（0.45 匣掉出去）
    (0.80, (-1.6, -2.2, 6.2), (-13, -4, 52)),      # 在下面换新匣（这段旧匣被藏起来）
    (1.15, (-1.7, -2.1, 5.9), (-17, 4, 62)),       # 举着新匣往上送
    (1.45, (-1.3, -2.3, 3.5), (-14, 0, 40)),       # 把匣推进弹匣井
    (1.75, (-0.6, -1.0, 1.4), (-6, 0, 16)),        # 手回护木
    (2.20, (0.0, 0.0, 0.0), (0, 0, 0)),
]

# 左手（打空换弹）：先换匣，最后再把枪机推一次
RELOAD_EMPTY_HAND_L = [
    (0.00, (0.0, 0.0, 0.0), (0, 0, 0)),
    (0.12, (-0.7, -2.0, 2.9), (-3, -2, 12)),
    (0.25, (-1.3, -2.3, 6.7), (-11, -5, 46)),
    (0.60, (-1.3, -2.3, 6.7), (-11, -5, 46)),
    (0.95, (1.5, -5.0, 9.0), (-13, -10, 60)),      # 空匣抽出来往下带
    (1.30, (-1.7, -2.1, 5.9), (-17, 4, 62)),
    (1.60, (-1.3, -2.3, 3.5), (-14, 0, 40)),
    (1.85, (-0.5, -0.8, 1.2), (-5, 0, 14)),
    (2.05, (0.0, 0.0, 0.0), (0, 0, 0)),
    (3.30, (0.0, 0.0, 0.0), (0, 0, 0)),
]

# 右手（打空换弹收尾）：换完匣再拉一次栓（= BOLT_HAND_R 整体后移，见文件后半的 _shift）

# 左手（出枪）：枪从画面下方抬起来时手才搭上护木
DRAW_HAND_L = [
    (0.00, (-1.4, 6.0, 5.0), (-15, -11, 11)),      # 手还在下面
    (0.08, (-1.4, 6.6, 9.6), (-27, -36, 14)),
    (0.17, (-1.1, 5.1, 8.2), (-22, -32, 11)),
    (0.25, (-0.4, 1.9, 3.2), (-9, -13, 4)),
    (0.35, (0.0, 0.0, 0.0), (0, 0, 0)),
    (0.50, (0.0, 0.0, 0.0), (0, 0, 0)),
]

# 右手（收枪）：手随枪往下放开（放完保持末帧，所以不用回握把）
PUT_AWAY_HAND_R = [
    (0.00, (0.0, 0.0, 0.0), (0, 0, 0)),
    (0.19, (-1.3, 1.9, 2.1), (0, -13, 42)),
    (0.31, (1.4, 4.7, 1.0), (1, -21, 68)),
    (0.44, (4.7, 2.5, -9.1), (6, -47, 164)),
    (0.56, (4.1, 2.8, -11.8), (33, -21, 132)),
    (0.75, (3.9, 3.0, -12.3), (32, -22, 130)),
]

PUT_AWAY_HAND_L = [
    (0.00, (0.0, 0.0, 0.0), (0, 0, 0)),
    (0.09, (0.0, -0.4, 1.0), (0, 0, 0)),
    (0.18, (0.0, -0.5, 2.1), (0, 0, 0)),
    (0.75, (0.0, -0.4, 2.6), (0, 0, 0)),
]

# 右手（检视）：跟着枪翻过来看一下枪身
INSPECT_HAND_R = [
    (0.00, (0.0, 0.0, 0.0), (0, 0, 0)),
    (0.35, (-1.3, 0.0, 0.0), (0, -14, -2)),        # 手腕松一下
    (0.90, (-1.3, 0.0, 0.0), (0, -14, -2)),
    (1.30, (-3.5, 3.0, -3.0), (-4, 6, -60)),
    (1.90, (-3.5, 3.2, -3.2), (-4, 6, -62)),
    (2.30, (-1.0, 0.5, -1.0), (-2, 0, -18)),
    (2.50, (0.0, 0.0, 0.0), (0, 0, 0)),
]


def _hands():
    """两只手的**持枪姿态**（相对枪身的静止位置）—— 写在 STATIC 轨（static_idle / static_bolt_caught）里。

    数值来自官方 ai_awp 的 `static_idle`（照抄）：这是 TaCZ 那套手模型握住这把枪的姿势。

    ★★ 注意「持枪姿态」和「手的动作」是两回事（2026-09-19 两轮实测才分清）：

      * **持枪姿态**（本函数）：手握着枪不动时的位置 —— 放 STATIC 轨，全程都在跑。
        没被动作动画 key 到的手骨，就继续保持这个姿态（官方 ai_awp 的 `shoot`
        完全不写手，开枪时手也不会飞，就是因为 STATIC 轨一直在供这个姿态）。
      * **手的动作**（下面的 `*_HAND_*` 表）：换弹去抓弹匣、拉栓去抓拉机柄 ——
        必须写在**主轨道的动作动画**里，因为 TaCZ 的手是挂在
        `righthand_pos` / `lefthand_pos` 上的固定尺寸手臂模型，
        不写这两根手骨，手就会一直贴在枪上不动（用户反馈的「换弹、拉栓没有正确的动画」）。
      * 唯一不能写手的是 `shoot`：它跑在开火轨道行（GUN_KICK）上、是**叠加**的，
        写手会把同一份位移叠两次 ⇒ 两双手从枪身向两侧分开（用户实测）。
    """
    return {
        'righthand': {'rotation': list(ROT_HAND_R), 'position': list(POS_HAND_R),
                      'scale': list(SCALE_HAND)},
        'lefthand': {'rotation': list(ROT_HAND_L), 'position': list(POS_HAND_L),
                     'scale': list(SCALE_HAND)},
    }


def _anim(length, bones, loop=False):
    a = {'bones': bones}
    if loop:
        a['loop'] = True
    if length:
        a['animation_length'] = length
    return a


SHELL_HIDDEN = {'scale': [0, 0, 0]}      # 平时把膛里的空壳藏起来


def animation_json():
    A = {}

    # ① static_idle —— 静止持枪姿态（循环）＝ STATIC 轨道的地基
    A['static_idle'] = _anim(None, dict(_hands(),
                                        root={'rotation': [0, 0, 0], 'position': [0, 0, 0]},
                                        bullet_shell=dict(SHELL_HIDDEN)), loop=True)

    # ② static_bolt_caught —— 枪机挂机时的静止姿态（同样是循环）
    A['static_bolt_caught'] = _anim(None, dict(_hands(),
                                               root={'rotation': [0, 0, 0], 'position': [0, 0, 0]},
                                               bullet_shell=dict(SHELL_HIDDEN)), loop=True)

    # ③ shoot —— 开火后座（枪口上抬 + 向射手方向后座，随后自己滑回去）
    #    ★ 官方 ai_awp 的 shoot 也**不写手**：手由 static 轨继续驱动 ⇒ 开枪时手纹丝不动
    A['shoot'] = _anim(0.35, dict(bullet_shell=dict(SHELL_HIDDEN), **{
        'root': {'rotation': _k([(0.0, [0, 0, 0]),
                                 (0.04, [RECOIL_PITCH, 0, 0]),
                                 (0.30, [0, 0, 0])]),
                 'position': _k([(0.0, [0, 0, 0]),
                                 (0.04, [0, 0, RECOIL_BACK]),
                                 (0.30, [0, 0, 0])])},
        'camera': {'rotation': _k([(0.0, [0, 0, 0]),
                                   (0.04, [RECOIL_PITCH * 0.35, 0, 0]),
                                   (0.30, [0, 0, 0])])},
        'constraint': {'position': _k([(0.0, [0, 0, 0]),
                                       (0.04, [0, 0, 0.6]),
                                       (0.30, [0, 0, 0])])},
    }))

    # ④ bolt —— 拉栓：右手抬起抓住拉机柄 → **向上翻腕**把柄抬起来 → 跟着枪机往后退（抽壳）
    #            → 停一下 → 推回闭锁 → 压柄、手回握把
    #    ★ 时间线按**手的动作**排（BOLT_T / BOLT_HAND_R，由 _bolt_keys 生成枪身那一半）：
    #      手先到位（0.20）→ 翻腕抬柄（0.26~0.38）→ 退枪机（0.38~0.56）→ 停（~0.70）
    #      → 推回（0.70~0.86）→ 压柄（0.86~0.96）；空壳 0.56 出现，与状态机参数对齐。
    A['bolt'] = _anim(1.0, dict(_bolt_keys(0.0), **{
        'righthand': _hand(ROT_HAND_R, POS_HAND_R, BOLT_HAND_R),
        'root': {'rotation': _k([(0.0, [0, 0, 0]), (0.38, [0, 0, 3]),
                                 (0.76, [0, 0, 3]), (0.94, [0, 0, 0])]),
                 'position': _k([(0.0, [0, 0, 0]), (0.38, [0, 0, 1.6]),
                                 (0.76, [0, 0, 1.6]), (0.94, [0, 0, 0])])},
    }))

    # ⑤⑥ 换弹：弹匣脱出 → 藏起来 → 新匣升上来 → 卡进弹匣井
    def _reload_mag(t0, t1, t2, t3, t4):
        return {
            'magazine': {
                'position': _k([(t0, [0, 0, 0]),
                                (t1, [0, -MAG_DROP, 0]),
                                (t3, [0, -MAG_DROP, 0]),
                                (t4, [0, 0, 0])]),
                'rotation': _k([(t0, [0, 0, 0]),
                                (t1, [MAG_TILT, 0, 0]),
                                (t3, [MAG_TILT, 0, 0]),
                                (t4, [0, 0, 0])]),
                'scale': _k([(t0, [1, 1, 1]),
                             (t1, [1, 1, 1]),
                             (t1 + 0.06, [0, 0, 0]),
                             (t2, [0, 0, 0]),
                             (t2 + 0.06, [1, 1, 1])]),
            },
        }

    # 换弹时整枪的姿势：向外侧倒 + 枪口略低（照官方 ai_awp 的 reload，见 RELOAD_TILT）
    tilt = {'root': {'rotation': _k([(0.0, [0, 0, 0]),
                                     (0.25, list(RELOAD_TILT)),
                                     (1.80, list(RELOAD_TILT)),
                                     (2.20, [0, 0, 0])]),
                     'position': _k([(0.0, [0, 0, 0]),
                                     (0.25, [0, -2, 1.5]),
                                     (1.80, [0, -2, 1.5]),
                                     (2.20, [0, 0, 0])])}}

    #    ★ 左手下探抓弹匣（时间点跟弹匣脱出 / 新匣升上来的事件对齐）
    A['reload_tactical'] = _anim(2.2, dict(bullet_shell=dict(SHELL_HIDDEN),
                                           **{'lefthand': _hand(ROT_HAND_L, POS_HAND_L,
                                                               RELOAD_HAND_L)},
                                           **_reload_mag(0.15, 0.45, 0.90, 1.15, 1.45),
                                           **tilt))

    # 打完最后发（reload_empty）：左手换匣 + 右手最后再拉一次枪机
    A['reload_empty'] = _anim(3.3, {
        'lefthand': _hand(ROT_HAND_L, POS_HAND_L, RELOAD_EMPTY_HAND_L),
        'righthand': _hand(ROT_HAND_R, POS_HAND_R, RELOAD_EMPTY_HAND_R),
        **_reload_mag(0.15, 0.50, 1.20, 1.60, 1.95),
        'root': {'rotation': _k([(0.0, [0, 0, 0]),
                                 (0.35, list(RELOAD_TILT)),
                                 (2.60, list(RELOAD_TILT)),
                                 (3.10, [0, 0, 0])]),
                 'position': _k([(0.0, [0, 0, 0]),
                                 (0.35, [0, -2, 1.5]),
                                 (2.60, [0, -2, 1.5]),
                                 (3.10, [0, 0, 0])])},
        **_bolt_keys(1.92),
    })

    # ⑦⑧ 出枪 / 收枪（枪从画面下方抬起来 / 放下去）；出枪时左手才从下面搭上护木，
    #      收枪时右手随枪往下放开
    A['draw'] = _anim(0.50, dict(bullet_shell=dict(SHELL_HIDDEN),
                                 **{'lefthand': _hand(ROT_HAND_L, POS_HAND_L, DRAW_HAND_L)},
                                 **{
        'root': {'rotation': _k([(0.0, [28, 0, -8]), (0.35, [0, 0, 0])]),
                 'position': _k([(0.0, [0, -10, -3]), (0.35, [0, 0, 0])])},
    }))
    A['put_away'] = _anim(0.75, dict(bullet_shell=dict(SHELL_HIDDEN),
                                     **{'righthand': _hand(ROT_HAND_R, POS_HAND_R,
                                                           PUT_AWAY_HAND_R),
                                        'lefthand': _hand(ROT_HAND_L, POS_HAND_L,
                                                          PUT_AWAY_HAND_L)},
                                     **{
        'root': {'rotation': _k([(0.0, [0, 0, 0]), (0.60, [28, 0, -8])]),
                 'position': _k([(0.0, [0, 0, 0]), (0.60, [0, -10, -3])])},
    }))

    # ⑨⑩ 检视：把枪转过来看一眼（打空时顺带把枪机挂在后面）
    A['inspect'] = _anim(2.5, dict(bullet_shell=dict(SHELL_HIDDEN),
                                   **{'righthand': _hand(ROT_HAND_R, POS_HAND_R,
                                                         INSPECT_HAND_R)},
                                   **{
        'root': {'rotation': _k([(0.0, [0, 0, 0]),
                                 (0.50, [0, 0, 40]),
                                 (1.00, [0, 30, 40]),
                                 (1.70, [0, 30, 40]),
                                 (2.20, [0, 0, 40]),
                                 (2.50, [0, 0, 0])]),
                 'position': _k([(0.0, [0, 0, 0]),
                                 (0.50, [0, -2, 0]),
                                 (2.20, [0, -2, 0]),
                                 (2.50, [0, 0, 0])])},
    }))
    A['inspect_empty'] = _anim(2.5, dict(A['inspect']['bones'], **{
        'bolt_rotate': {'rotation': _k([(0.0, [0, 0, 0]), (0.30, [0, 0, BOLT_LIFT]),
                                        (2.20, [0, 0, BOLT_LIFT]), (2.50, [0, 0, 0])])},
        'bolt_group': {'position': _k([(0.0, [0, 0, 0]), (0.30, [0, 0, BOLT_BACK]),
                                       (2.20, [0, 0, BOLT_BACK]), (2.50, [0, 0, 0])])},
    }))

    return {'format_version': '1.8.0', 'animations': A}


def lang(zh):
    if zh:
        return {
            'hexalunar.gun.awp.name': 'AWP 栓动狙击枪',
            'hexalunar.gun.awp.desc': '六相月灾 · .338 栓动狙击枪，8 倍镜，单发 24 点伤害',
            'hexalunar.gun_pack.name': '六相月灾枪包',
        }
    return {
        'hexalunar.gun.awp.name': 'AWP Bolt-Action Sniper Rifle',
        'hexalunar.gun.awp.desc': 'HexaLunar Calamity .338 bolt-action sniper, 8x scope, 24 dmg',
        'hexalunar.gun_pack.name': 'HexaLunar Gun Pack',
    }


def write(rel, obj_or_bytes):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(obj_or_bytes, (bytes, bytearray)):
        with open(p, 'wb') as f:
            f.write(obj_or_bytes)
    else:
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(obj_or_bytes, f, ensure_ascii=False, indent=2)
            f.write('\n')
    return p


def copy_asset(src_rel, dst_rel):
    s = os.path.join(SRC, src_rel)
    if not os.path.exists(s):
        print('  ! 缺文件 %s' % src_rel)
        return False
    with open(s, 'rb') as f:
        write(dst_rel, f.read())
    return True


# ── 自检 ─────────────────────────────────────────────────────────────────────
REQUIRED = ['root', 'righthand_pos', 'lefthand_pos', 'muzzle_flash', 'shell',
            'magazine', 'mag_standard', 'bullet_in_mag', 'bullet_in_barrel',
            'iron_view', 'idle_view', 'ground', 'fixed', 'thirdperson_hand',
            'camera', 'constraint']


def self_check(geo, anim):
    fails = []
    bones = {b['name']: b for b in geo['minecraft:geometry'][0]['bones']}
    for n in REQUIRED:
        if n not in bones:
            fails.append('缺硬性组名: ' + n)
    # parent 必须存在
    for n, b in bones.items():
        p = b.get('parent')
        if p and p not in bones:
            fails.append('%s 的 parent %s 不存在' % (n, p))
    # ★ 手部骨架必须与官方 ai_awp 一致（含容器 pivot）——
    #   `*_pos` 与各自父级 pivot 相同、两把手的 pivot 不同，全靠父链分开。
    want = {'gun_and_righthand': P_GH_R, 'righthand': P_RH, 'righthand_pos': P_RHP,
            'mag_and_lefthand': P_GL, 'lefthand': P_LH, 'lefthand_pos': P_LHP}
    for n, pv in want.items():
        if n in bones and bones[n]['pivot'] != pv:
            fails.append('手部骨骼 %s pivot=%s，应为官方的 %s' % (n, bones[n]['pivot'], pv))
    # 枪身/弹匣绝不能被放在手部容器里（否则改容器 pivot 会平移模型）
    if bones.get('awp_body', {}).get('parent') in ('gun_and_righthand', 'righthand'):
        fails.append('awp_body 挂在手部容器下了，会被平移')
    if bones.get('magazine', {}).get('parent') in ('mag_and_lefthand', 'lefthand'):
        fails.append('magazine 挂在手部容器下了，会被平移')
    # 枪口必须在最前端
    mz = bones['muzzle_flash']['pivot'][2]
    zmin = min(c['origin'][2] for b in bones.values() for c in b['cubes'])
    if mz > zmin + 0.5:
        fails.append('muzzle_flash z=%.3f 不在模型最前端(zmin=%.3f)' % (mz, zmin))
    # 抛壳口必须在射手右侧：★ TaCZ 空间里**右侧是 −X**（见上方 MIRROR_X 那段）
    sh = bones['shell']['pivot']
    if sh[0] > 0.05:
        fails.append('shell 在 TaCZ 的左侧（x=%.3f，TaCZ 里右侧是 −X）' % sh[0])
    # ★ 倍镜装配点与自带镜子的隐藏名（装了配件要能自动藏起自带镜子）
    for n in ('scope_pos', 'scope_default'):
        if n not in bones:
            fails.append('缺 %s：TaCZ 找不到%s（前者是倍镜挂点、后者是自带镜子的隐藏名）'
                         % (n, '装配点' if n == 'scope_pos' else '自带镜子'))
    # ★ 眼球绝不能落在**任何一个方块里面**（实测踩过：相机插进枪身 ⇒ 第一人称整屏全黑）
    for nm in ('iron_view', 'idle_view', 'camera'):
        e = bones[nm]['pivot']
        for bn, bd in bones.items():
            for c in bd['cubes']:
                lo = [min(c['origin'][i], c['origin'][i] + c['size'][i]) for i in range(3)]
                hi = [max(c['origin'][i], c['origin'][i] + c['size'][i]) for i in range(3)]
                if all(lo[i] <= e[i] <= hi[i] for i in range(3)):
                    fails.append('%s 的眼球 %s 落在 %s 的方块里（第一人称会整屏全黑）'
                                 % (nm, e, bn))
                    break
    # ★ 坐标变换必须真的生效：枪口要落在官方 ai_awp 的枪口位置（z ≈ −33.2）
    mfz = bones['muzzle_flash']['pivot'][2]
    if abs(mfz + 33.225) > 0.6:
        fails.append('muzzle_flash z=%.2f 没落在官方枪口 −33.2（搬进官方坐标空间的变换没生效）' % mfz)
    anims = anim.get('animations', {})
    # TaCZ 认的动画名（GunAnimationConstant + 官方 ai_awp 交叉核对）——
    # 少一段就表现为「那件事在游戏里没动作」，所以一条都不能少。
    need = ['static_idle', 'static_bolt_caught', 'draw', 'put_away', 'shoot',
            'bolt', 'reload_tactical', 'reload_empty', 'inspect', 'inspect_empty']
    for n in need:
        if n not in anims:
            fails.append('动画里缺 %s（表现就是「换弹 / 拉栓 没动画」）' % n)
    sb = anims.get('static_idle', {}).get('bones', {})
    for h in ('righthand', 'lefthand'):
        if h not in sb or 'rotation' not in sb[h] or 'position' not in sb[h]:
            fails.append('static_idle 里 %s 缺 rotation/position（手会竖着、不在枪上）' % h)
    # ★★ 手骨：TaCZ 的手就是挂在 righthand_pos / lefthand_pos 上的固定尺寸手臂模型
    #    ⇒ 换弹 / 拉栓想让手真的动，**必须在主轨道的动作动画里写这两根手骨**
    #    （官方 ai_awp 的 bolt / reload_* / draw / put_away / inspect 都写了）。
    #    唯一不能写手的是 shoot：它跑在开火轨道行（GUN_KICK）上、是叠加的，
    #    写手会把持枪姿态叠两份 ⇒ 双手从枪身向两侧飞出去。
    want_hands = {
        'bolt': ('righthand',),
        'reload_tactical': ('lefthand',),
        'reload_empty': ('righthand', 'lefthand'),
        'draw': ('lefthand',),
        'put_away': ('righthand', 'lefthand'),
        'inspect': ('righthand',),
        'inspect_empty': ('righthand',),
    }
    for n, hands in want_hands.items():
        b = anims.get(n, {}).get('bones', {})
        for h in hands:
            node = b.get(h)
            if not node or 'rotation' not in node or 'position' not in node:
                fails.append('%s 没写 %s 的动作（TaCZ 的手挂在手骨上，不写就是「手一动不动贴在枪上」）'
                             % (n, h))
                continue
            if len(node['position']) < 4:
                fails.append('%s 的 %s 只有 %d 个关键帧（手不会真的动）'
                             % (n, h, len(node['position'])))
    for h in ('righthand', 'lefthand'):
        if h in anims.get('shoot', {}).get('bones', {}):
            fails.append('shoot 里写了 %s —— 开火轨道是叠加的，手会从枪身向两侧分开' % h)

    # 手放完动作必须能回到持枪姿态（否则动作一结束手就留在半空中）
    # put_away 例外：它是「放到一半就收进背包」，末帧故意留在放开的位置
    for n, h, which in (('bolt', 'righthand', 'last'),
                        ('reload_tactical', 'lefthand', 'last'),
                        ('reload_empty', 'lefthand', 'last'),
                        ('reload_empty', 'righthand', 'last'),
                        ('inspect', 'righthand', 'last'),
                        ('draw', 'lefthand', 'last'),
                        ('put_away', 'righthand', 'first'),
                        ('put_away', 'lefthand', 'first')):
        node = anims.get(n, {}).get('bones', {}).get(h)
        if not node or 'position' not in node:
            continue
        ks = sorted(node['position'], key=float)
        got = node['position'][ks[-1] if which == 'last' else ks[0]]
        base = POS_HAND_R if h == 'righthand' else POS_HAND_L
        if any(abs(got[i] - base[i]) > 0.05 for i in range(3)):
            fails.append('%s 的 %s %s帧没回到持枪姿态（动作结束手会留在空中）'
                         % (n, h, '末' if which == 'last' else '首'))
    # static 轨的两段必须都带手（没被动作动画 key 到的手骨就靠它们保持持枪姿态）
    for n in ('static_idle', 'static_bolt_caught'):
        for h in ('righthand', 'lefthand'):
            if h not in anims.get(n, {}).get('bones', {}):
                fails.append('static 轨的 %s 没带 %s 的持枪姿态（手会竖起来、不在枪上）' % (n, h))
    # ★ 拉栓必须真的驱动枪机，否则「拉栓」只剩后座、看不出在拉
    blt = anims.get('bolt', {}).get('bones', {})
    for b in ('bolt_rotate', 'bolt_group'):
        if b not in blt:
            fails.append('bolt 动画没驱动 %s（拉栓看不见）' % b)
    # ★★ 拉栓的手必须真的做出「抬起 → 向上翻腕 → 跟着枪机后退 → 推回」这四个动作：
    #    光有手骨关键帧不够，得量幅度（用户要求的表现就是这四步）
    br = blt.get('righthand')
    if br:
        dy = max(v[1] - POS_HAND_R[1] for v in br['position'].values())
        dz_back = max(v[2] - POS_HAND_R[2] for v in br['position'].values())
        dz_fwd = min(v[2] - POS_HAND_R[2] for v in br['position'].values())
        drx = max(v[0] - ROT_HAND_R[0] for v in br['rotation'].values())
        if dy < 4.0:
            fails.append('bolt 的右手没抬起来（最大抬升 %.2f，应 ≥ 4）' % dy)
        if drx < 80.0:
            fails.append('bolt 的右手没向上翻腕（最大翻腕 %.1f°，应 ≥ 80；用户要求翻腕要明显）' % drx)
        if dz_fwd > -2.0:
            fails.append('bolt 的右手没先往前够到拉机柄（最小 z 偏移 %.2f，应 ≤ -2）' % dz_fwd)
        if dz_back < 0.4:
            fails.append('bolt 的右手没跟着枪机往后退（最大后移 %.2f，应 ≥ 0.4）' % dz_back)
    # ★ 空壳出现的时刻必须与状态机参数一致（状态机到点会抛一颗世界空间的壳）
    shsc = blt.get('bullet_shell', {}).get('scale')
    if isinstance(shsc, dict) and _t(SHELL_POP_T) not in shsc:
        fails.append('bolt 的空壳不是在 %ss 出现（状态机 bolt_shell_ejecting_time=%s 会对不上）'
                     % (SHELL_POP_T, SHELL_POP_T))
    # ★ iron_zoom 只是机瞷放大，官方没有一把枪超过 2；写大了就是「没有正常打开倍镜」
    if IRON_ZOOM > 2.5:
        fails.append('iron_zoom=%s 太大（官方最高 2）：TaCZ 的倍镜是配件提供的，'
                     '机瞷放大配不出镜筒与分划视野' % IRON_ZOOM)
    # 所有被 cube 引用的贴图尺寸必须与描述一致
    return fails


# 资源引用 -> 实际文件（用来验证 display/index 里写的路径真能对上）
def ref_files():
    a = 'assets/%s' % NS
    d = 'data/%s' % NS
    return [
        ('%s:%s_display' % (NS, GUN), '%s/display/guns/%s_display.json' % (a, GUN)),
        ('%s:%s_data' % (NS, GUN), '%s/data/guns/%s_data.json' % (d, GUN)),
        ('%s:gun/%s_geo' % (NS, GUN), '%s/geo_models/gun/%s_geo.json' % (a, GUN)),
        ('%s:gun/uv/%s' % (NS, GUN), '%s/textures/gun/uv/%s.png' % (a, GUN)),
        ('%s:gun/slot/%s' % (NS, GUN), '%s/textures/gun/slot/%s.png' % (a, GUN)),
        ('%s:gun/hud/%s' % (NS, GUN), '%s/textures/gun/hud/%s.png' % (a, GUN)),
        ('%s:%s' % (NS, GUN), '%s/animations/%s.animation.json' % (a, GUN)),
        ('可装配件标签', '%s/tacz_tags/attachments/allow_attachments/%s.json' % (d, GUN)),
        ('%s:%s/%s_shoot' % (NS, GUN, GUN),
         '%s/tacz_sounds/%s/%s_shoot.ogg' % (a, GUN, GUN)),
        ('%s:%s/%s_reload_empty' % (NS, GUN, GUN),
         '%s/tacz_sounds/%s/%s_reload_empty.ogg' % (a, GUN, GUN)),
        ('%s:%s/%s_reload_tactical' % (NS, GUN, GUN),
         '%s/tacz_sounds/%s/%s_reload_tactical.ogg' % (a, GUN, GUN)),
        ('%s:%s/%s_bolt' % (NS, GUN, GUN),
         '%s/tacz_sounds/%s/%s_bolt.ogg' % (a, GUN, GUN)),
    ]


def main():
    deploy = '--deploy' in sys.argv
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)

    geo = build_geo()
    anim = animation_json()
    write('gunpack.meta.json', {'namespace': NS, 'dependencies': {'tacz': '[1.1.4,)'}})
    write('assets/%s/gunpack_info.json' % NS, pack_info_json())
    write('assets/%s/geo_models/gun/%s_geo.json' % (NS, GUN), geo)
    write('assets/%s/animations/%s.animation.json' % (NS, GUN), anim)
    write('assets/%s/display/guns/%s_display.json' % (NS, GUN), display_json())
    write('assets/%s/lang/zh_cn.json' % NS, lang(True))
    write('assets/%s/lang/en_us.json' % NS, lang(False))
    write('data/%s/index/guns/%s.json' % (NS, GUN), index_json())
    write('data/%s/data/guns/%s_data.json' % (NS, GUN), data_json())
    write('data/%s/recipes/gun/%s.json' % (NS, GUN), recipe_json())
    # 可装配件白名单：缺了它 TaCZ 的倍镜根本装不上（见 attachments_tag_json 的注释）
    write('data/%s/tacz_tags/attachments/allow_attachments/%s.json' % (NS, GUN),
          attachments_tag_json())

    # 贴图：模型贴图直接复用我们的 512² 逐面 UV 图
    copy_asset('textures/models/awp_geo.png',
               'assets/%s/textures/gun/uv/%s.png' % (NS, GUN))
    # 音效：改名进 tacz_sounds（TaCZ 不认原版 sounds/ 目录）
    for src, dst in (('sounds/weapon/awp_shot_1.ogg', '%s_shoot' % GUN),
                     ('sounds/weapon/awp_reload_1.ogg', '%s_reload_empty' % GUN),
                     ('sounds/weapon/awp_reload_1.ogg', '%s_reload_tactical' % GUN),
                     ('sounds/weapon/bolt_1.ogg', '%s_bolt' % GUN)):
        copy_asset(src, 'assets/%s/tacz_sounds/%s/%s.ogg' % (NS, GUN, dst))

    # 背包/快捷栏 2D 贴图：TaCZ 的物品栏用的是 2D 图标而不是模型，缺了就是紫黑格。
    try:
        import tacz_awp_icon
        tacz_awp_icon.main()
    except Exception as e:                                   # noqa: BLE001
        print('! 图标渲染失败（%s）—— 物品栏会显示成紫黑格' % e)

    # 枪包列表的图标：GunPackLoader.getModIcon 读的是枪包**根目录**的 icon.png
    icon_src = os.path.join(OUT, 'assets', NS, 'textures', 'gun', 'slot', '%s.png' % GUN)
    if os.path.exists(icon_src):
        with open(icon_src, 'rb') as f:
            write('icon.png', f.read())

    fails = self_check(geo, anim)
    # 资源引用 -> 文件必须真的存在
    for ref, rel in ref_files():
        if not os.path.exists(os.path.join(OUT, rel)):
            fails.append('display/index 引用了 %s，但 %s 不存在' % (ref, rel))
    bones = geo['minecraft:geometry'][0]['bones']
    ncube = sum(len(b['cubes']) for b in bones)
    print('\n骨骼 %d 个 / 方块 %d 个 / 动画 %s' % (
        len(bones), ncube, ','.join(anim.get('animations', {})) or '(无)'))
    print('硬性组名：%d/%d 齐全' % (sum(1 for n in REQUIRED if any(b['name'] == n for b in bones)),
                                   len(REQUIRED)))
    if fails:
        print('\n✗ 自检失败：')
        for f in fails:
            print('   -', f)
        return 1
    print('✓ 自检通过')

    if deploy:
        dst = os.path.join(DEPLOY, os.path.basename(OUT))
        os.makedirs(DEPLOY, exist_ok=True)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(OUT, dst)
        print('✓ 已部署到 %s' % dst)
    print('输出目录：%s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
