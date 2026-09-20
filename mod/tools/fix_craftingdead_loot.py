# -*- coding: utf-8 -*-
import json, io, os, re, zipfile
MODS = r'C:\Users\Administrator\Desktop\.minecraft\versions\1.20.1-Forge_47.4.23-2\mods'
WORLD = r'C:\Users\Administrator\Desktop\.minecraft\versions\1.20.1-Forge_47.4.23-2\saves\新的世界'
DP = os.path.join(WORLD, 'datapacks', 'hcd_loot_fix')
TABLES = ['civilian_loot.json', 'civilian_rare_loot.json', 'medic_loot.json', 'military_loot.json', 'police_loot.json']
FIX = {
    'craftingdead:splint': 'craftingdeadsurvival:splint',
    'craftingdead:cure_syringe': 'craftingdeadsurvival:cure_syringe',
    'craftingdead:rbi_syringe': 'craftingdeadsurvival:rbi_syringe',
    'craftingdead:red_dot_sight': 'hexalunar_calamity:red_dot_sight',
    'craftingdead:magnum_magazine': 'craftingdead:magnum_ammunition',
    'craftingdead:m1garand_magazine': 'craftingdead:m1garand_ammunition',
}
DROP = {'craftingdead:trenchgun', 'craftingdead:trenchgun_shells', 'craftingdead:pipe_grenade',
        'craftingdead:scarh', 'craftingdead:broad_sword', 'craftingdead:multi_paint'}
src = None
for root, dirs, files in os.walk(os.environ.get('LOCALAPPDATA', '') + r'\Temp'):
    if root.endswith(os.path.join('lootfix', 'data', 'hcdservercore', 'loot_tables', 'blocks')):
        src = root; break
assert src
paths, tags = set(), set()
for j in os.listdir(MODS):
    if not j.lower().endswith('.jar'):
        continue
    with zipfile.ZipFile(os.path.join(MODS, j)) as z:
        for n in z.namelist():
            low = n.lower()
            if not low.endswith('.json'):
                continue
            t = z.read(n).decode('utf-8', 'replace')
            if '/lang/' in low:
                # 物品与"配件"两套命名都要收（CD 的配件用 attachment. 前缀）
                for m in re.finditer(r'"(?:item|attachment|block)\.[a-z0-9_]+\.([a-z0-9_]+)"', t):
                    paths.add(m.group(1))
            if low.startswith('data/') and '/tags/' in low:
                for m in re.finditer(r'"([a-z0-9_]+:[a-z0-9_/]+)"', t):
                    tags.add(m.group(1))
outdir = os.path.join(DP, 'data', 'hcdservercore', 'loot_tables', 'blocks')
os.makedirs(outdir, exist_ok=True)
tf = td = 0
for f in TABLES:
    d = json.load(io.open(os.path.join(src, f), encoding='utf-8'))
    pools, fixed, dropped = [], [], []
    for pool in d.get('pools', []):
        kept = []
        for e in pool.get('entries', []):
            nm = e.get('name', '')
            if nm in FIX:
                e = dict(e); e['name'] = FIX[nm]; fixed.append('%s→%s' % (nm, FIX[nm])); kept.append(e); continue
            if e.get('type') == 'minecraft:tag':
                if nm.startswith('minecraft:') or nm in tags: kept.append(e)
                else: dropped.append(nm)
                continue
            if nm.startswith('minecraft:') or (nm.split(':', 1)[1] in paths and nm not in DROP):
                kept.append(e)
            else:
                dropped.append(nm)
        if kept:
            p = dict(pool); p['entries'] = kept; pools.append(p)
    d['pools'] = pools
    with io.open(os.path.join(outdir, f), 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)
    json.load(io.open(os.path.join(outdir, f), encoding='utf-8'))
    tf += len(fixed); td += len(dropped)
    print('%-24s 改名 %d | 剔除 %d %s' % (f, len(fixed), len(dropped), sorted(set(dropped))))
with io.open(os.path.join(DP, 'pack.mcmeta'), 'w', encoding='utf-8') as fh:
    json.dump({'pack': {'pack_format': 15, 'description': 'Crafting Dead Loot 战利品表修复'}}, fh, ensure_ascii=False, indent=2)
print('完成：改名 %d / 剔除 %d' % (tf, td))
