# -*- coding: utf-8 -*-
"""生成 AWP Printstream 风格 Minecraft 模型包：
- Blockbench 工程 (.bbmodel，含骨骼分组)
- 基岩版几何 JSON (bones) + 换弹/瞄具调节动画 JSON
- Java 版物品模型 JSON
- 128x128 贴图 PNG (Printstream 白底黑纹风格)
坐标约定: X=枪管朝前, Y=上, Z=横向; 单位=像素(16=1格)
"""
import json, base64, zlib, struct, os, math

OUT = r"D:\Documents\qwen-agent\xsnqdjt9au\default\AWP_Printstream_Minecraft"
TEX_W, TEX_H = 128, 128

# ---------------- 立方体定义 (name, bone, from, to, zone) ----------------
CUBES = [
    # 机匣/枪托/握把 -> bone_body
    ("receiver",      "bone_body", (-4, 0, -1),      (4, 3, 1),        "PATTERN"),
    ("top_rail",      "bone_body", (-3.5, 3, -0.5),  (3.5, 3.5, 0.5),  "BLACK"),
    ("stock_main",    "bone_body", (-9, 0, -0.8),    (-4, 2.6, 0.8),   "PATTERN"),
    ("stock_cheek",   "bone_body", (-8.5, 2.6, -0.6),(-4.5, 3.4, 0.6), "PATTERN"),
    ("butt_pad",      "bone_body", (-9.8, -1.2, -0.9),(-9, 3, 0.9),    "BLACK"),
    ("stock_belly",   "bone_body", (-8, -1, -0.7),   (-4, 0, 0.7),     "BLACK"),
    ("grip",          "bone_body", (1.6, -3.2, -0.7),(3, 0, 0.7),      "GRAY"),
    ("trigger_guard", "bone_body", (0.2, -1.4, -0.4),(1.8, -0.8, 0.4), "BLACK"),
    ("trigger",       "bone_body", (0.9, -1.2, -0.15),(1.2, -0.2, 0.15),"BLACK"),
    # 枪管 -> bone_barrel
    ("barrel_collar", "bone_barrel", (4, 1.4, -0.7),   (5.5, 2.8, 0.7),  "SILVER"),
    ("barrel",        "bone_barrel", (5.5, 1.6, -0.5), (16, 2.6, 0.5),   "SILVER"),
    ("muzzle_collar", "bone_barrel", (15.6, 1.2, -0.9),(16.6, 3, 0.9),   "BLACK"),
    ("muzzle_brake",  "bone_barrel", (16.6, 1.35, -0.75),(18.2, 2.85, 0.75),"SILVER"),
    # 8倍镜 -> bone_scope
    ("scope_mount_f", "bone_scope", (1.5, 3.4, -0.4), (2.5, 4.3, 0.4),  "BLACK"),
    ("scope_mount_r", "bone_scope", (-1.5, 3.4, -0.4),(-0.5, 4.3, 0.4), "BLACK"),
    ("scope_tube",    "bone_scope", (-2, 4.2, -0.6),  (2.5, 5.4, 0.6),  "SILVER"),
    ("scope_objective","bone_scope",(2.5, 4, -0.9),   (3.9, 5.6, 0.9),  "SILVER"),
    ("scope_lens_f",  "bone_scope", (3.9, 4.15, -0.75),(4.05, 5.45, 0.75),"LENS"),
    ("scope_ocular",  "bone_scope", (-3, 4.05, -0.75),(-2, 5.55, 0.75), "BLACK"),
    ("scope_lens_r",  "bone_scope", (-3.15, 4.2, -0.6),(-3, 5.4, 0.6),  "LENS"),
    ("scope_turret_top","bone_scope",(-0.2, 5.4, -0.4),(0.6, 6.1, 0.4), "BLACK"),
    # 可调节部分(变倍环+侧调焦钮) -> bone_scope_adjust
    ("zoom_ring",     "bone_scope_adjust", (1, 4.05, -0.75),(1.6, 5.55, 0.75),"BLACK"),
    ("turret_side",   "bone_scope_adjust", (-0.2, 4.5, 0.6),(0.6, 5.2, 1.05),"BLACK"),
    # 弹匣 -> bone_magazine (换弹骨骼)
    ("magazine",      "bone_magazine", (-2.2, -3, -0.8), (-0.2, 0.2, 0.8), "BLACK"),
    ("mag_baseplate", "bone_magazine", (-2.4, -3.4, -0.9),(0, -3, 0.9),   "BLACK"),
    # 枪栓 -> bone_bolt (换弹骨骼)
    ("bolt_arm",      "bone_bolt", (-1.2, 1.6, 1),   (0.2, 2.4, 1.6),  "BLACK"),
    ("bolt_knob",     "bone_bolt", (-1, 1.5, 1.6),   (0, 2.5, 2.2),    "BLACK"),
    # 折叠两脚架 -> bone_bipod
    ("bipod_leg_r",   "bone_bipod", (5.5, 0.9, 0.5),  (9.5, 1.3, 0.9),   "SILVER"),
    ("bipod_foot_r",  "bone_bipod", (9.5, 0.75, 0.45),(10.2, 1.45, 1.15),"BLACK"),
    ("bipod_leg_l",   "bone_bipod", (5.5, 0.9, -0.9), (9.5, 1.3, -0.5),  "SILVER"),
    ("bipod_foot_l",  "bone_bipod", (9.5, 0.75, -1.15),(10.2, 1.45, -0.45),"BLACK"),
]

