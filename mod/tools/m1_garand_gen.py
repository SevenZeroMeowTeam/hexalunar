# -*- coding: utf-8 -*-
"""⚠️ **已被 `tools/m1_garand_v2.py` 取代**（r111：空心圆管枪管 / 八棱觇孔 + 透明镜片十字线 /
可翻开的弹夹盖 / 8 发可见子弹的漏夹 / 12 骨骼 + 逐面 UV 512² 图集）。

留着只作历史参考 —— **别跑这个脚本**：它写的是同一组资源路径
（`geo/m1_garand.geo.json` / `textures/models/m1_garand_geo.png` / `animations/m1_garand.animation.json`），
跑一遍就会把新模型盖回去（而且它的贴图是 128² 分带贴图，与 Java 侧的新骨骼对不上）。

原始说明（r108 第一版）如下。

M1 加兰德（M1 Garand，**7.62x61**）—— 模型/贴图生成器

产出
----
1. ``assets/hexalunar_calamity/geo/m1_garand.geo.json``   bedrock 几何（Blockbench 里
   File -> Import -> Bedrock Model 可直接打开编辑；本目录另有 ``geo2bbmodel.py`` 可转 .bbmodel）
2. ``assets/hexalunar_calamity/textures/models/m1_garand_geo.png``  程序化贴图
   （胡桃木托 / 发蓝钢 / 灰绿磷化 / 黄铜弹壳与漏夹）
3. ``assets/hexalunar_calamity/textures/models/m1_garand_geo_glowmask.png``  自发光遮罩
   （只留 钢 / 磷化黑 / 黄铜 三条色带 ⇒ 供 ``GlossGlintLayer`` 的抛光流光层用）
4. 末尾打印骨骼表、包围盒与**关键模型点**（枪口 / 照门准星高度 / 抛壳口 / 握把 / 压弹点）
   —— 这些数要原样抄进 ``weapon/WeaponMount.java`` 与 ``client/M1GarandGeoModel.java``

坐标约定（与项目内其它枪一致）
------------------------------
* 原点 = 握把附近；**枪口 = -Z**、上 = +Y、+X = 右
* 1 单位 = 1 模型像素 = 1/16 格；本枪总长 ≈ 20.9 像素（枪口 z≈-13.6、托底 z≈+7.3）

骨骼名（**沿用 AWP / Kar98k 那一套**，好让动画与工具链能复用）
--------------------------------------------------------------
``root -> move -> body -> {barrel, handguard, bolt, casing, clip_in, magazine, trigger}``

* ``bolt``：枪机 + **右侧长拉机柄导气杆（op-rod）** —— 半自动，每发**自动**后退抛壳再复进
* ``clip_in``：**8 发漏夹（en-bloc clip）** —— 换弹时右手把它从机匣上方压进去，
  打空最后一发时整只漏夹弹出来（M1 的「叮」）
* ``handguard``：上下两片木护木（加兰德几乎整根枪管都包在木头里，这是它与 Kar98k 最大的外观差别）
* ``casing``：抛壳（空弹壳从机匣右侧飞出去）

动画想法（简单版）
------------------
idle：枪端在右手上，随呼吸极轻微起伏（由 ``WeaponPose`` 的 walk/breath 负责）；
击发：扳机后扣 11° + 枪口焰 → **枪机自动后退 2.4 像素**把空弹壳带出来抛向右上 → 复进闭锁；
换弹：右手抬起漏夹 → 压进机匣 → 枪机**释放一次**（拉一次栓即可）上膛 → 可继续连射。

用法
----
    python tools/m1_garand_gen.py          # 直接写进 resources
"""
import io
import json
import os
import sys
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
GEO_OUT = os.path.join(RES, 'geo', 'm1_garand.geo.json')
TEX_OUT = os.path.join(RES, 'textures', 'models', 'm1_garand_geo.png')
GLOW_OUT = os.path.join(RES, 'textures', 'models', 'm1_garand_geo_glowmask.png')
ANIM_OUT = os.path.join(RES, 'animations', 'm1_garand.animation.json')
BUILD = os.path.join(HERE, '..', 'build')                 # 给 geo2bbmodel / bbanim 用

