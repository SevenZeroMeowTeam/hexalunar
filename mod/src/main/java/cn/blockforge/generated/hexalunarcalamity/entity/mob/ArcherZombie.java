package cn.blockforge.generated.hexalunarcalamity.entity.mob;

import cn.blockforge.generated.hexalunarcalamity.entity.ToxicArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RangedAttackGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import org.jetbrains.annotations.Nullable;

/**
 * 喷吐尸：手持毒弩的僵尸，中距离持续射出带尸毒的箭。
 */
public class ArcherZombie extends Zombie implements RangedAttackMob {

    public ArcherZombie(EntityType<? extends ArcherZombie> type, Level level) {
        super(type, level);
        this.xpReward = 7;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes()
                .add(Attributes.MOVEMENT_SPEED, 0.23D)
                .add(Attributes.MAX_HEALTH, 24.0D)
                .add(Attributes.FOLLOW_RANGE, 56.0D);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(2, new RangedAttackGoal(this, 1.0D, 34, 110));
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.0D, true));
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, LivingEntity.class,
                true, le -> le instanceof net.minecraft.world.entity.player.Player));
    }

    @Nullable
    @Override
    public net.minecraft.world.entity.SpawnGroupData finalizeSpawn(ServerLevelAccessor level,
            DifficultyInstance difficulty, MobSpawnType reason,
            @Nullable net.minecraft.world.entity.SpawnGroupData spawnData,
            @Nullable net.minecraft.nbt.CompoundTag tag) {
        this.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.BOW));
        this.setCanPickUpLoot(false);
        return super.finalizeSpawn(level, difficulty, reason, spawnData, tag);
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean recentlyHit) {
        super.dropCustomDeathLoot(source, looting, recentlyHit);
        if (!level().isClientSide) {
            // 喷吐尸吐的就是尸毒箭，嘴里自然也带着萃取剂（比剧毒骷髅少一些）
            int n = 1 + (this.random.nextFloat() < 0.35F + looting * 0.12F ? 1 : 0);
            for (int i = 0; i < n; i++) {
                ItemEntity drop = this.spawnAtLocation(
                        new ItemStack(cn.blockforge.generated.hexalunarcalamity.registry.ModItems.POISON_REAGENT.get()));
                if (drop != null) drop.setPickUpDelay(20);
            }
        }
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        ToxicArrowEntity arrow = new ToxicArrowEntity(level(), this);
        double dx = target.getX() - getX();
        double dy = target.getEyeY() - getEyeY();
        double dz = target.getZ() - getZ();
        double hd = Math.sqrt(dx * dx + dz * dz);
        arrow.setBaseDamage(3.5D + power);
        arrow.setShotFromCrossbow(true);
        arrow.pickup = AbstractArrow.Pickup.DISALLOWED;
        arrow.shoot(dx, dy + hd * 0.18D, dz, 1.7F,
                (float) (14 - level().getDifficulty().getId() * 3));
        level().addFreshEntity(arrow);
        level().playSound(null, getX(), getY(), getZ(),
                ModSounds.CROSSBOW_SHOT.get(), SoundSource.HOSTILE, 0.8F, 0.85F + this.random.nextFloat() * 0.2F);
    }
}
