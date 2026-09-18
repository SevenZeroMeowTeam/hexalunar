#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""给 akm.animation.json 的弹匣/枪机补上位移通道：弹匣向下抽出、枪机向后滑动。

原来只有 rotation，弹匣会绕着自身中心原地转（像晃动），补上 position 才像真的换弹。
"""
import io
import json

P = 'src/main/resources/assets/hexalunar_calamity/animations/akm.animation.json'
with io.open(P, encoding='utf-8') as fh:
    d = json.load(fh)

A = d['animations']


def vec(pairs):
    return dict(('%g' % t, {'vector': list(v)}) for t, v in pairs)


# 换弹：弹匣向下抽出 → 空档停一下 → 新匣推回
A['reload']['bones'].setdefault('magazine', {})['position'] = vec(
    [(0.0, (0, 0, 0)), (0.15, (0, -2.8, 0.4)), (0.55, (0, -2.8, 0.4)),
     (0.8, (0, 0, 0)), (1.2, (0, 0, 0))])
# 换弹时枪机也向后带一点（释放枪机回到位）
A['reload']['bones'].setdefault('bolt', {})['position'] = vec(
    [(0.0, (0, 0, 0)), (0.55, (0, 0, 2.0)), (0.8, (0, 0, 2.0)),
     (0.95, (0, 0, 0)), (1.2, (0, 0, 0))])
# 打空拉栓：枪机向后 → 回位
A['bolt_pull']['bones'].setdefault('bolt', {})['position'] = vec(
    [(0.0, (0, 0, 0)), (0.08, (0, 0, 2.2)), (0.34, (0, 0, 2.2)),
     (0.44, (0, 0, 0)), (0.55, (0, 0, 0))])

with io.open(P, 'w', encoding='utf-8') as fh:
    json.dump(d, fh, ensure_ascii=False, indent=1)

for n, a in A.items():
    chs = {}
    for b, v in (a.get('bones') or {}).items():
        for c in v:
            chs.setdefault(b, []).append(c)
    print('%-10s %s' % (n, chs))
