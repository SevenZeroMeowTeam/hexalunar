# -*- coding: utf-8 -*-
"""AWP 改动后的三张对照图（整枪 / 扳机区 / 镜座区），每张单独命名。

用法::  python tools/_awpshot_fix.py
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import bbmcp                                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SAVED = os.path.join(ROOT, 'build', 'bbshots', 'shot_capture_screenshot.png')

SHOTS = (
    ('full', [14.0, 7.0, 12.0], [0.0, 0.6, -6.0]),      # 整枪 3/4
    ('tg', [4.2, -1.2, 1.6], [0.0, -0.3, 0.2]),         # 扳机/护圈/握把近景
    ('sc', [4.6, 4.6, 1.2], [0.0, 2.6, -0.4]),          # 镜座/镜筒近景
)


def main():
    m = bbmcp.Mcp().connect()
    for nm, pos, tgt in SHOTS:
        m.call('set_camera_angle', {'position': pos, 'target': tgt,
                                    'projection': 'perspective'})
        m.call('capture_screenshot', {})
        out = os.path.join(ROOT, 'build', '_awp_fix_%s.png' % nm)
        shutil.copyfile(SAVED, out)
        print('wrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
