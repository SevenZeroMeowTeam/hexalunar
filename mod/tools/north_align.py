#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把所有模型「枪口/前端」统一转正到 -Z（北），并保持游戏内外观完全不变。

原理（关键）：
  * 游戏内 OBJ 顶点 = (bbmodel 顶点 - c)/16 + 0.5 —— 两者是同一个形状（可能差一个旋转）；
  * MC 的 display 旋转是绕**模型空间原点**（OBJ 原点）转的；bbmodel 里对应点是
    p = c - 8（bbmodel 居中在原点、OBJ 居中在 (0.5,0.5,0.5)）。
    所以几何必须绕 p 旋转，display 才能用「纯旋转」补偿；
  * 几何转动 Δ 后，display 按 R_new = R_old · Δ⁻¹ 补偿 ⇒ 外观一模一样。

旧模型（弩箭/mtx/mud）的 bbmodel 当年导入时多拧了一个角度、与 OBJ 不一致，
本工具先算出这个旋转 S，再把两边都归到同一目标姿态。

用法:
  python tools/north_align.py --plan                    # 分析并打印方案
  python tools/north_align.py --plan --render           # 另存点云对比图 build/north/
  python tools/north_align.py --apply                   # 执行（备份 build/north_backup/）
  python tools/north_align.py --revert                  # 还原
  python tools/north_align.py --apply akm compound_bow  # 只处理指定模型
