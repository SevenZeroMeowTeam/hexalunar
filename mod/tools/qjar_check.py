#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Q 弹版 / 普通版 jar 出货前自检。

用法:
    python tools/qjar_check.py                     # 自动找 build/libs 下的两个 jar
    python tools/qjar_check.py <jar> [<jar> ...]   # 指定 jar

为什么需要它 —— 这两类事故都真实发生过（2026-09-20）：
  1. `build/libs/hexalunar_calamity-1.0.0-r110.jar` 有资源、**0 个 class**（两个 Gradle 构建
     共用同一个 `build/` 目录并发跑，jar 任务抓到了空的 classes 输出）⇒ 进游戏必 ClassNotFound。
  2. 部署到 `.minecraft/mods/` 的 `hexalunar_calamity-1.0.0-r109.jar` **不是合法 zip**
     （1.1MB 截断包）⇒ Forge 直接报无效模组。
  所以「构建成功」不等于「产物可用」，本脚本按 jar 本体做体检。

检查项：
  * zip 完整性、条目数、**class 数量**（两版应一致，且远大于 0）
  * `META-INF/mods.toml` 的 modId / version / displayName
  * 资源命名空间**硬隔离**：普通版不得出现 `hexalunar_calamity_q:`，
    Q 版不得出现 `hexalunar_calamity:`（扫全部 .json/.mcmeta/.toml 文本）
  * Q 版必须有 Q 版样板资源（Q AKM 骨骼/贴图/流光遮罩、Q 僵尸贴图），普通版不得有
  * （可选，需要 javap）反汇编 `ModClient`：确认 BOMBER_ZOMBIE 绑的是
    普通版 `lambda$onRegisterRenderers$4`(tintedZombie) / Q 版 `$5`(QChibiZombieRenderer)，
    即 `BuildInfo.Q_MODE` 常量确实在编译期折掉了
