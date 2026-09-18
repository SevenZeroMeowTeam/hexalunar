package cn.blockforge.generated.hexalunarcalamity.moon;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraftforge.event.entity.living.MobSpawnEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * 月相对自然生成的影响（r74 精简）。
 *
 * <p>蓝月移速、黄月掉落这两项加成已删除 —— 蓝月只给玩家幸运、黄月只管催作物，
 * 两者都不再给僵尸任何好处。这里只留两件事：
 * <ul>
 *   <li>僵尸进化（与月相无关，只看天数；血月夜里额外随时间增幅）；</li>
 *   <li>血月：自然生成的僵尸有概率带出同伴。</li>
 * </ul>
 */
@Mod.EventBusSubscriber
public final class MoonSpawnEvents {

    /** 血月：自然生成的僵尸会额外带出同伴 */
    @SubscribeEvent
    public static void onFinalizeSpawn(MobSpawnEvent.FinalizeSpawn event) {
        if (!(event.getEntity() instanceof Zombie zombie)) return;
        if (!(event.getLevel() instanceof ServerLevel server)) return;

        // 僵尸进化：与月相无关，只看「过了多少天」——时间越久，进化概率越高
        if (event.getSpawnType() == MobSpawnType.NATURAL) {
            ZombieEvolution.markIfEvolving(server, zombie, server.getRandom());
        }

        MoonPhase phase = MoonManager.current(server);
        if (phase == null) return;

        // 血月：自然生成的僵尸有概率带出同伴
        var rand = server.getRandom();
        if (phase.boostsSpawns() && event.getSpawnType() == MobSpawnType.NATURAL
                && !zombie.isBaby() && rand.nextFloat() < 0.22F * phase.spawnMultiplier) {
            float ang = rand.nextFloat() * Mth.TWO_PI;
            double dx = zombie.getX() + Mth.cos(ang) * 2.2D;
            double dz = zombie.getZ() + Mth.sin(ang) * 2.2D;
            Zombie extra = EntityType.ZOMBIE.create(server);
            if (extra != null) {
                extra.setPos(dx, zombie.getY(), dz);
                extra.finalizeSpawn(server, server.getCurrentDifficultyAt(extra.blockPosition()),
                        MobSpawnType.NATURAL, null, null);
                server.addFreshEntity(extra);
            }
        }
    }

    private MoonSpawnEvents() {}
}
