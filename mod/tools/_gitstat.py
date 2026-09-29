# -*- coding: utf-8 -*-
"""把 git status --short 按 UTF-8 落成 build/_gitstatus.txt（终端中文会乱码 / 会被截断）。

用法::  python tools/_gitstat.py
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)

out = subprocess.run(['git', '-c', 'core.quotepath=false', 'status', '--short'],
                     cwd=MOD, capture_output=True)
txt = out.stdout.decode('utf-8', 'replace')
lines = [ln for ln in txt.splitlines() if ln.strip()]
dst = os.path.join(MOD, 'build', '_gitstatus.txt')
with open(dst, 'w', encoding='utf-8') as fh:
    for ln in lines:
        fh.write(ln.rstrip() + '\n')
print('changed=%d -> build/_gitstatus.txt' % len(lines))
