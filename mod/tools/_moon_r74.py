# -*- coding: utf-8 -*-
"""r74 月相玩法改造 —— 离线自检。

两件事：
1. 读月相相关 Java 源码，核对关键不变量（蓝月移速 / 黄月掉落这两项旧加成必须删干净）；
2. 按 MoonPhase / MoonManager 里的常数把四种血月夜的尸潮规模算出来，方便肉眼核对。

用法： cd mod; python tools/_moon_r74.py
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA = os.path.join(ROOT, "src", "main", "java", "cn", "blockforge", "generated",
                    "hexalunarcalamity")
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "hexalunar_calamity", "lang")

ok = True


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(u"  [%s] %s%s" % (u"OK " if cond else u"FAIL", label,
                            (u"  -> " + detail) if detail else ""))


def src(*parts):
    return read(os.path.join(JAVA, *parts))


print(u"== 1. 源码不变量 ==")

phase = src("moon", "MoonPhase.java")
for name in ("isBlood", "isBlue", "isYellow", "luckAmplifier", "cropTickInterval", "hordeScale"):
    check(u"MoonPhase 有 %s()" % name, re.search(r"%s\s*\(" % name, phase) is not None)
check(u"MoonPhase 已删除 boostsSpeed/boostsDrops",
      "boostsSpeed" not in phase and "boostsDrops" not in phase)
check(u"蓝月 speedBonus = 0", "1.0F, 0.0F, 0.0F" in phase, u"BLUE/SUPER_BLUE 行")
check(u"黄月 dropMultiplier = 1", "1.0F, 0.0F, 1.0F" in phase, u"YELLOW 行")
check(u"幸运等级：蓝月 I / 超级蓝月 II",
      "case BLUE -> 0;" in phase and "case SUPER_BLUE -> 1;" in phase)
check(u"作物间隔：黄月 20 / 超级黄月 7",
      "case YELLOW -> 20;" in phase and "case SUPER_YELLOW -> 7;" in phase)
check(u"尸潮倍率 1.5x（超级）= hordeScale",
      "superMoon ? 1.5F : 1.0F" in phase)

bless = src("moon", "MoonBlessings.java")
for label, needle in ((u"幸运效果 LUCK", "MobEffects.LUCK"),
                      (u"作物标签 CROPS", "BlockTags.CROPS"),
                      (u"睡不了觉 NOT_POSSIBLE_NOW", "NOT_POSSIBLE_NOW"),
                      (u"白天防火 FIRE_RESISTANCE", "MobEffects.FIRE_RESISTANCE"),
                      (u"尸潮标记 TAG_HORDE", "TAG_HORDE"),
                      (u"天亮收尾 dawnCleanup", "public static void dawnCleanup"),
                      (u"残留徘徊者 4 个", "DAWN_WANDERERS = 4")):
    check(label, needle in bless)

mgr = src("moon", "MoonManager.java")
check(u"尸潮固定 4 波", "HORDE_WAVES = 4" in mgr)
check(u"每波数量不同", "WAVE_SIZES = {6, 9, 13, 18}" in mgr)
check(u"血量月才开尸潮", "if (phase.isBlood())" in mgr)
check(u"第 14 天里程碑概率更高", "day % 14L == 0L" in mgr)
check(u"天亮调 dawnCleanup", "MoonBlessings.dawnCleanup(server)" in mgr)
check(u"尸潮怪会打标记", "MoonBlessings.TAG_HORDE, true" in mgr)

spawn = src("moon", "MoonSpawnEvents.java")
check(u"MoonSpawnEvents 不再给僵尸加速度", "AttributeModifier" not in spawn)
check(u"MoonSpawnEvents 不再改掉落", "LivingDropsEvent" not in spawn)
check(u"保留进化调用", "ZombieEvolution.markIfEvolving" in spawn)

evo = src("moon", "ZombieEvolution.java")
check(u"血月夜里进化随时间增幅", "nightRamp" in evo and "1.0F + p" in evo)
check(u"两处概率都乘了增幅", evo.count("* nightRamp(server)") == 2,
      u"命中 %d 处" % evo.count("* nightRamp(server)"))

print(u"== 2. 语言文件 ==")
for name in ("zh_cn.json", "en_us.json"):
    text = read(os.path.join(LANG, name))
    keys = [u"moon.hexalunar_calamity." + k for k in
            (u"no_sleep", u"horde_incoming", u"horde_wave", u"horde_cleared")]
    missing = [k for k in keys if u'"%s"' % k not in text]
    check(u"%s 有 4 个新键" % name, not missing, u"缺 %s" % missing if missing else u"")
    check(u"%s 文案已改成新规则（旧的移速/掉落描述已清掉）" % name,
          u"僵尸变得更快了" not in text and u"the dead run faster" not in text)

print(u"== 3. 尸潮规模推演（每波对每个玩家） ==")
sizes = [6, 9, 13, 18]
for label, scale, milestone in ((u"普通血月（第 7 天）", 1.0, False),
                                (u"超级血月（第 8 天）", 1.5, False),
                                (u"普通血月（第 14 天倍数）", 1.0 * 1.5, True),
                                (u"超级血月（第 14 天倍数）", 1.5 * 1.5, True)):
    counts = [int(-(-s * scale * 1.0 // 1)) for s in sizes]      # 期望值（0.85~1.15 抖动）
    total = sum(counts)
    print(u"  %-22s 四波: %-22s 合计 %d 只" %
          (label, u" / ".join(str(c) for c in counts), total))

print(u"== 4. r75：月相改成随机 + 指令 ==")
mgrtxt = mgr
check(u"MoonPhase 不再按夜数轮转（forNight 已删）", "forNight" not in phase)
check(u"MoonPhase 提供 random() / byId()",
      "public static MoonPhase random(" in phase and "public static MoonPhase byId(" in phase)
check(u"入夜走掷骰 rollNightPhase", "rollNightPhase" in mgrtxt)
check(u"基础概率常量 + 旱情补偿",
      "DEFAULT_MOON_CHANCE" in mgrtxt and "DROUGHT_GRACE" in mgrtxt)
check(u"没有月相时尸潮也能走（波次循环移出血月分支）",
      "if (data.hordeActive) {" in mgrtxt and "hordePhase(phase)" in mgrtxt)
data75 = src("moon", "MoonPhaseData.java")
for field in (u"moonChance", u"dryNights", u"forced"):
    check(u"MoonPhaseData 有字段 %s" % field, field in data75)
    check(u"MoonPhaseData 存/读 %s" % field,
          (u'putFloat("MoonChance"' in data75 if field == u"moonChance"
           else u'"%s"' % (u"DryNights" if field == u"dryNights" else u"Forced") in data75))

cmd = src("moon", "MoonCommands.java")
check(u"注册 hexalunar 与简写 hlc", '"hexalunar"' in cmd and '"hlc"' in cmd)
check(u"需要 OP 2 级权限", "hasPermission(PERMISSION)" in cmd and "PERMISSION = 2" in cmd)
for sub in (u"\"moon\"", u"\"set\"", u"\"clear\"", u"\"random\"", u"\"info\"", u"\"list\"", u"\"chance\"",
            u"\"horde\"", u"\"start\"", u"\"stop\"", u"\"wave\"", u"\"barrage\""):
    check(u"指令树含 %s" % sub, sub in cmd)
check(u"set 支持 none / byId 查表", u'"none".equalsIgnoreCase(id)' in cmd and
      "MoonPhase.byId(id)" in cmd)
check(u"msg() 返回 MutableComponent（Component 接口没有 withStyle）",
      "MutableComponent msg(" in cmd)
check(u"方法名不叫 level（避开 `ServerLevel level = level(src)` 的同名遮蔽）",
      "private static ServerLevel targetLevel(" in cmd)

langzh = read(os.path.join(LANG, "zh_cn.json"))
langen = read(os.path.join(LANG, "en_us.json"))
for name, text in ((u"zh_cn.json", langzh), (u"en_us.json", langen)):
    missing = [k for k in (u"moon.set", u"moon.cleared", u"moon.rolled", u"moon.rolled_none",
                           u"moon.unknown", u"moon.list", u"moon.none", u"moon.info1",
                           u"moon.info2", u"moon.info3", u"time.night", u"time.day",
                           u"horde.state_active", u"horde.state_idle", u"horde.started",
                           u"horde.stopped", u"horde.wave", u"barrage", u"chance.set")
               if u'"command.hexalunar_calamity.%s"' % k not in text]
    check(u"%s 指令文案齐全" % name, not missing, u"缺 %s" % missing if missing else u"")

print(u"== 5. 随机月相：连旱概率推演（基础 25% + 第 10 夜后每夜 +1%，上限 60%） ==")

def dry_after(nights):
    p = 1.0
    for k in range(1, nights + 1):
        chance = min(0.60, 0.25 + 0.01 * max(0, k - 1 - 10))
        p *= (1.0 - chance)
    return p

for n in (1, 3, 5, 10, 15, 20, 30, 40):
    print(u"  连续 %2d 夜都没月相的概率：%8.4f%%" % (n, dry_after(n) * 100.0))

print(u"")
print(u"结果：" + (u"全部通过" if ok else u"有 FAIL，需要修"))
sys.exit(0 if ok else 1)
