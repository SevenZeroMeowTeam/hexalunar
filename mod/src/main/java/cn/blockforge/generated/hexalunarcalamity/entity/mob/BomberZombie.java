package cn.blockforge.generated.hexalunarcalamity.entity.mob;

import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * 自爆尸：贴近玩家后引爆导火索，死亡同样爆炸，炸开一团尸毒雾。
 */
public class BomberZombie extends Zombie {

    private static final int FUSE_TICKS = 30;
    private int fuse = -1;
    private boolean exploded;

    public BomberZombie(EntityType<? extends BomberZombie> type, Level level) {
        super(type, level);
        this.xpReward = 8;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Zombie.createAttributes()
                .add(Attributes.MOVEMENT_SPEED, 0.27D)
                .add(Attributes.MAX_HEALTH, 30.0D)
                .add(Attributes.FOLLOW_RANGE, 48.0D);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.0D, true));
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (level().isClientSide) return;
        LivingEntity target = getTarget();
        if (fuse < 0 && target != null && distanceToSqr(target) < 3.6D * 3.6D) {
            fuse = FUSE_TICKS;
            level().playSound(null, getX(), getY(), getZ(),
                    ModSounds.FUSE.get(), SoundSource.HOSTILE, 1.0F, 1.0F);
        }
        if (fuse >= 0) {
            fuse--;
            if (level() instanceof ServerLevel server) {
                server.sendParticles(ParticleTypes.SMOKE,
                        getX(), getY() + getBbHeight() * 0.75D, getZ(),
                        2, 0.15, 0.2, 0.15, 0.02D);
            }
            if (fuse <= 0) {
                detonate();
            }
        }
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (!level().isClientSide && !exploded) {
            detonate();
        }
    }

    private void detonate() {
        if (exploded || level().isClientSide) return;
        exploded = true;
        Vec3 at = position();
        level().explode(this, at.x, at.y + 0.4D, at.z,
                2.6F, false, Level.ExplosionInteraction.MOB);
        cn.blockforge.generated.hexalunarcalamity.util.ToxicClouds.burst(
                level(), at, 3.2D, 200, 0);
        if (!isRemoved()) this.discard();
    }

    @Override
    protected void playStepSound(net.minecraft.core.BlockPos pos, BlockState state) {
        // 沉重脚步沿用僵尸原版
        super.playStepSound(pos, state);
    }
}
