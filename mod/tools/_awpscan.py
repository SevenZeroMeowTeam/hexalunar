# -*- coding: utf-8 -*-
"""扫描「给枪加多少俯仰角，屏幕上的枪管轴线才是水平的」。

两种加法都算一遍：
  A. display 旋转（绕模型原点 = 机匣中心）
  B. move 骨骼 rotX（绕握把 pivot，举枪时可以再转回去）

用法: python tools\\_awpscan.py
"""
import math
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _awpfp as fp                                     # noqa: E402

W = H = 1200.0
FOV = 70.0
# 枪管轴线两个采样点（模型像素）：机匣前 / 枪口
AXIS = [(0.0, 1.575, 0.0), (0.0, 1.575, -16.275)]
# 关键点：枪托后端、枪口、镜筒中心
BUTT = (0.0, 1.575, 7.350)
SCOPE = (0.0, 3.150, -0.30)


def measure(rx, mode):
    """mode='disp' → 绕模型原点；'move' → 绕 move pivot（握把）"""
    pts = []
    for p in AXIS + [BUTT, SCOPE]:
        q = p
        if mode == 'move' and abs(rx) > 1e-9:
            piv = fp.MOVE_P
            c, s = math.cos(math.radians(rx)), math.sin(math.radians(rx))
            dy, dz = q[1] - piv[1], q[2] - piv[2]
            q = (q[0], piv[1] + dy * c - dz * s, piv[2] + dy * s + dz * c)
        pts.append(q)
    rot = (rx, 0.0, 0.0) if mode == 'disp' else (0.0, 0.0, 0.0)
    cam = fp.xform(pts, rot, fp.AWP_T)
    pp = fp.project(cam, W, H, FOV)
    if any(p is None for p in pp):
        return None
    (x0, y0, _), (x1, y1, _), (xb, yb, _), (xs, ys, _) = pp
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    if abs(ang) > 90:                                   # 归一化到「枪口方向」的倾角
        ang += 180 if ang > 0 else -180
    return ang, (x1, y1), (xb, yb), (xs, ys)


def show(mode, rx):
    r = measure(rx, mode)
    if r is None:
        print('  rx=%+5.1f  有顶点跑到相机后面' % rx)
        return
    ang, muz, butt, scope = r
    print('  rx=%+5.1f°  轴线倾角 %+6.1f°   枪口(%5.0f,%5.0f)  枪托后(%5.0f,%5.0f)  镜筒(%5.0f,%5.0f)'
          % (rx, ang, muz[0], muz[1], butt[0], butt[1], scope[0], scope[1]))


print('=== A. display 旋转（绕机匣中心；角度为负 = 枪口下压）')
for rx in range(0, -34, -3):
    show('disp', float(rx))
print('=== B. move 骨骼 rotX（绕握把；举枪时可归零）')
for rx in range(0, -34, -3):
    show('move', float(rx))
print('画面 %.0fx%.0f，竖直 FOV %.0f°，相机在眼睛处、朝 -Z' % (W, H, FOV))
