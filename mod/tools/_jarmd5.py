"""列出 build/libs 最新 jar 内匹配资源的大小与 md5，和 src 下的源文件对比。

用法: python tools\_jarmd5.py [关键词]      # 默认 compound_bow
"""
import hashlib
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBS = os.path.join(ROOT, 'build', 'libs')
RES = os.path.join(ROOT, 'src', 'main', 'resources')
key = sys.argv[1] if len(sys.argv) > 1 else 'compound_bow'

jar = None
for f in sorted(os.listdir(LIBS)):
    if f.endswith('.jar') and 'sources' not in f:
        jar = os.path.join(LIBS, f)
print('jar =', os.path.basename(jar), ' %.2f MB' % (os.path.getsize(jar) / 1048576.0))
z = zipfile.ZipFile(jar)
names = [n for n in z.namelist() if key in n]
if not names:
    print('  (jar 内没有匹配 %r 的条目)' % key)
for n in sorted(names):
    data = z.read(n)
    h = hashlib.md5(data).hexdigest()
    src = os.path.join(RES, n.replace('/', os.sep))
    tag = '??'
    if os.path.isfile(src):
        sh = hashlib.md5(open(src, 'rb').read()).hexdigest()
        tag = 'MATCH' if sh == h else 'DIFF(src=%s)' % sh[:8]
    print('%-52s %9d  %s  %s' % (n.split('assets/')[-1], len(data), h[:12], tag))
