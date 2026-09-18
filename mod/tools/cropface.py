"""按 geo.json 里某个方块某个面的 UV 矩形裁剪贴图，放大输出（核对逐面细节）。

用法: python tools/cropface.py <geo.json> <png> <cube_name> <face> <out> [scale]
  cube_name 形如 body/main_a（骨骼/方块名），face = north/south/east/west/up/down
"""
import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    geo_p, png_p, want, face, out = argv[1], argv[2], argv[3], argv[4], argv[5]
    sc = int(argv[6]) if len(argv) > 6 else 4
    bones = json.load(open(os.path.join(ROOT, geo_p), encoding='utf-8'))['minecraft:geometry'][0]['bones']
    for b in bones:
        for i, c in enumerate(b.get('cubes', [])):
            full = '%s/%s' % (b['name'], c.get('name', ''))
            if full == want or c.get('name') == want or want == '%s:%d' % (b['name'], i):
                u = c['uv'][face]
                x, y = int(u['uv'][0]), int(u['uv'][1])
                w, h = int(u['uv_size'][0]), int(u['uv_size'][1])
                im = Image.open(os.path.join(ROOT, png_p)).convert('RGB')
                c2 = im.crop((x, y, x + w, y + h))
                c2 = c2.resize((c2.width * sc, c2.height * sc), Image.NEAREST)
                c2.save(os.path.join(ROOT, out))
                print('%s %s uv=(%d,%d) %dx%d -> %s %dx%d'
                      % (full, face, x, y, w, h, out, c2.width, c2.height))
                return
    print('找不到 %s' % want)


if __name__ == '__main__':
    main(sys.argv)