# ------------------------------------------------------------------ 动画参数
BOLT_BACK = 2.40        # 导气杆/枪机后座量（与 M1GarandGeoModel.BOLT_BACK 一致）
CLIP_DROP = 2.25        # 漏夹抬升量（顶 2.06 → 4.31，机匣顶 3.00 之上看得见）
TRIGGER_PULL = 11.0     # 扣扳机角度（与 WeaponAnim / animation.awp.fire 一致）

TEX = 128
# 贴图色带（y 坐标从上往下分块，每块 10 像素高，32x10 便于平铺）
BANDS = {
    'wood':    (0,  (138, 88, 46)),      # 胡桃木托（比 Kar98k 略偏红）
    'wood_d':  (16, (104, 62, 30)),      # 木纹暗部 / 握把
    'steel':   (32, (104, 108, 110)),    # 发蓝钢（枪管 / 机匣）
    'steel_d': (48, (62, 66, 68)),       # 磷化深灰（护木箍 / 机件）
    'scope':   (64, (38, 40, 44)),       # 黑件（照门座 / 枪机）
    'lens':    (80, (60, 120, 150)),     # 本枪无镜片：保留色带与其它枪一致，不使用
    'brass':   (96, (188, 152, 68)),     # 黄铜（弹壳 / 漏夹里的子弹）
}
PAT = {k: (0, v[0], 32, 10) for k, v in BANDS.items()}     # 色带左端 32x10：整面取同一块纯色
GLOW_BANDS = ('steel', 'scope', 'brass')                   # 会反光的那几条带


def uv_for(name):
    """每面同一张色带（整块纯色，靠贴图分带）"""
    u, v, w, h = PAT[name]
    return {f: {'uv': [u, v], 'uv_size': [w, h]}
            for f in ('north', 'east', 'south', 'west', 'up', 'down')}


def box(x0, x1, y0, y1, z0, z1, tex):
    return {
        'origin': [round(min(x0, x1), 4), round(min(y0, y1), 4), round(min(z0, z1), 4)],
        'size': [round(abs(x1 - x0), 4), round(abs(y1 - y0), 4), round(abs(z1 - z0), 4)],
        'uv': uv_for(tex),
    }


def bone(name, pivot, parent, cubes=None):
    # ★ bedrock 的 parent 必须是字符串，根骨骼要**整个省略**这个键（写成 null 会让 GeckoLib 崩）
    b = {'name': name, 'pivot': [round(v, 4) for v in pivot], 'cubes': cubes or []}
    if parent:
        b['parent'] = parent
    return b


