package cn.blockforge.generated.hexalunarcalamity.entity.mob;

import cn.blockforge.generated.hexalunarcalamity.entity.ToxicArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.util.ToxicClouds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Skeleton;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * 剧毒骷髅：射出附着尸毒的骨箭，死亡时躯体炸开毒雾并掉落毒剂。
 */
public class ToxicSkeleton extends Skeleton {

    public ToxicSkeleton(EntityType<? extends ToxicSkeleton> type, Level level) {
        super(type, level);
        this.xpReward = 9;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Skeleton.createAttributes()
                .add(Attributes.MAX_HEALTH, 30.0D)
                .add(Attributes.FOLLOW_RANGE, 60.0D);
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        ToxicArrowEntity arrow = new ToxicArrowEntity(level(), this);
        double dx = target.getX() - getX();
        double dy = target.getEyeY() - getEyeY();
        double dz = target.getZ() - getZ();
        double hd = Math.sqrt(dx * dx + dz * dz);
        arrow.setBaseDamage(3.0D + power * 1.5D);
        arrow.pickup = AbstractArrow.Pickup.DISALLOWED;
        arrow.shoot(dx, dy + hd * 0.2D, dz, 1.6F,
                (float) (20 - level().getDifficulty().getId() * 4));
        level().addFreshEntity(arrow);
        level().playSound(null, getX(), getY(), getZ(),
                ModSounds.BOW_SHOT.get(), SoundSource.HOSTILE, 1.0F, 0.8F);
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean recentlyHit) {
        super.dropCustomDeathLoot(source, looting, recentlyHit);
        if (!level().isClientSide) {
            int n = 1 + (this.random.nextFloat() < 0.45F + looting * 0.15F ? 1 : 0);
            for (int i = 0; i < n; i++) {
                ItemEntity drop = this.spawnAtLocation(new ItemStack(ModItems.POISON_REAGENT.get()));
                if (drop != null) drop.setPickUpDelay(20);
            }
            // 死亡毒雾：近距离击杀会被殃及
            if (source.getEntity() instanceof LivingEntity attacker
                    && attacker.distanceTo(this) < 4.0D) {
                ToxicClouds.burst(level(), position(), 2.0D, 120, 0);
                level().playSound(null, getX(), getY(), getZ(),
                        ModSounds.TOXIC_BURST.get(), SoundSource.HOSTILE, 0.8F, 1.1F);
            }
        }
    }
}
