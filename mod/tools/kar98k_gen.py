# -*- coding: utf-8 -*-
"""
Kar98k（独立新武器，保留原 AWP）—— 模型/贴图生成器
================================================================================

产出
----
1. ``assets/hexalunar_calamity/geo/kar98k.geo.json``   bedrock 几何（Blockbench 里
   File -> Import -> Bedrock Model 可直接打开编辑）
2. ``assets/hexalunar_calamity/textures/models/kar98k_geo.png``  程序化贴图（木/钢/镜/黄铜）
3. ``assets/hexalunar_calamity/textures/models/kar98k_geo_glowmask.png``  自发光遮罩
   （只留 钢/镜筒/镜片/黄铜 四条色带 ⇒ 供 ``GlossGlintLayer`` 的抛光流光层用）
4. 顺便打印骨骼清单与包围盒（供后续调 WeaponMount / WeaponArms 参照点用）

接线状态（r105 已完成，见下面「后续接线」的对应条目）
----------------------------------------------------
模型 → 代码的每一条线都接好了：``Kar98kItem`` / ``Kar98kGeoModel`` / ``Kar98kGeoRenderer`` /
``models/item/kar98k.json`` / ``WeaponMount.KAR98K_*`` / ``WeaponArms.renderKar98k`` /
``lang`` + 创造页签。本脚本改动后直接重跑即可（几何 + 两张贴图一起覆盖）。

坐标约定（与项目内其它枪一致）
------------------------------
* 原点 = 握把附近；**枪口 = -Z**、上 = +Y、+X = 右
* 1 单位 = 1 模型像素 = 1/16 格；本枪总长 ≈ 20 像素（枪口 z≈-13、枪托底 z≈+7）

骨骼名（**必须**与 ``awp.animation.json`` 一致，才能直接复用现有动画）
--------------------------------------------------------------------
``root -> move -> body -> {barrel, stock, scope, bolt, casing, round_in, magazine, trigger, bipod}``
动画里被 key 的通道：``move``（后坐/拉栓整枪位移）、``bolt``（拉机柄）、``casing``（抛壳）
★ ``round_in`` 是 r107 新增的第 11 根骨骼（压弹时那一发），由 ``Kar98kGeoModel`` **程序化**驱动
（``awp.animation.json`` 里没有它，所以不影响动画复用）。

接线清单（r105 已逐条接完，落地位置记在括号里）
----------------------------------------------
1. ``registry/ModItems``：``KAR98K`` → 新类 ``Kar98kItem``（``weapon/Kar98kItem.java``，与
   ``AwpRifleItem`` 同款栓动逻辑，弹种沿用 AWP 的 ``AmmoType.SNIPER`` = .338）
2. ``client``：``Kar98kGeoModel`` / ``Kar98kGeoRenderer`` / ``Kar98kAnimState`` /
   ``Kar98kItemClientExtensions``，由 ``Kar98kItem.initializeClient`` 注册 BEWLR；
   动画**直接复用** ``animations/awp.animation.json``（骨骼名一致）
3. ``models/item/kar98k.json``：``parent = builtin/entity`` + firstperson display
   （平移 −5.0 / −1.10 / 0.50，与 ``WeaponMount.KAR98K_T*`` 必须一致）
4. ``WeaponMount``：``KAR98K_MUZZLE`` {0, 2.25, −13.60}、``KAR98K_EJECT``、``KAR98K_SCOPE_Y``
   = 4.40（镜筒 y 中心 = scope 骨骼 pivot）、``kar98kAds`` / ``kar98k()`` 换算
5. ``WeaponArms.renderKar98k``：右手握把 / 拉栓抓下弯柄、左手托护木 / 换弹时压桥夹
   （手位点写在 ``Kar98kGeoModel`` 里，必须与骨骼几何对着量）
6. ``lang``（en_us/zh_cn 的 ``item/tooltip.hexalunar_calamity.kar98k*``）+ 创造页签
   ``ModTabs``；弹种沿用 AWP 的 .338
7. 4 倍镜：``Kar98kItem.SCOPE_ZOOM`` = 4.0 ⇒ 复用 AWP 的整屏镜筒开镜
   （``ClientEvents.scoping`` / ``maskScoping``）；枪模投影 FOV 见
   ``GunPose.MODEL_FOV_AIM_KAR98K``

用法
----
    python tools/kar98k_gen.py          # 直接写进 resources（几何 + 贴图 + 遮罩）
"""
import io
import json
import math
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
GEO_OUT = os.path.join(RES, 'geo', 'kar98k.geo.json')
TEX_OUT = os.path.join(RES, 'textures', 'models', 'kar98k_geo.png')
GLOW_OUT = os.path.join(RES, 'textures', 'models', 'kar98k_geo_glowmask.png')

