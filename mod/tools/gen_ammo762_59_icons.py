#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""画 7.62x59（莫辛-纳甘）弹药与弹盒的 16×16 物品图标。

与 .338 那套的区别：弹壳更长、口径更细、弹头是尖头（.338 更粗更短），
弹盒沿用军绿铁盒但改一条**红棕色标签带**（与 7.62x39 的步枪弹盒区分开）。

用法: python tools\\gen_ammo762_59_icons.py
产出：textures/item/ammo_762_59.png、textures/item/ammo_box_762_59.png
      （放大预览另存 build/_ammo76259_*.png）
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXDIR = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                      'textures', 'item')
PREVDIR = os.path.join(ROOT, 'build')

BRASS_HI = (236, 198, 116)
BRASS = (196, 150, 72)
BRASS_LO = (136, 98, 42)
STEEL = (170, 174, 180)
STEEL_LO = (98, 102, 108)
TIP = (70, 74, 80)
OUTLINE = (30, 28, 26)
OLIVE = (92, 96, 62)
OLIVE_HI = (126, 132, 86)
OLIVE_LO = (60, 64, 40)
LABEL = (138, 58, 40)
LABEL_HI = (176, 82, 56)


def px(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c + (255,))


def cartridge(img, x0, y0, length=12):
    """一枚 7.62x59：细长弹壳 + 尖弹头（往右上画）。"""
    for i in range(length):
        x, y = x0 + i, y0 - i
        px(img, x, y, BRASS)
        px(img, x, y - 1, BRASS_HI if i % 4 else BRASS)
        px(img, x + 1, y, BRASS_LO)
    # 肩部收细 + 尖头（比 .338 更长更尖）
    tx, ty = x0 + length, y0 - length
    px(img, tx, ty, BRASS_LO)
    px(img, tx, ty - 1, STEEL_LO)
    px(img, tx + 1, ty, STEEL)
    px(img, tx + 1, ty - 1, STEEL)
    px(img, tx + 2, ty - 1, TIP)
    # 底缘
    px(img, x0 - 1, y0, BRASS_HI)
    px(img, x0, y0 + 1, BRASS_LO)
    px(img, x0 - 1, y0 + 1, BRASS)


def ammo_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    cartridge(img, 2, 13, 11)          # 前一枚
    cartridge(img, 5, 15, 10)          # 后一枚（错开，看起来像一排）
    return img


def box_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for x in range(2, 14):                        # 箱体正面
        for y in range(6, 15):
            px(img, x, y, OLIVE)
    for x in range(3, 14):                        # 顶面
        for y in range(4, 7):
            px(img, x, y, OLIVE_HI)
    for x in range(2, 14):                        # 描边
        px(img, x, 5, OUTLINE)
        px(img, x, 14, OUTLINE)
    for y in range(5, 15):
        px(img, 2, y, OUTLINE)
        px(img, 13, y, OUTLINE)
    for x in range(3, 14):                        # 顶面前沿
        px(img, x, 6, OLIVE_LO)
    for (x, y) in ((5, 9), (8, 9), (11, 9)):      # 盒盖上的三发（黄铜小点）
        px(img, x, y, BRASS_HI)
        px(img, x, y + 1, BRASS_LO)
    for x in range(4, 12):                        # ★ 红棕标签带（7.62x59 专属）
        px(img, x, 12, LABEL)
    for x in range(4, 12):
        px(img, x, 11, LABEL_HI)
    return img


def save(img, name):
    dst = os.path.join(TEXDIR, name)
    img.save(dst)
    img.resize((img.width * 12, img.height * 12), Image.NEAREST).save(
        os.path.join(PREVDIR, '_ammo76259_' + name))
    print('wrote %-26s (%dx%d)  预览 build\\_ammo76259_%s'
          % (os.path.relpath(dst, ROOT), img.width, img.height, name))


if __name__ == '__main__':
    save(ammo_icon(), 'ammo_762_59.png')
    save(box_icon(), 'ammo_box_762_59.png')
