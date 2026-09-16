package cn.blockforge.generated.hexalunarcalamity.util;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEffects;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Skeleton;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.level.Level;
import org.joml.Vector3f;

/**
 * 尸毒辅助：施加尸毒效果与爆裂毒雾范围。
 */
public final class ToxicClouds {

    /** 对目标施加尸毒（ undead 天然免疫） */
    public static void applyPoisonTo(LivingEntity target, int ticks, int amplifier) {
        if (target == null) return;
        if (target instanceof Zombie || target instanceof Skeleton) return;
        target.addEffect(new MobEffectInstance(ModEffects.CORPSE_POISON.get(), ticks, amplifier, false, true));
    }

    /** 在指定位置炸开一团毒雾：范围粒子 + 范围尸毒 */
    public static void burst(Level level, Vec3 center, double radius, int ticks, int amplifier) {
        if (level.isClientSide) return;
        AABB box = new AABB(center, center).inflate(radius);
        for (LivingEntity living : level.getEntitiesOfClass(LivingEntity.class, box,
                e -> e.isAlive() && !(e instanceof Zombie) && !(e instanceof Skeleton))) {
            applyPoisonTo(living, ticks, amplifier);
        }
        if (level instanceof ServerLevel server) {
            int rgb = 0x7FA832;
            DustParticleOptions options = new DustParticleOptions(
                    new Vector3f(((rgb >> 16) & 0xFF) / 255F, ((rgb >> 8) & 0xFF) / 255F, (rgb & 0xFF) / 255F), 1.1F);
            server.sendParticles(options, center.x, center.y, center.z,
                    60, radius * 0.5D, 0.5D, radius * 0.5D, 0.02D);
        }
    }

    private ToxicClouds() {}
}
