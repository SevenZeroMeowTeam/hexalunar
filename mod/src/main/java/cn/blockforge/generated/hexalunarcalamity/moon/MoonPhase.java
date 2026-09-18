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
            0xFF4A38, 0xFF2A18, 0x1C0608, 0x521114,
            false, 2.0F, 0.0F, 0.0F, 0.10F, 0.6F, () -> ModSounds.ALARM_BLOOD.get()),
    BLUE("blue_moon", "蓝月", 0x274F9E, 0x3A3355CC, 0x66AAFF,
            0xAECBFF, 0x4A7CFF, 0x06101F, 0x143A6E,
            false, 1.0F, 0.35F, 0.0F, 0.06F, 1.0F, () -> ModSounds.ALARM_BLUE.get()),
    YELLOW("yellow_moon", "黄月", 0x8A6D1F, 0x33C8A032, 0xFFDD55,
            0xFFD35E, 0xFFB320, 0x141005, 0x453512,
            false, 1.0F, 0.0F, 2.0F, 0.04F, 1.4F, () -> ModSounds.ALARM_YELLOW.get()),
    SUPER_BLOOD("super_blood", "超级血月", 0x6E0F0F, 0x55DD1818, 0xFF3030,
            0xFF6E52, 0xFF3018, 0x28070B, 0x6E1616,
            true, 3.0F, 0.0F, 0.0F, 0.22F, 0.6F, () -> ModSounds.ALARM_BLOOD.get()),
    SUPER_BLUE("super_blue", "超级蓝月", 0x183A80, 0x4A2244CC, 0x88CCFF,
            0xD2E8FF, 0x5E96FF, 0x08142E, 0x1C4A88,
            true, 1.0F, 0.60F, 0.0F, 0.18F, 1.0F, () -> ModSounds.ALARM_BLUE.get()),
    SUPER_YELLOW("super_yellow", "超级黄月", 0x6E520F, 0x44E0B040, 0xFFEE77,
            0xFFE9A0, 0xFFC840, 0x1C1608, 0x57431A,
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

    /** 按夜晚序号取月相：第 1 夜血月，第 2 夜蓝月……循环推进 */
    @Nullable
    public static MoonPhase forNight(long nightCount) {
        if (nightCount <= 0) return null;
        return ORDER[(int) ((nightCount - 1) % ORDER.length)];
    }

    /** 黄月类月相下是否提升掉落 */
    public boolean boostsDrops() {
        return this == YELLOW || this == SUPER_YELLOW;
    }

    /** 蓝月类月相下僵尸是否加速 */
    public boolean boostsSpeed() {
        return this == BLUE || this == SUPER_BLUE;
    }

    /** 血月类月相是否增加数量 */
    public boolean boostsSpawns() {
        return this == BLOOD || this == SUPER_BLOOD;
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
