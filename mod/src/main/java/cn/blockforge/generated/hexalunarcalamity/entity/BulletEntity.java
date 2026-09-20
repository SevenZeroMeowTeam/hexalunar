package cn.blockforge.generated.hexalunarcalamity.entity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.weapon.Ballistics;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponFx;
import net.minecraft.world.phys.Vec3;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/**
 * 7.62x39 步枪弹：几乎平直的高初速弹道，命中伤害高、附带强击退。
 */
public class BulletEntity extends ThrowableItemProjectile {

    /** 命中伤害：10 点 = 5 颗心（原版铁剑 6 / 下界合金剑 8，所以这是一枪很痛的水平） */
    public static final float BULLET_DAMAGE = 10.0F;
    /** 狙击弹（AWP）伤害：24 点 = 12 颗心，一枪基本带走 */
    public static final float SNIPER_DAMAGE = 75.0F;
    /**
     * ★ r106：栓动步枪（莫辛-纳甘 7.62x59）伤害 26 —— 直接照 TaCZ 的 {@code kar98_data.json}
     * （{@code bullet.damage = 26}）；介于 AKM（{@link #BULLET_DAMAGE} 10）与 AWP（75）之间。
     */
    public static final float MOSIN_DAMAGE = 26.0F;
    /**
     * ★ r107：Kar98k 伤害 **50**（用户指定）—— 同样打 7.62x59，但初速 5.7 比莫辛的 5.4 高一档，
     * 介于莫辛（26）与 AWP（75）之间。
     */
    public static final float KAR98K_DAMAGE = 50.0F;
    /**
     * ★ r108：M1 加兰德伤害 **22** —— 它是**半自动连射**（每 10 tick 一发）+ 8 发漏夹，
     * 单发刻意低于栓动枪（莫辛 26 / Kar98k 50），靠射速与弹容量取胜。
     */
    public static final float M1_DAMAGE = 22.0F;
    /** ★ r108：半自动步枪的爆头倍率（比栓动枪的 1.85 略低，连射不该一发爆头带走） */
    public static final float SEMI_HEADSHOT_MULTIPLIER = 1.50F;
    /** ★ r106：栓动步枪的爆头倍率 —— TaCZ kar98k 的 {@code head_shot_multiplier = 1.85} */
    public static final float BOLT_HEADSHOT_MULTIPLIER = 1.85F;
    /** ★ r104：爆头倍率（仅狙击弹）—— 75 × 2 = 150，
     *  正常僵尸爆头一枪带走；只有血量特别厚的（比如 CD 进化僵尸）才需要补枪。 */
    public static final float HEADSHOT_MULTIPLIER = 2.0F;

    public BulletEntity(EntityType<? extends BulletEntity> type, Level level) {
        super(type, level);
    }

    public BulletEntity(Level level, LivingEntity shooter) {
        super(ModEntities.BULLET.get(), shooter, level);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.AMMO_762.get();
    }

    /** 发射点：首个 tick 捕获，主客侧各自以同步到的出生点起算，弹道一致 */
    private Vec3 launchOrigin;

    /**
     * 出膛速度（首个 tick 捕获）—— 用来分辨**狙击弹**：
     * AWP 的初速 6.2，AKM 最高 5.0，取 5.5 为界。
     *
     * <p>为什么不加个布尔字段再同步：弹道在**主客两侧各自独立演算**（客户端画曳光、服务端算命中），
     * 多一个字段就得多一条同步路径，不如直接用它手头已有的、两侧一致的初速来判定。
     */
    private double launchSpeed;

    private boolean sniper() {
        return launchSpeed > 5.9D;
    }

    /**
     * ★ r106：**栓动步枪**（莫辛-纳甘 7.62x59，初速 5.4）—— 介于步枪弹与狙击弹之间的第三档。
     *
     * <p>分档全部按「首个 tick 捕获的出膛速度」判（主客两侧一致，不用多加同步字段）。
     * 完整档位表（★ r108 起五档）：
     * <pre>
     *   AKM         ≤5.08   → 10 点
     *   M1 加兰德    5.15   → 22 点（半自动、8 发漏夹）
     *   莫辛-纳甘    5.40   → 26 点（爆头 ×1.85）
     *   Kar98k      5.70   → 50 点（爆头 ×1.85）
     *   AWP         6.20   → 75 点（爆头 ×2.0）
     * </pre>
     */
    private boolean boltRifle() {
        return launchSpeed > 5.30D && launchSpeed <= 5.55D;
    }

    /**
     * ★ r107：**Kar98k 档**（7.62x59，初速 5.7）—— 用户指定「一次击发一发、拉栓抛壳、伤害 50」。
     *
     * <p>它与莫辛是**同一发弹**（{@code AmmoType.RIFLE_762_59}），差别只在装药/枪管给出的初速
     * （5.7 vs 5.4）⇒ 伤害 50 vs 26；弹道仍按 7.62x59 那一组走（见 {@link #getGravity()}）。
     */
    private boolean kar98k() {
        return launchSpeed > 5.55D && launchSpeed <= 5.9D;
    }

