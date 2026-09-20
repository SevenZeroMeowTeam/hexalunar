# -*- coding: utf-8 -*-
"""莫辛：看镜筒内部（从目镜往里看）/ 看机匣尾部（俯视）—— 每张单独命名。

用法::  python tools/_mosshot_eye.py
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
    ('eye', [0.0, 3.34, 1.30], [0.0, 3.34, -2.60]),     # 正对目镜往里看
    ('eye2', [0.9, 3.90, 0.60], [0.0, 3.20, -2.20]),    # 斜着看镜筒内部
    ('recv', [0.35, 4.80, 0.55], [0.0, 2.20, -1.60]),   # 机匣尾部俯视（看有没有缝）
)


def main():
    m = bbmcp.Mcp().connect()
    for nm, pos, tgt in SHOTS:
        m.call('set_camera_angle', {'position': pos, 'target': tgt,
                                    'projection': 'perspective'})
        m.call('capture_screenshot', {})
        out = os.path.join(ROOT, 'build', '_mos_fix_%s.png' % nm)
        shutil.copyfile(SAVED, out)
        print('wrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
