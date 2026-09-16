#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""旋转 OBJ 的顶点（绕 X / Y / Z，单位度，按 Z→Y→X 顺序复合）。

用途：原版物品贴图/工具模型的「长度方向」是 +Y（display 的 handheld 参数就是按这个约定调的），
而 Blockbench 里常把枪/弩建模成沿 +Z 伸长。把几何预先旋转到 Y 轴，就能直接套用原版
item/handheld 的姿态参数，既不用手调 rotation，也不会出现「模型横躺在屏幕里」。

用法:
  python obj_rotate.py <obj> --x -90 [--y 0] [--z 0] [--out 目标.obj]
  # 不给 --out 时原地修改，并自动写 .rotbak 备份
"""
import argparse
import math
import os
import shutil


def rot_point(p, rx, ry, rz):
    x, y, z = p
    # Rz
    if rz:
        c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
        x, y = x * c - y * s, x * s + y * c
    # Ry
    if ry:
        c, s = math.cos(math.radians(ry)), math.sin(math.radians(ry))
        x, z = x * c + z * s, -x * s + z * c
    # Rx
    if rx:
        c, s = math.cos(math.radians(rx)), math.sin(math.radians(rx))
        y, z = y * c - z * s, y * s + z * c
    return x, y, z


def bbox_center(path):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            p = line.split()
            if p and p[0] == "v":
                for i in range(3):
                    v = float(p[1 + i])
                    lo[i] = min(lo[i], v)
                    hi[i] = max(hi[i], v)
    return [(lo[i] + hi[i]) / 2.0 for i in range(3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj")
    ap.add_argument("--x", type=float, default=0.0)
    ap.add_argument("--y", type=float, default=0.0)
    ap.add_argument("--z", type=float, default=0.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--origin", action="store_true",
                    help="绕原点旋转（默认绕几何中心，保持模型居中在 (0.5,0.5,0.5)）")
    args = ap.parse_args()

    pivot = [0.0, 0.0, 0.0] if args.origin else bbox_center(args.obj)
    out_path = args.out or args.obj
    out_lines = []
    nv = 0
    with open(args.obj, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            p = line.split()
            if p and p[0] == "v":
                local = (float(p[1]) - pivot[0], float(p[2]) - pivot[1], float(p[3]) - pivot[2])
                x, y, z = rot_point(local, args.x, args.y, args.z)
                out_lines.append(f"v {x + pivot[0]:.6f} {y + pivot[1]:.6f} {z + pivot[2]:.6f}\n")
                nv += 1
            else:
                out_lines.append(line if line.endswith("\n") else line + "\n")

    if args.out is None:
        bak = args.obj + ".rotbak"
        if not os.path.exists(bak):
            shutil.copy2(args.obj, bak)
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"{os.path.basename(out_path)}: {nv} 个顶点 旋转 x={args.x} y={args.y} z={args.z} 轴心={[round(v, 4) for v in pivot]}")


if __name__ == "__main__":
    main()
