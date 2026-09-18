"""按 MC 第一人称物品变换链，验算「瞄准参照点」是否落在屏幕中心。

world = Trans(0.56, -0.52, -0.71) · Trans(display.translation/16) · R · S · (模型像素/16)
相机在原点朝 -Z 看；屏幕中心 ⇔ 该点的 x_cam = y_cam = 0。

用法: python tools/_ads_check.py akm|bow [--aim]
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity', 'geo')
ITM = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'models', 'item')
ARM = (0.56, -0.52, -0.71)
VFOV = 70.0
ASPECT = 16.0 / 9.0

# (geo, item json, 旋转, 平移, 缩放, 参照点名, 参照点模型坐标)
CASES = {
    'akm': ('akm.geo.json', 'akm.json', [0, 0, 0], [-2.6, 1.4, 1.8], [1, 1, 1],
            [('照门叶片顶', (0.0, 3.44, -4.75)), ('准星柱顶', (0.0, 3.44, -8.43)),
             ('枪管轴', (0.0, 1.94, -8.43))]),
    'akm_aim': ('akm.geo.json', 'akm.json', [0, 0, 0],
                [-2.6 - 6.36, 1.4 + (8.32 - 3.44 - 1.4), 1.8 + 1.4], [1, 1, 1],
                [('照门叶片顶', (0.0, 3.44, -4.75)), ('准星柱顶', (0.0, 3.44, -8.43)),
                 ('枪管轴', (0.0, 1.94, -8.43))]),
    'bow': ('compound_bow.geo.json', 'compound_bow.json', [0, 0, 0], [0, 0, 0],
            [0.75, 0.75, 0.75],
            [('瞄准圈圆心', (0.0, 2.86, -4.12)), ('箭杆', (0.0, 0.85, -8.0))]),
    'bow_draw': ('compound_bow.geo.json', 'compound_bow.json', [0, 0, 0],
                 [-8.96, 8.32 - 0.75 * 2.86, -2.6], [0.75, 0.75, 0.75],
                 [('瞄准圈圆心', (0.0, 2.86, -4.12)), ('箭杆', (0.0, 0.85, -8.0))]),
}


def project(key):
    _geo, _item, rot, trans, scale, pts = CASES[key]
    rx, ry, rz = (math.radians(a) for a in rot)
    sx, sy, sz = scale
    print('== %s   rot=%s trans=%s scale=%s' % (key, rot, trans, scale))
    for name, p in pts:
        # R = Rz·Ry·Rx（MC 的 mulPose 顺序：先 X 再 Y 后 Z ⇒ 矩阵是 Rz·Ry·Rx）
        x, y, z = (p[0] * sx, p[1] * sy, p[2] * sz)
        # 先绕 X
        y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
        x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
        x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
        x = ARM[0] + trans[0] / 16.0 + x / 16.0
        y = ARM[1] + trans[1] / 16.0 + y / 16.0
        z = ARM[2] + trans[2] / 16.0 + z / 16.0
        depth = -z
        u = math.degrees(math.atan2(x, depth))
        v = math.degrees(math.atan2(y, depth))
        hu = math.degrees(math.atan(math.tan(math.radians(VFOV / 2)) * ASPECT))
        print('   %-12s 相机空间(%7.3f,%7.3f,%7.3f) 深度%.3f  屏幕偏移 X %+6.2f%%  Y %+6.2f%%'
              % (name, x, y, z, depth, 100.0 * u / hu, 100.0 * v / (VFOV / 2)))


if __name__ == '__main__':
    for k in (sys.argv[1:] or CASES.keys()):
        project(k)
