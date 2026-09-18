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
