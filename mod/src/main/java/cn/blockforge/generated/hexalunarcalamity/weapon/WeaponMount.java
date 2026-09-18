package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

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
 * 让「照门顶—准星顶」那条线（模型 X=0、Y=SIGHT_Y）落到屏幕中心，需要的 display 平移增量：
 * <pre>
 * dx = -side*8.96 - TX      （右手 -6.36、左手 +11.56）
 * dy =  8.32 - 3.44 - TY    （= +3.48）
 * dz =  1.4                 （顺手拉近一点，不影响对准）
 * </pre>
 * 这三个数与 {@code AkmGeoModel} 推 {@code move} 骨骼的偏移量是同一份数（骨骼位移也在
 * 模型空间、单位同样是模型像素），改一处必须同步另一处 —— 所以都放在这里。
 */
public final class WeaponMount {

    /** 原版 applyItemArmTransform 的手部基准（右手主手；单位：格） */
    private static final double ARM_X = 0.56D;
    private static final double ARM_Y = -0.52D;
    private static final double ARM_Z = -0.72D;
    /** 瞄准参照点的模型 Y（照门顶 = 准星顶） */
    private static final double SIGHT_Y = 3.44D;
    /** 屏幕中心 ⇔ 相机空间 X = 0，对应 display 平移 = -8.96（模型像素） */
    private static final double HAND_X_PX = ARM_X * 16.0D;

    // ------------------------------------------------------------------ AKM
    /** models/item/akm.json → display.firstperson_righthand.translation */
    public static final float AKM_TX = -2.6F;
    public static final float AKM_TY = 1.4F;
    public static final float AKM_TZ = 1.8F;
    /** 举枪增量（上面公式的推演结果，右手） */
    public static final float AKM_AIM_DX = (float) (-HAND_X_PX - AKM_TX);              // -6.36
    public static final float AKM_AIM_DY = (float) (-ARM_Y * 16.0D - SIGHT_Y - AKM_TY); // +3.48
    public static final float AKM_AIM_DZ = 1.4F;
    /** 枪口（模型像素）：枪管轴线 Y=1.75、最前端 z=-11.60 */
    public static final double[] AKM_MUZZLE = {0.0D, 1.75D, -11.60D};
    /** 抛壳口（模型像素）：枪机右侧 x≈0.95、高度 2.62 */
    public static final double[] AKM_EJECT = {0.95D, 2.62D, -2.30D};
    /** 弹匣换成手的位置（模型像素）：弹匣井上方 */
    public static final double[] AKM_MAG_GRIP = {0.0D, 1.55D, -3.95D};
    /** 红点圆心（模型 Y；与 akm_v3.py 的 build_dot_sight 一致） */
    public static final double AKM_DOT_Y = 3.79D;
    /** 4 倍镜光轴（模型 Y；与 akm_v3.py 的 build_scope_4x 一致） */
    public static final double AKM_SCOPE_Y = 4.00D;

    /** 当前瞄具对应的「该顶到屏幕中心的参照高度」 */
    public static double akmAnchorY(int sight) {
        return switch (sight) {
            case Sights.DOT -> AKM_DOT_Y;
            case Sights.SCOPE -> AKM_SCOPE_Y;
            default -> SIGHT_Y;                 // 机械瞄具：照门顶 = 准星顶
        };
    }

    /** 举枪时该给的 display Y 增量（随瞄具高度变） */
    public static float akmAimDy(int sight) {
        return (float) (-ARM_Y * 16.0D - akmAnchorY(sight) - AKM_TY);
    }
    /** 复合弓的箭杆（发射点）：模型像素 */
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
        return toWorld(entity,
                AKM_TX + (aiming ? akmAimDx(entity) : 0.0F),
                AKM_TY + (aiming ? akmAimDy(sight) : 0.0F),
                AKM_TZ + (aiming ? AKM_AIM_DZ : 0.0F),
                1.0F, modelPoint);          // AKM 的 display scale = 1
    }

    /** 机械瞄具版（等价于 akm(..., Sights.IRON, ...)，给不关心瞄具的调用点用） */
    public static Vec3 akm(LivingEntity entity, boolean aiming, double[] modelPoint) {
        return akm(entity, aiming, Sights.IRON, modelPoint);
    }

    /**
     * 模型像素坐标 → 世界坐标。
     *
     * @param tx/ty/tz display.firstperson 的平移（单位 1/16 格；在 scale <b>之前</b>生效）
     * @param scale    display.firstperson 的缩放（模型点要乘它；骨骼位移不用管，另有 BOW_BONE_* 一组）
     * @param p        模型像素点
     */
    public static Vec3 toWorld(LivingEntity entity, float tx, float ty, float tz,
                               float scale, double[] p) {
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
        double lx = s * ARM_X + tx / 16.0D + scale * p[0] / 16.0D;
        double ly = ARM_Y + ty / 16.0D + scale * p[1] / 16.0D;
        double lz = ARM_Z + tz / 16.0D + scale * p[2] / 16.0D;
        // 手部空间：+X 屏幕右、+Y 屏幕上、+Z 朝玩家身后（相机朝 -Z）
        return entity.getEyePosition()
                .add(right.scale(lx))
                .add(up.scale(ly))
                .add(look.scale(-lz));
    }

    private static double side(LivingEntity entity) {
        return entity.getMainArm() == HumanoidArm.RIGHT ? 1.0D : -1.0D;
    }

    private WeaponMount() {
    }
}
