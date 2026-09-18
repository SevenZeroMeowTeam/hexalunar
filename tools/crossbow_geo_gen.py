#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""十字弩（复合弩）Bedrock 几何 / 贴图 / 动画生成器。

为什么用这个而不是直接手搓 Blockbench：
  Bedrock/GeckoLib 的几何是「长方体 + 骨骼层级」，用代码生成可以精确控制尺寸、UV 与骨骼 pivot，
  并且能一键重生成。产物同时给出 .bbmodel（给你在 Blockbench 里继续调）与 .geo.json（游戏实际加载的）。

坐标约定（Bedrock，1 单位 = 1 像素 = 1/16 方块）：
  +X = 右, +Y = 上, -Z = 枪口/箭头方向（与 MC 物品「朝前 = -Z」一致）
  模型总长 ≈ 16 px ≈ 1 方块，与 AKM/复合弓同量级，因此可沿用现有的 display 手持参数。

用法:
    python tools/crossbow_geo_gen.py            # 生成全部产物
    python tools/crossbow_geo_gen.py --obj-only # 只出调试用 OBJ（喂 tools/fp_preview.py）
"""
import argparse
import json
import math
import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "mod/src/main/resources/assets/hexalunar_calamity")
MODELDIR = os.path.join(ROOT, "mod/模型")
NS = "hexalunar_calamity"
TEX_NAME = "crossbow_geo"
GEO_ID = "geometry.crossbow"
TEX_W = TEX_H = 64

# ---------------------------------------------------------------- 材质色板
# 每个材质给一个 8x8 的色块区域（UV: x, y 为左上角），面 UV 就映射到这块里
MATERIALS = {
    #  名称          基色(R,G,B 0-1)        噪点幅度
    "polymer": ((0.105, 0.105, 0.115), 0.030),   # 黑色聚合物机匣
    "polymer2": ((0.135, 0.138, 0.145), 0.030),  # 稍浅的护手/枪托
    "metal": ((0.235, 0.245, 0.265), 0.050),     # 深色金属（导轨、凸轮轴）
    "scope": ((0.075, 0.075, 0.085), 0.025),     # 瞄准镜镜筒
    "lens": ((0.115, 0.330, 0.520), 0.060),      # 镜片（偏蓝）
    "string": ((0.760, 0.760, 0.735), 0.045),    # 弦/缆
    "limb": ((0.085, 0.085, 0.095), 0.035),      # 弓片
    "camo": ((0.300, 0.290, 0.255), 0.070),      # 迷彩贴片（照参考图的浅色块）
    "bolt": ((0.150, 0.150, 0.165), 0.035),      # 箭杆
    "fletch": ((0.720, 0.230, 0.130), 0.070),    # 箭羽（醒目橙红）
    "tip": ((0.420, 0.430, 0.460), 0.060),       # 箭头
}
MAT_ORDER = list(MATERIALS.keys())
MAT_CELL = 8            # 每个材质占 8x8 像素
MAT_COLS = 8            # 每行 8 个材质


def rel(path):
    """相对仓库根的展示路径（跨盘符时直接给绝对路径）"""
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path


def mat_uv(name):
    """材质 -> 贴图左上角 (u, v)"""
    i = MAT_ORDER.index(name)
    return (i % MAT_COLS) * MAT_CELL, (i // MAT_COLS) * MAT_CELL


# ---------------------------------------------------------------- 骨骼 / 方块定义
# box(name, 材质, origin[x,y,z], size[dx,dy,dz], rotation(度,可选), pivot(可选))
BONES = []


def bone(name, pivot, parent=None, cubes=()):
    BONES.append({"name": name, "pivot": list(pivot), "parent": parent, "cubes": list(cubes)})


def box(mat, origin, size, rot=None, pivot=None):
    d = {"mat": mat, "origin": list(origin), "size": list(size)}
    if rot:
        d["rot"] = list(rot)
        d["pivot"] = list(pivot if pivot else [origin[0] + size[0] / 2.0,
                                              origin[1] + size[1] / 2.0,
                                              origin[2] + size[2] / 2.0])
    return d


def build():
    BONES.clear()
    # ---- 机匣/弩身（含导轨、护手）----
    bone("riser", [0, 0, 0],
         cubes=[
             box("polymer", [-1.0, -1.0, -6.5], [2.0, 2.0, 10.0]),
             box("polymer2", [-1.4, -0.6, -7.4], [2.8, 1.9, 1.4]),      # 前端护手
             box("metal", [-0.9, 0.95, -8.0], [1.8, 0.40, 12.6]),       # 导轨（箭道）
             box("camo", [-1.05, -1.05, -3.2], [2.1, 1.1, 3.4]),        # 侧面迷彩贴片
             box("metal", [-1.05, -3.0, 0.2], [2.1, 2.0, 1.6]),         # 扳机护圈座
         ])
    # ---- 扳机 ----
    bone("trigger", [0, -1.5, 1.0], parent="riser",
         cubes=[box("metal", [-0.25, -2.9, 0.75], [0.5, 1.5, 0.5], rot=[12, 0, 0],
                    pivot=[0, -1.5, 1.0])])
    # ---- 握把 ----
    bone("grip", [0, -1.0, 1.8], parent="riser",
         cubes=[box("polymer2", [-1.0, -5.2, 1.05], [2.0, 4.4, 2.2], rot=[16, 0, 0],
                    pivot=[0, -1.0, 1.8])])
    # ---- 枪托 ----
    bone("stock", [0, -1.2, 3.2], parent="riser",
         cubes=[
             box("polymer2", [-1.2, -3.9, 3.2], [2.4, 2.8, 4.6], rot=[8, 0, 0],
                 pivot=[0, -1.2, 3.2]),
             box("polymer", [-1.4, -4.6, 6.4], [2.8, 3.6, 1.6], rot=[8, 0, 0],
                 pivot=[0, -1.2, 3.2]),
         ])
    # ---- 瞄准镜 ----
    bone("scope", [0, 1.3, -1.5], parent="riser",
         cubes=[
             box("scope", [-1.1, 1.45, -4.6], [2.2, 2.2, 5.6]),
             box("metal", [-1.35, 1.3, -5.2], [2.7, 2.5, 0.7]),          # 前镜圈
             box("metal", [-1.35, 1.3, 0.3], [2.7, 2.5, 0.7]),           # 后镜圈
             box("lens", [-1.05, 1.55, -5.0], [2.1, 1.9, 0.25], rot=None),  # 前镜片
             box("lens", [-1.05, 1.55, 0.9], [2.1, 1.9, 0.25]),          # 后镜片
             box("metal", [-0.55, 0.9, -3.4], [1.1, 1.5, 1.0]),          # 镜桥（前）
             box("metal", [-0.55, 0.9, -0.9], [1.1, 1.5, 1.0]),          # 镜桥（后）
         ])
    # ---- 弓片（左右各两节，靠 cube rotation 做出后掠）----
    for side, sx in (("left", -1.0), ("right", 1.0)):
        limb_pivot = [sx * 1.2, 0.9, -5.2]
        bone("limb_" + side, limb_pivot, parent="riser",
             cubes=[
                 box("limb", [min(sx * 1.2, sx * 6.4), 0.35, -5.9],
                     [5.2, 1.1, 1.3], rot=[0, -16 if side == "left" else 16, 0],
                     pivot=limb_pivot),
                 box("limb", [min(sx * 6.2, sx * 8.4), 0.0, -5.0],
                     [2.2, 1.0, 1.2], rot=[0, -30 if side == "left" else 30, 0],
                     pivot=limb_pivot),
                 box("camo", [min(sx * 3.0, sx * 5.0), 0.5, -5.6],
                     [2.0, 0.9, 1.0], rot=[0, -16 if side == "left" else 16, 0],
                     pivot=limb_pivot),
             ])
        # ---- 凸轮（复合弩的偏心轮）----
        cam_pivot = [sx * 7.2, 0.5, -3.6]
        bone("cam_" + side, cam_pivot, parent="limb_" + side,
             cubes=[
                 box("metal", [min(sx * 7.2, sx * 9.0), -0.9, -4.8], [1.8, 2.8, 2.4]),
                 box("metal", [min(sx * 7.0, sx * 7.8), -0.4, -4.2], [0.8, 1.8, 1.4]),
             ])
    # ---- 弦（左右两半，各自以凸轮为轴，拉弦时旋转成 V 形）----
    for side, sx in (("left", -1.0), ("right", 1.0)):
        cam_pivot = [sx * 7.2, 0.5, -3.6]
        bone("string_" + side, cam_pivot, parent="cam_" + side,
             cubes=[box("string", [min(sx * 7.4, sx * 0.0), 0.55, -3.75],
                        [7.4, 0.30, 0.30])])
    # ---- 箭 ----
    bone("bolt", [0, 1.2, -3.0], parent="riser",
         cubes=[
             box("bolt", [-0.35, 1.35, -7.6], [0.7, 0.45, 8.4]),         # 箭杆
             box("tip", [-0.5, 1.25, -8.7], [1.0, 0.65, 1.2]),           # 箭头
             box("fletch", [-0.95, 1.35, -0.5], [0.6, 0.45, 1.7]),       # 左羽
             box("fletch", [0.35, 1.35, -0.5], [0.6, 0.45, 1.7]),        # 右羽
             box("fletch", [-0.3, 1.35, -0.5], [0.6, 0.45, 1.7]),        # 上羽
         ])


# ---------------------------------------------------------------- 输出：Bedrock 几何
def emit_geo(path):
    build()
    bones = []
    for b in BONES:
        cubes = []
        for c in b["cubes"]:
            u, v = mat_uv(c["mat"])
            face = {"uv": [u, v], "uv_size": [MAT_CELL, MAT_CELL]}
            cube = {
                "origin": [round(x, 3) for x in c["origin"]],
                "size": [round(x, 3) for x in c["size"]],
                "pivot": [round(x, 3) for x in c.get("pivot", [0, 0, 0])],
                "uv": {k: dict(face) for k in
                       ("north", "east", "south", "west", "up", "down")},
            }
            if c.get("rot"):
                cube["rotation"] = [round(x, 3) for x in c["rot"]]
            cubes.append(cube)
        entry = {"name": b["name"], "pivot": [round(x, 3) for x in b["pivot"]]}
        if b["parent"]:
            entry["parent"] = b["parent"]
        if cubes:
            entry["cubes"] = cubes
        bones.append(entry)
    geo = {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": GEO_ID,
                "texture_width": TEX_W,
                "texture_height": TEX_H,
                "visible_bounds_width": 4,
                "visible_bounds_height": 3,
                "visible_bounds_offset": [0, 0.5, 0],
            },
            "bones": bones,
        }],
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(geo, f, indent=1, ensure_ascii=False)
    n = sum(len(b.get("cubes", [])) for b in bones)
    print(f"  geo  -> {rel(path)}  ({len(bones)} 骨骼 / {n} 方块)")
    return geo


# ---------------------------------------------------------------- 输出：贴图
def write_png(path, w, h, pix):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pix[y * w * 4:(y + 1) * w * 4]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def emit_texture(path):
    pix = bytearray(TEX_W * TEX_H * 4)
    for y in range(TEX_H):
        for x in range(TEX_W):
            i = (y * TEX_W + x) * 4
            pix[i:i + 4] = bytes((8, 8, 10, 255))
    rng = 12345

    def rnd():
        nonlocal rng
        rng = (1103515245 * rng + 12345) & 0x7FFFFFFF
        return rng / 0x7FFFFFFF

    for name in MAT_ORDER:
        (base, amp) = MATERIALS[name]
        u0, v0 = mat_uv(name)
        for dy in range(MAT_CELL):
            # 上亮下暗的轻微渐变，避免死板
            shade = 1.0 + 0.16 * (1.0 - 2.0 * dy / (MAT_CELL - 1))
            for dx in range(MAT_CELL):
                n = (rnd() - 0.5) * 2.0 * amp
                r = min(1.0, max(0.0, base[0] * shade + n))
                g = min(1.0, max(0.0, base[1] * shade + n))
                b = min(1.0, max(0.0, base[2] * shade + n))
                # 边缘 1px 描一层暗边，面与面之间更有分界感
                if dx == 0 or dy == 0 or dx == MAT_CELL - 1 or dy == MAT_CELL - 1:
                    r, g, b = r * 0.72, g * 0.72, b * 0.72
                x, y = u0 + dx, v0 + dy
                i = (y * TEX_W + x) * 4
                pix[i:i + 4] = bytes((int(r * 255), int(g * 255), int(b * 255), 255))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_png(path, TEX_W, TEX_H, pix)
    print(f"  tex  -> {rel(path)}  ({TEX_W}x{TEX_H})")


# ---------------------------------------------------------------- 输出：调试用 OBJ
def emit_debug_obj(path):
    """把长方体拆成三角面写成 OBJ（坐标 ÷16 变成方块单位），用来喂 tools/fp_preview.py"""
    build()
    verts, uvs, faces = [], [], []

    def cube_corners(origin, size, rot=None, pivot=None):
        x0, y0, z0 = origin
        x1, y1, z1 = x0 + size[0], y0 + size[1], z0 + size[2]
        pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
               (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        if rot and pivot:
            rx, ry, rz = [math.radians(a) for a in rot]

            def apply(p):
                px, py, pz = p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2]
                # Bedrock 顺序：Z -> Y -> X
                cz, sz = math.cos(rz), math.sin(rz)
                px, py = px * cz - py * sz, px * sz + py * cz
                cy, sy = math.cos(ry), math.sin(ry)
                px, pz = px * cy + pz * sy, -px * sy + pz * cy
                cx, sx = math.cos(rx), math.sin(rx)
                py, pz = py * cx - pz * sx, py * sx + pz * cx
                return (px + pivot[0], py + pivot[1], pz + pivot[2])

            pts = [apply(p) for p in pts]
        return [(p[0] / 16.0, p[1] / 16.0, p[2] / 16.0) for p in pts]

    face_idx = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7),
                (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)]
    for b in BONES:
        for c in b["cubes"]:
            pts = cube_corners(c["origin"], c["size"], c.get("rot"), c.get("pivot"))
            base = len(verts)
            verts += pts
            u, v = mat_uv(c["mat"])
            uv = ((u + 2) / TEX_W, 1.0 - (v + 2) / TEX_H)
            for f in face_idx:
                uvs.append(uv)
                faces.append([base + f[0] + 1, base + f[1] + 1,
                              base + f[2] + 1, base + f[3] + 1])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# crossbow debug obj (block units)\nmtllib akm.mtl\no crossbow\n")
        for p in verts:
            f.write("v %.6f %.6f %.6f\n" % p)
        for uv in uvs:
            f.write("vt %.6f %.6f\n" % uv)
        f.write("usemtl mat\n")
        for i, q in enumerate(faces):
            a, bb, cc, d = q
            f.write("f %d/%d %d/%d %d/%d\n" % (a, i + 1, bb, i + 1, cc, i + 1))
            f.write("f %d/%d %d/%d %d/%d\n" % (a, i + 1, cc, i + 1, d, i + 1))
    print(f"  obj  -> {rel(path)}  ({len(verts)} 顶点 / {len(faces)} 四边形)")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--obj-only", action="store_true")
    args = ap.parse_args()

    if args.obj_only:
        emit_debug_obj(os.path.join(os.environ.get("TEMP", "."), "hlc_crossbow.obj"))
        return 0
    print("生成十字弩资源：")
    emit_geo(os.path.join(ASSETS, "geo/crossbow.geo.json"))
    emit_texture(os.path.join(ASSETS, "textures/item", TEX_NAME + ".png"))
    emit_debug_obj(os.path.join(os.environ.get("TEMP", "."), "hlc_crossbow.obj"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
