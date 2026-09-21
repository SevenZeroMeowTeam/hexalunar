package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * 第一人称「手持武器」的空间换算：把<b>模型像素坐标</b>换成世界坐标。
 *
 * <p>为什么要算这个：子弹、枪口焰、抛壳如果都从「眼睛前方 0.7 格」生成，画面上
 * 就会看到火花和弹道从屏幕中间飞出来、和枪管对不上（枪在右边、弹道在中间 ⇒
 * 看起来弹道是斜的）。改成从<b>枪口模型点</b>生成，弹道才真正从枪口出发。
 *
 * <h2>原版变换链（{@code ItemInHandRenderer} + {@code ItemRenderer}）</h2>
 * <pre>
 * 相机空间 = Trans(i*0.56, -0.52, -0.72) · Trans(display.translation/16) · R · S · (模型像素/16)
 * </pre>
 * i = 右手 +1 / 左手 -1；{@code display.translation} 单位是 1/16 格 = 1 模型像素，
 * 所以模型像素坐标和 display 平移可以直接相加。相机在眼睛处、朝 -Z 看。
 *
 * <p>AKM 的 display 是「无旋转 + scale 1」，所以 R/S 都是单位变换，上面这条链就是全部。
 *
 * <h2>举枪（ADS）平移</h2>
 * 让「照门顶—准星顶—导轨齿顶」那条线（模型 X=0、Y=SIGHT_Y）落到屏幕中心，需要的 display 平移增量：
 * <pre>
 * dx = -side*8.96 - TX      （右手 -6.36、左手 +11.56）
 * dy =  8.32 - 3.44 - TY    （= +3.48）
 * dz =  1.4                 （顺手拉近一点，不影响对准）
 * </pre>
 * 这三个数与 {@code AkmGeoModel} 推 {@code move} 骨骼的偏移量是同一份数（骨骼位移也在
 * 模型空间、单位同样是模型像素），改一处必须同步另一处 —— 所以都放在这里。
 *
 * <p>★ r67：模型里护木顶部导轨的齿顶从 3.16 抬到了 3.44（{@code akm_v3.py} 的 RAIL_LIFT），
 * 于是「准星柱顶 = 照门顶 = 导轨齿顶」三点共线 —— 用户要的「导管上方凸点和护木装倍镜
 * 上方是一条直线」。SIGHT_Y 本身没变，所以这里的对准数学一行都不用改。
 */
public final class WeaponMount {

    /** 原版 applyItemArmTransform 的手部基准（右手主手；单位：格） */
    private static final double ARM_X = 0.56D;
    private static final double ARM_Y = -0.52D;
    private static final double ARM_Z = -0.72D;
    /** 瞄准参照点的模型 Y（照门顶 = 准星顶 = 导轨齿顶，akm_v3.py 的 SIGHT_Y） */
    private static final double SIGHT_Y = 3.44D;
    /** 屏幕中心 ⇔ 相机空间 X = 0，对应 display 平移 = -8.96（模型像素） */
    private static final double HAND_X_PX = ARM_X * 16.0D;

    // ------------------------------------------------------------------ AKM
    /** models/item/akm.json → display.firstperson_righthand.translation */
    public static final float AKM_TX = -5.0F;
    public static final float AKM_TY = -0.6F;
    public static final float AKM_TZ = 1.8F;
    /** 举枪增量（上面公式的推演结果，右手） */
    public static final float AKM_AIM_DX = (float) (-HAND_X_PX - AKM_TX);              // -6.36
    public static final float AKM_AIM_DY = (float) (-ARM_Y * 16.0D - SIGHT_Y - AKM_TY); // +3.48
    /**
     * ★★ r100：**按 TaCZ AK47 的定位组改** —— 机瞄时把枪朝射手方向收（贴近眼睛）。
     *
     * <p>TaCZ 的枪没有 display 位移，姿态全靠模型内的定位组（display json 原话：
     * 「旋转和位移使用模型内定位组」）。AK47 的两组是：
     * <pre>
     *   idle_view（腰射）pivot = (2.5, 12.0,    13.75)      z 最大 = 枪离眼最远
     *   iron_view（机瞄）pivot = (0.0, 10.8875, 10.15625)   z 小了 3.59 ⇒ 枪**朝射手收 3.59 单位**
     * </pre>
     * 三把枪规律一致（M4A1 收 3.8、Glock 收 0.75、均**右移归零 + 上抬**），而且
     * **`iron_view` 没有任何旋转** —— 步枪机瞄就是「枪管正对视线 + 把后照门拉到你眼前」。
     *
     * <p>我们原来的 {@code -3.0} 是**往枪口方向推**（枪越举越远、屏幕上越小），方向正好相反。
     * 现在改成 **+1.8**（这是**相对 akm.json 腰射位移的增量**，见 {@code GunPose.matrix}）：
     * TaCZ 的 3.59 单位是相对它 38 单位长的枪，我们这把约 19 单位 ⇒ 按比例取 3.59 × 0.5 ≈ 1.8。
     * 相对旧值相当于**把枪拉近 4.8 px ≈ 0.3 格**，屏幕上有明显变大，又刻意没取满
     * （r88 试过增量 +4.0：眼睛会被塞进机匣里、后摇板铺满屏幕）。
     */
    public static final float AKM_AIM_DZ = 1.8F;
    /** ★ r88：装了 4 倍镜时同样**往前走**（以前是把眼睛贴到目镜上，结果整把枪占满屏幕） */
    public static final float AKM_SCOPE_AIM_DZ = -3.0F;
    /**
     * ★★ r88：举枪时给枪一点**横滚** —— TaCZ 的机瞷矄准就是这个构图：
     * 枪身斜插在画面右下、机匣顶面看得见，而瞄准线（照门顶 = 准星顶）仍钉在屏幕中心。
     *
     * <p><b>为什么能做到「准星不动、枪身动」</b>：横滚是绕**眼睛**施加的（见 {@code GunPose.matrix}
     * 的乘法顺序），而举枪平移已经把「照门顶—准星顶」那条线顶到了眼睛上 ⇒ 线上每一点
     * 都在旋转轴上，横滚对它零影响；枪身其余部分离轴线越远甩得越多。
     */
    /**
     * ★★ r92：举枪横滚常量 —— **0**（参考 TaCZ 的 AK47 配置，见 {@link #akmAdsRoll}）。
     *
     * <p>r88 曾用 15°（机瞷）/ 8°（红点）做「枪身斜插画面」的构图，但那是**绕眼睛**转，
     * 虽然准星还在中心，用户要的却是图 1 那种「枪正着端在眼前」的持枪，所以归零。
     * 常量保留下来是为了让 {@link #rollComp} 那段补心位移继续可用（0 时它自动跳过）。
     */
    public static final float AKM_ADS_ROLL = 0.0F;
    /** 枪口（模型像素）：枪管轴线 Y=1.75、最前端 z=-11.60 */
    public static final double[] AKM_MUZZLE = {0.0D, 1.75D, -11.60D};
    /** 抛壳口（模型像素）：枪机右侧 x≈0.95、高度 2.62 */
    public static final double[] AKM_EJECT = {0.95D, 2.62D, -2.30D};
    /** 弹匣换成手的位置（模型像素）：弹匣井上方 */
    public static final double[] AKM_MAG_GRIP = {0.0D, 1.55D, -3.95D};
    /** 红点圆心（模型 Y；与 akm_v3.py 的 build_dot_sight 一致：3.79 + RAIL_LIFT 0.28） */
    public static final double AKM_DOT_Y = 4.07D;
    /** 4 倍镜光轴（模型 Y；与 akm_v3.py 的 build_scope_4x 一致：4.00 + RAIL_LIFT 0.28） */
    public static final double AKM_SCOPE_Y = 4.28D;

