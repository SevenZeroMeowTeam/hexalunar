# -*- coding: utf-8 -*-
"""六相月灾「天空颜色 + 月亮颜色」的离线预览（r66）。

按 MoonSkyRenderer 的同一套结构画一张 6 格图：
每格 = 天空竖直渐变（天顶色 → 地平线色，与 Java 同样的透明度）+ 月盘（底色 + 三个陨石坑 + 叠加光晕）
—— 只看配色与月盘观感，不看真实几何。

跑法: python tools/_moonsky_mock.py [out.png]
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'build', '_moonsky_mock.png')

# 与 MoonPhase.java 的 moonColor / moonHalo / skyTop / skyHorizon 一一对应
PHASES = [
    ('血月',      0xFF4A38, 0xFF2A18, 0x1C0608, 0x521114, False),
    ('蓝月',      0xAECBFF, 0x4A7CFF, 0x06101F, 0x143A6E, False),
    ('黄月',      0xFFD35E, 0xFFB320, 0x141005, 0x453512, False),
    ('超级血月',  0xFF6E52, 0xFF3018, 0x28070B, 0x6E1616, True),
    ('超级蓝月',  0xD2E8FF, 0x5E96FF, 0x08142E, 0x1C4A88, True),
    ('超级黄月',  0xFFE9A0, 0xFFC840, 0x1C1608, 0x57431A, True),
]

SKY_TOP_A, SKY_HORIZON_A = 0.42, 0.60     # 与 Java 一致
NIGHT = (0x05, 0x07, 0x0E)                # 近似原版夜空（我们的天穹是叠在它上面的）
PANEL_W, PANEL_H = 420, 260


def rgb(v):
    return ((v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def blend(base, col, a):
    return mix(base, col, a)


def draw_panel(name, moon, halo, top, hor, super_moon):
    img = Image.new('RGB', (PANEL_W, PANEL_H), NIGHT)
    d = ImageDraw.Draw(img)
    top_c, hor_c = rgb(top), rgb(hor)
    # 天空：地平线在下方 78% 处，天顶在上缘（与 Java 的球面渐变对应）
    horizon_y = int(PANEL_H * 0.78)
    for y in range(horizon_y):
        t = y / max(1, horizon_y - 1)                 # 0 = 天顶、1 = 地平线
        base = blend(NIGHT, top_c, SKY_TOP_A)
        col = mix(base, blend(NIGHT, hor_c, SKY_HORIZON_A), t)
        d.line([(0, y), (PANEL_W, y)], fill=col)
    d.rectangle([0, horizon_y, PANEL_W, PANEL_H], fill=mix(NIGHT, top_c, 0.16))

    cx, cy = PANEL_W // 2, int(PANEL_H * 0.30)
    r = 46
    mc, hc = rgb(moon), rgb(halo)
    # 光晕：叠加混合（越靠外越弱）
    glow = int(r * (2.35 if super_moon else 1.8))
    for i in range(60, 0, -1):
        rr = glow * i / 60.0
        a = (0.42 if super_moon else 0.30) * max(0.0, (1.0 - (rr - r) / max(1.0, glow - r)))
        if rr < r:
            break
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  outline=mix(NIGHT, hc, a), width=2)
    # 月盘（不透明）+ 陨石坑
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mc)
    for fr, ox, oy, f in ((0.22, 0.34, -0.26, 0.82), (0.15, -0.30, 0.30, 0.88),
                          (0.11, -0.14, -0.44, 1.08)):
        rr = r * fr
        px, py = cx + r * ox, cy + r * oy
        col = tuple(min(255, int(c * f)) for c in mc)
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col)
    d.rectangle([0, PANEL_H - 22, PANEL_W, PANEL_H], fill=(10, 10, 14))
    d.text((8, PANEL_H - 18), '%s  月 #%06X  天顶 #%06X  地平线 #%06X'
           % (name, moon, top, hor), fill=(230, 230, 236))
    return img


def main(argv):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
    out = argv[1] if len(argv) > 1 else OUT
    sheet = Image.new('RGB', (PANEL_W * 3, PANEL_H * 2), (0, 0, 0))
    for i, (name, moon, halo, top, hor, sm) in enumerate(PHASES):
        sheet.paste(draw_panel(name, moon, halo, top, hor, sm),
                    ((i % 3) * PANEL_W, (i // 3) * PANEL_H))
    sheet.save(out)
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv)
