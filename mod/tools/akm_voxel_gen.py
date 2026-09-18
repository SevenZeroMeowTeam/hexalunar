#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 模型/akm.bbmodel（真枪外形网格）体素化成 GeckoLib 方块骨骼模型。

为什么这么做：
  实测 GeckoLib 4.8.4（1.20.1）**只解析 poly_mesh、不渲染它** ——
  cache/object/GeoBone 里只有 getCubes()，没有网格字段，
  用 poly_mesh 的模型能加载但游戏里看不见。
  所以把参考网格按 0.5px 体素化：外形 = 参考枪的轮廓，
  每个体素面的 UV 直接从参考贴图（2048→512）采样，
  于是颜色/细节全部来自用户自己的参考模型。

骨骼沿用 12 根真骨骼（body/bolt/magazine/stock/...），换弹、拉栓动画照旧能驱动。

产出：
  geo/akm.geo.json             方块骨骼模型（GeckoLib 可渲染）
  textures/models/akm_geo.png  512x512 贴图
  模型/akm_voxel.bbmodel       Blockbench 工程（方块 + 骨骼分组）

用法: python tools/akm_voxel_gen.py [--step 0.5] [--tex 512] [--no-bbmodel]
"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from akm_mesh_gen import BONES            # 骨骼定义（单点维护）

REF = '模型/akm.bbmodel'
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png'
BB_OUT = '模型/akm_voxel.bbmodel'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def ray_tri(orig, d, a, b, c):
    """Möller–Trumbore，返回 (t, u, v)。"""
    e1 = sub(b, a)
    e2 = sub(c, a)
    p = cross(d, e2)
    det = dot(e1, p)
    if abs(det) < 1e-12:
        return None
    inv = 1.0 / det
    t1 = sub(orig, a)
    u = dot(t1, p) * inv
    if u < -1e-6 or u > 1.0 + 1e-6:
        return None
    q = cross(t1, e1)
    v = dot(d, q) * inv
    if v < -1e-6 or u + v > 1.0 + 1e-6:
        return None
    t = dot(e2, q) * inv
    if t <= 1e-6:
        return None
    return t, u, v


