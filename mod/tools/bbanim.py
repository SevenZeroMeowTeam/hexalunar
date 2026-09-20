#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 build/<name>.animation.json（Bedrock/GeckoLib 格式）推进正在运行的 Blockbench。

用法: python tools/bbanim.py build/mosin_m9130.animation.json [--clear]

行为：对每条动画调一次 MCP 的 ``create_animation``（骨骼按名字匹配大纲里的组），
于是在 Blockbench 时间轴上就能直接播放 / 逐帧看（拉栓、抛壳、推弹入膛、换弹）。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bbmcp import Mcp                                   # noqa: E402


def to_tool_args(name, spec):
    bones = {}
    for bone, chans in (spec.get('bones') or {}).items():
        by_time = {}
        for channel, times in chans.items():          # ★ 通道 → 时刻
            for tstr, val in times.items():
                v = list(val) if isinstance(val, (list, tuple)) else [val] * 3
                by_time.setdefault(float(tstr), {})[channel] = [float(x) for x in v]
        kfs = [dict(kf, time=t) for t, kf in sorted(by_time.items())]
        bones[bone] = kfs
    lp = spec.get('loop')
    return {'name': name,
            'loop': bool(lp is True or lp == 'loop' or lp == 'hold_on_last_frame'),
            'animation_length': float(spec.get('animation_length', 1.0)),
            'bones': bones}


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = json.load(open(argv[1], encoding='utf-8'))
    anims = data.get('animations', data)
    mcp = Mcp().connect()
    for name, spec in anims.items():
        args = to_tool_args(name, spec)
        out = mcp.call('create_animation', args)
        txt = (out.get('text') or '')[:160].replace('\n', ' ')
        print('%s %-34s %-2d 根骨骼  %ss  %s'
              % ('OK ' if out.get('ok') else 'ERR', name, len(args['bones']),
                 args['animation_length'], txt))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
