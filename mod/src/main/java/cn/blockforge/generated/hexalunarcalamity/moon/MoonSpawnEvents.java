package cn.blockforge.generated.hexalunarcalamity.moon;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.Level;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.event.entity.living.MobSpawnEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** 月相对自然生成与掉落的影响 */
@Mod.EventBusSubscriber
public final class MoonSpawnEvents {

    private static final String BLUE_SPEED_MODIFIER = "hexalunar_calamity.blue_moon_speed";

    /** 蓝月提高僵尸速度；血月额外增加僵尸数量 */
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

        if (phase.boostsSpeed() && phase.speedBonus > 0.0F) {
            AttributeInstance speed = zombie.getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null && !hasNamedModifier(speed)) {
                speed.addPermanentModifier(new AttributeModifier(BLUE_SPEED_MODIFIER,
                        phase.speedBonus, AttributeModifier.Operation.MULTIPLY_TOTAL));
            }
        }

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

    private static boolean hasNamedModifier(AttributeInstance instance) {
        for (AttributeModifier modifier : instance.getModifiers()) {
            if (BLUE_SPEED_MODIFIER.equals(modifier.getName())) return true;
        }
        return false;
    }

    /** 黄月提升掉落 */
    @SubscribeEvent
    public static void onDrops(LivingDropsEvent event) {
        if (!(event.getEntity() instanceof Zombie)) return;
        Level level = event.getEntity().level();
        if (!(level instanceof ServerLevel server)) return;
        MoonPhase phase = MoonManager.current(server);
        if (phase == null || !phase.boostsDrops()) return;
        float chance = (phase.dropMultiplier - 1.0F) * 0.6F;
        for (ItemEntity drop : event.getDrops()) {
            if (level.random.nextFloat() < chance) {
                var stack = drop.getItem();
                stack.setCount(Math.min(stack.getMaxStackSize(), stack.getCount() * 2));
            }
        }
    }

    private MoonSpawnEvents() {}
}
