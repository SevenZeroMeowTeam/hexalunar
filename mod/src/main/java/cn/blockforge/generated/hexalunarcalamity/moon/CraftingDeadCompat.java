package cn.blockforge.generated.hexalunarcalamity.moon;

import net.minecraft.world.level.Level;
import net.minecraftforge.fml.ModList;
import org.jetbrains.annotations.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Method;

/**
 * ★★ r102：与 <b>Crafting Dead Survival</b> 的月相同步（软依赖，缺失时自动退回本模组自己的轮转）。
 *
 * <h2>为什么要同步</h2>
 * Crafting Dead Survival（modId {@code craftingdeadsurvival}）自己有一套**同名同构**的月相：
 * <pre>
 *   MoonEventType: NONE / BLOOD_MOON / BLUE_MOON / YELLOW_MOON
 *                  / SUPER_BLOOD_MOON / SUPER_BLUE_MOON / SUPER_YELLOW_MOON
 *   MoonEventType.forDay(day)  =  day % 28: 6=蓝月 7=超级蓝月 13=血月 20=黄月 21=超级黄月 27=超级血月，其余 NONE
 *   ApocalypseManager.getMoonEvent(Level)   ← 还会参考它自己的 /moon 手动指令
 *   MoonDataHolder.getEventType()           ← 客户端（已由 SyncMoonDataMessage 同步）
 * </pre>
 * 如果两边各转各的，玩家会在它 HUD 上看到"月相: 满月"、在我们 HUD 上看到"黄月"（用户反馈），
 * 天上的颜色也对不上。所以：**装了 CD 时，今夜月相完全以 CD 为准**。
 *
 * <h2>怎么做到"软依赖"</h2>
 * 不把它写进 build.gradle 的依赖（玩家可能不装/换版本），全部走反射；
 * 找不到类/方法就 {@link #available()} 返回 false，调用方照常走自己的逻辑。
 */
public final class CraftingDeadCompat {

    private static final Logger LOGGER = LoggerFactory.getLogger("hexalunar_calamity");
    private static final String MOD_ID = "craftingdeadsurvival";
    private static final String APOCALYPSE = "com.craftingdead.survival.world.moon.ApocalypseManager";

    /** null = 还没探测过 */
    private static Boolean available;
    @Nullable
    private static Method getMoonEvent;
    /** 只在第一次成功同步时打一条日志，避免刷屏 */
    private static boolean loggedOnce;

    /** CD 在不在、接口能不能用（结果缓存） */
    public static boolean available() {
        if (available != null) return available;
        try {
            if (!ModList.get().isLoaded(MOD_ID)) {
                available = false;
                return false;
            }
            Class<?> am = Class.forName(APOCALYPSE);
            getMoonEvent = am.getMethod("getMoonEvent", Level.class);
            available = true;
            LOGGER.info("[HLCMOON] 检测到 Crafting Dead Survival —— 月相将跟随它（{}#getMoonEvent）", APOCALYPSE);
        } catch (Throwable t) {
            available = false;
            LOGGER.info("[HLCMOON] 没找到 Crafting Dead Survival 的月相接口，使用本模组自己的轮转：{}",
                    t.toString());
        }
        return available;
    }

    /**
     * 今夜 CD 认的月相。
     *
     * @return 对应到本模组的 {@link MoonPhase}；CD 说 NONE（或者反射失败）时返回 {@code null}
     */
    @Nullable
    public static MoonPhase phase(Level level) {
        if (!available() || getMoonEvent == null || level == null) return null;
        try {
            Object event = getMoonEvent.invoke(null, level);
            if (event == null) return null;
            String name = ((Enum<?>) event).name();
            MoonPhase mapped = map(name);
            if (!loggedOnce && mapped != null) {
                loggedOnce = true;
                LOGGER.info("[HLCMOON] 月相已与 Crafting Dead 同步：{} ⇒ {}", name, mapped.zhName);
            }
            return mapped;
        } catch (Throwable t) {
            // 反射失败（版本变了）：降级为自己轮转，别影响游戏
            available = false;
            LOGGER.warn("[HLCMOON] 读取 Crafting Dead 月相失败，退回本模组轮转：{}", t.toString());
            return null;
        }
    }

    /** CD 的枚举名 → 本模组的月相（NONE / 未知 ⇒ null） */
    @Nullable
    private static MoonPhase map(String name) {
        return switch (name) {
            case "BLOOD_MOON" -> MoonPhase.BLOOD;
            case "BLUE_MOON" -> MoonPhase.BLUE;
            case "YELLOW_MOON" -> MoonPhase.YELLOW;
            case "SUPER_BLOOD_MOON" -> MoonPhase.SUPER_BLOOD;
            case "SUPER_BLUE_MOON" -> MoonPhase.SUPER_BLUE;
            case "SUPER_YELLOW_MOON" -> MoonPhase.SUPER_YELLOW;
            default -> null;
        };
    }

    private CraftingDeadCompat() {
    }
}