BONES = {
    "bone_body":          {"pivot": [0, 0, 0],       "parent": None},
    "bone_barrel":        {"pivot": [4, 2, 0],       "parent": "bone_body"},
    "bone_scope":         {"pivot": [0, 3.8, 0],     "parent": "bone_body"},
    "bone_scope_adjust":  {"pivot": [1.3, 4.8, 0],   "parent": "bone_scope"},
    "bone_magazine":      {"pivot": [-1.2, 0, 0],    "parent": "bone_body"},
    "bone_bolt":          {"pivot": [-0.5, 2, 1.2],  "parent": "bone_body"},
    "bone_bipod":         {"pivot": [6, 1.1, 0],     "parent": "bone_barrel"},
}

ZONES = {
    "PATTERN": (0, 0, 64, 48),
    "WHITE":   (64, 0, 96, 48),
    "SILVER":  (96, 0, 128, 48),
    "BLACK":   (0, 48, 64, 80),
    "LENS":    (64, 48, 96, 80),
    "GRAY":    (96, 48, 128, 80),
}

# ---------------- UV 打包 (box UV 布局) ----------------
cursor = {k: [z[0] + 1, z[1] + 1, 0] for k, z in ZONES.items()}  # x, y, row_h
uv_map = {}
for name, bone, f, t, zone in CUBES:
    w, h, d = t[0]-f[0], t[1]-f[1], t[2]-f[2]
    fw, fh = 2*(w+d), h+d
    zx, zy, zx2, zy2 = ZONES[zone]
    cx, cy, row_h = cursor[zone]
    if cx + fw > zx2:
        cy += row_h + 1
        cx = zx + 1
        row_h = 0
    assert cy + fh <= zy2, "zone overflow: %s %s" % (zone, name)
    cursor[zone] = [cx + fw + 1, cy, max(row_h, fh)]
    ou, ov = cx, cy
    uv_map[name] = {
        "origin": [ou, ov],
        "faces": {
            "up":    [ou+d,   ov,   ou+d+w,   ov+d],
            "down":  [ou+d+w, ov,   ou+d+2*w, ov+d],
            "west":  [ou,     ov+d, ou+d,     ov+d+h],
            "north": [ou+d,   ov+d, ou+d+w,   ov+d+h],
            "east":  [ou+d+w, ov+d, ou+2*d+w, ov+d+h],
            "south": [ou+2*d+w, ov+d, ou+2*(d+w), ov+d+h],
        },
    }

# ---------------- 贴图绘制 ----------------
px = bytearray(TEX_W * TEX_H * 3)
def setpx(x, y, c):
    if 0 <= x < TEX_W and 0 <= y < TEX_H:
        i = (y * TEX_W + x) * 3
        px[i:i+3] = bytes(c)
def fill_zone(key, c):
    zx, zy, zx2, zy2 = ZONES[key]
    for y in range(zy, zy2):
        for x in range(zx, zx2):
            setpx(x, y, c)

