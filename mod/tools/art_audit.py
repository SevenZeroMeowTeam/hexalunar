#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""美术规范体检 —— 按根目录《美术规范.md》检查 `assets/hexalunar_calamity/geo/*.geo.json` 与配套贴图/动画。

只读，不改任何模型。终端里中文可能显示成乱码（PowerShell 解码问题），**完整报告看 `build/art_audit.txt`**。

用法::

    python tools/art_audit.py             # 全量体检
    python tools/art_audit.py awp akm     # 只查指定模型
    python tools/art_audit.py -v          # 明细也打到终端（默认只打摘要）

检查项编号与《美术规范.md》第七节一一对应：

  A 单位/朝向   枪械最长轴必须是 Z（前向 −Z）；长度 0.9~2.6 格（投掷物 0.2~0.9 格）；骨骼不许带旋转
  B 贴图        512²（与 geo 的 texture_* 一致）；面必须齐全、uv_size>0、UV 不越界；逐面图集不许面重叠
  C 命名        骨骼名 ^[a-z][a-z0-9_]*$、父骨存在、必需骨 root/move/body、名字不重复
  D pivot       有方块的骨：pivot 到自己几何的距离 ≤ 4u（轴心写错基本都会超）；控制器骨豁免
  E 抛壳       有 casing 骨的武器：casing 几何中心 x > 0（+X = 射手右侧，铁律）
  F 规模       方块三轴尺寸 > 0（负尺寸 = 生成器没归一化 min/max）；骨 ≤ 40、方块 ≤ 600
  G 交付       贴图 `<名>_geo.png` 存在、`_glowmask.png` 存在、`animations/<名>.animation.json` 存在

等级：错误（必须改，退出码 1）/ 警告（该改，存量豁免见规范第八节）/ 提示（知道就行）。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # mod/
ASSETS = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
GEO = os.path.join(ASSETS, 'geo')
TEX = os.path.join(ASSETS, 'textures', 'models')
ANIM = os.path.join(ASSETS, 'animations')
REPORT = os.path.join(ROOT, 'build', 'art_audit.txt')

U_PER_BLOCK = 16.0                                  # 16 u = 1 方块
NAME_RE = re.compile(r'^[a-z][a-z0-9_]*$')
CONTROLLER_BONES = {'root', 'move', 'camera', 'constraint'}   # 纯控制器骨，pivot 允许离几何远
FACES = ('north', 'south', 'east', 'west', 'up', 'down')
PIVOT_FAR = 4.0                                     # pivot 离自身几何超过这么多 u = 轴心写错了
TEX_WANT = 512                                      # 规范贴图边长
MAX_BONES, MAX_CUBES = 40, 600

# 类目 → 长度区间（格）。gun 额外要求最长轴 = Z；bow/throwable 不服从此条。
KIND = {
    'akm': 'gun', 'awp': 'gun', 'kar98k': 'gun', 'm1_garand': 'gun', 'mosin': 'gun',
    'crossbow': 'gun', 'crossbow_geo': 'gun',
    'compound_bow': 'bow',
    'flashbang': 'throwable', 'mud': 'throwable',
}
KIND_CN = {'gun': '枪', 'bow': '弓', 'throwable': '投'}
LEN_RANGE = {'gun': (0.9, 2.6), 'bow': (1.0, 2.2), 'throwable': (0.2, 0.9)}
NEED_BONES = ('root', 'move', 'body')

# 动画文件别名：模型名 → 动画文件基名；None = 姿态由 Java 程序化驱动，不需要动画文件。
# （crossbow_geo 这个体素模型共用 crossbow.animation.json；kar98k 全靠 GeoModel 每帧算）
ANIM_OF = {'crossbow_geo': 'crossbow', 'kar98k': None}

# 死资源不在这里登记（2026-09-21 那批已用 tools/dead_assets.py 清完）。
# 「还有哪个文件没人引用」请跑 `python tools/dead_assets.py`（引用闭包扫描）。
# 保留这个空表是为了以后临时豁免某个已知死文件（体检不报它）。
LEGACY = {}

# 体素化模型（crossbow_vox.py 按 --step 0.45 生成）方块数天然多，用另一条上限
VOXEL_MAX_CUBES = 1400


def tex_paths(name):
    """贴图名：`<名>_geo.png`（现行）；名字已以 `_geo` 结尾（如 crossbow_geo）则直接用 `<名>.png`。"""
    if name.endswith('_geo'):
        return [os.path.join(TEX, name + '.png')]
    return [os.path.join(TEX, name + '_geo.png'), os.path.join(TEX, name + '.png')]


