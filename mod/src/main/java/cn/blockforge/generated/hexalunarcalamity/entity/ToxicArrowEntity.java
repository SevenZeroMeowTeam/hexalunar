package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.util.ToxicClouds;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;

/**
 * 毒雾箭：命中生物时施加尸毒，命中方块时可能散出一小团毒雾。
 */
public class ToxicArrowEntity extends AbstractArrow {

    public ToxicArrowEntity(EntityType<? extends ToxicArrowEntity> type, Level level) {
        super(type, level);
        this.pickup = Pickup.DISALLOWED;
        this.setBaseDamage(3.0D);
    }

    public ToxicArrowEntity(Level level, LivingEntity owner) {
        super(ModEntities.TOXIC_ARROW.get(), owner, level);
        this.pickup = Pickup.DISALLOWED;
        this.setBaseDamage(3.0D);
        // 基类构造时 soundEvent 已固定为普通箭命中声（此时还没标 ShotFromCrossbow），
        // 这里显式覆盖：毒弩箭与玩家弩箭统一用自制十字弓命中音
        this.setSoundEvent(ModSounds.CROSSBOW_HIT.get());
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        if (result.getEntity() instanceof LivingEntity target) {
            ToxicClouds.applyPoisonTo(target, 160 + this.random.nextInt(80), 0);
        }
    }

    @Override
    protected ItemStack getPickupItem() {
        return ItemStack.EMPTY;
    }
}