fill_zone("WHITE", (243, 243, 241))
fill_zone("SILVER", (198, 202, 204))
fill_zone("BLACK", (24, 24, 27))
fill_zone("GRAY", (62, 62, 66))
# PATTERN: 白底 + 黑斜纹 + XXX 标记 (Printstream 风格)
zx, zy, zx2, zy2 = ZONES["PATTERN"]
for y in range(zy, zy2):
    for x in range(zx, zx2):
        c = (240, 240, 238)
        if (x + y) % 12 < 2:
            c = (20, 20, 22)
        setpx(x, y, c)
for cxc in (14, 26, 38):
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if abs(abs(dx) - abs(dy)) == 0 or abs(abs(dx-1) - abs(dy)) == 0:
                setpx(cxc+dx, 36+dy, (18, 18, 20))
# SILVER 加横向拉丝线
zx, zy, zx2, zy2 = ZONES["SILVER"]
for y in range(zy, zy2):
    if y % 4 == 0:
        for x in range(zx, zx2):
            setpx(x, y, (170, 175, 178))
# LENS: 深色镜片 + 灰环
zx, zy, zx2, zy2 = ZONES["LENS"]
fill_zone("LENS", (10, 10, 12))
cx0, cy0 = (zx+zx2)//2, (zy+zy2)//2
for y in range(zy, zy2):
    for x in range(zx, zx2):
        r = math.hypot(x-cx0, y-cy0)
        if r < 6:
            setpx(x, y, (22, 28, 40))
        elif r < 8:
            setpx(x, y, (120, 130, 140))

def write_png(path, w, h, rgb):
    raw = b"".join(b"\x00" + bytes(rgb[y*w*3:(y+1)*w*3]) for y in range(h))
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "bedrock"), exist_ok=True)
os.makedirs(os.path.join(OUT, "java"), exist_ok=True)
tex_path = os.path.join(OUT, "awp_printstream.png")
write_png(tex_path, TEX_W, TEX_H, px)
with open(tex_path, "rb") as f:
    tex_b64 = base64.b64encode(f.read()).decode()

# ---------------- Blockbench 工程 ----------------
elements, outliner_children = [], {}
for idx, (name, bone, f, t, zone) in enumerate(CUBES):
    uuid = "el%02d" % idx
    faces = {}
    for fk in ("north", "south", "east", "west", "up", "down"):
        faces[fk] = {"uv": uv_map[name]["faces"][fk], "texture": 0}
    elements.append({
        "name": name, "uuid": uuid, "from": list(f), "to": list(t),
        "rotation": 0, "faces": faces, "export": True,
    })
    outliner_children.setdefault(bone, []).append(uuid)

def group_node(bname):
    kids = list(outliner_children.get(bname, []))
    for sub, info in BONES.items():
        if info["parent"] == bname:
            kids.append(group_node(sub))
    return {
        "name": bname, "uuid": "gr_" + bname, "origin": BONES[bname]["pivot"],
        "children": kids, "export": True, "isOpen": True,
    }

bbmodel = {
    "meta": {"format_version": "4.5", "model_format": "bedrock", "box_uv": False},
    "name": "AWP_Printstream",
    "uuid": "awp00001",
    "elements": elements,
    "outliner": [group_node("bone_body")],
    "textures": [{
        "name": "awp_printstream", "mode": "bitmap", "saved": True,
        "source": "data:image/png;base64," + tex_b64,
        "width": TEX_W, "height": TEX_H, "uuid": "tex0",
    }],
    "visibility": True,
}
with open(os.path.join(OUT, "awp_printstream.bbmodel"), "w", encoding="utf-8") as f:
    json.dump(bbmodel, f, ensure_ascii=False)

# ---------------- 基岩版几何 ----------------
bones_out = []
for bname, info in BONES.items():
    cubes = []
    for name, bone, f, t, zone in CUBES:
        if bone != bname:
            continue
        cubes.append({
            "origin": [f[0], f[1], f[2]],
            "size": [t[0]-f[0], t[1]-f[1], t[2]-f[2]],
            "uv": uv_map[name]["origin"],
            "inflate": 0,
        })
    b = {"name": bname, "pivot": info["pivot"], "cubes": cubes}
    if info["parent"]:
        b["parent"] = info["parent"]
    bones_out.append(b)
