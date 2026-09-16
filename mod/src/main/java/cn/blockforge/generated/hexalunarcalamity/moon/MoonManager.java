package cn.blockforge.generated.hexalunarcalamity.moon;

import cn.blockforge.generated.hexalunarcalamity.entity.GiantArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.ArcherZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.BarrelZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.BomberZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.GiantZombie;
import cn.blockforge.generated.hexalunarcalamity.net.ModNetwork;
import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import org.jetbrains.annotations.Nullable;

/**
 * 服务端月灾进程：夜晚推进六相轮转、延长超级月相夜晚、驱动战术尸潮与巨型箭矢弹幕。
 */
@Mod.EventBusSubscriber
public final class MoonManager {

    @SubscribeEvent
    public static void onLevelTick(TickEvent.LevelTickEvent event) {
        if (event.phase != TickEvent.Phase.END || event.level.isClientSide) return;
        Level level = event.level;
        if (!(level instanceof ServerLevel server) || level.dimension() != Level.OVERWORLD) return;

        MoonPhaseData data = get(server);
        boolean night = level.isNight();
        MoonPhase phase = data.phase();

        // 夜晚开始：推进到下一个月相
        if (night && !data.wasNight) {
            data.nightCount++;
            MoonPhase next = MoonPhase.forNight(data.nightCount);
            data.setPhase(next);
            data.wasNight = true;
            data.nextHordeTick = level.getGameTime() + 100;
            data.nextBarrageTick = level.getGameTime() + 300;
            if (next != null) {
                announce(server, next);
                ModNetwork.syncToAll(MoonPhase.indexOf(next), data.nightCount);
            }
            data.setDirty();
            return;
        }
        // 白天：月相结束
        if (!night && data.wasNight) {
            data.wasNight = false;
            data.setPhase(null);
            ModNetwork.syncToAll(-1, data.nightCount);
            data.setDirty();
            return;
        }

        if (!night || phase == null) return;

        // 超级月相：延长夜晚（每 tick 回退时间）
        if (phase.superMoon) {
            server.setDayTime(level.getDayTime() - 3L);
        }

        // 战术尸潮
        if (level.getGameTime() >= data.nextHordeTick) {
            data.nextHordeTick = level.getGameTime() + (phase.superMoon ? 90 : 160);
            runHorde(server, phase);
            data.setDirty();
        }

        // 超级月相巨型箭矢弹幕
        if (phase.superMoon && level.getGameTime() >= data.nextBarrageTick) {
            data.nextBarrageTick = level.getGameTime() + 220 + level.random.nextInt(160);
            runBarrage(server);
            data.setDirty();
        }
    }

    private static void announce(ServerLevel level, MoonPhase phase) {
        net.minecraft.ChatFormatting color = switch (phase) {
            case BLOOD, SUPER_BLOOD -> net.minecraft.ChatFormatting.RED;
            case BLUE, SUPER_BLUE -> net.minecraft.ChatFormatting.BLUE;
            default -> net.minecraft.ChatFormatting.GOLD;
        };
        Component title = Component.translatable("moon.title." + phase.id).withStyle(color);
        Component bar = Component.translatable("moon." + phase.id).withStyle(color);
        for (ServerPlayer sp : level.players()) {
            sp.connection.send(new net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket(10, 70, 20));
            sp.connection.send(new net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket(title));
            sp.connection.send(new net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket(bar));
            sp.connection.send(new ClientboundSetActionBarTextPacket(bar));
        }
    }

    /** 在玩家周围生成一波战术尸潮 */
    private static void runHorde(ServerLevel level, MoonPhase phase) {
        RandomSource rand = level.getRandom();
        for (ServerPlayer player : level.players()) {
            if (player.isCreative() || player.isSpectator()) continue;
            if (player.gameMode.getGameModeForPlayer() == GameType.CREATIVE) continue;
            int nearby = level.getEntitiesOfClass(Zombie.class,
                    player.getBoundingBox().inflate(64.0D)).size();
            if (nearby > 28) continue;
            int count = Mth.ceil(phase.spawnMultiplier * (1.0F + rand.nextFloat()));
            for (int i = 0; i < count; i++) {
                BlockPos pos = findSpawnPos(level, player.blockPosition(), 34 + rand.nextInt(24), rand);
                if (pos == null) continue;
                spawnWaveMember(level, phase, pos, rand);
            }
        }
    }

