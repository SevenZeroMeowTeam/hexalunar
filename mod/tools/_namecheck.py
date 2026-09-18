# -*- coding: utf-8 -*-
"""校验 Mod 显示名（mods.toml 里的 displayName）是不是正确的 UTF-8 中文。

两件事：
1. 扫源码里还有没有「乱码残留」（把常见的乱码区段当成非法字符找出来）；
2. 直接读 jar 里的 META-INF/mods.toml，检查 displayName / description 的原始字节。

用法：
    cd mod; python tools/_namecheck.py                      # 只查源码
    cd mod; python tools/_namecheck.py build/libs/xxx.jar   # 顺带查 jar

输出：%TEMP%\\_namecheck_out.txt（写文件而不是打印：PS 控制台会把中文搞坏）
"""

import io
import os
import re
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(tempfile.gettempdir(), u'_namecheck_out.txt')

# 现在 build.gradle 里应该出现的正确名字
WANT = u'\u516d\u76f8\u6708\u707e'      # 六相月灾
# 乱码的特征码点：CJK 兼容/生僻区 + 私用区（PUA）。正常源码里不该出现 PUA
PUA = re.compile(u'[\ue000-\uf8ff]')
SUSPECT = re.compile(u'[\u5f90\u95b8\u53be\u5a34\u936b\u7e3e\u5910]')

lines = []
ok = True


def check(label, cond, detail=u''):
    global ok
    ok = ok and bool(cond)
    lines.append(u'  [%s] %s%s' % (u'OK ' if cond else u'FAIL', label,
                                   (u'  -> ' + detail) if detail else u''))


SCAN_EXT = (u'.java', u'.gradle', u'.toml', u'.json', u'.properties', u'.mcmeta')

lines.append(u'== 1. 源码扫描（私用区字符 / 乱码特征字） ==')
bad_files = 0
comment_files = 0
for base, dirs, files in os.walk(ROOT):
    if u'build' in base.split(os.sep) or u'.git' in base.split(os.sep):
        continue
    for name in files:
        if not name.endswith(SCAN_EXT):
            continue
        path = os.path.join(base, name)
        try:
            text = io.open(path, encoding=u'utf-8').read()
        except Exception as exc:
            lines.append(u'  [FAIL] 不是合法 UTF-8：%s（%s）' % (path, exc))
            ok = False
            continue
        hits = []
        warns = []
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            is_comment = (stripped.startswith(u'//') or stripped.startswith(u'#')
                          or stripped.startswith(u'*') or stripped.startswith(u'/*'))
            if PUA.search(line) or (SUSPECT.search(line) and WANT not in line):
                if is_comment:
                    warns.append(u'L%d' % i)
                else:
                    hits.append(u'L%d' % i)
        if hits:
            bad_files += 1
            lines.append(u'  [..] %s : %s（**非注释**，必须修）'
                         % (os.path.relpath(path, ROOT), u', '.join(hits)))
        if warns:
            comment_files += 1
            lines.append(u'  [..] %s : %s（仅注释里的历史乱码，不影响构建）'
                         % (os.path.relpath(path, ROOT), u', '.join(warns)))
check(u'非注释处没有乱码残留', bad_files == 0,
      u'%d 个文件命中' % bad_files if bad_files else u'')
if comment_files:
    lines.append(u'  （提示：%d 个文件的注释里有历史乱码，纯外观问题）' % comment_files)

lines.append(u'')
lines.append(u'== 2. build.gradle 的 mod_name ==')
bg = io.open(os.path.join(ROOT, u'build.gradle'), encoding=u'utf-8').read()
m = re.search(r"mod_name:\s*'([^']*)'", bg)
if m:
    lines.append(u'  mod_name = %s' % m.group(1))
    check(u'mod_name 等于 %s' % WANT, m.group(1) == WANT,
          u'utf-8 bytes = %s' % m.group(1).encode(u'utf-8').hex() if m.group(1) != WANT else u'')
else:
    check(u'找到 mod_name', False)

lines.append(u'')
lines.append(u'== 3. jar 里的 META-INF/mods.toml ==')
jar = sys.argv[1] if len(sys.argv) > 1 else None
if jar is None:
    libs = os.path.join(ROOT, u'build', u'libs')
    cands = [f for f in os.listdir(libs)] if os.path.isdir(libs) else []
    cands = sorted(cands)
    jar = os.path.join(libs, cands[-1]) if cands else None
    lines.append(u'  （未指定 jar，自动用最新的：%s）' % (os.path.basename(jar) if jar else u'无'))

if jar and os.path.isfile(jar):
    lines.append(u'  jar = %s' % os.path.basename(jar))
    with zipfile.ZipFile(jar) as zf:
        data = zf.read(u'META-INF/mods.toml')
    text = data.decode(u'utf-8')
    disp = re.search(u'displayName\\s*=\\s*"([^"]*)"', text) \
        or re.search(u'displayName\\s*=\\s*\'([^\']*)\'', text)
    desc = re.search(u'description\\s*=\\s*\'\'\'([^\']*)\'\'\'', text)
    if disp:
        lines.append(u'  displayName = %s' % disp.group(1))
        check(u'displayName 是正确 UTF-8 的 %s' % WANT, disp.group(1) == WANT,
              u'utf-8 bytes = %s' % disp.group(1).encode(u'utf-8').hex())
    else:
        check(u'jar 里有 displayName', False)
    if desc:
        lines.append(u'  description = %s' % desc.group(1))
        check(u'description 正确', desc.group(1) == WANT)
    # 整个 mods.toml 里不该再出现私用区/替换字符
    check(u'mods.toml 里没有替换字符 U+FFFD / 私用区',
          u'\ufffd' not in text and not PUA.search(text))
else:
    check(u'找到 jar', False, u'先跑一次 build')

lines.append(u'')
lines.append(u'结果：' + (u'全部通过' if ok else u'有 FAIL，需要修'))

with io.open(OUT, u'w', encoding=u'utf-8') as fh:
    fh.write(u'\n'.join(lines))
print(u'written: %s' % OUT)
sys.exit(0 if ok else 1)
