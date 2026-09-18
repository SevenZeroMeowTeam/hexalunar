package cn.blockforge.generated.hexalunarcalamity.moon;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.PlayerSleepInBedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * 月相给玩家与世界的「祝福 / 灾祸」——服务端每 tick 推进（r74）。
 *
 * <ul>
 *   <li><b>蓝月 / 超级蓝月</b>：给玩家<b>幸运</b>（蓝月 = 幸运 I、超级蓝月 = 幸运 II），
 *       一直续到天亮。僵尸**没有任何加成**（以前的蓝月移速加成已删除）。</li>
 *   <li><b>黄月 / 超级黄月</b>：每隔 {@link MoonPhase#cropTickInterval()} tick 催一次玩家附近的作物
 *       （超级黄月更快），**没有其他加成**（以前的掉落翻倍已删除）。</li>
 *   <li><b>血月 / 超级血月</b>：玩家**不能睡觉**；天亮时尸潮自动收尾 ——
 *       标记为尸潮的亡灵清掉，只留下少量在原地徘徊，白天**不会烧起来**。</li>
 * </ul>
 *
 * <p>尸潮本体（分 4 波）在 {@link MoonManager}；这里只管「月相附带的持续效果」。
 */
@Mod.EventBusSubscriber
public final class MoonBlessings {

    /** 幸运/防火这类效果每次续多少 tick（比刷新间隔长，才不会闪烁） */
    private static final int LUCK_REFRESH = 40;
    private static final int LUCK_DURATION = 300;
    /** 白天给残留亡灵续的防火时长 */
    private static final int DAY_FIRE_RESIST = 600;

    /** 天亮时每个玩家附近最多留下的徘徊者数量 */
    public static final int DAWN_WANDERERS = 4;

    // ------------------------------------------------------------------ 每 tick

    @SubscribeEvent
    public static void onLevelTick(TickEvent.LevelTickEvent event) {
        if (event.phase != TickEvent.Phase.END || event.level.isClientSide) return;
        if (!(event.level instanceof ServerLevel server) || server.dimension() != Level.OVERWORLD) {
            return;
        }
        MoonPhase phase = MoonManager.current(server);
        long time = server.getGameTime();
        boolean day = !server.isNight();

        // 白天：尸潮残留（含被留下的少量徘徊者）不许烧起来
        if (day && time % 20L == 0L) {
            keepWanderersAlive(server);
        }
        if (phase == null) return;

        // 蓝月：给玩家幸运（僵尸没份）
        int luck = phase.luckAmplifier();
        if (luck >= 0 && time % LUCK_REFRESH == 0L) {
            for (ServerPlayer sp : server.players()) {
                sp.addEffect(new MobEffectInstance(MobEffects.LUCK, LUCK_DURATION, luck,
                        true, false));
            }
        }

        // 黄月：催作物
        int interval = phase.cropTickInterval();
        if (interval > 0 && time % interval == 0L) {
            for (ServerPlayer sp : server.players()) {
                tickCropsAround(server, sp);
            }
        }
    }

    // ------------------------------------------------------------------ 黄月：加速作物

    /**
     * 在玩家附近随机抽几处作物，直接替它们跑一次原版的 {@code randomTick}
     * —— 等价于"这一格被随机刻到了"，所以生长速度变成原来的若干倍，而且不需要碰任何
     * 作物实现（小麦/胡萝卜/马铃薯/甜菜/树苗都吃这一套）。
     */
    private static void tickCropsAround(ServerLevel level, ServerPlayer player) {
        RandomSource rand = level.getRandom();
        BlockPos center = player.blockPosition();
        int radius = 18;
        for (int i = 0; i < 24; i++) {
            int x = center.getX() + rand.nextInt(radius * 2 + 1) - radius;
            int z = center.getZ() + rand.nextInt(radius * 2 + 1) - radius;
            int y = center.getY() + rand.nextInt(9) - 4;
            BlockPos pos = new BlockPos(x, y, z);
            BlockState state = level.getBlockState(pos);
            if (!state.is(BlockTags.CROPS) && !state.is(BlockTags.SAPLINGS)) continue;
            state.randomTick(level, pos, rand);
        }
    }

    // ------------------------------------------------------------------ 血月：不能睡觉

    @SubscribeEvent
    public static void onSleep(PlayerSleepInBedEvent event) {
        Player player = event.getEntity();
        if (!(player.level() instanceof ServerLevel server)) return;
        MoonPhase phase = MoonManager.current(server);
        if (phase == null || !phase.isBlood()) return;
        event.setResult(Player.BedSleepingProblem.NOT_POSSIBLE_NOW);
        player.displayClientMessage(Component.translatable("moon.hexalunar_calamity.no_sleep")
                .withStyle(net.minecraft.ChatFormatting.RED), true);
    }

    // ------------------------------------------------------------------ 白天：残留不烧、自动清除

    /** 尸潮标记（写在实体 ForgeData 上；MoonManager 生成尸潮时打） */
    public static final String TAG_HORDE = "HlcHorde";

    /** 找尸潮亡灵时的搜索半径（尸潮都是围着玩家刷的，不用扫全图） */
    private static final double SEARCH_RANGE = 160.0D;

    /** 附近所有打了尸潮标记的亡灵 */
    private static java.util.List<Mob> hordeMobs(ServerLevel level) {
        java.util.List<Mob> out = new java.util.ArrayList<>();
        for (ServerPlayer sp : level.players()) {
            for (Mob mob : level.getEntitiesOfClass(Mob.class,
                    sp.getBoundingBox().inflate(SEARCH_RANGE),
                    m -> m.getPersistentData().getBoolean(TAG_HORDE))) {
                if (!out.contains(mob)) out.add(mob);
            }
        }
        return out;
    }

    /** 慢慢清掉白天残留的尸潮亡灵：每个玩家附近只留 {@link #DAWN_WANDERERS} 个 */
    public static void dawnCleanup(ServerLevel level) {
        java.util.List<Mob> tagged = hordeMobs(level);
        if (tagged.isEmpty()) return;
        var players = level.players();
        int keepTotal = Math.max(DAWN_WANDERERS, DAWN_WANDERERS * players.size());
        // 离玩家最近的若干个留下来徘徊，其余直接清掉
        tagged.sort((a, b) -> Double.compare(nearestPlayerDist(a, players),
                nearestPlayerDist(b, players)));
        for (int i = 0; i < tagged.size(); i++) {
            Mob mob = tagged.get(i);
            if (i < keepTotal && !players.isEmpty()) {
                mob.getPersistentData().putBoolean(TAG_HORDE, false);   // 成为「徘徊者」
            } else {
                mob.discard();
            }
        }
    }

    private static double nearestPlayerDist(Mob mob, java.util.List<ServerPlayer> players) {
        double best = Double.MAX_VALUE;
        for (ServerPlayer sp : players) {
            best = Math.min(best, mob.distanceToSqr(sp));
        }
        return best;
    }

    /** 白天：给尸潮残留灭火 + 防火，白天不燃烧 */
    private static void keepWanderersAlive(ServerLevel level) {
        if (level.isNight()) return;
        for (Mob mob : hordeMobs(level)) {
            mob.clearFire();
            mob.setRemainingFireTicks(0);
            mob.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, DAY_FIRE_RESIST,
                    0, true, false));
        }
    }

    private MoonBlessings() {
    }
}
