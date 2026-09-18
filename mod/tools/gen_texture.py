#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成十字弩的 64x64 像素贴图（纯 Python，只用 zlib/struct 写 PNG）。

产物：
  build/bbtex/crossbow_geo.png                      预览用
  src/main/resources/assets/hexalunar_calamity/textures/item/crossbow_geo.png
  tools/bb_texture.js                               把贴图塞进 Blockbench 的脚本

贴图布局（必须和 tools/bb_build.js 里的 MAT / PAT 表一致）：
  上半 0..15 行是 8x8 的纯色格子，模型面直接采样格子中心 1 texel，保证平色不出噪点；
  下半是手工绘制的细节块：机匣侧面、皮轨齿、弹匣筋、握把防滑纹、镜片、凸轮等。
"""
import base64
import json
import os
import struct
import zlib

RES = 64

PALETTE = {
    'body_main': '#17171A', 'body_hi': '#26262C', 'body_dark': '#0C0C0F', 'metal': '#3B3B43',
    'rubber': '#0F0F12', 'string': '#C9C2AE', 'glass': '#1D4A63', 'steel': '#7C7C86',
    'limb': '#101014', 'cam': '#2A2A31', 'limb_hi': '#1C1C22', 'accent': '#6E6E78',
    'scope_body': '#1A1A1F', 'bolt_wood': '#2E2E34', 'glass_dark': '#0B2A3A', 'white': '#D8D8DC',
}

# 每个色板在贴图上的格子位置（列, 行）
SWATCH_AT = {
    'body_main': (0, 0), 'body_hi': (1, 0), 'body_dark': (2, 0), 'metal': (3, 0),
    'rubber': (4, 0), 'string': (5, 0), 'glass': (6, 0), 'steel': (7, 0),
    'limb': (0, 1), 'cam': (1, 1), 'limb_hi': (2, 1), 'accent': (3, 1),
    'scope_body': (4, 1), 'bolt_wood': (5, 1), 'glass_dark': (6, 1), 'white': (7, 1),
}

# 细节块 (u, v, w, h) —— 必须和 bb_build.js 的 PAT 完全一致
PATCHES = {
    'recvSide': (0, 16, 8, 4), 'recvTop': (9, 16, 4, 8), 'midSide': (14, 16, 7, 4),
    'rivSide': (22, 16, 5, 5), 'magSide': (28, 16, 4, 6), 'gripSide': (33, 16, 3, 5),
    'scopeSide': (37, 16, 7, 2), 'scopeFront': (45, 16, 4, 3), 'camSide': (50, 16, 3, 3),
    'buttSide': (54, 16, 6, 5), 'railTop': (0, 32, 2, 14), 'limbTop': (3, 32, 6, 2),
    'boltSide': (10, 32, 8, 1), 'riserSide': (19, 32, 2, 5), 'misc': (22, 32, 4, 4),
}


def hx(c):
    c = c.lstrip('#')
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


class Canvas(object):
    def __init__(self, w, h, bg='#000000'):
        self.w = w
        self.h = h
        r, g, b = hx(bg)
        self.px = bytearray([r, g, b, 255] * (w * h))

    def set(self, x, y, color):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        r, g, b = hx(color)
        i = (y * self.w + x) * 4
        self.px[i:i + 4] = bytes([r, g, b, 255])

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def row(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def col(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def to_png(self):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            raw += self.px[y * self.w * 4:(y + 1) * self.w * 4]

        def chunk(tag, data):
            c = struct.pack('>I', len(data)) + tag + data
            return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

        return (b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', struct.pack('>IIBBBBB', self.w, self.h, 8, 6, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
                + chunk(b'IEND', b''))


def build():
    c = Canvas(RES, RES, '#101014')

    # 1) 纯色色板
    for name, (col, row) in SWATCH_AT.items():
        c.rect(col * 8, row * 8, 8, 8, PALETTE[name])

    # 2) 细节块
    u, v, w, h = PATCHES['recvSide']
    c.rect(u, v, w, h, '#17171A')
    c.row(u, v, w, '#22222A')
    c.row(u, v + 3, w, '#0A0A0C')
    c.rect(u + 2, v + 1, 4, 1, '#0A0A0C')
    c.rect(u + 5, v + 2, 3, 1, '#2E2E36')
    for p in ((0, 1), (7, 1), (0, 2), (7, 2)):
        c.set(u + p[0], v + p[1], '#5A5A64')

    u, v, w, h = PATCHES['recvTop']
    c.rect(u, v, w, h, '#1C1C22')
    c.col(u, v, h, '#26262C')
    c.col(u + 3, v, h, '#26262C')
    c.col(u + 1, v, h, '#0C0C0F')
    c.col(u + 2, v, h, '#0C0C0F')

    u, v, w, h = PATCHES['midSide']
    c.rect(u, v, w, h, '#17171A')
    c.row(u, v, w, '#22222A')
    c.row(u, v + 3, w, '#0A0A0C')
    for x in (1, 3, 5):
        c.col(u + x, v + 1, 2, '#0A0A0C')
    c.set(u + 6, v + 1, '#5A5A64')

    u, v, w, h = PATCHES['rivSide']
    c.rect(u, v, w, h, '#1A1A1F')
    c.rect(u + 1, v + 1, 3, 3, '#101014')
    c.row(u, v + 2, w, '#22222A')
    for p in ((0, 0), (4, 0), (0, 4), (4, 4)):
        c.set(u + p[0], v + p[1], '#5A5A64')

    u, v, w, h = PATCHES['magSide']
    c.rect(u, v, w, h, '#2F2F36')
    c.col(u, v, h, '#3B3B43')
    c.col(u + 3, v, h, '#232329')
    c.row(u, v + 1, w, '#43434C')
    c.row(u, v + 3, w, '#43434C')
    c.row(u, v + 5, w, '#0C0C0F')
    c.set(u + 1, v + 2, '#54545E')

    u, v, w, h = PATCHES['gripSide']
    c.rect(u, v, w, h, '#0F0F12')
    c.row(u, v, w, '#17171A')
    for p in ((1, 0), (0, 1), (2, 1), (1, 2), (0, 3), (2, 3), (1, 4)):
        c.set(u + p[0], v + p[1], '#1A1A20')

    u, v, w, h = PATCHES['scopeSide']
    c.rect(u, v, w, h, '#1A1A1F')
    c.row(u, v, w, '#2A2A31')
    c.row(u, v + 1, w, '#0C0C0F')
    c.col(u + 1, v, h, '#26262C')
    c.col(u + 5, v, h, '#26262C')

    u, v, w, h = PATCHES['scopeFront']
    c.rect(u, v, w, h, '#0C0C0F')
    c.rect(u + 1, v + 1, 2, 1, '#3E8FBE')
    c.rect(u, v + 2, 4, 1, '#17171A')
    c.set(u + 2, v + 2, '#2E5C7A')
    for p in ((0, 1), (3, 1), (1, 0), (2, 0)):
        c.set(u + p[0], v + p[1], '#1A1A1F')

    u, v, w, h = PATCHES['camSide']
    c.rect(u, v, w, h, '#2A2A31')
    for p in ((0, 0), (2, 0), (0, 2), (2, 2)):
        c.set(u + p[0], v + p[1], '#16161A')
    for p in ((1, 0), (1, 2), (0, 1), (2, 1)):
        c.set(u + p[0], v + p[1], '#3A3A44')
    c.set(u + 1, v + 1, '#6E6E78')

    u, v, w, h = PATCHES['buttSide']
    c.rect(u, v, w, h, '#17171A')
    c.row(u, v, w, '#22222A')
    c.row(u, v + 4, w, '#0A0A0C')
    c.rect(u + 2, v + 3, 2, 1, '#0A0A0C')
    c.set(u, v + 1, '#2E2E36')
    c.set(u + 5, v + 2, '#2E2E36')
    c.col(u + 5, v, h, '#121216')

    u, v, w, h = PATCHES['railTop']
    c.rect(u, v, w, h, '#3B3B43')
    for i in range(0, 14, 2):
        c.row(u, v + i, w, '#202027')
    c.col(u, v, h, '#4A4A54')
    c.col(u + 1, v, h, '#33333B')

    u, v, w, h = PATCHES['limbTop']
    c.rect(u, v, w, h, '#1C1C22')
    c.row(u, v, w, '#2A2A31')
    c.row(u, v + 1, w, '#0C0C0F')
    c.col(u + 5, v, h, '#101014')
    c.set(u + 4, v, '#33333B')

    u, v, w, h = PATCHES['boltSide']
    c.rect(u, v, w, h, '#2E2E34')
    c.rect(u, v, 5, 1, '#3E3E46')
    c.set(u + 6, v, '#6E6E78')

    u, v, w, h = PATCHES['riserSide']
    c.rect(u, v, w, h, '#17171A')
    c.col(u, v, h, '#22222A')
    c.set(u + 1, v + 1, '#5A5A64')
    c.set(u + 1, v + 3, '#5A5A64')
    c.set(u + 1, v + 4, '#0A0A0C')

    u, v, w, h = PATCHES['misc']
    c.rect(u, v, w, h, '#17171A')
    c.rect(u + 1, v + 1, 2, 2, '#2E2E36')
    c.set(u + 1, v + 1, '#C9C2AE')

    return c.to_png()


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    png = build()

    preview = os.path.join(root, 'build', 'bbtex', 'crossbow_geo.png')
    os.makedirs(os.path.dirname(preview), exist_ok=True)
    with open(preview, 'wb') as fh:
        fh.write(png)

    asset = os.path.join(root, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                         'textures', 'item', 'crossbow_geo.png')
    os.makedirs(os.path.dirname(asset), exist_ok=True)
    with open(asset, 'wb') as fh:
        fh.write(png)

    b64 = base64.b64encode(png).decode('ascii')
    js = ("(function () {\n"
          "  Texture.all.slice().forEach(function (t) { if (typeof t.remove === 'function') { t.remove(false); } });\n"
          "  var t = Texture.fromDataURL('data:image/png;base64,%s', 'crossbow_geo', true);\n"
          "  try { t.setAsDefaultTexture(); } catch (e) { }\n"
          "  Cube.all.forEach(function (c) { c.texture = 0; });\n"
          "  Canvas.updateAll();\n"
          "  return JSON.stringify({ tex: Texture.all.map(function (x) { return x.name + ' ' + x.width + 'x' + x.height; }), "
          "cube_tex: Cube.all.length ? Cube.all[0].texture : null });\n"
          "})();\n") % b64
    js_path = os.path.join(root, 'tools', 'bb_texture.js')
    with open(js_path, 'w', encoding='utf-8') as fh:
        fh.write(js)

    print('png  -> %s (%d bytes)' % (asset, len(png)))
    print('preview -> %s' % preview)
    print('js   -> %s (%d bytes)' % (js_path, len(js)))


if __name__ == '__main__':
    main()
