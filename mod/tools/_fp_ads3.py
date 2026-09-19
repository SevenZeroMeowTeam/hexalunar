#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""举枪（ADS）构图预览：在 _awpfp.py 的原版手持链条上再叠「举枪平移 + 横滚」。

和 Java 完全同一个顺序（`GunPose.matrix`）：
    相机 = ARM(±0.56, -0.52, -0.72) + ads + Rz(roll) · (displayT + R_move·p)/16
注意 **横滚绕的是模型原点**（= 显示原点），不是眼睛 —— 这一点很关键：
模型原点离握把很近，所以手基本不动，但**准星（在轴线上方 0.34 格）会被甩偏**。

用法:
  python tools\\_fp_ads3.py <geo> <tex> <out.png> --tx -2.6 --ty 1.4 --tz 1.8 \
         --ads -6.36,3.48,1.4 --roll 0 --fov 45 --hands
"""
import math
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _awpfp as fp                                       # noqa: E402

ARM_X, ARM_Y, ARM_Z = fp.ARM_X, fp.ARM_Y, fp.ARM_Z
PITCH_PIVOT = fp.MOVE_P
_rollDeg = [0.0]
_ads = [(0.0, 0.0, 0.0)]
_scale = [1.0]
_dscale = [1.0]                     # display 缩放（十字弩 = 0.8）
_anchor = [(0.0, 0.0, 0.0)]          # 模型像素：瞄准参照点（照门顶等）


def xform_roll(pts, rot, trans_px, pitch=0.0):
    """模型像素 → 相机空间（格）。

    显示平移/旋转 → **绕参照点**缩放 + 横滚 → 举枪平移 → ARM 基准。
    绕参照点做缩放/旋转，瞄准线就不会跑（参照点本来就是被顶到屏幕中心的那一点）。
    """
    R = fp.rot_mat(rot)
    a = math.radians(pitch)
    cp, sp = math.cos(a), math.sin(a)
    r = math.radians(_rollDeg[0])
    cr, sr = math.cos(r), math.sin(r)
    s = _scale[0]
    ax = (trans_px[0] + _anchor[0][0]) / 16.0
    ay = (trans_px[1] + _anchor[0][1]) / 16.0
    az = (trans_px[2] + _anchor[0][2]) / 16.0
    out = []
    for p in pts:
        q = np.asarray(p, dtype=float) * _dscale[0]
        if abs(pitch) > 1e-9:
            dy, dz = q[1] - PITCH_PIVOT[1], q[2] - PITCH_PIVOT[2]
            q = np.array([q[0], PITCH_PIVOT[1] + dy * cp - dz * sp,
                          PITCH_PIVOT[2] + dy * sp + dz * cp])
        q = R @ q
        vx = (trans_px[0] + q[0]) / 16.0 - ax
        vy = (trans_px[1] + q[1]) / 16.0 - ay
        vz = (trans_px[2] + q[2]) / 16.0 - az
        vx, vy, vz = vx * s, vy * s, vz * s      # 绕参照点缩放
        vx, vy = vx * cr - vy * sr, vx * sr + vy * cr    # 绕参照点横滚
        ad = _ads[0]
        out.append((fp.ARM_X + ax + vx + ad[0] / 16.0,
                    fp.ARM_Y + ay + vy + ad[1] / 16.0,
                    fp.ARM_Z + az + vz + ad[2] / 16.0))
    return out


fp.xform = xform_roll


def main(argv):
    geo, tex, out = argv[1], argv[2], argv[3]

    def val(name, default):
        return argv[argv.index(name) + 1] if name in argv else default

    tx = float(val('--tx', -2.6))
    ty = float(val('--ty', 1.4))
    tz = float(val('--tz', 1.8))
    ads = tuple(float(v) for v in val('--ads', '0,0,0').split(','))
    _ads[0] = ads
    _rollDeg[0] = float(val('--roll', 0.0))
    _scale[0] = float(val('--scale', 1.0))
    _dscale[0] = float(val('--dscale', 1.0))
    _anchor[0] = tuple(float(v) for v in val('--anchor', '0,0,0').split(','))
    fp.render(geo, tex, out, trans=(tx, ty, tz), rot=(0.0, 0.0, 0.0),
              fov=float(val('--fov', 45.0)), size=int(val('--h', 816)),
              aspect=float(val('--aspect', 1.79)), aim=False, kick=0.0, bp=-1.0,
              hands=('--hands' in argv), ss=2, pitch=0.0)


if __name__ == '__main__':
    main(sys.argv)
