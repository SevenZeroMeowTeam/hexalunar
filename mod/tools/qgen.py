#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Q 弹版模型批量生成器 —— 把基础版 geo **就地变胖** + 贴图提色，写进 Q 版覆盖层。

用法
----
    python tools/qgen.py                # 生成 CONFIG 里的全部模型
    python tools/qgen.py awp crossbow_geo
    python tools/qgen.py --list

为什么这样变胖是安全的（Q 版最关键的约束是**一个锚点都不能动**）
------------------------------------------------------------------
基础版的 Java 侧写死了一批「模型像素锚点」（见 `weapon/WeaponMount` 与各 `weapon/*Item`）：

    AKM    枪口 (0,1.75,-11.60)   抛壳 (0.95,2.62,-2.30)   光轴 红点 4.07 / 4x 4.28
    AWP    枪口 (0,1.575,-16.275) 抛壳 (0.90,1.39,-0.60)   镜 3.15
    莫辛   枪口 (0,1.75,-16.78)   抛壳 (0.62,2.10,-1.95)   镜 3.44
    Kar98k 枪口 (0,2.25,-13.60)   抛壳 (0.55,3.00,-1.20)   镜 4.40
    M1     枪口 (0,2.30,-13.60)   抛壳 (0.42,2.90,-1.05)
    复合弓 箭杆 (0,0.85,-8.0)

本脚本用的变换是 **逐个方块绕自身几何中心在 X/Y 上放大**（Z 方向**完全不动**）：

  * 方块中心不变 ⇒ 高度中心不变 ⇒ **所有光轴 Y（红点/4x/镜）逐字不变**；
  * Z 一个面都不动 ⇒ **枪口端面、抛壳口、弹匣井、拉机柄、箭杆出膛点全部原地不动**；
  * 只放大不缩小 ⇒ **任何原本落在方块内部的锚点仍然在内部**（枪口点在枪管方块内、
    抛壳点在 `casing` 内、握把点在 `grip` 内……）；
  * 骨骼名 / 骨骼数 / 每骨骼方块数 / 骨骼 pivot 一律**原样保留** ⇒
    GeckoLib 的换弹/拉栓/抛壳动画与 `AkmGeoModel`… 的程序化驱动一行都不用改；
  * 仿射变换保共面性 ⇒ 基础版没有共面重叠面的话，变胖后也不会新出现 z-fighting。

不想变胖的零件（弓弦、箭杆、弹壳、通条……）在 `CONFIG[...]['skip']` 里按骨骼名排除。

