package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.moon.MoonPhase;
import net.minecraft.client.Minecraft;
import org.jetbrains.annotations.Nullable;

/**
 * 客户端月相状态：由网络包写入，供雾色/着色/HUD 读取。
 */
public final class ClientMoonState {

    public static volatile int phaseIndex = -1;
    public static volatile long night = 0L;

    private static int hitTicks = 0;
    private static boolean hitKill = false;

    public static void apply(int idx, long nightCount, Minecraft mc) {
        if (idx != phaseIndex) {
            phaseIndex = idx;
            MoonPhase p = MoonPhase.byIndex(idx);
            if (p != null && mc.player != null) {
                mc.player.playSound(p.alarmSound.get(), 0.9F, p.alarmPitch);
            }
        }
        night = nightCount;
    }

    @Nullable
    public static MoonPhase phase() {
        return MoonPhase.byIndex(phaseIndex);
    }

    public static void showHitMarker(boolean kill) {
        hitTicks = kill ? 18 : 10;
        hitKill = kill;
    }

    public static boolean hitActive() {
        return hitTicks > 0;
    }

    public static boolean hitIsKill() {
        return hitKill;
    }

    public static int hitTicksLeft() {
        return hitTicks;
    }

    public static void onClientTick() {
        if (hitTicks > 0) hitTicks--;
    }

    private ClientMoonState() {}
}
