# -*- coding: utf-8 -*-
"""AWP 抛壳左右自检：用 `_awpfp.py` 那套（与游戏逐像素对齐过的）第一人称变换链，
把「抛壳口 / 弹壳 / 拉机柄」等模型点投影到屏幕，打印像素 x，直接看哪边是"右"。

用法::  python tools/_casing_probe.py [bp]
"""
import math
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)

ARM_X, ARM_Y, ARM_Z = 0.56, -0.52, -0.72
AWP_T = (-5.0, -0.425, 0.5)

# ---- AwpGeoModel 里的抛壳常量（改了要同步这里）
CASE_T0, CASE_T1 = 0.12, 0.80
CASE_BACK, CASE_VX, CASE_VY, CASE_G = 1.90, 5.0, 2.2, 0.8
CASING_PIVOT = (0.0, 1.575, -2.25)
SHELL_LOCAL = (0.0, 0.0, 0.05)          # 弹壳几何相对 pivot 的中心（膛内，x 居中）

W, H, FOV = 1462, 816, 70.0


def to_cam(p):
    """模型像素 → 相机空间（格）：Trans(+0.56, −0.52, −0.72) · Trans(display/16)，旋转为单位阵"""
    return (ARM_X + (AWP_T[0] + p[0]) / 16.0,
            ARM_Y + (AWP_T[1] + p[1]) / 16.0,
            ARM_Z + (AWP_T[2] + p[2]) / 16.0)


def project(c):
    """相机空间 → 屏幕像素（sx 随相机 x 单调增 ⇒ +X = 屏幕右）"""
    x, y, z = c
    w = -z
    if w <= 0.02:
        return None
    f = 1.0 / math.tan(math.radians(FOV) / 2.0)
    aspect = W / float(H)
    return ((x * f / aspect / w + 1.0) * 0.5 * W, (1.0 - y * f / w) * 0.5 * H)


def casing_point(bp):
    if bp < CASE_T0 or bp > CASE_T1:
        return None
    c = (bp - CASE_T0) / (CASE_T1 - CASE_T0)
    out = min(c / 0.22, 1.0)
    fly = max(0.0, min((c - 0.22) / 0.78, 1.0))
    return (CASING_PIVOT[0] + CASE_VX * fly + SHELL_LOCAL[0],
            CASING_PIVOT[1] + CASE_VY * fly - CASE_G * fly * fly + SHELL_LOCAL[1],
            CASING_PIVOT[2] + CASE_BACK * out - 1.2 * fly + SHELL_LOCAL[2])


def main():
    bp = float(sys.argv[1]) if len(sys.argv) > 1 else 0.60
    pts = [
        ('拉机柄球头 (+1.31)', (1.31, 1.365, -0.045)),
        ('镜像点     (-1.31)', (-1.31, 1.365, -0.045)),
        ('抛壳口     (+0.90)', (0.90, 1.39, -0.60)),
        ('镜像点     (-0.90)', (-0.90, 1.39, -0.60)),
        ('枪管轴线   (x=0)', (0.0, 1.575, -12.0)),
        ('握把       (x=0)', (0.0, -1.07, 1.305)),
    ]
    c = casing_point(bp)
    if c is not None:
        pts.append(('★ 弹壳 bp=%.2f' % bp, c))

    lines = ['屏幕 %dx%d  FOV %.0f  屏幕中心 x = %.0f（> 中心 = 屏幕右）' %
             (W, H, FOV, W / 2.0), '']
    for name, p in pts:
        cam = to_cam(p)
        q = project(cam)
        if q is None:
            lines.append('  %-20s 模型 %-24s ← 相机后面' % (name, [round(v, 2) for v in p]))
            continue
        lines.append('  %-20s 模型 %-24s 相机 x=%+6.3f  →  屏幕 x=%7.1f  %s  深度 %.2f' %
                     (name, [round(v, 2) for v in p], cam[0], q[0],
                      '屏幕右' if q[0] > W / 2.0 else '屏幕左', -cam[2]))
    text = '\n'.join(lines)
    with open(os.path.join(MOD, 'build', '_casing_probe.txt'), 'w', encoding='utf-8') as fh:
        fh.write(text + '\n')
    print(text)
    text = '\n'.join(lines)
    dst = os.path.join(MOD, 'build', '_casing_probe.txt')
    with open(dst, 'w', encoding='utf-8') as fh:
        fh.write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
