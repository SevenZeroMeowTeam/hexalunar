package cn.blockforge.generated.hexalunarcalamity.util;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.net.ModNetwork;
import cn.blockforge.generated.hexalunarcalamity.registry.ModEffects;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * 手雷起爆：
 * <ul>
 *   <li>碎片手雷 —— 走原版爆炸，破片 + 冲击，范围约 6.5 格，中心可秒掉普通感染者；
 *       方块破坏跟随 mobGriefing 规则。</li>
 *   <li>震爆弹 —— 不炸方块、基本不造成伤害，靠强光与巨响让范围内生物
 *       眩晕（几乎走不动）+ 致盲。中间隔着不透明方块时效果大幅衰减，
 *       「躲在墙角后」是有用的。</li>
 * </ul>
 */
public final class GrenadeBlasts {

    /** 碎片手雷：爆炸威力（TNT 为 4.0） */
    public static final float FRAG_POWER = 3.5F;
    /** 震爆弹：有效作用半径 */
    public static final double FLASH_RADIUS = 9.0D;

    private GrenadeBlasts() {}

    /**
     * 在指定位置起爆。
     *
     * @param physical 爆炸的「物理来源」：原版会把这个实体从爆炸伤害里排除，
     *                 所以投掷出去的手雷要传手雷自己，绝不能传投掷者，
     *                 否则「拿着不放超过 5 秒自爆」就炸不到人了。
     * @param thrower  记账用的投掷者：伤害来源归到他头上，击杀统计与命中标记照常生效
     */
    public static void detonate(Level level, Vec3 at, GrenadeItem.Kind kind,
                                @Nullable Entity physical, @Nullable LivingEntity thrower) {
        if (level.isClientSide) return;
        if (kind == GrenadeItem.Kind.FLASH) {
            flashbang(level, at, thrower);
        } else {
            frag(level, at, physical, thrower);
        }
    }

    /** 攥在手里引信烧尽：在掌心起爆，投掷者自己吃满伤害（物理来源给 null，谁都不排除） */
    public static void detonateInHand(Level level, Player holder, GrenadeItem.Kind kind) {
        Vec3 at = holder.getEyePosition().subtract(0.0D, 0.55D, 0.0D);
        detonate(level, at, kind, null, holder);
        holder.setDeltaMovement(holder.getDeltaMovement().multiply(0.4D, 0.5D, 0.4D));
    }

    // ------------------------------------------------------------------ 破片杀伤

    private static void frag(Level level, Vec3 at,
                             @Nullable Entity physical, @Nullable LivingEntity thrower) {
        Entity credit = thrower != null && thrower.isAlive() ? thrower : null;
        // 爆点压在玩家身上时抬到胸口，免得伤害被脚下方块吃掉
        if (credit != null && credit.position().distanceToSqr(at) < 1.0D) {
            at = credit.getEyePosition().subtract(0.0D, 0.35D, 0.0D);
        }
        level.explode(physical, level.damageSources().explosion(physical, credit), null,
                at.x, at.y, at.z, FRAG_POWER, false, Level.ExplosionInteraction.MOB);
        shrapnel(level, at);
    }

    /** 破片四散：纯表现，服务端广播给附近所有客户端 */
    private static void shrapnel(Level level, Vec3 at) {
        if (!(level instanceof ServerLevel server)) return;
        server.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 50, 1.4D, 1.0D, 1.4D, 0.65D);
        server.sendParticles(ParticleTypes.SMOKE, at.x, at.y, at.z, 24, 0.9D, 0.7D, 0.9D, 0.05D);
        server.sendParticles(ParticleTypes.POOF, at.x, at.y, at.z, 12, 0.6D, 0.5D, 0.6D, 0.3D);
    }

    // ------------------------------------------------------------------ 震爆

    private static void flashbang(Level level, Vec3 at, @Nullable LivingEntity thrower) {
        if (level instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.FLASH, at.x, at.y, at.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
            server.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y, at.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
            server.sendParticles(ParticleTypes.POOF, at.x, at.y, at.z, 30, 1.2D, 0.9D, 1.2D, 0.25D);
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 40, 1.5D, 1.2D, 1.5D, 0.2D);
            server.sendParticles(ParticleTypes.CLOUD, at.x, at.y, at.z, 25, 1.6D, 0.9D, 1.6D, 0.05D);
        }
        level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE, SoundSource.MASTER, 4.0F, 1.75F);

        double r = FLASH_RADIUS;
        AABB box = new AABB(at, at).inflate(r);
        for (LivingEntity living : level.getEntitiesOfClass(LivingEntity.class, box,
                e -> e.isAlive() && !e.isSpectator())) {
            Vec3 eye = living.getEyePosition();
            float dist = (float) eye.distanceTo(at);
            if (dist > r) continue;
            float falloff = 1.0F - dist / (float) r;
            boolean blocked = occluded(level, eye, at);
            if (blocked) falloff *= 0.25F;

            int blind = (int) (40.0F + 150.0F * falloff);
            int stun = (int) (40.0F + 120.0F * falloff);
            int amp = falloff > 0.72F ? 1 : 0;
            living.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, blind, 0, false, true));
            living.addEffect(new MobEffectInstance(ModEffects.STUN.get(), stun, amp, false, true));
            // 贴脸再吃一点点冲击，不足以致死，只用来打断贴身尸的动作
            if (!blocked && falloff > 0.5F) {
                living.hurt(level.damageSources().sonicBoom(thrower), 1.0F);
            }
            if (living instanceof Player player) {
                ModNetwork.flash(player, falloff);
                // 耳鸣只让被震到的人自己听见
                level.playSound(player, at.x, at.y, at.z, SoundEvents.NOTE_BLOCK_CHIME.value(),
                        SoundSource.MASTER, 1.0F, 1.9F);
            }
        }
    }

    /** 视线是否被不透明方块挡住（0.35 格步进采样，玻璃不挡光） */
    private static boolean occluded(Level level, Vec3 from, Vec3 to) {
        Vec3 delta = to.subtract(from);
        double len = delta.length();
        if (len < 0.6D) return false;
        Vec3 unit = delta.scale(1.0D / len);
        for (double t = 0.35D; t < len - 0.2D; t += 0.35D) {
            Vec3 p = from.add(unit.scale(t));
            BlockPos pos = BlockPos.containing(p.x, p.y, p.z);
            if (level.getBlockState(pos).isSolidRender(level, pos)) return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ 引信与压杆表现

    /** 引信点燃 / 飞行途中：冒一点烟和火星 */
    public static void fuseSparks(Level level, Vec3 at) {
        if (!(level instanceof ServerLevel server)) return;
        server.sendParticles(ParticleTypes.SMOKE, at.x, at.y + 0.05D, at.z, 1,
                0.02D, 0.03D, 0.02D, 0.012D);
        if (level.getRandom().nextBoolean()) {
            server.sendParticles(ParticleTypes.SMALL_FLAME, at.x, at.y + 0.05D, at.z, 1,
                    0.02D, 0.02D, 0.02D, 0.0D);
        }
    }

    /** 出手瞬间压杆 / 保险销崩飞 */
    public static void spoonFlyOff(Level level, Vec3 at) {
        if (!(level instanceof ServerLevel server)) return;
        server.sendParticles(ParticleTypes.END_ROD, at.x, at.y, at.z, 14, 0.15D, 0.15D, 0.15D, 0.12D);
        server.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 10, 0.2D, 0.2D, 0.2D, 0.35D);
        server.sendParticles(ParticleTypes.POOF, at.x, at.y, at.z, 4, 0.1D, 0.1D, 0.1D, 0.05D);
    }
}
