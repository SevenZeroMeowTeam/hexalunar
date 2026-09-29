#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""给 Blockbench 里的 AKM 套上贴图，并出「线框图同款视角」的几张图，方便和参考图对比。

用法::  python tools/ak_bb_view.py [工程名]
输出：build/_bb_ak_side.png / _bb_ak_iso.png / _bb_ak_front.png
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from bbmcp import Mcp                                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTDIR = os.path.join(ROOT, 'build', 'bbshots')
TEXNAME = 'akm_geo.png'

# 视角：(名字, 相机位置, 目标, 投影)
VIEWS = [
    ('side', [-40, 1.75, -2], [0, 1.75, -2], 'orthographic'),      # 正侧视（线框图那样）
    ('iso', [-16, 11, 20], [0, 1.6, -2], 'perspective'),           # 斜后上方
    ('front', [0, 1.75, -34], [0, 1.75, -10], 'perspective'),      # 枪口朝你
]


def newest():
    files = [os.path.join(SHOTDIR, f) for f in os.listdir(SHOTDIR)] if os.path.isdir(SHOTDIR) else []
    files = [f for f in files if f.endswith('.png')]
    return max(files, key=os.path.getmtime) if files else None


def grab(mcp, out_name):
    mcp.call('capture_screenshot', {})
    src = newest()
    if not src:
        print('  没拿到截图')
        return
    dst = os.path.join(ROOT, 'build', out_name)
    shutil.copyfile(src, dst)
    print('  ->', out_name)


def main(argv):
    tex = argv[0] if argv else 'akm_geo.png'
    mcp = Mcp().connect()
    texs = mcp.call('list_textures', {})
    print('工程里的贴图：', (texs.get('text') or '')[:200])

    r = mcp.call('apply_texture', {'id': 'root', 'texture': tex, 'applyTo': 'all'})
    print('apply_texture(root/all, %s) -> %s' % (tex, (r.get('text') or '')[:160]))

    for name, pos, tgt, proj in VIEWS:
        mcp.call('set_camera_angle', {'position': pos, 'target': tgt, 'projection': proj})
        print(name)
        grab(mcp, '_bb_ak_%s.png' % name)


if __name__ == '__main__':
    main(sys.argv[1:])