退出码：0 = 全部通过；1 = 有 FAIL。
"""
import os
import re
import shutil
import subprocess
import sys
import zipfile

BASE_NS = 'hexalunar_calamity'
Q_NS = 'hexalunar_calamity_q'
Q_ASSETS = (
    'geo/akm.geo.json',
    'textures/models/akm_geo.png',
    'textures/models/akm_geo_glowmask.png',
    'textures/entity/q_chibi_zombie.png',
)
TEXT_EXT = ('.json', '.mcmeta', '.toml')

ok_all = True


def fail(msg):
    global ok_all
    ok_all = False
    print('  [FAIL] %s' % msg)


def info(msg):
    print('  %s' % msg)


def default_jars():
    libs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'build', 'libs')
    if not os.path.isdir(libs):
        return []
    return [os.path.join(libs, f) for f in sorted(os.listdir(libs))
            if f.endswith('.jar') and f.startswith(BASE_NS)]


def disasm_modclient(jar):
    """返回 (normal_live, q_live)：BOMBER_ZOMBIE 的 provider 绑到哪个 lambda。"""
    javap = shutil.which('javap')
    if not javap:
        for cand in (r'C:\Users\Administrator\.jdks\temurin-17\bin\javap.exe',):
            if os.path.exists(cand):
                javap = cand
                break
    if not javap:
        return None
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_modclient.class')
    with zipfile.ZipFile(jar) as z:
        hit = [x for x in z.namelist() if x.endswith('/ModClient.class')]
        if not hit:
            return None
        with open(tmp, 'wb') as fh:
            fh.write(z.read(hit[0]))
    try:
        out = subprocess.run([javap, '-v', '-p', tmp], capture_output=True,
                             text=True, encoding='utf-8', errors='replace').stdout
    except Exception:
        return None
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    # BootstrapMethods 里出现 MethodHandle 的 lambda 才是活的；
    # 只以 Utf8 名字出现的那个是 javac 留下的死方法体。
    live = set(re.findall(r'REF_invokeStatic [\w/$.]*ModClient\.lambda\$onRegisterRenderers\$(\d+)', out))
    return {'normal_live': '4' in live, 'q_live': '5' in live, 'live': sorted(live)}


def check(jar):
    global ok_all
    name = os.path.basename(jar)
    print('=' * 72)
    print('%s  (%.2f MB)' % (name, os.path.getsize(jar) / 1048576.0))
    if not os.path.exists(jar):
        fail('文件不存在')
        return
    try:
        z = zipfile.ZipFile(jar)
        bad = z.testzip()
    except zipfile.BadZipFile:
        fail('不是合法 zip（截断/损坏的产物，部署到 mods/ 会让 Forge 报无效模组）')
        return
    if bad:
        fail('zip 内损坏条目: %s' % bad)
        return

    n = z.namelist()
    cls = [x for x in n if x.endswith('.class')]
    is_q = any(x.startswith('assets/%s/' % Q_NS) for x in n)
    info('modId = %s' % (Q_NS if is_q else BASE_NS))

    mt = [x for x in n if x.endswith('META-INF/mods.toml')]
    if not mt:
        fail('缺 META-INF/mods.toml')
        return
    toml = z.read(mt[0]).decode('utf-8', 'replace')
    get = lambda k: (re.search(k + r'\s*=\s*"([^"]+)"', toml) or [None, None])[1]
    info('entries=%d  class=%d  modId=%s  version=%s' % (len(n), len(cls), get('modId'), get('version')))
    info('displayName=%s' % get('displayName'))
    if len(cls) < 100:
        fail('class 只有 %d 个 —— 大概率是抓到了空 classes 输出的残缺 jar' % len(cls))
    if get('modId') != (Q_NS if is_q else BASE_NS):
        fail('mods.toml 的 modId 与该 jar 的资源命名空间不一致')

    # 命名空间硬隔离
    pat_base = re.compile(re.escape(BASE_NS) + r'(?!_q)[:/]')
    pat_q = re.compile(re.escape(Q_NS) + r'[:/]')
    checked = cross = 0
    for e in n:
        if not e.endswith(TEXT_EXT):
            continue
        try:
            txt = z.read(e).decode('utf-8')
        except Exception:
            continue
        checked += 1
        hit = pat_base.search(txt) if is_q else pat_q.search(txt)
        if hit:
            cross += 1
            fail('%s 里出现%s命名空间引用: …%s…' % (
                e, '基础' if is_q else 'Q', txt[max(0, hit.start() - 30):hit.end() + 30]))
    info('文本资源 %d 个，跨命名空间引用 %d 处' % (checked, cross))
    if checked < 20:
        fail('文本资源太少（%d）—— 资源没打进 jar？' % checked)

    # Q 样板资源
    for a in Q_ASSETS:
        e = 'assets/%s/%s' % (Q_NS, a)
        if is_q and e not in n:
            fail('Q 版缺样板资源 %s' % e)
        if not is_q and e in n:
            fail('普通版里混进了 Q 专属资源 %s' % e)
    if is_q:
        info('Q 样板资源 %d/%d 就位' % (sum(1 for a in Q_ASSETS if 'assets/%s/%s' % (Q_NS, a) in n), len(Q_ASSETS)))
    else:
        if 'textures/entity/q_chibi_zombie.png' in ' '.join(n):
            fail('普通版里有 Q 僵尸贴图 —— 资源隔离漏了')

    # 常量折叠（可选）
    d = disasm_modclient(jar)
    if d is None:
        info('javap 不可用或有管道限制，跳过反汇编检查（不影响退出码）')
    else:
        info('活着的 onRegisterRenderers lambda: %s' % d['live'])
        if is_q and not d['q_live']:
            fail('Q 版里 BOMBER_ZOMBIE 没绑到 QChibiZombieRenderer($5)')
        if not is_q and not d['normal_live']:
            fail('普通版里 BOMBER_ZOMBIE 没绑到 tintedZombie($4)')


def main():
    jars = sys.argv[1:] or default_jars()
    if not jars:
        print('没找到 jar，请先 gradlew build')
        return 2
    for j in jars:
        check(os.path.abspath(j))
    print('=' * 72)
    print('结论: %s' % ('全部通过 ✅' if ok_all else '有 FAIL ❌'))
    return 0 if ok_all else 1


if __name__ == '__main__':
    sys.exit(main())
