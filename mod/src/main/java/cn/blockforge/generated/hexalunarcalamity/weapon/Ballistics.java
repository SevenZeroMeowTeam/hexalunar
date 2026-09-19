package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.world.phys.Vec3;

/**
 * 三种玩家武器的有效射程与超距弹道参数。
 * <p>
 * 规则：弹头在有效射程内保持平直（很小的重力），超过有效射程后，
 * 每 tick 追加的下坠量随「超出比例」的平方增长，越远掉得越狠——
 * 想打得准，就得把目标留在有效距离之内。
 */
public final class Ballistics {

    /** AKM 有效射程（格）：步枪弹初速高，射程最远 */
    public static final double AKM_RANGE = 60.0D;
    /** AWP 有效射程（格）：.338 栓动狙击，比步枪弹更远更直 */
    public static final double AWP_RANGE = 96.0D;
    /** 十字弩有效射程（格） */
    public static final double BOLT_RANGE = 40.0D;
    /** 复合弓有效射程（格） */
    public static final double BOW_RANGE = 34.0D;

    /** AKM 弹头在有效射程内的重力（原版投掷物为 0.03，这里几乎平直） */
    public static final double AKM_IN_RANGE_GRAVITY = 0.006D;
    /** AWP 弹头在有效射程内的重力（比步枪弹更平） */
    public static final double AWP_IN_RANGE_GRAVITY = 0.004D;
    /** 弩箭在有效射程内的重力（原版箭为 0.05，这里收紧一半以上） */
    public static final double BOLT_IN_RANGE_GRAVITY = 0.022D;
    /** 复合弓箭在有效射程内的重力 */
    public static final double BOW_IN_RANGE_GRAVITY = 0.028D;
    /** 原版 AbstractArrow 每 tick 硬编码的重力，供对照 */
    public static final double VANILLA_ARROW_GRAVITY = 0.05D;

    /** 超距追加重力系数：g_extra = min(over^2, CAP) * FACTOR */
    private static final double EXTRA_FACTOR = 0.08D;
    /** 超出比例平方上限（≈ 2.25 倍有效射程后下坠不再继续加剧） */
    private static final double EXTRA_CAP = 1.5D;

    /**
     * 超出有效射程后每 tick 追加的下坠重力。
     *
     * @param travelled 从发射点起算的水平飞行距离（格）
     * @param range     该武器的有效射程（格）
     * @return 射程内为 0，超距后按平方增长，最大 {@code 0.12}
     */
    public static double extraGravity(double travelled, double range) {
        double over = (travelled - range) / range;
        if (over <= 0.0D) return 0.0D;
        return Math.min(over * over, EXTRA_CAP) * EXTRA_FACTOR;
    }

    /** 相对发射点的水平飞行距离（格） */
    public static double flown(Vec3 from, Vec3 to) {
        double dx = to.x - from.x;
        double dz = to.z - from.z;
        return Math.sqrt(dx * dx + dz * dz);
    }

    private Ballistics() {}
}
