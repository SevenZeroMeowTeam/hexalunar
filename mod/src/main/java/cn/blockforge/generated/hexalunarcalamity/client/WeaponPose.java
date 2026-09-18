package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.model.ItemTransform;
import net.minecraft.client.renderer.block.model.ItemTransforms;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.joml.Vector3f;

/**
 * 手持动作的「姿态数学」：把 {@link WeaponAnim} 的冲量折算成 display 的
 * rotation / translation / scale 增量。
 *
 * <p>为什么动 display 而不是在 PoseStack 上硬怼：display 的参数（rotation 单位度、
 * translation 单位 1/16 方块）就是模型 JSON 里那套数，一是有现成的离线预览工具
 * {@code tools/fp_preview.py} 可以直接验证姿态，二是左右手镜像、第三人称、GUI 都由
 * 原版自己处理，我们只需要给「手部上下文」加增量。
 *
 * <p>轴向约定（已用 fp_preview 实测）：
 * <ul>
 *   <li>translation 是「手部空间」的偏移：+Y 抬手、+Z 朝玩家自己（后坐方向）</li>
 *   <li>rotation 对应模型 JSON 的 [x, y, z]，其中 +x 是枪口下压</li>
 * </ul>
 */
public final class WeaponPose {

    /**
     * ADS 对准的几何常量（单位都是模型像素，1 格 = 16）。
     *
     * <p>MC 第一人称物品的实际变换链：
     * <pre>world = Trans(0.56, -0.52, -0.72) · Trans(display.translation/16) · R · S · x</pre>
     * 相机在原点、朝 -Z 看，所以屏幕中心 ⇔ x_cam = y_cam = 0：
     * <pre>
     * 0.56 + Tx/16 = 0                     → Tx = -8.96
     * -0.52 + Ty/16 + S*瞄准点Y/16 = 0     → Ty = 8.32 - S*瞄准点Y
     * </pre>
     * （display 的 translation 用模型像素，模型几何也是 16 = 1 格）
     *
     * <p>★ 各武器的基准 display 平移与举枪增量都放在 {@link WeaponMount}（骨骼与子弹共用同一组数）。
     */

    public static ItemTransforms animate(WeaponAnim.Kind kind, ItemTransforms base) {
        WeaponAnim.State st = WeaponAnim.of(kind);
        if (WeaponAnim.isIdle(st)) return base;

        return new ItemTransforms(
                hands(kind, base.thirdPersonLeftHand, st, true, false),
                hands(kind, base.thirdPersonRightHand, st, false, false),
                hands(kind, base.firstPersonLeftHand, st, true, true),
                hands(kind, base.firstPersonRightHand, st, false, true),
                base.head, base.gui, base.ground, base.fixed);
    }

    /** 手部上下文的变换（leftHand 时按原版习惯做镜像） */
    private static ItemTransform hands(WeaponAnim.Kind kind, ItemTransform base, WeaponAnim.State st,
                                       boolean leftHand, boolean firstPerson) {
        float[] d = new float[8];
        deltas(kind, st, firstPerson, d);
        if (leftHand) {
            // 原版左右手镜像：x 位移与 y/z 旋转取反（y 旋转在 FP 里就是「朝哪边翻」）
            d[3] = -d[3];
            d[1] = -d[1];
            d[2] = -d[2];
        }
        if (d[0] == 0 && d[1] == 0 && d[2] == 0 && d[3] == 0 && d[4] == 0 && d[5] == 0 && d[6] == 0) {
            return base;
        }
        float rx = base.rotation.x() + d[0];
        float ry = base.rotation.y() + d[1];
        float rz = base.rotation.z() + d[2];
        float tx = base.translation.x() + d[3];
        float ty = base.translation.y() + d[4];
        float tz = base.translation.z() + d[5];
        float s = base.scale.x() * (1.0F + d[6]);
        return new ItemTransform(new Vector3f(rx, ry, rz), new Vector3f(tx, ty, tz),
                new Vector3f(s, s, s));
    }

    private static void deltas(WeaponAnim.Kind kind, WeaponAnim.State st, boolean firstPerson, float[] d) {
        switch (kind) {
            case AKM -> akm(st, firstPerson, d);
            case CROSSBOW -> crossbow(st, d);
            case BOW -> bow(st, d);
            case GRENADE, FLASH -> grenade(st, d);
            default -> {
            }
        }
        applyWalkAndBreath(d, st.aim);
    }