TEX = 128
# 贴图色带（y 坐标从上往下分块，每块 10 像素高，正方形 32x32 便于平铺）
BANDS = {
    'wood':   (0,  (122, 82, 44)),
    'wood_d': (16, (96, 62, 32)),
    'steel':  (32, (86, 90, 96)),
    'steel_d': (48, (54, 57, 62)),
    'scope':  (64, (34, 36, 40)),
    'lens':   (80, (60, 120, 150)),
    'brass':  (96, (176, 142, 62)),
}
PAT = {k: (0, v[0], 32, 10) for k, v in BANDS.items()}     # 色带左端 32x10：整面取同一块纯色


def uv_for(name):
    """每面同一张色带（和 crossbow_vox.py 的做法一致：整块纯色，靠贴图分带）"""
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
    # ★ 注意：bedrock 的 parent 必须是**字符串**，根骨骼要**整个省略**这个键。
    #   写成 "parent": null 会让 GeckoLib 报 "parent to be a string, was null" 并崩客户端
    #   （r105 修：之前 kar98k.geo.json 就是这么崩的）。
    b = {'name': name, 'pivot': [round(v, 4) for v in pivot], 'cubes': cubes or []}
    if parent:
        b['parent'] = parent
    return b


def build_bones():
    """Kar98k：木托长枪 + 拉栓 + 自带 4 倍镜筒"""
    B = []

    # ---------------- body：机匣 + 木托 + 护木（整枪主体）
    body = []
    # 机匣（钢）：z -2.4 .. 1.2，高 y 1.5..3.0
    body.append(box(-0.62, 0.62, 1.50, 3.00, -2.40, 1.20, 'steel'))
    # 机匣顶部的桥夹槽/表尺座（钢，略窄）
    body.append(box(-0.42, 0.42, 3.00, 3.42, -1.20, 0.90, 'steel_d'))
    # 木托：从机匣后到枪托底（z 1.2 .. 7.2），向下倾斜（用两段近似）
    body.append(box(-0.66, 0.66, 1.20, 2.90, 1.20, 4.20, 'wood'))
    body.append(box(-0.72, 0.72, 0.60, 2.60, 4.20, 7.20, 'wood'))      # 枪托（更粗更靠下）
    body.append(box(-0.72, 0.72, 0.72, 1.30, 6.60, 7.20, 'steel_d'))   # 托底钢板
    # 握把（木，向下）
    body.append(box(-0.52, 0.52, -0.10, 1.30, 1.30, 2.60, 'wood_d'))
    # 护木（木，机匣前方，包住枪管下半）
    body.append(box(-0.58, 0.58, 1.30, 2.45, -8.60, -2.40, 'wood'))
    body.append(box(-0.44, 0.44, 2.45, 2.80, -8.60, -2.40, 'wood_d'))  # 护木上沿
    # 弹仓底盖（钢）
    body.append(box(-0.50, 0.50, 1.05, 1.55, -1.60, 0.60, 'steel_d'))
    # 扳机护圈 + 扳机
    body.append(box(-0.34, 0.34, 0.62, 1.15, 0.90, 2.05, 'steel_d'))
    B.append(bone('body', (0.0, 1.9, 0.6), 'move', body))

    # ---------------- barrel：枪管 + 准星 + 刺刀座
    barrel = []
    barrel.append(box(-0.30, 0.30, 1.95, 2.55, -13.60, -8.40, 'steel'))       # 外露枪管
    barrel.append(box(-0.36, 0.36, 2.20, 2.95, -13.20, -12.80, 'steel_d'))    # 准星座
    barrel.append(box(-0.10, 0.10, 2.95, 3.35, -13.05, -12.90, 'steel_d'))    # 准星片
    barrel.append(box(-0.30, 0.30, 1.35, 1.95, -12.60, -11.60, 'steel_d'))    # 刺刀座/通条
    B.append(bone('barrel', (0.0, 2.25, -8.4), 'body', barrel))

    # ---------------- bolt：拉机柄（直栓 + 下弯手柄）
    bolt = []
    bolt.append(box(-0.24, 0.24, 2.75, 3.25, -1.90, 1.10, 'steel'))           # 枪机本体
    bolt.append(box(0.24, 1.30, 2.65, 3.15, 0.20, 0.80, 'steel_d'))           # 手柄横臂
    bolt.append(box(1.05, 1.45, 1.60, 2.90, 0.20, 0.80, 'steel_d'))           # 手柄下弯
    B.append(bone('bolt', (0.0, 2.95, -1.9), 'body', bolt))

    # ---------------- magazine：弹仓（Kar98k 是内置弹仓 ⇒ 只画底板）
    mag = [box(-0.46, 0.46, 0.95, 1.45, -1.20, 0.40, 'steel_d')]
    B.append(bone('magazine', (0.0, 1.2, -1.2), 'body', mag))

    # ---------------- trigger：扳机
    trig = [box(-0.09, 0.09, 0.60, 1.10, 1.30, 1.60, 'brass')]
    B.append(bone('trigger', (0.0, 1.1, 1.3), 'body', trig))

    # ---------------- casing：抛壳点（弹壳本体 + 动画锚点）
    # 弹壳就压在机匣右侧的抛壳口里（平时被 Kar98kGeoModel.staticPose 藏起来，
    # 拉栓进度走到 CASE_T0..CASE_T1 时才露出来、跟着枪机抽出来再翻滚抛向右上）
    case = [box(0.18, 0.42, 2.80, 3.04, -1.55, -0.85, 'brass')]
    B.append(bone('casing', (0.30, 3.00, -1.20), 'body', case))

    # ---------------- round_in：逐发压弹时那一发（7.62x59）
    # 静止位在机匣**内部**（y≈1.7，机匣 z −2.4…1.2 里的装填口那一段），装填时由 Kar98kGeoModel
    # 把它抬到机匣上方（LOAD_DROP 1.7 ⇒ y≈3.4：在机匣顶 3.00 之上、4 倍镜筒底 3.95 之下），
    # 再跟着左手一发一发按进弹仓。
    # ★ z 取 −1.75（不是 −1.55）：桥夹槽方块占 z −1.2…0.9、y 3.00…3.42，弹尾要留在它**前面**，
    #   否则抬起来时弹壳尾部会被桥夹槽挡掉一截。
    # 弹头朝 −Z（枪口方向）——与「上了膛的那一发」同向。
    rin = [box(-0.10, 0.10, 1.60, 1.80, -1.81, -1.25, 'brass'),      # 弹壳
           box(-0.08, 0.08, 1.62, 1.78, -1.95, -1.81, 'brass'),      # 弹肩
           box(-0.07, 0.07, 1.63, 1.77, -2.25, -1.95, 'steel')]      # 弹头
    B.append(bone('round_in', (0.0, 1.70, -1.75), 'body', rin))

    # ---------------- scope：自带 4 倍镜筒（镜身 + 前后镜片 + 两个镜环）
    scope = []
    scope.append(box(-0.42, 0.42, 3.95, 4.85, -4.20, 2.00, 'scope'))          # 镜筒
    scope.append(box(-0.52, 0.52, 3.85, 4.95, -4.70, -4.20, 'scope'))         # 物镜座
    scope.append(box(-0.40, 0.40, 3.95, 4.85, -4.62, -4.20, 'lens'))          # 物镜片
    scope.append(box(-0.40, 0.40, 3.95, 4.85, 2.00, 2.42, 'lens'))            # 目镜片
    scope.append(box(-0.46, 0.46, 3.30, 3.95, -3.10, -2.50, 'steel_d'))       # 前镜环
    scope.append(box(-0.46, 0.46, 3.30, 3.95, 0.60, 1.20, 'steel_d'))         # 后镜环
    B.append(bone('scope', (0.0, 4.4, -1.0), 'body', scope))

    # ---------------- bipod：空骨骼（保持与 AWP 同一套骨骼名，便于共用动画/逻辑）
    B.append(bone('bipod', (0.0, 1.9, -10.0), 'barrel', []))

    # ---------------- move / root
    B.append(bone('move', (0.0, 1.75, 0.0), 'root', []))
    B.append(bone('root', (0.0, 0.0, 0.0), None, []))
    return B


