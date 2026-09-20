# -*- coding: utf-8 -*-
"""跑一遍 `tools/awp_v2.py` 的自检并把结果按 UTF-8 落成 `build/_awp2check.txt`（终端会乱码）。"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
KEYS = ('★', 'OK', '!!', '整体', '关键模型点', 'density', '-> ', '??', '骨骼名')

env = dict(os.environ, PYTHONIOENCODING='utf-8')
proc = subprocess.run([sys.executable, os.path.join(HERE, 'awp_v2.py')],
                      cwd=MOD, capture_output=True, env=env)
txt = proc.stdout.decode('utf-8', 'replace') + proc.stderr.decode('utf-8', 'replace')
lines = [ln for ln in txt.splitlines() if any(k in ln for k in KEYS)]
bad = [ln for ln in lines if '!!' in ln]
dst = os.path.join(MOD, 'build', '_awp2check.txt')
with open(dst, 'w', encoding='utf-8') as fh:
    fh.write('awp_v2.py exit=%d   自检行 %d   ★ 失败 %d\n\n'
             % (proc.returncode, len(lines), len(bad)))
    fh.write('\n'.join(lines) + '\n')
print('exit=%d  lines=%d  bad=%d -> build/_awp2check.txt' % (proc.returncode, len(lines), len(bad)))
