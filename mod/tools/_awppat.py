# -*- coding: utf-8 -*-
"""打印参考贴图某一小块（默认机匣侧面那一块）的字符图，用来看清图案结构/周期。

用法: python tools\_awppat.py [x0 y0 x1 y1]
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, '模型', 'AWP_Printstream_Minecraft', 'awp_printstream.png')

a = [int(v) for v in sys.argv[1:5]] or [0, 0, 24, 16]
x0, y0, x1, y1 = a
img = Image.open(TEX).convert('RGBA')
print('贴图 %s  区域 (%d,%d)-(%d,%d)' % (img.size, x0, y0, x1, y1))
print('    ' + ''.join(str(x % 10) for x in range(x0, x1)))
for y in range(y0, y1):
    row = ''
    for x in range(x0, x1):
        r, g, b, al = img.getpixel((x, y))
        v = (r + g + b) / 3.0
        row += '#' if v < 96 else ('+' if v < 168 else ('.' if v < 224 else ' '))
    print('%3d %s' % (y, row))
