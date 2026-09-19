"""裁图 + 放大（看用户截图里的细节）。

用法: python tools\_crop2.py <src.png> <out.png> x0 y0 x1 y1 [zoom]
"""
import sys

from PIL import Image


def main(argv):
    src, out = argv[1], argv[2]
    x0, y0, x1, y1 = (int(v) for v in argv[3:7])
    zoom = float(argv[7]) if len(argv) > 7 else 4.0
    im = Image.open(src).convert('RGB').crop((x0, y0, x1, y1))
    w, h = im.size
    im = im.resize((int(w * zoom), int(h * zoom)), Image.NEAREST)
    im.save(out)
    print('%s -> %s  (%dx%d, zoom %.1f)' % (src, out, w, h, zoom))


if __name__ == '__main__':
    main(sys.argv)
