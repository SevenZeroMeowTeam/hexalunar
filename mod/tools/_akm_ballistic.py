# -*- coding: utf-8 -*-
"""AKM 弹道离线验算：从枪口射向准星的方法，落点到底偏多少（r67 排查用）。

复刻 Java 侧同一套数：
  · 枪口模型点 WEAPON_MOUNT.AKM_MUZZLE，经 Trans(ARM)·Trans(display/16) 换到相机空间；
  · 方向 = 枪口 → 准星落点（沿视线 max(8, 命中距离)…96），与 WeaponMount.fireDir 一致；
  · 每 tick：先按当前速度做命中判定再位移，然后 ×0.99 阻尼，再 y -= gravity
    （ThrowableProjectile.tick 的顺序；gravity = 0.006 + 超距追加）。
输出：各距离上「弹道 y」与「准星射线 y」的差（负 = 打在准星下方）。
"""
import math
import sys

ARM = (0.56, -0.52, -0.72)
AKM_TX, AKM_TY, AKM_TZ = -2.6, 1.4, 1.8
MUZZLE = (0.0, 1.75, -11.60)
SIGHT_Y = 3.44
AKM_AIM_DY = -ARM[1] * 16.0 - SIGHT_Y - AKM_TY
SPEED_HIP, SPEED_AIM = 4.5, 5.0
DRAG = 0.99
G_IN = 0.006
RANGE = 60.0
EXTRA_FACTOR, EXTRA_CAP = 0.08, 1.5


def cam(px):
    """模型像素 → 相机空间（格）"""
    return (ARM[0] + (AKM_TX + px[0]) / 16.0,
            ARM[1] + (AKM_TY + px[1]) / 16.0,
            ARM[2] + (AKM_TZ + px[2]) / 16.0)


def extra_gravity(flown):
    over = (flown - RANGE) / RANGE
    if over <= 0.0:
        return 0.0
    return min(over * over, EXTRA_CAP) * EXTRA_FACTOR


def fire(aiming, target_dist):
    """返回 {(水平距离): (dy, dx)}：弹道相对准星射线的偏移"""
    muz = cam(MUZZLE)
    # 相机空间：眼在原点、朝 -Z；举枪时 move 骨骼额外平移 akmAimDy
    if aiming:
        muz = (muz[0], muz[1] + AKM_AIM_DY / 16.0, muz[2] + 1.4 / 16.0)
    # 准星落点（无方块命中时取 96 格；有命中时取 max(8, 距离)）
    d_conv = max(8.0, min(96.0, target_dist))
    aim = (0.0, 0.0, -d_conv)
    vx, vy, vz = (aim[0] - muz[0], aim[1] - muz[1], aim[2] - muz[2])
    n = math.sqrt(vx * vx + vy * vy + vz * vz)
    speed = SPEED_AIM if aiming else SPEED_HIP
    vx, vy, vz = vx / n * speed, vy / n * speed, vz / n * speed
    x, y, z = muz
    out = {}
    t = 0
    while t < 400 and z > -400.0:
        x += vx
        y += vy
        z += vz
        vx *= DRAG
        vz *= DRAG
        vy = vy * DRAG - (G_IN + extra_gravity(-z))
        t += 1
        dist = -z                       # 水平前进距离（沿视线轴）
        for probe in (5, 10, 20, 30, 40, 60, 80, 96):
            if probe not in out and dist >= probe:
                # 准星射线在同样的 z 处 y 应为 0（眼高、水平看）
                out[probe] = (y, x)
        if len(out) >= 8:
            break
    return out, muz


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
    print('枪口（相机空间，格）：%s' % (tuple(round(v, 3) for v in cam(MUZZLE)),))
    _, muz = fire(False, 96)
    print('腰射枪口：(%+.3f, %+.3f, %+.3f)  ⇒ 比视线低 %.3f 格、偏右 %.3f 格'
          % (muz[0], muz[1], muz[2], -muz[1], muz[0]))
    for aiming, label in ((False, '腰射'), (True, '举枪')):
        for target in (8.0, 32.0, 96.0):
            res, _ = fire(aiming, target)
            row = '  '.join('%d格:%+.2f' % (d, res[d][0]) for d in (5, 10, 20, 30, 40, 60, 80, 96)
                            if d in res)
            print('%-2s 瞄 %3.0f 格收敛 | 相对准星的竖直偏移（负=偏低）：%s' % (label, target, row))
    print()
    print('== 收敛距离上限该取多少？（战斗距离 5~60 格内，腰射 / 举枪各自的最大偏差）')
    print('  上限 | 姿态 | ' + '  '.join('%5d 格' % d for d in (5, 10, 20, 30, 40, 60)))
    for cap in (16.0, 24.0, 32.0, 40.0, 48.0, 96.0):
        for aiming, label in ((False, '腰射'), (True, '举枪')):
            res, _ = fire(aiming, cap)
            vals = [abs(res[d][0]) for d in (5, 10, 20, 30, 40, 60) if d in res]
            line = '  '.join('%+.2f' % res[d][0] if d in res else '  -  '
                             for d in (5, 10, 20, 30, 40, 60))
            print('%5.0f | %s | %s   （最差 %.2f 格）'
                  % (cap, label, line, max(vals) if vals else 0.0))


if __name__ == '__main__':
    main()
