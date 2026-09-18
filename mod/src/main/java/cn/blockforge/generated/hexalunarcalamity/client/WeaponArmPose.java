package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * 第三人称手臂姿态。
 *
 * <p>原版 {@code PlayerRenderer} 只认「是不是原版弓/弩/三叉戟」来决定手臂姿势，模组物品
 * 一律走 {@code ITEM}（单手垂着），看着像端着个板砖。这里通过
 * {@link IClientItemExtensions#getArmPose} 把它们映射到最接近的原版姿势：
 * <ul>
 *   <li>步枪 / 弩：双手持握（{@code CROSSBOW_HOLD}），瞄准时 {@code CROSSBOW_CHARGE}</li>
 *   <li>手雷已拔销 / 拔销中：{@code THROW_SPEAR}（抬手准备扔）</li>
 * </ul>
 * 复合弓不用管：它用 {@code UseAnim.BOW}，原版自己会给 {@code BOW_AND_ARROW}。
 */
public final class WeaponArmPose implements IClientItemExtensions {

    private final WeaponAnim.Kind kind;

    public static final WeaponArmPose AKM = new WeaponArmPose(WeaponAnim.Kind.AKM);
    public static final WeaponArmPose CROSSBOW = new WeaponArmPose(WeaponAnim.Kind.CROSSBOW);
    public static final WeaponArmPose BOW = new WeaponArmPose(WeaponAnim.Kind.BOW);
    public static final WeaponArmPose GRENADE = new WeaponArmPose(WeaponAnim.Kind.GRENADE);

    private WeaponArmPose(WeaponAnim.Kind kind) {
        this.kind = kind;
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        boolean using = entity.isUsingItem() && entity.getUseItem() == stack;
        return switch (kind) {
            case AKM -> using ? HumanoidModel.ArmPose.CROSSBOW_CHARGE : HumanoidModel.ArmPose.CROSSBOW_HOLD;
            case CROSSBOW -> {
                // 上弦时也用「弩蓄力」姿势：原版那套会把左手放在弦上往回拉，正好是上弦动作
                long now = entity.level() == null ? 0L : entity.level().getGameTime();
                yield using || CrossbowWeaponItem.reloading(stack, now)
                        ? HumanoidModel.ArmPose.CROSSBOW_CHARGE : HumanoidModel.ArmPose.CROSSBOW_HOLD;
            }
            case BOW -> using
                    ? HumanoidModel.ArmPose.BOW_AND_ARROW      // 拉弓（原版按 UseAnim.BOW 给的那个姿）
                    : HumanoidModel.ArmPose.ITEM;
            case GRENADE, FLASH -> {
                // ★ 只有**拿着雷的那只手**才抬起来做投掷预姿；另一只保持垂放。
                //   原版 THROW_SPEAR 对左右手都会摆，两只手一起动 —— 就是用户说的「双手投掷」。
                boolean holding = hand == InteractionHand.MAIN_HAND
                        ? entity.getMainHandItem() == stack : entity.getOffhandItem() == stack;
                if (!holding) yield HumanoidModel.ArmPose.ITEM;
                int state = GrenadeItem.state(stack);
                yield state == GrenadeItem.STATE_ARMED || state == GrenadeItem.STATE_PULLING
                        || state == GrenadeItem.STATE_REINSERTING
                        ? HumanoidModel.ArmPose.THROW_SPEAR : null;
            }
        };
    }

    /**
     * 顺手给没被 {@link #AKM} / {@link #CROSSBOW} 覆盖到的武器留个兜底（目前用不到，
     * 只是让 {@code initializeClient} 的调用点统一）。
     */
    public static WeaponArmPose forWeapon(ItemStack stack) {
        if (stack.getItem() instanceof AkmRifleItem) return AKM;
        if (stack.getItem() instanceof CrossbowWeaponItem) return CROSSBOW;
        if (stack.getItem() instanceof CompoundBowItem) return BOW;
        if (stack.getItem() instanceof GrenadeItem) return GRENADE;
        return AKM;
    }
}
