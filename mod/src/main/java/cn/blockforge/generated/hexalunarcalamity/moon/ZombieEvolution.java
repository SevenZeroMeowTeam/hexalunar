package cn.blockforge.generated.hexalunarcalamity.moon;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.Level;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.function.Supplier;

/**
 * 僵尸进化：**时间越久，进化概率越高、能进化出的档次越强**。
 *
 * <p>两种触发方式：
 * <ol>
 *   <li><b>生成即进化</b>：自然生成的原版僵尸按当前天数掷骰，命中就换成进化体
 *       （概率从第 1 天的 3% 每天 +1.4%，上限 55%）；</li>
 *   <li><b>存活进化</b>：已存在且存活够久的原版僵尸，每 8 秒在玩家 48 格内掷一次骰，
 *       命中就原地"变异"（概率第 1 天 1.2%，每天 +0.6%，上限 30%）。</li>
 * </ol>
 *
 * <p>档次按天数解锁，抽签时低档权重更高（越晚越容易往上走）：
 * 弓箭手(第2天) → 爆破手(第4天) → 油桶兵(第7天) → 巨人(第11天)。
 *
 * <p>实现注意：进化体不能直接在 {@code FinalizeSpawn} / {@code EntityJoinLevelEvent} 里生成
 * （前者实体还没进世界，后者正在 add 实体、嵌套 add 会踩到实体列表），所以用
 * {@code server.execute(...)} 推迟到本 tick 收尾时替换，并带上黑烟/冷焰/音效。
 */
@Mod.EventBusSubscriber
public final class ZombieEvolution {

    /** 待进化标记（写在实体 ForgeData 上，进世界后再替换） */
    private static final String TAG_PENDING = "HlcPendingEvolve";

    /** 生成即进化：基础概率 / 每天增幅 / 上限 */
    private static final float BASE_SPAWN_CHANCE = 0.03F;
    private static final float SPAWN_GAIN_PER_DAY = 0.014F;
    private static final float MAX_SPAWN_CHANCE = 0.55F;

    /** 存活进化：检查间隔 / 基础概率 / 每天增幅 / 上限 */
    private static final int LIVE_INTERVAL = 160;
    private static final float BASE_LIVE_CHANCE = 0.012F;
    private static final float LIVE_GAIN_PER_DAY = 0.006F;
    private static final float MAX_LIVE_CHANCE = 0.30F;
    /** 存活超过这么多 tick（约 5 分钟）才可能原地进化 */
    private static final int LIVE_MIN_AGE = 6000;
    /** 存活进化只检查玩家周围这个半径 */
    private static final double LIVE_RANGE = 48.0D;

    private ZombieEvolution() {
    }

    private static final class Tier {
        final Supplier<EntityType<? extends Zombie>> type;
        final int day;

        Tier(Supplier<EntityType<? extends Zombie>> type, int day) {
            this.type = type;
            this.day = day;
        }
    }

    /** 档次表：天数到点才解锁（用 Supplier 惰性取注册表，别在类初始化时拿） */
    private static final Tier[] TIERS = {
            new Tier(() -> ModEntities.ARCHER_ZOMBIE.get(), 2),
            new Tier(() -> ModEntities.BOMBER_ZOMBIE.get(), 4),
            new Tier(() -> ModEntities.BARREL_ZOMBIE.get(), 7),
            new Tier(() -> ModEntities.GIANT_ZOMBIE.get(), 11),
    };

    /* ---------------------------------------------------------------- 概率 */

    /** 世界天数（第 1 天起） */
    public static long dayOf(Level level) {
        return level.getDayTime() / 24000L + 1L;
    }

    /** 自然生成时直接是进化体的概率 */
    public static float spawnChance(long day) {
        return Mth.clamp(BASE_SPAWN_CHANCE + SPAWN_GAIN_PER_DAY * (day - 1L),
                BASE_SPAWN_CHANCE, MAX_SPAWN_CHANCE);
    }

    /** 存活僵尸每 {@link #LIVE_INTERVAL} tick 的原地进化概率 */
    public static float liveChance(long day) {
        return Mth.clamp(BASE_LIVE_CHANCE + LIVE_GAIN_PER_DAY * (day - 1L),
                BASE_LIVE_CHANCE, MAX_LIVE_CHANCE);
    }

    /** 当前天数已解锁的最高档（0 = 还没解锁任何档） */
    public static int unlockedTiers(long day) {
        int n = 0;
        for (Tier t : TIERS) {
            if (day >= t.day) n++;
        }
        return n;
    }

    /* ---------------------------------------------------------------- 触发 */

    /** 自然生成的原版僵尸 → 打标记，等进世界后再替换 */
    public static void markIfEvolving(ServerLevel server, Zombie zombie, RandomSource rand) {
        if (zombie.getType() != EntityType.ZOMBIE || zombie.isBaby()) return;
        if (zombie.getPersistentData().getBoolean(TAG_PENDING)) return;
        long day = dayOf(server);
        if (rand.nextFloat() < spawnChance(day)) {
            zombie.getPersistentData().putBoolean(TAG_PENDING, true);
        }
    }

