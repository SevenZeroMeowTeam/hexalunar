# -*- coding: utf-8 -*-
"""标定：原版 renderPlayerArm 的变换链到底把手臂方块的哪一端放在「手」的位置。

已知事实：
  · 链条（equip=p, swing=0）：
      T(f*0.64, -0.6 - 0.6p, -0.72) · Ry(f*45) · T(f*-1, 3.6, 3.5)
      · Rz(f*120) · Rx(200) · Ry(f*-135) · T(f*5.6, 0, 0)
  · PlayerRenderer.renderHand 先 resetPose()，所以手臂方块带 **PartPose 偏移**
      right_arm：pivot (-5, 2, 0)px，box x[-3,1] y[-2,10] z[-2,2]px
      left_arm ：pivot ( 5, 2, 0)px，box x[-1,3] y[-2,10] z[-2,2]px（mirror）
  · 参考真值：原版空手时拳头 ≈ 放物品的位置 = ARM_FP + display平移
      右手 (0.56, -0.52-0.6, -0.72)  左手 (-0.56, -0.52-0.6, -0.72)
"""
import math

import numpy as np


def rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def T(v):
    m = np.eye(4)
    m[:3, 3] = v
    return m


def R(m3):
    m = np.eye(4)
    m[:3, :3] = m3
    return m


def chain(f, equip):
    return (T([f * 0.64, -0.6 - 0.6 * equip, -0.72]) @ R(ry(f * 45.0))
            @ T([f * -1.0, 3.6, 3.5]) @ R(rz(f * 120.0)) @ R(rx(200.0))
            @ R(ry(f * -135.0)) @ T([f * 5.6, 0.0, 0.0]))


def main():
    for f, name in ((1.0, 'right'), (-1.0, 'left')):
        # 手臂方块两端中心（pose 坐标系，格）
        px = f * 0.3125                      # pivot 偏移
        xc = px + f * -0.0625                # 方块 x 中心（右臂 box 中心 -2px，左臂镜像 +2px）
        p_shoulder = np.array([xc, 0.125 - 0.125, 0.0])   # 局部 y = -2px 那一端
        p_far = np.array([xc, 0.125 + 0.625, 0.0])        # 局部 y = +10px 那一端
        m = chain(f, 0.0)                    # 手持物品时 equip = 1 - mainHandHeight = 0
        for label, p in (('局部y=-2px 端', p_shoulder), ('局部y=+10px 端', p_far)):
            w = m @ np.append(p, 1.0)
            print('%-6s %-14s -> (%.3f, %.3f, %.3f)' % (name, label, w[0], w[1], w[2]))
        ref = np.array([f * 0.56, -0.52, -0.72])
        for label, p in (('局部y=-2px 端', p_shoulder), ('局部y=+10px 端', p_far)):
            w = (m @ np.append(p, 1.0))[:3]
            print('        |%s - 参考拳位| = %.3f' % (label, np.linalg.norm(w - ref)))
        print()


if __name__ == '__main__':
    main()