    /**
     * ★ r108：**M1 加兰德档**（7.62x61，初速 5.15）—— 半自动连射 + 8 发漏夹，
     * 所以单发伤害比栓动枪低（22），走它自己的弹道组（{@link Ballistics#M1_RANGE} 72 格）。
     */
    private boolean m1Garand() {
        return launchSpeed > 5.08D && launchSpeed <= 5.30D;
    }

    /** 有效射程内几乎平直；超出有效射程后下坠按超出比例的平方加剧 */
    @Override
    protected float getGravity() {
        boolean sn = sniper();
        // ★ r107：Kar98k 与莫辛是同一发 7.62x59 ⇒ 弹道同组（只有伤害/初速不同）
        boolean mo = boltRifle() || kar98k();
        boolean m1 = m1Garand();                                    // ★ r108 7.62x61 自己一组
        double base = sn ? Ballistics.AWP_IN_RANGE_GRAVITY
                : m1 ? Ballistics.M1_IN_RANGE_GRAVITY
                : (mo ? Ballistics.MOSIN_IN_RANGE_GRAVITY : Ballistics.AKM_IN_RANGE_GRAVITY);
        double range = sn ? Ballistics.AWP_RANGE
                : m1 ? Ballistics.M1_RANGE
                : (mo ? Ballistics.MOSIN_RANGE : Ballistics.AKM_RANGE);
        if (launchOrigin == null) return (float) base;
        double flown = Ballistics.flown(launchOrigin, position());
        return (float) (base + Ballistics.extraGravity(flown, range));
    }

    @Override
    public void tick() {
        if (launchOrigin == null) {
            launchOrigin = position();
            launchSpeed = getDeltaMovement().length();
        }
        super.tick();
        if (level() instanceof ServerLevel server && !isRemoved()) {
            // 曳光：光点每 tick + 热痕隔 tick，拼出连续弹道光带（轻量）
            Vec3 at = position();
            WeaponFx.tracer(server, at);
            if (tickCount % 2 == 0) {
                WeaponFx.tracerHot(server, at);
            }
        }
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (!level().isClientSide) {
            this.discard();
        }
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        Entity hit = result.getEntity();
        // ★ r107/r108：Kar98k 档 = 50 点（用户指定），M1 加兰德档 = 22 点（半自动连射）
        float damage = sniper() ? SNIPER_DAMAGE
                : (kar98k() ? KAR98K_DAMAGE
                : (m1Garand() ? M1_DAMAGE
                : (boltRifle() ? MOSIN_DAMAGE : BULLET_DAMAGE)));
        // ★ r104：爆头判定 —— 命中点高于「眼睛略往下」就算爆头（用实体自己的眼高，不硬编码）
        //   ★ r106/r107：栓动步枪（莫辛 / Kar98k）的爆头倍率取 TaCZ kar98k 的 1.85
        //   ★ r108：M1 加兰德是半自动连射 ⇒ 用更低的 1.5（见 SEMI_HEADSHOT_MULTIPLIER）
        if ((sniper() || boltRifle() || kar98k() || m1Garand())
                && result.getLocation().y >= hit.getEyeY() - hit.getBbHeight() * 0.12D) {
            damage *= sniper() ? HEADSHOT_MULTIPLIER
                    : (m1Garand() ? SEMI_HEADSHOT_MULTIPLIER : BOLT_HEADSHOT_MULTIPLIER);
        }
        LivingEntity attacker = getOwner() instanceof LivingEntity living ? living : null;
        if (attacker != null) {
            hit.hurt(level().damageSources().mobProjectile(this, attacker), damage);
            if (hit instanceof LivingEntity target) {
                target.hurtMarked = true;
                target.setDeltaMovement(target.getDeltaMovement().add(
                        getDeltaMovement().normalize().scale(0.55D)));
            }
        } else {
            hit.hurt(level().damageSources().generic(), damage);
        }
        if (level() instanceof ServerLevel server) {
            WeaponFx.impactEntity(server, result.getLocation().add(0.0D, 0.5D, 0.0D));
        }
        level().playSound(null, getX(), getY(), getZ(), ModSounds.HIT.get(), SoundSource.PLAYERS, 0.7F, 0.7F);
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        super.onHitBlock(result);
        if (level() instanceof ServerLevel server) {
            // 火花 + 烟尘 + 命中方块的碎屑（碎屑就是「弹痕」的观感）
            WeaponFx.impactBlock(server, result.getLocation(),
                    level().getBlockState(result.getBlockPos()));
        }
    }
}