    // ------------------------------------------------ 第一人称双臂（双手持枪，见 client/AkmArms）
    /**
     * 袖口（pose 原点）在相机空间的位置，单位：<b>格</b>；角度是 {@code XP·YP·ZP} 依次旋转的度数；
     * 长度是只沿手臂长度方向的拉伸（粗细不变）。
     *
     * <p>算法：手臂方块在 pose 坐标里占 {@code y[0,0.75]}（那是手动端），
     * 所以 {@code 原点 = 手 − R·(方块x中心, 0.75, 0)}；手分别放在握把（模型 0,0.55,-0.15）
     * 与护木下缘（模型 0,2.05,-6.3），均经 {@code Trans(±0.56,-0.52,-0.72)·Trans(display/16)} 换算。
     * 由 {@code tools/_dblhold.py} 离线算并渲图确认，改模型 display 或调手位要重算。
     */
    public static final float[] AKM_ARM_R_ORIGIN = {1.002F, -0.776F, -0.095F};
    public static final float[] AKM_ARM_R_ANGLE = {-19.06F, -31.49F, 28.21F};
    public static final float AKM_ARM_R_LEN = 1.067F;
    public static final float[] AKM_ARM_L_ORIGIN = {-0.189F, -0.745F, -0.498F};
    public static final float[] AKM_ARM_L_ANGLE = {-16.59F, 31.33F, -25.58F};
    public static final float AKM_ARM_L_LEN = 1.076F;

    /** 当前瞄具对应的「该顶到屏幕中心的参照高度」 */
    public static double akmAnchorY(int sight) {
        return switch (sight) {
            case Sights.DOT -> AKM_DOT_Y;
            case Sights.SCOPE -> AKM_SCOPE_Y;
            default -> SIGHT_Y;                 // 机械瞄具：照门顶 = 准星顶 = 导轨齿顶
        };
    }

    /** 举枪握枪姿态的横滚角（度）：**恒为 0**。
     *
     * <p>★ r92：参考 TaCZ 的 {@code ak47_display.json} —— 那份配置里 **旋转与位移都不在这里给**
     * （只有 {@code transform.scale}），枪的举枪姿态就是「模型内定位组 + 纯平移」；
     * {@code iron_zoom = 1.33} / {@code zoom_model_fov = 45} / {@code show_crosshair = false}
     * 这三项我们早已对齐。所以 r88 那种「机瞷 15°、红点 8° 横滚」的构图去掉：
     * 举枪只做平移 ⇒ 照门—准星那条线永远钉在屏幕中心，枪身也是正的（就是用户图 1 那种持枪）。
     */
    public static float akmAdsRoll(int sight) {
        return 0.0F;
    }
    /** 举枪时该给的 display Y 增量（随瞄具高度变） */
    public static float akmAimDy(int sight) {
        return (float) (-ARM_Y * 16.0D - akmAnchorY(sight) - AKM_TY);
    }
    /** 举枪时向前拉的量：4 倍镜要贴到目镜上，机瞷/红点只是拉近一点 */
    public static float akmAimDz(int sight) {
        return sight == Sights.SCOPE ? AKM_SCOPE_AIM_DZ : AKM_AIM_DZ;
    }

    /**
     * 举枪位移（**相机空间、单位格**）：渲染（{@link GunPose}）与弹道共用这一份。
     *
     * <p>★ r85：以前这些值是以「模型像素」推在 {@code move} 骨骼上的，会被动画关键帧遮掉
     * （AKM 的 reload 动画自带 −1.2px/+7°）⇒ 画面上就是「换弹/发射时枪和手往下沉」。
     * 现在一律换成相机空间格值，由我们自己填的那段 pose 施加。
     *
     * <p>★ r88b：{@code out[0..2]} = xyz，{@code out[3]} = 举枪横滚（度，供渲染用）。
     * 横滚同时会带来一块**侧移**，已经在这里补掉了 —— 见 {@link #rollComp}。
     */
    public static void akmAds(LivingEntity entity, int sight, float[] out) {
        float roll = akmAdsRoll(sight);
        out[0] = akmAimDx(entity) / 16.0F;
        out[1] = akmAimDy(sight) / 16.0F;
        out[2] = akmAimDz(sight) / 16.0F;
        rollComp(roll, (int) side(entity), out);
        if (out.length > 3) out[3] = roll;
    }

    /** AWP 的举枪位移（相机空间、格）；{@code out[3]} = 0（镜筒必须正着） */
    public static void awpAds(LivingEntity entity, float[] out) {
        out[0] = awpAimDx(entity) / 16.0F;
        out[1] = AWP_AIM_DY / 16.0F;
        out[2] = AWP_AIM_DZ / 16.0F;
        if (out.length > 3) out[3] = 0.0F;
    }

    /**
     * ★★ r88b：横滚的「补心」位移（相机空间、格）。
     *
     * <p>为什么要它：{@link GunPose} 的横滚写在 pose 矩阵里，而 pose 原点在相机空间是
     * {@code (side·0.56, −0.52, −0.72)}（原版手部基准）——**不是眼睛**。绕这一点转 θ 会把
     * 整条瞄准线（它与视线平行）侧移 {@code Rz(−θ)·ARM − ARM}，于是准星/照门离开屏幕中心
     * （用户实测：\"准星/照门不在准心\"）。把这块位移加回举枪平移里，瞄准线就精确回到眼睛上，
     * 枪身照样绕它甩向右下。
     *
     * <p>推导：举枪平移后瞄准参照点落在相机空间 {@code −ARM}（加 ARM 后正好是眼睛），
     * 横滚把它乘上 Rz ⇒ 需补 {@code ARM − Rz(−θ)·ARM}；补完后参照点仍映射到原点（眼睛）。
     */
    private static void rollComp(float rollDeg, int side, float[] ads) {
        if (rollDeg == 0.0F) return;
        double r = Math.toRadians(-rollDeg);
        double c = Math.cos(r), s = Math.sin(r);
        double ax = side * ARM_X, ay = ARM_Y;
        ads[0] += (float) (ax - (ax * c - ay * s));
        ads[1] += (float) (ay - (ax * s + ay * c));
    }    /** 复合弓的箭杆（发射点）：模型像素 */
    public static final double[] BOW_ARROW = {0.0D, 0.85D, -8.0D};

