# -*- coding: utf-8 -*-
"""M1 加兰德（M1 Garand，**7.62x61**）—— 模型/贴图生成器

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
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
GEO_OUT = os.path.join(RES, 'geo', 'm1_garand.geo.json')
TEX_OUT = os.path.join(RES, 'textures', 'models', 'm1_garand_geo.png')
GLOW_OUT = os.path.join(RES, 'textures', 'models', 'm1_garand_geo_glowmask.png')

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
    # 机匣（发蓝钢）：加兰德机匣很长，从护木后端一直到托颈
    body.append(box(-0.60, 0.60, 1.55, 3.00, -3.10, 2.10, 'steel'))
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
    bolt = []
    bolt.append(box(-0.20, 0.20, 2.58, 2.98, -2.60, 0.60, 'steel'))      # 枪机本体（顶比机匣低 0.02）
    bolt.append(box(0.18, 0.46, 2.60, 2.95, -1.80, -0.90, 'scope'))      # 枪机右耳
    bolt.append(box(0.52, 0.78, 1.98, 2.42, -13.00, -2.40, 'steel_d'))   # 导气杆（沿枪管右侧）
    bolt.append(box(0.76, 1.12, 1.98, 2.72, -1.40, -0.70, 'steel_d'))    # 拉机柄（右手抓这里）
    B.append(bone('bolt', (0.0, 2.80, -1.60), 'body', bolt))

    # ---------------- clip_in：8 发漏夹（换弹时右手压进去的那一整个）
    # ★ 底面抬到 1.56（机匣底 1.55）——不与机匣共面
    clip = []
    clip.append(box(-0.36, 0.36, 1.56, 1.81, -1.55, -0.25, 'steel_d'))   # 漏夹本体（钢）
    clip.append(box(-0.30, 0.30, 1.81, 2.06, -1.50, -0.30, 'brass'))     # 夹里的 8 发（一排黄铜）
    B.append(bone('clip_in', (0.0, 1.81, -0.90), 'body', clip))

    # ---------------- casing：抛壳（空弹壳从机匣右侧飞出去）
    case = [box(0.30, 0.54, 2.78, 3.02, -1.40, -0.75, 'brass')]
    B.append(bone('casing', (0.42, 2.90, -1.05), 'body', case))

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
    os.makedirs(os.path.dirname(GEO_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    with io.open(GEO_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(geo, f, ensure_ascii=False, indent=1)
        f.write('\n')
    build_texture().save(TEX_OUT)
    build_glowmask().save(GLOW_OUT)

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
    print('geo  ->', os.path.normpath(GEO_OUT))
    print('tex  ->', os.path.normpath(TEX_OUT))
    print('glow ->', os.path.normpath(GLOW_OUT))
    for b in geo['minecraft:geometry'][0]['bones']:
        print('  %-10s parent=%-7s cubes=%d pivot=%s'
              % (b['name'], b.get('parent'), len(b['cubes']), b['pivot']))


if __name__ == '__main__':
    main()
