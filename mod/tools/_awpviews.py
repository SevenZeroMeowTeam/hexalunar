# -*- coding: utf-8 -*-
"""AWP 模型离线出图（右侧 / 左侧 / 俯视 / 仰视 / 等轴）—— 不开游戏就能核对形状。

用法::

    python tools/_awpviews.py <tag>
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

GEO = 'src/main/resources/assets/hexalunar_calamity/geo/awp.geo.json'
TEX = 'src/main/resources/assets/hexalunar_calamity/textures/models/awp_geo.png'
VIEWS = (('side', 90.0, 0.0), ('side_l', -90.0, 0.0), ('top', 0.0, 90.0),
         ('bottom', 0.0, -90.0), ('iso', 215.0, 20.0))


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'cur'
    geo = sys.argv[2] if len(sys.argv) > 2 else GEO
    tex = sys.argv[3] if len(sys.argv) > 3 else TEX
    for name, yaw, pitch in VIEWS:
        out = os.path.join(ROOT, 'build', '_awp_%s_%s.png' % (tag, name))
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'geo_texview.py'),
                        geo, tex, os.path.relpath(out, ROOT),
                        '--yaw', str(yaw), '--pitch', str(pitch),
                        '--size', '1500', '--zoom', '1.0'],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        print('wrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
