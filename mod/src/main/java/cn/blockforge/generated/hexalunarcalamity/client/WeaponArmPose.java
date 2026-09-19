package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
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
 *   <li>步枪 / 弩：双手持握（{@code CROSSBOW_HOLD}），瞄准时换成自定义的
 *       {@link #RIFLE_AIM}（两臂抬到肩线、跟着头俯仰 —— TaCZ 那种「把枪端到眼前」）</li>
 *   <li>手雷已拔销 / 拔销中：{@code THROW_SPEAR}（抬手准备扔）</li>
 * </ul>
 * 复合弓不用管：它用 {@code UseAnim.BOW}，原版自己会给 {@code BOW_AND_ARROW}。
 */
public final class WeaponArmPose implements IClientItemExtensions {

    /**
     * ★ TaCZ 风格的**举枪瞄准**姿势（第三人称）。
     *
     * <p>原版弩的 {@code CROSSBOW_CHARGE} 是「上弦」姿势：两臂收到胸前、肘往外撑
     * （{@code xRot = -0.97}），举枪的时候看着像在拉弦而不是瞄准。这个姿势把两臂抬到肩线
     * （{@code xRot = -π/2 + 头俯仰}）、支撑手往内收（{@code yRot} 从 0.60 → 0.50），
     * 就是「双手端枪、枪随视线」的剪影。
     *
     * <p>用 Forge 的 {@code ArmPose.create}（{@code IExtensibleEnum}）新建枚举常量，
     * 不需要 mixin；{@code twoHanded = true} 时原版只会把这个姿势给「持枪那只手」，
     * 所以两条手臂都要在同一个 transformer 里摆（跟原版 {@code animateCrossbowHold} 一样）。
     */
    /**
     * ★★ r95：自定义姿势**必须在模组构造期就建好**，不能等第一次渲染懒加载 —— 见
     * {@link cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity#clientBootstrapping} 的详细说明：
     * javac 给 {@code switch (ArmPose)} 生成的 {@code $SwitchMap} 表按「建表那一刻的
     * {@code values().length}」定长；世界里第一只人形生物（含我们加的僵尸）被渲染时表就定成 10 长，
     * 之后才出现的第 11 个常量（ordinal 10）会让 {@code HumanoidModel.poseRightArm} 的 switch
     * 抛 {@code ArrayIndexOutOfBoundsException: Index 10 out of bounds for length 10} ⇒ 游戏 FATAL。
     *
     * <p>所以：模组构造期（{@code clientBootstrapping = true} 的窗口内）由
     * {@link #initArmPoses()} 主动触碰本类，触发静态初始化、把常量建出来；
     * 一旦本类是被**懒加载**的（窗口已关），就直接退回原版姿势 —— 姿势朴素总比崩游戏好。
     */
    public static final HumanoidModel.ArmPose RIFLE_AIM =
            cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity.clientBootstrapping
                    ? createAimPose()
                    : HumanoidModel.ArmPose.CROSSBOW_HOLD;

    /**
     * ★ r95：构造期引导入口 —— 由 {@code HexaLunarCalamity} 的构造函数在客户端调用。
     *
     * <p>方法体是空的：**调用它本身**就会触发本类的静态初始化，从而在上面的三目里把
     * {@link #RIFLE_AIM} 建出来（那时 {@code clientBootstrapping} 还是 true）。
     */
    public static void initArmPoses() {
        // 故意为空 —— 见上面的说明
    }

    /**
     * 建姿势带兜底：{@code ArmPose.create} 走的是 Forge 的 {@code IExtensibleEnum} 运行时改写，
     * 万一某个环境下没改写成功（或将来 Forge 改了机制）就直接退回原版姿势，别让游戏崩在类加载上。
     */
    private static HumanoidModel.ArmPose createAimPose() {
        try {
            return HumanoidModel.ArmPose.create("HEXALUNAR_RIFLE_AIM", true,
                    (model, entity, arm) -> poseRifleAim(model, entity));
        } catch (Throwable t) {
            // 不再静默：退回原版「双手持握」姿势，并记一条日志，方便一眼看出姿势没生效
            org.slf4j.LoggerFactory.getLogger("hexalunar_calamity").warn(
                    "[hexalunar] 自定义 ArmPose 创建失败，退回 CROSSBOW_HOLD（第三人称举枪姿势会朴素一些）", t);
            return HumanoidModel.ArmPose.CROSSBOW_HOLD;
        }
    }

    /** 两臂抬到肩线、跟着头俯仰；撑手那侧往内收一点扶住护木 */
    private static void poseRifleAim(HumanoidModel<?> model, LivingEntity entity) {
        boolean right = entity.getMainArm() == HumanoidArm.RIGHT;
        int s = right ? 1 : -1;
        ModelPart gun = right ? model.rightArm : model.leftArm;          // 持枪手
        ModelPart support = right ? model.leftArm : model.rightArm;      // 支撑手
        float pitch = model.head.xRot;
        float yaw = model.head.yRot;
        gun.xRot = -((float) Math.PI / 2F) + pitch + 0.02F;
        gun.yRot = -s * 0.26F + yaw;
        gun.zRot = s * 0.05F;
        support.xRot = -((float) Math.PI / 2F) + pitch - 0.02F;
        support.yRot = -s * 0.50F + yaw;
        support.zRot = -s * 0.05F;
    }

    private final WeaponAnim.Kind kind;

    public static final WeaponArmPose AKM = new WeaponArmPose(WeaponAnim.Kind.AKM);
    public static final WeaponArmPose AWP = new WeaponArmPose(WeaponAnim.Kind.AWP);
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
            // ★ AKM / AWP：腰射「双手端枪」（CROSSBOW_HOLD），举枪换成自定义的举枪矄准姿势
            case AKM, AWP -> using ? RIFLE_AIM : HumanoidModel.ArmPose.CROSSBOW_HOLD;
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
        if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem) {
            return AWP;
        }
        if (stack.getItem() instanceof CrossbowWeaponItem) return CROSSBOW;
        if (stack.getItem() instanceof CompoundBowItem) return BOW;
        if (stack.getItem() instanceof GrenadeItem) return GRENADE;
        return AKM;
    }
}
