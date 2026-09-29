#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""死资源扫描 —— 找出 `assets/hexalunar_calamity/**` 里**引用闭包之外**的文件（只读，不删东西）。

为什么不能只看「字符串出现次数」：`models/item/crossbow_pulling_0.json` 自己引用 `.obj`、
旧 `crossbow.json`（现在是备份 `.dispbak`）又引用 pulling 模型 —— 单独看都"有引用"，
其实**整簇**都已经没人用了。所以这里做的是**可达性分析**：

    根（消费者）：`src/main/java/**/*.java` 全部
    传递：任何「活着的文本文件」里以路径/文件名提到过的资源也算活
    约定：靠命名加载、Java 里搜不到路径的，按**裸名字**判定（只在 java 语料里找）：
          · `models/item/<注册名>.json`   ← 物品注册名
          · `textures/item|gui|mob_effect/<名>.png` ← 物品模型 / 效果图标
          · `sounds/**/<名>.ogg`          ← 音效 id
          · `textures/models/<基名>_glowmask.png` ← `GlossGlintLayer` 按「基名 + _glowmask.png」现拼的
      ⚠️ `.obj` / `.mtl` **不做**裸名判定（它们只能被 JSON 显式点名），否则「同名的物品还在」会误判成活的。
    引擎约定文件（`lang/*.json`、`atlases/**`、`pack.mcmeta`）恒为活。

用法::

    python tools/dead_assets.py            # 扫描（报告写 build/dead_assets.txt）
    python tools/dead_assets.py -v         # 连「谁引用了它」一起打出来
"""
import os
import re
import sys
from collections import defaultdict, deque

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # mod/
SRC = os.path.join(ROOT, 'src', 'main')
ASSETS = os.path.join(SRC, 'resources', 'assets', 'hexalunar_calamity')
NS = 'hexalunar_calamity'
REPORT = os.path.join(ROOT, 'build', 'dead_assets.txt')

TEXT_EXT = {'.json', '.mcmeta', '.txt', '.xml', '.properties', '.lang', '.obj', '.mtl', '.toml'}
SKIP_DIRS = {'__pycache__'}
NO_WEAK = {'.obj', '.mtl'}                          # 这类只能被显式点名
JUNK_SUFFIX = ('.unit16bak', '.dispbak', '.bak', '.rotbak', '.orig', '.tmp')
ENGINE_FILES = {'atlases/blocks.json', 'lang/zh_cn.json', 'lang/en_us.json', 'pack.mcmeta',
                'sounds.json', 'sounds/sounds.json'}


def rel_assets(p):
    return os.path.relpath(p, ASSETS).replace('\\', '/')


def strip_comments(t):
    """剥掉 Java 注释：注释里提到文件名不算引用（ModClient 的注释提过 crossbow.json，
    会把它的 .dispbak 备份判成活的）。只跳过 http:// 这种假 //。"""
    t = re.sub(r'/\*.*?\*/', ' ', t, flags=re.S)
    return re.sub(r'(?<!:)//[^\n]*', ' ', t)


def load_chunks():
    """{(根名, 绝对路径): 文本}；根名 java / res 决定它是不是「消费者根」。"""
    chunks = {}
    for kind, base, exts in (('java', os.path.join(ROOT, 'src', 'main', 'java'), {'.java'}),
                             ('res', os.path.join(SRC, 'resources'), TEXT_EXT),
                             ('q', os.path.join(ROOT, 'src', 'qresources'), TEXT_EXT)):
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() not in exts:
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    t = open(p, encoding='utf-8', errors='replace').read()
                except OSError:
                    continue
                chunks[(kind, p)] = strip_comments(t) if kind == 'java' else t
    return chunks


def strong_patterns(rel):
    """路径级引用串（出现即算被引用）。"""
    parts = rel.split('/')
    name = parts[-1]
    stem = name[:name.rindex('.')] if '.' in name else name
    rel_stem = rel[:rel.rindex('.')] if '.' in rel else rel
    pats = {rel, rel_stem, name}
    if len(parts) > 1:                              # 去掉第一段目录：Java 写 textures/...，物品 JSON 写 item/...
        sub = '/'.join(parts[1:])
        pats.add(sub)
        if '.' in sub:
            pats.add(sub[:sub.rindex('.')])
    if parts[0] == 'models' and len(parts) > 2:     # models/item/x.json → item/x
        pats.add('/'.join(parts[1:-1] + [stem]))
    if rel.endswith('.geo.json'):                   # GeckoLib 只写骨架名，后缀由加载器补
        pats.add('geo/' + name[:-len('.geo.json')])
    if rel.endswith('.animation.json'):
        pats.add('animations/' + name[:-len('.animation.json')])
    return sorted(p for p in pats if p)


