package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * 第一人称双臂（双手持枪）。
 *
 * <p>原版对**非空物品**只画物品、不画手臂（{@code renderArmWithItem} 里只有
 * {@code itemStack.isEmpty()} 才走 {@code renderPlayerArm}），所以枪看着像浮在空中。
 * 这里用玩家自己的皮肤补画两条手臂：
 * <ul>
 *   <li><b>右手</b>：始终握在握把上（枪本来就画在右手位置）</li>
 *   <li><b>左手</b>：按动作走 —— AKM 托护木 → 抽弹匣 → 插新匣 → 拉机柄；
 *       十字弩托护木 → 拉弦 → 递箭上槽</li>
 * </ul>
 *
 * <h2>手臂怎么摆</h2>
 * {@code PlayerRenderer#renderHand} 会先 {@code resetPose()}，所以手臂方块在传入的 pose 坐标里占
 * {@code y[0, 0.75]}（原点那一端是肩、局部 +0.75 格那一端是手），方块 x 中心 ±0.375。
 * 于是「把手放到 H」= 原点平移 {@code H − s·R·(x中心, 0.75, 0)}；
 * 朝向由「肩 → 手」方向决定，再加一个绕手臂轴的自转（掌朝向）。
 *
 * <p>手的目标点由各武器按进度给出（**模型像素**，{@link GunFrame} 换成相机空间），
 * 所以手臂自动跟着举枪 / 换弹动画一起动 —— 不需要在这里重复任何武器逻辑。
 */
public final class WeaponArms {

    /** 原版第一人称的手部基准（相机空间，格）：与 {@code WeaponMount} 同一份数 */
    public static final double ARM_X = 0.56D;
    public static final double ARM_Y = -0.52D;
    public static final double ARM_Z = -0.72D;

    /** 肩点（相机空间，格）：固定不动，手离得远手臂就按比例拉长 */
    private static final float[] SHOULDER_R = {0.72F, -1.00F, -0.20F};
    private static final float[] SHOULDER_L = {0.10F, -0.95F, -0.62F};
    /** 原版手臂长度（格） */
    private static final float ARM_LEN = 0.75F;
    /** 手臂方块在 pose 坐标里的 x 中心（格） */
    private static final float HALF = 0.375F;
    /** 绕手臂轴的自转（度）：让掌心大致朝向枪身 */
    private static final float ROLL_R = 155.0F;
    private static final float ROLL_L = 24.0F;

    /** AKM 右手（模型像素）：握把 */
    private static final float[] AKM_RIGHT = {0.0F, 0.55F, -0.15F};
    /** 十字弩右手（模型像素）：grip 骨骼方块中心 */
    private static final float[] CB_RIGHT = {0.0F, -0.90F, 0.60F};

    public static void renderAkm(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light) {
        float p = AkmGeoModel.localReloadProgress();
        render(mc, pose, buffer, light, AkmGeoModel.frame,
                AKM_RIGHT, AkmGeoModel.leftHandPx(p, new float[3]));
    }

    public static void renderCrossbow(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light) {
        render(mc, pose, buffer, light, CrossbowGeoModel.frame,
                CB_RIGHT, CrossbowGeoModel.leftHandPx(new float[3]));
    }

    private static void render(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light,
                               GunFrame frame, float[] rightPx, float[] leftPx) {
        AbstractClientPlayer player = mc.player;
        if (player == null) return;
        if (!(mc.getEntityRenderDispatcher().getRenderer(player) instanceof PlayerRenderer pr)) return;
        float[] handR = frame.toCamera(rightPx[0], rightPx[1], rightPx[2], new float[3]);
        float[] handL = frame.toCamera(leftPx[0], leftPx[1], leftPx[2], new float[3]);
        if (handR == null || handL == null) return;      // 还没捕获到枪的变换：这一帧不画
        drawArm(pose, buffer, light, pr, player, true, handR, SHOULDER_R, ROLL_R);
        drawArm(pose, buffer, light, pr, player, false, handL, SHOULDER_L, ROLL_L);
    }

    /** 把手放到 hand（相机空间，格），手臂从 shoulder 方向伸出来 */
    private static void drawArm(PoseStack pose, MultiBufferSource buffer, int light, PlayerRenderer pr,
                                AbstractClientPlayer player, boolean right, float[] hand,
                                float[] shoulder, float rollDeg) {
        Vector3f y = new Vector3f(hand[0] - shoulder[0], hand[1] - shoulder[1], hand[2] - shoulder[2]);
        float dist = y.length();
        if (dist < 1.0E-4F) return;
        float s = dist / ARM_LEN;                   // 只沿长度方向拉伸，粗细保持原版
        y.div(dist);
        Vector3f ref = new Vector3f(0.0F, 1.0F, 0.0F);
        if (Math.abs(y.dot(ref)) > 0.95F) ref.set(0.0F, 0.0F, -1.0F);
        Vector3f z = new Vector3f(y).cross(ref).normalize();
        Vector3f x = new Vector3f(y).cross(z).normalize();
        float r = rollDeg * Mth.DEG_TO_RAD;
        float cr = Mth.cos(r);
        float sr = Mth.sin(r);
        Vector3f xr = new Vector3f(x).mul(cr).add(new Vector3f(z).mul(sr));
        Vector3f zr = new Vector3f(z).mul(cr).sub(new Vector3f(x).mul(sr));
        Matrix3f m = new Matrix3f(xr.x, y.x, zr.x,
                                  xr.y, y.y, zr.y,
                                  xr.z, y.z, zr.z);
        Quaternionf q = m.getNormalizedRotation(new Quaternionf());
        float ox = xr.x * HALF + y.x * ARM_LEN * s;
        float oy = xr.y * HALF + y.y * ARM_LEN * s;
        float oz = xr.z * HALF + y.z * ARM_LEN * s;
        pose.pushPose();
        pose.translate(hand[0] - ox, hand[1] - oy, hand[2] - oz);
        pose.mulPose(q);
        pose.scale(1.0F, s, 1.0F);
        if (right) {
            pr.renderRightHand(pose, buffer, light, player);
        } else {
            pr.renderLeftHand(pose, buffer, light, player);
        }
        pose.popPose();
    }

    private WeaponArms() {
    }
}
