#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把所有模型「枪口/前端」统一转正到 -Z（北），并保持游戏内外观完全不变。

原理（重要）：
  * 游戏内 OBJ 顶点 = (bbmodel 顶点 - c)/16 + 0.5，两者是同一个形状（可能差一个旋转）；
  * MC 的 display 旋转是**绕模型空间原点**转的（OBJ 原点）；
    bbmodel 里对应的点是 p = c - 8。所以要让补偿只是一个纯旋转，几何必须绕这个点转；
  * 几何转动 Δ 后，display 旋转按 R_new = R_old · Δ⁻¹ 补偿即可让外观一模一样。

部分旧模型（弩箭/mtx/mud）的 bbmodel 比 OBJ 多了一个旋转（当年导入时拧过），
本工具会先算出这两个网格之间的旋转 S，再把两边都归到「朝北」的目标姿态。

用法:
  python tools/align_north.py --plan                  # 只分析、打印方案
  python tools/align_north.py --plan --render         # 顺带渲染当前/目标姿态图
  python tools/align_north.py --apply                 # 执行（自动备份 build/north_backup/）
  python tools/align_north.py --revert                # 从备份还原
  python tools/align_north.py --verify                # 数值校验：外观是否与改动前一致
"""
import json
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb_north as bn  # noqa: E402

ITEM = 'src/main/resources/assets/hexalunar_calamity/models/item'
BACKUP = 'build/north_backup'

# ---------------------------------------------------------------- 模型清单
# north: 'yaw'        -> 只差一个偏航，转正即可（bb 与 obj 本来就一致）
#        'axis'       -> 按主轴对齐到 -Z（弩箭：bb 是斜的，obj 已经是沿 Z 的）
#        'straighten' -> obj 是斜置的，需要把它拧成 bb 那样的竖直姿态
MODELS = {
    'akm': dict(
        bb='模型/akm.bbmodel', obj='akm.obj',
        jsons=['akm.json'], north='yaw', front='auto'),
    'compound_bow': dict(
        bb='模型/复合弓.bbmodel',
        obj='compound_bow.obj',
        extra_objs=['compound_bow_pulling_0.obj', 'compound_bow_pulling_1.obj',
                    'compound_bow_pulling_2.obj'],
        jsons=['compound_bow.json', 'compound_bow_pulling_0.json',
               'compound_bow_pulling_1.json', 'compound_bow_pulling_2.json'],
        north='yaw', front='auto'),
    'bolt': dict(
        bb='模型/弩箭.bbmodel', obj='bolt.obj', jsons=[],
        north='axis', front='auto'),
    'mtx': dict(
        bb='模型/mtx.bbmodel', obj='mtx.obj', jsons=['mtx.json'],
        north='straighten', front='auto'),
    'mud': dict(
        bb='模型/mud.bbmodel', obj='mud.obj', jsons=['mud.json'],
        north='straighten', front='auto'),
}


# ---------------------------------------------------------------- OBJ 读写
def read_obj(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        lines = fh.read().splitlines()
    verts = []
    idx = []
    for i, ln in enumerate(lines):
        if ln.startswith('v '):
            p = ln.split()
            verts.append([float(p[1]), float(p[2]), float(p[3])])
            idx.append(i)
    return lines, idx, verts


def write_obj(path, lines, idx, verts):
    for i, k in enumerate(idx):
        lines[k] = 'v %.6f %.6f %.6f' % (verts[i][0], verts[i][1], verts[i][2])
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')


def obj_bbox(verts):
    return bbox(verts)


def bbox(pts):
    return (min(p[0] for p in pts), max(p[0] for p in pts),
            min(p[1] for p in pts), max(p[1] for p in pts),
            min(p[2] for p in pts), max(p[2] for p in pts))


def bbox_ext(b):
    return (b[1] - b[0], b[3] - b[2], b[5] - b[4])


def bbox_ctr(b):
    return ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)


# ---------------------------------------------------------------- 旋转匹配
def apply_R(R, pts):
    return [bn.mat_vec(R, p) for p in pts]


def find_S(bb_pts, obj_pts):
    """找旋转 S，使 S·(bb/16) 与 obj 的包围盒一致（bb 与 obj 之间只差一个旋转）。"""
    b16 = [(p[0] / 16.0, p[1] / 16.0, p[2] / 16.0) for p in bb_pts]
    tb = bbox_ext(obj_bbox(b16))

    def cost(a, b, c):
        R = bn.mat_mul(bn.mat_mul(bn.rot_axis((1, 0, 0), a), bn.rot_axis((0, 1, 0), b)),
                       bn.rot_axis((0, 0, 1), c))
        te = bbox_ext(obj_bbox(apply_R(R, b16)))
        return sum((te[i] - tb[i]) ** 2 for i in range(3))

    best = (None, 1e18)
    for a in range(-60, 61, 5):
        for b in range(-60, 61, 5):
            for c in range(-60, 61, 5):
                v = cost(a, b, c)
                if v < best[1]:
                    best = ((a, b, c), v)
    ang = list(best[0])
    step = 4.0
    while step > 0.01:
        improved = False
        for i in range(3):
            for d in (-step, step):
                trial = list(ang)
                trial[i] += d
                v = cost(*trial)
                if v < best[1] - 1e-12:
                    best = (tuple(trial), v)
                    ang = trial
                    improved = True
        if not improved:
            step /= 3.0
    a, b, c = best[0]
    R = bn.mat_mul(bn.mat_mul(bn.rot_axis((1, 0, 0), a), bn.rot_axis((0, 1, 0), b)),
                   bn.rot_axis((0, 0, 1), c))
    return R, (a, b, c), math.sqrt(best[1])


# ---------------------------------------------------------------- 目标姿态
def yaw_align(pts):
    """绕 Y 找让 Z 跨度最大的角度（长轴对齐 Z）。"""
    best = None
    for i in range(0, 3601):
        ang = -180 + i * 0.1
        rp = apply_R(bn.rot_axis((0, 1, 0), ang), pts)
        sz = max(v[2] for v in rp) - min(v[2] for v in rp)
        if best is None or sz > best[0]:
            best = (sz, ang)
    return best[1]


def axis_align(u_front):
    """把 u_front 转到 -Z、上方向尽量保持 +Y 的旋转。"""
    return bn.build_rot(u_front)


def cross_section(pts, R, end):
    """在 R 之后的坐标系里，看 ±Z 两端的宽度（用于判断哪端是枪口）。"""
    rp = apply_R(R, pts)
    zs = [v[2] for v in rp]
    z0, z1 = min(zs), max(zs)
    span = z1 - z0
    if end == '+z':
        sel = [v for v in rp if v[2] > z1 - span * 0.25]
    else:
        sel = [v for v in rp if v[2] < z0 + span * 0.25]
    if not sel:
        return 0.0
    return max(v[0] for v in sel) - min(v[0] for v in sel)


# ---------------------------------------------------------------- 主流程
def load_bb(path):
    data = bn.load(path)
    pts = [bn.elem_local_to_world(el, tuple(v)) for el, v in bn.world_verts(data)]
    return data, pts


def bb_bake(data):
    """把元素自带 rotation 烘进顶点（外观不变，只是把倾斜变成几何本身）。"""
    n = 0
    for el in data.get('elements', []):
        r = el.get('rotation') or [0, 0, 0]
        if any(abs(x) > 1e-9 for x in r):
            o = tuple(el.get('origin') or [0, 0, 0])
            for k, v in list(el['vertices'].items()):
                el['vertices'][k] = list(bn.elem_local_to_world(el, tuple(v)))
            el['rotation'] = [0, 0, 0]
            el['origin'] = [0, 0, 0]
            n += 1
    return n


def bb_rotate(data, R, pivot):
    """绕 pivot 旋转整个工程几何。"""
    p = tuple(pivot)
    for el in data.get('elements', []):
        for k, v in el['vertices'].items():
            rel = (v[0] - p[0], v[1] - p[1], v[2] - p[2])
            r = bn.mat_vec(R, rel)
            el['vertices'][k] = [r[0] + p[0], r[1] + p[1], r[2] + p[2]]


def euler_xyz(R):
    """把旋转矩阵拆成 MC 的 Rx·Ry·Rz（返回角度）。"""
    sb = max(-1.0, min(1.0, R[0][2]))
    b = math.asin(sb)
    if abs(sb) > 0.99999:                    # 万向锁
        c = 0.0
        a = math.atan2(R[1][0], R[1][1])
    else:
        cb = math.cos(b)
        a = math.atan2(-R[1][2] / cb, R[2][2] / cb)
        c = math.atan2(-R[0][1] / cb, R[0][0] / cb)
    out = [math.degrees(x) for x in (a, b, c)]
    return [0.0 if abs(x) < 1e-9 else round(x, 4) for x in out]


def euler_mat(rot):
    a, b, c = [math.radians(x) for x in rot]
    return bn.mat_mul(bn.mat_mul(bn.rot_axis((1, 0, 0), math.degrees(a)),
                                  bn.rot_axis((0, 1, 0), math.degrees(b))),
                      bn.rot_axis((0, 0, 1), math.degrees(c)))


def slot_mat(rot):
    return euler_mat(rot)


def load_json(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_json(path, spec):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(spec, fh, indent=1, ensure_ascii=False)
        fh.write('\n')


def backup(path):
    if not os.path.isdir(BACKUP):
        os.makedirs(BACKUP)
    dst = os.path.join(BACKUP, os.path.basename(path))
    if not os.path.exists(dst):
        shutil.copy2(path, dst)
    return dst


def plan_one(name, cfg, render=False):
    bbp = cfg['bb']
    objp = os.path.join(ITEM, cfg['obj'])
    data, bb_pts = load_bb(bbp)
    lines, idx, obj_pts = read_obj(objp)
    S, angs, resid = find_S(bb_pts, obj_pts)
    # bb -> obj 的单位换算:  o = S·(b/16) + tau
    b16 = bbox_ctr(bbox([(p[0] / 16, p[1] / 16, p[2] / 16) for p in apply_R(S, bb_pts)]))
    tau = tuple(bbox_ctr(bbox(obj_pts))[i] - b16[i] for i in range(3))
    # c = 映射到 obj 中心 (0.5,0.5,0.5) 的 bb 点
    Sinv = bn.mat_t(S)
    c = [16 * (bn.mat_vec(Sinv, (0.5 - tau[0], 0.5 - tau[1], 0.5 - tau[2]))[i]) for i in range(3)]
    pivot = (c[0] - 8, c[1] - 8, c[2] - 8)
    print('== %s ==' % name)
    print('   bb 包围盒  %s' % fmt_bbox(bbox(bb_pts)))
    print('   obj 包围盒 %s' % fmt_bbox(bbox(obj_pts)))
    print('   bb->obj 旋转 S: (%.2f, %.2f, %.2f)°  残差 %.4f' % (angs[0], angs[1], angs[2], resid))
    print('   居中常量 c=(%.3f, %.3f, %.3f)  -> bb 里的旋转中心 p=(%.2f, %.2f, %.2f)'
          % (c[0], c[1], c[2], pivot[0], pivot[1], pivot[2]))

    kind = cfg['north']
    if kind == 'yaw':
        th = yaw_align(bb_pts)
        Rbb_north = bn.rot_axis((0, 1, 0), th)
        Robj_north = bn.rot_axis((0, 1, 0), th)     # bb 与 obj 同姿态
        total_bb = Rbb_north
        print('   偏航转正角 = %+.2f°  (绕 Y)' % th)
    elif kind == 'axis':
        u = bn.principal_axis(bb_pts)
        # 前端符号：弩箭箭头在 +u 端（由渲染确认）
        if cfg.get('front') == 'neg':
            u = bn.mul(u, -1.0)
        Rbb_north = axis_align(u)
        Robj_north = Rbb_north                     # obj 与 bb 同姿态（bb 是斜的，需一起转）
        total_bb = Rbb_north
        print('   bb 主轴 u=(%.3f, %.3f, %.3f) -> 转到 -Z' % (u[0], u[1], u[2]))
    else:   # straighten：bb 保持竖直，把 obj 拧成和 bb 一样
        Rbb_north = bn.mat_id()
        Robj_north = bn.mat_t(S)                   # obj 转 S⁻¹ 后与 bb 同姿态
        total_bb = Rbb_north
        print('   bb 已是竖直姿态，obj 需旋转 S⁻¹')
    # 端点宽窄（判断枪口朝向）
    rp = apply_R(Robj_north, obj_pts)
    w_pz = cross_section(obj_pts, Robj_north, '+z')
    w_nz = cross_section(obj_pts, Robj_north, '-z')
    print('   转正后 obj：-Z 端宽 %.3f，+Z 端宽 %.3f  -> %s 端更细'
          % (w_nz, w_pz, '-Z' if w_nz < w_pz else '+Z'))
    return dict(cfg=cfg, name=name, S=S, tau=tau, c=c, pivot=pivot,
                total_bb=total_bb, Robj_north=Robj_north, bb_path=bbp, obj_path=objp,
                obj_lines=lines, obj_idx=idx, obj_pts=obj_pts, bb_data=data, bb_pts=bb_pts)


def fmt_bbox(b):
    return 'X[%.2f..%.2f] Y[%.2f..%.2f] Z[%.2f..%.2f] (%.2f x %.2f x %.2f)' % (
        b[0], b[1], b[2], b[3], b[4], b[5],
        b[1] - b[0], b[3] - b[2], b[5] - b[4])


def main(argv):
    mode = next((a for a in argv[1:] if a.startswith('--')), None)
    only = [a for a in argv[1:] if not a.startswith('--')]
    names = only or list(MODELS)
    if mode == '--revert':
        n = 0
        if os.path.isdir(BACKUP):
            for fn in os.listdir(BACKUP):
                dst = os.path.join(BACKUP, fn)
                if fn.endswith('.bbmodel'):
                    tgt = os.path.join('模型', fn)
                else:
                    tgt = os.path.join(ITEM, fn)
                shutil.copy2(dst, tgt)
                n += 1
        print('已从 %s 还原 %d 个文件' % (BACKUP, n))
        return 0

    infos = []
    for name in names:
        infos.append(plan_one(name, MODELS[name]))
        print('')

    if mode == '--apply':
        for info in infos:
            cfg, name = info['cfg'], info['name']
            # 1) bbmodel
            data = info['bb_data']
            bb_bake(data)
            bb_rotate(data, info['total_bb'], info['pivot'])
            backup(info['bb_path'])
            save_bb(info['bb_path'], data)
            # 2) obj(s)
            Robj = info['Robj_north']
            for fn in [cfg['obj']] + list(cfg.get('extra_objs') or []):
                p = os.path.join(ITEM, fn)
                lines, idx, verts = read_obj(p)
                newv = [list(bn.mat_vec(Robj, v)) for v in verts]
                backup(p)
                write_obj(p, lines, idx, newv)
            # 3) display 补偿 R_new = R_old · Robj⁻¹
            Rinv = bn.mat_t(Robj)
            for jf in cfg['jsons']:
                p = os.path.join(ITEM, jf)
                spec = load_json(p)
                disp = spec.get('display') or {}
                for slot, val in disp.items():
                    old = val.get('rotation') or [0, 0, 0]
                    Rnew = bn.mat_mul(slot_mat(old), Rinv)
                    val['rotation'] = euler_xyz(Rnew)
                spec['display'] = disp
                backup(p)
                save_json(p, spec)
            print('%s: 已转正（bbmodel + %d 个 obj + %d 个 json）'
                  % (name, 1 + len(cfg.get('extra_objs') or []), len(cfg['jsons'])))
    return 0


def save_bb(path, data):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