    /**
     * 准星落点：从眼睛沿视线打一条线，打到方块就用命中点（距离夹在 min..max），否则取 max 处。
     *
     * <p>用来让「子弹/箭」从枪口（弓的搭箭点）出发、终点正好落在准星上 —— 直线且不脱靶。
     */
    public static Vec3 aimPoint(LivingEntity entity, Level level, double minDist, double maxDist) {
        Vec3 eye = entity.getEyePosition();
        Vec3 look = entity.getLookAngle();
        net.minecraft.world.phys.BlockHitResult hit = level.clip(new ClipContext(eye,
                eye.add(look.scale(maxDist)), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, entity));
        if (hit.getType() == net.minecraft.world.phys.HitResult.Type.MISS) {
            return eye.add(look.scale(maxDist));
        }
        // 收敛距离下限：太近时枪口/搭箭点与视线的横向差会被放大成很大偏角
        double d = Math.max(minDist, eye.distanceTo(hit.getLocation()));
        return eye.add(look.scale(d));
    }

    /** 从模型点 modelPoint 射向准星落点的单位方向；异常时退回视线方向 */
    public static Vec3 fireDir(LivingEntity entity, Level level, Vec3 from,
                               double minDist, double maxDist) {
        Vec3 look = entity.getLookAngle();
        Vec3 dir = aimPoint(entity, level, minDist, maxDist).subtract(from);
        if (dir.lengthSqr() < 1.0E-6D || dir.normalize().dot(look) < 0.2D) return look;
        return dir;
    }
    /** 举枪时该给的 display X 增量（左撇子要反号） */
    public static float akmAimDx(LivingEntity entity) {
        return side(entity) > 0 ? AKM_AIM_DX : (float) (HAND_X_PX - AKM_TX);        // +11.56
    }

    // ------------------------------------------------------------------ AWP（栓动狙击枪）
    /**
     * {@code models/item/awp.json → display.firstperson_righthand.translation}。
     *
     * <p>★ 目标是「和 AKM 一样的持枪方式」：屏幕上两把枪的**枪管轴线重合**。
     * 枪管轴线平行于视线时，它在屏幕上必然是**过屏幕中心的一条直线**，斜率只由
     * 「轴线到眼睛的横向偏移」决定 —— AKM 的轴线在模型 Y=1.75（它的握把也在 1.75），
     * AWP 的轴线在 Y=1.575，所以 {@code TY = AKM_TY + (1.75 − 1.575) = 1.575} 时两条线完全重合
     * （离线实测：屏幕倾角 39.1°，与 AKM 的 39.1° 一致）。
     *
     * <p>⚠️ 副作用（模型原点不同带来的必然结果）：AWP 的握把（{@code move} 骨骼 pivot）
     * 比它的枪管轴线低 2.65，所以这样摆以后**双手会比 AKM 的手位低 0.165 格**。
     * 手臂走 {@code GunFrame}、跟着枪走，不会脱手；举枪（ADS）只做平移，
     * 镜筒光轴照样顶到屏幕中心（见 {@link #AWP_AIM_DY}）。
     */
    public static final float AWP_TX = -5.0F;
    public static final float AWP_TY = -0.425F;
    public static final float AWP_TZ = 0.50F;
    /** 8 倍镜光轴（模型 Y；对应 awp_gen.py 打印的 SCOPE_AXIS = 3.15） */
    public static final double AWP_SCOPE_Y = 3.15D;
    public static final float AWP_AIM_DX = (float) (-HAND_X_PX - AWP_TX);              // -6.36
    public static final float AWP_AIM_DY = (float) (-ARM_Y * 16.0D - AWP_SCOPE_Y - AWP_TY);
    /** 枪口（模型像素）：枪管轴线 Y=1.575、最前端 z=-16.275 */
    public static final double[] AWP_MUZZLE = {0.0D, 1.575D, -18.00D};
    /**
     * ★★ r88：**往前走**（负值 = 远离眼睛）。
     *
     * <p>r85~r87 一直往正方向加（6.0 → 7.5），本意是「把眼睛贴到目镜上、镜环占屏」，
     * 结果眼睛钻进了镜筒：目镜只剩 7 厘米 ⇒ 筒壁与目镜内侧面铺满屏幕（用户反馈「黑屏」）。
     * 而往正方向加又有个硬门槛：枪托尾端在模型 z=+7.35，要让它退到眼睛后面得 dz ≥ 5.5
     * —— 那时目镜已经只有 7 厘米，怎么都躲不开「黑屏 or 一堵枪托」。
     * 所以反过来选「整把枪在眼前」：目镜 0.68 格、枪托 0.60 格，镜筒/枪身都看得清，
     * 屏幕中心那点黑只是目镜玻璃（0.05 格宽）在 0.68 格外的投影。
     */
    public static final float AWP_AIM_DZ = -3.5F;
    /**
     * ★★ r116（用户标注图：「所有武器自动抛壳为绿色箭头位置，抛壳方向应该为蓝色箭头位置」）：
     * 抛壳点必须**明显落在枪身右侧**。r115 曾把这里从 `{0.90, 1.39, -0.60}` 改到
     * `{0.30, 1.575, -2.50}`（x 几乎回到枪身中线）⇒ 粒子看着还在枪身中间，用户再次反馈。
     * 现在 x 取 **0.78**（机匣半宽 0.36 的外侧一点 = 抛壳窗外沿），z 对齐右侧抛壳窗中心，
     * 与模型里 `casing` 骨骼（`tools/awp_v2.py` 的 `CASE_X`）同一侧。
     */
    public static final double[] AWP_EJECT = {0.78D, 1.50D, -2.50D};
    /**
     * ★ AWP 与 AKM 是**同一套持枪规则**：不做任何额外旋转（{@code AwpGeoModel.computeMovePose}
     * 的三个角度恒为 0），所以枪口 / 抛壳点的模型坐标可以直接用，不需要按角度补偿。
     *
     * <p>r82 曾加过 {@code AWP_HIP_PITCH = -14°} 把枪管在屏幕上压成水平，但那等于让枪在世界里
     * 真的朝下 14°（用户反馈「枪口下垂」）—— 已去掉。要调屏幕上的倾斜感请改 display 旋转。
     */

    /** 举枪时的 display X 增量（左撇子走另一侧） */
    public static float awpAimDx(LivingEntity entity) {
        return side(entity) > 0 ? AWP_AIM_DX : (float) (HAND_X_PX - AWP_TX);
    }

