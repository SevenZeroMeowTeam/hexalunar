"""校验 jar 内 lang 文案是否混入杂空格，并列出关键键。

用法: python tools\_langchk.py [键名前缀]
"""
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBS = os.path.join(ROOT, 'build', 'libs')
jar = None
for f in sorted(os.listdir(LIBS)):
    if f.endswith('.jar') and 'sources' not in f:
        jar = os.path.join(LIBS, f)
print('jar =', os.path.basename(jar))
z = zipfile.ZipFile(jar)
d = json.loads(z.read('assets/hexalunar_calamity/lang/zh_cn.json').decode('utf-8'))
want = sys.argv[1] if len(sys.argv) > 1 else 'grenade'
bad = 0
for k in sorted(d):
    if want not in k:
        continue
    v = d[k]
    # 中文之间夹一个半角空格 = 手抖写进去的
    susp = any(v[i] == ' ' and i > 0 and i + 1 < len(v)
               and v[i - 1] > '\u2fff' and v[i + 1] > '\u2fff' for i in range(len(v)))
    if susp:
        bad += 1
    print('%-46s %s %s' % (k, 'SUSPECT' if susp else 'ok', v))
print('检查 %d 条，可疑 %d 条' % (len([k for k in d if want in k]), bad))
