"""按**比例**裁图放大（不用先知道分辨率）。

用法: python tools\_crop3.py <src.png> <out.png> fx0 fy0 fx1 fy1 [zoom]
"""
import sys

from PIL import Image


def main(argv):
    src, out = argv[1], argv[2]
    fx0, fy0, fx1, fy1 = (float(v) for v in argv[3:7])
    zoom = float(argv[7]) if len(argv) > 7 else 4.0
    im = Image.open(src).convert('RGB')
    w, h = im.size
    box = (int(w * fx0), int(h * fy0), int(w * fx1), int(h * fy1))
    im = im.crop(box)
    cw, ch = im.size
    im = im.resize((int(cw * zoom), int(ch * zoom)), Image.NEAREST)
    im.save(out)
    print('%dx%d  crop%s  zoom %.1f -> %s' % (w, h, box, zoom, out))


if __name__ == '__main__':
    main(sys.argv)
