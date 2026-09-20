#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""莫辛纳甘 M91/30（带长刺刀）—— 按用户给的实枪照片做的模型生成器。

★ 只出**模型**（geo + 贴图 + Blockbench 工程），**不改 Java、不进模组**。
  产物：
    1. ``build/mosin_m9130.geo.json``            几何（GeckoLib / Bedrock 通用）
    2. ``build/mosin_m9130.png``                 贴图（128²，色带式）
    3. ``build/mosin_m9130_glowmask.png``        流光遮罩
    4. ``模型/mosin_m9130/``                     以上三份的永久副本（gradlew clean 不会冲掉）
  再跑 ``python tools/geo2bbmodel.py`` 就能得到 ``模型/hexalunar_mosin_m9130.bbmodel``。

规格（照照片量的，1 模型像素 = 1/16 格 ≈ 6.25 cm）
--------------------------------------------------
    全长（含刺刀）  28.2 像素 ≈ 1.76 格      其中刺刀 5.8 像素 ≈ 36 cm
    枪管轴线        Y = 1.75                 机瞄瞄准线 Y = 2.72（准星柱顶 = 表尺两耳顶）
    枪口端面        z = -16.78               弹仓 pivot (0, 1.06, -2.75)
    抛壳口          (0.62, 2.10, -1.95)      托底 z = +5.60
  锚点与现有 ``mosin.geo.json`` **逐字一致**（BORE/IRON_Y/枪口/抛壳/弹仓/上护木/拉机柄），
  骨骼名也照抄（body/barrel/handguard/bolt/magazine/round_in/trigger/casing/scope/camera），
  只多一根 ``bayonet``（刺刀独立骨骼，方便做刺杀动作或单独显隐）
  ⇒ 以后想把它接进游戏，直接替换 geo 即可，Java 一行不用改。

照片特征 → 模型部件
--------------------
  浅胡桃木托 + 上护木（比现有发蓝钢+红棕漆那版更亮） / 两道**黄铜**枪箍 /
  **黄铜**外露弹仓 + 钢底板 / 立框式表尺 + 罩式准星 / 直拉机柄 + 下弯球头 /
  枪托侧面两个枪背带槽 + 钢托板 / 枪管下方通条 / 枪口插座式长刺刀（带固定螺钉）。

用法
----
    python tools/mosin_m9130_gen.py