def build_bones():
    """M1 加兰德：整木托 + 上护木 + 右侧导气杆 + 8 发漏夹"""
    B = []

    # ---------------- body：机匣 + 枪托 + 扳机组 + 照门
    body = []
    # 枪托（胡桃木，从机匣后到托底；用两段近似下倾）
    body.append(box(-0.60, 0.60, 1.20, 2.85, 2.10, 4.20, 'wood'))        # 托颈（wrist）
    body.append(box(-0.66, 0.66, 0.55, 2.75, 4.20, 7.10, 'wood'))        # 枪托主体
    body.append(box(-0.66, 0.66, 0.60, 2.75, 7.08, 7.30, 'steel_d'))     # 托底钢板
    body.append(box(-0.56, 0.56, 0.40, 2.40, 2.06, 3.30, 'wood_d'))      # 握把（下缘）
    # ★★ 机匣：**空心** + 顶部漏夹口 + 右侧抛壳口
    #    加兰德是漏夹供弹：导气杆后座时从上面看得见 8 发漏夹；枪机复进就把口盖上
    #    （原来是整块实心钢 —— 枪机 / 漏夹 / 弹壳全被埋在里面，什么都看不见）
    body.append(box(-0.60, 0.60, 1.55, 1.95, -3.10, 2.10, 'steel'))       # 底
    body.append(box(-0.60, -0.24, 1.95, 3.00, -3.10, 2.10, 'steel'))      # 左壁（整高）
    body.append(box(0.24, 0.60, 1.95, 2.78, -3.10, 2.10, 'steel'))        # 右壁（下）
    body.append(box(0.24, 0.60, 2.78, 3.00, -3.10, -1.75, 'steel'))       # 右壁（上·前）
    body.append(box(0.24, 0.60, 2.78, 3.00, -0.45, 2.10, 'steel'))        # 右壁（上·后）
    body.append(box(-0.24, 0.24, 1.95, 3.00, -3.10, -1.90, 'steel'))      # 前节套（弹膛/枪管座）
    body.append(box(-0.24, 0.24, 1.95, 3.00, 1.10, 2.10, 'steel'))        # 后节套
    #   顶部口 = |x|<0.24、z −1.90…1.10；右侧抛壳口 = x0.24…0.60、y2.78…3.00、z −1.75…−0.45
    # 照门座 + 觇孔（后照门：M1 的标志性大觇孔）
    body.append(box(-0.40, 0.40, 2.95, 3.30, -0.62, 0.06, 'steel'))
    body.append(box(-0.24, 0.24, 3.02, 3.26, -0.84, -0.58, 'scope'))
    # 扳机护圈：做成「环」（前后立柱 + 底横梁）——中间能看见扳机，也贴近照片里的护圈
    # ★ 立柱比横梁窄 0.02：避免侧面共面 z-fighting（README 第 13 条）
    body.append(box(-0.11, 0.11, 0.70, 1.62, 1.90, 2.30, 'steel_d'))     # 前立柱
    body.append(box(-0.11, 0.11, 0.70, 1.62, 0.60, 0.95, 'steel_d'))     # 后立柱
    body.append(box(-0.13, 0.13, 0.70, 0.90, 0.60, 2.30, 'steel_d'))     # 底横梁
    # 背带环（托底下方）
    body.append(box(-0.10, 0.10, 0.30, 0.62, 5.60, 5.90, 'steel_d'))
    B.append(bone('body', (0.0, 1.80, 0.60), 'move', body))

    # ---------------- handguard：上下两片木护木 + 前后箍（加兰德几乎整根枪管包在木头里）
    # ★ 木护木往机匣里多伸 0.04（−3.06），前端伸进护木帽 0.06（−9.54）：两处方块都不共面
    hg = []
    hg.append(box(-0.50, 0.50, 2.35, 2.85, -9.54, -3.06, 'wood'))        # 上护木
    hg.append(box(-0.56, 0.56, 1.55, 2.45, -9.54, -3.06, 'wood'))        # 下护木（前托）
    hg.append(box(-0.54, 0.54, 1.60, 2.90, -9.95, -9.54, 'steel_d'))     # 前箍 / 护木帽
    hg.append(box(-0.58, 0.58, 1.50, 2.50, -7.45, -7.05, 'steel_d'))     # 下箍 + 背带环座
    B.append(bone('handguard', (0.0, 2.20, -9.54), 'body', hg))

    # ---------------- barrel：露出的枪管 + 导气箍 + 准星 + 通条
    bar = []
    bar.append(box(-0.24, 0.24, 2.06, 2.54, -13.60, -9.48, 'steel'))     # 外露枪管（轴线 y=2.30，尾端伸进护木）
    bar.append(box(-0.30, 0.30, 1.62, 2.10, -12.80, -11.20, 'steel_d'))  # 导气箍（顶 2.10 进枪管）
    bar.append(box(-0.14, 0.14, 2.50, 2.95, -13.35, -13.05, 'steel_d'))  # 准星座（底 2.50 进枪管）
    bar.append(box(-0.05, 0.05, 2.92, 3.10, -13.25, -13.12, 'steel_d'))  # 准星片（顶 = 3.10）
    bar.append(box(-0.28, 0.28, 1.40, 1.68, -12.60, -12.24, 'steel_d'))  # 枪口箍 / 通条
    B.append(bone('barrel', (0.0, 2.30, -9.54), 'body', bar))

    # ---------------- bolt：枪机 + 右侧长导气杆（op-rod）+ 拉机柄
    #    ★ 枪机本体加宽到 ±0.24（= 顶部口宽度）：复进到位时**正好把漏夹口盖上**
    bolt = []
    bolt.append(box(-0.24, 0.24, 2.58, 2.98, -2.60, 0.60, 'steel'))      # 枪机本体（盖住漏夹口）
    bolt.append(box(0.24, 0.46, 2.60, 2.95, -1.80, -0.90, 'scope'))      # 枪机右耳
    bolt.append(box(0.52, 0.78, 1.98, 2.42, -13.00, -2.40, 'steel_d'))   # 导气杆（沿枪管右侧）
    bolt.append(box(0.76, 1.12, 1.98, 2.72, -1.40, -0.70, 'steel_d'))    # 拉机柄（导气杆手柄）
    B.append(bone('bolt', (0.0, 2.80, -1.60), 'body', bolt))

    # ---------------- clip_in：8 发漏夹（换弹时右手压进去的那一整个）
    # ★ 收窄到 ±0.22（顶部口内宽 ±0.24）—— 不然漏夹比口宽，从上面根本看不见
    clip = []
    clip.append(box(-0.22, 0.22, 1.56, 1.84, -1.55, -0.25, 'steel_d'))   # 漏夹本体（钢）
    clip.append(box(-0.18, 0.18, 1.84, 2.06, -1.48, -0.32, 'brass'))     # 夹里的 8 发（一撮黄铜）
    B.append(bone('clip_in', (0.0, 1.81, -0.90), 'body', clip))

    # ---------------- casing：空弹壳（静止时藏在机匣**前节套里** = 看不见）
    #   ★ 别放在原来的 (0.30…0.54, 2.78…3.02) —— 机匣右上方现在开了抛壳口，那块会露出来
    case = [box(-0.12, 0.12, 2.72, 2.96, -2.45, -1.95, 'brass')]
    B.append(bone('casing', (0.0, 2.84, -2.20), 'body', case))

    # ---------------- magazine：弹仓底板（M1 是漏夹供弹，没有可拆弹匣 ⇒ 只画底板）
    mag = [box(-0.42, 0.42, 1.42, 1.66, -1.30, 0.70, 'steel_d')]
    B.append(bone('magazine', (0.0, 1.54, -0.30), 'body', mag))

    # ---------------- trigger：扳机（挂在机匣底面上，能透过护圈看见）
    trig = [box(-0.09, 0.09, 0.90, 1.58, 1.20, 1.45, 'steel')]
    B.append(bone('trigger', (0.0, 1.58, 1.32), 'body', trig))

    # ---------------- move / root
    B.append(bone('move', (0.0, 1.30, 1.60), 'root', []))
    B.append(bone('root', (0.0, 0.0, 0.0), None, []))
    return B


