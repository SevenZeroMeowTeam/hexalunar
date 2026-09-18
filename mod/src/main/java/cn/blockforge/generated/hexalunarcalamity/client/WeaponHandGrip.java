package cn.blockforge.generated.hexalunarcalamity.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;

/**
 * 枪械第一人称「拿在手里」的那一步变换：交给原版做，但**去掉攻击挥动**。
 *
 * <h2>为什么</h2>
 * 原版 {@code ItemInHandRenderer#renderArmWithItem} 对「非空物品 + 没在举枪」一律套两段变换：
 * <ol>
 *   <li>{@code applyItemArmTransform}：把手部基准平移 {@code (±0.56, −0.52 − 0.6·equip, −0.72)}</li>
 *   <li>{@code applyItemArmAttackTransform}：**挥剑用的攻击挥动**，最多 {@code rotX −80°}。
 *       而且 {@code LivingEntity#swing} 会在 swingTime 过半时重新触发 —— 枪是全自动左键连发，
 *       于是枪在手里**不停地上下点头**。</li>
 * </ol>
 * 我们补画的第一人称双手（{@link WeaponArms}）是跟着骨骼 {@code move} 走的，跟不到这段原版挥动，
 * 看起来就是「枪在手心里打滑 / 自己在晃」。
 *
 * <h2>做法</h2>
 * 实现 Forge 的 {@code IClientItemExtensions#applyForgeHandTransform} 并返回 {@code true}
 * （= 已处理，原版直接跳到渲染），其中只保留第一段基准平移；
 * 开火的后坐改由 {@code move} 骨骼推（见各 GeoModel 的 {@code KICK_*}）——
 * 那段位移在 {@link GunFrame} 里被手臂读到，所以**枪动、手一定跟着动**。
 *
 * <p>举弓类姿态（十字弩按住右键的拉弦）仍然交回原版处理，免得把瞄准姿态做丢。
 */
public final class WeaponHandGrip {

    /** 原版手部基准 X（右手 +0.56 / 左手 −0.56），与 {@link WeaponArms#ARM_X} 是同一份数 */
    public static final float BASE_X = 0.56F;
    /** 原版手部基准 Y */
    public static final float BASE_Y = -0.52F;
    /** 原版手部基准 Z */
    public static final float BASE_Z = -0.72F;

    /**
     * 当前这一帧「抬起物品」的进度（0 = 抬到位，1 = 刚切到手上还在抬）。
     * 原版会给物品 {@code −0.6·equip} 的 Y 位移，手臂要用同一个值（见 {@link WeaponArms#baseY()}）。
     */
    public static volatile float equipNow;

    /**
     * @return {@code true} = 已经处理完，让原版跳过它自己那套变换
     */
    public static boolean apply(PoseStack pose, LocalPlayer player, HumanoidArm arm,
                                ItemStack stack, float equip) {
        equipNow = equip;
        // 举弓/拉弦的姿势（十字弩按住右键）交给原版；开镜时手臂本来就隐藏了
        if (player.isUsingItem() && player.getUseItem() == stack
                && stack.getUseAnimation() != UseAnim.NONE) {
            return false;
        }
        int i = arm == HumanoidArm.RIGHT ? 1 : -1;
        pose.translate(i * BASE_X, BASE_Y - 0.6F * equip, BASE_Z);
        return true;
    }

    private WeaponHandGrip() {
    }
}