def build_geo():
    return {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.kar98k',
                'texture_width': TEX,
                'texture_height': TEX,
                'visible_bounds_width': 6,
                'visible_bounds_height': 4,
                'visible_bounds_offset': [0, 1.5, 0],
            },
            'bones': build_bones(),
        }],
    }


def build_texture():
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name, (y, rgb) in BANDS.items():
        base = rgb
        for x in range(256):                      # 只用到左侧 256 列中的色带
            if x >= TEX:
                break
            jitter = 1 + ((x * 7 + y * 13) % 5 - 2) * 0.02
            col = tuple(min(255, int(c * jitter)) for c in base)
            d.line([(x, y % TEX), (x, (y % TEX) + 9)], fill=col + (255,))
    # 一条黑色描边，避免全图纯色
    d.rectangle([0, 0, TEX - 1, TEX - 1], outline=(0, 0, 0, 255))
    return img


# 会发光的色带（抛光钢 / 镜筒 / 镜片 / 黄铜弹壳）：木托不发光
GLOW_BANDS = ('steel', 'scope', 'lens', 'brass')


def build_glowmask():
    """自发光遮罩：只把 GLOW_BANDS 那几条色带涂上（alpha=255），其余全透明。

    配合 ``client/GlossGlintLayer``（``GlossGlintLayer.mask('kar98k_geo')`` ⇒
    ``textures/models/kar98k_geo_glowmask.png``）做出「抛光件在暗处也反光」的流光层。
    几何与底色用的是同一条色带、同一个抖动公式，所以遮罩与贴图逐像素对齐。
    """
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name in GLOW_BANDS:
        y, rgb = BANDS[name]
        for x in range(TEX):
            jitter = 1 + ((x * 7 + y * 13) % 5 - 2) * 0.02
            col = tuple(min(255, int(c * jitter)) for c in rgb)
            d.line([(x, y), (x, y + 9)], fill=col + (255,))
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

    # 自检 + 打印包围盒（后面调 WeaponMount/WeaponArms 要用）
    xs, ys, zs, cubes = [], [], [], 0
    for b in geo['minecraft:geometry'][0]['bones']:
        for c in b['cubes']:
            cubes += 1
            o, s = c['origin'], c['size']
            xs += [o[0], o[0] + s[0]]
            ys += [o[1], o[1] + s[1]]
            zs += [o[2], o[2] + s[2]]
    print('bones =', len(geo['minecraft:geometry'][0]['bones']), ' cubes =', cubes)
    print('bbox  x[%.2f, %.2f]  y[%.2f, %.2f]  z[%.2f, %.2f]  (枪口 = -Z)'
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print('length = %.2f 像素 = %.3f 格' % (max(zs) - min(zs), (max(zs) - min(zs)) / 16.0))
    print('geo  ->', os.path.normpath(GEO_OUT))
    print('tex  ->', os.path.normpath(TEX_OUT))
    print('glow ->', os.path.normpath(GLOW_OUT))
    for b in geo['minecraft:geometry'][0]['bones']:
        # ★ 根骨骼按 bedrock 规范**省略** parent 键（见 bone() 的说明），所以这里用 get
        print('  %-9s parent=%-7s cubes=%d pivot=%s'
              % (b['name'], b.get('parent'), len(b['cubes']), b['pivot']))


if __name__ == '__main__':
    main()
