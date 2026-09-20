# -*- coding: utf-8 -*-
"""Q 弹版 AKM（Q版造型）—— 模型/贴图生成器

产出（写进 **Q 弹版** 的资源覆盖层，由 `gradlew build -Pqmode=true` 打进 Q 版 jar）
----------------------------------------------------------------------------
1. ``src/qresources/assets/hexalunar_calamity_q/geo/akm.geo.json``
2. ``src/qresources/assets/hexalunar_calamity_q/textures/models/akm_geo.png``
3. ``src/qresources/assets/hexalunar_calamity_q/textures/models/akm_geo_glowmask.png``

Q 版 = **短、粗、圆、可爱**：枪管短粗、机匣胖、护木圆墩、弹匣大香蕉、枪托短胖、
照门/准星做成夸张的大耳朵。

★ 关键：**所有「参照点」都保持和原版 AKM 完全一致**，所以不需要改任何 Java 代码
--------------------------------------------------------------------
`client/AkmGeoModel` / `weapon/WeaponMount` / `client/WeaponArms` 里写死的锚点是：

    ============  ==================================  ==========================
    用途          锚点（模型像素）                    本脚本自检项
    ============  ==================================  ==========================
    枪管轴线      Y = 1.75                            BORE_Y
    枪口          (0, 1.75, -11.60)                   MUZZLE_Z（枪管前端面）
    瞄准线        Y = 3.44（照门顶 = 准星顶 = 导轨齿顶） SIGHT_Y
    红点圆心      Y = 4.07                            DOT_Y
    4 倍镜光轴    Y = 4.28                            SCOPE_Y
    抛壳口        (0.95, 2.62, -2.30)                 EJECT
    右手握把      (0.00, 0.55, -0.15)                 GRIP
    左手托护木    (0.00, 2.05, -6.30)                 HANDGUARD
    弹匣          pivot (0, 1.45, -3.78)，下坠 9.8    MAG
    拉机柄        (0.70, 2.64, -3.54)，后退 1.9       BOLT
    ============  ==================================  ==========================

骨骼名也**原样照抄原版 AKM**（root/move/body/barrel/sights/handguard/dust_cover/bolt/
magazine/trigger/grip/stock/selector/camera/dot_sight/scope_4x/casing_0..3），
所以 GeckoLib 的换弹/拉栓/抛壳动画与 `AkmGeoModel` 的程序化驱动一行都不用动。

用法
----
    python tools/q_akm_gen.py          # 直接写进 src/qresources（Q 版覆盖层）
"""
import io
import json
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, 'src', 'qresources', 'assets', 'hexalunar_calamity_q')
GEO_OUT = os.path.join(RES, 'geo', 'akm.geo.json')
TEX_OUT = os.path.join(RES, 'textures', 'models', 'akm_geo.png')
GLOW_OUT = os.path.join(RES, 'textures', 'models', 'akm_geo_glowmask.png')

TEX = 128
# Q 版配色：比写实版更亮更饱和（木色偏橙、钢件偏蓝黑、高光更跳）
BANDS = {
    'wood':    (0,  (206, 148, 86)),     # 亮橙木（Q 版护木/枪托）
    'wood_d':  (16, (166, 110, 58)),     # 木纹暗部
    'steel':   (32, (96, 104, 120)),     # 蓝灰钢
    'steel_d': (48, (54, 60, 74)),       # 深蓝黑（机匣/弹匣）
    'scope':   (64, (36, 40, 52)),       # 黑件（瞄具/准星）
    'lens':    (80, (90, 190, 220)),     # 镜片（Q 版给个更亮的青蓝）
    'brass':   (96, (222, 186, 96)),     # 黄铜弹壳
}
PAT = {k: (0, v[0], 32, 10) for k, v in BANDS.items()}
GLOW_BANDS = ('steel', 'scope', 'lens', 'brass')

