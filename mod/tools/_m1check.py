# -*- coding: utf-8 -*-
"""跑一遍 `tools/m1_garand_v2.py` 的自检，把关心的行按 **UTF-8** 写进 `build/_m1check.txt`。

为什么要这个脚本：这台机器的终端管道会把中文按 GBK 二次解码 ⇒ 直接看输出全是乱码；
把结果落成 UTF-8 文件再用编辑器打开就正常了。
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)

KEYS = ('★', 'OK', '!!', '整体', '关键模型点', 'wrote')

env = dict(os.environ, PYTHONIOENCODING='utf-8')
proc = subprocess.run([sys.executable, os.path.join(HERE, 'm1_garand_v2.py')],
                      cwd=MOD, capture_output=True, env=env)
txt = proc.stdout.decode('utf-8', 'replace') + proc.stderr.decode('utf-8', 'replace')
lines = [ln for ln in txt.splitlines() if any(k in ln for k in KEYS)]
bad = [ln for ln in lines if '!!' in ln]

dst = os.path.join(MOD, 'build', '_m1check.txt')
with open(dst, 'w', encoding='utf-8') as fh:
    fh.write('m1_garand_v2.py exit=%d   自检行 %d   ★ 失败 %d\n\n'
             % (proc.returncode, len(lines), len(bad)))
    fh.write('\n'.join(lines) + '\n')
print('exit=%d  lines=%d  bad=%d -> build/_m1check.txt' % (proc.returncode, len(lines), len(bad)))
