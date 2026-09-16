#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志体检：把 mod/logs（含 .gz 轮转日志）扫一遍，捞出模组相关的报错与可疑告警。

用法:
  python tools/log_audit.py [--dir mod/logs] [--show 20]
"""
import argparse
import gzip
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PKG = "cn.blockforge.generated.hexalunarcalamity"

LEVELS = ("FATAL", "ERROR", "WARN")
LINE_RE = re.compile(
    r"^\[[^\]]*?(\d{2}:\d{2}:\d{2}\.\d+)\]\s*\[([^\]]+)/(FATAL|ERROR|WARN|INFO|DEBUG)\]")


def read_lines(path):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def main():
    # Windows 控制台默认 GBK，日志里有非法字节会直接抛 UnicodeEncodeError
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(ROOT, "mod", "logs"))
    ap.add_argument("--show", type=int, default=25, help="每类最多显示多少条")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        print("找不到日志目录:", args.dir)
        return 1

    files = sorted(
        (f for f in os.listdir(args.dir) if f.endswith((".log", ".log.gz"))),
        key=lambda f: os.path.getmtime(os.path.join(args.dir, f)),
    )
    if not files:
        print("目录里没有日志文件:", args.dir)
        return 1

    timeline = []          # (file, level, source, message)
    stack_hits = []        # 堆栈里出现模组包名的行
    interesting = defaultdict(list)

    for name in files:
        path = os.path.join(args.dir, name)
        for raw in read_lines(path):
            line = raw.rstrip("\r\n")
            m = LINE_RE.match(line)
            if m:
                _time, source, level = m.group(1), m.group(2), m.group(3)
                if level in LEVELS:
                    timeline.append((name, level, source, line))
            if PKG in line or "hexalunar" in line.lower():
                stack_hits.append((name, line.strip()))

    print("=" * 74)
    print(f"扫描 {len(files)} 个日志文件（{files[0]} … {files[-1]}）")
    print("=" * 74)

    # 1) 模组包名出现在堆栈/报错里 —— 最可能是我们的 bug
    ours = [h for h in stack_hits if "at " in h[1] or "Exception" in h[1] or "Caused by" in h[1]]
    print(f"\n### 与模组包名相关的堆栈/异常：{len(ours)} 行")
    for name, line in ours[:args.show]:
        print(f"  [{name}] {line}")
    if len(ours) > args.show:
        print(f"  … 其余 {len(ours) - args.show} 行省略")

    # 2) 按错误类型归类（忽略模组加载的常规噪音）
    noise = ("Mod file ", "mods.toml", "uses unexpected schema", "Missing sound for event",
             "could not find sampler", "preferIPv6Addresses", "version differences",
             "did not get ID it asked for", "Loaded ", "Preparing crash report")
    counter = Counter()
    samples = defaultdict(list)
    for name, level, source, line in timeline:
        if any(n in line for n in noise):
            continue
        # 归类键：异常类名 / 消息主干
        key = None
        m = re.search(r"([A-Za-z.]*(?:Exception|Error|Throwable))\b", line)
        if m:
            key = m.group(1).split(".")[-1]
        elif level in ("FATAL", "ERROR"):
            key = line.split("]")[-1].strip()[:90]
        if key:
            counter[key] += 1
            if len(samples[key]) < args.show:
                samples[key].append((name, line))

    print(f"\n### 归类后的报错/告警（{sum(counter.values())} 条）")
    for key, count in counter.most_common():
        print(f"\n  ● [{count}x] {key}")
        for name, line in samples[key][:args.show]:
            print(f"      [{name}] {line[line.find(']', line.find(']') + 1) + 1:].strip()[:150]}")

    # 3) 关心的一些具体信号
    print("\n### 关键信号")
    signals = {
        "配方数量": r"Loaded (\d+) recipes",
        "进度数量": r"Loaded (\d+) advancements",
        "缺失贴图/模型": r"Missing (?:sprite|model|texture)[^\n]*",
        "战利品修饰器错误": r"(?i)loot modifier[^\n]*|global_loot[^\n]*",
        "客户端崩溃报告": r"Preparing crash report with UUID",
    }
    for label, pattern in signals.items():
        hits = []
        for name in files:
            for raw in read_lines(os.path.join(args.dir, name)):
                for m in re.finditer(pattern, raw):
                    hits.append((name, m.group(0).strip()))
        if hits:
            uniq = sorted({h[1] for h in hits})
            print(f"  · {label}: {', '.join(uniq[:6])}")
        else:
            print(f"  · {label}: 无")
    return 0


if __name__ == "__main__":
    sys.exit(main())