geometry = {
    "format_version": "1.16.0",
    "minecraft:geometry": [{
        "description": {
            "identifier": "geometry.awp_printstream",
            "texture_width": TEX_W, "texture_height": TEX_H,
            "visible_bounds_width": 3, "visible_bounds_height": 1.5,
            "visible_bounds_offset": [0, 0.25, 0],
        },
        "bones": bones_out,
    }],
}
with open(os.path.join(OUT, "bedrock", "geometry.awp_printstream.json"), "w", encoding="utf-8") as f:
    json.dump(geometry, f, ensure_ascii=False, indent=2)

# ---------------- 基岩版动画 ----------------
anim_reload = {
    "format_version": "1.10.0",
    "animations": {
        "animation.awp_printstream.reload": {
            "loop": False,
            "animation_length": 2.2,
            "bones": {
                "bone_magazine": {
                    "position": {
                        "0.0": [0, 0, 0], "0.35": [0, -5, 0],
                        "1.1": [0, -5, 0], "1.5": [0, 0, 0], "2.2": [0, 0, 0],
                    }
                },
                "bone_bolt": {
                    "position": {
                        "0.6": [0, 0, 0], "0.85": [-2.5, 0, 0],
                        "1.05": [-2.5, 0, 0], "1.3": [0, 0, 0], "2.2": [0, 0, 0],
                    }
                },
            },
        }
    },
}
anim_scope_adjust = {
    "format_version": "1.10.0",
    "animations": {
        "animation.awp_printstream.scope_adjust": {
            "loop": False,
            "animation_length": 1.6,
            "bones": {
                "bone_scope_adjust": {
                    "rotation": {"0.0": [0, 0, 0], "1.2": [720, 0, 0], "1.6": [720, 0, 0]}
                },
                "bone_scope": {
                    "rotation": {"0.0": [0, 0, 0], "0.6": [-3, 0, 0], "1.6": [-3, 0, 0]}
                },
            },
        }
    },
}
anim_scope_ads = {
    "format_version": "1.10.0",
    "animations": {
        "animation.awp_printstream.scope_ads": {
            "loop": False,
            "animation_length": 0.4,
            "bones": {
                "bone_scope": {
                    "position": {"0.0": [0, 0, 0], "0.25": [-0.5, 0.8, 0], "0.4": [-0.5, 0.8, 0]},
                    "rotation": {"0.0": [0, 0, 0], "0.25": [-8, 0, 0], "0.4": [-8, 0, 0]},
                }
            },
        }
    },
}
for fn, data in (
    ("animation.awp_printstream.reload.json", anim_reload),
    ("animation.awp_printstream.scope_adjust.json", anim_scope_adjust),
    ("animation.awp_printstream.scope_ads.json", anim_scope_ads),
):
    with open(os.path.join(OUT, "bedrock", fn), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------- Java 版物品模型 ----------------
jl_elements = []
for name, bone, f, t, zone in CUBES:
    faces = {}
    for fk in ("north", "south", "east", "west", "up", "down"):
        faces[fk] = {"uv": uv_map[name]["faces"][fk], "texture": "#0"}
    jl_elements.append({"from": list(f), "to": list(t), "faces": faces})
java_model = {
    "credit": "AWP Printstream style - polygon model for Minecraft",
    "gui_light": "front",
    "textures": {"0": "item/awp_printstream", "particle": "item/awp_printstream"},
    "elements": jl_elements,
    "display": {
        "gui": {"rotation": [25, -45, 0], "translation": [0, 1, 0], "scale": [0.5, 0.5, 0.5]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
        "thirdperson_righthand": {"rotation": [0, -90, 5], "translation": [1, 3, 1], "scale": [0.5, 0.5, 0.5]},
        "firstperson_righthand": {"rotation": [0, -90, 5], "translation": [1, 3, 1], "scale": [0.5, 0.5, 0.5]},
    },
}
with open(os.path.join(OUT, "java", "awp_printstream.json"), "w", encoding="utf-8") as f:
    json.dump(java_model, f, ensure_ascii=False, indent=2)

# 校验
for root, _, files in os.walk(OUT):
    for fn in files:
        p = os.path.join(root, fn)
        if fn.endswith(".json") or fn.endswith(".bbmodel"):
            with open(p, encoding="utf-8") as fh:
                json.load(fh)
print("OK cubes=%d quads=%d" % (len(CUBES), len(CUBES)*6))
for root, _, files in os.walk(OUT):
    for fn in sorted(files):
        print(os.path.join(root, fn))
