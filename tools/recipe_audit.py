#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配方静态体检（纯标准库）。

检查内容：
  1. 配方 JSON 合法性、type 是否为 1.20.1 支持的类型
  2. 引用的物品/标签是否存在（模组物品从 ModItems.java 解析，原版物品从客户端 jar 的 en_us.json 解析）
  3. 有序合成 pattern 自检：每行等长、字符与 key 一一对应、result 数量合法
  4. 配方冲突：同一输出 + 同材料布局的重复配方（游戏里会报 "Recipe conflict / duplicate"）
  5. 无法获取的物品：有注册但既无配方产出、也无掉落/其他获取途径（提示，不报错）

用法：
  python tools/recipe_audit.py
  python tools/recipe_audit.py --jar <客户端 jar 路径>
"""
import argparse
import json
import os
import re
import sys
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOD_NAME = "hexalunar_calamity"
SRC = os.path.join(ROOT, "mod", "src", "main")
RECIPE_DIR = os.path.join(SRC, "resources", "data", MOD_NAME, "recipes")
JAVA_DIR = os.path.join(SRC, "java")

# 原版资源/数据都在 *-extra.jar（srg.jar 只有 class，没有 assets/data）
DEFAULT_JAR = (
    r"C:\Users\Administrator\Desktop\.minecraft\libraries\net\minecraft\client"
    r"\1.20.1-20230612.114412\client-1.20.1-20230612.114412-extra.jar"
)

KNOWN_TYPES = {
    "minecraft:crafting_shaped",
    "minecraft:crafting_shapeless",
    "minecraft:crafting_special_armordye",
    "minecraft:crafting_special_bannerduplicate",
    "minecraft:crafting_special_bookcloning",
    "minecraft:crafting_special_firework_rocket",
    "minecraft:crafting_special_firework_star",
    "minecraft:crafting_special_firework_star_fade",
    "minecraft:crafting_special_mapcloning",
    "minecraft:crafting_special_mapextending",
    "minecraft:crafting_special_repairitem",
    "minecraft:crafting_special_shielddecoration",
    "minecraft:crafting_special_shulkerboxcoloring",
    "minecraft:crafting_special_suspiciousstew",
    "minecraft:crafting_special_tippedarrow",
    "minecraft:smelting",
    "minecraft:blasting",
    "minecraft:smoking",
    "minecraft:campfire_cooking",
    "minecraft:stonecutting",
    "minecraft:smithing_transform",
    "minecraft:smithing_trim",
}

problems = []
notes = []


def problem(msg):
    problems.append(msg)


def note(msg):
    notes.append(msg)


def mod_items():
    """从 ModItems.java 里抓 ITEMS.register("xxx", ...) 的物品名 → 返回 (id, 常量名的映射)。"""
    path = os.path.join(
        JAVA_DIR, "cn", "blockforge", "generated", "hexalunarcalamity", "registry", "ModItems.java"
    )
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # 形如： public static final RegistryObject<Item> CROSSBOW = ITEMS.register("crossbow", ...
    pairs = re.findall(
        r'\b([A-Z][A-Z0-9_]*)\s*=\s*\n?\s*ITEMS\.register\("([a-z0-9_]+)"', text
    )
    names = {i for _c, i in pairs} or set(re.findall(r'ITEMS\.register\("([a-z0-9_]+)"', text))
    if not names:
        problem("ModItems.java 里没解析到任何物品注册")
    return names, {i: c for c, i in pairs}


def vanilla_items(jar):
    """从客户端 jar 的语言/数据文件里解析原版物品 id、物品标签、战利品表 id。"""
    if not jar or not os.path.isfile(jar):
        note("未找到客户端 jar，跳过原版物品/标签/战利品表校验（可用 --jar 指定）")
        return None, None, None
    with zipfile.ZipFile(jar) as z:
        lang = json.loads(z.read("assets/minecraft/lang/en_us.json").decode("utf-8"))
        items = {k[len("item.minecraft."):] for k in lang if k.startswith("item.minecraft.")}
        tags = set()
        tables = set()
        for entry in z.namelist():
            m = re.fullmatch(r"data/minecraft/tags/items/(.+)\.json", entry)
            if m:
                tags.add("minecraft:" + m.group(1))
            m = re.fullmatch(r"data/minecraft/loot_tables/(.+)\.json", entry)
            if m:
                tables.add("minecraft:" + m.group(1))
    return items, tags, tables


def refs_of(value, out):
    """递归收集配方里的 {"item": ...} / {"tag": ...} 引用。"""
    if isinstance(value, dict):
        if "item" in value and isinstance(value["item"], str):
            out.add(value["item"])
        if "tag" in value and isinstance(value["tag"], str):
            out.add(value["tag"])
        for v in value.values():
            refs_of(v, out)
    elif isinstance(value, list):
        for v in value:
            refs_of(v, out)


def shape_signature(recipe):
    """把配方归一化成“材料布局签名”，用于查重。"""
    if recipe.get("type") == "minecraft:crafting_shaped":
        key = recipe.get("key", {})
        rows = recipe.get("pattern", [])
        cells = tuple(
            tuple(
                json.dumps(key.get(ch, {}), sort_keys=True, ensure_ascii=False)
                for ch in row
            )
            for row in rows
        )
        return ("shaped", cells, recipe.get("result", {}).get("item"))
    if recipe.get("type") == "minecraft:crafting_shapeless":
        ing = sorted(
            json.dumps(i, sort_keys=True, ensure_ascii=False) for i in recipe.get("ingredients", [])
        )
        return ("shapeless", tuple(ing), recipe.get("result", {}).get("item"))
    return None


def check_recipe(name, recipe, mods, van, tags):
    path = f"recipes/{name}.json"
    rtype = recipe.get("type")
    if rtype is None:
        problem(f"{path}: 缺 type 字段")
        return
    if rtype not in KNOWN_TYPES:
        problem(f"{path}: 未知配方类型 {rtype}")

    result = recipe.get("result")
    if not isinstance(result, dict) or "item" not in result:
        problem(f"{path}: result 缺 item")
        return
    count = result.get("count", 1)
    if not isinstance(count, int) or not 1 <= count <= 64:
        problem(f"{path}: result.count={count} 不合法")

    refs = set()
    refs_of(recipe, refs)
    for ref in sorted(refs):
        if ref.startswith(MOD_NAME + ":"):
            short = ref.split(":", 1)[1]
            if short not in mods:
                problem(f"{path}: 引用了未注册的模组物品 {ref}")
        elif ref.startswith("minecraft:"):
            short = ref.split(":", 1)[1]
            if van is None:
                continue
            if rtype in ("minecraft:crafting_shaped", "minecraft:crafting_shapeless") and short not in van:
                # 可能是物品标签
                if ("minecraft:" + short) not in tags:
                    problem(f"{path}: 未知原版物品/标签 {ref}")
        else:
            problem(f"{path}: 引用缺少命名空间的 id {ref}")

    if rtype == "minecraft:crafting_shaped":
        pattern = recipe.get("pattern", [])
        key = recipe.get("key", {})
        if not pattern:
            problem(f"{path}: 缺 pattern")
            return
        width = len(pattern[0])
        if width != 3:
            note(f"{path}: 每行 {width} 格（原版配方通常是 3，2 格只在 2x2 配方里合法）")
        for i, row in enumerate(pattern):
            if len(row) != width:
                problem(f"{path}: pattern 第 {i + 1} 行长度 {len(row)} != {width}")
        used = {ch for row in pattern for ch in row if ch != " "}
        for ch in used:
            if ch not in key:
                problem(f"{path}: pattern 用到字符 '{ch}' 但 key 里没定义")
        for ch in key:
            if ch not in used:
                problem(f"{path}: key 定义了 '{ch}' 但 pattern 里没用（游戏会忽略，属冗余）")
    elif rtype == "minecraft:crafting_shapeless":
        ings = recipe.get("ingredients", [])
        if not 1 <= len(ings) <= 9:
            problem(f"{path}: ingredients 数量 {len(ings)} 不合法")


def loot_modifier_items():
    """战利品修饰器里能开出的模组物品名（算作“可获得”）。"""
    out = set()
    lm_dir = os.path.join(SRC, "resources", "data", MOD_NAME, "loot_modifiers")
    if not os.path.isdir(lm_dir):
        return out
    for fn in os.listdir(lm_dir):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(lm_dir, fn), encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            continue
        for entry in data.get("settings", {}).get("entries", []):
            ref = entry.get("weapon", "")
            if ref.startswith(MOD_NAME + ":"):
                out.add(ref.split(":", 1)[1])
    return out


def check_loot_modifiers(mods, tables):
    """校验 data/<mod>/loot_modifiers/*.json：是否被启用、战利品表 id 与物品 id 是否真实存在。"""
    lm_dir = os.path.join(SRC, "resources", "data", MOD_NAME, "loot_modifiers")
    if not os.path.isdir(lm_dir):
        return 0
    enabled = set()
    global_json = os.path.join(SRC, "resources", "data", "forge", "loot_modifiers",
                               "global_loot_modifiers.json")
    if os.path.isfile(global_json):
        with open(global_json, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("replace"):
            problem("data/forge/loot_modifiers/global_loot_modifiers.json 的 replace=true 会盖掉其它模组的同类文件")
        enabled = {e.split(":", 1)[-1] for e in data.get("entries", [])}
    else:
        problem("缺少 data/forge/loot_modifiers/global_loot_modifiers.json，战利品修饰器不会生效")

    count = 0
    for fn in sorted(os.listdir(lm_dir)):
        if not fn.endswith(".json"):
            continue
        count += 1
        name = fn[:-5]
        try:
            with open(os.path.join(lm_dir, fn), encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            problem(f"loot_modifiers/{fn}: JSON 语法错误 -> {e}")
            continue
        if not data.get("type", "").endswith(":weapon_cache"):
            problem(f"loot_modifiers/{fn}: type={data.get('type')} 不是本模组的 weapon_cache")
        if name not in enabled:
            problem(f"loot_modifiers/{fn} 没有列进 global_loot_modifiers.json 的 entries")
        settings = data.get("settings", {})
        if not settings.get("entries"):
            problem(f"loot_modifiers/{fn}: settings.entries 为空")
        elif sum(max(0, e.get("weight", 1)) for e in settings["entries"]) <= 0:
            problem(f"loot_modifiers/{fn}: 所有条目 weight 都是 0，永远抽不出东西")
        total = sum(max(0, e.get("weight", 1)) for e in settings.get("entries", []))
        for entry in settings.get("entries", []):
            for key in ("weapon", "ammo"):
                ref = entry.get(key)
                if not ref:
                    continue
                ns, _, short = ref.partition(":")
                if ns == MOD_NAME and short not in mods:
                    problem(f"loot_modifiers/{fn}: 引用了未注册的模组物品 {ref}")
            if entry.get("ammo") and not entry.get("ammo_count"):
                note(f"loot_modifiers/{fn}: {entry.get('weapon')} 配了 ammo 但 ammo_count=0，不会发弹药")
        for table in settings.get("tables", []):
            if tables is not None and table not in tables:
                problem(f"loot_modifiers/{fn}: 未知战利品表 {table}")
        if total:
            note(f"loot_modifiers/{name}: chance={settings.get('chance')}，作用 {len(settings.get('tables', []))} 个箱子表")
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", default=DEFAULT_JAR)
    args = ap.parse_args()

    if not os.path.isdir(RECIPE_DIR):
        print(f"找不到配方目录 {RECIPE_DIR}")
        return 1

    mods, const_of = mod_items()
    van, tags, tables = vanilla_items(args.jar)

    recipes = {}
    for fn in sorted(os.listdir(RECIPE_DIR)):
        if not fn.endswith(".json"):
            continue
        name = fn[:-5]
        full = os.path.join(RECIPE_DIR, fn)
        try:
            with open(full, encoding="utf-8") as f:
                recipes[name] = json.load(f)
        except json.JSONDecodeError as e:
            problem(f"recipes/{fn}: JSON 语法错误 -> {e}")
    if not recipes:
        problem("没有任何配方文件")

    for name, recipe in recipes.items():
        check_recipe(name, recipe, mods, van, tags)

    # 配方查重（同输出 + 同布局）
    by_sig = defaultdict(list)
    for name, recipe in recipes.items():
        sig = shape_signature(recipe)
        if sig:
            by_sig[sig].append(name)
    for sig, names in by_sig.items():
        if len(names) > 1:
            problem(f"配方冲突（材料布局完全相同）: {', '.join(sorted(names))}")

    # 产出覆盖面：哪些模组物品没有配方产出（可能靠掉落/战利品/创造模式）
    produced = {r.get("result", {}).get("item", "").split(":", 1)[-1] for r in recipes.values()}
    produced |= loot_modifier_items()
    blob_other = ""
    for dirpath, _dirs, files in os.walk(JAVA_DIR):
        for fn in files:
            if fn.endswith(".java") and fn not in ("ModItems.java", "ModTabs.java"):
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    blob_other += f.read()
    for item in sorted(mods):
        if item in produced:
            continue
        const = const_of.get(item)
        if const and re.search(r"ModItems\." + const + r"\b", blob_other):
            notes.append(f"物品 {MOD_NAME}:{item} 无配方产出，但代码里引用了（掉落/投掷等），确认是否可获得")
        else:
            notes.append(f"物品 {MOD_NAME}:{item} 无配方产出，也未见掉落逻辑 → 只能创造模式获取")

    print("=" * 70)
    lm_count = check_loot_modifiers(mods, tables)
    print(f"配方数量: {len(recipes)}   模组物品: {len(mods)}   战利品修饰器: {lm_count}")
    if problems:
        print(f"\n[问题] {len(problems)}")
        for p in problems:
            print("  ✗ " + p)
    else:
        print("\n[问题] 无")
    if notes:
        print(f"\n[提示] {len(notes)}")
        for n in notes:
            print("  · " + n)
    print("=" * 70)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
