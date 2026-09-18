# -*- coding: utf-8 -*-
"""看 bbmodel 里 mesh 面的 UV 到底存在哪个空间（0..1 / 0..16 / 0..512 像素）。

用法: python tools\\_uvprobe.py "模型\\十字弩_v2.bbmodel"
      python tools\\_uvprobe.py "模型\\akm.bbmodel"
"""
import base64
import io
import json
import sys

from PIL import Image


def main(argv):
    path = argv[1]
    data = json.loads(io.open(path, encoding='utf-8').read())
    print('== %s ==' % path)
    print('resolution =', data.get('resolution'))
    for i, e in enumerate(data.get('elements', [])[:2]):
        print('-- element[%d] name=%s type=%s verts=%d faces=%d' % (
            i, e.get('name'), e.get('type'), len(e.get('vertices', {})), len(e.get('faces', {}))))
        for j, (fn, f) in enumerate(list(e.get('faces', {}).items())[:3]):
            print('   face %-8s keys=%s' % (fn, sorted(f.keys())))
            print('      uv=%s' % f.get('uv'))
            print('      vertices=%s' % f.get('vertices'))
            pts = [e['vertices'][v] for v in (f.get('vertices') or []) if v in e.get('vertices', {})]
            if pts:
                print('      位置=%s' % [[round(c, 2) for c in p] for p in pts])
    for t in data.get('textures', []):
        src = t.get('source') or ''
        if src.startswith('data:image'):
            im = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1])))
            print('贴图 %s = %s  uv_width=%s' % (t.get('name'), im.size, t.get('uv_width')))


if __name__ == '__main__':
    main(sys.argv)
