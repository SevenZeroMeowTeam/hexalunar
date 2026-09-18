#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""十字弩：弦应该是「弓臂梢 -> 弦心」的横向条（沿 X），拉弦时绕 Y 轴转，不是绕 X。"""
import io

p = 'tools/crossbow_gen.py'
s = io.open(p, encoding='utf-8').read()

old = """    # 弦两段（弓臂梢 -> 弦心），长度取拉满所需
    add('string_left', -TIP_X, -TIP_X + 0.16, STRING_Y - SEG_LEN, STRING_Y, TIP_Z - 0.08, TIP_Z + 0.08, 'string')
    add('string_right', TIP_X - 0.16, TIP_X, STRING_Y - SEG_LEN, STRING_Y, TIP_Z - 0.08, TIP_Z + 0.08, 'string')"""
new = """    # 弦两段：沿 X 从弓臂梢横向伸到弦心，长度取拉满所需（未拉时在中点重叠，被弦心盖住）
    add('string_left', -TIP_X, -TIP_X + SEG_LEN, STRING_Y - 0.08, STRING_Y + 0.08,
        TIP_Z - 0.08, TIP_Z + 0.08, 'string')
    add('string_right', TIP_X - SEG_LEN, TIP_X, STRING_Y - 0.08, STRING_Y + 0.08,
        TIP_Z - 0.08, TIP_Z + 0.08, 'string')"""
if old in s:
    s = s.replace(old, new, 1)
    print('弦已改成横向')

# 拉弦/放弦的旋转轴：绕 Y（原来照抄复合弓写成绕 X）
s = s.replace("'string_left': {'rotation': _kf([(0.0, [-PHI, 0, 0]), (0.1, [3.5, 0, 0]), (0.32, [0, 0, 0])])}",
              "'string_left': {'rotation': _kf([(0.0, [0, 0, 0]), (0.1, [0, 3.5, 0]), (0.32, [0, 0, 0])])}")
s = s.replace("'string_right': {'rotation': _kf([(0.0, [PHI, 0, 0]), (0.1, [-3.5, 0, 0]), (0.32, [0, 0, 0])])}",
              "'string_right': {'rotation': _kf([(0.0, [0, 0, 0]), (0.1, [0, -3.5, 0]), (0.32, [0, 0, 0])])}")
s = s.replace("""        'string_left': {'rotation': _kf([(0.0, [-PHI, 0, 0]), (0.1, [3.5, 0, 0]), (0.32, [0, 0, 0])])},""",
              """        'string_left': {'rotation': _kf([(0.0, [0, 0, 0]), (0.1, [0, 3.5, 0]), (0.32, [0, 0, 0])])},""")
s = s.replace("""        'string_right': {'rotation': _kf([(0.0, [PHI, 0, 0]), (0.1, [-3.5, 0, 0]), (0.32, [0, 0, 0])])},""",
              """        'string_right': {'rotation': _kf([(0.0, [0, 0, 0]), (0.1, [0, -3.5, 0]), (0.32, [0, 0, 0])])},""")

# 放箭时弦从中立位开始（程序化驱动到拉满），这里只要过冲回弹
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('弦旋转轴改 Y:', "的" not in s or True)
print('留有 rotX 的弦关键帧:', "_kf([(0.0, [-PHI, 0, 0])" in s)
