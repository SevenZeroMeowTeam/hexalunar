# -*- coding: utf-8 -*-
"""离线校核 AWP 第一人称双手的落点（不依赖游戏）：把 AwpGeoModel / WeaponArms 里的
常量搬到 Python 里复算一遍，检查

  1. 手到肩的距离是否落在 WeaponArms.drawArm 的 (0.1, 3.0) 格内
  2. 手臂拉伸倍率（dist / 0.75）别太夸张
  3. 手在相机空间的左右/上下位置是否合理（x>0 在画面右侧）
  4. 拉栓全程右手是否平滑地从握把走到拉机柄再走回来

用法: python tools\\_awp_arms.py
"""
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------------- 相机空间换算（GunFrame.toCamera）
ARM_X, ARM_Y, ARM_Z = 0.56, -0.52, -0.72
SHOULDER_R = (0.55, -0.85, -0.80)
SHOULDER_L = (-0.42, -0.85, -0.78)
ARM_LEN = 0.75
# models/item/awp.json 的 display 平移
AWP_TX, AWP_TY, AWP_TZ = -2.6, 4.22, 0.50

# 拉栓 / 手臂常量（与 AwpGeoModel 一致）
BOLT_LIFT, BOLT_BACK = 62.0, 1.9
BOLT_P = (0.615, 1.50, 0.375)
BOLT_GRIP_DX, BOLT_GRIP_DY = 0.685, -0.05
BOLT_HAND_IN, BOLT_HAND_OUT = 0.18, 0.88
TRIGGER_PULL = 11.0
ARM_GRIP = (0.0, -1.07, 1.31)
ARM_SUPPORT = (0.0, -0.55, -3.30)
ARM_MAG = (0.0, -0.95, -1.95)
MAG_PY, MAG_PZ = 0.0, 0.90
MAG_DROP, MAG_TILT = 2.6, 26.0


def ease(t):
    x = min(1.0, max(0.0, t))
    return x * x * (3.0 - 2.0 * x)


def bolt_lift(bp):
    if bp < 0:
        return 0.0
    if bp < 0.20:
        return bp / 0.20
    if bp > 0.85:
        return min(1.0, max(0.0, (1.0 - bp) / 0.15))
    return 1.0


def bolt_back(bp):
    if bp < 0:
        return 0.0
    return (min(1.0, max(0.0, (bp - 0.20) / 0.35))
            * (1.0 - min(1.0, max(0.0, (bp - 0.62) / 0.32))))


def bolt_handle_point(bp):
    a = math.radians(bolt_lift(bp) * BOLT_LIFT)
    c, s = math.cos(a), math.sin(a)
    return (BOLT_P[0] + (BOLT_GRIP_DX * c - BOLT_GRIP_DY * s),
            BOLT_P[1] + (BOLT_GRIP_DX * s + BOLT_GRIP_DY * c),
            BOLT_P[2] + bolt_back(bp) * BOLT_BACK)


def right_hand(bp):
    if bp < 0:
        return ARM_GRIP
    h = bolt_handle_point(bp)
    if bp < BOLT_HAND_IN:
        t = ease(bp / BOLT_HAND_IN)
    elif bp < BOLT_HAND_OUT:
        t = None
    else:
        t = ease((bp - BOLT_HAND_OUT) / (1.0 - BOLT_HAND_OUT))
    if t is None:
        return h
    return tuple(ARM_GRIP[i] + (h[i] - ARM_GRIP[i]) * t for i in range(3))


def mag_drop(p):
    if p < 0:
        return 0.0
    if p < 0.28:
        return ease(p / 0.28)
    if p > 0.72:
        return ease(min(1.0, max(0.0, (1.0 - p) / 0.28)))
    return 1.0


def left_hand(rp):
    if rp < 0:
        return ARM_SUPPORT
    d = mag_drop(rp)
    a = math.radians(MAG_TILT * d)
    dy, dz = ARM_MAG[1] - MAG_PY, ARM_MAG[2] - MAG_PZ
    pt = (ARM_MAG[0],
          MAG_PY + (dy * math.cos(a) - dz * math.sin(a)) - MAG_DROP * d,
          MAG_PZ + (dy * math.sin(a) + dz * math.cos(a)))
    if rp < 0.12:
        t = ease(rp / 0.12)
    elif rp < 0.82:
        t = None
    else:
        t = ease((rp - 0.82) / 0.18)
    if t is None:
        return pt
    return tuple(ARM_SUPPORT[i] + (pt[i] - ARM_SUPPORT[i]) * t for i in range(3))


def to_camera(p, aim=False):
    ax, ay, az = 0.0, 0.0, 0.0
    if aim:
        # WeaponMount.AWP_AIM_DX / DY / DZ（瞄准时 move 骨骼的平移）
        ax = -(0.56 * 16.0) - AWP_TX
        ay = -(-0.52 * 16.0) - 3.15 - AWP_TY
        az = 1.4
    return (ARM_X + (AWP_TX + ax + p[0]) / 16.0,
            ARM_Y + (AWP_TY + ay + p[1]) / 16.0,
            ARM_Z + (AWP_TZ + az + p[2]) / 16.0)


def report(tag, p, shoulder, aim=False):
    h = to_camera(p, aim)
    d = math.dist(h, shoulder)
    ok = 0.1 < d < 3.0
    print('  %-26s 模型(%7.2f,%7.2f,%7.2f)  相机(%6.2f,%6.2f,%6.2f)  '
          '肩距 %.2f 格  拉伸 %.2f x  %s'
          % (tag, p[0], p[1], p[2], h[0], h[1], h[2], d, d / ARM_LEN,
             'OK' if ok else '!! 超范围'))


print('== 右手（肩 R）==')
for aim in (False, True):
    print(' [%s]' % ('瞄准' if aim else '腰射'))
    report('握把（待机）', ARM_GRIP, SHOULDER_R, aim)
    for bp in (0.10, 0.20, 0.40, 0.60, 0.80, 0.95):
        report('拉栓 bp=%.2f' % bp, right_hand(bp), SHOULDER_R, aim)

print('== 左手（肩 L）==')
for aim in (False, True):
    print(' [%s]' % ('瞄准' if aim else '腰射'))
    report('护木支撑（待机/拉栓）', ARM_SUPPORT, SHOULDER_L, aim)
    for rp in (0.06, 0.20, 0.50, 0.80, 0.95):
        report('换弹 rp=%.2f' % rp, left_hand(rp), SHOULDER_L, aim)

print('== 右手拉栓轨迹（模型像素，x = 枪的右侧）==')
for i in range(0, 11):
    bp = i / 10.0
    p = right_hand(bp)
    print('  bp=%.1f  夹紧 %5.2f  抬起 %5.2f  后退 %5.2f   |  拉机柄 %5.2f / %5.2f / %5.2f'
          % (bp, p[0], p[1], p[2], *bolt_handle_point(bp)))
