#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 OBJ 里的多边形面拆成三角形。

为什么需要：Forge 的 OBJ 加载器（ObjModel）只稳吃三角形，四边形/多边形面在老版本里
会被直接跳过或读错顶点。程序化补出来的盒子（盖板、拉机柄）天然是四边形，发布前统一拆一下。

用法:
    python tools/obj_triangulate.py <file.obj> [...]     # 原地改写（会先备份 .quadbak）
    python tools/obj_triangulate.py --dry <file.obj>     # 只统计不改写
"""
import argparse
import os
import shutil
import sys


def triangulate(path, dry=False):
    """返回 (拆掉的多边形数, 生成的面数)。f a b c d -> f a b c + f a c d（保持原有 v/vt 索引）"""
    lines = []
    polys = 0
    made = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s.startswith("f "):
                toks = s.split()[1:]
                if len(toks) == 4:
                    a, b, c, d = toks
                    lines.append("f %s %s %s" % (a, b, c))
                    lines.append("f %s %s %s" % (a, c, d))
                    polys += 1
                    made += 2
                    continue
                if len(toks) > 4:
                    for i in range(1, len(toks) - 1):
                        lines.append("f %s %s %s" % (toks[0], toks[i], toks[i + 1]))
                    polys += 1
                    made += len(toks) - 2
                    continue
            lines.append(line.rstrip("\r\n"))
    if not dry and polys:
        backup = path + ".quadbak"
        if not os.path.exists(backup):
            shutil.copy2(path, backup)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
    return polys, made


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dry", action="store_true", help="只统计，不改写")
    args = ap.parse_args()

    total = 0
    for path in args.files:
        if not os.path.exists(path):
            print("跳过（不存在）:", path)
            continue
        polys, made = triangulate(path, args.dry)
        total += polys
        flag = "只统计" if args.dry else "已拆"
        print(f"{os.path.basename(path):<18} 多边形面 {polys} -> 三角形 {made}   [{flag}]")
    print("合计多边形面:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