    // -------------------------------------------------- AWP 的持枪姿态（TaCZ 步枪那一套）
    /**
     * ★★ r114（用户：「**套用 TaCZ 步枪的持枪动画**」；TaCZ 里没有 AWP，用精密国际
     * {@code ai_awp} 那套 —— 它的 {@code ai_awp_display.json} 写的是
     * {@code use_default_animation: "rifle"}，也就是**与 M1 / AK47 同一份**
     * {@code assets/tacz/animations/rifle_default.animation.json}）。
     *
     * <p>所以这里与 {@link #m1HoldPose} 取同一组 TaCZ 数值（角度与枪长无关，直接沿用；
     * 位移按枪长折算：TaCZ 那把 38 单位 → 我们 24 单位，×0.63，而 M1 是 ×0.55）：
     * <pre>
     *   idle         7.2667s 循环  root rot X −0.70..0.83  Y −0.97..0.07  Z −0.27..1.41
     *   walk_aiming  1.0s   循环  root rot ≤ 0.7°    pos ≤ 0.11 单位
     *   run          0.8s   循环  root rot X −43..−28.3  Y −53.6..−35.7  Z 24.6..38.2
     *                              ⇒ 跑动时**枪压低并转到射手右侧**（TaCZ 的冲刺持枪）
     * </pre>
     *
     * <p>★ 为什么放在 {@link WeaponMount} 而不是 GeoModel：**枪口 / 抛壳点的世界坐标必须用
     * 同一份姿态**（见 {@link #awpHoldPoint}），否则跑动时枪口焰与弹道会与枪身脱开
     * （r82 的 AWP 腰射下压角就踩过这个坑）。
     */
    public static final float AWP_RUN_PITCH = -35.6F;
    public static final float AWP_RUN_YAW = -44.6F;
    public static final float AWP_RUN_ROLL = 31.4F;
    public static final float AWP_RUN_DX = -0.80F;
    public static final float AWP_RUN_DY = -3.50F;
    public static final float AWP_RUN_DZ = -0.40F;
    /** idle 呼吸（TaCZ rifle_default idle 的幅度） */
    public static final float AWP_BREATH_ROT_X = 0.80F;
    public static final float AWP_BREATH_ROT_Y = 0.50F;
    public static final float AWP_BREATH_ROT_Z = 0.90F;
    public static final float AWP_BREATH_PY = 0.10F;
    /** {@code move} 骨骼 pivot（geo 里的值，改模型要同步；{@code tools/awp_v2.py} 打印过） */
    public static final float AWP_MOVE_PX = 0.0F;
    public static final float AWP_MOVE_PY = -1.0725F;
    public static final float AWP_MOVE_PZ = 1.305F;

    /**
     * AWP 的持枪姿态（TaCZ 通用步枪 {@code rifle_default}）——写进 {@code out}：
     * {@code out[0..2]} = {@code move} 骨骼位移（模型像素），{@code out[3..5]} = 三个欧拉角（弧度）。
     *
     * @param aim 举枪比例 0..1（**抵肩时姿态全部收掉**：镜筒光轴必须精确落在屏幕中心）
     * @param run 冲刺量 0..1（客户端给平滑值，服务端给 0/1）
     */
    public static void awpHoldPose(LivingEntity entity, float aim, float run, float[] out) {
        float damp = 1.0F - clamp01(aim);
        float t = entity == null ? 0.0F : (float) entity.tickCount;
        float r = clamp01(run);

        // ---- idle 呼吸（TaCZ rifle_default idle）
        float brx = (float) Math.sin(t * 0.050F) * AWP_BREATH_ROT_X;
        float bry = -0.45F + (float) Math.sin(t * 0.041F + 2.0F) * AWP_BREATH_ROT_Y;
        float brz = 0.57F + (float) Math.sin(t * 0.031F + 1.2F) * AWP_BREATH_ROT_Z;
        float bpx = (float) Math.sin(t * 0.043F) * 0.02F;
        float bpy = -0.08F + (float) Math.sin(t * 0.050F + 0.6F) * AWP_BREATH_PY;

        // ---- walk_aiming：很轻的走路摆动（跑起来就不叠了，TaCZ 的 run 另有一整套）
        float speed = entity == null ? 0.0F
                : clamp01((float) entity.getDeltaMovement().horizontalDistance() * 3.6F);
        float w = speed * (1.0F - r);
        float wrx = (float) Math.sin(t * 0.55F) * 0.70F * w;
        float wpy = -(float) Math.abs(Math.cos(t * 0.55F)) * 0.11F * w;

        out[0] = (bpx + AWP_RUN_DX * r) * damp;
        out[1] = (bpy + wpy + AWP_RUN_DY * r) * damp;
        out[2] = (AWP_RUN_DZ * r) * damp;
        out[3] = (float) Math.toRadians(brx + wrx + AWP_RUN_PITCH * r) * damp;
        out[4] = (float) Math.toRadians(bry + AWP_RUN_YAW * r) * damp;
        out[5] = (float) Math.toRadians(brz + AWP_RUN_ROLL * r) * damp;
    }

    /** 服务端 / 弹药侧用的便捷版：冲刺量直接取实体状态 */
    public static void awpHoldPose(LivingEntity entity, float aim, float[] out) {
        awpHoldPose(entity, aim, awpRun(entity), out);
    }

    /** 冲刺量（0/1）：站着 / 空中 / 非冲刺都算 0（与 {@code AwpAnimState.sprinting()} 同判据） */
    public static float awpRun(LivingEntity entity) {
        return entity != null && entity.isSprinting() && entity.onGround() ? 1.0F : 0.0F;
    }

    /**
     * 把 {@code move} 骨骼的姿态作用到一个**模型像素点**上（口径与 {@link #m1HoldPoint} 完全一致）：
     * {@code p' = pivot + pos + R·(p − pivot)}，旋转用 {@code new Quaternionf().rotationXYZ(...)}
     * —— 与 GeckoLib 渲染器内部构造四元数的方式逐字相同，所以这里的点与屏幕上看到的枪是同一个位置。
     */
    public static void awpHoldPoint(float[] pose, double[] p, double[] out) {
        Vector3f v = new Vector3f((float) (p[0] - AWP_MOVE_PX), (float) (p[1] - AWP_MOVE_PY),
                (float) (p[2] - AWP_MOVE_PZ));
        new Quaternionf().rotationXYZ(pose[3], pose[4], pose[5]).transform(v);
        out[0] = AWP_MOVE_PX + pose[0] + v.x;
        out[1] = AWP_MOVE_PY + pose[1] + v.y;
        out[2] = AWP_MOVE_PZ + pose[2] + v.z;
    }

    /**
     * AWP 的某个模型点 → 世界坐标（aiming = 正抵肩瞄准）。
     *
     * <p>★ r114：先过一遍 {@code move} 骨骼的持枪姿态（呼吸 / 走动 / 冲刺压低），再过 display + 举枪姿态
     * —— 与 {@code AwpGeoModel.computeMovePose} 取的是同一份数（見 {@link #awpHoldPose}）。
     */
    public static Vec3 awp(LivingEntity entity, boolean aiming, double[] modelPoint) {
        float[] ads = new float[4];
        awpAds(entity, ads);
        float aim = aiming ? 1.0F : 0.0F;
        float[] hold = new float[6];
        double[] p = new double[3];
        awpHoldPose(entity, aim, hold);
        awpHoldPoint(hold, modelPoint, p);
        return toWorld(entity, AWP_TX, AWP_TY, AWP_TZ, 1.0F, p, aim,
                ads[0] * aim, ads[1] * aim, ads[2] * aim, 0.0F);
    }

