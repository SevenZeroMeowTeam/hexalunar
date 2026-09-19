# -*- coding: utf-8 -*-
"""画 .338 弹药与弹盒的 16×16 物品图标（直接写进 mod 资源目录）。

用法: python tools\gen_ammo338_icons.py
产出（放大预览另存 build/_ammo338_*.png，方便肉眼核对）：
  textures/item/ammo_338.png
  textures/item/ammo_box_sniper.png
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXDIR = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                      'textures', 'item')
PREVDIR = os.path.join(ROOT, 'build')

BRASS_HI = (232, 196, 112)
BRASS = (198, 152, 74)
BRASS_LO = (140, 100, 44)
STEEL = (168, 172, 178)
STEEL_LO = (96, 100, 106)
TIP = (74, 78, 84)
OUTLINE = (28, 26, 24)
OLIVE = (92, 96, 62)
OLIVE_HI = (124, 130, 84)
OLIVE_LO = (62, 66, 42)


def px(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c + (255,))


def cartridge(img, x0, y0, length=11):
    """一枚 .338 弹：从 (x0,y0) 往右上画（弹头在右上、底缘在左下）。"""
    for i in range(length):
        x, y = x0 + i, y0 - i
        # 弹壳本体（2 像素宽）
        px(img, x, y, BRASS)
        px(img, x, y - 1, BRASS_HI if i % 3 else BRASS)
        px(img, x + 1, y, BRASS_LO)
    # 弹头（顶端 3 像素、颜色更冷、更尖）
    tx, ty = x0 + length, y0 - length
    px(img, tx, ty, STEEL)
    px(img, tx, ty - 1, STEEL_LO)
    px(img, tx + 1, ty, TIP)
    px(img, tx, ty + 1, STEEL_LO)
    # 底缘（左下角一圈亮边）
    px(img, x0 - 1, y0, BRASS_HI)
    px(img, x0, y0 + 1, BRASS_LO)
    px(img, x0 - 1, y0 + 1, BRASS)


def ammo_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    cartridge(img, 3, 12, 10)          # 前一枚
    cartridge(img, 6, 14, 9)           # 后一枚（错开，看起来像一排）
    return img


def box_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    # 箱体：正面 + 顶面（顶面浅、正面深，黑描边）
    for x in range(2, 14):
        for y in range(6, 15):
            px(img, x, y, OLIVE)
    for x in range(3, 14):
        for y in range(4, 7):
            px(img, x, y, OLIVE_HI)
    for x in range(2, 14):                       # 上下描边
        px(img, x, 5, OUTLINE)
        px(img, x, 14, OUTLINE)
    for y in range(5, 15):
        px(img, 2, y, OUTLINE)
        px(img, 13, y, OUTLINE)
    for x in range(3, 14):                       # 顶面前沿
        px(img, x, 6, OLIVE_LO)
    # 箱盖上的两发 .338（黄铜小点）
    for (x, y) in ((5, 9), (8, 9), (11, 9)):
        px(img, x, y, BRASS_HI)
        px(img, x, y + 1, BRASS_LO)
    # 正面一条标签带
    for x in range(4, 12):
        px(img, x, 12, OLIVE_HI)
    return img


def save(img, name):
    dst = os.path.join(TEXDIR, name)
    img.save(dst)
    img.resize((img.width * 12, img.height * 12), Image.NEAREST).save(
        os.path.join(PREVDIR, '_ammo338_' + name))
    print('wrote %-24s (%dx%d)  预览 build\\_ammo338_%s'
          % (os.path.relpath(dst, ROOT), img.width, img.height, name))


if __name__ == '__main__':
    save(ammo_icon(), 'ammo_338.png')
    save(box_icon(), 'ammo_box_sniper.png')
