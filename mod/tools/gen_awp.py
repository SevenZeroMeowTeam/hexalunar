# -*- coding: utf-8 -*-
"""AWP Printstream 风格 Minecraft 模型生成器 v2
- 512x512 贴图, 全四边面(box=6 quads), 写实细节
- 骨骼: body/barrel/bipod/scope/scope_zoom/scope_turrets/magazine/bolt/shell
- 动画: 换弹(含抛壳), 独立拉栓抛壳, 瞄具调节, 开镜
坐标: X=枪口朝前, Y=上, Z=横向; 单位像素(16=1格)
"""
import json, base64, zlib, struct, os, math, random

OUT = r"D:\Documents\qwen-agent\xsnqdjt9au\default\AWP_Printstream_Minecraft"
TEX_W, TEX_H = 512, 512

CUBES = [
    # ---- bone_body 机匣/枪托/握把 ----
    ("receiver_main",  "bone_body", (-4, 0, -1),       (4, 3, 1),        "PATTERN"),
    ("rail",           "bone_body", (-3.5, 3, -0.5),   (3.5, 3.5, 0.5),  "BLACK"),
    ("ejection_port",  "bone_body", (-0.5, 1.2, 0.98), (1.8, 2.6, 1.04), "BLACK"),
    ("stock_main",     "bone_body", (-9, 0, -0.8),     (-4, 2.6, 0.8),   "PATTERN"),
    ("cheek_riser",    "bone_body", (-8.5, 2.6, -0.6), (-4.5, 3.3, 0.6), "PATTERN"),
    ("cheek_knob",     "bone_body", (-6.8, 2.7, 0.6),  (-6.2, 3.1, 0.95),"BLACK"),
    ("butt_pad",       "bone_body", (-9.8, -1.4, -0.9),(-9, 3, 0.9),     "BLACK"),
    ("stock_belly",    "bone_body", (-8, -1, -0.7),    (-4, 0, 0.7),     "BLACK"),
    ("grip",           "bone_body", (1.6, -3.4, -0.7), (3, 0, 0.7),      "GRAY"),
    ("trigger_guard",  "bone_body", (0.2, -1.5, -0.4), (1.8, -0.8, 0.4), "BLACK"),
    ("trigger",        "bone_body", (0.9, -1.3, -0.15),(1.2, -0.3, 0.15),"BLACK"),
    ("magwell",        "bone_body", (-2.4, -0.6, -0.9),(0, 0.2, 0.9),    "BLACK"),
    # ---- bone_barrel 枪管 ----
    ("barrel_collar",  "bone_barrel", (4, 1.2, -0.8),    (5.6, 3, 0.8),    "SILVER"),
    ("barrel_mid",     "bone_barrel", (5.6, 1.7, -0.45), (12, 2.5, 0.45),  "SILVER"),
    ("barrel_front",   "bone_barrel", (12, 1.75, -0.4),  (16.5, 2.45, 0.4),"SILVER"),
    ("muzzle_collar",  "bone_barrel", (16.2, 1.3, -0.9), (17, 2.9, 0.9),   "BLACK"),
    ("muzzle_brake",   "bone_barrel", (17, 1.45, -0.7),  (19, 2.75, 0.7),  "VENT"),
    ("brake_tip",      "bone_barrel", (19, 1.6, -0.55),  (19.4, 2.6, 0.55),"BLACK"),
    # ---- bone_scope 8倍镜 ----
    ("ring_front",     "bone_scope", (1.6, 3.4, -0.45),  (2.4, 4.4, 0.45),  "BLACK"),
    ("ring_rear",      "bone_scope", (-1.6, 3.4, -0.45), (-0.8, 4.4, 0.45), "BLACK"),
    ("scope_tube",     "bone_scope", (-2, 4.3, -0.55),   (2.2, 5.4, 0.55),  "SILVER"),
    ("objective_bell", "bone_scope", (2.2, 4.05, -0.95), (4.2, 5.65, 0.95), "SILVER"),
    ("objective_rim",  "bone_scope", (4.2, 4.15, -0.85), (4.5, 5.55, 0.85), "BLACK"),
    ("lens_front",     "bone_scope", (4.5, 4.3, -0.7),   (4.62, 5.4, 0.7),  "LENS"),
    ("ocular_bell",    "bone_scope", (-3.2, 4.15, -0.75),(-2, 5.55, 0.75),  "BLACK"),
    ("lens_rear",      "bone_scope", (-3.32, 4.3, -0.6), (-3.2, 5.4, 0.6),  "LENS"),
    ("turret_elev",    "bone_scope", (-0.3, 5.4, -0.45), (0.5, 6.2, 0.45),  "BLACK"),
    ("turret_cap",     "bone_scope", (-0.2, 6.2, -0.35), (0.4, 6.45, 0.35), "SILVER"),
    # ---- bone_scope_zoom 变倍环(可调节) ----
    ("zoom_ring",      "bone_scope_zoom", (1.2, 4.15, -0.7), (1.8, 5.55, 0.7), "BLACK"),
    # ---- bone_scope_turrets 侧调焦/风偏钮(可调节) ----
    ("turret_side",    "bone_scope_turrets", (-0.3, 4.55, 0.55),  (0.5, 5.25, 1.15),  "BLACK"),
    ("turret_wind",    "bone_scope_turrets", (-0.3, 4.55, -1.15), (0.5, 5.25, -0.55), "BLACK"),
    # ---- bone_magazine 弹匣(换弹) ----
    ("mag_body",       "bone_magazine", (-2.2, -3.2, -0.75), (-0.2, 0.2, 0.75), "BLACK"),
    ("mag_base",       "bone_magazine", (-2.4, -3.6, -0.85), (0, -3.2, 0.85),   "BLACK"),
    # ---- bone_bolt 枪栓(拉栓) ----
    ("bolt_shroud",    "bone_bolt", (-2.2, 1.6, -0.6), (-1.4, 2.6, 0.6),  "SILVER"),
    ("bolt_arm",       "bone_bolt", (-1.4, 1.7, 0.95), (0.4, 2.5, 1.5),   "SILVER"),
    ("bolt_knob",      "bone_bolt", (-1.1, 1.55, 1.5), (0.1, 2.65, 2.1),  "BLACK"),
    # ---- bone_shell 弹壳(抛壳) ----
    ("shell_casing",   "bone_shell", (0.0, 1.2, -0.3), (1.2, 1.8, 0.3), "BRASS"),
    # ---- bone_bipod 两脚架 ----
    ("bipod_mount",    "bone_bipod", (5.6, 0.9, -0.5),  (6.6, 1.6, 0.5),    "BLACK"),
    ("bipod_leg_r",    "bone_bipod", (6.4, 1.0, 0.4),   (10.4, 1.4, 0.8),   "SILVER"),
    ("bipod_foot_r",   "bone_bipod", (10.4, 0.85, 0.35),(11.1, 1.55, 1.05), "BLACK"),
    ("bipod_leg_l",    "bone_bipod", (6.4, 1.0, -0.8),  (10.4, 1.4, -0.4),  "SILVER"),
    ("bipod_foot_l",   "bone_bipod", (10.4, 0.85, -1.05),(11.1, 1.55, -0.35),"BLACK"),
]

