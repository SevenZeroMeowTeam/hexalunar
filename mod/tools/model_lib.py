#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""程序化建模基础库（Blockbench free / mesh 格式）。

  Atlas  512x512 材质图集，16x16 个 32px 贴图块
  Mesh   顶点/面收集器 + box / prism / cyl / sweep 图元（自动 UV、自动修正绕向）
  写出   write_obj / write_mtl / write_bbmodel / bb_parts_payload

约定：16 u = 1 方块 = 1 m；UV 空间 0..16，1 单位 = 1 个贴图块。
"""
import base64
import json
import math
import os
import random
import uuid as uuidlib

from PIL import Image, ImageDraw

RES = 16.0
TILE = 32
COLS = ROWS = 16


# ============================================================ 贴图图集
def _cl(x, lo=0, hi=255):
    return int(max(lo, min(hi, x)))


def _shade(c, f):
    return (_cl(c[0] * f), _cl(c[1] * f), _cl(c[2] * f))


class Rnd:
    def __init__(self, seed):
        self.s = (seed & 0x7fffffff) or 1

    def f(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7fffffff
        return self.s / 0x7fffffff

    def rng(self, a, b):
        return a + (b - a) * self.f()


class Atlas:
    def __init__(self, cols=COLS, rows=ROWS, tile=TILE):
        self.cols, self.rows, self.tile = cols, rows, tile
        self.img = Image.new('RGBA', (cols * tile, rows * tile), (0, 0, 0, 255))
        self._slots = {}
        self._n = 0

    def add(self, name, painter):
        if name in self._slots:
            raise KeyError('tile exists: ' + name)
        col, row = self._n % self.cols, self._n // self.cols
        if row >= self.rows:
            raise RuntimeError('atlas full (%d)' % self._n)
        self._n += 1
        self._slots[name] = (col, row)
        t = Image.new('RGBA', (self.tile, self.tile), (0, 0, 0, 255))
        painter(t, ImageDraw.Draw(t))
        self.img.paste(t, (col * self.tile, row * self.tile))
        return name

    def uv(self, name):
        col, row = self._slots[name]
        return (float(col), float(row))

    def save(self, path):
        d = os.path.dirname(os.path.abspath(path))
        if d:
            os.makedirs(d, exist_ok=True)
        self.img.save(path)
        return path


def grad(base, top=1.18, bot=0.74, vig=0.20, noise=5, seed=1, streaks=0, streak_f=1.20, extra=None):
    """竖直渐变（上亮下暗）+ 四周压暗（假 AO/倒角）+ 细噪声 + 可选横向拉丝。"""
    def painter(img, d):
        w, h = img.size
        px = img.load()
        rn = Rnd(seed)
        for y in range(h):
            ty = (y + 0.5) / h
            f = top + (bot - top) * ty
            fy = 1.0 - vig * (abs(ty - 0.5) * 2) ** 2 if vig else 1.0
            for x in range(w):
                tx = (x + 0.5) / w
                fx = 1.0 - vig * (abs(tx - 0.5) * 2) ** 2 if vig else 1.0
                c = _shade(base, f * fy * fx)
                if noise:
                    n = int(rn.rng(-noise, noise))
                    c = (_cl(c[0] + n), _cl(c[1] + n), _cl(c[2] + n))
                px[x, y] = (c[0], c[1], c[2], 255)
        for _ in range(streaks):
            y = int(rn.rng(0, h - 1))
            f = streak_f if rn.f() < 0.5 else 1.0 / streak_f
            for x in range(w):
                px[x, y] = _shade(px[x, y], f)
        if extra:
            extra(img, d)
    return painter


def flat(base, vig=0.22, noise=4, seed=7, extra=None):
    """顶面/底面用：弱渐变 + 压暗 + 噪声。"""
    def painter(img, d):
        w, h = img.size
        px = img.load()
        rn = Rnd(seed)
        for y in range(h):
            for x in range(w):
                tx = abs((x + 0.5) / w - 0.5) * 2
                ty = abs((y + 0.5) / h - 0.5) * 2
                f = 1.0 - vig * max(tx, ty) ** 2
                c = _shade(base, f)
                if noise:
                    n = int(rn.rng(-noise, noise))
                    c = (_cl(c[0] + n), _cl(c[1] + n), _cl(c[2] + n))
                px[x, y] = (c[0], c[1], c[2], 255)
        if extra:
            extra(img, d)
    return painter


def ex_lines(step=6, vertical=False, col=(0, 0, 0), inset=2, width=1):
    def f(img, d):
        w, h = img.size
        rng = range(inset, (w if vertical else h) - inset, step)
        for i in rng:
            if vertical:
                d.line([(i, inset), (i, h - 1 - inset)], fill=col, width=width)
            else:
                d.line([(inset, i), (w - 1 - inset, i)], fill=col, width=width)
    return f


def ex_checker(step=8, col=(12, 13, 14)):
    def f(img, d):
        w, h = img.size
        for y in range(0, h, step):
            for x in range(0, w, step):
                if ((x // step) + (y // step)) % 2 == 0:
                    d.rectangle([x + 1, y + 1, x + step - 2, y + step - 2], outline=col)
    return f


def ex_holes(n=5, r=4, col=(8, 9, 10), ring=(76, 80, 86)):
    def f(img, d):
        w, h = img.size
        for i in range(n):
            cx = w * (i + 1) / (n + 1)
            cy = h * 0.5
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=ring)
    return f


def ex_ring(r=11, width=3, col=(14, 15, 17), hi=(96, 101, 108)):
    def f(img, d):
        w, h = img.size
        cx, cy = w / 2, h / 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=width)
        d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], outline=hi, width=1)
    return f


def ex_slots(n=3, col=(10, 11, 13), hi=(70, 74, 80)):
    def f(img, d):
        w, h = img.size
        for i in range(n):
            y = h * (i + 1) / (n + 1) - 2
            d.rectangle([3, y, w - 4, y + 4], fill=col)
            d.line([(3, y), (w - 4, y)], fill=hi)
    return f


def ex_camo(blobs=((24, 26, 27), (46, 49, 46), (36, 40, 38)), seed=5):
    def f(img, d):
        rn = Rnd(seed)
        w, h = img.size
        for col in blobs:
            for _ in range(4):
                cx, cy = rn.rng(0, w), rn.rng(0, h)
                r = rn.rng(4, 9)
                d.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], fill=col)
    return f


def ex_lens():
    def f(img, d):
        w, h = img.size
        px = img.load()
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = min(cx, cy)
        for y in range(h):
            for x in range(w):
                dist = math.hypot(x - cx, y - cy) / r
                if dist > 1.0:
                    px[x, y] = (14, 16, 18, 255)
                    continue
                c = _shade((58, 136, 158), 1.30 - 0.80 * dist ** 2)
                px[x, y] = (c[0], c[1], c[2], 255)
        d.ellipse([cx - r * 0.84, cy - r * 0.84, cx + r * 0.84, cy + r * 0.84],
                  outline=(168, 214, 226), width=1)
        d.line([(cx - r * 0.46, cy + r * 0.5), (cx + r * 0.18, cy - r * 0.48)],
               fill=(214, 240, 246), width=2)
    return f


def ex_twist(hl, step=5):
    """绳索/线缆的绞纹。"""
    def f(img, d):
        w, h = img.size
        for x in range(-h, w, step):
            d.line([(x, h), (x + h, 0)], fill=hl, width=1)
    return f


# ============================================================ 网格
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, f):
    return (a[0] * f, a[1] * f, a[2] * f)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _len(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    n = _len(a) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def _center(pts):
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


def _poly_normal(pts):
    """Newell 法：与顶点顺序右手对应的面法线。"""
    n = [0.0, 0.0, 0.0]
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        n[0] += (p[1] - q[1]) * (p[2] + q[2])
        n[1] += (p[2] - q[2]) * (p[0] + q[0])
        n[2] += (p[0] - q[0]) * (p[1] + q[1])
    return (n[0], n[1], n[2])


class Mesh:
    """一个部件（导出为 Blockbench 的一个 mesh 元素）。"""

    def __init__(self, name):
        self.name = name
        self.verts = []
        self.faces = []
        self._look = {}

    def vid(self, p):
        k = (round(p[0], 5), round(p[1], 5), round(p[2], 5))
        i = self._look.get(k)
        if i is None:
            i = len(self.verts)
            self.verts.append([p[0], p[1], p[2]])
            self._look[k] = i
        return i

    def face(self, pts, tile, inside=None):
        """加一个面；inside 给该实体内部一点，用于自动把绕向修正为朝外。"""
        pts = [tuple(p) for p in pts]
        n = _poly_normal(pts)
        if inside is not None and _dot(n, _sub(_center(pts), inside)) < 0:
            pts = pts[::-1]
            n = _poly_normal(pts)
        n = _unit(n)
        if abs(n[1]) > 0.9:
            v_axis = (0.0, 0.0, -1.0)
        else:
            v_axis = (0.0, 1.0, 0.0)
        u_axis = _unit(_cross(v_axis, n))
        v_axis = _unit(_cross(n, u_axis))
        us = [_dot(p, u_axis) for p in pts]
        vs = [_dot(p, v_axis) for p in pts]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        du, dv = (u1 - u0) or 1.0, (v1 - v0) or 1.0
        idx = [self.vid(p) for p in pts]
        uv = {i: [(us[k] - u0) / du, 1.0 - (vs[k] - v0) / dv] for k, i in enumerate(idx)}
        self.faces.append({'vertices': idx, 'tile': tile, 'uv': uv})
        return idx

    def box(self, x0, x1, y0, y1, z0, z1, mat, over=None, skip=()):
        over = over or {}
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        t = {'px': mat + '_s', 'nx': mat + '_s', 'pz': mat + '_s', 'nz': mat + '_s',
             'py': mat + '_t', 'ny': mat + '_b'}
        t.update(over)
        quads = {
            'px': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
            'nx': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            'pz': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            'nz': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
            'py': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
            'ny': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        }
        for k, pts in quads.items():
            if k in skip:
                continue
            self.face(pts, t[k], inside=c)
        return self

    def prism(self, bot, top, mat, over=None):
        """上下两个顶点数相同、从 +Y 俯视为逆时针的多边形之间的柱/台。"""
        over = over or {}
        n = len(bot)
        c = _center([_add(bot[i], top[i]) for i in range(n)])
        for i in range(n):
            j = (i + 1) % n
            self.face([bot[i], bot[j], top[j], top[i]], over.get('side', mat + '_s'), inside=c)
        self.face(list(bot), over.get('bot', mat + '_b'), inside=c)
        self.face(list(top), over.get('top', mat + '_t'), inside=c)
        return self

    def cyl(self, axis, c1, c2, a0, a1, r0, r1=None, seg=14, mat='alu',
            cap=True, cap_mat=None, side_mat=None, caps=('both', 'both')):
        """轴向圆柱/圆台；axis: 'x'|'y'|'z'，c1/c2 为另两轴上的圆心坐标。"""
        r1 = r0 if r1 is None else r1
        i0 = {'x': 0, 'y': 1, 'z': 2}[axis]
        o = [i for i in range(3) if i != i0]
        ring0, ring1 = [], []
        for k in range(seg):
            ang = 2 * math.pi * k / seg
            ca, sa = math.cos(ang), math.sin(ang)
            p0 = [0.0, 0.0, 0.0]
            p1 = [0.0, 0.0, 0.0]
            p0[i0], p1[i0] = a0, a1
            p0[o[0]] = c1 + ca * r0
            p0[o[1]] = c2 + sa * r0
            p1[o[0]] = c1 + ca * r1
            p1[o[1]] = c2 + sa * r1
            ring0.append(tuple(p0))
            ring1.append(tuple(p1))
        cmid = [0.0, 0.0, 0.0]
        cmid[i0] = (a0 + a1) / 2
        cmid[o[0]] = c1
        cmid[o[1]] = c2
        cmid = tuple(cmid)
        sm = side_mat or (mat + '_s')
        for k in range(seg):
            m = (k + 1) % seg
            self.face([ring0[k], ring0[m], ring1[m], ring1[k]], sm, inside=cmid)
        if cap:
            cma = cap_mat or (mat + '_t')
            lo_ring, hi_ring = (ring0, ring1) if a0 < a1 else (ring1, ring0)
            if caps[0] != 'none':
                self.face(lo_ring, cma, inside=cmid)
            if caps[1] != 'none':
                self.face(hi_ring, cma, inside=cmid)
        return self

    def sweep(self, pts, hw, hh, mat, side_mat=None, cap_mat=None, top_mat=None, bot_mat=None):
        """沿折线扫掠矩形截面（弓臂）。hw 沿水平横轴、hh 沿竖直。"""
        rings = []
        for i, p in enumerate(pts):
            if i == 0:
                d = _sub(pts[1], pts[0])
            elif i == len(pts) - 1:
                d = _sub(pts[-1], pts[-2])
            else:
                d = _sub(pts[i + 1], pts[i - 1])
            d = _unit(d)
            a = _unit(_cross((0.0, 1.0, 0.0), d))
            b = _unit(_cross(d, a))
            w = hw[min(i, len(hw) - 1)] if isinstance(hw, (list, tuple)) else hw
            h = hh[min(i, len(hh) - 1)] if isinstance(hh, (list, tuple)) else hh
            rings.append([_add(p, _add(_mul(a, w * s1), _mul(b, h * s2)))
                          for s1, s2 in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
        sm = side_mat or (mat + '_s')
        # 扁片截面：朝上的面用 _t（亮），朝下的面用 _b，侧边用 _s
        seg_tiles = (top_mat or (mat + '_t'), sm, bot_mat or (mat + '_b'), sm)
        for i in range(len(rings) - 1):
            inside = _center([_center(rings[i]), _center(rings[i + 1])])
            for k in range(4):
                m = (k + 1) % 4
                self.face([rings[i][k], rings[i][m], rings[i + 1][m], rings[i + 1][k]],
                          seg_tiles[k], inside=inside)
        self.face(rings[0], cap_mat or (mat + '_b'), inside=_center(rings[1]))
        self.face(rings[-1], cap_mat or (mat + '_b'), inside=_center(rings[-2]))
        return self

    def transform(self, fn):
        self.verts = [list(fn(*v)) for v in self.verts]
        self._look = {(round(v[0], 5), round(v[1], 5), round(v[2], 5)): i
                      for i, v in enumerate(self.verts)}
        return self

    def rot_y(self, deg, pivot=(0.0, 0.0, 0.0)):
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        return self.transform(lambda x, y, z: (
            ca * (x - pivot[0]) + sa * (z - pivot[2]) + pivot[0], y,
            -sa * (x - pivot[0]) + ca * (z - pivot[2]) + pivot[2]))

    def rot_x(self, deg, pivot=(0.0, 0.0, 0.0)):
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        return self.transform(lambda x, y, z: (
            x, ca * (y - pivot[1]) - sa * (z - pivot[2]) + pivot[1],
            sa * (y - pivot[1]) + ca * (z - pivot[2]) + pivot[2]))

    def translate(self, off):
        return self.transform(lambda x, y, z: (x + off[0], y + off[1], z + off[2]))

    def bbox(self):
        return ([min(v[i] for v in self.verts) for i in range(3)],
                [max(v[i] for v in self.verts) for i in range(3)])


# ============================================================ 写出
def _abs_uv(base, n, tile=TILE):
    """把面内的归一化坐标 n∈[0,1] 映射到贴图块内部的像素中心（base 为该块的 u 或 v 起点）。"""
    return base + (n * (tile - 1) + 0.5) / float(tile)


def _tri_faces(mesh):
    out = []
    for f in mesh.faces:
        vs = f['vertices']
        for k in range(1, len(vs) - 1):
            out.append(([vs[0], vs[k], vs[k + 1]], f))
    return out


def write_obj(path, meshes, mtl_name, atlas, name='model', center=None, divide=16.0):
    allv = [v for m in meshes for v in m.verts]
    lo = [min(v[i] for v in allv) for i in range(3)]
    hi = [max(v[i] for v in allv) for i in range(3)]
    c = list(center) if center else [(lo[i] + hi[i]) / 2 for i in range(3)]
    vlines, flines = [], ['usemtl mat']
    vt_map, vt_list = {}, []
    vbase = 0
    for m in meshes:
        for v in m.verts:
            vlines.append('v %.6f %.6f %.6f' % ((v[0] - c[0]) / divide + 0.5,
                                                (v[1] - c[1]) / divide + 0.5,
                                                (v[2] - c[2]) / divide + 0.5))
    for m in meshes:
        for tri, f in _tri_faces(m):
            org = atlas.uv(f['tile'])
            refs = []
            for idx in tri:
                n = f['uv'].get(idx, [0.0, 0.0])
                uv = (_abs_uv(org[0], n[0]), _abs_uv(org[1], n[1]))
                key = (round(uv[0], 5), round(uv[1], 5))
                if key not in vt_map:
                    vt_map[key] = len(vt_list) + 1
                    vt_list.append((uv[0] / RES, uv[1] / RES))
                refs.append('%d/%d' % (vbase + idx + 1, vt_map[key]))
            flines.append('f ' + ' '.join(refs))
        vbase += len(m.verts)
    out = ['# %s.obj exported from Blockbench free model' % name, 'mtllib ' + mtl_name, 'o ' + name]
    out += vlines
    out += ['vt %.6f %.6f' % t for t in vt_list]
    out += flines
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out) + '\n')
    return {'verts': len(allv), 'tris': len(flines) - 1, 'vt': len(vt_list),
            'bbox': (lo, hi), 'center': c}


def write_mtl(path, tex_ref='hexalunar_calamity:models/crossbow'):
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('# crossbow material\nnewmtl mat\nKd 1.0 1.0 1.0\nKa 1.0 1.0 1.0\n'
                 'Ks 0.0 0.0 0.0\nNs 0\nmap_Kd %s\n' % tex_ref)


def write_bbmodel(path, meshes, atlas, png_path, name, template=None, res=RES):
    if template and os.path.exists(template):
        with open(template, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    else:
        data = {'meta': {'format_version': '5.0', 'model_format': 'free', 'box_uv': False},
                'visible_box': [1, 1, 0], 'timeline_setups': [],
                'variable_placeholder_buttons': [], 'variable_placeholders': '',
                'unhandled_root_fields': {}, 'groups': []}
    data['name'] = name
    data['model_identifier'] = name
    data['resolution'] = {'width': res, 'height': res}
    data['elements'] = []
    data['outliner'] = []
    for m in meshes:
        vkeys, verts = [], {}
        for v in m.verts:
            k = str(uuidlib.uuid4())
            vkeys.append(k)
            verts[k] = [round(v[0], 5), round(v[1], 5), round(v[2], 5)]
        faces = {}
        for f in m.faces:
            fk = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))
            org = atlas.uv(f['tile'])
            vs = [vkeys[i] for i in f['vertices']]
            uvmap = {}
            for i, k in zip(f['vertices'], vs):
                n = f['uv'][i]
                uvmap[k] = [round(_abs_uv(org[0], n[0]), 6), round(_abs_uv(org[1], n[1]), 6)]
            faces[fk] = {'uv': uvmap, 'texture': 0, 'vertices': vs}
        el = {'name': m.name, 'color': 0, 'origin': [0, 0, 0], 'rotation': [0, 0, 0],
              'shading': 'flat', 'export': True, 'visibility': True, 'locked': False,
              'render_order': 'default', 'scope': 0, 'allow_mirror_modeling': True,
              'vertices': verts, 'faces': faces, 'type': 'mesh', 'uuid': str(uuidlib.uuid4())}
        data['elements'].append(el)
        data['outliner'].append(el['uuid'])
    with open(png_path, 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode('ascii')
    data['textures'] = [{'name': name, 'id': '0', 'uuid': str(uuidlib.uuid4()),
                         'uv_width': res, 'uv_height': res, 'particle': False,
                         'source': 'data:image/png;base64,' + b64}]
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)
    return path


def bb_parts_payload(meshes, atlas):
    """给 Blockbench 用的紧凑几何数据（已含绝对 UV）。"""
    parts = []
    for m in meshes:
        verts = [[round(v[0], 5), round(v[1], 5), round(v[2], 5)] for v in m.verts]
        faces = []
        for f in m.faces:
            org = atlas.uv(f['tile'])
            uv = {str(i): [round(_abs_uv(org[0], f['uv'][i][0]), 6),
                           round(_abs_uv(org[1], f['uv'][i][1]), 6)]
                  for i in f['vertices']}
            faces.append({'v': f['vertices'], 'uv': uv})
        parts.append({'name': m.name, 'verts': verts, 'faces': faces})
    return parts