def build_geo():
    return {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.m1_garand',
                'texture_width': TEX,
                'texture_height': TEX,
                'visible_bounds_width': 6,
                'visible_bounds_height': 4,
                'visible_bounds_offset': [0, 1.5, 0],
            },
            'bones': build_bones(),
        }],
    }


# ==================================================================== 动画
def _kf(t, **kw):
    return (t, {k: tuple(float(x) for x in v) for k, v in kw.items()})


def _bedrock(bones):
    """[(t, {通道: 值})] → Bedrock/GeckoLib 的 {骨骼: {通道: {时刻: [x,y,z]}}}

    ★ 嵌套顺序不能写反（仓库里 awp/mosin 的动画文件就是这个顺序）：
      骨骼 → rotation|position|scale → 时间字符串 → 值
    """
    out = {}
    for name, kfs in bones.items():
        ch_out = {}
        for t, ch in kfs:
            key = ('%.4f' % t).rstrip('0').rstrip('.') or '0'
            for k, v in ch.items():
                ch_out.setdefault(k, {})[key] = [round(float(x), 4) for x in v]
        out[name] = ch_out
    return out


def _sway(name, length, amp, steps=4):
    """idle / run 用的轻微摆动（只动 move；游戏里 move 被 Java 归零，这几条是给 Blockbench 看的）"""
    kfs = []
    for i in range(steps + 1):
        t = length * i / steps
        kfs.append(_kf(t, position=(0.0, amp if i % 2 == 0 else -amp, 0.0),
                       rotation=(0.0, 0.0, 0.0)))
    return name, {'loop': True, 'animation_length': length,
                  'bones': _bedrock({'move': kfs})}


