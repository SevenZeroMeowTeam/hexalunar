package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.weapon.Ballistics;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;

/** 十字弩弹射的弩箭：快速、可拾回；40 格内弹道平直，超出后明显下坠 */
public class BoltEntity extends AbstractArrow {

    /** 发射点：首个 tick 捕获（原版 AbstractArrow 重力写死 0.05，这里改为自管） */
    private Vec3 launchOrigin;

    public BoltEntity(EntityType<? extends BoltEntity> type, Level level) {
        super(type, level);
        this.pickup = Pickup.ALLOWED;
        this.setBaseDamage(7.5D);
        this.setNoGravity(true);
    }

    public BoltEntity(Level level, LivingEntity owner) {
        super(ModEntities.BOLT.get(), owner, level);
        this.pickup = Pickup.ALLOWED;
        this.setBaseDamage(7.5D);
        this.setNoGravity(true);
        // AbstractArrow 的这个字段用于命中播放（原版弩箭设的也是 CROSSBOW_HIT），
        // 射击声由 CrossbowWeaponItem / ArcherZombie 在发射瞬间显式播放
        this.setSoundEvent(ModSounds.CROSSBOW_HIT.get());
    }

    @Override
    public void tick() {
        if (launchOrigin == null) launchOrigin = position();
        super.tick();
        if (isRemoved() || inGround || isNoPhysics()) return;
        double flown = Ballistics.flown(launchOrigin, position());
        double gravity = getOwner() instanceof Player
                ? Ballistics.BOLT_IN_RANGE_GRAVITY : Ballistics.VANILLA_ARROW_GRAVITY;
        gravity += Ballistics.extraGravity(flown, Ballistics.BOLT_RANGE);
        Vec3 mv = getDeltaMovement();
        setDeltaMovement(mv.x, mv.y - gravity, mv.z);
    }

    @Override
    protected ItemStack getPickupItem() {
        return new ItemStack(ModItems.CROSSBOW_BOLT.get());
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        if (result.getEntity() instanceof LivingEntity && level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.SMALL_FLAME,
                    result.getLocation().x, result.getLocation().y, result.getLocation().z,
                    6, 0.1, 0.1, 0.1, 0.05D);
        }
    }
}
