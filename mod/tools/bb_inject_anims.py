#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 animations/akm.animation.json（Bedrock 格式）注入 Blockbench 工程，方便在
Blockbench 的时间轴里直接编辑换弹/拉栓动画。

用法: python tools/bb_inject_anims.py
"""
import json
import os
import sys

BB = '模型/akm_geckolib.bbmodel'
ANIM = 'src/main/resources/assets/hkexalunar_calamity/animations/akm.animation.json'
ANIM = 'src/main/resources/assets/hexalunar_calamity/animations/akm.animation.json'


def main():
    if not os.path.exists(BB):
        print('找不到工程文件 %s' % BB)
        return 1
    with open(BB, 'r', encoding='utf-8') as fh:
        proj = json.load(fh)
    with open(ANIM, 'r', encoding='utf-8') as fh:
        anims = json.load(fh).get('animations', {})
    # 骨骼名 -> 分组 uuid
    uuid_of = {g['name']: g['uuid'] for g in proj.get('groups', [])}
    out = []
    for name, a in anims.items():
        animators = {}
        for bone, tracks in (a.get('bones') or {}).items():
            u = uuid_of.get(bone)
            if not u:
                continue
            kfs = []
            for t, val in tracks.items():
                time = float(t)
                if 'vector' in val:
                    ch, dp = 'position', val['vector']
                elif 'post' in val:
                    ch, dp = 'rotation', val['post']
                else:
                    continue
                if isinstance(dp, list) and len(dp) == 1 and isinstance(dp[0], list):
                    dp = dp[0]
                kfs.append({'channel': ch, 'time': time,
                            'interpolation': 'catmullrom',
                            'data_points': [{'x': dp[0], 'y': dp[1], 'z': dp[2]}]})
            kfs.sort(key=lambda k: k['time'])
            animators[u] = {'name': bone, 'type': 'bone', 'keyframes': kfs}
        out.append({
            'name': name,
            'loop': 'loop' if a.get('loop') else 'once',
            'override': False,
            'length': float(a.get('animation_length', 1.0)),
            'snapping': 24,
            'selected': False,
            'anim_time_update': '',
            'blend_weight': '',
            'start_delay': '',
            'loop_delay': '',
            'animators': animators,
            'uuid': 'anim-' + name,
        })
    proj['animations'] = out
    with open(BB, 'w', encoding='utf-8') as fh:
        json.dump(proj, fh, ensure_ascii=False)
    print('已注入 %d 条动画到 %s：%s' % (len(out), BB, ', '.join(a['name'] for a in out)))
    for a in out:
        bones = ', '.join(v['name'] for v in a['animators'].values())
        print('   %-10s 时长 %.2fs  loop=%-4s  骨骼: %s' % (a['name'], a['length'], a['loop'], bones))
    return 0


if __name__ == '__main__':
    sys.exit(main())