"""
import json
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb_north as bn  # noqa: E402

ITEM = 'src/main/resources/assets/hexalunar_calamity/models/item'
BACKUP = 'build/north_backup'

MODELS = {
    'akm': dict(bb='模型/akm.bbmodel', obj='akm.obj', jsons=['akm.json'],
                extra_objs=['akm_bolt.obj', 'akm_mag.obj'],
                north='yaw', front='narrow'),
    'compound_bow': dict(bb='模型/复合弓.bbmodel', obj='compound_bow.obj',
                         extra_objs=['compound_bow_pulling_0.obj',
                                     'compound_bow_pulling_1.obj',
                                     'compound_bow_pulling_2.obj'],
                         jsons=['compound_bow.json', 'compound_bow_pulling_0.json',
                                'compound_bow_pulling_1.json',
                                'compound_bow_pulling_2.json'],
                         north='yaw', front='wide'),
    'bolt': dict(bb='模型/弩箭.bbmodel', obj='bolt.obj', jsons=[],
                 north='flip', front='narrow'),
    'mtx': dict(bb='模型/mtx.bbmodel', obj='mtx.obj', jsons=['mtx.json'],
                north='straighten'),
    'mud': dict(bb='模型/mud.bbmodel', obj='mud.obj', jsons=['mud.json'],
                north='straighten'),
}


# ------------------------------------------------------------------ 数学
def bbox(pts):
    return pts.min(axis=0), pts.max(axis=0)


def ext_of(pts):
    lo, hi = bbox(pts)
    return hi - lo


def rotmat(axis, deg):
    return np.asarray(bn.rot_axis(axis, deg), dtype=float)


def rotmat_xyz(rot):
    a, b, c = rot
    return rotmat((1, 0, 0), a) @ rotmat((0, 1, 0), b) @ rotmat((0, 0, 1), c)


def euler_xyz(R):
    """旋转矩阵 -> MC 的 Rx·Ry·Rz 角度（度）。"""
    sb = max(-1.0, min(1.0, float(R[0][2])))
    b = math.asin(sb)
    if abs(sb) > 0.99999:
        c = 0.0
        a = math.atan2(R[1][0], R[1][1])
    else:
        cb = math.cos(b)
        a = math.atan2(-R[1][2] / cb, R[2][2] / cb)
        c = math.atan2(-R[0][1] / cb, R[0][0] / cb)
    out = [math.degrees(x) for x in (a, b, c)]
    return [0.0 if abs(x) < 1e-9 else round(x, 4) for x in out]


def pca_frame(pts):
    a = pts - pts.mean(axis=0)
    cov = a.T @ a / max(len(a) - 1, 1)
    w, v = np.linalg.eigh(cov)
    order = np.argsort(w)[::-1]
    return v[:, order]


def principal_axis(pts):
    return pca_frame(pts)[:, 0]


# ------------------------------------------------------------------ 读入
def load_bb(path):
    data = bn.load(path)
    pts = [bn.elem_local_to_world(el, tuple(v)) for el, v in bn.world_verts(data)]
    return data, np.asarray(pts, dtype=float)


def read_obj(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        lines = fh.read().splitlines()
    verts, idx = [], []
    for i, ln in enumerate(lines):
        if ln.startswith('v '):
            p = ln.split()
            verts.append((float(p[1]), float(p[2]), float(p[3])))
            idx.append(i)
    return lines, idx, np.asarray(verts, dtype=float)


def write_obj(path, lines, idx, verts):
    out = []
    for i, k in enumerate(idx):
        v = verts[i]
        out.append((k, 'v %.6f %.6f %.6f' % (v[0], v[1], v[2])))
    for k, s in out:
        lines[k] = s
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')


# ------------------------------------------------------------------ bb<->obj
def support_match(bb_pts, obj_pts, S, ndir=96):
    """支撑函数校验：两个网格是否同形状（先各自居中，返回最大偏差，单位=方块）。"""
    k = np.arange(ndir) + 0.5
    phi = np.arccos(1 - 2 * k / ndir)
    theta = np.pi * (1 + 5 ** 0.5) * k
    D = np.stack([np.cos(theta) * np.sin(phi), np.sin(theta) * np.sin(phi),
                  np.cos(phi)], axis=1)              # ndir x 3
    b = bb_pts / 16.0
    b = b - b.mean(axis=0)
    o = obj_pts - obj_pts.mean(axis=0)
    hb = (b @ S.T @ D.T).max(axis=0)
    ho = (o @ D.T).max(axis=0)
    return float(np.abs(hb - ho).max())


def elem_rot_mat(data):
    """bbmodel 元素自带 rotation 的矩阵（旧模型靠它把斜置网格拧成竖直）。"""
    for el in data.get('elements', []):
        r = el.get('rotation') or [0, 0, 0]
        if any(abs(x) > 1e-9 for x in r):
            return rotmat_xyz(r), list(r)
    return None, None


def find_S(bb_pts, obj_pts):
    """S 使 S·(bb/16) 与 obj 同形状（只差平移）。主轴坐标系 + 符号组合 + 细化。"""
    b16 = bb_pts / 16.0
    uq = lambda a: np.unique(np.round(a, 4), axis=0)   # noqa: E731
    Vb = pca_frame(uq(b16))
    Vo = pca_frame(uq(obj_pts))
    tb = ext_of(obj_pts)
    cands = [np.eye(3)]          # 两个网格本来就同姿态时优先选单位阵
    for s0 in (1, -1):
        for s1 in (1, -1):
            for s2 in (1, -1):
                R = Vo @ np.diag([s0, s1, s2]) @ Vb.T
                if np.linalg.det(R) > 0:
                    cands.append(R)
    best = (None, 1e18)
    for R in cands:
        v = float(np.sum((ext_of(b16 @ R.T) - tb) ** 2))
        if v < best[1]:
            best = (R, v)
    cur, curv = best[0].copy(), best[1]
    step = 2.0
    while step > 0.01:
        improved = False
        for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            for d in (step, -step):
                cand = rotmat(axis, d) @ cur
                c = float(np.sum((ext_of(b16 @ cand.T) - tb) ** 2))
                if c < curv - 1e-12:
                    cur, curv, improved = cand, c, True
        if not improved:
            step /= 3.0
    return cur, math.sqrt(curv)


def tau_of(S, bb_pts, obj_pts):
    cb = (bbox(bb_pts / 16.0 @ S.T)[0] + bbox(bb_pts / 16.0 @ S.T)[1]) / 2
    co = (bbox(obj_pts)[0] + bbox(obj_pts)[1]) / 2
    return co - cb


def yaw_align(pts):
    """绕 Y 扫，使 Z 跨度最大（两级细化）。"""
    z, x = pts[:, 2], pts[:, 0]

    def best_in(a0, a1, step):
        angs = np.arange(a0, a1, step)
        c, s = np.cos(np.radians(angs)), np.sin(np.radians(angs))
        zp = np.outer(z, c) - np.outer(x, s)
        spans = zp.max(axis=0) - zp.min(axis=0)
        k = int(np.argmax(spans))
        return float(angs[k]), float(spans[k])

    a, _ = best_in(-180.0, 180.0, 0.1)
    a2, _ = best_in(a - 0.2, a + 0.2, 0.004)
    return a2, a


def end_widths(pts, R, frac=0.25):
    a = pts @ R.T
    z = a[:, 2]
    z0, z1 = z.min(), z.max()
    span = max(z1 - z0, 1e-9)
    lo = a[z < z0 + span * frac]
    hi = a[z > z1 - span * frac]
    w = lambda s: float(s[:, 0].max() - s[:, 0].min()) if len(s) else 0.0   # noqa: E731
    return w(lo), w(hi)


# ------------------------------------------------------------------ bb 变换
def bb_bake(data):
    n = 0
    for el in data.get('elements', []):
        r = el.get('rotation') or [0, 0, 0]
        if any(abs(x) > 1e-9 for x in r):
            for k, v in list(el['vertices'].items()):
                el['vertices'][k] = list(bn.elem_local_to_world(el, tuple(v)))
            el['rotation'] = [0, 0, 0]
            el['origin'] = [0, 0, 0]
            n += 1
    return n


def bb_rotate(data, R, pivot):
    p = np.asarray(pivot, dtype=float)
    for el in data.get('elements', []):
        for k, v in el['vertices'].items():
            el['vertices'][k] = list(R @ (np.asarray(v, dtype=float) - p) + p)


# ------------------------------------------------------------------ 备份
def backup(path):
    os.makedirs(BACKUP, exist_ok=True)
    dst = os.path.join(BACKUP, os.path.basename(path))
    if not os.path.exists(dst):
        shutil.copy2(path, dst)
    return dst


def fmt(b):
    lo, hi = b
    return ('X[%.2f..%.2f] Y[%.2f..%.2f] Z[%.2f..%.2f] (%.2f x %.2f x %.2f)'
            % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
               hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))


# ------------------------------------------------------------------ 单个模型
def plan_one(name, cfg, render=False):
    objp = os.path.join(ITEM, cfg['obj'])
    data, bb_pts = load_bb(cfg['bb'])
    lines, idx, obj_pts = read_obj(objp)
    S_num, resid = find_S(bb_pts, obj_pts)
    E, eangles = elem_rot_mat(data)
    S = S_num
    sm_num = support_match(bb_pts, obj_pts, S_num)
    if E is not None:
        cand = E.T
        sm_e = support_match(bb_pts, obj_pts, cand)
        print('== %s ==' % name)
        print('   elem rot %s -> S support 偏差 %.5f ; 数值解 %.5f'
              % (eangles, sm_e, sm_num))
        if sm_e <= sm_num:
            S = cand
    tau = tau_of(S, bb_pts, obj_pts)
    cc = 16.0 * (S.T @ (np.array([0.5, 0.5, 0.5]) - tau))
    pivot = cc - 8.0
    kind = cfg['north']
    if not name.startswith('__'):
        print('== %s ==' % name)
    else:
        print('== %s ==' % name)
    print('   bb   %s' % fmt(bbox(bb_pts)))
    print('   obj  %s' % fmt(bbox(obj_pts)))
    print('   S(bb->obj) = (%.2f, %.2f, %.2f) deg   resid %.3f   support %.5f'
          % tuple(list(euler_xyz(S)) + [resid, support_match(bb_pts, obj_pts, S)]))
    print('   bb pivot p = (%.2f, %.2f, %.2f)' % tuple(pivot))
    w0o, w1o = end_widths(obj_pts, np.eye(3))
    print('   obj now : -Z end %.3f   +Z end %.3f' % (w0o, w1o))

    def pick_by_front(cands):
        """在候选中选一个使「前端」落在 -Z 的。front=narrow: -Z 端最窄; wide: -Z 端最宽。"""
        best = None
        for T in cands:
            w0, w1 = end_widths(obj_pts, T)
            score = (w1 - w0) if cfg.get('front') == 'narrow' else (w0 - w1)
            if best is None or score > best[0]:
                best = (score, T, (w0, w1))
        return best

    if kind == 'yaw':
        th, th_coarse = yaw_align(obj_pts)
        cands = [rotmat((0, 1, 0), a) for a in (th, th + 180.0, th - 180.0)]
        _, T, (w0, w1) = pick_by_front(cands)
        print('   yaw scan %+.2f deg (coarse %+.2f) -> pick %+.2f deg'
              % (th, th_coarse, euler_xyz(T)[1] if abs(euler_xyz(T)[0]) < 1e-6 else euler_xyz(T)[1]))
    elif kind == 'flip':
        cands = [np.eye(3), rotmat((0, 1, 0), 180.0), rotmat((1, 0, 0), 180.0)]
        _, T, (w0, w1) = pick_by_front(cands)
        print('   flip pick = (%.2f, %.2f, %.2f) deg' % tuple(euler_xyz(T)))
    else:                                    # straighten
        T = S.T
        print('   T = S^-1 (obj 拧正到 bb 的竖直姿态)')
        w0, w1 = end_widths(obj_pts, T)
    Rbb = T @ S
    Robj = T
    print('   Rbb = (%.2f, %.2f, %.2f) deg   Robj = (%.2f, %.2f, %.2f) deg'
          % tuple(list(euler_xyz(Rbb)) + list(euler_xyz(Robj))))
    print('   target: -Z end %.3f  +Z end %.3f  -> %s side narrower'
          % (w0, w1, '-Z' if w0 < w1 else '+Z'))
    print('   obj target bbox %s' % fmt(bbox(obj_pts @ Robj.T)))
    print('   bb  target bbox %s' % fmt(bbox((bb_pts - pivot) @ Rbb.T + pivot)))
    info = dict(name=name, cfg=cfg, data=data, bb_pts=bb_pts, obj_lines=lines,
                obj_idx=idx, obj_pts=obj_pts, S=S, tau=tau, pivot=pivot,
                Rbb=Rbb, Robj=Robj, cc=cc)
    if render:
        render_check(info)
    print('')
    return info


def render_check(info):
    from PIL import Image, ImageDraw
    os.makedirs('build/north', exist_ok=True)
    newbb = (info['bb_pts'] - info['pivot']) @ info['Rbb'].T + info['pivot']
    newobj = info['obj_pts'] @ info['Robj'].T
    panels = [('bb 现在', info['bb_pts']), ('bb 转正后', newbb),
              ('obj 现在', info['obj_pts']), ('obj 转正后', newobj)]
    imgs = [(tag, cloud(pts)) for tag, pts in panels]
    w = sum(im.width for _, im in imgs) + 8 * (len(imgs) - 1)
    h = max(im.height for _, im in imgs)
    canvas = Image.new('RGB', (w, h + 20), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    x = 0
    for tag, im in imgs:
        canvas.paste(im, (x, 20))
        d.text((x + 4, 5), tag, fill=(0, 0, 0))
        x += im.width + 8
    out = 'build/north/%s_check.png' % info['name']
    canvas.save(out)
    print('   -> %s' % out)


def cloud(pts, size=360, margin=16):
    """侧视点云：横轴 Z（右 = +Z），纵轴 Y（上 = +Y）。"""
    from PIL import Image, ImageDraw
    z, y = pts[:, 2], pts[:, 1]
    spanz = max(z.max() - z.min(), 1e-6)
    spany = max(y.max() - y.min(), 1e-6)
    sc = min((size - 2 * margin) / spanz, (size - 2 * margin) / spany)
    img = Image.new('RGB', (size, size), (250, 250, 246))
    d = ImageDraw.Draw(img)
    px = margin + (z - z.min()) * sc
    py = size - margin - (y - y.min()) * sc
    for a, b in zip(px, py):
        d.point((a, b), fill=(70, 70, 110))
    ox = margin + (0 - z.min()) * sc
    oy = size - margin - (0 - y.min()) * sc
    d.line([ox - 5, oy, ox + 5, oy], fill=(200, 0, 0), width=2)
    d.line([ox, oy - 5, ox, oy + 5], fill=(200, 0, 0), width=2)
    return img


# ------------------------------------------------------------------ 主入口
def main(argv):
    mode = next((a for a in argv[1:] if a.startswith('--')), None)
    render = '--render' in argv
    only = [a for a in argv[1:] if not a.startswith('--')]
    names = only or list(MODELS)
    if mode == '--revert':
        n = 0
        if os.path.isdir(BACKUP):
            for fn in os.listdir(BACKUP):
                src = os.path.join(BACKUP, fn)
                tgt = (os.path.join('模型', fn) if fn.endswith('.bbmodel')
                       else os.path.join(ITEM, fn))
                shutil.copy2(src, tgt)
                n += 1
        print('已从 %s 还原 %d 个文件' % (BACKUP, n))
        return 0

    infos = [plan_one(n, MODELS[n], render=render) for n in names]

    if mode == '--apply':
        for info in infos:
            cfg = info['cfg']
            data = info['data']
            bb_bake(data)
            bb_rotate(data, info['Rbb'], info['pivot'])
            backup(cfg['bb'])
            with open(cfg['bb'], 'w', encoding='utf-8') as fh:
                json.dump(data, fh, ensure_ascii=False)
            Robj = info['Robj']
            for fn in [cfg['obj']] + list(cfg.get('extra_objs') or []):
                p = os.path.join(ITEM, fn)
                lines, idx, verts = read_obj(p)
                backup(p)
                write_obj(p, lines, idx, verts @ Robj.T)
            Rinv = Robj.T
            for jf in cfg['jsons']:
                p = os.path.join(ITEM, jf)
                with open(p, 'r', encoding='utf-8') as fh:
                    spec = json.load(fh)
                disp = spec.get('display') or {}
                for slot, val in disp.items():
                    Rnew = rotmat_xyz(val.get('rotation') or [0, 0, 0]) @ Rinv
                    val['rotation'] = euler_xyz(Rnew)
                spec['display'] = disp
                backup(p)
                with open(p, 'w', encoding='utf-8') as fh:
                    json.dump(spec, fh, indent=1, ensure_ascii=False)
                    fh.write('\n')
            print('%s 已应用：bbmodel + %d obj + %d json'
                  % (info['name'], 1 + len(cfg.get('extra_objs') or []), len(cfg['jsons'])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
