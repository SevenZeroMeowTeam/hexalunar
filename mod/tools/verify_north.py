#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""校验转正前后「游戏内外观」是否完全一致。

对每个 display 槽位，用 MC 的变换链 world = T · (Rx·Ry·Rz) · S · x
分别算旧（旧 obj + 旧 json）与新（新 obj + 新 json）的顶点世界坐标，要求逐点相同。

用法: python tools/verify_north.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import north_align as na  # noqa: E402

BAK = na.BACKUP


def sample(pts, n=240):
    if len(pts) <= n:
        return pts
    idx = np.linspace(0, len(pts) - 1, n).astype(int)
    return pts[idx]


def transform(rot, trans, scale, pts):
    S = np.diag(scale)
    R = na.rotmat_xyz(rot)
    return (pts @ S.T @ R.T) + np.asarray(trans, dtype=float)


def main():
    ok_all = True
    for name, cfg in na.MODELS.items():
        if not cfg['jsons']:
            print('%-14s 无 json，跳过' % name)
            continue
        for jf in cfg['jsons']:
            newp = os.path.join(na.ITEM, jf)
            oldp = os.path.join(BAK, jf)
            if not os.path.exists(oldp):
                print('%-14s %s 无备份，跳过' % (name, jf))
                continue
            newj = json.load(open(newp, encoding='utf-8'))
            oldj = json.load(open(oldp, encoding='utf-8'))
            objn = jf.replace('.json', '.obj')
            if objn != jf and not os.path.exists(os.path.join(na.ITEM, objn)):
                objn = cfg['obj']
            lines, idx, vnew = na.read_obj(os.path.join(na.ITEM, objn))
            lines2, idx2, vold = na.read_obj(os.path.join(BAK, objn))
            pn, po = sample(vnew), sample(vold)
            worst = 0.0
            slots = set(list(newj.get('display', {}).keys()) + list(oldj.get('display', {}).keys()))
            for slot in sorted(slots):
                a = (oldj.get('display') or {}).get(slot) or {}
                b = (newj.get('display') or {}).get(slot) or {}
                wa = transform(a.get('rotation', [0, 0, 0]), a.get('translation', [0, 0, 0]),
                               a.get('scale', [1, 1, 1]), po)
                wb = transform(b.get('rotation', [0, 0, 0]), b.get('translation', [0, 0, 0]),
                               b.get('scale', [1, 1, 1]), pn)
                d = float(np.abs(wa - wb).max())
                worst = max(worst, d)
                flag = 'OK  ' if d < 2e-4 else 'FAIL'
                if d >= 2e-4:
                    ok_all = False
                print('  %s %-14s %-22s rot %-22s -> %-22s  dv=%.6f'
                      % (flag, name, slot,
                         str(a.get('rotation', [0, 0, 0])), str(b.get('rotation', [0, 0, 0])), d))
            print('%-14s %-26s 最大偏差 %.6f' % ('', jf, worst))
    print('')
    print('全部通过' if ok_all else '存在偏差，请检查！')
    return 0 if ok_all else 1


if __name__ == '__main__':
    sys.exit(main())
