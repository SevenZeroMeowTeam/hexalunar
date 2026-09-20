# -*- coding: utf-8 -*-
"""裁剪/放大用户截图（QQ 粘贴的标注图），坐标按「显示宽度 768」给，自动换算到原图。

用法: python tools/_zoomshot.py <png> <x0,y0,x1,y1> <out> [scale] [--refw 768]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    src, box, out = sys.argv[1], sys.argv[2], sys.argv[3]
    sc = int(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else 3
    refw = 768.0
    if '--refw' in sys.argv:
        refw = float(sys.argv[sys.argv.index('--refw') + 1])
    p = src if os.path.isabs(src) else os.path.join(ROOT, src)
    im = Image.open(p).convert('RGB')
    k = im.width / refw
    x0, y0, x1, y1 = [float(v) for v in box.split(',')]
    c = im.crop((int(x0 * k), int(y0 * k), int(x1 * k), int(y1 * k)))
    c = c.resize((c.width * sc, c.height * sc), Image.LANCZOS)
    dst = out if os.path.isabs(out) else os.path.join(ROOT, out)
    c.save(dst)
    print('src %dx%d  k=%.2f  ->  %s  %dx%d'
          % (im.width, im.height, k, out, c.width, c.height))


if __name__ == '__main__':
    main()
