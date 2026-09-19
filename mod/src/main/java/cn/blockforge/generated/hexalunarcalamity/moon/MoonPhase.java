package cn.blockforge.generated.hexalunarcalamity.moon;

import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.sounds.SoundEvent;
import org.jetbrains.annotations.Nullable;

import java.util.function.Supplier;

/**
 * 六相月灾进程：每夜按血月、蓝月、黄月、超级血月、超级蓝月、超级黄月顺序轮转。
 */
public enum MoonPhase {
    BLOOD("blood_moon", "血月", 0x8A1F1F, 0x40CC2222, 0xCC2222,
            0xFF3030, 0xFF2020, 0x5A0C0E, 0xB01818,
            false, 2.0F, 0.0F, 0.0F, 0.10F, 0.6F, () -> ModSounds.ALARM_BLOOD.get()),
    BLUE("blue_moon", "蓝月", 0x274F9E, 0x3A3355CC, 0x66AAFF,
            0x88B8FF, 0x4A7CFF, 0x0C2258, 0x2A5ABE,
            false, 1.0F, 0.0F, 0.0F, 0.06F, 1.0F, () -> ModSounds.ALARM_BLUE.get()),
    YELLOW("yellow_moon", "黄月", 0x8A6D1F, 0x33C8A032, 0xFFDD55,
            0xFFD35E, 0xFFB320, 0x4E3C0C, 0xB08A1E,
            false, 1.0F, 0.0F, 1.0F, 0.04F, 1.4F, () -> ModSounds.ALARM_YELLOW.get()),
    SUPER_BLOOD("super_blood", "超级血月", 0x6E0F0F, 0x55DD1818, 0xFF3030,
            0xFF5A46, 0xFF2818, 0x7A1012, 0xD01818,
            true, 3.0F, 0.0F, 0.0F, 0.22F, 0.6F, () -> ModSounds.ALARM_BLOOD.get()),
    SUPER_BLUE("super_blue", "超级蓝月", 0x183A80, 0x4A2244CC, 0x88CCFF,
            0xB8D8FF, 0x5E96FF, 0x142E78, 0x3A74E0,
            true, 1.0F, 0.0F, 0.0F, 0.18F, 1.0F, () -> ModSounds.ALARM_BLUE.get()),
    SUPER_YELLOW("super_yellow", "超级黄月", 0x6E520F, 0x44E0B040, 0xFFEE77,
            0xFFE070, 0xFFC840, 0x634D10, 0xD8AC28,
            true, 1.0F, 0.0F, 3.0F, 0.14F, 1.4F, () -> ModSounds.ALARM_YELLOW.get());

    public static final MoonPhase[] ORDER = values();

    /** 顺序索引（-1 表示无月相） */
    public static int indexOf(@Nullable MoonPhase phase) {
        if (phase == null) return -1;
        return phase.ordinal();
    }

    @Nullable
    public static MoonPhase byIndex(int index) {
        if (index < 0 || index >= ORDER.length) return null;
        return ORDER[index];
    }

    /**
     * 随机抽一个月相：六相同权重。
     *
     * <p>r75：不再按夜数轮转 —— 所以**可能连着两夜同一个**，也**可能几十夜都不出月相**
     * （出不出由 {@code MoonManager.rollNightPhase} 的概率决定）。
     */
    public static MoonPhase random(net.minecraft.util.RandomSource rand) {
        return ORDER[rand.nextInt(ORDER.length)];
    }

    /** 按 id 找月相（"blood_moon" 这种），找不到返回 null */
    @Nullable
    public static MoonPhase byId(String id) {
        for (MoonPhase p : ORDER) {
            if (p.id.equalsIgnoreCase(id)) return p;
        }
        return null;
    }

    /** 血月类（含超级）：亡灵会进化、玩家不能睡觉、会有尸潮 */
    public boolean isBlood() {
        return this == BLOOD || this == SUPER_BLOOD;
    }

    /** 蓝月类（含超级）：玩家拿幸运，僵尸没有任何加成 */
    public boolean isBlue() {
        return this == BLUE || this == SUPER_BLUE;
    }

    /** 黄月类（含超级）：只加速作物生长，没有其他加成 */
    public boolean isYellow() {
        return this == YELLOW || this == SUPER_YELLOW;
    }

    /**
     * 蓝月给玩家加「幸运」的药水等级；-1 表示这个月相不给。
     * 蓝月 = 幸运 I，超级蓝月 = 幸运 II。
     */
    public int luckAmplifier() {
        return switch (this) {
            case BLUE -> 0;
            case SUPER_BLUE -> 1;
            default -> -1;
        };
    }

    /**
     * 黄月加速作物生长：每隔多少 tick 催一次玩家附近的作物（0 = 不催）。
     * 超级黄月更快。
     */
    public int cropTickInterval() {
        return switch (this) {
            case YELLOW -> 20;
            case SUPER_YELLOW -> 7;
            default -> 0;
        };
    }

    /** 尸潮规模倍率（超级血月是普通血月的 1.5 倍） */
    public float hordeScale() {
        return superMoon ? 1.5F : 1.0F;
    }

    /** 血月类月相是否增加数量 */
    public boolean boostsSpawns() {
        return isBlood();
    }

    public final String id;
    public final String zhName;
    /** 雾色 RGB */
    public final int fogColor;
    /** 全屏天空着色 ARGB */
    public final int skyTint;
    /** 环境粒子颜色 RGB */
    public final int dustColor;
    /** ★ 月盘颜色 RGB（r66：AFTER_SKY 阶段自己画的天穹/月盘，见 client/MoonSkyRenderer） */
    public final int moonColor;
    /** ★ 月盘光晕颜色 RGB（叠加混合） */
    public final int moonHalo;
    /** ★ 天顶颜色 RGB */
    public final int skyTop;
    /** ★ 地平线颜色 RGB */
    public final int skyHorizon;
    /** 超级月相：延长夜晚、提高精英率 */
    public final boolean superMoon;
    /** 尸潮数量倍率 */
    public final float spawnMultiplier;
    /** 僵尸移速加成 */
    public final float speedBonus;
    /** 掉落倍率 */
    public final float dropMultiplier;
    /** 特殊感染者出现概率 */
    public final float eliteChance;
    /** 警报音效播放音高 */
    public final float alarmPitch;
    public final Supplier<SoundEvent> alarmSound;

    MoonPhase(String id, String zhName, int fogColor, int skyTint, int dustColor,
              int moonColor, int moonHalo, int skyTop, int skyHorizon,
              boolean superMoon, float spawnMultiplier, float speedBonus, float dropMultiplier,
              float eliteChance, float alarmPitch, Supplier<SoundEvent> alarmSound) {
        this.id = id;
        this.zhName = zhName;
        this.fogColor = fogColor;
        this.skyTint = skyTint;
        this.dustColor = dustColor;
        this.moonColor = moonColor;
        this.moonHalo = moonHalo;
        this.skyTop = skyTop;
        this.skyHorizon = skyHorizon;
        this.superMoon = superMoon;
        this.spawnMultiplier = spawnMultiplier;
        this.speedBonus = speedBonus;
        this.dropMultiplier = dropMultiplier;
        this.eliteChance = eliteChance;
        this.alarmPitch = alarmPitch;
        this.alarmSound = alarmSound;
    }
}
