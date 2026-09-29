# -*- coding: utf-8 -*-
"""反汇编某个类的 javap 输出并列出它调用的方法（查「欧拉角合成顺序」这类问题）。"""
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JAR = (os.path.expanduser('~') + r'\.gradle\caches\modules-2\files-2.1\software.bernie'
       r'.geckolib\geckolib-forge-1.20.1\4.8.4'
       r'\35153b92ee86becebbf3b0b2559e2bc9ee8d16fb\geckolib-forge-1.20.1-4.8.4.jar')

cls = sys.argv[1] if len(sys.argv) > 1 else 'software.bernie.geckolib.cache.object.GeoBone'
pat = sys.argv[2] if len(sys.argv) > 2 else 'Method'

out = subprocess.run(['javap', '-p', '-c', '-cp', JAR, cls],
                     capture_output=True, text=True, errors='replace').stdout
for line in out.splitlines():
    if pat in line:
        print(line.strip())
