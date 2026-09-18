package cn.blockforge.generated.hexalunarcalamity.moon;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.saveddata.SavedData;
import org.jetbrains.annotations.Nullable;

/** 月灾进程持久化数据 */
public class MoonPhaseData extends SavedData {
    private static final String NAME = "hexalunar_moon";

    public long nightCount = 0L;
    /** 当前月相序号，-1 表示无月相 */
    public int activePhase = -1;
    public boolean wasNight = false;
    public long nextHordeTick = 0L;
    public long nextBarrageTick = 0L;
    /** 尸潮：是否正在进行 */
    public boolean hordeActive = false;
    /** 尸潮：已经放出的波数（0 = 还没开波，1..4 = 已放出的波数） */
    public int hordeWave = 0;
    /** 尸潮：下一波的时刻 */
    public long nextWaveTick = 0L;
    /** 每晚出现月相的基础概率（0~1，指令可调） */
    public float moonChance = MoonManager.DEFAULT_MOON_CHANCE;
    /** 已经连续多少夜没有月相（旱得越久越容易出，见 MoonManager#effectiveChance） */
    public int dryNights = 0;
    /** 今夜月相已被指令指定 ⇒ 入夜时不再掷骰 */
    public boolean forced = false;

    public static MoonPhaseData load(CompoundTag tag) {
        MoonPhaseData data = new MoonPhaseData();
        data.nightCount = tag.getLong("NightCount");
        data.activePhase = tag.getInt("ActivePhase");
        data.wasNight = tag.getBoolean("WasNight");
        data.nextHordeTick = tag.getLong("NextHorde");
        data.nextBarrageTick = tag.getLong("NextBarrage");
        data.hordeActive = tag.getBoolean("HordeActive");
        data.hordeWave = tag.getInt("HordeWave");
        data.nextWaveTick = tag.getLong("NextWave");
        if (tag.contains("MoonChance")) data.moonChance = tag.getFloat("MoonChance");
        data.dryNights = tag.getInt("DryNights");
        data.forced = tag.getBoolean("Forced");
        return data;
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        tag.putLong("NightCount", nightCount);
        tag.putInt("ActivePhase", activePhase);
        tag.putBoolean("WasNight", wasNight);
        tag.putLong("NextHorde", nextHordeTick);
        tag.putLong("NextBarrage", nextBarrageTick);
        tag.putBoolean("HordeActive", hordeActive);
        tag.putInt("HordeWave", hordeWave);
        tag.putLong("NextWave", nextWaveTick);
        tag.putFloat("MoonChance", moonChance);
        tag.putInt("DryNights", dryNights);
        tag.putBoolean("Forced", forced);
        return tag;
    }

    @Nullable
    public MoonPhase phase() {
        return MoonPhase.byIndex(activePhase);
    }

    public void setPhase(@Nullable MoonPhase phase) {
        activePhase = phase == null ? -1 : phase.ordinal();
        setDirty();
    }

    public static String name() {
        return NAME;
    }
}