BONES = {
    "bone_body":          {"pivot": [0, 0, 0],      "parent": None},
    "bone_barrel":        {"pivot": [4, 2, 0],      "parent": "bone_body"},
    "bone_bipod":         {"pivot": [6, 1.2, 0],    "parent": "bone_barrel"},
    "bone_scope":         {"pivot": [0, 3.8, 0],    "parent": "bone_body"},
    "bone_scope_zoom":    {"pivot": [1.5, 4.85, 0], "parent": "bone_scope"},
    "bone_scope_turrets": {"pivot": [0.1, 4.9, 0],  "parent": "bone_scope"},
    "bone_magazine":      {"pivot": [-1.2, 0, 0],   "parent": "bone_body"},
    "bone_bolt":          {"pivot": [-0.5, 2.1, 1.2],"parent": "bone_body"},
    "bone_shell":         {"pivot": [0.6, 1.5, 0],  "parent": "bone_body"},
}

ZONES = {
    "PATTERN": (0, 0, 192, 128),
    "SILVER":  (192, 0, 320, 128),
    "BLACK":   (320, 0, 448, 128),
    "GRAY":    (448, 0, 512, 64),
    "LENS":    (448, 64, 512, 128),
    "BRASS":   (0, 128, 64, 192),
    "VENT":    (64, 128, 160, 192),
}

