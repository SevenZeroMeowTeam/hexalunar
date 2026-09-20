#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""画 7.62x61（M1 加兰德）弹药与弹盒的 16×16 物品图标。

与 7.62x59（莫辛-纳甘）那套的区别：弹壳**更长更细**（13 像素），
肩部有明显收口的**深色弹颈**（瓶颈弹壳），弹头换成深钢铜尖头；
弹盒沿用军绿铁盒，但标签带改成**钢蓝灰**（区别于 7.62x39 的无带、
7.62x59 的红棕带）。

用法: python tools\\gen_ammo762_61_icons.py
产出：textures/item/ammo_762_61.png、textures/item/ammo_box_762_61.png
      （放大预览另存 build/_ammo76261_*.png）
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXDIR = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                      'textures', 'item')
PREVDIR = os.path.join(ROOT, 'build')

BRASS_HI = (238, 202, 122)
BRASS = (198, 152, 74)
BRASS_LO = (132, 94, 40)
NECK = (104, 72, 32)
COPPER = (176, 108, 62)
TIP = (58, 62, 70)
OUTLINE = (30, 28, 26)
OLIVE = (92, 96, 62)
OLIVE_HI = (126, 132, 86)
OLIVE_LO = (60, 64, 40)
BAND = (84, 104, 128)
BAND_HI = (120, 144, 168)


def px(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c + (255,))


def cartridge(img, x0, y0, length=13):
    """一枚 7.62x61：细长瓶颈弹壳 + 深色尖弹头（往右上画）。

    比 7.62x59 更长（壳身 13 像素）、更细：弹颈只占 2 像素高，
    弹头收成尖头，整体读起来是瓶颈弹壳。
    """
    for i in range(length):
        x, y = x0 + i, y0 - i
        px(img, x, y, BRASS)
        px(img, x, y - 1, BRASS_HI if i % 5 else BRASS)
        px(img, x + 1, y, BRASS_LO)
    # 肩部收口：一段深色弹颈（瓶颈弹壳的特征，比壳身细一像素）
    nx, ny = x0 + length, y0 - length
    px(img, nx, ny, NECK)
    px(img, nx, ny - 1, NECK)
    # 尖弹头：铜被甲 + 深钢弹尖
    px(img, nx + 1, ny, COPPER)
    px(img, nx + 1, ny - 1, TIP)
    # 底缘（抽壳沟）
    px(img, x0 - 1, y0, BRASS_HI)
    px(img, x0, y0 + 1, BRASS_LO)
    px(img, x0 - 1, y0 + 1, BRASS)


def ammo_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    cartridge(img, 1, 14, 13)          # 前一枚（长壳身 13 像素）
    cartridge(img, 4, 15, 10)          # 后一枚（错开，看起来像一排）
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
    for x in range(4, 12):                        # ★ 钢蓝灰标签带（7.62x61 专属）
        px(img, x, 12, BAND)
    for x in range(4, 12):
        px(img, x, 11, BAND_HI)
    return img


def save(img, name):
    dst = os.path.join(TEXDIR, name)
    img.save(dst)
    img.resize((img.width * 12, img.height * 12), Image.NEAREST).save(
        os.path.join(PREVDIR, '_ammo76261_' + name))
    print('wrote %-26s (%dx%d)  预览 build\\_ammo76261_%s'
          % (os.path.relpath(dst, ROOT), img.width, img.height, name))


if __name__ == '__main__':
    save(ammo_icon(), 'ammo_762_61.png')
    save(box_icon(), 'ammo_box_762_61.png')
