package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
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
        applyWalkAndBreath(d);
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

        // 举枪：往画面中心（-X）收，略上抬并拉近一点（fp_preview 实测屏幕包围盒）
        d[3] -= 2.4F * st.aim;
        d[4] += 1.1F * st.aim;
        d[5] += 1.4F * st.aim;
        d[2] += -2.0F * st.aim;

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

    /** 十字弩：开镜时往画面中心收、拍一次明显的后坐 */
    private static void crossbow(WeaponAnim.State st, float[] d) {
        d[5] += 1.6F * st.recoil;
        d[4] += 1.2F * st.recoil;
        d[0] -= 5.0F * st.recoil;
        d[2] += 3.0F * st.recoilYaw;
        d[3] -= 1.2F * st.aim;
        d[4] += 0.6F * st.aim;
        d[5] += 0.9F * st.aim;
    }

    /** 复合弓：拉弦时把弓往身前拉、上抬一点；放箭时向前回弹（幅度要小，否则会顶到镜头） */
    private static void bow(WeaponAnim.State st, float[] d) {
        d[5] -= 2.6F * st.draw;
        d[4] += 1.4F * st.draw;
        d[0] += 1.6F * st.draw;
        d[1] += 2.2F * st.draw;

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

    /** 走路摆动 + 呼吸微漂（幅度很小，只在第一人称给） */
    private static void applyWalkAndBreath(float[] d) {
        Player player = Minecraft.getInstance().player;
        if (player == null) return;
        float speed = Mth.clamp((float) player.getDeltaMovement().horizontalDistance() * 3.6F, 0.0F, 1.0F);
        float phase = (float) player.walkDist;
        if (speed > 0.01F) {
            d[0] += Mth.sin(phase * 4.4F) * 0.9F * speed;
            d[3] += Mth.sin(phase * 2.2F) * 1.1F * speed;
            d[4] -= Math.abs(Mth.cos(phase * 4.4F)) * 0.7F * speed;
        }
        float breath = Mth.sin((player.tickCount + 0.0F) * 0.06F);
        d[4] += breath * 0.35F;
        d[3] += Mth.sin(player.tickCount * 0.043F) * 0.25F;
    }

    /** 钟形冲击：p 落在 center 附近 width 内时给出 0..1 */
    private static float bump(float p, float center, float width) {
        float x = (p - center) / width;
        return Mth.clamp(1.0F - x * x, 0.0F, 1.0F);
    }

    private WeaponPose() {}
}