# ---------- UV 打包 (每面 4 个 UV 角点 = 四边面) ----------
cursor = {k: [z[0] + 1, z[1] + 1, 0] for k, z in ZONES.items()}
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
            "up":    [ou+d,     ov,   ou+d+w,     ov+d],
            "down":  [ou+d+w,   ov,   ou+d+2*w,   ov+d],
            "west":  [ou,       ov+d, ou+d,       ov+d+h],
            "north": [ou+d,     ov+d, ou+d+w,     ov+d+h],
            "east":  [ou+d+w,   ov+d, ou+2*d+w,   ov+d+h],
            "south": [ou+2*d+w, ov+d, ou+2*(d+w), ov+d+h],
        },
    }

# ---------- 512x512 贴图绘制 ----------
px = bytearray(TEX_W * TEX_H * 3)
def setpx(x, y, c):
    if 0 <= x < TEX_W and 0 <= y < TEX_H:
        i = (y * TEX_W + x) * 3
        px[i:i+3] = bytes(max(0, min(255, int(round(v)))) for v in c)
def noise(x, y, amp):
    return ((x * 13 + y * 7) * 31) % (2 * amp + 1) - amp
def fill(key, fn):
    zx, zy, zx2, zy2 = ZONES[key]
    for y in range(zy, zy2):
        for x in range(zx, zx2):
            setpx(x, y, fn(x - zx, y - zy, x, y))

def f_pattern(lx, ly, gx, gy):
    c = [238, 238, 235]
    if ly in (20, 21, 60, 61, 100, 101):
        c = [150, 150, 148]
    if 70 <= ly < 110 and (lx + ly) % 24 < 4:
        c = [30, 30, 32]
    if ly == 115 and lx % 16 < 8:
        c = [120, 120, 118]
    for cxc in (40, 70, 100):
        dx, dy = lx - cxc, ly - 40
        if abs(dx) <= 11 and abs(dy) <= 11 and abs(abs(dx) - abs(dy)) <= 2:
            c = [25, 25, 28]
    for sx, sy in ((8, 8), (184, 8), (8, 120), (184, 120)):
        if (lx - sx) ** 2 + (ly - sy) ** 2 <= 9:
            c = [60, 60, 60]
    return c

def f_silver(lx, ly, gx, gy):
    g = 225 - int(75 * min(1.0, ly / 128.0))
    c = [g, g + 3, g + 5]
    if ly % 3 == 0:
        c = [v - 6 for v in c]
    if 40 <= lx < 52:
        c = [min(255, v + 25) for v in c]
    n = noise(gx, gy, 3)
    return [v + n for v in c]

def f_black(lx, ly, gx, gy):
    v = 26 + noise(gx, gy, 4) + (4 if ly < 6 else 0)
    return [v, v, v + 3]

def f_gray(lx, ly, gx, gy):
    v = 70 + noise(gx, gy, 6)
    if 20 <= ly < 26 or 40 <= ly < 46:
        v -= 25
    return [v, v, v + 4]

def f_lens(lx, ly, gx, gy):
    r = math.hypot(lx - 32, ly - 32)
    if 26 <= r < 28:
        return [90, 100, 115]
    if r < 10:
        c = [35, 45, 80]
    elif r < 18:
        c = [22, 30, 55]
    elif r < 26:
        c = [14, 18, 32]
    else:
        c = [8, 9, 12]
    ang = math.degrees(math.atan2(ly - 32, lx - 32)) % 360
    if 200 <= ang <= 240 and 12 <= r <= 14:
        c = [120, 140, 180]
    return c

def f_brass(lx, ly, gx, gy):
    g = 215 - int(55 * min(1.0, ly / 64.0))
    c = [g, int(g * 0.8), int(g * 0.45)]
    if ly == 8:
        c = [120, 90, 40]
    if 20 <= lx < 26:
        c = [min(255, v + 30) for v in c]
    return c

def f_vent(lx, ly, gx, gy):
    g = 210 - int(50 * min(1.0, ly / 64.0))
    c = [g, g + 3, g + 5]
    for x0 in (20, 44, 68):
        if x0 <= lx < x0 + 10 and 10 <= ly < 54:
            c = [20, 20, 22]
    return c

