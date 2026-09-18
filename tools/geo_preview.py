#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线预览 Bedrock/GeckoLib 几何（.geo.json）：不需要 Blender、不需要开游戏。

做的事：
  1. 读 .geo.json（含骨骼层级 / 方块 / Bedrock 的 Z→Y→X 旋转顺序）
  2. 每个面按其 UV 采样贴图取色（顺带验证 UV 映射与贴图是否正确）
  3. 简单兰伯特光照 + 画家算法排序，正交/透视投影输出 PNG

因为直接读游戏实际加载的那个文件，所以「预览好看」基本等价于「进游戏好看」。

用法:
    python tools/geo_preview.py --geo <x.geo.json> --tex <x.png> --out <dir>
    python tools/geo_preview.py --geo ... --views side,top,persp --res 1000x700
"""
import argparse
import json
import math
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------- PNG 读写
def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG: " + path)
    pos = 8
    w = h = bitdepth = colortype = None
    idat = b""
    while pos < len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if tag == b"IHDR":
            w, h, bitdepth, colortype = struct.unpack(">IIBB", body[:10])
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break
    if bitdepth != 8 or colortype not in (2, 6):
        raise ValueError(f"只支持 8bit RGB/RGBA PNG（当前 depth={bitdepth} type={colortype}）")
    ch = 3 if colortype == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * ch
    out = bytearray(w * h * ch)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, bytes(out)


def write_png(path, w, h, pix):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pix[y * w * 4:(y + 1) * w * 4]

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- 几何解析
def bedrock_rotate(p, rot, pivot):
    """Bedrock 的旋转顺序：Z -> Y -> X（与 Blockbench/游戏一致）"""
    rx, ry, rz = [math.radians(a) for a in rot]
    x, y, z = p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2]
    cz, sz = math.cos(rz), math.sin(rz)
    x, y = x * cz - y * sz, x * sz + y * cz
    cy, sy = math.cos(ry), math.sin(ry)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cx, sx = math.cos(rx), math.sin(rx)
    y, z = y * cx - z * sx, y * sx + z * cx
    return (x + pivot[0], y + pivot[1], z + pivot[2])


FACE_KEYS = ("north", "east", "south", "west", "up", "down")


def collect_faces(geo_path):
    """返回 [(顶点4个, 材质色 uv 中心, uv 矩形, 骨骼名)]，坐标单位为像素"""
    with open(geo_path, encoding="utf-8") as f:
        doc = json.load(f)
    geom = doc["minecraft:geometry"][0]
    bones = {b["name"]: b for b in geom["bones"]}
    out = []

    def walk(bone):
        bp = bone.get("pivot", [0, 0, 0])
        for cube in bone.get("cubes", []):
            o = cube["origin"]
            s = cube["size"]
            x0, y0, z0 = o
            x1, y1, z1 = x0 + s[0], y0 + s[1], z0 + s[2]
            # 角点顺序与 MC 一致：先底面再顶面
            pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
            rot = cube.get("rotation")
            pivot = cube.get("pivot", [x0 + s[0] / 2, y0 + s[1] / 2, z0 + s[2] / 2])
            if rot:
                pts = [bedrock_rotate(p, rot, pivot) for p in pts]
            # 6 个面的顶点环（与外法线方向无关，只为取色与投影）
            rings = {
                "north": (5, 4, 0, 1),   # -Z
                "south": (3, 2, 6, 7),   # +Z
                "west": (4, 7, 3, 0),    # -X
                "east": (1, 2, 6, 5),    # +X
                "up": (7, 6, 2, 3),      # +Y
                "down": (4, 5, 1, 0),    # -Y
            }
            for key in FACE_KEYS:
                uv = cube.get("uv", {})
                uvset = uv.get(key) if isinstance(uv, dict) and key in uv else None
                if uvset is None:
                    continue
                u, v = uvset.get("uv", [0, 0])
                uw, vh = uvset.get("uv_size", [1, 1])
                out.append({
                    "pts": [pts[i] for i in rings[key]],
                    "uv": (u, v, uw, vh),
                    "uv_center": (u + uw / 2.0, v + vh / 2.0),
                    "bone": bone["name"],
                })
        for child in bone.get("children", []):
            walk(child)

    # 建父子关系（geo 里是扁平的 parent 字段）
    roots = [b for b in geom["bones"] if not b.get("parent")]
    for b in geom["bones"]:
        b["children"] = []
    for b in geom["bones"]:
        p = b.get("parent")
        if p and p in bones:
            bones[p]["children"].append(b)
    for r in roots:
        walk(r)
    return out, geom["description"]


# ---------------------------------------------------------------- 渲染
def render(faces, size, view_dir, up_hint, w, h, ortho_scale, tex, tex_w, tex_h, tex_ch,
           tex_pix, flip_v=True):
    cam = [0.0, 0.0, 0.0]
    vd = norm(view_dir)
    up = norm(up_hint)
    right = norm(cross(up, vd))
    realup = cross(vd, right)
    pix = bytearray(w * h * 4)
    for i in range(w * h):
        pix[i * 4 + 3] = 255
        pix[i * 4] = 26
        pix[i * 4 + 1] = 28
        pix[i * 4 + 2] = 32

    light = norm((-0.45, 0.75, -0.50))
    tris = []
    for f in faces:
        u, v, uw, vh = f["uv"]
        sx = int(min(tex_w - 1, max(0, (u + uw / 2.0))))
        sy = int(min(tex_h - 1, max(0, (v + vh / 2.0))))
        if flip_v:
            sy = tex_h - 1 - sy
        o = (sy * tex_w + sx) * tex_ch
        base = (tex_pix[o] / 255.0, tex_pix[o + 1] / 255.0, tex_pix[o + 2] / 255.0)
        pts = f["pts"]
        # 面法线（用前三个点）
        n = norm(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])))
        lam = abs(dot(n, light))
        shade = 0.42 + 0.70 * lam
        col = tuple(min(1.0, c * shade) for c in base)
        # 投影
        proj = []
        for p in pts:
            rel = sub(p, cam)
            px = dot(rel, right)
            py = dot(rel, realup)
            pz = dot(rel, vd)
            k = ortho_scale / max(0.05, pz)
            proj.append(((px * k * w / 2.0) + w / 2.0, h / 2.0 - (py * k * w / 2.0), pz))
        depth = sum(q[2] for q in proj) / 4.0
        tris.append((depth, proj, col))
    tris.sort(key=lambda t: -t[0])
    for _, proj, col in tris:
        fill_quad(pix, w, h, proj, col)
    return pix


def fill_quad(pix, w, h, pts, col):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = max(0, int(min(xs))), min(w - 1, int(max(xs)) + 1)
    y0, y1 = max(0, int(min(ys))), min(h - 1, int(max(ys)) + 1)
    if x1 < x0 or y1 < y0:
        return
    r, g, b = int(col[0] * 255), int(col[1] * 255), int(col[2] * 255)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            inside = False
            j = 3
            for i in range(4):
                xi, yi = pts[i][0], pts[i][1]
                xj, yj = pts[j][0], pts[j][1]
                if (yi > y) != (yj > y):
                    xint = xi + (y - yi) * (xj - xi) / (yj - yi)
                    if x < xint:
                        inside = not inside
                j = i
            if inside:
                o = (y * w + x) * 4
                pix[o] = r
                pix[o + 1] = g
                pix[o + 2] = b
                pix[o + 3] = 255


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


VIEWS = {
    "side": ((1.0, 0.0, 0.12), (0, 1, 0)),      # 从 +X 看（与模型朝向无关，只是侧面）
    "persp": ((0.85, 0.55, 0.75), (0, 1, 0)),
    "top": ((0.05, 1.0, 0.05), (0, 0, -1)),
    "front": ((0.15, 0.12, -1.0), (0, 1, 0)),   # 从 -Z（箭头方向）看
}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", required=True)
    ap.add_argument("--tex", required=True)
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "hlc_geo_preview"))
    ap.add_argument("--views", default="side,persp,top")
    ap.add_argument("--res", default="900x620")
    ap.add_argument("--ortho", type=float, default=0.62, help="投影强度（越小越像正交）")
    ap.add_argument("--flip-v", action="store_true", default=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tw, th, tch, tpix = read_png(args.tex)
    faces, desc = collect_faces(args.geo)
    print(f"几何 {desc.get('identifier')}  贴图 {tw}x{th}x{tch}  面数 {len(faces)}  纹理宽高 {desc.get('texture_width')}x{desc.get('texture_height')}")

    w, h = [int(x) for x in args.res.lower().split("x")]
    for name in args.views.split(","):
        vd, up = VIEWS[name]
        pix = render(faces, None, vd, up, w, h, args.ortho, None, tw, th, tch, tpix)
        path = os.path.join(args.out, f"xbow_{name}.png")
        write_png(path, w, h, pix)
        print("  渲染 ->", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