脚本最后会**逐条自检**（骨骼集合一致、方块数一致、每个方块中心没动、尺寸只增不减、
锚点仍在其骨骼内），任何一条不过就直接退出码 1，不会写出坏模型。
"""
import io
import json
import os
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
QDIR = os.path.join(ROOT, 'src', 'qresources', 'assets', 'hexalunar_calamity_q')

# ---------------------------------------------------------------------------
# 每个模型一份配置
#   kx / ky       X / Y 加粗倍率（1.0 = 不动）
#   skip          不变胖的骨骼名（或名字前缀）
#   tail          (z_from, k)：z > z_from 的方块在 Z 上朝 z_from 压缩（只压缩"没锚点的一端"，
#                 比如枪托尾端）。默认不启用 —— 启用前必须确认那一端没有任何锚点。
#   anchors       必须仍然落在某个骨骼方块内的点（自动从 WeaponMount 抄来）
#   tex           贴图文件名（默认 <模型名>_geo.png）
# ---------------------------------------------------------------------------
# 瞄具类骨骼默认**只加宽、不加高**：它们的高度就是 Java 里的瞄具线
# （WeaponMount 的 SIGHT_Y / *_IRON_Y / *_SCOPE_Y），加高会把瞄准参照点顶偏；
# 只加宽既能变 Q 又让光轴/照门顶逐字不动。
FLATY = ('sight', 'sights', 'dot_sight', 'scope', 'rear_sight', 'front_sight')

CONFIG = {
    'awp': dict(
        kx=1.62, ky=1.50, skip=('bipod', 'casing'),
        anchors={'barrel': [(0.0, 1.575, -16.275)]},
        tail=(3.00, 0.78)),
    'compound_bow': dict(
        kx=1.42, ky=1.34, skip=('string_upper', 'string_lower', 'arrow', 'nock'),
        anchors={'arrow': [(0.0, 0.85, -8.0)]}),
    'crossbow_geo': dict(
        kx=1.42, ky=1.42, skip=('string_left', 'string_right', 'nock', 'bolt'),
        tex='crossbow_geo.png',
        tail=(1.60, 0.78)),          # 枪托尾端没有锚点，朝机匣收短
    'flashbang': dict(kx=1.48, ky=1.44, skip=()),
    'mud': dict(kx=1.48, ky=1.44, skip=()),
    'mosin': dict(
        kx=1.62, ky=1.52, skip=('casing', 'round_in', 'camera'),
        anchors={'barrel': [(0.0, 1.75, -16.78)]},
        tail=(2.00, 0.78)),          # 枪托尾段收短（锚点都在 z<2 的前中段）
    'kar98k': dict(
        kx=1.58, ky=1.48, skip=('casing', 'round_in', 'bipod'),
        anchors={'barrel': [(0.0, 2.25, -13.60)]},
        tail=(2.60, 0.78)),
    'm1_garand': dict(
        # ★ r111：漏夹本体 / 8 发子弹 / 弹夹盖都不参与 Q 化
        #   （漏夹要能塞进机匣顶部的开口、盖板的旋转要刚好盖住它，加粗会穿模）
        # ★★ 锚点不能再用枪口轴心 (0, 2.30, −13.60) —— 枪管从 r111 起是**空心圆管**，
        #   轴线正中是那个洞（不在任何方块里）。改取管壁那段小盒的中心。
        kx=1.58, ky=1.48, skip=('casing', 'clip_in', 'clip_rounds', 'cover'),
        anchors={'barrel': [(0.18, 2.37, -13.50)]},
        tail=(2.60, 0.78)),
}

GRADE = dict(color=1.28, bright=1.10, contrast=1.06)   # 贴图 Q 化：更艳更亮


def load_base(name):
    p = os.path.join(BASE, 'geo', name + '.geo.json')
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def skipped(bone_name, skip):
    return any(bone_name == s or bone_name.startswith(s) for s in skip)


def qify_cube(c, kx, ky, tail):
    """方块绕自身中心在 X/Y 放大；tail 生效时把 z > z_from 的部分朝 z_from 压缩。

    注意基础版 geo 里有 **负 size** 的方块（Bedrock 用负尺寸翻面），所以一律按
    lo/hi 处理再按原来的符号写回，别假设 size > 0。
    """
    o, s = c['origin'], c['size']
    out = dict(c)
    out['origin'] = list(o)
    out['size'] = list(s)
    for i, k in ((0, kx), (1, ky)):
        cen = o[i] + s[i] / 2.0
        lo = cen - abs(s[i]) * k / 2.0
        hi = cen + abs(s[i]) * k / 2.0
        out['origin'][i] = round(lo if s[i] >= 0 else hi, 6)
        out['size'][i] = round(abs(hi - lo) * (1 if s[i] >= 0 else -1), 6)
    if tail:
        zf, k = tail
        z0, z1 = o[2], o[2] + s[2]
        lo, hi = min(z0, z1), max(z0, z1)
        if hi > zf:
            nlo = lo if lo <= zf else zf + (lo - zf) * k
            nhi = zf + (hi - zf) * k
            out['origin'][2] = round(nlo if s[2] >= 0 else nhi, 6)
            out['size'][2] = round(abs(nhi - nlo) * (1 if s[2] >= 0 else -1), 6)
    # 带 rotation 的方块（Bedrock 的 cube rotation + pivot）要把 pivot 一起搬
    if 'rotation' in c and 'pivot' in c:
        pv = c['pivot']
        out['pivot'] = [
            round(o[i] + s[i] / 2.0 + (pv[i] - (o[i] + s[i] / 2.0)) * (kx if i == 0 else ky if i == 1 else 1.0), 6)
            for i in range(3)]
    return out


def inside(cubes, p, eps=1e-6):
    for c in cubes:
        o, s = c['origin'], c['size']
        if all(o[i] - eps <= p[i] <= o[i] + s[i] + eps for i in range(3)):
            return True
    return False


def grade_texture(name, tex_name):
    src = os.path.join(BASE, 'textures', 'models', tex_name)
    im = Image.open(src).convert('RGBA')
    r, g, b, a = im.split()
    rgb = Image.merge('RGB', (r, g, b))
    rgb = ImageEnhance.Color(rgb).enhance(GRADE['color'])
    rgb = ImageEnhance.Brightness(rgb).enhance(GRADE['bright'])
    rgb = ImageEnhance.Contrast(rgb).enhance(GRADE['contrast'])
    out = Image.merge('RGBA', rgb.split() + (a,))
    dst = os.path.join(QDIR, 'textures', 'models', tex_name)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    out.save(dst)
    return dst


def run(name):
    cfg = CONFIG[name]
    base = load_base(name)
    geo = json.loads(json.dumps(base))            # deep copy
    body = geo['minecraft:geometry'][0]
    bones = body['bones']
    kx, ky = cfg['kx'], cfg['ky']
    skip = cfg.get('skip', ())
    flaty = cfg.get('flaty', FLATY)
    tail = cfg.get('tail')

    fat_cubes = skipped_cubes = 0
    for b in bones:
        b['cubes'] = b.get('cubes', [])
        if skipped(b['name'], skip):
            skipped_cubes += len(b['cubes'])
            continue
        kyb = 1.0 if skipped(b['name'], flaty) else ky
        b['cubes'] = [qify_cube(c, kx, kyb, tail) for c in b['cubes']]
        fat_cubes += len(b['cubes'])

    # ---------------- 自检 ----------------
    errs = []
    bb = {b['name']: b for b in base['minecraft:geometry'][0]['bones']}
    for b in bb.values():
        b['cubes'] = b.get('cubes', [])
    nb = {b['name']: b for b in bones}
    if set(bb) != set(nb):
        errs.append('骨骼集合变了：%s' % (set(bb) ^ set(nb)))
    for nm, ob in bb.items():
        new = nb.get(nm)
        if new is None:
            continue
        if len(ob.get('cubes', [])) != len(new.get('cubes', [])):
            errs.append('%s 的方块数变了' % nm)
            continue
        if not skipped(nm, skip):
            flat = skipped(nm, flaty)     # 瞄具骨骼：高度必须逐字不变（那就是瞄具线）
            for i, (oc, nc) in enumerate(zip(ob.get('cubes', []), new.get('cubes', []))):
                if flat and abs(nc['size'][1] - oc['size'][1]) > 1e-9:
                    errs.append('%s[%d] 是瞄具骨骼但 Y 高度变了（%.4f -> %.4f）'
                                % (nm, i, oc['size'][1], nc['size'][1]))
                for ax in (0, 1):
                    ocen = oc['origin'][ax] + oc['size'][ax] / 2.0
                    ncen = nc['origin'][ax] + nc['size'][ax] / 2.0
                    if abs(ocen - ncen) > 2e-6:
                        errs.append('%s[%d] 轴%d 中心移动了 %.6f' % (nm, i, ax, ncen - ocen))
                    if abs(nc['size'][ax]) < abs(oc['size'][ax]) - 1e-9:
                        errs.append('%s[%d] 轴%d 变细了' % (nm, i, ax))
                # Z：没启用 tail 时必须一模一样；启用了只允许"朝 zf 压缩"
                if not tail:
                    if abs(oc['origin'][2] - nc['origin'][2]) > 1e-9 or \
                       abs(oc['size'][2] - nc['size'][2]) > 1e-9:
                        errs.append('%s[%d] 的 Z 面动了' % (nm, i))
                else:
                    zf = tail[0]
                    for edge in (0, 1):
                        oe = oc['origin'][2] + (oc['size'][2] if edge else 0)
                        ne = nc['origin'][2] + (nc['size'][2] if edge else 0)
                        if oe <= zf + 1e-9 and abs(oe - ne) > 1e-9:
                            errs.append('%s[%d] 锚点侧 Z%d 面动了（%.4f -> %.4f）'
                                        % (nm, i, edge, oe, ne))
                        if oe > zf + 1e-9 and ne > oe + 1e-9:
                            errs.append('%s[%d] 尾部 Z%d 反而变长了' % (nm, i, edge))
    for bone_name, pts in cfg.get('anchors', {}).items():
        if bone_name not in nb:
            errs.append('锚点骨骼 %s 不存在' % bone_name)
            continue
        for p in pts:
            if not inside(nb[bone_name]['cubes'], p):
                errs.append('锚点 %s 掉出骨骼 %s' % (p, bone_name))
            if not inside(bb[bone_name]['cubes'], p):
                errs.append('锚点 %s 原本就不在 %s 内（配置写错了）' % (p, bone_name))

    status = 'OK' if not errs else 'FAIL'
    print('%-14s kx=%.2f ky=%.2f  加粗 %d 方块 / 跳过 %d 方块  锚点 %d 组  自检 %s'
          % (name, kx, ky, fat_cubes, skipped_cubes, len(cfg.get('anchors', {})), status))
    for e in errs[:12]:
        print('    !! %s' % e)
    if errs:
        return False

    dst = os.path.join(QDIR, 'geo', name + '.geo.json')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with io.open(dst, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(geo, f, ensure_ascii=False, separators=(',', ':'))
    tex = cfg.get('tex', name + '_geo.png')
    tex_out = grade_texture(name, tex)
    print('    geo -> %s' % os.path.relpath(dst, ROOT))
    print('    tex -> %s' % os.path.relpath(tex_out, ROOT))
    return True


def main():
    args = [a for a in sys.argv[1:]]
    if '--list' in args:
        for k, v in CONFIG.items():
            print('%-14s kx=%.2f ky=%.2f skip=%s' % (k, v['kx'], v['ky'], v.get('skip', ())))
        return 0
    names = args or list(CONFIG)
    ok = True
    for n in names:
        if n not in CONFIG:
            print('未知模型: %s（可用: %s）' % (n, ', '.join(CONFIG)))
            ok = False
            continue
        ok = run(n) and ok
    print('\n结果: %s' % ('全部通过 ✅' if ok else '有 FAIL ❌'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