fill("PATTERN", f_pattern)
fill("SILVER", f_silver)
fill("BLACK", f_black)
fill("GRAY", f_gray)
fill("LENS", f_lens)
fill("BRASS", f_brass)
fill("VENT", f_vent)

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

# ---------- 四边面校验 ----------
quad_count = 0
for name, bone, f, t, zone in CUBES:
    for fk, uv in uv_map[name]["faces"].items():
        assert len(uv) == 4 and all(len(p) == 2 for p in [uv[0:2], uv[2:4]]), name
        quad_count += 1

# ---------- Blockbench 工程 ----------
elements, outliner_children = [], {}
for idx, (name, bone, f, t, zone) in enumerate(CUBES):
    uuid = "el%02d" % idx
    faces = {fk: {"uv": uv_map[name]["faces"][fk], "texture": 0}
             for fk in ("north", "south", "east", "west", "up", "down")}
    elements.append({"name": name, "uuid": uuid, "from": list(f), "to": list(t),
                     "rotation": 0, "faces": faces, "export": True})
    outliner_children.setdefault(bone, []).append(uuid)

def group_node(bname):
    kids = list(outliner_children.get(bname, []))
    for sub, info in BONES.items():
        if info["parent"] == bname:
            kids.append(group_node(sub))
    return {"name": bname, "uuid": "gr_" + bname, "origin": BONES[bname]["pivot"],
            "children": kids, "export": True, "isOpen": True}

bbmodel = {
    "meta": {"format_version": "4.5", "model_format": "bedrock", "box_uv": False},
    "name": "AWP_Printstream_v2",
    "uuid": "awp00002",
    "elements": elements,
    "outliner": [group_node("bone_body")],
    "textures": [{"name": "awp_printstream", "mode": "bitmap", "saved": True,
                  "source": "data:image/png;base64," + tex_b64,
                  "width": TEX_W, "height": TEX_H, "uuid": "tex0"}],
    "visibility": True,
}
with open(os.path.join(OUT, "awp_printstream.bbmodel"), "w", encoding="utf-8") as f:
    json.dump(bbmodel, f, ensure_ascii=False)

# ---------- 基岩版几何 ----------
bones_out = []
for bname, info in BONES.items():
    cubes = [{"origin": [f[0], f[1], f[2]],
              "size": [t[0]-f[0], t[1]-f[1], t[2]-f[2]],
              "uv": uv_map[name]["origin"], "inflate": 0}
             for name, bone, f, t, zone in CUBES if bone == bname]
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

