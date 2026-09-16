package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.weapon.Ballistics;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** 复合弓的穿透箭：pierceLevel 由武器设置；34 格内平直，超出后明显下坠 */
public class PiercingArrowEntity extends AbstractArrow {

    /** 发射点：首个 tick 捕获（原版箭重力写死 0.05，这里改为自管） */
    private Vec3 launchOrigin;

    private boolean toxic;

    public PiercingArrowEntity(EntityType<? extends PiercingArrowEntity> type, Level level) {
        super(type, level);
        this.pickup = Pickup.ALLOWED;
        this.setNoGravity(true);
    }

    public PiercingArrowEntity(Level level, LivingEntity owner) {
        super(ModEntities.COMPOUND_ARROW.get(), owner, level);
        this.pickup = Pickup.ALLOWED;
        this.setNoGravity(true);
    }

    @Override
    public void tick() {
        if (launchOrigin == null) launchOrigin = position();
        super.tick();
        if (isRemoved() || inGround || isNoPhysics()) return;
        double flown = Ballistics.flown(launchOrigin, position());
        double gravity = getOwner() instanceof Player
                ? Ballistics.BOW_IN_RANGE_GRAVITY : Ballistics.VANILLA_ARROW_GRAVITY;
        gravity += Ballistics.extraGravity(flown, Ballistics.BOW_RANGE);
        Vec3 mv = getDeltaMovement();
        setDeltaMovement(mv.x, mv.y - gravity, mv.z);
    }

    public void setToxic(boolean toxic) {
        this.toxic = toxic;
    }

    public boolean isToxic() {
        return toxic;
    }

    @Override
    public void addAdditionalSaveData(net.minecraft.nbt.CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("Toxic", toxic);
    }

    @Override
    public void readAdditionalSaveData(net.minecraft.nbt.CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        toxic = tag.getBoolean("Toxic");
    }

    @Override
    protected void onHitEntity(net.minecraft.world.phys.EntityHitResult result) {
        super.onHitEntity(result);
        if (toxic && result.getEntity() instanceof LivingEntity target) {
            cn.blockforge.generated.hexalunarcalamity.util.ToxicClouds.applyPoisonTo(target, 100, 0);
        }
    }

    @Override
    protected ItemStack getPickupItem() {
        return new ItemStack(toxic
                ? ModItems.POISON_ARROW.get()
                : ModItems.COMPOUND_ARROW.get());
    }
}
