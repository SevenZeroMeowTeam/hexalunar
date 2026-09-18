"""只渲染某根骨骼（含子骨骼）的方块，放大看部件形状。

用法: python tools\_boneview.py <geo.json> <png> <骨骼名> [前缀]
  产出 build/<前缀>_<view>.png
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = [('side', 90.0, 6.0), ('iso', 215.0, 22.0), ('top', 0.0, 74.0)]


def subset(geo_path, dst, bone_name):
    with open(geo_path, encoding='utf-8') as fh:
        g = json.load(fh)
    bones = g['minecraft:geometry'][0]['bones']
    for b in bones:
        if b['name'] != bone_name:
            b.pop('cubes', None)
    with open(dst, 'w', encoding='utf-8') as fh:
        json.dump(g, fh, ensure_ascii=False)
    return [b['name'] for b in bones if b.get('cubes')]


def main(argv):
    geo, tex, bone = argv[1], argv[2], argv[3]
    prefix = argv[4] if len(argv) > 4 else ('_bone_%s' % bone)
    sub = os.path.join(ROOT, 'build', '_bone_%s.geo.json' % bone)
    print('kept cubes on:', subset(os.path.join(ROOT, geo), sub, bone))
    outs = []
    for name, yaw, pitch in VIEWS:
        out = os.path.join(ROOT, 'build', '%s_%s.png' % (prefix, name))
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'geo_texview.py'),
                        sub, os.path.join(ROOT, tex), out,
                        '--yaw', str(yaw), '--pitch', str(pitch),
                        '--size', '900', '--zoom', '1.6'], check=True,
                       stdout=subprocess.DEVNULL)
        outs.append(os.path.relpath(out, ROOT))
    print('wrote', ', '.join(outs))


if __name__ == '__main__':
    main(sys.argv)
