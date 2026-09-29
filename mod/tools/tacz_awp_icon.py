#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染 TaCZ 枪包的背包 2D 图标（slot 贴图）。

TaCZ 的枪在背包/快捷栏里用低分辨率 2D 贴图（模型只用于手持/世界渲染），
官方推荐 32x32 正方形。这里复用我们的离线基岩模型渲染器 geo_texview，
按 Blockbench「等轴视角右（2:1）」的角度渲一张，再抠成透明、裁切、缩到 32x32。
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geo_texview as gv  # noqa: E402

MOD = os.path.dirname(HERE)
PACK = os.path.join(MOD, 'tacz_pack', 'hexalunar_gun_pack')
GEO = os.path.join(PACK, 'assets', 'hexalunar', 'geo_models', 'gun', 'awp_geo.json')
TEX = os.path.join(PACK, 'assets', 'hexalunar', 'textures', 'gun', 'uv', 'awp.png')
OUT = os.path.join(PACK, 'assets', 'hexalunar', 'textures', 'gun', 'slot', 'awp.png')
OUT_HUD = os.path.join(PACK, 'assets', 'hexalunar', 'textures', 'gun', 'hud', 'awp.png')
PREVIEW = os.path.join(MOD, 'build', '_awp_slot_preview.png')
PREVIEW_HUD = os.path.join(MOD, 'build', '_awp_hud_preview.png')
RAW = os.path.join(MOD, 'build', '_awp_slot_raw.png')
RAW_HUD = os.path.join(MOD, 'build', '_awp_hud_raw.png')
HIDDEN = os.path.join(MOD, 'build', '_awp_slot_geo.json')

# ★ 尺寸必须照官方：slot = 64x64，hud = 180x60（TaCZ 是当贴图直接贴到 HUD 面板上的，
#   尺寸不对就会显示异常）
SIZE = 64
HUD_W, HUD_H = 180, 60
# ★ hud 剪影用官方那个浅灰（实测官方 ai_awp.png 不透明像素众数 = #D4D4D4）
HUD_GRAY = 212
# Blockbench 的「等轴视角右（2:1）」映射到本渲染器的 yaw=225 / pitch=30：
# 枪托在左上、枪口朝右下、镜筒在枪身上方 —— 与 TaCZ 官方 slot 图一致。
YAW, PITCH = 225.0, 30.0
# hud 用正侧视：yaw=90 让枪口朝屏幕左（与官方一致），pitch=0 保证枪身水平。
HUD_YAW, HUD_PITCH = 90.0, 0.0
FILL = 0.94

# 这些组的方块是 TaCZ 的「定位用标记」/运行时才出现的东西，画图标时不能算进去
# （手臂定位组里那两块 12 高的预览方块会把包围盒撑大一倍）。
DROP_CUBES = {'righthand_pos', 'lefthand_pos', 'sight', 'attachment_adapter',
              'muzzle_flash', 'shell', 'bullet_in_mag', 'bullet_in_barrel',
              'camera', 'constraint'}


def strip_geo(src, dst):
    with open(src, encoding='utf-8') as f:
        d = json.load(f)
    dropped = 0
    for b in d['minecraft:geometry'][0]['bones']:
        if b['name'] in DROP_CUBES and b.get('cubes'):
            dropped += len(b['cubes'])
            b['cubes'] = []
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print('剔除 %d 个定位用方块（不参与图标）' % dropped)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_HUD), exist_ok=True)
    strip_geo(GEO, HIDDEN)
    gv.render(HIDDEN, TEX, RAW, yaw=YAW, pitch=PITCH, size=768, zoom=1.0, ss=1)

    im = Image.open(RAW).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    bg = np.array(gv.BG, dtype=np.int16)
    mask = np.abs(a - bg).max(axis=2) > 3
    if not mask.any():
        print('! 渲染结果全是背景色，检查 geo/贴图路径')
        return 1

    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([np.asarray(im)[y0:y1, x0:x1],
                      (mask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    img = Image.fromarray(rgba)

    w, h = img.size
    k = (SIZE * FILL) / max(w, h)
    img = img.resize((max(1, int(round(w * k))), max(1, int(round(h * k)))),
                     Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))
    canvas.save(OUT)
    canvas.resize((SIZE * 8, SIZE * 8), Image.NEAREST).save(PREVIEW)
    print('wrote %s  %dx%d  (裁剪自 %dx%d)' % (
        os.path.relpath(OUT, MOD), SIZE, SIZE, w, h))
    print('预览：%s' % os.path.relpath(PREVIEW, MOD))

    # ── hud：180x60 的纯白侧视剪影 ──
    gv.render(HIDDEN, TEX, RAW_HUD, yaw=HUD_YAW, pitch=HUD_PITCH,
              size=900, zoom=1.0, ss=1)
    him = Image.open(RAW_HUD).convert('RGB')
    ha = np.asarray(him).astype(np.int16)
    hmask = np.abs(ha - bg).max(axis=2) > 3
    if not hmask.any():
        print('! hud 侧视图渲染为空')
        return 1
    hy, hx = np.where(hmask)
    hcrop = hmask[hy.min():hy.max() + 1, hx.min():hx.max() + 1]
    hh, hw = hcrop.shape
    rgba = np.dstack([np.full((hh, hw), HUD_GRAY, np.uint8)] * 3 +
                     [(hcrop * 255).astype(np.uint8)])
    hud = Image.fromarray(rgba)
    hk = min(HUD_W / hw, HUD_H / hh) * 0.96
    hud = hud.resize((max(1, int(hw * hk)), max(1, int(hh * hk))), Image.LANCZOS)
    hcanvas = Image.new('RGBA', (HUD_W, HUD_H), (0, 0, 0, 0))
    hcanvas.paste(hud, ((HUD_W - hud.width) // 2, (HUD_H - hud.height) // 2))
    hcanvas.save(OUT_HUD)
    hcanvas.resize((HUD_W * 3, HUD_H * 3), Image.NEAREST).save(PREVIEW_HUD)
    print('wrote %s  %dx%d  (侧视剪影，裁剪自 %dx%d)' % (
        os.path.relpath(OUT_HUD, MOD), HUD_W, HUD_H, hw, hh))
    print('预览：%s' % os.path.relpath(PREVIEW_HUD, MOD))
    return 0


if __name__ == '__main__':
    sys.exit(main())