    // ------------------------------------------------------------------ Kar98k（栓动步枪，自带 4 倍镜）
    /**
     * {@code models/item/kar98k.json → display.firstperson_righthand.translation}。
     *
     * <p>★ 与 {@link #AWP_TY} 同一个定法：<b>枪管轴线在屏幕上与 AKM 重合</b>。
     * AKM 的枪管轴线在模型 Y=1.75，Kar98k 的枪管轴线在 Y=2.25
     * （{@code kar98k_gen.py} 的外露枪管方块 y 1.95…2.55 的中心）
     * ⇒ {@code TY = AKM_TY + (1.75 − 2.25) = −1.10}；TX / TZ 沿用 AKM / AWP 那组（−5.0 / 0.50）。
     *
     * <p>⚠️ 与 AWP 的差别：Kar98k 的**握把在模型 Y≈0.6**（比枪管轴线低 1.65），
     * 所以双手会比 AWP 的手位再低一点 —— 手臂走 {@code GunFrame}、跟着枪走，不会脱手。
     */
    public static final float KAR98K_TX = -5.0F;
    public static final float KAR98K_TY = -1.10F;
    public static final float KAR98K_TZ = 0.50F;
    /**
     * 4 倍镜筒光轴（模型 Y）：镜筒方块 y 3.95…4.85 的中心 = {@code scope} 骨骼 pivot **4.4**
     * （必须与 {@code tools/kar98k_gen.py} 里那根镜筒的 y 中心一致 —— 改模型要同步改这里）。
     */
    public static final double KAR98K_SCOPE_Y = 4.40D;
    public static final float KAR98K_AIM_DX = (float) (-HAND_X_PX - KAR98K_TX);                       // -3.96
    public static final float KAR98K_AIM_DY =
            (float) (-ARM_Y * 16.0D - KAR98K_SCOPE_Y - KAR98K_TY);                                   // +5.02
    /**
     * 举枪时整把枪往前推离眼睛的量（与 AWP 同一取值）。抵肩即**整屏镜筒遮罩**
     * （见 {@code ClientEvents.maskScoping}），枪本体开镜时根本不画 ⇒
     * 这个数实际只影响**开镜射击时枪口 / 抛壳点的世界坐标**（弹道起点）。
     */
    public static final float KAR98K_AIM_DZ = -3.5F;
    /** 枪口（模型像素）：枪管轴线 Y=2.25、最前端 z=−13.60 */
    public static final double[] KAR98K_MUZZLE = {0.0D, 2.25D, -13.60D};
    /** 抛壳口（模型像素）：机匣右侧、正对拉机柄（{@code casing} 骨骼 pivot 0.30 / 3.00 / −1.20） */
    public static final double[] KAR98K_EJECT = {0.80D, 3.00D, -1.20D};

    /** 举枪时的 display X 增量（左撇子走另一侧） */
    public static float kar98kAimDx(LivingEntity entity) {
        return side(entity) > 0 ? KAR98K_AIM_DX : (float) (HAND_X_PX - KAR98K_TX);
    }

    /** Kar98k 的举枪位移（相机空间、格）；{@code out[3]} = 0（镜筒必须正着） */
    public static void kar98kAds(LivingEntity entity, float[] out) {
        out[0] = kar98kAimDx(entity) / 16.0F;
        out[1] = KAR98K_AIM_DY / 16.0F;
        out[2] = KAR98K_AIM_DZ / 16.0F;
        if (out.length > 3) out[3] = 0.0F;
    }

    /** Kar98k 的某个模型点 → 世界坐标（aiming = 正抵肩瞄准；枪不做任何额外旋转，直接取模型点） */
    public static Vec3 kar98k(LivingEntity entity, boolean aiming, double[] modelPoint) {
        float[] ads = new float[4];
        kar98kAds(entity, ads);
        float aim = aiming ? 1.0F : 0.0F;
        return toWorld(entity, KAR98K_TX, KAR98K_TY, KAR98K_TZ, 1.0F, modelPoint, aim,
                ads[0] * aim, ads[1] * aim, ads[2] * aim, 0.0F);
    }

    // ------------------------------------------------------------------ 莫辛-纳甘 M91/30（7.62x59 栓动，出厂自带 4 倍镜）
    /**
     * {@code models/item/mosin_nagant.json → display.firstperson_righthand.translation}。
     *
     * <p>★ 与 AKM **完全同一组**：莫辛的原点就是握把、枪管轴线也在模型 Y=1.75
     * （{@code tools/mosin_gen.py} 的 {@code BORE}）⇒ 手持构图与 AKM 逐像素一致。
     */
    public static final float MOSIN_TX = -5.0F;
    public static final float MOSIN_TY = -0.6F;
    public static final float MOSIN_TZ = 1.8F;
    /**
     * 机瞄瞮准线（模型 Y）：照门缺口两耳顶 = 准星柱顶 = **2.72**
     * （与 {@code tools/mosin_m9130_v3.py} 的 {@code IRON_Y} 必须一致）。
     */
    public static final double MOSIN_IRON_Y = 2.72D;
    /** 4 倍镜光轴（模型 Y）：镜筒中心 = **3.34**（{@code mosin_m9130_v3.py} 的 {@code SCOPE_Y}） */
    public static final double MOSIN_SCOPE_Y = 3.34D;
    public static final float MOSIN_AIM_DX = (float) (-HAND_X_PX - MOSIN_TX);
    /** 机瞄举枪的 Y 增量（把「照门顶—准星顶」那条线顶到屏幕中心） */
    public static final float MOSIN_IRON_AIM_DY =
            (float) (-ARM_Y * 16.0D - MOSIN_IRON_Y - MOSIN_TY);
    /** 4 倍镜举枪的 Y 增量（把镜筒光轴顶到屏幕中心） */
    public static final float MOSIN_SCOPE_AIM_DY =
            (float) (-ARM_Y * 16.0D - MOSIN_SCOPE_Y - MOSIN_TY);
    /**
     * 举枪时把枪**朝射手收**多少（display 平移增量、模型像素）。
     *
     * <p>TaCZ kar98k 的定位组：{@code idle_view z = 17.0} → {@code iron_view z = 17.5}
     * （只差 0.5 单位），换算到我们这把 22.4 像素长的枪上 ≈ 0.2 像素 ⇒ **几乎不前后走**；
     * 取 1.2 只是让举枪后的构图稍微紧凑一点（抵肩时眼睛离机匣不会太远）。
     */
    public static final float MOSIN_AIM_DZ = 1.2F;
    /** 枪口（模型像素）：枪管轴线 Y=1.75、最前端 z=−17.35（长枪管） */
    public static final double[] MOSIN_MUZZLE = {0.0D, 1.75D, -17.35D};
    /**
     * 抛壳口（模型像素）：机匣右侧、正对拉机柄。
     * ★ r116：x 由 0.62 提到 **0.90**（机匣半宽 0.38 的外侧一点）—— 粒子要**明显在枪身右侧**，
     * 贴着枪身 midline 的话在屏幕上看着还是「从枪身中间冒出来」。
     */
    public static final double[] MOSIN_EJECT = {0.90D, 2.10D, -1.95D};