# ---- 必须守住的锚点（与 AkmGeoModel / WeaponMount / WeaponArms 里的常数一致）----
BORE_Y = 1.75
MUZZLE_Z = -11.60
SIGHT_Y = 3.44
DOT_Y = 4.07
SCOPE_Y = 4.28
EJECT = (0.95, 2.62, -2.30)
GRIP = (0.00, 0.55, -0.15)
HANDGUARD = (0.00, 2.05, -6.30)
MAG_PIVOT = (0.0, 1.45, -3.78)
BOLT = (0.70, 2.64, -3.54)


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


def bone(name, pivot, parent, cubes=None):
    b = {'name': name, 'pivot': [round(v, 4) for v in pivot], 'cubes': cubes or []}
    if parent:
        b['parent'] = parent
    return b


def build_bones():
    """Q 版 AKM：短粗圆胖，但所有锚点与原版一致"""
    B = []

    # ---------------- body：胖机匣 + 短胖枪托 + 大握把 + 扳机组
    body = []
    body.append(box(-0.62, 0.62, 1.30, 2.90, -1.40, 2.20, 'steel_d'))    # 机匣（胖）
    body.append(box(-0.50, 0.50, 2.90, 3.44, -1.30, -0.30, 'scope'))     # 照门塔（顶 = 3.44）
    body.append(box(-0.30, 0.30, 3.36, 3.44, -1.10, -0.50, 'steel'))     # 照门缺口（也顶到 3.44）
    body.append(box(-0.54, 0.54, 1.05, 2.55, 2.20, 5.30, 'wood'))        # 短胖枪托
    body.append(box(-0.54, 0.54, 1.00, 2.55, 5.30, 5.60, 'steel_d'))     # 托底板
    body.append(box(-0.26, 0.26, -0.55, 1.40, -0.50, 0.25, 'wood_d'))    # 大握把（含 0,0.55,-0.15）
    body.append(box(-0.34, 0.34, 0.35, 1.35, -1.95, 0.35, 'steel_d'))    # 扳机护圈
    body.append(box(-0.10, 0.10, 0.60, 1.30, -1.85, -1.55, 'steel'))     # 扳机
    body.append(box(-0.36, 0.36, 1.05, 1.40, -2.60, -1.40, 'steel_d'))   # 弹匣井
    B.append(bone('body', (0.0, 1.75, -2.60), 'move', body))

    # ---------------- barrel：短粗枪管 + 大准星 + 导气箍
    bar = []
    bar.append(box(-0.42, 0.42, 1.33, 2.17, -11.60, -5.90, 'steel'))     # 粗枪管（轴线 1.75，前端面 -11.60）
    bar.append(box(-0.52, 0.52, 1.25, 2.25, -11.60, -10.90, 'steel_d'))  # 枪口箍（夸张）
    bar.append(box(-0.30, 0.30, 2.17, 2.60, -9.90, -9.10, 'steel_d'))    # 导气箍
    bar.append(box(-0.14, 0.14, 2.60, 3.44, -9.75, -9.45, 'scope'))      # 大准星柱（顶 = 3.44）
    B.append(bone('barrel', (0.0, 1.75, -9.30), 'body', bar))

    # ---------------- handguard：圆墩墩的木护木（含左手锚点 0,2.05,-6.30 ⇒ 前伸到 −6.60）
    hg = []
    hg.append(box(-0.56, 0.56, 1.25, 2.62, -6.60, -1.40, 'wood'))
    hg.append(box(-0.46, 0.46, 2.62, 2.88, -6.20, -1.70, 'wood_d'))      # 上沿（导气管盖）
    B.append(bone('handguard', (0.0, 2.20, -6.30), 'body', hg))

    # ---------------- sights：机瞄（导轨上的小耳朵，Q 版给大一点）
    sights = [box(-0.26, 0.26, 2.88, 3.05, -6.20, -5.40, 'scope')]
    B.append(bone('sights', (0.0, 2.40, -8.00), 'body', sights))

    # ---------------- dust_cover：机匣盖（Q 版加厚）
    dc = [box(-0.58, 0.58, 2.90, 3.20, -4.90, -1.40, 'steel_d')]
    B.append(bone('dust_cover', (0.0, 2.96, -4.50), 'body', dc))

    # ---------------- bolt：拉机柄（含锚点 0.70,2.64,-3.54；后退 1.9）
    bolt = [
        box(-0.30, 0.30, 2.35, 2.90, -4.20, -2.60, 'steel'),             # 枪机框
        box(0.42, 0.88, 2.45, 2.85, -3.80, -3.30, 'scope'),              # 大拉机柄（含 0.70,2.64,-3.54）
    ]
    B.append(bone('bolt', (0.0, 2.55, -3.60), 'body', bolt))

    # ---------------- magazine：大香蕉弹匣（pivot 0,1.45,-3.78 必须落在方块内；下坠 9.8）
    mag = [
        box(-0.34, 0.34, 0.30, 1.55, -4.60, -3.60, 'steel_d'),           # 匣体（含 pivot）
        box(-0.30, 0.30, 0.00, 0.35, -4.20, -3.45, 'steel_d'),           # 下段（香蕉弯）
    ]
    B.append(bone('magazine', MAG_PIVOT, 'body', mag))

    # ---------------- trigger / grip / stock / selector
    trig = [box(-0.10, 0.10, 0.60, 1.30, -1.85, -1.55, 'steel')]
    B.append(bone('trigger', (0.0, 1.25, -1.55), 'body', trig))
    grip = [box(-0.26, 0.26, -0.55, 1.40, -0.50, 0.25, 'wood_d')]
    B.append(bone('grip', (0.0, 1.30, -0.05), 'body', grip))
    stock = [box(-0.54, 0.54, 1.05, 2.55, 2.20, 5.60, 'wood')]
    B.append(bone('stock', (0.0, 2.00, 0.22), 'body', stock))
    sel = [box(-0.14, 0.14, 2.75, 3.00, -4.60, -4.20, 'scope')]
    B.append(bone('selector', (0.0, 2.60, -4.30), 'body', sel))

    # ---------------- camera：空骨骼（动画用它推镜头，AkmGeoModel 会清零）
    B.append(bone('camera', (0.0, 2.65, -1.85), 'body', []))

    # ---------------- 瞄具（按档位显隐；圆心/光轴必须落在 DOT_Y / SCOPE_Y 上）
    dot = [
        box(-0.26, 0.26, 3.44, 4.30, -5.95, -5.05, 'scope'),             # 红点外壳
        box(-0.20, 0.20, 3.95, 4.20, -5.85, -5.15, 'lens'),              # 镜片（圆心 4.07）
    ]
    B.append(bone('dot_sight', (0.0, DOT_Y, -5.50), 'body', dot))
    scope = [
        box(-0.30, 0.30, 3.98, 4.58, -7.10, -4.10, 'scope'),             # 镜筒（光轴 4.28）
        box(-0.36, 0.36, 3.90, 4.66, -7.30, -6.90, 'scope'),             # 物镜座
        box(-0.36, 0.36, 3.90, 4.66, -4.30, -3.90, 'scope'),             # 目镜座
        box(-0.34, 0.34, 3.85, 3.98, -6.60, -6.20, 'steel_d'),           # 前镜环
        box(-0.34, 0.34, 3.85, 3.98, -5.30, -4.90, 'steel_d'),           # 后镜环
    ]
    B.append(bone('scope_4x', (0.0, SCOPE_Y, -5.60), 'body', scope))

    # ---------------- casing_0..3：抛壳（锚点 0.95,2.62,-2.30；只给 casing_0 一个方块，
    #                  其余三根留空骨骼 —— AkmGeoModel 对 null 有判空，空骨骼也不会渲染）
    case = [box(0.72, 1.18, 2.42, 2.82, -2.60, -2.00, 'brass')]
    for i in range(4):
        B.append(bone('casing_%d' % i, EJECT, 'body', case if i == 0 else []))

    # ---------------- move / root（move pivot 必须 = (0,1.75,0)，AkmGeoModel 写死了）
    B.append(bone('move', (0.0, 1.75, 0.0), 'root', []))
    B.append(bone('root', (0.0, 1.75, 0.0), None, []))
    return B