    /** 进世界：带标记的僵尸立刻换成进化体（推迟到 tick 收尾，避免嵌套 add 实体） */
    @SubscribeEvent
    public static void onJoinLevel(EntityJoinLevelEvent event) {
        if (event.getLevel().isClientSide()) return;
        if (!(event.getEntity() instanceof Zombie zombie)) return;
        if (!(event.getLevel() instanceof ServerLevel server)) return;
        if (!zombie.getPersistentData().getBoolean(TAG_PENDING)) return;
        zombie.getPersistentData().remove(TAG_PENDING);
        // ServerLevel 本身没有 execute，要从 MinecraftServer 上排队
        server.getServer().execute(() -> evolveInto(server, zombie, true));
    }

    /** 存活进化：每 8 秒在玩家周围掷一次骰（不是每 tick 扫，够轻） */
    @SubscribeEvent
    public static void onLevelTick(TickEvent.LevelTickEvent event) {
        if (event.phase != TickEvent.Phase.END || event.level.isClientSide) return;
        if (!(event.level instanceof ServerLevel server)) return;
        if (server.dimension() != Level.OVERWORLD) return;
        if (server.getGameTime() % LIVE_INTERVAL != 0L) return;
        List<ServerPlayer> players = server.players();
        if (players.isEmpty()) return;

        long day = dayOf(server);
        float chance = liveChance(day);
        RandomSource rand = server.getRandom();
        for (ServerPlayer player : players) {
            if (player.isCreative() || player.isSpectator()) continue;
            for (Zombie zombie : server.getEntitiesOfClass(Zombie.class,
                    player.getBoundingBox().inflate(LIVE_RANGE))) {
                if (zombie.isRemoved()) continue;
                if (zombie.getType() != EntityType.ZOMBIE) continue;
                if (zombie.isBaby() || zombie.tickCount < LIVE_MIN_AGE) continue;
                if (zombie.getPersistentData().getBoolean(TAG_PENDING)) continue;
                if (rand.nextFloat() < chance) {
                    evolveInto(server, zombie, false);
                }
            }
        }
    }

    /* ---------------------------------------------------------------- 进化 */

    /** 按天数抽一个档次：低档权重大，越晚越容易抽到高档 */
    @Nullable
    private static EntityType<? extends Zombie> pick(ServerLevel server, long day, RandomSource rand) {
        int unlocked = unlockedTiers(day);
        if (unlocked <= 0) return null;
        float total = unlocked * (unlocked + 1) / 2.0F;
        float r = rand.nextFloat() * total;
        for (int i = 1; i <= unlocked; i++) {
            r -= (unlocked - i + 1);
            if (r <= 0.0F) {
                return TIERS[i - 1].type.get();
            }
        }
        return TIERS[0].type.get();
    }

    /**
     * 把原版僵尸替换成进化体（同位置、同朝向、继承目标）。
     *
     * @param withFx 是否带烟雾/火苗/音效（自然生成的那次也带，视觉上更明确）
     */
    private static void evolveInto(ServerLevel server, Zombie from, boolean withFx) {
        if (from.isRemoved()) return;
        EntityType<? extends Zombie> type = pick(server, dayOf(server), server.getRandom());
        if (type == null) return;
        Zombie evolved = type.create(server);
        if (evolved == null) return;
        evolved.moveTo(from.getX(), from.getY(), from.getZ(), from.getYRot(), from.getXRot());
        evolved.setYHeadRot(from.getYHeadRot());
        evolved.finalizeSpawn(server, server.getCurrentDifficultyAt(evolved.blockPosition()),
                MobSpawnType.MOB_SUMMONED, null, null);
        if (from.getTarget() != null) {
            evolved.setTarget(from.getTarget());
        }
        if (from.isPersistenceRequired()) {
            evolved.setPersistenceRequired();
        }
        if (!server.addFreshEntity(evolved)) return;

        if (withFx) {
            double x = from.getX();
            double y = from.getY() + from.getBbHeight() * 0.5D;
            double z = from.getZ();
            server.sendParticles(ParticleTypes.LARGE_SMOKE, x, y, z, 6, 0.3D, 0.5D, 0.3D, 0.02D);
            server.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, x, y, z, 8, 0.28D, 0.5D, 0.28D, 0.02D);
            server.sendParticles(ParticleTypes.CRIT, x, y, z, 6, 0.3D, 0.4D, 0.3D, 0.0D);
            server.playSound(null, x, y, z, SoundEvents.ZOMBIE_INFECT, SoundSource.HOSTILE,
                    0.9F, 0.7F + server.getRandom().nextFloat() * 0.15F);
        }
        from.discard();
    }
}
