"""画两个瞄具物品的 16x16 图标（红点 / 4 倍镜），直接写进资源目录。

用法: python tools\gen_sight_icons.py
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'textures', 'item')
S = 16

STEEL = (58, 60, 66, 255)
STEEL_D = (34, 35, 40, 255)
STEEL_L = (96, 100, 108, 255)
GLASS = (60, 132, 156, 255)
GLASS_L = (128, 200, 214, 255)
RED = (255, 66, 44, 255)
RED_L = (255, 200, 190, 255)


def dot_icon():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 底座
    d.rectangle([1, 11, 14, 14], fill=STEEL_D)
    d.rectangle([1, 11, 14, 12], fill=STEEL)
    # 立柱
    d.rectangle([6, 8, 9, 11], fill=STEEL)
    # 护罩（开口方框）
    d.rectangle([2, 3, 13, 8], outline=STEEL, width=1)
    d.rectangle([2, 3, 13, 3], fill=STEEL_L)
    # 镜片
    d.rectangle([4, 4, 11, 7], fill=GLASS)
    d.rectangle([4, 4, 11, 4], fill=GLASS_L)
    # 红点
    d.rectangle([7, 5, 8, 6], fill=RED)
    d.rectangle([7, 5, 7, 5], fill=RED_L)
    return im


def scope_icon():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 底座 + 两个镜环座
    d.rectangle([2, 11, 13, 14], fill=STEEL_D)
    d.rectangle([4, 9, 5, 11], fill=STEEL)
    d.rectangle([10, 9, 11, 11], fill=STEEL)
    # 镜筒
    d.rectangle([4, 4, 11, 9], fill=STEEL, outline=STEEL_D)
    d.rectangle([4, 4, 11, 5], fill=STEEL_L)
    # 物镜（前端一圈玻璃）
    d.rectangle([11, 4, 12, 9], fill=GLASS)
    d.rectangle([11, 5, 11, 8], fill=GLASS_L)
    # 目镜
    d.rectangle([3, 5, 4, 8], fill=STEEL_D)
    # 调节钮
    d.rectangle([7, 2, 8, 4], fill=STEEL_L)
    return im


def main():
    for name, im in (('red_dot_sight', dot_icon()), ('scope_4x', scope_icon())):
        path = os.path.join(OUT, name + '.png')
        im.save(path)
        print('wrote', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    main()