    // ------------------------------------------------------------------ 各武器

    /** AKM：后坐（上抬 + 后拖 + 随机枪口偏摆）、举枪过渡、换弹起伏、走路摆动 */
    private static void akm(WeaponAnim.State st, boolean firstPerson, float[] d) {
        float fp = firstPerson ? 1.0F : 0.6F;      // 第三人称幅度小一点
        // 后坐：枪托向后（+Z）、整体上抬（+Y）、枪口上翻 + 随机偏摆
        // （注：模型是「垂直握持」的，光靠 rotX 几乎看不出动，得靠 +Y/+Z 位移和 rotZ 偏摆）
        d[5] += 1.5F * st.recoil * fp;
        d[4] += 1.5F * st.recoil * fp;
        d[0] -= 5.5F * st.recoil * fp;
        d[2] += 4.5F * st.recoilYaw * fp;
        d[1] += 1.5F * st.recoilYaw * fp;

        // 举枪（ADS）：把「照门顶 + 准星顶」那条瞄准线顶到屏幕中心 ⇒ 看到枪身上方
        // 一条与枪管平行的直线。基准平移是 (-2.6, 1.4, 1.8)，所以增量要减掉它。
        // 不加任何 rotation：一旦旋转，瞄准线就会离开屏幕中心（原来的 -2° 侧倾正是
        // 「看上去不是水平一条线」的原因之一）。
        //
        // ★ AKM 现在走 GeckoLib 骨骼渲染，举枪位移实际是 AkmGeoModel 推 move 骨骼做的
        //   （display 包装器对 GeckoLib 物品不生效），两边用的是 WeaponMount 里同一组数，
        //   这里保留只是给「还用 display 那套」的旧武器兜底，不要两处同时生效。
        d[3] += WeaponMount.AKM_AIM_DX * st.aim;
        d[4] += WeaponMount.AKM_AIM_DY * st.aim;
        d[5] += WeaponMount.AKM_AIM_DZ * st.aim;

        // 换弹：整把枪下沉、向内侧翻，末段拉一下枪机
        if (st.reload >= 0.0F) {
            float p = Mth.sin(st.reload * (float) Math.PI);
            d[4] -= 3.4F * p;
            d[3] -= 1.6F * p;
            d[2] -= 18.0F * p;
            d[0] += 6.0F * p;
            // 插弹匣/拉机柄的两次小顿挫
            float bump = bump(st.reload, 0.45F, 0.12F) + bump(st.reload, 0.9F, 0.1F);
            d[5] += 0.9F * bump;
            d[4] += 0.5F * bump;
        }
    }

    /** 十字弩：开镜时往画面中心收、拍一次明显的后坐；上弦时左手把弦拉回（整把弩跟着后拖下沉） */
    private static void crossbow(WeaponAnim.State st, float[] d) {
        d[5] += 1.6F * st.recoil;
        d[4] += 1.2F * st.recoil;
        d[0] -= 5.0F * st.recoil;
        d[2] += 3.0F * st.recoilYaw;
        d[3] -= 1.2F * st.aim;
        d[4] += 0.6F * st.aim;
        d[5] += 0.9F * st.aim;

        // 上弦：拉弦阶段往后拖、略下沉并外翻；弓弦挂上、弩箭入槽各顿一下
        if (st.reload >= 0.0F) {
            float pull = Mth.clamp(st.reload / 0.62F, 0.0F, 1.0F);      // 拉弦阶段
            float ease = Mth.sin(pull * (float) Math.PI * 0.5F);        // 先快后慢，像真的在拉力
            d[5] += 2.6F * ease;                                       // 往身前（+Z）拖
            d[4] -= 1.4F * ease;                                       // 下沉
            d[3] -= 0.8F * ease;                                       // 往画面中心收
            d[2] += 7.0F * ease;                                        // 外翻
            d[0] += 3.0F * ease;
            // 挂弦 + 推箭入槽的两次顿挫
            float bump = bump(st.reload, 0.60F, 0.10F) + bump(st.reload, 0.92F, 0.08F);
            d[5] += 1.0F * bump;
            d[4] -= 0.5F * bump;
        }
    }