def load_ref(path=None):
    with open(path or REF, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    el = data['elements'][0]
    verts = {k: tuple(v) for k, v in el['vertices'].items()}
    tris, seen = [], set()
    for f in el['faces'].values():
        vids = [v for v in f.get('vertices') or [] if v in verts]
        if len(vids) < 3:
            continue
        uvmap = f.get('uv') or {}
        uv = [uvmap.get(v, (0.0, 0.0)) for v in vids]
        # 扇形三角化
        for i in range(1, len(vids) - 1):
            a, b, c = verts[vids[0]], verts[vids[i]], verts[vids[i + 1]]
            # 自由模型同一表面常常有正反两层，按顶点集合去重，否则奇偶判定失效
            key = tuple(sorted(
                tuple(round(c, 3) for c in v) for v in (a, b, c)))
            if key in seen:
                continue
            seen.add(key)
            tris.append((a, b, c, uv[0], uv[i], uv[i + 1]))
    tex = None
    for t in data.get('textures') or []:
        src = t.get('source') or ''
        if src.startswith('data:image'):
            tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGB')
            break
    res = data.get('resolution') or {}
    return verts, tris, tex, res.get('width', 2048) or 2048, res.get('height', 2048) or 2048


def voxelize(tris, step, uv_w, uv_h, quiet=False):
    """返回 {cell: (u, v)}：cell = (ix, iy, iz)，u/v 为命中面在 UV 空间的坐标。"""
    xs = [p[i][0] for p in tris for i in range(3)]
    ys = [p[i][1] for p in tris for i in range(3)]
    zs = [p[i][2] for p in tris for i in range(3)]
    lo = (min(xs), min(ys), min(zs))
    hi = (max(xs), max(ys), max(zs))
    if not quiet:
        print('网格包围盒  x %.2f~%.2f  y %.2f~%.2f  z %.2f~%.2f' %
              (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))

    # 按 YZ 分桶（射线沿 +X，只需查同格三角面）
    ny = int((hi[1] - lo[1]) / step) + 2
    nz = int((hi[2] - lo[2]) / step) + 2
    buckets = {}
    for t in tris:
        iy0 = max(0, int((min(t[i][1] for i in range(3)) - lo[1]) / step))
        iy1 = min(ny - 1, int((max(t[i][1] for i in range(3)) - lo[1]) / step))
        iz0 = max(0, int((min(t[i][2] for i in range(3)) - lo[2]) / step))
        iz1 = min(nz - 1, int((max(t[i][2] for i in range(3)) - lo[2]) / step))
        for iy in range(iy0, iy1 + 1):
            for iz in range(iz0, iz1 + 1):
                buckets.setdefault((iy, iz), []).append(t)

    nx = int((hi[0] - lo[0]) / step) + 1
    d = (1.0, 0.0, 0.0)
    cells = {}
    stats = [0, 0]
    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                cand = buckets.get((iy, iz))
                if not cand:
                    continue
                cx = lo[0] + (ix + 0.5) * step
                cy = lo[1] + (iy + 0.5) * step
                cz = lo[2] + (iz + 0.5) * step
                orig = (lo[0] - 1.0, cy, cz)
                hits = []
                for t in cand:
                    r = ray_tri(orig, d, t[0], t[1], t[2])
                    if r:
                        hits.append((r[0], r[1], r[2], t))
                if not hits:
                    continue
                stats[0] += 1
                hits.sort(key=lambda h: h[0])
                ox = lo[0] - 1.0
                # 单层壳模型：按"穿入/穿出"成对填充，薄壁吸附到最近一格
                spans = []
                k = 0
                while k + 1 < len(hits):
                    spans.append((hits[k], hits[k + 1]))
                    k += 2
                if len(hits) % 2 == 1:
                    spans.append((hits[-1], hits[-1]))
                for h0, h1 in spans:
                    t0 = ox + h0[0]
                    t1 = ox + h1[0]
                    if t1 - t0 < step * 0.5:        # 薄壁：至少覆盖一格
                        mid = (t0 + t1) * 0.5
                        t0, t1 = mid - step * 0.25, mid + step * 0.25
                    j0 = max(0, int(math.floor((t0 - lo[0]) / step + 1e-9)))
                    j1 = min(nx - 1, int(math.ceil((t1 - lo[0]) / step - 1e-9)) - 1)
                    if j1 < j0 or not (j0 <= ix <= j1):
                        continue
                    stats[1] += 1
                    t_, u_, v_, tri = h0            # 入射面 -> 贴图坐标
                    ua, ub, uc = tri[3], tri[4], tri[5]
                    w0, w1, w2 = 1.0 - u_ - v_, u_, v_
                    uu = ua[0] * w0 + ub[0] * w1 + uc[0] * w2
                    vv = ua[1] * w0 + ub[1] * w1 + uc[1] * w2
                    cells[(ix, iy, iz)] = (uu, vv)
                    break
    if not quiet:
        print('  有命中射线的格子 %d，填充为实体的 %d' % (stats[0], stats[1]))
    return cells, lo, hi


def region_vox(cx, cy, cz):
    """按参考网格实测轮廓划分部件（侧视图：枪口在 -z，枪托在 +z）。"""
    if cz < -5.55:                          # 枪口 / 枪管
        return 'barrel'
    if cz < -3.15:                          # 护木
        return 'handguard'
    if cy > 3.55 and cz < -2.3:             # 照门
        return 'rear_sight'
    if cy > 3.05 and cz < 0.35:             # 机匣盖
        return 'dust_cover'
    if abs(cx) > 1.05 and -1.9 < cz < -0.25 and cy > 2.3:
        return 'bolt'                       # 拉机柄（可见的枪机部分）
    if cy < 1.75 and -2.35 < cz < -0.65:    # 弹匣
        return 'magazine'
    if cy < 1.75 and 2.3 < cz < 3.3:        # 扳机
        return 'trigger'
    if cy < 1.8 and 3.3 <= cz < 5.0:        # 握把
        return 'grip'
    if cz >= 5.0:                           # 枪托
        return 'stock'
    return 'body'


def rot_y(p, c, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    x, z = p[0] - c[0], p[2] - c[2]
    return (c[0] + x * ca + z * sa, p[1], c[2] - x * sa + z * ca)


def rotate_tris(tris, deg):
    """绕 Y 轴整体旋转（UV 不变）。"""
    xs = [t[i][0] for t in tris for i in range(3)]
    zs = [t[i][2] for t in tris for i in range(3)]
    c = ((min(xs) + max(xs)) / 2, 0.0, (min(zs) + max(zs)) / 2)
    out = []
    for t in tris:
        out.append((rot_y(t[0], c, deg), rot_y(t[1], c, deg), rot_y(t[2], c, deg),
                    t[3], t[4], t[5]))
    return out


def yaw_slope(cells, lo, step):
    """每层 z 的平均 x 对 z 的斜率 = 偏航量。"""
    by = {}
    for (ix, iz) in set((c[0], c[2]) for c in cells):
        by.setdefault(iz, []).append(lo[0] + (ix + 0.5) * step)
    zs = sorted(by)
    if len(zs) < 4:
        return 0.0
    xs = [sum(by[z]) / len(by[z]) for z in zs]
    zz = [lo[2] + (z + 0.5) * step for z in zs]
    n = len(zs)
    mx, mz = sum(xs) / n, sum(zz) / n
    den = sum((zz[i] - mz) ** 2 for i in range(n)) or 1e-9
    return sum((zz[i] - mz) * (xs[i] - mx) for i in range(n)) / den


def main(argv):
    step = 0.5
    if '--step' in argv:
        step = float(argv[argv.index('--step') + 1])
    tex_size = 512
    if '--tex' in argv:
        tex_size = int(argv[argv.index('--tex') + 1])

    verts, tris, tex, uv_w, uv_h = load_ref()
    print('参考网格: %d 顶点 / %d 三角面   UV 空间 %dx%d' % (len(verts), len(tris), uv_w, uv_h))
    if tex is None:
        raise SystemExit('参考工程里没有内嵌贴图')
    tex.resize((tex_size, tex_size), Image.LANCZOS).save(TEX_OUT)
    print('贴图 -> %d x %d' % (tex_size, tex_size))

    # ---- 自动摆正：参考模型本身带一点偏航，枪口必须正对北(-Z) ----
    cells0, lo0, hi0 = voxelize(tris, step, uv_w, uv_h)
    s0 = yaw_slope(cells0, lo0, step)
    cells, lo, hi = cells0, lo0, hi0
    total = 0.0
    for _round in range(2):
        s_cur = yaw_slope(cells, lo, step)
        if abs(s_cur) < 0.004:            # < 0.25° 就停
            break
        best = None
        for deg in (math.degrees(math.atan(s_cur)), -math.degrees(math.atan(s_cur))):
            t2 = rotate_tris(tris, total + deg)
            c2, l2, h2 = voxelize(t2, step, uv_w, uv_h, quiet=True)
            s2 = yaw_slope(c2, l2, step)
            if best is None or abs(s2) < abs(best[0]):
                best = (s2, total + deg, c2, l2, h2)
        _s, total, cells, lo, hi = best
    if abs(total) > 0.05:
        print('自动摆正: 偏航 %.2f° -> %.2f°（共旋转 %.2f°）' %
              (math.degrees(math.atan(s0)), math.degrees(math.atan(yaw_slope(cells, lo, step))), total))
    print('体素 %.2fpx -> %d 个方块' % (step, len(cells)))

    # 体素在贴图上的覆盖尺寸（1 体素 = step 世界像素）
    su, sv = tex_size / float(uv_w), tex_size / float(uv_h)
    wu, wv = step * su, step * sv

    # ---- 先分区，再以握把为原点（手持时枪正好握在手里）----
    regs = {}
    centers = {}
    for (ix, iy, iz), (u, v) in cells.items():
        cx = lo[0] + (ix + 0.5) * step
        cy = lo[1] + (iy + 0.5) * step
        cz = lo[2] + (iz + 0.5) * step
        r = region_vox(cx, cy, cz)
        regs[(ix, iy, iz)] = r
        centers.setdefault(r, []).append((cx, cy, cz))
    for k in sorted(centers):
        print('   %-12s %4d 方块' % (k, len(centers[k])))
    g = centers.get('grip') or centers.get('trigger')
    if g:
        # x 以整枪为中心（手持时枪在手掌正中），y/z 以握把为原点
        delta = (-(lo[0] + hi[0]) / 2, -sum(p[1] for p in g) / len(g),
                 -sum(p[2] for p in g) / len(g))
    else:
        delta = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -(lo[2] + hi[2]) / 2)
    print('原点偏移（握把归零）: %.2f, %.2f, %.2f' % delta)

    buckets = {b[0]: [] for b in BONES}
    for (ix, iy, iz), (u, v) in cells.items():
        x0 = lo[0] + ix * step + delta[0]
        y0 = lo[1] + iy * step + delta[1]
        z0 = lo[2] + iz * step + delta[2]
        face = {'uv': [round(u - wu / 2, 3), round(v - wv / 2, 3)],
                'uv_size': [round(wu, 3), round(wv, 3)]}
        cube = {
            'origin': [round(x0, 4), round(y0, 4), round(z0, 4)],
            'size': [round(step, 4)] * 3,
            'uv': {f: dict(face) for f in FACES},
        }
        buckets[regs[(ix, iy, iz)]].append(cube)

    out_bones = []
    for name, parent, piv in BONES:
        cubes = buckets.get(name) or []
        if cubes:
            # 旋转轴用心：该部件所有方块的中心
            n = len(cubes)
            piv = tuple(round((sum(c['origin'][i] + step / 2 for c in cubes) / n), 4)
                        for i in range(3))
        else:
            piv = tuple(round(piv[i] + delta[i], 4) for i in range(3))
        b = {'name': name, 'pivot': list(piv)}
        if parent:
            b['parent'] = parent
        if cubes:
            b['cubes'] = cubes
        out_bones.append(b)
    geo = {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.akm',
                'texture_width': tex_size, 'texture_height': tex_size,
                'visible_bounds_width': 3, 'visible_bounds_height': 3,
                'visible_bounds_offset': [0, 1.2, 0],
            },
            'bones': out_bones,
        }],
    }
    os.makedirs(os.path.dirname(GEO_OUT), exist_ok=True)
    with open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    print('模型 -> %s （%d 骨骼 / %d 方块）' % (GEO_OUT, len(out_bones), len(cells)))

    if '--no-bbmodel' not in argv:
        pivots = {b['name']: b['pivot'] for b in out_bones}
        elements, groups = [], []
        for name, parent, _piv in BONES:
            cubes = buckets.get(name) or []
            if not cubes:
                continue
            piv = pivots[name]
            uu = _uuid(name)
            for i, c in enumerate(cubes):
                o, s = c['origin'], c['size']
                elements.append({
                    'name': '%s_%d' % (name, i), 'type': 'cube', 'uuid': _uuid('%s_%d' % (name, i)),
                    'origin': o, 'size': s, 'inflate': 0,
                    'uv': c['uv'], 'visibility': True, 'export': True, 'locked': False,
                })
            groups.append({'name': name, 'uuid': uu, 'origin': list(piv), 'rotation': [0, 0, 0],
                           'children': [_uuid('%s_%d' % (name, i)) for i in range(len(cubes))],
                           'visibility': True, 'autouv': 0, 'color': 0, 'export': True,
                           'locked': False, 'isOpen': False, 'parent': parent or 'root'})
        with open(TEX_OUT, 'rb') as fh:
            durl = 'data:image/png;base64,' + base64.b64encode(fh.read()).decode()
        bb = {
            'meta': {'format_version': '4.5', 'model_format': 'geckolib_model', 'box_uv': False},
            'name': 'akm_voxel',
            'resolution': {'width': tex_size, 'height': tex_size},
            'elements': elements,
            'outliner': [g['uuid'] for g in groups],
            'groups': groups,
            'textures': [{'path': '', 'name': 'akm_geo.png', 'folder': 'block', 'namespace': '',
                          'id': '0', 'particle': False, 'render_mode': 'default', 'visible': True,
                          'mode': 'bitmap', 'saved': True, 'uuid': _uuid('tex'), 'source': durl}],
            'animations': [],
            'animation_controllers': [],
        }
        with open(BB_OUT, 'w', encoding='utf-8') as fh:
            json.dump(bb, fh, ensure_ascii=False)
        print('工程 -> %s （%.1f MB）' % (BB_OUT, os.path.getsize(BB_OUT) / 1048576))
    return 0


def _uuid(s):
    import hashlib
    h = hashlib.md5(s.encode('utf-8')).hexdigest()
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:32])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
