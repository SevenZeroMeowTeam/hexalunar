"""把 Blockbench .bbmodel（网格模型）转成 Forge 能用的 OBJ + MTL。

关键点（沿用本项目踩过的坑）：
  - Forge 的 ObjLoader 把 OBJ 坐标当【方块】用 ⇒ /16
  - 几何要居中在 (0.5,0.5,0.5)，因为 ItemRenderer 会无条件 translate(-0.5,-0.5,-0.5)
  - bbmodel 的 UV 是【贴图像素】坐标 ⇒ /贴图宽高

用法: python bbmodel_to_obj.py <bbmodel> <输出obj> [--mtl <mtl>] [--tex <sprite资源名>]
"""
import json
import os
import struct
import sys

a = sys.argv
src, out_obj = a[1], a[2]
out_mtl = a[a.index('--mtl') + 1] if '--mtl' in a else os.path.splitext(out_obj)[0] + '.mtl'
tex_sprite = a[a.index('--tex') + 1] if '--tex' in a else 'hexalunar_calamity:models/unknown'


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        return (16, 16)
    w, h = struct.unpack('>II', head[16:24])
    return (w, h)


with open(src, encoding='utf-8', errors='replace') as f:
    bb = json.load(f)

texs = bb.get('textures') or []
tex_dir = os.path.dirname(os.path.abspath(src))
tex_path = None
for t in texs:
    p = t.get('relative_path') or t.get('name') or ''
    cand = os.path.join(tex_dir, os.path.basename(p))
    if os.path.exists(cand):
        tex_path = cand
        break
tw, th = png_size(tex_path) if tex_path else (16, 16)
print(f'模型: {os.path.basename(src)}｜贴图: {os.path.basename(tex_path) if tex_path else "无"} {tw}x{th}')

verts = []          # 3D 顶点（模型单位）
uvs = []            # UV（0..1）
faces = []          # 每个面: [(vert_idx, uv_idx), ...] + material
mats = {}

for el in bb.get('elements', []):
    if not el.get('visibility', True):
        continue
    if el.get('type') != 'mesh':
        print(f"  [跳过] 非 mesh 元素: {el.get('name')} ({el.get('type')})")
        continue
    verts_map = el.get('vertices') or {}
    order = list(verts_map.keys())
    idx_of = {}
    for vid in order:
        idx_of[vid] = len(verts)
        v = verts_map[vid]
        verts.append((float(v[0]), float(v[1]), float(v[2])))
    for fid, face in (el.get('faces') or {}).items():
        vids = [str(x) for x in face.get('vertices', [])]
        if len(vids) < 3:
            continue
        uvmap = face.get('uv') or {}
        face_uv = []
        for vid in vids:
            if vid in uvmap:
                u, v = uvmap[vid]
                face_uv.append((float(u) / tw, 1.0 - float(v) / th))
            else:
                face_uv.append((0.0, 0.0))
        ti = face.get('texture')
        mat = f'mat{ti}' if ti is not None else 'mat'
        mats[mat] = ti
        faces.append(([idx_of[v] for v in vids], face_uv, mat))

print(f'顶点 {len(verts)}｜面 {len(faces)}')

xs = [v[0] for v in verts]
ys = [v[1] for v in verts]
zs = [v[2] for v in verts]
cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
print(f'原始包围盒 尺寸 {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}（模型单位）'
      f' → /16 后 {size[0]/16:.3f} x {size[1]/16:.3f} x {size[2]/16:.3f} 格')


def conv(v):
    """模型单位 -> 方块单位，并居中到 (0.5,0.5,0.5)"""
    return ((v[0] - cx) / 16.0 + 0.5, (v[1] - cy) / 16.0 + 0.5, (v[2] - cz) / 16.0 + 0.5)


with open(out_obj, 'w', encoding='utf-8') as f:
    f.write(f'# 由 tools/bbmodel_to_obj.py 从 {os.path.basename(src)} 转换\n')
    f.write(f'mtllib {os.path.basename(out_mtl)}\n')
    f.write('o model\n')
    for v in verts:
        p = conv(v)
        f.write(f'v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n')
    for uv in uvs:
        f.write(f'vt {uv[0]:.6f} {uv[1]:.6f}\n')
    for vert_idxs, face_uv, mat in faces:
        for uv in face_uv:
            uvs.append(uv)
    # UV 索引在写完之后才知道，改为第二遍
    base_uv = len(uvs) - sum(len(fu) for _, fu, _ in faces)

with open(out_obj, 'w', encoding='utf-8') as f:
    f.write(f'# 由 tools/bbmodel_to_obj.py 从 {os.path.basename(src)} 转换\n')
    f.write(f'mtllib {os.path.basename(out_mtl)}\n')
    f.write('o model\n')
    for v in verts:
        p = conv(v)
        f.write(f'v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n')
    for _, face_uv, _ in faces:
        for u, vv in face_uv:
            f.write(f'vt {u:.6f} {vv:.6f}\n')
    cur = None
    uv_i = 1
    for vert_idxs, face_uv, mat in faces:
        if mat != cur:
            f.write(f'usemtl {mat}\n')
            cur = mat
        toks = ' '.join(f'{vi + 1}/{uv_i + k}' for k, vi in enumerate(vert_idxs))
        f.write(f'f {toks}\n')
        uv_i += len(vert_idxs)

with open(out_mtl, 'w', encoding='utf-8') as f:
    for mat in (mats or {'mat': None}):
        f.write(f'newmtl {mat}\nKd 1.0 1.0 1.0\nKa 1.0 1.0 1.0\nKs 0.0 0.0 0.0\nNs 0\n'
                f'map_Kd {tex_sprite}\n\n')
print(f'写出 {os.path.basename(out_obj)} + {os.path.basename(out_mtl)}'
      f'（贴图引用 {tex_sprite}）')
