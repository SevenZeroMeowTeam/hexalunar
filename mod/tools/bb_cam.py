#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在 Blockbench 里出「游戏内视角」预览图：第一人称 / 武器在玩家手里。

流程（全自动，依赖 Blockbench 正在运行 + MCP 服务器开着）：
  1. risky_eval 里用 Node 的 fs + Codecs.project 打开 模型/<x>.bbmodel（格式 free）
  2. trigger_action convert_project + fill_dialog 把工程转成 Java 版方块/物品
     （格式支持 display，才能预览显示变换）
  3. 把游戏内 item json 的 display（rotation/translation/scale，8 个槽位）写进工程
  4. enter_display_mode(slot, reference='player') → set_camera_angle → capture_screenshot

用法:
  python tools/bb_cam.py --list                        # 看看有哪些预设
  python tools/bb_cam.py akm                           # 默认视角组合
  python tools/bb_cam.py akm --slot thirdperson_righthand --cam hand3p
  python tools/bb_cam.py --all
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bbmcp import Mcp  # noqa: E402

ITEM = 'src/main/resources/assets/hexalunar_calamity/models/item'
OUT = 'build/bbviews'
ROOT = os.path.abspath('.')

MODELS = {
    'akm': ('模型/akm.bbmodel', 'akm.json'),
    'crossbow': ('模型/十字弩_v2.bbmodel', 'crossbow.json'),
    'compound_bow': ('模型/复合弓.bbmodel', 'compound_bow.json'),
    'bolt': ('模型/弩箭.bbmodel', None),
    'mtx': ('模型/mtx.bbmodel', 'mtx.json'),
    'mud': ('模型/mud.bbmodel', 'mud.json'),
}

# 相机预设：位置/目标（Blockbench 单位，1 格 = 16）
CAMS = {
    'hand3p':       dict(pos=[36, 30, 36], tgt=[0, 14, 0]),
    'hand3p_front': dict(pos=[0, 26, 46], tgt=[0, 16, 0]),
    'hand3p_side':  dict(pos=[46, 24, 0], tgt=[0, 16, 0]),
    'hand3p_top':   dict(pos=[18, 52, 26], tgt=[0, 16, 0]),
    'fp':           dict(pos=[0, 0, 0], tgt=[0, 0, -160]),
    'fp_back':      dict(pos=[0, 0, 60], tgt=[0, 0, -60]),
    'fp_side':      dict(pos=[34, 6, -6], tgt=[0, 3, -30]),
    'iso':          dict(pos=[34, 26, 34], tgt=[0, 8, 0]),
}

SLOTS = ['thirdperson_righthand', 'firstperson_righthand']


def load_model(mcp, bb_path):
    p = os.path.join(ROOT, bb_path).replace('\\', '/')
    code = ("const fs=require('fs');const p='%s';const o=JSON.parse(fs.readFileSync(p,'utf8'));"
            "const r=Codecs.project.parse(o,p);Promise.resolve(r).then(mm=>{const m=mm||r;"
            "if(m&&m.load){m.load(p);}return 'ok';});'loading'" % p)
    r = mcp.call('risky_eval', {'code': code})
    time.sleep(1.6)
    return r


def convert_to_java(mcp):
    mcp.call('trigger_action', {'action': 'convert_project', 'confirmDialog': False})
    time.sleep(1.0)
    r = mcp.call('fill_dialog', {'values': '{}', 'confirm': True})
    time.sleep(1.6)
    return r


def push_display(mcp, json_name):
    if not json_name:
        return ['(该模型没有 item json，跳过 display)']
    with open(os.path.join(ITEM, json_name), 'r', encoding='utf-8') as fh:
        disp = (json.load(fh).get('display') or {})
    msgs = []
    for slot, val in disp.items():
        args = {'slot': slot}
        if val.get('rotation') is not None:
            args['rotation'] = val['rotation']
        if val.get('translation') is not None:
            args['translation'] = val['translation']
        if val.get('scale') is not None:
            args['scale'] = val['scale']
        r = mcp.call('set_display_transform', args)
        msgs.append('%s %s' % ('OK ' if r.get('ok') else 'ERR', slot))
    return msgs


def shot(mcp, model, slot, cam, tag):
    mcp.call('enter_display_mode', {'slot': slot, 'reference': 'player'})
    time.sleep(1.2)
    c = CAMS[cam]
    mcp.call('set_camera_angle', {'position': [float(x) for x in c['pos']],
                                  'target': [float(x) for x in c['tgt']],
                                  'projection': 'perspective'})
    time.sleep(1.2)
    r = mcp.call('capture_screenshot', {})
    os.makedirs(OUT, exist_ok=True)
    text = r.get('text') or ''
    if 'saved:' in text:
        src = text.split('saved:')[1].split(',')[0].strip()
        dst = os.path.join(OUT, '%s_%s_%s.png' % (model, slot.split('_')[0], cam))
        os.replace(src, dst)
        return dst
    return 'ERR ' + text[:120]


def close_project(mcp, keep_open=False):
    if keep_open:
        return
    mcp.call('risky_eval', {'code': "(Project.all||[]).slice().forEach(p=>{try{if(p.name&&/akm|crossbow|compound|bolt|mtx|mud|Converted|north_preview|十字弩|弩箭|复合弓/i.test(p.name))p.close&&p.close(true);}catch(e){}});'closed'"})
    time.sleep(0.8)


def main(argv):
    if '--list' in argv:
        print('模型: ' + ', '.join(MODELS))
        print('相机: ' + ', '.join(CAMS))
        print('槽位: ' + ', '.join(SLOTS))
        return 0
    mcp = Mcp().connect()
    args = [a for a in argv[1:] if not a.startswith('--')]
    if '--all' in argv:
        args = list(MODELS)
    if not args:
        args = ['akm']
    slots = SLOTS
    if '--slot' in argv:
        slots = [argv[argv.index('--slot') + 1]]
    cams = ['hand3p', 'hand3p_front', 'fp'] if '--allcams' not in argv else list(CAMS)
    if '--cam' in argv:
        cams = [argv[argv.index('--cam') + 1]]
    for name in args:
        bb, js = MODELS[name]
        print('== %s ==' % name)
        load_model(mcp, bb)
        convert_to_java(mcp)
        for m in push_display(mcp, js):
            print('   display %s' % m)
        for slot in slots:
            for cam in cams:
                p = shot(mcp, name, slot, cam, cam)
                print('   %-22s %-14s -> %s' % (slot, cam, p))
        close_project(mcp, keep_open='--keep' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
