#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在 Blockbench 当前工程里摆相机 → 截图存盘（看细部用）。

用法::

    python tools/ak_bb_shot.py px,py,pz tx,ty,tz 输出名 [orthographic|perspective]

例（枪口正前方看膛孔/膛线）::

    python tools/ak_bb_shot.py 0,1.75,-26 0,1.75,-11 _ak_muzzle.png perspective
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from bbmcp import Mcp                                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTDIR = os.path.join(ROOT, 'build', 'bbshots')


def newest():
    if not os.path.isdir(SHOTDIR):
        return None
    files = [os.path.join(SHOTDIR, f) for f in os.listdir(SHOTDIR) if f.endswith('.png')]
    return max(files, key=os.path.getmtime) if files else None


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    pos = [float(v) for v in argv[0].split(',')]
    tgt = [float(v) for v in argv[1].split(',')]
    out = os.path.join(ROOT, 'build', argv[2])
    proj = argv[3] if len(argv) > 3 else 'perspective'
    mcp = Mcp().connect()
    mcp.call('set_camera_angle', {'position': pos, 'target': tgt, 'projection': proj})
    mcp.call('capture_screenshot', {})
    src = newest()
    if not src:
        print('没拿到截图')
        return 1
    shutil.copyfile(src, out)
    print('->', os.path.basename(out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
