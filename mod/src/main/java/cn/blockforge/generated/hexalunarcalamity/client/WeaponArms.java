package cn.blockforge.generated.hexalunarcalamity.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.util.Mth;
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

    /**
     * 原版手部基准 Y：拿非空物品时还会叠一段「抬起物品」的位移 {@code −0.6·equip}
     * （刚切到手上那几帧物品是从下面升上来的），手臂用同一个值才不会脱手。
     */
    static float baseY() {
        return (float) ARM_Y - 0.6F * WeaponHandGrip.equipNow;
    }

    /**
     * 肩点（相机空间，格）：固定不动，手离得远手臂就按比例拉长。
     *
     * <p>数值照抄原版第一人称手臂的落点（{@code ItemInHandRenderer#renderPlayerArm} 里那条链算出来
     * 的方块起点大约在 {@code (0.58, -0.38, -0.50)}、朝 {@code (0.33, 0.47, -0.82)} 伸出去）：
     * 也就是「从屏幕右下角外伸进来、朝前方」。所以肩点要**靠前**（z 约 -0.4），
     * 太靠后（z ≈ -0.2）手臂根部会贴着相机，屏幕边上就是一片糊的色块。
     * ★ r65 修正：肩点再也不能放到 z≈-0.42（离相机只有 0.42 格）——那时整条手臂在屏幕上
     *   就是一大片皮肤色梯形，把枪遮住（用户录屏里的问题）。现在放到画面下缘外、约 0.8 格处，
     *   并且**不再为了够到肩点把手臂拉长**（肩距≈0.9 格 ⇒ 拉伸只有 ~1.2 倍）。
     */
    private static final float[] SHOULDER_R = {0.55F, -0.85F, -0.80F};
    private static final float[] SHOULDER_L = {-0.42F, -0.85F, -0.78F};

    /**
     * ★★ r99：举枪（ADS）时肩点外推倍率。
     *
     * <p>枪模投影在举枪时会从 {@code MODEL_FOV_HIP = 76°} 收到 {@code MODEL_FOV_AIM = 45°}
     * （≈1.69 倍放大），而肩点（{@link #SHOULDER_R}/{@link #SHOULDER_L}）离眼睛只有 0.78~0.80 格
     * ⇒ 在 ADS 里两条手臂会被放大成一大片皮肤色楔子，正好糊在准星上（用户截图里的"机瞄问题"）。
     * 按 aim 把肩点整体外推这个倍率之后，手臂在 ADS 与腰射下的**视觉粗细/长度**基本一致。
     */
    private static final float ADS_SHOULDER_PUSH = 1.55F;
    /** 原版手臂长度（格） */
    private static final float ARM_LEN = 0.75F;
    /** 手臂方块在 pose 坐标里的 x 中心（格） */
    private static final float HALF = 0.375F;
    /** 手臂粗细（相对原版 0.25 格的倍率）：略细一点，少挡视野 */
    private static final float THICK = 0.85F;
    /** 绕手臂轴的自转（度）：让掌心大致朝向枪身 */
    private static final float ROLL_R = 155.0F;
    private static final float ROLL_L = 24.0F;

    /** AKM 右手（模型像素）：握把 */
    private static final float[] AKM_RIGHT = {0.0F, 0.55F, -0.15F};
    /** 十字弩右手（模型像素）：grip 骨骼方块中心 */
    private static final float[] CB_RIGHT = {0.0F, -0.90F, 0.60F};

    // ---------------------------------------------------------------- ★ r96 干净基准
    /**
     * ★★ r96：手持渲染链的「干净起点」。
     *
     * <p><b>为什么需要</b>：{@code RenderHandEvent} 上不止挂了我们 —— TaCZ + SimpleBedrockModel 的
     * {@code FirstPersonRenderHandler} 也挂在同一个事件上，它给自家的枪做第一人称渲染时会**直接改事件里的
     * PoseStack**。拿**不是它家**的物品（比如我们的 AKM）时，它的 {@code Optional} 为空、什么都没画，
     * 但**改动可能已经留在栈上** ⇒ 之后原版那一遍 {@code renderArmWithItem}（枪）和我们的手臂都会被这段
     * 残留的平移/缩放带走 ⇒ 画面上就是「枪飘在手右上方、和手臂分离」。
     *
     * <p><b>做法</b>：在事件的 **HIGHEST 优先级**（还没被任何人动过）记下这一层的 pose/normal，
     * 然后在我们画手臂、以及 {@code applyForgeHandTransform} 里给枪摆位之前，把
     * {@code poseStack.last() } 覆盖回这份干净矩阵 ⇒ 枪和手永远用同一个基准。
     * 没有任何外部篡改时这就是一次无副作用的复制。
     */
    private static final org.joml.Matrix4f CLEAN_POSE = new org.joml.Matrix4f();
    private static final org.joml.Matrix3f CLEAN_NORMAL = new org.joml.Matrix3f();
    private static boolean cleanValid = false;
    /** 自上次报告以来检测到的最大「外部篡改量」（矩阵元素最大绝对差，诊断用） */
    public static volatile float externalPoseDelta = 0.0F;

    /** 在 {@code RenderHandEvent} 的 HIGHEST 优先级里调用：记下还没被别的模组改过的这一层 pose */
    public static void captureCleanPose(PoseStack pose) {
        CLEAN_POSE.set(pose.last().pose());
        CLEAN_NORMAL.set(pose.last().normal());
        cleanValid = true;
    }

    /** 把最后一层覆盖回干净矩阵；顺便量一下这次被外部改了多少（诊断） */
    public static void restoreCleanPose(PoseStack pose) {
        if (!cleanValid) return;
        org.joml.Matrix4f cur = pose.last().pose();
        float delta = 0.0F;
        for (int c = 0; c < 4; c++) {
            for (int r = 0; r < 4; r++) {
                delta = Math.max(delta, Math.abs(cur.get(c, r) - CLEAN_POSE.get(c, r)));
            }
        }
        externalPoseDelta = Math.max(externalPoseDelta, delta);
        cur.set(CLEAN_POSE);
        pose.last().normal().set(CLEAN_NORMAL);
    }

    public static void renderAkm(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light) {
        WeaponDiag.armsCalled = true;                            // 诊断
        // ★ 先把「当前帧」的枪姿态算出来：手臂在 RenderHandEvent 里画，比物品渲染早，
        //   靠「渲染时捕获」的话只能拿到上一帧的值 —— 开火那一瞬枪和手会差一帧（用户反馈的「多一帧」）。
        AkmGeoModel.captureNow();
        float p = AkmGeoModel.localReloadProgress();
        render(mc, pose, buffer, light, AkmGeoModel.frame,
                AKM_RIGHT, AkmGeoModel.leftHandPx(p, new float[3]));
    }

    public static void renderCrossbow(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light) {
        WeaponDiag.armsCalled = true;                            // 诊断
        CrossbowGeoModel.captureNow();
        render(mc, pose, buffer, light, CrossbowGeoModel.frame,
                CB_RIGHT, CrossbowGeoModel.leftHandPx(new float[3]));
    }

    /**
     * AWP：**右手**平时握在握把上（食指在扳机上），拉栓时抬起来抓拉机柄、
     * 跟着枪机一起抬起 / 后退抛壳，拉完再回握把；**左手**托在护木下方不动
     * （栓动步枪的支撑手），只在换弹时伸过去拆 / 装弹匣。
     */
    public static void renderAwp(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light) {
        WeaponDiag.armsCalled = true;                            // 诊断
        AwpGeoModel.captureNow();
        render(mc, pose, buffer, light, AwpGeoModel.frame,
                AwpGeoModel.rightHandPx(new float[3]), AwpGeoModel.leftHandPx(new float[3]));
    }

    /**
     * 手雷 / 震爆弹：**右手**握在弹体上；**左手**只在拔销 / 插销的时候出现（抓保险销拉环），
     * 投掷时绝不把左手也甩出去（用户要求「不是双手投掷动作」）。
     */
    public static void renderGrenade(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light) {
        WeaponAnim.Kind kind = GrenadePose.heldKind();
        if (kind == null) return;
        GrenadePose.captureNow(kind);
        render(mc, pose, buffer, light, GrenadePose.FRAME,
                GrenadePose.rightHandPx(kind, new float[3]),
                GrenadePose.leftHandPx(kind, new float[3]),
                GrenadePose.SHOULDER_R, GrenadePose.SHOULDER_L, GrenadePose.leftHandActive());
    }

    private static void render(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light,
                               GunFrame frame, float[] rightPx, float[] leftPx) {
        // ★★ r99：举枪（ADS）时枪模投影 FOV 会从 76° 收到 45°（≈1.69 倍放大），而肩点离眼睛只有
        //   0.8 格 ⇒ 两条手臂在屏幕上会胀成一大片皮肤色楔子，把准星/机瞷糊住（用户截图里的问题）。
        //   这里按 aim 把肩点整体往外推，让手臂在 ADS 时的**视觉粗细和长度**与腰射接近。
        float aim = 0.0F;
        WeaponAnim.Kind kind = WeaponAnim.heldKind(mc.player);
        if (kind != null) aim = Mth.clamp(WeaponAnim.of(kind).aim, 0.0F, 1.0F);
        float push = 1.0F + (ADS_SHOULDER_PUSH - 1.0F) * aim;
        render(mc, pose, buffer, light, frame, rightPx, leftPx,
                scale(SHOULDER_R, push), scale(SHOULDER_L, push), true);
    }

    /** 把肩点向量按倍率外推（相机空间、以眼睛为原点） */
    private static float[] scale(float[] v, float k) {
        return new float[]{v[0] * k, v[1] * k, v[2] * k};
    }

    /**
     * 把手画到枪 / 雷上的两个目标点。
     *
     * @param leftVisible 左手要不要画（投掷动作只动右手，左手直接不画）
     */
    private static void render(Minecraft mc, PoseStack pose, MultiBufferSource buffer, int light,
                               GunFrame frame, float[] rightPx, float[] leftPx,
                               float[] shoulderR, float[] shoulderL, boolean leftVisible) {
        AbstractClientPlayer player = mc.player;
        if (player == null) return;
        if (!(mc.getEntityRenderDispatcher().getRenderer(player) instanceof PlayerRenderer pr)) return;
        float[] handR = frame.toCamera(rightPx[0], rightPx[1], rightPx[2], new float[3]);
        if (handR == null) return;                       // 还没捕获到武器变换：这一帧不画
        drawArm(pose, buffer, light, pr, player, true, handR, shoulderR, ROLL_R);
        if (!leftVisible) return;
        float[] handL = frame.toCamera(leftPx[0], leftPx[1], leftPx[2], new float[3]);
        if (handL == null) return;
        drawArm(pose, buffer, light, pr, player, false, handL, shoulderL, ROLL_L);
    }

    /** 把手放到 hand（相机空间，格），手臂从 shoulder 方向伸出来 */
    private static void drawArm(PoseStack pose, MultiBufferSource buffer, int light, PlayerRenderer pr,
                                AbstractClientPlayer player, boolean right, float[] hand,
                                float[] shoulder, float rollDeg) {
        Vector3f y = new Vector3f(hand[0] - shoulder[0], hand[1] - shoulder[1], hand[2] - shoulder[2]);
        float dist = y.length();
        // 数值不对劲（还没捕获到 / 数据坏了）宁可这一帧不画，也别糊一大片在屏幕上
        if (!(dist > 1.0E-4F) || dist > 3.0F) return;
        // ★ r96：手臂也用「干净基准」—— 见 captureCleanPose 的说明（否则会被别的手持渲染带走）
        restoreCleanPose(pose);
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
        // ★ 必须用 setColumn 一列一列地填：JOML 的 9 参数构造是「列优先命名」
        //   （m01 = 第 0 列第 1 行），照 (x,y,z) 顺序写进去得到的是**转置矩阵** = 反向旋转 ——
        //   手臂会翻到相机后面去，近平面切一刀，屏幕上就是一大片皮肤色（r57 的 bug）。
        Quaternionf q = new Matrix3f().setColumn(0, xr)
                                      .setColumn(1, y)
                                      .setColumn(2, zr)
                                      .getNormalizedRotation(new Quaternionf());
        // 手臂方块的局部 x 中心：右臂 -0.375、左臂 +0.375（左臂在模型里是 mirror 出来的）
        float dx = (right ? -HALF : HALF) * THICK;
        float ox = xr.x * dx + y.x * ARM_LEN * s;
        float oy = xr.y * dx + y.y * ARM_LEN * s;
        float oz = xr.z * dx + y.z * ARM_LEN * s;
        pose.pushPose();
        pose.translate(hand[0] - ox, hand[1] - oy, hand[2] - oz);
        pose.mulPose(q);
        pose.scale(THICK, s, THICK);
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
