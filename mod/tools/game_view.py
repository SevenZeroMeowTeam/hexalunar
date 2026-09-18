#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按 MC 的真实变换链渲染「游戏内视角」预览图。

变换链（与 MC 一致）:
    world = Trans(手部偏移) · Rz? … 这里用 MC 的写法：T_display · Rx·Ry·Rz · S_display · x
其中 x 是模型像素坐标（1 格 = 16）。

相机预设:
  fp        第一人称：相机在原点朝 -Z 看，武器按 MC 的 firstperson_righthand 手部偏移摆放
  hand      第三人称手持：35° 斜上方看武器（含示意手臂），用 thirdperson_righthand
  hand_side 侧视手持
  gui       GUI 图标视角（正视，微俯）

用法:
  python tools/game_view.py                       # 全部模型 × (fp, hand)
  python tools/game_view.py akm --slots hand      # 指定模型/视角
"""
import base64
import io
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import north_align as na  # noqa: E402

ITEM = na.ITEM
OUT = 'build/gameviews'

MODELS = {
    'akm': ('模型/akm.bbmodel', 'akm.json'),
    'crossbow': ('模型/十字弩_v2.bbmodel', 'crossbow.json'),
    'compound_bow': ('模型/复合弓.bbmodel', 'compound_bow.json'),
    'bolt': ('模型/弩箭.bbmodel', None),
    'mtx': ('模型/mtx.bbmodel', 'mtx.json'),
    'mud': ('模型/mud.bbmodel', 'mud.json'),
}

# MC ItemInHandRenderer.applyItemArmTransform 的平移（格）→ 像素
ARM_FP = np.array([0.56, -0.52, -0.71]) * 16.0

PRESETS = {
    'fp': dict(slot='firstperson_righthand', arm='fp', frame=[90.0, 0.0, 0.0],
               cam=(12.0, -2.0, 14.0), tgt=(10.0, -8.0, -30.0), fov=50.0),
    'hand': dict(slot='thirdperson_righthand', arm='player', frame=[0.0, 0.0, 0.0],
                 cam=(30.0, 24.0, -30.0), tgt=(2.0, -2.0, -2.0), fov=45.0),
    'hand_side': dict(slot='thirdperson_righthand', arm='player', frame=[0.0, 0.0, 0.0],
                      cam=(42.0, 10.0, 4.0), tgt=(0.0, -2.0, -6.0), fov=45.0),
    'gui': dict(slot='gui', arm=None, frame=[0.0, 0.0, 0.0],
                cam=(0.0, 40.0, -95.0), tgt=(0.0, 6.0, 0.0), fov=30.0),
}


# ---------------------------------------------------------------- 读模型
def load_mesh(bb_path):
    """返回 (顶点像素坐标, 面, 贴图)。"""
    data = na.bn.load(bb_path)
    bb_pts = np.asarray([na.bn.elem_local_to_world(el, tuple(v))
                         for el, v in na.bn.world_verts(data)], dtype=float)
    # 面：按元素分别取
    faces = []
    order = []
    for el in data.get('elements', []):
        keys = list(el.get('vertices', {}).keys())
        for fid, f in (el.get('faces') or {}).items():
            vs = f.get('vertices') or []
            idx = [keys.index(k) for k in vs if k in keys]
            if len(idx) < 3:
                continue
            uv = f.get('uv') or {}
            uvs = [uv.get(k) for k in vs if k in uv]
            cols = f.get('color') if f.get('color') else None
            faces.append((idx, uvs, cols))
    tex = load_tex(data)
    return bb_pts, faces, tex, len(bb_pts)


def load_tex(data):
    for t in data.get('textures', []):
        src = t.get('source') or ''
        if src.startswith('data:image'):
            raw = base64.b64decode(src.split(',', 1)[1])
            return Image.open(io.BytesIO(raw)).convert('RGBA')
    return None


def shift_to_mc_space(bb_pts, bb_path):
    """把 bbmodel 顶点搬到 MC 模型空间（原点是 display 旋转中心 = 对应 obj 原点）。"""
    data = na.bn.load(bb_path)
    objp = None
    for name, (bb, js) in MODELS.items():
        if bb == bb_path and js:
            objp = os.path.join(ITEM, js.replace('.json', '.obj'))
    if not objp or not os.path.exists(objp):
        return bb_pts
    lines, idx, obj_pts = na.read_obj(objp)
    S, _ = na.find_S(bb_pts, obj_pts)
    tau = na.tau_of(S, bb_pts, obj_pts)
    cc = 16.0 * (S.T @ (np.array([0.5, 0.5, 0.5]) - tau))
    pivot = cc - 8.0
    return bb_pts - pivot


# ---------------------------------------------------------------- display
def display_of(json_name, slot):
    if not json_name:
        return [0, 0, 0], [0, 0, 0], [1, 1, 1]
    p = os.path.join(ITEM, json_name)
    if not os.path.exists(p):
        return [0, 0, 0], [0, 0, 0], [1, 1, 1]
    d = (json.load(open(p, encoding='utf-8')).get('display') or {}).get(slot) or {}
    return (d.get('rotation') or [0, 0, 0], d.get('translation') or [0, 0, 0],
            d.get('scale') or [1, 1, 1])


def apply_display(pts, rot, trans, scale, arm=None, frame=None):
    """world = Trans(手部平移) · FrameRot · (T_disp · R_disp · S_disp · x)。"""
    R = np.array(na.rotmat_xyz(rot))
    S = np.diag(scale)
    out = (pts @ S.T @ R.T) + np.array(trans, dtype=float)
    if frame is not None:
        out = out @ np.array(na.rotmat_xyz(frame)).T
    if arm is not None:
        out = out + np.array(arm, dtype=float)
    return out


# ---------------------------------------------------------------- 渲染
def render(pts, faces, tex, cam, tgt, fov, out_path, size=760, extra=None, label=''):
    cam = np.asarray(cam, dtype=float)
    tgt = np.asarray(tgt, dtype=float)
    fwd = tgt - cam
    fwd /= max(np.linalg.norm(fwd), 1e-9)
    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up0)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    def to_cam(p):
        d = p - cam
        return np.array([d @ right, d @ up, d @ fwd])

    fc = 0.5 * size / math.tan(math.radians(fov) / 2)

    def proj(p):
        c = to_cam(p)
        z = max(c[2], 1e-3)
        return (size / 2 + c[0] * fc / z, size / 2 - c[1] * fc / z, z)

    all_pts = list(pts)
    polys = []
    for idx, uvs, cols in faces:
        p3 = [pts[i] for i in idx]
        depth = float(np.mean([to_cam(p)[2] for p in p3]))
        col = shade(tex, uvs, cols)
        polys.append((depth, [proj(p) for p in p3], col))

    if extra:
        for el in extra:
            x0, x1, y0, y1, z0, z1, col = el
            box = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
                   (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
            quads = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (3, 2, 6, 7),
                     (0, 3, 7, 4), (1, 2, 6, 5)]
            for q in quads:
                p3 = [box[i] for i in q]
                depth = float(np.mean([to_cam(p)[2] for p in p3]))
                polys.append((depth, [proj(p) for p in p3], col))

    img = Image.new('RGB', (size, size), (238, 240, 244))
    dr = ImageDraw.Draw(img)
    polys.sort(key=lambda t: -t[0])
    for depth, poly, col in polys:
        if all(p[2] <= 0.05 for p in poly):
            continue
        dr.polygon([(p[0], p[1]) for p in poly], fill=col, outline=None)
    if label:
        dr.rectangle([0, 0, size, 22], fill=(255, 255, 255))
        dr.text((6, 6), label, fill=(0, 0, 0))
    img.save(out_path)
    return out_path


def shade(tex, uvs, cols):
    if cols:
        c = cols
        if isinstance(c, str):
            c = c.lstrip('#')
            c = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
        return tuple(c[:3])
    if tex is None or not uvs:
        return (170, 170, 178)
    w, h = tex.size
    us = [u[0] for u in uvs if u]
    vs = [u[1] for u in uvs if u]
    if not us:
        return (170, 170, 178)
    px = int(round(np.mean(us) / 16.0 * w)) % w
    py = int(round(np.mean(vs) / 16.0 * h)) % h
    r, g, b, a = tex.getpixel((px, py))
    if a < 40:
        return (210, 212, 216)
    return (int(r * 0.75), int(g * 0.75), int(b * 0.75))


def player_boxes():
    """示意：持武器的手 + 小臂（MC 像素，比例参照玩家 4px 粗的手臂）。"""
    hand = (-2.5, 2.5, -4.5, 1.5, -4, 6, (128, 136, 152))
    forearm = (-2.0, 2.0, -3.5, 1.0, 6, 22, (86, 92, 106))
    return [hand, forearm]


def main(argv):
    names = [a for a in argv[1:] if not a.startswith('--') and a in MODELS]
    presets = list(PRESETS)
    if '--slots' in argv:
        presets = argv[argv.index('--slots') + 1].split(',')
    if not names:
        names = list(MODELS)
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        bb, js = MODELS[name]
        pts0, faces, tex, _ = load_mesh(bb)
        pts = shift_to_mc_space(pts0, bb)
        for pre in presets:
            P = PRESETS[pre]
            rot, trans, scale = display_of(js, P['slot'])
            arm = ARM_FP if P.get('arm') == 'fp' else None
            moved = apply_display(pts, rot, trans, scale, arm=arm, frame=P.get('frame'))
            extra = None
            if P.get('arm') == 'player':
                extra = player_boxes()
            lbl = '%s  %s  slot=%s  rot=%s' % (name, pre, P['slot'], rot)
            out = os.path.join(OUT, '%s_%s.png' % (name, pre))
            render(moved, faces, tex, P['cam'], P['tgt'], P['fov'], out, extra=extra, label=lbl)
            print('wrote %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
