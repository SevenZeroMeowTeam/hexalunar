# -*- coding: utf-8 -*-
"""莫辛「扳机组」多角度截图（每张单独命名，避免 bbmcp 覆盖同名文件）。

用法::  python tools/_mosshot_tg.py [project]
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
    ('botf', [3.4, -1.5, -4.2], [0, 0.55, -1.5]),   # 前下方斜看（用户那个角度）
    ('side', [3.2, 0.55, -1.50], [0, 0.60, -1.45]),  # 正右侧近景
    ('down', [0.6, -2.4, -1.5], [0, 0.60, -1.5]),    # 正下方
)


def main():
    proj = sys.argv[1] if len(sys.argv) > 1 else 'hexalunar_mosin_m9130'
    m = bbmcp.Mcp().connect()
    for nm, pos, tgt in SHOTS:
        m.call('set_camera_angle', {'position': pos, 'target': tgt,
                                    'projection': 'perspective'})
        m.call('capture_screenshot', {})
        out = os.path.join(ROOT, 'build', '_mos_tg_%s.png' % nm)
        shutil.copyfile(SAVED, out)
        print('wrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
