#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""震爆弹：把保险销/拉环挪到引信头外侧（原来埋在头部体积里看不见）。"""
import io

p = 'tools/flashbang_gen.py'
s = io.open(p, encoding='utf-8').read()
old = """    # 保险销：横销 + 外端拉环（拉出方向 -Z）
    add('pin', -0.34, 0.34, 11.85, 12.55, 0.6, 4.6, 'pin')
    ring_c, ring_r = (0.0, 11.6, -1.1), 1.15"""
new = """    # 保险销：横销穿过引信头 + 外端拉环挂在头外侧（拉出方向 -Z）
    add('pin', -0.34, 0.34, 11.85, 12.55, -4.60, 4.20, 'pin')
    ring_c, ring_r = (0.0, 11.6, -5.85), 1.15"""
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('拉环已挪到外侧:', 'ring_c, ring_r = (0.0, 11.6, -5.85), 1.15' in s)
else:
    print('未匹配，需手工检查')
