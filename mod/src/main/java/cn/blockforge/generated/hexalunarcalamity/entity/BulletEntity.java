package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.weapon.Ballistics;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponFx;
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

    /** 命中伤害：10 点 = 5 颗心（原版铁剑 6 / 下界合金剑 8，所以这是一枪很痛的水平） */
    public static final float BULLET_DAMAGE = 10.0F;
    /** 狙击弹（AWP）伤害：24 点 = 12 颗心，一枪基本带走 */
    public static final float SNIPER_DAMAGE = 24.0F;

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

    /**
     * 出膛速度（首个 tick 捕获）—— 用来分辨**狙击弹**：
     * AWP 的初速 6.2，AKM 最高 5.0，取 5.5 为界。
     *
     * <p>为什么不加个布尔字段再同步：弹道在**主客两侧各自独立演算**（客户端画曳光、服务端算命中），
     * 多一个字段就得多一条同步路径，不如直接用它手头已有的、两侧一致的初速来判定。
     */
    private double launchSpeed;

    private boolean sniper() {
        return launchSpeed > 5.5D;
    }

    /** 有效射程内几乎平直；超出有效射程后下坠按超出比例的平方加剧 */
    @Override
    protected float getGravity() {
        boolean sn = sniper();
        double base = sn ? Ballistics.AWP_IN_RANGE_GRAVITY : Ballistics.AKM_IN_RANGE_GRAVITY;
        double range = sn ? Ballistics.AWP_RANGE : Ballistics.AKM_RANGE;
        if (launchOrigin == null) return (float) base;
        double flown = Ballistics.flown(launchOrigin, position());
        return (float) (base + Ballistics.extraGravity(flown, range));
    }

    @Override
    public void tick() {
        if (launchOrigin == null) {
            launchOrigin = position();
            launchSpeed = getDeltaMovement().length();
        }
        super.tick();
        if (level() instanceof ServerLevel server && !isRemoved()) {
            // 曳光：光点每 tick + 热痕隔 tick，拼出连续弹道光带（轻量）
            Vec3 at = position();
            WeaponFx.tracer(server, at);
            if (tickCount % 2 == 0) {
                WeaponFx.tracerHot(server, at);
            }
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
        float damage = sniper() ? SNIPER_DAMAGE : BULLET_DAMAGE;
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
            WeaponFx.impactEntity(server, result.getLocation().add(0.0D, 0.5D, 0.0D));
        }
        level().playSound(null, getX(), getY(), getZ(), ModSounds.HIT.get(), SoundSource.PLAYERS, 0.7F, 0.7F);
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        super.onHitBlock(result);
        if (level() instanceof ServerLevel server) {
            // 火花 + 烟尘 + 命中方块的碎屑（碎屑就是「弹痕」的观感）
            WeaponFx.impactBlock(server, result.getLocation(),
                    level().getBlockState(result.getBlockPos()));
        }
    }
}