    /** 举枪时该顶到屏幕中心的参照高度（机瞄 / 4 倍镜两档） */
    public static double mosinAnchorY(int sight) {
        return sight == Sights.SCOPE ? MOSIN_SCOPE_Y : MOSIN_IRON_Y;
    }

    /** 举枪时该给的 display Y 增量（随瞄具档位变） */
    public static float mosinAimDy(int sight) {
        return sight == Sights.SCOPE ? MOSIN_SCOPE_AIM_DY : MOSIN_IRON_AIM_DY;
    }

    /** 举枪时的 display X 增量（左撇子走另一侧） */
    public static float mosinAimDx(LivingEntity entity) {
        return side(entity) > 0 ? MOSIN_AIM_DX : (float) (HAND_X_PX - MOSIN_TX);
    }

    /** 莫辛的举枪位移（相机空间、格）；{@code out[3]} = 0（举枪只做平移，瞮准线才钉在屏幕中心） */
    public static void mosinAds(LivingEntity entity, int sight, float[] out) {
        out[0] = mosinAimDx(entity) / 16.0F;
        out[1] = mosinAimDy(sight) / 16.0F;
        out[2] = MOSIN_AIM_DZ / 16.0F;
        if (out.length > 3) out[3] = 0.0F;
    }

    /** 莫辛的某个模型点 → 世界坐标（aiming = 正抵肩瞮准；枪不做任何额外旋转，直接取模型点） */
    public static Vec3 mosin(LivingEntity entity, boolean aiming, int sight, double[] modelPoint) {
        float[] ads = new float[4];
        mosinAds(entity, sight, ads);
        float aim = aiming ? 1.0F : 0.0F;
        return toWorld(entity, MOSIN_TX, MOSIN_TY, MOSIN_TZ, 1.0F, modelPoint, aim,
                ads[0] * aim, ads[1] * aim, ads[2] * aim, 0.0F);
    }

    // ------------------------------------------------------------------ M1 加兰德（半自动，机瞄）
    /**
     * {@code models/item/m1_garand.json → display.firstperson_righthand.translation}。
     *
     * <p>与 AKM / AWP / Kar98k / 莫辛同一个定法：<b>枪管轴线在屏幕上与 AKM 重合</b>。
     * AKM 的枪管轴线在模型 Y=1.75，M1 的枪管轴线在 Y=2.30
     * （{@code m1_garand_v2.py} 的 {@code BORE}，r108 起就是 2.30，v2 重建后没变）
     * ⇒ {@code TY = AKM_TY + (1.75 − 2.30) = −1.15}；TX / TZ 沿用 −5.0 / 0.50。
     */
    public static final float M1_TX = -5.0F;
    public static final float M1_TY = -1.15F;
    public static final float M1_TZ = 0.50F;
    /**
     * 机瞄瞄准线（模型 Y）：**觇孔（八棱空心环）圆心 = 准星片顶**。
     *
     * <p>★ r111：觇孔做成**真空心圆环 + 透明镜片**之后直径从「一块方片」变成 1.16 单位，
     * 圆心抬到 **3.44**（与 AKM / AWP / Kar98k / 莫辛同一高度）。改模型必须同步这个数。
     */
    public static final double M1_IRON_Y = 3.44D;
    public static final float M1_AIM_DX = (float) (-HAND_X_PX - M1_TX);                         // -3.96
    public static final float M1_AIM_DY = (float) (-ARM_Y * 16.0D - M1_IRON_Y - M1_TY);         // +6.03
    /**
     * 举枪时「把后照门拉到你眼前」的量（模型像素）。
     *
     * <p>照 TaCZ 的 {@code ak47_display.json} 规律（{@code idle_view z = 13.75} →
     * {@code iron_view z = 10.156}，收 3.59 单位且**没有任何旋转**）：它那把枪 38 单位长，
     * 我们这把 20.96 ⇒ 按比例 3.59 × 0.55 ≈ **1.9**（与 AKM 的 {@code AKM_AIM_DZ} 同量级）。
     */
    public static final float M1_AIM_DZ = 1.9F;
    /** 枪口（模型像素）：枪管轴线 Y=2.30、最前端 z=−13.60（`m1_garand_v2.py` 的 MUZZLE_Z） */
    public static final double[] M1_MUZZLE = {0.0D, 2.30D, -13.60D};
    /**
     * 抛壳口（模型像素）：机匣右侧抛壳窗（x 0.20…0.46、y 2.78…3.00、z −1.75…−0.45）。
     * ★ r116：x 由 0.33（窗内）提到 **0.85**（窗外侧）—— 粒子要明显在枪身右侧。
     */
    public static final double[] M1_EJECT = {0.85D, 2.88D, -1.05D};

    // ------------------------------------------------ ★ M1 的「持枪动画」= TaCZ 通用步枪 rifle_default
    /**
     * TaCZ 的 {@code assets/tacz/animations/rifle_default.animation.json} 是**所有没自带动画的步枪**
     * 共用的那一套（TaCZ 里没有 M1）。用户要求「套用 TaCZ 步枪的持枪动画」，取它的三个状态：
     * <pre>
     *   idle         7.2667s 循环  root rot  X −0.70..0.83  Y −0.97..0.07  Z −0.27..1.41
     *                              root pos  X −0.05..0     Y −0.17..0.01
     *   walk_aiming  1.0s   循环  root rot  X/Y/Z ≤ 0.7°    pos ≤ 0.11 单位
     *   run          0.8s   循环  root rot  X −43..−28.3    Y −53.6..−35.7  Z 24.6..38.2
     *                              root pos  X −3.27..0.64  Y −7.24..−3.88
     *                              ⇒ 跑动时**枪压低并转到射手右侧**（TaCZ 的冲刺持枪）
     * </pre>
     * 取三段的**均值**当姿态，位置按枪长折算（TaCZ 那把 38 单位 → 我们 20.96，×0.55）。
     *
     * <p>★ 为什么这些数要放在 {@link WeaponMount} 而不是 GeoModel：**枪口 / 抛壳点的世界坐标必须
     * 用同一份姿态**（见 {@link #m1HoldPoint}），否则跑动时枪口焰与弹道会与枪身脱开
     * （r82 的 AWP 腰射下压角就踩过：改了模型姿态忘了同步弹道）。
     */
    public static final float M1_RUN_PITCH = -35.6F;
    public static final float M1_RUN_YAW = -44.6F;
    public static final float M1_RUN_ROLL = 31.4F;
    public static final float M1_RUN_DX = -0.70F;
    public static final float M1_RUN_DY = -3.05F;
    public static final float M1_RUN_DZ = -0.35F;
    /** idle 呼吸（TaCZ rifle_default idle 的幅度） */
    public static final float M1_BREATH_ROT_X = 0.80F;
    public static final float M1_BREATH_ROT_Y = 0.50F;
    public static final float M1_BREATH_ROT_Z = 0.90F;
    public static final float M1_BREATH_PY = 0.10F;
    /** {@code move} 骨骼 pivot（geo 里的值，改模型要同步） */
    public static final float M1_MOVE_PX = 0.0F;
    public static final float M1_MOVE_PY = 1.30F;
    public static final float M1_MOVE_PZ = 1.60F;

