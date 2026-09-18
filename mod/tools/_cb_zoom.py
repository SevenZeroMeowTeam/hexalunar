"""只保留十字弩"弓臂 + 弦"部件的小图，放大渲染，用于判断弦是否横向超出弓臂。

用法: python tools/_cb_zoom.py <in.geo> <tag>
  产出 build/_cbz_<tag>_<view>.png
"""
import json
import os
import subprocess
import sys

KEEP = ('prod_left', 'prod_right', 'string_left', 'string_right', 'nock')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = [('back', 0.0, 0.0), ('top', 0.0, 89.0), ('side', 90.0, 0.0), ('iso', 205.0, -14.0)]


def subset(src, dst):
    """保留整条骨骼链（父骨骼仍需要，否则子骨骼解析不出来），但只留 KEEP 里骨骼的方块。"""
    g = json.load(open(src, encoding='utf-8'))
    bones = g['minecraft:geometry'][0]['bones']
    for b in bones:
        if b['name'] not in KEEP:
            b.pop('cubes', None)
    g['minecraft:geometry'][0]['bones'] = bones
    json.dump(g, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    return [b['name'] for b in bones]


def main(argv):
    src, tag = argv[1], argv[2]
    sub = os.path.join(ROOT, 'build', '_cbz_%s.geo.json' % tag)
    kept = subset(src, sub)
    print('kept:', kept)
    for name, yaw, pitch in VIEWS:
        out = os.path.join(ROOT, 'build', '_cbz_%s_%s.png' % (tag, name))
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'geo_texview.py'),
                        sub, os.path.join(ROOT, 'build', 'crossbow_v2.png'), out,
                        '--yaw', str(yaw), '--pitch', str(pitch),
                        '--size', '1100', '--zoom', '2.2'], check=True)


if __name__ == '__main__':
    main(sys.argv)