def build_anims():
    """★ 加兰德是**气动**半自动：没有任何「拉栓」动作。

    射击：扣扳机 → 导气杆把枪机顶开后退（{@link BOLT_BACK}）→ 空弹壳从**右侧抛壳口**翻出去
          → 复进簧把枪机推回去自动闭锁、顶上下一发 —— 全程玩家只扣扳机；
    换弹：右手把 8 发漏夹从**顶部漏夹口**压进去 → 枪机**自动**复进闭锁（不用拉栓）；
    打空：枪机停在后位（空仓挂机），最后一发的漏夹弹出来（M1 的「叮」）。
    """
    A = {}
    A.update([_sway('animation.m1_garand.idle', 2.6, 0.06, 4)])
    A.update([_sway('animation.m1_garand.run', 1.0, 0.16, 4)])
    A.update([_sway('animation.m1_garand.run_fast', 0.6, 0.24, 4)])

    mech = {                                   # 气动循环的「机械部分」（bolt / casing）
        'bolt': [_kf(0.00, position=(0, 0, 0)),
                 _kf(0.14, position=(0, 0, BOLT_BACK)),
                 _kf(0.22, position=(0, 0, BOLT_BACK)),
                 _kf(0.36, position=(0, 0, 0)),
                 _kf(0.50, position=(0, 0, 0))],
        # 空弹壳：被枪机从弹膛抽出来 → 到右侧抛壳口 → 翻着跟头飞出去 → 缩没
        'casing': [_kf(0.00, position=(0, 0, 0), rotation=(0, 0, 0), scale=(0, 0, 0)),
                   _kf(0.10, position=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)),
                   _kf(0.16, position=(0, 0, 1.35), rotation=(0, 0, 20), scale=(1, 1, 1)),
                   _kf(0.22, position=(0.75, 0.45, 1.35), rotation=(0, 0, 60), scale=(1, 1, 1)),
                   _kf(0.30, position=(1.55, 0.95, 1.30), rotation=(140, 150, 110)),
                   _kf(0.38, position=(2.35, 0.60, 1.20), rotation=(330, 280, 220)),
                   _kf(0.44, position=(2.75, 0.35, 1.20), rotation=(420, 340, 260),
                       scale=(0.6, 0.6, 0.6)),
                   _kf(0.50, position=(2.85, 0.25, 1.20), rotation=(440, 360, 280),
                       scale=(0, 0, 0))],
    }

    # ★ fire：扣扳机 + 气动循环（不含任何拉栓/拉机柄动作）
    fire_bones = dict(mech)
    fire_bones['trigger'] = [_kf(0.00, rotation=(0, 0, 0)),
                             _kf(0.05, rotation=(-TRIGGER_PULL, 0, 0)),
                             _kf(0.16, rotation=(0, 0, 0))]
    A['animation.m1_garand.fire'] = {'loop': False, 'animation_length': 0.50,
                                     'bones': _bedrock(fire_bones)}
    # bolt：只有机械循环（打空自动挂机那一下 / 单独查看用）
    A['animation.m1_garand.bolt'] = {'loop': False, 'animation_length': 0.50,
                                     'bones': _bedrock(mech)}

    # ★ reload：压漏夹 → 枪机**自动**释放复进闭锁（无需拉栓）
    A['animation.m1_garand.reload'] = {
        'loop': False, 'animation_length': 1.40, 'bones': _bedrock({
            'bolt': [_kf(0.00, position=(0, 0, BOLT_BACK)),      # 空仓挂机：枪机停在后位
                     _kf(0.62, position=(0, 0, BOLT_BACK)),
                     _kf(0.78, position=(0, 0, 0)),              # ★ 漏夹到位 → 枪机自己弹回来
                     _kf(0.82, position=(0, 0, 0.32)),           #   一点点回弹（撞到位的感觉）
                     _kf(0.88, position=(0, 0, 0)),
                     _kf(1.40, position=(0, 0, 0))],
            'clip_in': [_kf(0.00, position=(0, CLIP_DROP, 0)),   # 8 发漏夹在机匣上方
                        _kf(0.30, position=(0, CLIP_DROP, 0)),
                        _kf(0.62, position=(0, 0, 0)),           # 压到底（坐进机匣）
                        _kf(1.40, position=(0, 0, 0))],
        })}

    # ── 下面是「看得见的状态」用的两条附加动画（游戏里由 Java 程序化驱动，这里方便在
    #    Blockbench 里直接看姿态）
    # clip_eject：打空最后一发 → 空漏夹弹出来（M1 的「叮」）
    A['animation.m1_garand.clip_eject'] = {
        'loop': False, 'animation_length': 0.55, 'bones': _bedrock({
            'clip_in': [_kf(0.00, position=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)),
                        _kf(0.14, position=(0, 1.10, 0), rotation=(18, 0, 0), scale=(1, 1, 1)),
                        _kf(0.30, position=(0.35, 2.60, 0), rotation=(90, 25, 15)),
                        _kf(0.44, position=(0.70, 3.80, 0), rotation=(180, 45, 30),
                            scale=(0.5, 0.5, 0.5)),
                        _kf(0.55, position=(0.85, 4.60, 0), rotation=(220, 55, 35),
                            scale=(0, 0, 0))],
        })}
    # hold_open：打空后的样子（枪机停在后位、漏夹已经弹走）
    A['animation.m1_garand.hold_open'] = {
        'loop': 'hold_on_last_frame', 'animation_length': 0.30, 'bones': _bedrock({
            'bolt': [_kf(0.00, position=(0, 0, 0)),
                     _kf(0.16, position=(0, 0, BOLT_BACK)),
                     _kf(0.30, position=(0, 0, BOLT_BACK))],
            'clip_in': [_kf(0.00, position=(0, 0, 0), scale=(1, 1, 1)),
                        _kf(0.30, position=(0, 0, 0), scale=(0, 0, 0))],
        })}
    return {'format_version': '1.10.0', 'animations': A}