    /**
     * M1 的持枪姿态（TaCZ 通用步枪 {@code rifle_default}）：写进 {@code out}
     * <pre>
     *   out[0..2] = move 骨骼的位移（模型像素）   out[3..5] = 三个欧拉角（弧度）
     * </pre>
     * 顺序与 GeckoLib 的骨骼变换一致：{@code p' = pivot + pos + R(rot)·(p − pivot)}。
     *
     * @param aim 举枪比例 0..1（**举枪时姿态全部收掉**：瞄准线必须精确落在屏幕中心）
     * @param run 冲刺量 0..1（客户端给平滑值，服务端给 0/1 —— 与 ADS 同一套取舍）
     */
    public static void m1HoldPose(LivingEntity entity, float aim, float run, float[] out) {
        float damp = 1.0F - clamp01(aim);
        float t = entity == null ? 0.0F : (float) entity.tickCount;
        float r = clamp01(run);

        // ---- idle 呼吸（TaCZ rifle_default idle）
        float brx = (float) Math.sin(t * 0.050F) * M1_BREATH_ROT_X;
        float bry = -0.45F + (float) Math.sin(t * 0.041F + 2.0F) * M1_BREATH_ROT_Y;
        float brz = 0.57F + (float) Math.sin(t * 0.031F + 1.2F) * M1_BREATH_ROT_Z;
        float bpx = (float) Math.sin(t * 0.043F) * 0.02F;
        float bpy = -0.08F + (float) Math.sin(t * 0.050F + 0.6F) * M1_BREATH_PY;

        // ---- walk_aiming：很轻的走路摆动（跑起来就不叠了，TaCZ 的 run 另有一整套）
        float speed = entity == null ? 0.0F
                : clamp01((float) entity.getDeltaMovement().horizontalDistance() * 3.6F);
        float w = speed * (1.0F - r);
        float wrx = (float) Math.sin(t * 0.55F) * 0.70F * w;
        float wpy = -(float) Math.abs(Math.cos(t * 0.55F)) * 0.11F * w;

        out[0] = (bpx + M1_RUN_DX * r) * damp;
        out[1] = (bpy + wpy + M1_RUN_DY * r) * damp;
        out[2] = (M1_RUN_DZ * r) * damp;
        out[3] = (float) Math.toRadians(brx + wrx + M1_RUN_PITCH * r) * damp;
        out[4] = (float) Math.toRadians(bry + M1_RUN_YAW * r) * damp;
        out[5] = (float) Math.toRadians(brz + M1_RUN_ROLL * r) * damp;
    }

    /** 服务端 / 弹药侧用的便捷版：冲刺量直接取实体状态（与客户端稳态完全一致） */
    public static void m1HoldPose(LivingEntity entity, float aim, float[] out) {
        m1HoldPose(entity, aim, m1Run(entity), out);
    }

    /** 冲刺量（0/1）：站着 / 空中 / 非冲刺都算 0（与 {@code M1GarandAnimState.sprinting()} 同判据） */
    public static float m1Run(LivingEntity entity) {
        return entity != null && entity.isSprinting() && entity.onGround() ? 1.0F : 0.0F;
    }

    /**
     * 把 {@code move} 骨骼的姿态作用到一个**模型像素点**上：
     * {@code p' = pivot + pos + R·(p − pivot)}（S = 1）。
     *
     * <p>旋转用 {@code new Quaternionf().rotationXYZ(rx, ry, rz)} —— **与 GeckoLib 渲染器
     * 内部（{@code RenderUtils}）构造四元数的方式逐字相同**，所以这里的点与屏幕上看到的
     * 枪是同一个位置（自定义欧拉角顺序会偏，别自己拼矩阵）。
     */
    public static void m1HoldPoint(float[] pose, double[] p, double[] out) {
        Vector3f v = new Vector3f((float) (p[0] - M1_MOVE_PX), (float) (p[1] - M1_MOVE_PY),
                (float) (p[2] - M1_MOVE_PZ));
        new Quaternionf().rotationXYZ(pose[3], pose[4], pose[5]).transform(v);
        out[0] = M1_MOVE_PX + pose[0] + v.x;
        out[1] = M1_MOVE_PY + pose[1] + v.y;
        out[2] = M1_MOVE_PZ + pose[2] + v.z;
    }

    private static float clamp01(float v) {
        return v < 0.0F ? 0.0F : (v > 1.0F ? 1.0F : v);
    }

    /** 举枪时的 display X 增量（左撇子走另一侧） */
    public static float m1GarandAimDx(LivingEntity entity) {
        return side(entity) > 0 ? M1_AIM_DX : (float) (HAND_X_PX - M1_TX);
    }

    /** M1 加兰德的举枪位移（相机空间、格）；{@code out[3]} = 0（机瞄只做平移） */
    public static void m1GarandAds(LivingEntity entity, float[] out) {
        out[0] = m1GarandAimDx(entity) / 16.0F;
        out[1] = M1_AIM_DY / 16.0F;
        out[2] = M1_AIM_DZ / 16.0F;
        if (out.length > 3) out[3] = 0.0F;
    }

    /**
     * M1 加兰德的某个模型点 → 世界坐标（aiming = 正抵肩瞄准）。
     *
     * <p>★ r111：先过一遍 {@code move} 骨骼的持枪姿态（呼吸 / 跑动压低），再过 display + 举枪姿态。
     */
    public static Vec3 m1Garand(LivingEntity entity, boolean aiming, double[] modelPoint) {
        float[] ads = new float[4];
        m1GarandAds(entity, ads);
        float aim = aiming ? 1.0F : 0.0F;
        float[] hold = new float[6];
        double[] p = new double[3];
        m1HoldPose(entity, aim, hold);
        m1HoldPoint(hold, modelPoint, p);
        return toWorld(entity, M1_TX, M1_TY, M1_TZ, 1.0F, p, aim,
                ads[0] * aim, ads[1] * aim, ads[2] * aim, 0.0F);
    }

