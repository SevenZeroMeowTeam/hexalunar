package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * 巨型箭矢：超级月相的空降弹幕，缓慢追踪玩家，落地造成大范围伤害。
 */
public class GiantArrowEntity extends AbstractArrow {

    @Nullable
    private Entity tracked;
    private int trackedId;

    public GiantArrowEntity(EntityType<? extends GiantArrowEntity> type, Level level) {
        super(type, level);
        this.pickup = Pickup.DISALLOWED;
        this.setBaseDamage(9.0D);
        this.setNoGravity(false);
    }

    public GiantArrowEntity(Level level, double x, double y, double z) {
        super(ModEntities.GIANT_ARROW.get(), x, y, z, level);
        this.pickup = Pickup.DISALLOWED;
        this.setBaseDamage(9.0D);
    }

    public void setTarget(Entity target) {
        this.tracked = target;
        this.trackedId = target.getId();
        // 朝目标大致方向出手
        Vec3 dir = target.position().add(0, target.getBbHeight() * 0.5D, 0).subtract(position()).normalize();
        this.shoot(dir.x, dir.y, dir.z, 1.35F, 2.2F);
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) return;
        if (tracked == null && trackedId != 0 && level() instanceof net.minecraft.server.level.ServerLevel server) {
            tracked = server.getEntity(trackedId);
        }
        if (tracked == null || !tracked.isAlive()) {
            tracked = null;
            return;
        }
        // 缓速转向目标
        Vec3 dv = this.getDeltaMovement();
        double speed = Math.max(0.75D, Math.min(1.25D, dv.length()));
        Vec3 want = tracked.position().add(0, tracked.getBbHeight() * 0.5D, 0)
                .subtract(this.position()).normalize().scale(speed);
        this.setDeltaMovement(dv.lerp(want, 0.045D));
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("HlcTrack", trackedId);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        trackedId = tag.getInt("HlcTrack");
    }

    @Override
    protected ItemStack getPickupItem() {
        return ItemStack.EMPTY;
    }
}
