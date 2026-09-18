package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.util.Mth;

/**
 * 第一人称「双手持枪」：原版对**非空物品**只画物品、不画手臂（{@code renderArmWithItem}
 * 里只有 {@code itemStack.isEmpty()} 才走 {@code renderPlayerArm}），所以枪看着像浮在空中。
 * 这里把玩家自己的两条手臂补上：
 *
 * <ul>
 *   <li><b>右手</b>：握在握把上（正好是原版放物品的位置）</li>
 *   <li><b>左手</b>：托在护木下缘（支撑手），也就是「双手持」看起来的那只手</li>
 * </ul>
 *
 * <h2>为什么是自己算变换，而不是抄原版 {@code renderPlayerArm}</h2>
 * 原版那条链是给「空手」用的：手的位置固定在 {@code ARM_FP} 附近，手臂往下垂。
 * 枪的护木在眼睛前方约 1 格、还要跟着举枪（ADS）一起挪，所以直接给
 * {@link #drawArm} 算好的「袖口位置 + 朝向 + 长度缩放」三件套。
 *
 * <h2>几何（1.20.1 源码核对过）</h2>
 * {@code PlayerRenderer.renderHand} 会先 {@code resetPose()}，所以手臂方块在传入的
 * pose 坐标里占：<br>
 * 右臂 {@code x[-0.5,-0.25] y[0,0.75] z[-0.125,0.125]}，左臂 {@code x[0.25,0.5]}……<br>
 * 即 <b>pose 原点那一端是肩，局部 +y 伸出 0.75 格那一端是手</b>。
 * 因此「把手放到 H」= 原点平移 {@code H - R·(方块x中心, 0.75, 0)}。
 *
 * <p>常数由 {@code mod/tools/_dblhold.py} 离线算出并渲图验证（脚件里同一条链）。
 */
public final class AkmArms {

    /** 举枪（ADS）时手臂跟着枪一起挪，和 {@code AkmGeoModel} 推 move 骨骼用的是同一份数 */
    private static final float PX = 16.0F;
    /** 手臂只沿长度方向拉伸，粗细保持原版（否则整条胳膊变成大棒子） */
    private AkmArms() {
    }

    public static void render(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light) {
        AbstractClientPlayer player = mc.player;
        if (player == null) return;
        if (!(mc.getEntityRenderDispatcher().getRenderer(player) instanceof PlayerRenderer renderer)) {
            return;
        }
        // 举枪时枪被挪到屏幕正中，手臂要跟着一起挪（倍数与 AkmGeoModel 的 aim 一致）
        float aim = Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.AKM).aim, 0.0F, 1.0F);
        float dx = WeaponMount.AKM_AIM_DX * aim / PX;
        float dy = WeaponMount.akmAimDy(AkmGeoModel.sightNow) * aim / PX;
        float dz = WeaponMount.AKM_AIM_DZ * aim / PX;

        drawArm(pose, buffer, light, renderer, player, true,
                WeaponMount.AKM_ARM_R_ORIGIN, WeaponMount.AKM_ARM_R_ANGLE,
                WeaponMount.AKM_ARM_R_LEN, dx, dy, dz);
        drawArm(pose, buffer, light, renderer, player, false,
                WeaponMount.AKM_ARM_L_ORIGIN, WeaponMount.AKM_ARM_L_ANGLE,
                WeaponMount.AKM_ARM_L_LEN, dx, dy, dz);
    }

    private static void drawArm(PoseStack pose, MultiBufferSource buffer, int light,
                                PlayerRenderer renderer, AbstractClientPlayer player, boolean right,
                                float[] origin, float[] angle, float length,
                                float dx, float dy, float dz) {
        pose.pushPose();
        pose.translate(origin[0] + dx, origin[1] + dy, origin[2] + dz);
        pose.mulPose(Axis.XP.rotationDegrees(angle[0]));
        pose.mulPose(Axis.YP.rotationDegrees(angle[1]));
        pose.mulPose(Axis.ZP.rotationDegrees(angle[2]));
        pose.scale(1.0F, length, 1.0F);
        if (right) {
            renderer.renderRightHand(pose, buffer, light, player);
        } else {
            renderer.renderLeftHand(pose, buffer, light, player);
        }
        pose.popPose();
    }
}
