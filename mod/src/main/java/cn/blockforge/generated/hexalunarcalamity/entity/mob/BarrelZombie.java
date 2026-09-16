package cn.blockforge.generated.hexalunarcalamity.entity.mob;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.Level;

/**
 * 蛮兵尸：裹着铁皮的重装僵尸，血厚攻高、几乎不惧击退，但行动迟缓。
 */
public class BarrelZombie extends Zombie {

    public BarrelZombie(EntityType<? extends BarrelZombie> type, Level level) {
        super(type, level);
        this.xpReward = 12;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes()
                .add(Attributes.MAX_HEALTH, 90.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.185D)
                .add(Attributes.ATTACK_DAMAGE, 8.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8D)
                .add(Attributes.ARMOR, 8.0D);
    }

    @Override
    public boolean canBreakDoors() {
        return false;
    }
}
