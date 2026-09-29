#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把现有 AKM 模型导进正在运行的 Blockbench（作为「在 Blockbench 里重做」的起点）。

流程：
  1) `create_project` 建 GeckoLib 格式新工程（失败会打印可选 format id）
  2) `from_geo_json` 把 `assets/hexalunar_calamity/geo/akm.geo.json` 导进去（骨骼 + 144 方块 + UV 全带上）
  3) `create_texture` 把 `textures/models/akm_geo.png` 作为贴图塞进工程（改配色就从这张开始）
  4) 截图存 `build/_bb_ak_shot.png` 供肉眼核对

用法::  python tools/ak_bb_import.py
"""
import base64
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from bbmcp import Mcp                                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'geo', 'akm.geo.json')
TEX = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'textures', 'models', 'akm_geo.png')
SHOT = os.path.join(ROOT, 'build', '_bb_ak_shot.png')
SHOTDIR = os.path.join(ROOT, 'build', 'bbshots')
LOG = os.path.join(ROOT, 'build', '_bb_ak_import.txt')

FORMATS = ['geckolib_model', 'bedrock', 'bedrock_old', 'free']


def call(mcp, tool, args, log):
    r = mcp.call(tool, args)
    txt = json.dumps(r, ensure_ascii=False)[:400]
    log.append('%s %s -> %s' % (tool, json.dumps(args, ensure_ascii=False)[:160], txt))
    print(log[-1])
    return r


def newest_shot():
    """桥每次改动都会自动截图到 build/bbshots/，取最新那张就好。"""
    if not os.path.isdir(SHOTDIR):
        return None
    files = [os.path.join(SHOTDIR, f) for f in os.listdir(SHOTDIR) if f.endswith('.png')]
    return max(files, key=os.path.getmtime) if files else None


def main(argv):
    geo = argv[0] if len(argv) > 0 else GEO
    tex = argv[1] if len(argv) > 1 else TEX
    pname = argv[2] if len(argv) > 2 else 'hexalunar_ak47'
    mcp = Mcp().connect()
    log = []

    # 1) 新工程（format id 逐个试）
    ok = False
    for fmt in FORMATS:
        r = call(mcp, 'create_project', {'name': pname, 'format': fmt}, log)
        if r and not r.get('isError') and r.get('ok', True):
            ok = True
            print('工程已建，format =', fmt)
            break
    if not ok:
        print('!! 所有 format 都失败，看上面的报错（里面通常列了合法 id）')

    # 2) 导入 geo —— ★ 桥只接受 http(s) 或 **JSON 字符串本身**，不给本地文件路径
    with io.open(geo, encoding='utf-8') as f:
        raw = f.read()
    call(mcp, 'from_geo_json', {'geojson': raw}, log)

    # 3) 贴图：data 传本地 png 路径是被支持的（上面实测 ok）
    tex_name = os.path.basename(tex)
    call(mcp, 'create_texture', {'name': tex_name, 'width': 512, 'height': 512, 'data': tex}, log)
    call(mcp, 'apply_texture', {'id': 'root', 'texture': tex_name, 'applyTo': 'all'}, log)

    # 4) 现状 + 截图
    call(mcp, 'set_camera_angle', {'position': [-18, 12, 22], 'target': [0, 1.5, -2],
                                   'projection': 'perspective'}, log)
    out = call(mcp, 'list_outline', {}, log)
    print('outline:', (out.get('text') or '')[:300])
    shot = mcp.call('capture_screenshot', {})
    src = newest_shot()
    if src:
        import shutil
        shutil.copyfile(src, SHOT)
        print('截图 ->', SHOT, '(来源 %s)' % os.path.basename(src))
    else:
        print('没找到桥自动保存的截图，返回：%s' % json.dumps(shot, ensure_ascii=False)[:200])

    with io.open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log) + '\n')
    print('日志 ->', LOG)


if __name__ == '__main__':
    main(sys.argv[1:])