class Audit(object):
    def __init__(self):
        self.problems = []      # (等级, 类别, 模型, 说明)
        self.rows = []

    def add(self, level, cat, model, msg):
        self.problems.append((level, cat, model, msg))

    # ------------------------------------------------------------------ 单模型
    def check(self, path, name):
        if name in LEGACY:
            self.add('提示', '存量', name, LEGACY[name])
            return
        raw = json.load(open(path, encoding='utf-8'))
        geo = raw['minecraft:geometry'][0]
        desc = geo['description']
        tw, th = int(desc.get('texture_width', 0)), int(desc.get('texture_height', 0))
        bones = geo['bones']
        kind = KIND.get(name, 'gun')

        # ---- C 命名 / 层级
        bnames = [b['name'] for b in bones]
        for n in sorted({n for n in bnames if bnames.count(n) > 1}):
            self.add('错误', '命名', name, '骨骼名重复：%s' % n)
        for b in bones:
            n = b['name']
            if not NAME_RE.match(n):
                self.add('错误', '命名', name, '骨骼名不合规范（^[a-z][a-z0-9_]*$）：%s' % n)
            if b.get('parent') and b['parent'] not in bnames:
                self.add('错误', '命名', name, '骨骼 %s 的父骨 %s 不存在' % (n, b['parent']))
            rot = b.get('rotation')
            if rot and any(abs(float(v)) > 0.001 for v in rot):
                self.add('错误', '朝向', name, '骨骼 %s 带旋转 %s —— 朝向要烘进几何，不能挂骨骼上' % (n, rot))
        for n in NEED_BONES:
            if n not in bnames:
                self.add('错误', '命名', name, '缺必需骨骼 %s' % n)

        # ---- F 几何 / B UV
        lo, hi = [1e9] * 3, [-1e9] * 3
        cubes, rects, single = 0, [], 0
        for b in bones:
            bone_cubes = b.get('cubes') or []
            for c in bone_cubes:
                cubes += 1
                o = [float(v) for v in c['origin']]
                s = [float(v) for v in c['size']]
                if min(s) <= 0:
                    self.add('警告', '负尺寸', name, '%s 的方块 origin=%s size=%s（生成器要 min/max 归一化）'
                             % (n, o, s))
                blo = [min(o[i], o[i] + s[i]) for i in range(3)]
                bhi = [max(o[i], o[i] + s[i]) for i in range(3)]
                for i in range(3):
                    lo[i], hi[i] = min(lo[i], blo[i]), max(hi[i], bhi[i])
                uv = c.get('uv')
                if not isinstance(uv, dict):
                    self.add('警告', 'UV', name, '%s 的方块没有逐面 uv（旧版写法）' % n)
                    continue
                got = [f for f in FACES if f in uv]
                if len(got) != 6:
                    self.add('错误', 'UV', name, '%s 的方块缺面 %s' % (n, [f for f in FACES if f not in uv]))
                same = len({(float(uv[f]['uv'][0]), float(uv[f]['uv'][1]),
                             float(uv[f]['uv_size'][0]), float(uv[f]['uv_size'][1])) for f in got}) == 1
                single += 1 if same else 0
                for f in got:
                    x, y = float(uv[f]['uv'][0]), float(uv[f]['uv'][1])
                    w, h = float(uv[f]['uv_size'][0]), float(uv[f]['uv_size'][1])
                    if w <= 0 or h <= 0:
                        self.add('错误', 'UV', name, '%s/%s 的 uv_size 非法 %s' % (n, f, uv[f]['uv_size']))
                    rects.append((x, y, w, h, '%s/%s' % (n, f)))
            if b['name'] not in CONTROLLER_BONES and bone_cubes:
                p = [float(v) for v in b.get('pivot', [0, 0, 0])]
                blo = [min(float(c['origin'][i]) for c in bone_cubes) for i in range(3)]
                bhi = [max(float(c['origin'][i]) + float(c['size'][i]) for c in bone_cubes) for i in range(3)]
                d = sum((p[i] - max(blo[i], min(bhi[i], p[i]))) ** 2 for i in range(3)) ** 0.5
                if d > PIVOT_FAR:
                    self.add('错误', 'pivot', name, '骨骼 %s 的 pivot %s 离自己几何 %.2fu（>%.1fu，轴心八成写错）'
                             % (b['name'], p, d, PIVOT_FAR))
        if cubes == 0:
            self.add('错误', '几何', name, '一个方块都没有')
        # UV 模式（逐面图集 / 单块体素）：体素模型的 UV 是按世界位置采样连续贴图，允许重叠与越界
        voxel = cubes > 0 and single >= cubes * 0.6
        cap = VOXEL_MAX_CUBES if voxel else MAX_CUBES
        if cubes > cap:
            self.add('警告', '规模', name, '方块 %d 个 > %d' % (cubes, cap))
        if len(bones) > MAX_BONES:
            self.add('警告', '规模', name, '骨骼 %d 根 > %d' % (len(bones), MAX_BONES))

        # ---- UV 模式（逐面图集 / 单块体素）：体素模型的 UV 是按世界位置采样连续贴图，允许重叠与越界
        if not voxel:
            out = [r for r in rects if r[0] < 0 or r[1] < 0 or r[0] + r[2] > tw or r[1] + r[3] > th]
            for r in out[:6]:
                self.add('错误', 'UV', name, '%s 的 UV 越界 (%.1f,%.1f,%.1f,%.1f) 图集 %dx%d' % (r[4], r[0], r[1], r[2], r[3], tw, th))
            if len(out) > 6:
                self.add('错误', 'UV', name, '……另有 %d 个面 UV 越界（见 build 报告）' % (len(out) - 6))
            rects.sort(key=lambda r: r[0])
            hits = set()
            for i, a in enumerate(rects):
                for b2 in rects[i + 1:]:
                    if b2[0] >= a[0] + a[2]:
                        break
                    if a[1] < b2[1] + b2[3] and b2[1] < a[1] + a[3] and a[4].split('/')[0] != b2[4].split('/')[0]:
                        hits.add('%s|%s' % (a[4], b2[4]))
            if hits:
                self.add('警告', 'UV', name, '有 %d 对面重叠（逐面图集不该重叠，见 build 报告）' % len(hits))
        else:
            neg = [r for r in rects if r[0] < 0 or r[1] < 0]
            if neg:
                self.add('提示', 'UV', name, '体素 UV 有负值 %d 处（GeckoLib 会夹取边缘像素，观感还行但不规范）' % len(neg))
            self.add('提示', 'UV', name, 'UV 模式=单块/体素（%d/%d 个方块六面同矩形），跳过重叠与越界检查' % (single, cubes))

        # ---- A 单位 / 朝向
        size = [hi[i] - lo[i] for i in range(3)]
        axis = 'XYZ'[size.index(max(size))]
        length_blk = max(size) / U_PER_BLOCK
        if kind == 'gun' and axis != 'Z':
            self.add('错误', '朝向', name, '最长轴是 %s %s —— 枪械长轴必须是 Z（前向 −Z）' % (axis, [round(v, 2) for v in size]))
        w = LEN_RANGE[kind]
        if not (w[0] <= length_blk <= w[1]):
            self.add('警告', '单位', name, '最长轴 %.2f 格，超出 %s 类目建议区间 %.1f~%.1f 格'
                     % (length_blk, KIND_CN[kind], w[0], w[1]))

        # ---- E 抛壳（+X = 射手右侧）
        for b in bones:
            if b['name'] == 'casing' and b.get('cubes'):
                cx = sum(float(c['origin'][0]) + float(c['size'][0]) / 2.0 for c in b['cubes']) / len(b['cubes'])
                if cx <= 0:
                    self.add('错误', '抛壳', name, 'casing 几何中心 x=%.2f ≤ 0 —— 弹壳必须在 +X（射手右侧）' % cx)

        # ---- B/G 贴图与交付物
        tex = next((p for p in tex_paths(name) if os.path.exists(p)), None)
        tex_px = None
        if not tex:
            self.add('错误', '贴图', name, '缺贴图：%s' % ' 或 '.join(os.path.relpath(p, ROOT) for p in tex_paths(name)))
        else:
            try:
                from PIL import Image
                with Image.open(tex) as im:
                    tex_px = im.size
            except Exception as e:                                  # pragma: no cover
                self.add('警告', '贴图', name, '贴图读不出来：%s' % e)
            else:
                if tex_px != (tw, th):
                    self.add('警告', '贴图', name, '贴图实际 %dx%d ≠ geo 声明 %dx%d（UV 是按声明算的，内容要落在左上 %d² 内）'
                             % (tex_px[0], tex_px[1], tw, th, tw))
                if (tw, th) != (TEX_WANT, TEX_WANT):
                    self.add('警告', '贴图', name, 'geo 声明 %dx%d，规范是 %dx%d' % (tw, th, TEX_WANT, TEX_WANT))
        if not (tex and os.path.exists(tex[:-4] + '_glowmask.png')):
            stem = name if name.endswith('_geo') else name + '_geo'
            self.add('提示', '交付', name, '%s_glowmask.png 不存在（不需要自发光可忽略）' % stem)
        anim = ANIM_OF.get(name, name)
        if anim is not None and not os.path.exists(os.path.join(ANIM, anim + '.animation.json')):
            self.add('警告', '交付', name, '缺 animations/%s.animation.json' % anim)

        self.rows.append(dict(name=name, kind=kind, bones=len(bones), cubes=cubes, size=size,
                              length=length_blk, axis=axis, tw=tw, th=th, tex=tex_px, voxel=voxel,
                              mode=('体素' if cubes > 400 else '单块 UV') if voxel else '逐面图集'))

    # ------------------------------------------------------------------ 输出
    def report(self, verbose):
        cnt = {'错误': 0, '警告': 0, '提示': 0}
        for lv, _, _, _ in self.problems:
            cnt[lv] += 1
        out = []
        out.append('美术规范体检（《美术规范.md》第七节）—— 模型 %d 个' % len(self.rows))
        out.append('=' * 104)
        out.append('%-14s %-3s %4s %5s %21s %7s %7s %-11s %s' %
                   ('模型', '类', '骨', '方块', '包围盒 x,y,z', '长(格)', '长轴', '贴图', 'UV 模式'))
        for r in sorted(self.rows, key=lambda r: r['name']):
            out.append('%-14s %-3s %4d %5d %21s %7.2f %7s %-11s %s' %
                       (r['name'], KIND_CN[r['kind']], r['bones'], r['cubes'],
                        ','.join('%.2f' % v for v in r['size']), r['length'], r['axis'],
                        '%dx%d' % r['tex'] if r['tex'] else '缺失', r['mode']))
        out.append('')
        # 摘要：同类问题按 (等级, 模型, 类别) 合并成一行
        for lv in ('错误', '警告', '提示'):
            items = [p for p in self.problems if p[0] == lv]
            if not items:
                continue
            out.append('---- %s %d 条 ----' % (lv, len(items)))
            grp = {}
            for _, cat, m, msg in items:
                grp.setdefault((m, cat), []).append(msg)
            for (m, cat), msgs in sorted(grp.items()):
                out.append('  [%s] %s ×%d：%s' % (m, cat, len(msgs), msgs[0] if len(msgs) == 1
                                                  else msgs[0] + ' …'))
                if verbose:
                    for extra in msgs[1:]:
                        out.append('        · %s' % extra)
            out.append('')
        out.append('汇总：错误 %d / 警告 %d / 提示 %d' % (cnt['错误'], cnt['警告'], cnt['提示']))
        out.append('结果：' + ('✓ 无错误' if not cnt['错误'] else '✗ 有 %d 条错误要修' % cnt['错误']))
        text = '\n'.join(out)

        detail = ['', '=' * 104, '全部明细（含上面折叠掉的每一条）', '=' * 104]
        for lv, cat, m, msg in self.problems:
            detail.append('[%s][%s][%s] %s' % (lv, m, cat, msg))
        with open(REPORT, 'w', encoding='utf-8') as f:
            f.write(text + '\n' + '\n'.join(detail) + '\n')

        print(text if not verbose else text + '\n' + '\n'.join(detail))
        print('\n完整报告 -> %s' % os.path.relpath(REPORT, ROOT))
        return 1 if cnt['错误'] else 0


def main(argv):
    verbose = any(a in ('-v', '--verbose') for a in argv)
    only = [a for a in argv if not a.startswith('-')]
    if not os.path.isdir(GEO):
        print('找不到 geo 目录：%s' % GEO)
        return 2
    files = sorted(f for f in os.listdir(GEO) if f.endswith('.geo.json'))
    if only:
        files = [f for f in files if f[:-len('.geo.json')] in only]
    if not files:
        print('没有匹配的模型')
        return 2
    aud = Audit()
    for f in files:
        aud.check(os.path.join(GEO, f), f[:-len('.geo.json')])
    return aud.report(verbose)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
