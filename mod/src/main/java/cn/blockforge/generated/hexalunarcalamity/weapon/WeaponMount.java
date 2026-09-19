package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
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
    public static final float AKM_AIM_DZ = -3.0F;
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
    public static final double[] AWP_MUZZLE = {0.0D, 1.575D, -16.275D};
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
    /** 抛壳口（模型像素）：机匣右侧（弹壳从这儿翻出去） */
    public static final double[] AWP_EJECT = {0.90D, 1.39D, -0.60D};
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

    /** AWP 的某个模型点 → 世界坐标（aiming = 正抵肩瞄准） */
    public static Vec3 awp(LivingEntity entity, boolean aiming, double[] modelPoint) {
        float[] ads = new float[4];
        awpAds(entity, ads);
        float aim = aiming ? 1.0F : 0.0F;
        return toWorld(entity, AWP_TX, AWP_TY, AWP_TZ, 1.0F, modelPoint, aim,
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