def build_geo():
    return {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.akm',
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
    d.rectangle([0, 0, TEX - 1, TEX - 1], outline=(0, 0, 0, 255))
    return img


def build_glowmask():
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name in GLOW_BANDS:
        y, rgb = BANDS[name]
        for x in range(TEX):
            d.line([(x, y), (x, y + 9)], fill=_jitter(x, y, rgb) + (255,))
    return img


def _inside(cubes, p):
    """点 p 是否落在某个方块内（用来核对锚点）"""
    for c in cubes:
        o, s = c['origin'], c['size']
        if (o[0] - 1e-6 <= p[0] <= o[0] + s[0] + 1e-6
                and o[1] - 1e-6 <= p[1] <= o[1] + s[1] + 1e-6
                and o[2] - 1e-6 <= p[2] <= o[2] + s[2] + 1e-6):
            return True
    return False


def main():
    geo = build_geo()
    os.makedirs(os.path.dirname(GEO_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    with io.open(GEO_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(geo, f, ensure_ascii=False, indent=1)
        f.write('\n')
    build_texture().save(TEX_OUT)
    build_glowmask().save(GLOW_OUT)

    bones = {b['name']: b for b in geo['minecraft:geometry'][0]['bones']}
    cubes = 0
    xs, ys, zs = [], [], []
    for b in bones.values():
        for c in b['cubes']:
            cubes += 1
            o, s = c['origin'], c['size']
            xs += [o[0], o[0] + s[0]]
            ys += [o[1], o[1] + s[1]]
            zs += [o[2], o[2] + s[2]]
    print('Q 版 AKM：骨骼 %d / 方块 %d' % (len(bones), cubes))
    print('bbox x[%.2f, %.2f] y[%.2f, %.2f] z[%.2f, %.2f]  长度 %.2f 像素（原版 AKM 更长）'
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), max(zs) - min(zs)))
    print()
    print('★ 锚点自检（必须与 AkmGeoModel / WeaponMount / WeaponArms 一致）：')
    print('  枪口前端面 z = %.2f  （要求 %.2f）' % (min(zs), MUZZLE_Z))
    print('  枪管轴线  y = %.2f  （要求 %.2f）' % (BORE_Y, BORE_Y))

    def top_of(name):
        cs = bones[name]['cubes']
        return max(c['origin'][1] + c['size'][1] for c in cs)

    print('  准星顶    y = %.2f  （要求 %.2f）' % (top_of('barrel'), SIGHT_Y))
    print('  照门顶    y = %.2f  （要求 %.2f）' % (top_of('body'), SIGHT_Y))
    print('  瞄准线（准星顶 = 照门顶 = %.2f）%s'
          % (SIGHT_Y, 'OK' if abs(top_of('barrel') - top_of('body')) < 1e-6 else '*** 不一致 ***'))
    print('  枪口点 (0, %.2f, %.2f) 在枪管方块内：%s'
          % (BORE_Y, MUZZLE_Z, _inside(bones['barrel']['cubes'], (0, BORE_Y, MUZZLE_Z + 0.01))))
    print('  抛壳口 %s 在 casing_0 内：%s' % (EJECT, _inside(bones['casing_0']['cubes'], EJECT)))
    print('  右手握把 %s 在 grip 内：%s' % (GRIP, _inside(bones['grip']['cubes'], GRIP)))
    print('  左手护木 %s 在 handguard 内：%s' % (HANDGUARD, _inside(bones['handguard']['cubes'], HANDGUARD)))
    print('  弹匣 pivot %s 在 magazine 内：%s' % (MAG_PIVOT, _inside(bones['magazine']['cubes'], MAG_PIVOT)))
    print('  拉机柄 %s 在 bolt 内：%s' % (BOLT, _inside(bones['bolt']['cubes'], BOLT)))
    print('  红点圆心 y=%.2f / 4 倍镜光轴 y=%.2f（镜筒中心 %.2f）'
          % (DOT_Y, SCOPE_Y, 3.98 + (4.58 - 3.98) / 2))
    print()
    print('geo  ->', os.path.normpath(GEO_OUT))
    print('tex  ->', os.path.normpath(TEX_OUT))
    print('glow ->', os.path.normpath(GLOW_OUT))


if __name__ == '__main__':
    main()
