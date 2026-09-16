package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.util.GrenadeBlasts;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * 飞行中的手雷：压杆已经在出手时脱落，引信按剩余 tick 倒计时。
 *
 * <p>撞到人不销毁（会穿过去继续飞），撞到方块则反弹滚落，只有引信烧完才炸。
 */
public class GrenadeEntity extends ThrowableItemProjectile {

    private static final EntityDataAccessor<Integer> DATA_KIND =
            SynchedEntityData.defineId(GrenadeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_FUSE =
            SynchedEntityData.defineId(GrenadeEntity.class, EntityDataSerializers.INT);

    public GrenadeEntity(EntityType<? extends GrenadeEntity> type, Level level) {
        super(type, level);
    }

    public GrenadeEntity(Level level, LivingEntity thrower, GrenadeItem.Kind kind, int fuseTicks) {
        super(ModEntities.GRENADE.get(), thrower, level);
        setOwner(thrower);
        this.entityData.set(DATA_KIND, kind.ordinal());
        this.entityData.set(DATA_FUSE, Math.max(1, fuseTicks));
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_KIND, GrenadeItem.Kind.FRAG.ordinal());
        this.entityData.define(DATA_FUSE, GrenadeItem.FUSE_TICKS);
    }

    @Override
    protected Item getDefaultItem() {
        return kind() == GrenadeItem.Kind.FLASH
                ? ModItems.FLASHBANG.get() : ModItems.FRAG_GRENADE.get();
    }

    @Override
    protected float getGravity() {
        // 比尸毒瓶沉一些，扔出去是抛物线而不是飘
        return 0.09F;
    }

    public GrenadeItem.Kind kind() {
        int i = this.entityData.get(DATA_KIND);
        GrenadeItem.Kind[] all = GrenadeItem.Kind.values();
        return i >= 0 && i < all.length ? all[i] : GrenadeItem.Kind.FRAG;
    }

    public int fuseLeft() {
        return this.entityData.get(DATA_FUSE);
    }

    public void setFuse(int ticks) {
        this.entityData.set(DATA_FUSE, ticks);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide) return;
        int left = fuseLeft() - 1;
        setFuse(left);
        if (left <= 0 || this.tickCount > 400) {
            detonate();
            return;
        }
        // 引信在烧：每隔几 tick 冒一点烟和火星（服务端广播，所有客户端可见）
        if (left % 3 == 0) {
            GrenadeBlasts.fuseSparks(this.level(), this.position());
        }
    }

    @Override
    protected void onHit(HitResult result) {
        if (this.level().isClientSide) return;
        if (result.getType() == HitResult.Type.ENTITY) {
            // 撞到人不停：继续飞，引信说了算
            return;
        }
        if (result.getType() == HitResult.Type.BLOCK) {
            Vec3 mv = this.getDeltaMovement();
            this.setDeltaMovement(mv.multiply(-0.42D, -0.42D, -0.42D));
            if (mv.lengthSqr() > 0.03D) {
                this.level().playSound(null, this.getX(), this.getY(), this.getZ(),
                        net.minecraft.sounds.SoundEvents.TRIDENT_HIT,
                        net.minecraft.sounds.SoundSource.BLOCKS, 0.35F, 1.7F);
            }
        }
    }

    /** 引信烧尽：原地起爆 */
    public void detonate() {
        if (this.level().isClientSide || this.isRemoved()) return;
        // 物理来源是手雷自己：原版会把爆炸的 source 实体排除在伤害之外，
        // 传投掷者会导致「贴脸炸自己」不疼。
        GrenadeBlasts.detonate(this.level(), this.position().add(0.0D, 0.12D, 0.0D),
                kind(), this, getOwner() instanceof LivingEntity l ? l : null);
        this.discard();
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("HlcGrenadeKind", kind().ordinal());
        tag.putInt("HlcGrenadeFuse", fuseLeft());
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("HlcGrenadeKind")) this.entityData.set(DATA_KIND, tag.getInt("HlcGrenadeKind"));
        if (tag.contains("HlcGrenadeFuse")) this.entityData.set(DATA_FUSE, Math.max(1, tag.getInt("HlcGrenadeFuse")));
    }
}