    /** 复合弓：瞄准参照 = 箭上方的瞄准圈，把圈心顶到屏幕中心（旋转会推偏圈心，故不给旋转） */
    private static void bow(WeaponAnim.State st, float[] d) {
        // ★ 同 AKM：弓也走 GeckoLib 骨骼渲染，display 包装器不生效，实际对心在 BowGeoModel 里推 move 骨骼；
        //   这里保留给 display 那套旧路径兜底，数都在 WeaponMount 里。
        d[5] += WeaponMount.BOW_AIM_DZ * st.draw;
        d[3] += WeaponMount.BOW_AIM_DX * st.draw;
        d[4] += WeaponMount.BOW_AIM_DY * st.draw;

        d[5] += 1.5F * st.release;
        d[4] -= 0.6F * st.release;
        d[0] -= 4.0F * st.release;
    }

    /** 手雷 / 震爆弹：拔销要「使劲」、引信烧到尾巴开始抖、出手时甩手 */
    private static void grenade(WeaponAnim.State st, float[] d) {
        // 拔销：手腕外翻 + 抬手，越接近拔完动作越大
        float p = st.pin;
        d[2] += 16.0F * p;
        d[0] -= 8.0F * p;
        d[4] += 1.6F * p;
        d[5] += 0.8F * p;

        // 已拔销：引信剩余越短抖得越厉害（和 HUD 的倒计时一个节奏）
        float urgency = fuseUrgency();
        if (urgency > 0.0F) {
            Player player = Minecraft.getInstance().player;
            float t = (player == null ? 0.0F : player.tickCount) * 0.9F;
            float shake = Mth.sin(t) * 2.6F + Mth.sin(t * 2.7F) * 1.2F;
            d[2] += shake * urgency;
            d[3] += Mth.sin(t * 1.7F) * 0.7F * urgency;
        }

        // 出手：向前上方甩出去
        d[5] -= 3.0F * st.throwKick;
        d[4] += 2.2F * st.throwKick;
        d[0] -= 26.0F * st.throwKick;
    }

    /** 引信紧迫度 0..1（1 = 马上就要炸） */
    private static float fuseUrgency() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return 0.0F;
        ItemStack stack = GrenadeItem.heldGrenade(player);
        if (stack == null || GrenadeItem.state(stack) != GrenadeItem.STATE_ARMED) return 0.0F;
        int left = GrenadeItem.fuseLeft(stack, player.level().getGameTime());
        return Mth.clamp(1.0F - left / (float) GrenadeItem.FUSE_TICKS, 0.0F, 1.0F);
    }

    // ------------------------------------------------------------------ 通用

    /**
     * 走路摆动 + 呼吸微漂（幅度很小，只在第一人称给）。
     *
     * <p>举枪瞄准时按 aim 几乎全部收掉：ADS 是靠平移把「照门—准星」那条线压到屏幕
     * 中心的，任何额外的旋转/上下漂移都会把这条线推离准星 —— 看起来就是“枪口斜着朝下”。
     */
    private static void applyWalkAndBreath(float[] d, float aim) {
        Player player = Minecraft.getInstance().player;
        if (player == null) return;
        float damp = 1.0F - 0.9F * Mth.clamp(aim, 0.0F, 1.0F);
        float speed = Mth.clamp((float) player.getDeltaMovement().horizontalDistance() * 3.6F, 0.0F, 1.0F);
        float phase = (float) player.walkDist;
        if (speed > 0.01F) {
            d[0] += Mth.sin(phase * 4.4F) * 0.9F * speed * damp;
            d[3] += Mth.sin(phase * 2.2F) * 1.1F * speed * damp;
            d[4] -= Math.abs(Mth.cos(phase * 4.4F)) * 0.7F * speed * damp;
        }
        float breath = Mth.sin((player.tickCount + 0.0F) * 0.06F);
        d[4] += breath * 0.35F * damp;
        d[3] += Mth.sin(player.tickCount * 0.043F) * 0.25F * damp;
    }

    /** 钟形冲击：p 落在 center 附近 width 内时给出 0..1 */
    private static float bump(float p, float center, float width) {
        float x = (p - center) / width;
        return Mth.clamp(1.0F - x * x, 0.0F, 1.0F);
    }

    private WeaponPose() {}
}
