package cn.blockforge.generated.hexalunarcalamity.entity.mob;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.Level;

/**
 * 巨尸：体型放大的暴君级僵尸，只在超级月相的尸潮中露面。
 */
public class GiantZombie extends Zombie {

    public GiantZombie(EntityType<? extends GiantZombie> type, Level level) {
        super(type, level);
        this.xpReward = 20;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes()
                .add(Attributes.MAX_HEALTH, 130.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.16D)
                .add(Attributes.ATTACK_DAMAGE, 11.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9D);
    }

    @Override
    public boolean canBreakDoors() {
        return true;
    }

    @Override
    public int getExperienceReward() {
        return 20;
    }
}