    // ------------------------------------------------------------------ 复合弓
    /** models/item/compound_bow.json → display.firstperson_righthand（平移 0、scale 0.75） */
    public static final float BOW_TX = 0.0F;
    public static final float BOW_TY = 0.0F;
    public static final float BOW_TZ = 0.0F;
    public static final float BOW_SCALE = 0.75F;
    /** 瞄准参照 = 箭上方那个瞄准圈的圆心（模型像素） */
    public static final double BOW_RING_Y = 2.86D;
    /** 举弓（ADS）增量：把圈心顶到屏幕中心（display 平移口径，单位模型像素） */
    public static final float BOW_AIM_DX = (float) (-HAND_X_PX - BOW_TX);                              // -8.96
    public static final float BOW_AIM_DY =
            (float) (-ARM_Y * 16.0D - BOW_SCALE * BOW_RING_Y - BOW_TY);                                // +6.175
    public static final float BOW_AIM_DZ = -2.6F;

    /**
     * 同样的举弓增量，**骨骼口径**：骨骼位移在 display 的 scale <b>之内</b>——
     * 链子是 {@code Trans(t/16) · R · S · (模型像素 + 骨骼位移)/16}，
     * 所以骨骼位移 d 产生的世界偏移是 {@code S*d/16}，而 display 平移 t 是 {@code t/16}。
     * ⇒ 想让骨骼看起来等价于 display 平移 t，必须给 {@code d = t/S}（弓 S=0.75 ⇒ ×4/3）。
     * ★ AKM 的 S=1，两者相等，所以那边只有一套数；弓一定要用这组，用错就是“对心总差一截”。
     */
    public static final float BOW_BONE_DX = BOW_AIM_DX / BOW_SCALE;                                    // -11.947
    public static final float BOW_BONE_DY = BOW_AIM_DY / BOW_SCALE;                                    // +8.233
    public static final float BOW_BONE_DZ = BOW_AIM_DZ / BOW_SCALE;                                    // -3.467

    /** 举弓时该给的 display X 增量（左摈子要反号） */
    public static float bowAimDx(LivingEntity entity) {
        return side(entity) > 0 ? BOW_AIM_DX : (float) (HAND_X_PX - BOW_TX);        // +8.96
    }

    /** 复合弓的某个模型点 → 世界坐标（aiming = 正在拉弓） */
    public static Vec3 bow(LivingEntity entity, boolean aiming, double[] modelPoint) {
        return toWorld(entity,
                BOW_TX + (aiming ? bowAimDx(entity) : 0.0F),
                BOW_TY + (aiming ? BOW_AIM_DY : 0.0F),
                BOW_TZ + (aiming ? BOW_AIM_DZ : 0.0F),
                BOW_SCALE, modelPoint);
    }

    /** AKM 的某个模型点 → 世界坐标（aiming = 正按住右键举枪；sight = 装了什么瞄具） */
    public static Vec3 akm(LivingEntity entity, boolean aiming, int sight, double[] modelPoint) {
        float[] ads = new float[4];
        akmAds(entity, sight, ads);
        float aim = aiming ? 1.0F : 0.0F;
        return toWorld(entity, AKM_TX, AKM_TY, AKM_TZ, 1.0F, modelPoint, aim,
                ads[0] * aim, ads[1] * aim, ads[2] * aim,
                ads[3] * aim);                  // 渲染用的是同一个角（AKM 的 display scale = 1）
    }

    /** 机械瞄具版（等价于 akm(..., Sights.IRON, ...)，给不关心瞄具的调用点用） */
    public static Vec3 akm(LivingEntity entity, boolean aiming, double[] modelPoint) {
        return akm(entity, aiming, Sights.IRON, modelPoint);
    }

    public static Vec3 toWorld(LivingEntity entity, float tx, float ty, float tz, float scale,
                               double[] p, float aim) {
        return toWorld(entity, tx, ty, tz, scale, p, aim, 0.0F, 0.0F, 0.0F, 0.0F);
    }

    /**
     * 模型像素坐标 → 世界坐标。
     *
     * @param tx/ty/tz display.firstperson 的平移（单位 1/16 格；在 scale <b>之前</b>生效）
     * @param scale    display.firstperson 的缩放（模型点要乘它；骨骼位移不用管，另有 BOW_BONE_* 一组）
     * @param p        模型像素点
     * @param aim      持枪姿态插值（1 = 举枪，0 = 腰射的 {@link GunPose} 姿态）
     * @param adsX/Y/Z 举枪位移（相机空间、格），按 aim 插值
     * @param rollDeg  举枪横滚（度，绕视线）—— 渲染同一个值，否则枪口与枪身会对不上
     */
    public static Vec3 toWorld(LivingEntity entity, float tx, float ty, float tz, float scale,
                               double[] p, float aim, float adsX, float adsY, float adsZ,
                               float rollDeg) {
        Vec3 look = entity.getLookAngle();
        Vec3 right = look.cross(new Vec3(0.0D, 1.0D, 0.0D));
        if (right.lengthSqr() < 1.0E-6D) {
            right = new Vec3(1.0D, 0.0D, 0.0D);
        }
        right = right.normalize();
        Vec3 up = right.cross(look).normalize();

        double s = side(entity);
        // display 的 x：json 里左右手两条互为镜像，而原版 apply() 对左手又会再取反一次，
        // 净效果两边相同（都等于右手那条的值），所以这里只按右手值算。
        // ★ GunPose 那段姿态作用在「手臂基准之后、display 之前」，所以是先把 display 那部分
        //   算成相机空间向量、过了 GunPose 再叠手臂基准（与枪的 pose 链完全同一顺序）。
        Vector3f v = new Vector3f((float) (tx / 16.0D + scale * p[0] / 16.0D),
                (float) (ty / 16.0D + scale * p[1] / 16.0D),
                (float) (tz / 16.0D + scale * p[2] / 16.0D));
        GunPose.transform(aim, adsX, adsY, adsZ, 0.0F, rollDeg, v);
        double lx = s * ARM_X + v.x;
        double ly = ARM_Y + v.y;
        double lz = ARM_Z + v.z;
        // 手部空间：+X 屏幕右、+Y 屏幕上、+Z 朝玩家身后（相机朝 -Z）
        return entity.getEyePosition()
                .add(right.scale(lx))
                .add(up.scale(ly))
                .add(look.scale(-lz));
    }

    /** 不叠持枪姿态的老口径（复合弓用：弓不走 {@link GunPose} 那一套） */
    public static Vec3 toWorld(LivingEntity entity, float tx, float ty, float tz, float scale,
                               double[] p) {
        return toWorld(entity, tx, ty, tz, scale, p, 1.0F);
    }

    private static double side(LivingEntity entity) {
        return entity.getMainArm() == HumanoidArm.RIGHT ? 1.0D : -1.0D;
    }

    private WeaponMount() {
    }
}
