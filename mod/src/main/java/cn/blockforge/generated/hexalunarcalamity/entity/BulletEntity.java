package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.weapon.Ballistics;
import net.minecraft.world.phys.Vec3;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/**
 * 7.62x39 步枪弹：几乎平直的高初速弹道，命中伤害高、附带强击退。
 */
public class BulletEntity extends ThrowableItemProjectile {

    public BulletEntity(EntityType<? extends BulletEntity> type, Level level) {
        super(type, level);
    }

    public BulletEntity(Level level, LivingEntity shooter) {
        super(ModEntities.BULLET.get(), shooter, level);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.AMMO_762.get();
    }

    /** 发射点：首个 tick 捕获，主客侧各自以同步到的出生点起算，弹道一致 */
    private Vec3 launchOrigin;

    /** 有效射程内几乎平直；超过 60 格后下坠按超出比例的平方加剧 */
    @Override
    protected float getGravity() {
        if (launchOrigin == null) return (float) Ballistics.AKM_IN_RANGE_GRAVITY;
        double flown = Ballistics.flown(launchOrigin, position());
        return (float) (Ballistics.AKM_IN_RANGE_GRAVITY
                + Ballistics.extraGravity(flown, Ballistics.AKM_RANGE));
    }

    @Override
    public void tick() {
        if (launchOrigin == null) launchOrigin = position();
        super.tick();
        if (level() instanceof ServerLevel server && !isRemoved()) {
            server.sendParticles(ParticleTypes.SMALL_FLAME,
                    getX(), getY(), getZ(), 1, 0.01, 0.01, 0.01, 0.0);
        }
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (!level().isClientSide) {
            this.discard();
        }
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        Entity hit = result.getEntity();
        float damage = 9.0F;
        LivingEntity attacker = getOwner() instanceof LivingEntity living ? living : null;
        if (attacker != null) {
            hit.hurt(level().damageSources().mobProjectile(this, attacker), damage);
            if (hit instanceof LivingEntity target) {
                target.hurtMarked = true;
                target.setDeltaMovement(target.getDeltaMovement().add(
                        getDeltaMovement().normalize().scale(0.55D)));
            }
        } else {
            hit.hurt(level().damageSources().generic(), damage);
        }
        if (level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.CRIT,
                    result.getLocation().x, result.getLocation().y + 0.5D, result.getLocation().z,
                    8, 0.12, 0.25, 0.12, 0.4D);
        }
        level().playSound(null, getX(), getY(), getZ(), ModSounds.HIT.get(), SoundSource.PLAYERS, 0.7F, 0.7F);
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        super.onHitBlock(result);
        if (level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.CRIT,
                    result.getLocation().x, result.getLocation().y, result.getLocation().z,
                    6, 0.1, 0.1, 0.1, 0.3D);
        }
    }
}