def weak_stem(rel):
    """裸名字（命名约定加载）。.obj/.mtl 不做。"""
    name = rel.split('/')[-1]
    if os.path.splitext(name)[1].lower() in NO_WEAK:
        return None
    if rel.endswith('_glowmask.png'):               # 由基名 + _glowmask.png 现拼，裸名也不会出现
        return None
    return name[:name.rindex('.')] if '.' in name else name


def main(argv):
    verbose = any(a in ('-v', '--verbose') for a in argv)
    chunks = load_chunks()

    cands = []
    for dirpath, dirnames, filenames in os.walk(ASSETS):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            cands.append(rel_assets(p))
    cands = sorted(cands)

    pat2cands = defaultdict(set)
    for rel in cands:
        for pat in strong_patterns(rel):
            pat2cands[pat].add(rel)
    big = re.compile(r'(?<![\w.-])(?:%s)(?![\w.-])' % '|'.join(
        re.escape(p) for p in sorted(pat2cands, key=len, reverse=True)))

    def hits(text):
        return {c for m in big.finditer(text) for c in pat2cands.get(m.group(0), ())}

    # ---- 根：全部 java（+ 引擎约定文件）
    alive = {r for r in ENGINE_FILES if r in cands}
    why = {r: '引擎按固定位置读取' for r in alive}
    queue = deque()
    java_text = '\n'.join(t for (k, _), t in chunks.items() if k == 'java')
    for rel in cands:
        if rel in alive:
            continue
        w = weak_stem(rel)
        if w and re.search(r'(?<![\w.-])' + re.escape(w) + r'(?![\w.-])', java_text):
            alive.add(rel)
            why[rel] = 'Java 里按裸名引用（%s）' % w
    for (kind, p), t in chunks.items():
        if kind == 'java':
            queue.append(p)
            for rel in hits(t) - alive:
                alive.add(rel)
                why[rel] = 'Java: %s' % os.path.basename(p)
    # ---- 贴图基名 + _glowmask.png 的约定（GlossGlintLayer）
    if '_glowmask' in java_text:
        for rel in cands:
            if rel.endswith('_glowmask.png') and rel not in alive:
                base = rel[:-len('_glowmask.png')] + '.png'
                if base in alive:
                    alive.add(rel)
                    why[rel] = '基名贴图活着 + GlossGlintLayer 现拼 _glowmask.png'

    # ---- 传递闭包：活着的资源文件里提到的资源也算活（弱引用判活的文件同样要展开）
    rel_to_chunk = {rel_assets(p): (kind, p) for kind, p in chunks
                    if os.path.commonprefix([os.path.abspath(p), ASSETS]) == ASSETS}
    for rel in list(alive):
        if rel in rel_to_chunk:
            queue.append(rel_to_chunk[rel][1])
    while queue:
        p = queue.popleft()
        text = chunks.get(('res', p)) or chunks.get(('q', p)) or chunks.get(('java', p))
        if text is None:
            continue
        for rel in hits(text) - alive:
            alive.add(rel)
            why[rel] = '被 %s 引用' % rel_assets(p)
            if rel in rel_to_chunk:
                queue.append(rel_to_chunk[rel][1])

    dead = [r for r in cands if r not in alive]
    junk = [r for r in dead if r.endswith(JUNK_SUFFIX)]

    out = ['死资源扫描（引用闭包）—— assets/%s 共 %d 个文件' % (NS, len(cands))]
    out.append('  活着 %d ／ **死资源 %d**（其中备份垃圾 %d）' % (len(alive), len(dead), len(junk)))
    out.append('=' * 100)
    out.append('---- 死资源（可以删）----')
    for rel in dead:
        tag = '  [备份垃圾]' if rel.endswith(JUNK_SUFFIX) else ''
        out.append('  %-52s%s' % (rel, tag))
    if not dead:
        out.append('  （没有）')
    if verbose:
        out.append('')
        out.append('---- 活着的原因（抽样）----')
        for rel in cands:
            if rel in alive:
                out.append('  %-52s %s' % (rel, why.get(rel, '')))
    text = '\n'.join(out)
    print(text)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write(text + '\n')
    print('\n报告 -> %s' % os.path.relpath(REPORT, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