"""
import io
import json
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, 'build')
KEEP = os.path.join(ROOT, '模型', 'mosin_m9130')
GEO_NAME = 'mosin_m9130'

TEX = 128
# ------------------------------------------------------------------ 调色板（照照片）
BANDS = {
    'wood':     (0,   (198, 142, 92)),    # 亮胡桃木（照片里的托/护木）
    'wood_d':   (16,  (166, 110, 62)),    # 木纹暗部（前托/护木下缘）
    'wood_dd':  (32,  (138, 88, 48)),     # 枪背带槽 / 凹处
    'steel':    (48,  (150, 154, 164)),   # 抛光钢（刺刀/枪机/通条）
    'steel_d':  (64,  (62, 68, 82)),      # 深钢（枪管/机匣）
    'steel_dd': (80,  (40, 44, 56)),      # 更暗（准星座/表尺/托板/扳机）
    'brass':    (96,  (198, 154, 76)),    # 黄铜（枪箍/弹仓/弹壳）
    'black':    (112, (30, 34, 44)),      # 枪口内孔
}
PAT = {k: (0, v[0], 32, 10) for k, v in BANDS.items()}
GLOW_BANDS = ('steel', 'brass')           # 金属反光（很轻）

# ------------------------------------------------------------------ 必须守住的锚点
BORE = 1.75                 # 枪管轴线
IRON_Y = 2.72               # 机瞄瞄准线（准星柱顶 = 表尺两耳顶）
RCV_TOP = 2.44              # 机匣顶面（必须低于 IRON_Y）
MUZZLE_Z = -16.78           # 枪管前端面（弹丸出膛点）
EJECT = (0.62, 2.10, -1.95)  # 抛壳口
MAG_PIVOT = (0.0, 1.06, -2.75)
ROUND_PIVOT = (0.0, 0.86, -2.80)
HANDGUARD = (0.0, 2.06, -9.40)   # 左手托护木的锚点（现有 mosin 同值）
BUTT_Z = 5.60
BAYONET_TIP = -22.40


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
    """骨骼层级与现有 mosin 完全一致，多一根 bayonet"""
    B = []

    # ---------------- bayonet：枪口插座 + 固定螺钉 + 四棱长刺刀 ----------------
    bay = [
        box(-0.34, 0.34, 1.41, 2.09, -17.35, -16.60, 'steel'),      # 插座（包住枪口）
        box(0.34, 0.48, 1.68, 1.86, -17.22, -17.00, 'steel_dd'),    # 固定螺钉
        box(-0.15, 0.15, 1.60, 1.90, -18.60, -17.35, 'steel'),      # 刀身段 1
        box(-0.12, 0.12, 1.63, 1.87, -20.60, -18.60, 'steel'),      # 刀身段 2
        box(-0.08, 0.08, 1.67, 1.83, -22.40, -20.60, 'steel'),      # 刀尖
        box(-0.03, 0.03, 1.68, 1.82, -22.70, -22.40, 'steel'),      # 尖头
    ]
    B.append(bone('bayonet', (0.0, BORE, MUZZLE_Z), 'barrel', bay))

    # ---------------- barrel：阶梯枪管 + 枪口 + 准星 + 立框表尺 + 通条 ----------------
    bar = [
        box(-0.34, 0.34, BORE - 0.34, BORE + 0.34, -6.20, -4.30, 'steel_d'),   # 机匣前段
        box(-0.30, 0.30, BORE - 0.30, BORE + 0.30, -12.60, -6.20, 'steel_d'),  # 中段
        box(-0.26, 0.26, BORE - 0.26, BORE + 0.26, -16.62, -12.60, 'steel_d'),  # 前段（细）
        box(-0.28, 0.28, BORE - 0.28, BORE + 0.28, MUZZLE_Z, -16.62, 'steel'),  # 枪口帽
        box(-0.10, 0.10, BORE - 0.10, BORE + 0.10, MUZZLE_Z, MUZZLE_Z + 0.04, 'black'),  # 枪口内孔
        # 通条（照片里枪管下方那根细杆）
        box(-0.07, 0.07, 1.15, 1.29, -16.40, -5.60, 'steel'),
        box(-0.10, 0.10, 1.13, 1.31, -16.55, -16.40, 'steel_dd'),
        # 前准星：底座 + 柱（柱顶 = IRON_Y）+ 两片护耳（低于柱顶，不挡瞄准线）
        box(-0.28, 0.28, 2.02, 2.26, -15.95, -15.40, 'steel_dd'),
        box(-0.075, 0.075, 2.26, IRON_Y, -15.80, -15.55, 'steel_dd'),
        box(-0.30, -0.13, 2.26, 2.62, -15.90, -15.45, 'steel_dd'),
        box(0.13, 0.30, 2.26, 2.62, -15.90, -15.45, 'steel_dd'),
        # 立框式表尺（M91/30 的招牌件）：底座 + 斜坡 + 游标 + 缺口两耳（耳顶 = IRON_Y）
        box(-0.34, 0.34, 2.02, 2.28, -5.60, -4.30, 'steel_dd'),
        box(-0.30, 0.30, 2.28, 2.40, -5.50, -5.00, 'steel_dd'),
        box(-0.32, 0.32, 2.34, 2.48, -5.06, -4.80, 'steel_dd'),
        box(-0.32, -0.10, 2.48, IRON_Y, -5.62, -5.34, 'steel_dd'),
        box(0.10, 0.32, 2.48, IRON_Y, -5.62, -5.34, 'steel_dd'),
    ]
    B.append(bone('barrel', (0.0, BORE, -9.00), 'move', bar))

    # ---------------- handguard：上护木 + 两道黄铜枪箍 ----------------
    hg = [
        box(-0.42, 0.42, 2.02, 2.32, -13.40, -6.70, 'wood'),          # 上护木
        box(-0.40, 0.40, 1.98, 2.30, -14.10, -13.40, 'wood_d'),       # 护木前端收口
        box(-0.46, 0.46, 1.20, 2.34, -13.30, -12.90, 'brass'),        # 前枪箍（黄铜）
        box(-0.48, 0.48, 1.16, 2.36, -8.90, -8.50, 'brass'),          # 后枪箍（黄铜）
        box(-0.50, 0.50, 1.14, 1.20, -13.30, -12.90, 'steel_dd'),     # 前箍箍带（钢）
        box(-0.52, 0.52, 1.10, 1.16, -8.90, -8.50, 'steel_dd'),       # 后箍箍带（钢）
    ]
    B.append(bone('handguard', (0.0, 2.06, -9.40), 'body', hg))

    # ---------------- body：前托 + 枪托 + 机匣 + 托板 + 枪背带槽 + 扳机护圈 ----------------
    body = [
        box(-0.42, 0.42, 1.16, 1.98, -14.60, -13.40, 'wood_d'),       # 前托（枪口方向渐薄）
        box(-0.50, 0.50, 1.14, 2.06, -13.40, -6.60, 'wood'),          # 前托主体
        box(-0.52, 0.52, 1.10, 2.10, -6.60, -4.30, 'wood'),           # 机匣段木托
        box(-0.56, 0.56, 0.60, 2.28, -4.30, 0.60, 'wood'),            # 机匣座木托
        box(-0.46, 0.46, 0.66, 1.98, 0.60, 2.60, 'wood_d'),           # 握把（腕部）
        box(-0.52, 0.52, 0.40, 2.30, 2.60, 4.20, 'wood'),             # 托身（含高起的托腮台）
        box(-0.52, 0.52, 0.40, 2.06, 4.20, BUTT_Z, 'wood'),           # 托身（尾部收低 = 照片的台阶）
        box(-0.54, 0.54, 0.36, 2.34, BUTT_Z - 0.16, BUTT_Z, 'steel_dd'),  # 钢托板
        box(-0.58, -0.50, 1.28, 1.52, 3.70, 4.30, 'wood_dd'),         # 枪背带槽（托侧）
        box(-0.58, -0.50, 1.34, 1.58, -1.60, -1.10, 'wood_dd'),       # 枪背带槽（前）
        box(0.50, 0.58, 1.32, 1.56, 3.80, 4.20, 'brass'),             # 背带铜底板（右侧）
        # 机匣
        box(-0.38, 0.38, 1.40, RCV_TOP, -4.30, -0.30, 'steel_d'),
        box(-0.34, 0.34, RCV_TOP, RCV_TOP + 0.06, -4.10, -0.50, 'steel'),
        # 扳机护圈（前立柱 + 底梁 + 后立柱）
        box(-0.30, 0.30, 1.20, 1.30, -2.30, -2.18, 'steel_dd'),
        box(-0.24, 0.24, 0.44, 0.54, -2.30, -1.30, 'steel_dd'),
        box(-0.30, 0.30, 0.44, 1.30, -1.42, -1.30, 'steel_dd'),
    ]
    B.append(bone('body', (0.0, BORE, -2.40), 'move', body))

    # ---------------- bolt：枪机 + 机尾 + 直拉机柄 + 球头 ----------------
    bolt = [
        box(-0.26, 0.26, 1.52, 2.02, -3.60, -1.10, 'steel'),
        box(-0.30, 0.30, 1.46, 2.10, -1.10, -0.50, 'steel'),
        box(-0.22, 0.22, 1.58, 2.00, -0.50, -0.20, 'steel_d'),
        box(0.30, 0.86, 1.56, 1.84, -1.90, -1.60, 'steel'),           # 直拉机柄
        box(0.80, 1.06, 1.46, 1.70, -1.94, -1.62, 'steel_d'),         # 球头
    ]
    B.append(bone('bolt', (0.0, BORE, -1.85), 'body', bolt))

    # ---------------- magazine：外露弹仓（黄铜）+ 钢底板 ----------------
    mag = [
        box(-0.36, 0.36, 0.42, 1.30, -3.50, -2.10, 'brass'),
        box(-0.40, 0.40, 0.30, 0.46, -3.40, -2.20, 'steel_dd'),
    ]
    B.append(bone('magazine', MAG_PIVOT, 'body', mag))

    # ---------------- round_in：正在压进去的那一发（静止时收在弹仓里） ----------------
    rin = [
        box(-0.075, 0.075, 0.79, 0.93, -3.20, -2.62, 'brass'),
        box(-0.075, 0.075, 0.79, 0.93, -2.62, -2.36, 'steel'),
    ]
    B.append(bone('round_in', ROUND_PIVOT, 'body', rin))

    # ---------------- trigger ----------------
    B.append(bone('trigger', (0.0, 1.00, -1.78), 'body',
                  [box(-0.08, 0.08, 0.62, 1.06, -1.90, -1.72, 'steel_dd')]))

    # ---------------- casing：抛壳动画用的弹壳（含抛壳口锚点） ----------------
    B.append(bone('casing', EJECT, 'body',
                  [box(0.54, 0.70, 2.02, 2.18, -2.10, -1.80, 'brass')]))

    # ---------------- 与现有 mosin 同名的空骨骼（以后想接进游戏可以直接掉包） ----------------
    B.append(bone('scope', (0.0, 3.44, -2.60), 'body', []))
    B.append(bone('scope_elev', (0.0, 3.80, -2.40), 'scope', []))
    B.append(bone('scope_wind', (0.42, 3.44, -2.40), 'scope', []))
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


def _jitter(x, y, rgb):
    k = 1 + ((x * 7 + y * 13) % 5 - 2) * 0.025
    return tuple(min(255, int(c * k)) for c in rgb)


def _paint(bands):
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name in bands:
        y, rgb = BANDS[name]
        for x in range(TEX):
            d.line([(x, y), (x, y + 9)], fill=_jitter(x, y, rgb) + (255,))
    d.rectangle([0, 0, TEX - 1, TEX - 1], outline=(0, 0, 0, 255))
    return img


def _inside(cubes, p):
    for c in cubes:
        o, s = c['origin'], c['size']
        if all(o[i] - 1e-6 <= p[i] <= o[i] + s[i] + 1e-6 for i in range(3)):
            return True
    return False


def _top(bones, name):
    return max(c['origin'][1] + c['size'][1] for c in bones[name]['cubes'])


def main():
    geo = build_geo()
    bones = {b['name']: b for b in geo['minecraft:geometry'][0]['bones']}
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(KEEP, exist_ok=True)
    outs = []
    for d in (BUILD, KEEP):
        gp = os.path.join(d, GEO_NAME + '.geo.json')
        tp = os.path.join(d, GEO_NAME + '.png')
        wp = os.path.join(d, GEO_NAME + '_glowmask.png')
        with io.open(gp, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(geo, f, ensure_ascii=False, indent=1)
            f.write('\n')
        _paint(BANDS).save(tp)
        _paint(GLOW_BANDS).save(wp)
        outs.append(d)

    ncube = sum(len(b['cubes']) for b in bones.values())
    print('莫辛纳甘 M91/30（带刺刀）：骨骼 %d / 方块 %d' % (len(bones), ncube))
    zs = [c['origin'][2] + c['size'][2] for b in bones.values() for c in b['cubes']]
    z0 = [c['origin'][2] for b in bones.values() for c in b['cubes']]
    print('  bbox z[%.2f, %.2f]  全长 %.2f 像素 = %.2f 格（含刺刀 %.2f 像素 = %.2f 格）'
          % (min(z0), max(zs), max(zs) - min(z0), (max(zs) - min(z0)) / 16.0,
             MUZZLE_Z - BAYONET_TIP, (MUZZLE_Z - BAYONET_TIP) / 16.0))
    print()
    print('★ 锚点自检（与现有 mosin.geo.json / MosinRifleItem / WeaponMount 一致）：')
    print('  枪管轴线 y = %.2f（要求 %.2f）' % (BORE, BORE))
    print('  枪口端面 z = %.2f（要求 %.2f）' % (min(c['origin'][2] for c in bones['barrel']['cubes']
                                                if c['origin'][2] > BAYONET_TIP + 1), MUZZLE_Z))
    print('  准星柱顶 y = %.2f / 表尺两耳顶 y = %.2f（要求都 = %.2f）%s'
          % (2.26 + 0.46, IRON_Y, IRON_Y, 'OK' if abs(_top(bones, 'barrel') - IRON_Y) < 1e-6 else '??'))
    print('  机匣顶 %.2f < 机瞄线 %.2f：%s' % (RCV_TOP, IRON_Y,
                                             'OK' if RCV_TOP < IRON_Y else '!! 挡住机瞄'))
    print('  枪口点在枪管方块内：%s' % _inside(bones['barrel']['cubes'], (0, BORE, MUZZLE_Z + 0.05)))
    print('  抛壳点 %s 在 casing 内：%s' % (EJECT, _inside(bones['casing']['cubes'], EJECT)))
    print('  弹仓 pivot %s 在 magazine 内：%s' % (MAG_PIVOT, _inside(bones['magazine']['cubes'], MAG_PIVOT)))
    print('  压弹 pivot %s 在 round_in 内：%s'
          % (ROUND_PIVOT, _inside(bones['round_in']['cubes'], ROUND_PIVOT)))
    print('  左手护木锚点 %s 在 handguard 内：%s'
          % (HANDGUARD, _inside(bones['handguard']['cubes'], HANDGUARD)))
    print('  空骨骼（兼容现有 Java，按名字查不会 null）：%s'
          % [n for n in ('scope', 'scope_elev', 'scope_wind', 'camera') if not bones[n]['cubes']])
    print()
    print('骨骼层级：')
    for n in ('root', 'move', 'body', 'barrel', 'bayonet', 'handguard', 'bolt', 'magazine',
              'round_in', 'trigger', 'casing', 'scope', 'scope_elev', 'scope_wind', 'camera'):
        b = bones[n]
        print('  %-11s parent=%-10s pivot=%-22s cubes=%d'
              % (n, b.get('parent', '-'), '[%.2f,%.2f,%.2f]' % tuple(b['pivot']), len(b['cubes'])))
    print()
    for d in outs:
        print('  ->', os.path.relpath(os.path.join(d, GEO_NAME + '.geo.json'), ROOT))
    print('  接着跑：python tools/geo2bbmodel.py   （会导出 模型/hexalunar_%s.bbmodel）' % GEO_NAME)


if __name__ == '__main__':
    main()
