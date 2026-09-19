package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.GunPose;
import cn.blockforge.generated.hexalunarcalamity.weapon.Sights;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import org.joml.Matrix4f;

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
 * 那段位移在 {@link GunFrame} 里被手臂读到，所以**枪动、手一定跟着动**。 *
 * <p>★ r84 起这里还接管「TaCZ 风格持枪姿态」：腰射时给枪身一个往右下、带偏航/倾斜的
 * {@link GunPose} 变换，举枪时线性归零（见 {@link #apply}）。 *
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
     * 允许的最大「重新抬起」量。
     *
     * <p>★★ 原版 {@code ItemInHandRenderer.tick()} 会把 {@code mainHandHeight} 往
     * {@code attackStrengthScale³} 拉，而**每次攻击/开火**都会重置攻击力计数、Forge 的 requip
     * 判定也会插手 ⇒ equip 冲到 1 ⇒ 物品被 {@code −0.6·equip} 整体下拉（最多 0.6 格）。
     * 我们的手臂用同一个 equip（{@link WeaponArms#baseY()}）⇒ **枪和手一起往下沉** ——
     * 就是用户反馈的「发射 / 换弹时物品和手臂下沉」。枪是全自动连发，这种回弹毫无意义，
     * 所以夹到 0.10（最多 0.06 格）：只保留「切枪时枪从下面升上来」那一点点。
     */
    private static final float EQUIP_MAX = 0.10F;

    /** AWP 开火时枪口上抬（模型像素；枪与双手一起抬，由 {@link GunPose} 施加）
     *  ★ r93：已被 {@link #AWP_FIRE_PITCH}（绕手俯仰）取代 —— 单纯的整枪平抬会让枪托跟着往上走，
     *  而用户要的是「枪托微微下沉、枪管微微上抬」。常量留着方便回调。 */
    public static final float AWP_FIRE_LIFT = 2.0F;

    /**
     * ★★ r93：AWP 开火后坐 = **绕手（握把）的俯仰角**（度 × {@code WeaponAnim.recoil}）。
     *
     * <p>正角 = 枪管（前端 −Z）上抬、枪托（后端 +Z）下沉 —— 就是用户要的「枪托微微下沉，
     * 枪管微微上抬」。枢轴取姿态原点（原版手部基准 ≈ 握把），所以两条臂也绕同一点跟着动，
     * 手不会脱开。后坐冲量每档 ≈ 0.42（抵肩）/ 0.6（腰射），乘 6° 约 2.5°~3.6°，再按
     * {@code ×0.55/tick} 衰减 ⇒ 一记短促的「枪口一跳」。
     */
    public static final float AWP_FIRE_PITCH = 6.0F;

    /** {@link #apply} 复用的一块矩阵（客户端渲染单线程，不会并发） */
    private static final Matrix4f SCRATCH = new Matrix4f();
    /** {@link #pushAds} 复用的临时数组 */
    private static final float[] ADS_TMP = new float[3];

    /**
     * 把当前武器的「举枪位移」写进 {@link GunPose}（相机空间、格），手臂与枪都从这里取。
     *
     * <p>★ r85：以前举枪位移是推到 {@code move} 骨骼上的（模型像素），会被动画关键帧遮掉
     * —— AKM 的 {@code reload} 自带 {@code move.position = [0, −1.2, 0] / rotX +7°}，
     * 画面上就是「换弹时枪和手一起往下沉」。现在换成我们自己填的 pose 变换，**一定生效**。
     */
    public static void pushAds(WeaponAnim.Kind gun, ItemStack stack, net.minecraft.world.entity.player.Player player) {
        if (gun == null || player == null) {
            GunPose.clearAds();
            return;
        }
        if (gun == WeaponAnim.Kind.AWP) {
            WeaponMount.awpAds(player, ADS_TMP);
            // ★ r93：后坐改成**绕手俯仰**（枪管微抬 + 枪托微沉），不再是整枪平抬 —— 见 AWP_FIRE_PITCH
            GunPose.setAds(ADS_TMP[0], ADS_TMP[1], ADS_TMP[2], 0.0F, 0.0F,
                    AWP_FIRE_PITCH * WeaponAnim.of(gun).recoil);
        } else if (gun == WeaponAnim.Kind.AKM) {
            int sight = Sights.sight(stack);
            WeaponMount.akmAds(player, sight, ADS_TMP);
            // ★ r88：举枪加一点横滚（TaCZ 机瞷矄准的构图：瞄准线不动，枪身甩向右下、能看到机匣顶）。
            //   横滚绕**眼睛**施加（见 GunPose.matrix 的乘法顺序），所以准星依旧钉在屏幕中心；
            //   带倍镜时不给横滚（镜筒必须正着）。
            GunPose.setAds(ADS_TMP[0], ADS_TMP[1], ADS_TMP[2], 0.0F, WeaponMount.akmAdsRoll(sight));
        } else {
            GunPose.clearAds();          // 十字弩：开镜是整屏遮罩，不需要位移
        }
    }

    /**
     * 走 TaCZ 那套（枪模独立投影 + 腰射姿态）的武器；其它物品返回 null。
     * 复合弓不走：它的持弓/拉弦是另一套调好的变换，叠上去就乱了。
     */
    public static WeaponAnim.Kind gunKind(ItemStack stack) {
        WeaponAnim.Kind kind = WeaponAnim.kindOf(stack);
        return kind == WeaponAnim.Kind.AKM || kind == WeaponAnim.Kind.AWP
                || kind == WeaponAnim.Kind.CROSSBOW ? kind : null;
    }

    /**
     * @return {@code true} = 已经处理完，让原版跳过它自己那套变换
     */
    public static boolean apply(PoseStack pose, LocalPlayer player, HumanoidArm arm,
                                ItemStack stack, float equip) {
        WeaponDiag.applyCalled = true;                           // 诊断：我们的手持变换真的被调用了
        WeaponDiag.renderedItem = stack.getItem();                // 诊断：渲染这一刻手上是什么
        // ★ r96：先把「别的手持渲染留下的残留变换」清掉（TaCZ 的 FirstPersonRenderHandler 会改同一个
        //   事件里的 PoseStack；拿我们的枪时它什么都没画，但改动可能留在栈上）—— 枪与手必须用同一份基准
        WeaponArms.restoreCleanPose(pose);
        equipNow = Math.min(Math.max(equip, 0.0F), EQUIP_MAX);   // ★ 夹掉「开火/换弹下沉」
        // 举弓/拉弦的姿势（十字弩按住右键）交给原版；开镜时手臂本来就隐藏了
        if (player.isUsingItem() && player.getUseItem() == stack
                && stack.getUseAnimation() != UseAnim.NONE) {
            return false;
        }
        int i = arm == HumanoidArm.RIGHT ? 1 : -1;
        pose.translate(i * BASE_X, BASE_Y - 0.6F * equipNow, BASE_Z);
        // ★ TaCZ 风格持枪姿态 + 举枪位移（都在同一块矩阵里，见 {@link GunPose}）：
        //   腰射时枪身往右下并带一点偏航/倾斜，举枪时**旋转归零**并把眼睛贴到镜筒目镜上。
        //   归零是硬要求：AKM / AWP 的对准靠「举枪只做平移」（把照门—准星 / 镜筒光轴顶到屏幕中心）。
        WeaponAnim.Kind gun = gunKind(stack);
        pushAds(gun, stack, player);
        if (gun != null) {
            GunPose.matrix(WeaponAnim.of(gun).aim, SCRATCH);
            pose.mulPoseMatrix(SCRATCH);
        }
        return true;
    }

    private WeaponHandGrip() {
    }
}