def _jitter(x, y, rgb):
    k = 1 + ((x * 7 + y * 13) % 5 - 2) * 0.02
    return tuple(min(255, int(c * k)) for c in rgb)


def build_texture():
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name, (y, rgb) in BANDS.items():
        for x in range(TEX):
            d.line([(x, y), (x, y + 9)], fill=_jitter(x, y, rgb) + (255,))
    d.rectangle([0, 0, TEX - 1, TEX - 1], outline=(0, 0, 0, 255))     # 一条黑描边，避免全图纯色
    return img


def build_glowmask():
    """自发光遮罩：只把 GLOW_BANDS 那几条色带涂上（alpha=255），其余全透明。"""
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name in GLOW_BANDS:
        y, rgb = BANDS[name]
        for x in range(TEX):
            d.line([(x, y), (x, y + 9)], fill=_jitter(x, y, rgb) + (255,))
    return img


def main():
    geo = build_geo()
    anims = build_anims()
    os.makedirs(os.path.dirname(GEO_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(ANIM_OUT), exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    with io.open(GEO_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(geo, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with io.open(ANIM_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(anims, f, ensure_ascii=False, indent=1)
        f.write('\n')
    build_texture().save(TEX_OUT)
    build_glowmask().save(GLOW_OUT)
    # build/ 下的副本：geo2bbmodel.py / bbanim.py / bbshot 都从 build/ 取
    with io.open(os.path.join(BUILD, 'm1_garand.geo.json'), 'w', encoding='utf-8',
                 newline='\n') as f:
        json.dump(geo, f, ensure_ascii=False, indent=1)
        f.write('\n')
    build_texture().save(os.path.join(BUILD, 'm1_garand.png'))
    with io.open(os.path.join(BUILD, 'm1_garand.animation.json'), 'w', encoding='utf-8',
                 newline='\n') as f:
        json.dump(anims, f, ensure_ascii=False, indent=1)
        f.write('\n')

    # 自检 + 打印包围盒与关键模型点（要抄进 WeaponMount / M1GarandGeoModel）
    xs, ys, zs, cubes = [], [], [], 0
    for b in geo['minecraft:geometry'][0]['bones']:
        for c in b['cubes']:
            cubes += 1
            o, s = c['origin'], c['size']
            xs += [o[0], o[0] + s[0]]
            ys += [o[1], o[1] + s[1]]
            zs += [o[2], o[2] + s[2]]
    print('bones = %d  cubes = %d' % (len(geo['minecraft:geometry'][0]['bones']), cubes))
    print('bbox  x[%.2f, %.2f]  y[%.2f, %.2f]  z[%.2f, %.2f]  (枪口 = -Z)'
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print('length = %.2f 像素 = %.3f 格' % (max(zs) - min(zs), (max(zs) - min(zs)) / 16.0))
    print()
    print('★ 关键模型点（抄进代码）：')
    print('  枪管轴线 Y      = 2.30   （枪管方块 y 2.06…2.54 的中心）')
    print('  枪口            = (0.00, 2.30, -13.60)      -> WeaponMount.M1_MUZZLE')
    print('  瞄准线 Y        = 3.10   （准星片顶 = 照门觇孔中心）-> WeaponMount.M1_IRON_Y')
    print('  抛壳口          = (0.42, 2.90, -1.05)       -> WeaponMount.M1_EJECT')
    print('  握把（右手）    = (0.00, 1.25, 1.70)        -> M1GarandGeoModel.ARM_GRIP')
    print('  前托（左手）    = (0.00, 1.40, -6.20)        -> M1GarandGeoModel.ARM_SUPPORT')
    print('  压漏夹（右手）  = (0.00, 4.06, -0.90) → 压到 1.81 -> ARM_CLIP / CLIP_DROP')
    print('  枪机后退量      = 2.40 像素（导气杆跟着走）')
    print('  漏夹抬升量      = 2.25 像素（漏夹顶 2.06 → 机匣顶 3.00 之上，看得见）')
    print()
    print('★ 机匣开口自检（这轮新加的「看得见」部分）：')
    bod = {b['name']: b for b in geo['minecraft:geometry'][0]['bones']}['body']['cubes']
    port = [c for c in bod
            if c['origin'][0] < 0.24 and c['origin'][0] + c['size'][0] > -0.24
            and c['origin'][2] < 1.10 and c['origin'][2] + c['size'][2] > -1.90
            and c['origin'][1] + c['size'][1] > 2.00]
    print('  顶部漏夹口上方的遮挡块 %d 个（应为 0）' % len(port))
    print('  顶部口 |x|<0.24、z −1.90…1.10；右侧抛壳口 x0.24…0.60、y2.78…3.00、z −1.75…−0.45')
    print('  枪机本体 x±0.24、z −2.60…0.60 ⇒ 复进到位时盖住 z −1.90…0.60（漏夹看不见）')
    print('  枪机后退 %.2f 后：z %.2f…%.2f ⇒ 完全让开漏夹口（看得见 8 发漏夹）'
          % (BOLT_BACK, -2.60 + BOLT_BACK, 0.60 + BOLT_BACK))
    print('  弹壳静止位藏在机匣前节套里（z −2.45…−1.95 ⊂ −3.10…−1.90）⇒ 看不见')
    print()
    print('★ 动画（%d 条，全部**没有**拉栓动作）：' % len(anims['animations']))
    for k, v in anims['animations'].items():
        print('  %-34s loop=%-18s %.2fs  bones=%s'
              % (k, v['loop'], v['animation_length'], ','.join(v['bones'])))
    print()
    print('geo  ->', os.path.normpath(GEO_OUT))
    print('tex  ->', os.path.normpath(TEX_OUT))
    print('glow ->', os.path.normpath(GLOW_OUT))
    print('anim ->', os.path.normpath(ANIM_OUT))
    print('copy -> build/m1_garand.{geo.json,png,animation.json}（给 geo2bbmodel / bbanim 用）')
    for b in geo['minecraft:geometry'][0]['bones']:
        print('  %-10s parent=%-7s cubes=%d pivot=%s'
              % (b['name'], b.get('parent'), len(b['cubes']), b['pivot']))


if __name__ == '__main__':
    main()