    private static void spawnWaveMember(ServerLevel level, MoonPhase phase, BlockPos pos, RandomSource rand) {
        if (rand.nextFloat() < phase.eliteChance) {
            EntityType<? extends Zombie> special = pickSpecial(rand);
            spawnMob(level, special, pos, MobSpawnType.MOB_SUMMONED);
        } else {
            spawnMob(level, EntityType.ZOMBIE, pos, MobSpawnType.MOB_SUMMONED);
        }
    }

    private static EntityType<? extends Zombie> pickSpecial(RandomSource rand) {
        float r = rand.nextFloat();
        if (r < 0.30F) return ModEntities.BOMBER_ZOMBIE.get();
        if (r < 0.60F) return ModEntities.ARCHER_ZOMBIE.get();
        if (r < 0.85F) return ModEntities.BARREL_ZOMBIE.get();
        return ModEntities.GIANT_ZOMBIE.get();
    }

    @Nullable
    private static <T extends Mob> T spawnMob(ServerLevel level, EntityType<T> type, BlockPos pos, MobSpawnType reason) {
        T mob = type.create(level);
        if (mob == null) return null;
        mob.setPos(pos.getX() + 0.5D, pos.getY(), pos.getZ() + 0.5D);
        mob.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), reason, null, null);
        mob.setPersistenceRequired();
        level.addFreshEntityWithPassengers(mob);
        return mob;
    }

    /** 超级月相：跟踪玩家的巨型箭矢 */
    private static void runBarrage(ServerLevel level) {
        RandomSource rand = level.getRandom();
        for (ServerPlayer player : level.players()) {
            if (player.isCreative() || player.isSpectator()) continue;
            if (!level.canSeeSky(player.blockPosition())) continue;
            if (rand.nextFloat() > 0.75F) continue;
            int count = 1 + (rand.nextFloat() < 0.4F ? 1 : 0);
            for (int i = 0; i < count; i++) {
                double ang = rand.nextDouble() * Math.PI * 2.0D;
                double dist = 26.0D + rand.nextDouble() * 14.0D;
                Vec3 origin = player.position().add(
                        Math.cos(ang) * dist, 46.0D + rand.nextDouble() * 12.0D, Math.sin(ang) * dist);
                GiantArrowEntity arrow = new GiantArrowEntity(level, origin.x, origin.y, origin.z);
                arrow.setTarget(player);
                level.addFreshEntity(arrow);
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    cn.blockforge.generated.hexalunarcalamity.registry.ModSounds.GIANT_ARROW.get(),
                    player.getSoundSource(), 1.6F, 0.8F + rand.nextFloat() * 0.3F);
        }
    }

    /** 在半径内找一个可站立的空气位置 */
    @Nullable
    private static BlockPos findSpawnPos(ServerLevel level, BlockPos center, int radius, RandomSource rand) {
        for (int attempt = 0; attempt < 12; attempt++) {
            double ang = rand.nextDouble() * Math.PI * 2.0D;
            double d = radius * (0.7D + rand.nextDouble() * 0.3D);
            int x = center.getX() + (int) (Math.cos(ang) * d);
            int z = center.getZ() + (int) (Math.sin(ang) * d);
            for (int dy = 14; dy >= -14; dy--) {
                BlockPos pos = new BlockPos(x, center.getY() + dy, z);
                BlockState state = level.getBlockState(pos);
                if (!state.isAir()) break;
                BlockState floor = level.getBlockState(pos.below());
                if (!floor.isAir() && level.isEmptyBlock(pos) && level.isEmptyBlock(pos.above())) {
                    return pos;
                }
            }
        }
        return null;
    }

    public static MoonPhaseData get(ServerLevel level) {
        return (MoonPhaseData) level.getDataStorage().computeIfAbsent(
                MoonPhaseData::load, MoonPhaseData::new, MoonPhaseData.name());
    }

    @Nullable
    public static MoonPhase current(@Nullable ServerLevel level) {
        if (level == null) return null;
        return get(level).phase();
    }

    private MoonManager() {}
}
