# -*- coding: utf-8 -*-
"""在运行中的 Blockbench 里摆相机 → 截图存到 build/bbshots/<view>.png。

用法: python tools/_bbshot.py [view ...]                     # 全部视角，静止姿态
      python tools/_bbshot.py --anim bolt_open --time 0.6    # 先切到某条动画的某一时刻
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from bbmcp import Mcp                                   # noqa: E402

VIEWS = [
    ('iso',    [46.0, 30.0, -42.0], [0.0, 2.0, -4.0]),
    ('left',   [-72.0, 18.0, -8.0], [0.0, 2.0, -4.0]),
    ('action', [14.0, 20.0, 12.0], [0.0, 1.6, -2.6]),
    ('under',  [12.0, -8.0, -18.0], [0.0, 1.2, -2.0]),
    ('muzzle', [-10.0, 12.0, -58.0], [0.0, 1.75, -17.0]),
    ('scope',  [0.0, 5.6, 26.0], [-0.54, 3.24, -2.4]),
]

# M1 加兰德（总长 20.9 像素，机匣在 z −3.1…2.1）
M1_VIEWS = [
    ('iso',    [34.0, 22.0, -32.0], [0.0, 2.0, -3.0]),
    ('left',   [-52.0, 14.0, -6.0], [0.0, 2.0, -3.0]),
    ('action', [11.0, 14.0, 9.0], [0.0, 2.3, -0.9]),
    ('top',    [1.5, 16.0, 3.0], [0.0, 2.4, -0.9]),
    ('eject',  [16.0, 6.0, -1.0], [1.2, 3.0, -1.2]),
]


def parse_view_names(argv):
    """把位置参数当作「只拍这些视角」的过滤器（自动跳过选项后面的值）。"""
    opts = ('--anim', '--time', '--tag', '--gun')
    out, i = [], 1
    while i < len(argv):
        a = argv[i]
        if a in opts:
            i += 2
            continue
        if not a.startswith('--'):
            out.append(a)
        i += 1
    return out


def main(argv):
    views = parse_view_names(argv)
    table = M1_VIEWS if '--gun' in argv and argv[argv.index('--gun') + 1] == 'm1' else VIEWS
    mcp = Mcp().connect()
    if '--anim' in argv:
        name = argv[argv.index('--anim') + 1]
        t = float(argv[argv.index('--time') + 1]) if '--time' in argv else 0.0
        js = open(os.path.join(ROOT, 'build', '_bb_pose.js'), encoding='utf-8').read()
        js = js.replace('ANIM_NAME', "'%s'" % name).replace('ANIM_TIME', '%.3f' % t)
        out = mcp.call('risky_eval', {'code': js})
        print('pose:', (out.get('text') or '')[:200].replace('\n', ' '))
    os.makedirs(os.path.join(ROOT, 'build', 'bbshots'), exist_ok=True)
    for name, pos, tgt in table:
        if views and name not in views:
            continue
        mcp.call('set_camera_angle', {'position': pos, 'target': tgt,
                                      'projection': 'perspective'})
        out = mcp.call('capture_screenshot', {})
        src = os.path.abspath(os.path.join(ROOT, 'build', 'bbshots', 'shot_None.png'))
        for cand in ('shot_capture_screenshot.png', 'shot_None.png', 'shot_.png'):
            p = os.path.abspath(os.path.join(ROOT, 'build', 'bbshots', cand))
            if os.path.exists(p):
                src = p
                break
        dst = os.path.abspath(os.path.join(ROOT, 'build', 'bbshots',
                                           (argv[argv.index('--tag') + 1] + '_' if '--tag' in argv
                                            else '') + name + '.png'))
        if os.path.exists(src):
            os.replace(src, dst)
        print('%-8s -> %s  %s' % (name, os.path.relpath(dst, ROOT),
                                  (out.get('text') or '')[:60].replace('\n', ' ')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
