package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.util.Mth;

/**
 * ★ Q 弹版（{@code -Pqmode=true}）的「果冻弹簧」—— 一个会**来回振荡**的衰减量。
 *
 * <p>原来的后坐/晃动都是「一次性冲量 + 指数衰减」（{@code x *= 0.55} 那种），曲线是单调回落的，
 * 看着就是「顿一下就没了」。Q 弹版要的是**弹一下再弹回来**：所以这里存的是「振幅 + 相位」，
 * {@link #wobble()} 返回 {@code 振幅 × sin(相位)} —— 开火/落地/受伤时 {@link #punch} 打一个冲量，
 * 之后振幅按 {@code decay} 衰减、相位匀速前进，于是整条曲线是「冲出去 → 回弹 → 反向小一点 → 停」。
 *
 * <p>用它的地方：
 * <ul>
 *   <li>{@code WeaponAnim.State#jelly}：开火时冲量，{@link GunPose} 拿它做**整枪挤压拉伸**
 *       （Y 压扁、Z 拉长）→ 枪像果冻一样「噗」一下</li>
 *   <li>Q 版僵尸的渲染器（{@link QChibiZombieRenderer}）：走路 / 受伤 / 落地时挤压拉伸 + 小跳</li>
 * </ul>
 *
 * <p>客户端渲染单线程，不需要同步。
 */
public final class Jelly {

    /** 当前振幅（0 = 静止） */
    private float amplitude;
    /** 振荡相位（弧度） */
    private float phase;

    /** 打一个冲量（开火 / 落地 / 受伤）：可叠加，封顶 2.0 */
    public void punch(float amount) {
        amplitude = Math.min(2.0F, amplitude + amount);
    }

    /**
     * 每 tick 推进一次。
     *
     * @param decay 振幅衰减系数（0.8 ≈ 三四下就停）
     * @param speed 相位速度（弧度/tick，1.15 ≈ 每 5.5 tick 一个来回）
     */
    public void tick(float decay, float speed) {
        amplitude *= decay;
        if (amplitude < 0.004F) {
            amplitude = 0.0F;
            phase = 0.0F;
            return;
        }
        phase += speed;
        if (phase > Mth.TWO_PI * 64.0F) phase -= Mth.TWO_PI * 64.0F;   // 防浮点越滚越大
    }

    /** 当前形变量 -1..1（正 = 往「第一下」的方向，负 = 回弹） */
    public float wobble() {
        return amplitude * Mth.sin(phase);
    }

    /** 当前振幅（0..2），给「挤压拉伸」这类只关心强度的用途 */
    public float amplitude() {
        return amplitude;
    }

    /** 已经基本静止（渲染层可以跳过变换） */
    public boolean resting() {
        return amplitude <= 0.0F;
    }

    public void reset() {
        amplitude = 0.0F;
        phase = 0.0F;
    }
}