# ---------- 动画 ----------
SHELL_EJECT_POS = {
    "0.75": [0, 0, 0],
    "0.85": [0.3, 1.0, 1.3],
    "0.95": {"post": [2.5, 4.5, 5], "lerp_mode": "catmull_rom"},
    "1.25": [3, 1.5, 6],
    "1.55": [3.2, -7, 6.5],
    "1.56": [0, 0, 0],
    "2.6":  [0, 0, 0],
}
SHELL_EJECT_ROT = {
    "0.75": [0, 0, 0],
    "0.85": [40, 0, -30],
    "0.95": [180, 0, -140],
    "1.25": [420, 60, -220],
    "1.55": [720, 90, -300],
    "1.56": [0, 0, 0],
    "2.6":  [0, 0, 0],
}
BOLT_CYCLE = {
    "0.0": [0, 0, 0], "0.3": [0, 0.6, 0], "0.55": [-3, 0.6, 0],
    "0.8": [-3, 0.6, 0], "1.05": [0, 0.4, 0], "1.3": [0, 0, 0],
}
animations = {
    "animation.awp_printstream.reload": {
        "loop": False, "animation_length": 2.6,
        "bones": {
            "bone_magazine": {"position": {
                "0.0": [0, 0, 0], "0.35": [0, -5.5, 0], "0.55": [0, -5.5, 1.5],
                "1.3": [0, -5.5, 1.5], "1.55": [0, -5.5, 0], "1.9": [0, 0, 0], "2.6": [0, 0, 0]}},
            "bone_bolt": {"position": {
                "0.0": [0, 0, 0], "0.6": [0, 0, 0], "0.85": [-3, 0.6, 0],
                "1.1": [-3, 0.6, 0], "1.35": [0, 0.4, 0], "1.6": [0, 0, 0], "2.6": [0, 0, 0]}},
            "bone_shell": {"position": SHELL_EJECT_POS, "rotation": SHELL_EJECT_ROT},
        },
    },
    "animation.awp_printstream.bolt_cycle": {
        "loop": False, "animation_length": 1.4,
        "bones": {
            "bone_bolt": {"position": {
                "0.0": [0, 0, 0], "0.25": [0, 0.6, 0], "0.5": [-3, 0.6, 0],
                "0.75": [-3, 0.6, 0], "1.0": [0, 0.4, 0], "1.25": [0, 0, 0], "1.4": [0, 0, 0]}},
            "bone_shell": {
                "position": {
                    "0.45": [0, 0, 0], "0.55": [0.3, 1.0, 1.3], "0.65": [2.5, 4.5, 5],
                    "0.9": [3, 1.5, 6], "1.15": [3.2, -7, 6.5], "1.16": [0, 0, 0], "1.4": [0, 0, 0]},
                "rotation": {
                    "0.45": [0, 0, 0], "0.55": [40, 0, -30], "0.7": [180, 0, -140],
                    "0.95": [420, 60, -220], "1.15": [720, 90, -300], "1.16": [0, 0, 0], "1.4": [0, 0, 0]}},
        },
    },
    "animation.awp_printstream.scope_adjust": {
        "loop": False, "animation_length": 1.6,
        "bones": {
            "bone_scope_zoom": {"rotation": {"0.0": [0, 0, 0], "1.2": [720, 0, 0], "1.6": [720, 0, 0]}},
            "bone_scope_turrets": {"rotation": {"0.0": [0, 0, 0], "1.2": [0, 0, 540], "1.6": [0, 0, 540]}},
        },
    },
    "animation.awp_printstream.scope_ads": {
        "loop": False, "animation_length": 0.4,
        "bones": {
            "bone_scope": {
                "position": {"0.0": [0, 0, 0], "0.25": [-0.5, 0.8, 0], "0.4": [-0.5, 0.8, 0]},
                "rotation": {"0.0": [0, 0, 0], "0.25": [-8, 0, 0], "0.4": [-8, 0, 0]}},
        },
    },
}
for aname, adata in animations.items():
    fn = aname.replace("animation.awp_printstream.", "animation.awp_printstream.") + ".json"
    with open(os.path.join(OUT, "bedrock", fn), "w", encoding="utf-8") as f:
        json.dump({"format_version": "1.10.0", "animations": {aname: adata}},
                  f, ensure_ascii=False, indent=2)

# ---------- Java 版物品模型 ----------
jl_elements = []
for name, bone, f, t, zone in CUBES:
    faces = {fk: {"uv": uv_map[name]["faces"][fk], "texture": "#0"}
             for fk in ("north", "south", "east", "west", "up", "down")}
    jl_elements.append({"from": list(f), "to": list(t), "faces": faces})
java_model = {
    "credit": "AWP Printstream style v2 - quad-only polygon model for Minecraft",
    "gui_light": "front",
    "textures": {"0": "item/awp_printstream", "particle": "item/awp_printstream"},
    "elements": jl_elements,
    "display": {
        "gui": {"rotation": [25, -45, 0], "translation": [0, 1, 0], "scale": [0.4, 0.4, 0.4]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
        "fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
        "thirdperson_righthand": {"rotation": [0, -90, 5], "translation": [1, 3, 1], "scale": [0.4, 0.4, 0.4]},
        "firstperson_righthand": {"rotation": [0, -90, 5], "translation": [1, 3, 1], "scale": [0.4, 0.4, 0.4]},
    },
}
with open(os.path.join(OUT, "java", "awp_printstream.json"), "w", encoding="utf-8") as f:
    json.dump(java_model, f, ensure_ascii=False, indent=2)

# ---------- 校验 ----------
for root, _, files in os.walk(OUT):
    for fn in files:
        p = os.path.join(root, fn)
        if fn.endswith(".json") or fn.endswith(".bbmodel"):
            with open(p, encoding="utf-8") as fh:
                json.load(fh)
print("OK cubes=%d quads=%d tex=%dx%d" % (len(CUBES), quad_count, TEX_W, TEX_H))
for root, _, files in os.walk(OUT):
    for fn in sorted(files):
        print(os.path.join(root, fn))
