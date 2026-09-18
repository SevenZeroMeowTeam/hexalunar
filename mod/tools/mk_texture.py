#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成十字弩的 64x64 贴图，并输出一个把贴图导入 Blockbench 的 JS。

贴图布局必须与 tools/bb_model.js 里的 PAL / FACE 表保持一致：
  0..15 行  16 个 8x8 纯色材质格（模型面采样格子中心 1 texel）
  16..47 行 手工细节块：机匣侧面 / 弓头 / 皮轨齿 / 弹匣筋 / 握把防滑纹 / 镜筒 / 凸轮 / 弓臂 / 枪托 / 机匣顶面
产物：
  src/main/resources/assets/hexalunar_calamity/textures/item/crossbow_geo.png
  模型/_tex_preview.png    (8 倍放大预览)
  tools/bb_teximport.js    (内嵌 data URL，导入 Blockbench)
"""
import base64
import io
import os
import random

from PIL import Image, ImageDraw

W = H = 64

PALETTE = [
    ('body_main', '#1a1a20'), ('body_hi', '#2c2c34'), ('body_dark', '#0e0e12'), ('metal', '#45454e'),
    ('rubber', '#121216'), ('string', '#cfc6ad'), ('glass', '#2e6d8e'), ('steel', '#7c7c88'),
    ('limb', '#17171b'), ('cam', '#2a2a31'), ('limb_hi', '#37373f'), ('accent', '#8a1e1e'),
    ('scope_body', '#1e1e24'), ('bolt', '#4a4a52'), ('glass_dk', '#16384a'), ('white', '#a8a8b0'),
]

FACE = {
    'panel': (0, 16, 11, 5), 'riser': (12, 16, 5, 5), 'riserN': (18, 16, 5, 5),
    'railTop': (24, 16, 2, 11), 'mag': (28, 16, 4, 5), 'magN': (33, 16, 4, 2),
    'grip': (38, 16, 3, 6), 'tube': (42, 16, 7, 2), 'cam': (50, 16, 3, 3),
    'limb': (54, 16, 9, 2), 'bolt': (0, 22, 14, 1), 'stock': (16, 22, 4, 3),
    'receiverTop': (21, 22, 4, 11), 'glassFx': (52, 20, 3, 2),
}


def rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def build():
    img = Image.new('RGBA', (W, H), rgb('#0a0a0c'))
    d = ImageDraw.Draw(img)
    rnd = random.Random(20260917)

    def rect(x, y, w, h, c):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=c if isinstance(c, tuple) else rgb(c))

    def vgrad(x, y, w, h, c1, c2):
        a, b = rgb(c1), rgb(c2)
        for j in range(h):
            t = 0 if h == 1 else j / (h - 1)
            col = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))
            d.rectangle([x, y + j, x + w - 1, y + j], fill=col)

    def speck(x, y, w, h, c, prob):
        col = rgb(c)
        for j in range(h):
            for i in range(w):
                if rnd.random() < prob:
                    d.point((x + i, y + j), fill=col)

    def noisify(x, y, w, h, amp):
        for j in range(h):
            for i in range(w):
                r, g, b, a = img.getpixel((x + i, y + j))
                k = int(rnd.uniform(-amp, amp))
                img.putpixel((x + i, y + j),
                             (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)), a))

    def outline(x, y, w, h, c='#000000'):
        rect(x, y, w, 1, c)
        rect(x, y + h - 1, w, 1, c)
        rect(x, y, 1, h, c)
        rect(x + w - 1, y, 1, h, c)

    for i, (_, col) in enumerate(PALETTE):
        rect((i % 8) * 8, (i // 8) * 8, 8, 8, col)
        noisify((i % 8) * 8, (i // 8) * 8, 8, 8, 5)

    rect(0, 16, 11, 5, '#1c1c22')
    vgrad(0, 16, 11, 2, '#26262e', '#1c1c22')
    rect(0, 20, 11, 1, '#101014')
    for x in range(1, 10, 2):
        rect(x, 17, 1, 3, '#0b0b0e')
    rect(2, 18, 2, 1, '#5a5a66')
    rect(8, 18, 1, 1, '#5a5a66')
    outline(0, 16, 11, 5)

    rect(12, 16, 5, 5, '#181820')
    vgrad(12, 16, 5, 2, '#24242c', '#181820')
    rect(12, 20, 5, 1, '#0d0d11')
    rect(13, 19, 3, 1, '#3d3d47')
    outline(12, 16, 5, 5)

    rect(18, 16, 5, 5, '#131319')
    rect(20, 17, 1, 3, '#2e2e36')
    outline(18, 16, 5, 5)

    rect(24, 16, 2, 11, '#3c3c45')
    for y in range(0, 11, 2):
        rect(24, 16 + y, 2, 1, '#5d5d69')
    outline(24, 16, 2, 11)

    rect(28, 16, 4, 5, '#22222a')
    vgrad(28, 16, 2, 5, '#2a2a33', '#16161c')
    for y in range(0, 5, 2):
        rect(28, 16 + y, 4, 1, '#101015')
    outline(28, 16, 4, 5)

    rect(33, 16, 4, 2, '#1d1d24')
    rect(33, 17, 4, 1, '#0f0f13')
    outline(33, 16, 4, 2)

    rect(38, 16, 3, 6, '#141418')
    speck(38, 16, 3, 6, '#24242a', 0.45)
    speck(38, 16, 3, 6, '#0a0a0c', 0.35)
    outline(38, 16, 3, 6)

    vgrad(42, 16, 7, 2, '#2a2a32', '#141419')
    for x in (42, 45, 48):
        rect(x, 16, 1, 2, '#4a4a55')
    outline(42, 16, 7, 2)

    rect(50, 16, 3, 3, '#31313a')
    rect(51, 16, 1, 3, '#15151a')
    rect(50, 17, 3, 1, '#15151a')
    d.point((50, 16), fill=rgb('#6a6a76'))
    d.point((52, 18), fill=rgb('#6a6a76'))
    outline(50, 16, 3, 3)

    vgrad(54, 16, 9, 2, '#26262d', '#101014')
    rect(54, 16, 9, 1, '#33333c')
    rect(54, 17, 9, 1, '#0d0d10')
    outline(54, 16, 9, 2)

    vgrad(0, 22, 14, 1, '#5b5b66', '#33333b')
    rect(0, 22, 2, 1, '#8a8a96')

    rect(16, 22, 4, 3, '#20202a')
    vgrad(16, 22, 4, 1, '#2c2c36', '#20202a')
    rect(16, 24, 4, 1, '#121218')
    for x in range(1, 4):
        rect(16 + x, 23, 1, 1, '#0e0e12')
    outline(16, 22, 4, 3)

    rect(21, 22, 4, 11, '#1d1d23')
    vgrad(21, 22, 4, 2, '#2a2a32', '#1d1d23')
    for y in range(0, 11, 3):
        rect(21, 22 + y, 4, 1, '#101015')
    rect(22, 26, 2, 3, '#0c0c10')
    outline(21, 22, 4, 11)

    vgrad(52, 20, 3, 2, '#7fc6e4', '#245f80')
    d.point((52, 20), fill=rgb('#d8f2ff'))

    return img


JS_TEMPLATE = """(function () {
var data = 'data:image/png;base64,%s'.split('~').join('%s');
Texture.all.slice().forEach(function (t) { if (t.remove) t.remove(); });
var tex = new Texture({ name: 'crossbow', width: %d, height: %d });
tex.add();
tex.fromDataURL(data, { name: 'crossbow', width: %d, height: %d, particle: false });
tex.uv_width = %d;
tex.uv_height = %d;
tex.setAsDefaultTexture();
tex.apply();
Cube.all.forEach(function (c) { c.texture = 0; });
Canvas.updateAll();
if (typeof updateUVEditor === 'function') updateUVEditor();
var d = tex.ctx.getImageData(3, 3, 1, 1).data;
return JSON.stringify({
  canvas: tex.canvas.width + 'x' + tex.canvas.height,
  uv: tex.getUVWidth() + 'x' + tex.getUVHeight(),
  px_sample: [d[0], d[1], d[2], d[3]],
  default_tex: Texture.getDefault() ? Texture.getDefault().name : null,
  cubes: Cube.all.length
}, null, 1);
})();
"""


def main():
    img = build()
    out_png = os.path.join('src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                           'textures', 'item', 'crossbow_geo.png')
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img.save(out_png)
    img.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join('模型', '_tex_preview.png'))

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    print('png ->', out_png, os.path.getsize(out_png), 'bytes;  b64', len(b64), 'chars')

    with open(os.path.join('tools', 'bb_teximport.js'), 'w', encoding='utf-8') as fh:
        fh.write(JS_TEMPLATE % (b64.replace('/', '~'), '/', W, H, W, H, W, H))
    print('js  -> tools/bb_teximport.js')


if __name__ == '__main__':
    main()
