#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""翻译键体检：Java 里用到的 key 是否都存在于 lang 文件，中英文是否对齐。"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "mod", "src", "main")
JAVA = os.path.join(SRC, "java")
LANG = os.path.join(SRC, "resources", "assets", "hexalunar_calamity", "lang")

keys = set()
for dp, _d, files in os.walk(JAVA):
    for fn in files:
        if not fn.endswith(".java"):
            continue
        with open(os.path.join(dp, fn), encoding="utf-8") as f:
            text = f.read()
        for m in re.finditer(r'Component\.translatable\(\s*"([^"]+)"', text):
            keys.add(m.group(1))
        for m in re.finditer(r'"(?:item|entity|effect|moon|message|tooltip|key|hud)\.hexalunar_calamity\.[^"]*"', text):
            keys.add(m.group(0)[1:-1])

langs = {}
for name in ("en_us", "zh_cn"):
    with open(os.path.join(LANG, name + ".json"), encoding="utf-8") as f:
        langs[name] = json.load(f)

bad = 0
for key in sorted(keys):
    if key.endswith("."):
        continue  # 代码里是 "前缀." + 动态 id 拼出来的，不单独校验
    missing = [n for n, d in langs.items() if key not in d]
    if missing:
        print(f"[缺翻译] {key}  -> 缺少 {', '.join(missing)}")
        bad += 1

only_one = sorted(
    (set(langs["en_us"]) | set(langs["zh_cn"])) - (set(langs["en_us"]) & set(langs["zh_cn"]))
)
for key in only_one:
    where = "en_us" if key in langs["en_us"] else "zh_cn"
    print(f"[单边] {key} 只存在于 {where}")
    bad += 1

# 代码里拼出来的 key（前缀 + 动态 id）单独检查：item.hexalunar_calamity.<id>
items = set(re.findall(r'ITEMS\.register\("([a-z0-9_]+)"', open(os.path.join(
    JAVA, "cn", "blockforge", "generated", "hexalunarcalamity", "registry", "ModItems.java"),
    encoding="utf-8").read()))
for item in sorted(items):
    key = f"item.hexalunar_calamity.{item}"
    for name, d in langs.items():
        if key not in d:
            print(f"[缺翻译] {key} -> 缺少 {name}")
            bad += 1

print(f"\n扫描到代码引用 key {len(keys)} 个，问题 {bad} 处")
sys.exit(1 if bad else 0)
