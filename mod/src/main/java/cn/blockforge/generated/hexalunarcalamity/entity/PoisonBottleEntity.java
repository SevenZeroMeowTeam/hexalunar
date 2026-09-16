package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.util.ToxicClouds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;

/**
 * 投掷尸毒瓶：碎裂时释放尸毒雾。
 */
public class PoisonBottleEntity extends ThrowableItemProjectile {

    public PoisonBottleEntity(EntityType<? extends PoisonBottleEntity> type, Level level) {
        super(type, level);
    }

    public PoisonBottleEntity(Level level, LivingEntity shooter) {
        super(ModEntities.POISON_BOTTLE.get(), shooter, level);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.POISON_BOTTLE.get();
    }

    @Override
    protected float getGravity() {
        return 0.06F;
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (!level().isClientSide && !this.isRemoved()) {
            ToxicClouds.burst(level(), position(), 2.4D, 160, 0);
            level().playSound(null, getX(), getY(), getZ(),
                    ModSounds.TOXIC_BURST.get(), SoundSource.BLOCKS, 0.9F, 1.0F);
            this.discard();
        }
    }
}
