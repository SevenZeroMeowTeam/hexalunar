# -*- coding: utf-8 -*-
"""手雷 / 震爆弹「保险销 + 压杆」行为离线自检（r75）。

只做两件事：
1. 读源码核对关键规则（尤其是「手里攥着绝不能点燃引信」这条硬保证）；
2. 把状态机可读地打出来，方便对着用户描述逐条核对。

用法： cd mod; python tools/_gren_pin.py
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEM = os.path.join(ROOT, "src", "main", "java", "cn", "blockforge", "generated",
                    "hexalunarcalamity", "item", "GrenadeItem.java")
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "hexalunar_calamity", "lang")

ok = True


def check(label, cond, detail=u""):
    global ok
    ok = ok and bool(cond)
    print(u"  [%s] %s%s" % (u"OK " if cond else u"FAIL", label,
                            (u"  -> " + detail) if detail else u""))


with io.open(ITEM, encoding="utf-8") as fh:
    src = fh.read()

print(u"== 1. 硬保证：手里攥着的手雷永远不点燃引信 ==")
# 全文件里不允许出现「把状态写成 ARMED」的语句（ARMED 只属于飞行中的抛射体）
arm_writes = re.findall(r"putInt\(\s*TAG_STATE\s*,\s*STATE_ARMED", src)
check(u"没有任何地方把持有物写成 ARMED", not arm_writes, u"命中 %d 处" % len(arm_writes))
check(u"serverTick 把 ARMED 折回 PRIMED",
      re.search(r"case STATE_ARMED -> \{[^}]*setPrimed\(stack, now\)", src, re.S) is not None)
check(u"不在手上（副手/背包/护甲）的雷一律回 SAFE",
      src.count(u"setState(stack, STATE_SAFE)") >= 4,
      u"命中 %d 处" % src.count(u"setState(stack, STATE_SAFE)"))
check(u"引信只在 serverThrow（出手）里给抛射体",
      u"new GrenadeEntity(level, player, g.kind, remaining)" in src)

print(u"== 2. 松手规则 ==")
check(u"拔销没拔完松手 → SAFE", u'message.hexalunar_calamity.pin_slipped' in src)
check(u"刚拔完就松手 → 自动插回（AUTO_BACK_TICKS）",
      u"AUTO_BACK_TICKS" in src and u'"message.hexalunar_calamity.pin_autoback"' in src)
check(u"自动插回判据用「拔销时刻 + 宽限」",
      re.search(r"now - primedAt\(stack\) <= AUTO_BACK_TICKS", src) is not None)
check(u"插销中松手 → 回到 PRIMED（销还没进去）",
      re.search(r"STATE_REINSERTING\)\s*\{\s*\n\s*//.*\n\s*setPrimed\(stack, now\)", src) is not None)
check(u"setPrimed 记录拔销时刻", u"tag.putLong(TAG_PRIMED_AT, gameTime)" in src)
check(u"回 SAFE 时清掉拔销时刻", u"tag.remove(TAG_PRIMED_AT)" in src)

print(u"== 3. 语言文件 ==")
for name in ("zh_cn.json", "en_us.json"):
    with io.open(os.path.join(LANG, name), encoding="utf-8") as fh:
        text = fh.read()
    for key in (u"pin_slipped", u"pin_autoback", u"pin_back", u"pin_pulled",
                u"pin_reinsert_hint", u"need_pin"):
        full = u"message.hexalunar_calamity." + key
        check(u"%s 有 %s" % (name, key), u'"%s"' % full in text)

print(u"== 4. 状态机（对着需求逐条核对） ==")
rows = [
    (u"SAFE", u"按住右键 1 秒", u"PRIMED", u"拔销完成，销在外、压杆被手压着"),
    (u"SAFE", u"中途松手（<1 秒）", u"SAFE", u"销自己弹回去（提示 pin_slipped）"),
    (u"PRIMED", u"30 tick（1.5 秒）内松手", u"SAFE", u"当手滑处理，销自动插回（pin_autoback）"),
    (u"PRIMED", u"攥着超过 1.5 秒再松", u"PRIMED", u"保持待投（玩家是有意的）"),
    (u"PRIMED", u"潜行 + 右键 1 秒", u"SAFE", u"手动插回保险销"),
    (u"PRIMED", u"左键", u"抛射体", u"★ 引信在这一刻才点燃（满 5 秒）"),
    (u"REINSERTING", u"中途松手", u"PRIMED", u"销没进去，回到安全待投"),
    (u"任意", u"离开手（换槽位/收背包/副手被枪占）", u"SAFE", u"压杆失去手的压力，销自动弹回"),
    (u"任意", u"手里被塞进 ARMED（旧存档）", u"PRIMED", u"serverTick 折回，手里永不自爆"),
]
print(u"  %-12s %-28s %-8s %s" % (u"起态", u"事件", u"到态", u"说明"))
for a, b, c, d in rows:
    print(u"  %-12s %-28s %-8s %s" % (a, b, c, d))

print(u"")
print(u"结果：" + (u"全部通过" if ok else u"有 FAIL，需要修"))
sys.exit(0 if ok else 1)
