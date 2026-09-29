# -*- coding: utf-8 -*-
"""检查文件是否合法 UTF-8（这台机器上 PowerShell 改过的 .py 会被写成 GBK/坏字节）。"""
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
for f in sys.argv[1:]:
    b = open(f, 'rb').read()
    try:
        b.decode('utf-8')
        print('%-28s utf-8 OK   %d bytes' % (f, len(b)))
    except Exception as e:
        print('%-28s utf-8 FAIL %s' % (f, e))
        for enc in ('gbk', 'cp936', 'latin-1'):
            try:
                b.decode(enc)
                print('   -> 用 %s 能读通' % enc)
                break
            except Exception:
                pass
