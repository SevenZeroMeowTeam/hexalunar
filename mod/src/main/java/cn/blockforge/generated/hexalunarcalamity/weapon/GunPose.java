package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.util.Mth;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * 第一人称「持枪姿态 + 枪模投影」——照 TaCZ（永恒枪械工坊）那套做。
 *
 * <h2>TaCZ 是怎么让它"像把枪"的</h2>
 * <ol>
 *   <li><b>枪模用独立投影</b>：它的枪配置里写着 {@code "zoom_model_fov": 45} —— 世界视角照常缩到
 *       4 倍 / 8 倍，<b>枪模那一遍却固定用 45° 投影</b>（原版手持是 70°），所以镜里世界被放大时
 *       枪本体的大小不受影响（45° 比 70° 大 1.69 倍，正好是"抵肩贴近眼睛"的那种观感）。</li>
 *   <li><b>腰射时枪身偏出去</b>：枪不沿视线摆，而是往右下并带一点偏航/倾斜，举枪时才收回来对正。</li>
 *   <li><b>举枪时枪模变大</b>：{@code 45°} 只在举枪（aim → 1）时生效，腰射仍按原版 70°。</li>
 * </ol>
 *
 * <h2>这里怎么落地（★ r85 起重构）</h2>
 * <b>举枪位移改走「姿态层」</b>而不是模型骨骼：原版手持那一遍的变换链是
 * <pre>
 * 相机空间 = Trans(±0.56, −0.52, −0.72) · {@link #matrix}(姿态) · Trans(display/16) · R · S · (模型像素/16)
 * </pre>
 * 我们从 {@code WeaponHandGrip.apply} 里亲手填这一段，所以它**一定生效**；
 * 而骨骼那条路（在 {@code setCustomAnimations} 里推 {@code move}）会被动画的关键帧遮掉：
 * AKM 的 {@code reload} 动画就带着 {@code move.position = [0, −1.2, 0] / rotX +7°}，
 * 画面上就是「换弹时枪和双手往下沉」——用户反馈过两次。
 * 现在举枪位移、腰射姿态、开火上抬**全部只在姿态层算一份**，
 * 手臂（{@code GunFrame}）、枪口/抛壳点（{@link WeaponMount} → 服务器弹道）都读它，三者永不脱节。
 *
 * <p>★ 举枪时本变换的<b>旋转必须是单位阵</b>：AKM / AWP 的对准靠"举枪只做平移"（把照门—准星
 * 或镜筒光轴那条线顶到屏幕中心），一旦举枪还残留角度，轴线就会离开屏幕中心。
 */
public final class GunPose {

    /** TaCZ 的 {@code zoom_model_fov}：举枪时枪模用的投影 FOV（45° ⇒ 比原版手持大 1.69 倍） */
    public static final float MODEL_FOV_AIM = 45.0F;

    /**
     * ★ r94：AWP 的 {@code zoom_model_fov} —— TaCZ 的 {@code ai_awp_display.json} 写的是 **35**。
     *
     * <p>（同一份配置里 {@code iron_zoom = 1.5}；它挂的 8 倍镜是
     * {@code scope_standard_8x_display.json}：{@code zoom = [5, 10]}、{@code views_fov = 20}、
     * {@code "scope": true} ⇒ 看镜时枪模用 20°，但那时整把枪被镜筒遮住，所以这里用不上。）
     */
    public static final float MODEL_FOV_AIM_AWP = 25.0F;
    /**
     * 腰射时的枪模 FOV。原版手持那一遍本来就用 70°（{@code GameRenderer.renderItemInHand} 里
     * {@code getFov(camera, partial, false)} —— 那个 {@code false} 表示"不套 fov 设置与各种修正"）。
     *
     * <p>★ r98：70 → **76**。用户拿标注图指出「枪要往左下靠、手臂要往右上收，两者贴在一起」——
     * 放宽一点枪模投影就是「屏幕上的枪和手臂一起向画面中心收」，正是他要的构图；
     * 同时枪会略小一点（腰射时不再顶到右下角）。举枪（ADS）那一路不受影响（照门/准星靠平移对齐）。
     */
    public static final float MODEL_FOV_HIP = 76.0F;

    // ---------------------------------------------------------------- 腰射姿态（TaCZ 风格）
    /** 枪口略偏左：屏幕上就能看到枪身右侧，而不是对着一根正对着你的管子 */
    public static final float HIP_YAW = 4.0F;
    /** 枪口略抬 */
    public static final float HIP_PITCH = 1.6F;
    /** 屏幕上看枪身略微顺时针倒一点 */
    public static final float HIP_ROLL = -3.0F;
    /** 相机空间偏移（格）：往右下、略近一点 */
    public static final float HIP_DX = 0.02F;
    public static final float HIP_DY = 0.04F;
    public static final float HIP_DZ = 0.05F;

    /**
     * 当前武器的「举枪位移」（相机空间、单位<b>格</b>）：
     * [0..2] = xyz，[3] = 开火上抬（AWP 用），[4] = 举枪时的横滚（度，TaCZ 那种"从侧上方看枪顶"的构图），
     * [5] = ★ r93 开火俯仰（度，**绕手/握把**：正 = 枪管上抬 + 枪托下沉，AWP 用）。
     *
     * <p>由各武器在每帧的渲染/取帧路径写入（{@code WeaponHandGrip.apply} 与各 {@code captureNow()}
     * 写的是同一份值），手臂与枪都从这里取，所以不会错开。
     */
    public static final float[] ADS = new float[6];

    /** {@link #transform} 复用的一块四元数（客户端渲染单线程，不会并发） */
    private static final Quaternionf PITCH = new Quaternionf();

    /** 写入举枪位移（格）。lift 不受 aim 缩放：那是开火那一瞬的上抬 */
    public static void setAds(float x, float y, float z, float lift, float rollDeg) {
        setAds(x, y, z, lift, rollDeg, 0.0F);
    }

    /** ★ r93：再带一个「开火俯仰」（度，绕手/握把转：正 = 枪管上抬 + 枪托下沉） */
    public static void setAds(float x, float y, float z, float lift, float rollDeg, float firePitch) {
        ADS[0] = x;
        ADS[1] = y;
        ADS[2] = z;
        ADS[3] = lift;
        ADS[4] = rollDeg;
        ADS[5] = firePitch;
    }

    /** 不是我们这套武器时清零（否则换枪那一帧会残留上一把的位移） */
    public static void clearAds() {
        setAds(0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F);
    }

    /** 当前 aim 下的枪模投影 FOV（默认 45°，TaCZ 的 AK47 值） */
    public static float modelFov(double aim) {
        return modelFov(false, aim);
    }

    /**
     * ★ r94：按枪取「举枪时的枪模投影 FOV」—— 参考 TaCZ 各枪自己的 {@code zoom_model_fov}：
     * <b>AK47 = 45 / AWP(ai_awp) = 35</b>。腰射一律 70（= 原版手持那一遍，枪的大小不变）。
     *
     * <p>参数用 {@code boolean} 而不是 {@code WeaponAnim.Kind}，是为了不让 weapon 包反向依赖
     * client 包 —— {@link #transform} 会在**服务端**算弹道时被调用，一旦签名里出现客户端类，
     * 专用服务器加载本类时就可能炸。
     */
    public static float modelFov(boolean awp, double aim) {
        float aimFov = awp ? MODEL_FOV_AIM_AWP : MODEL_FOV_AIM;
        return (float) (MODEL_FOV_HIP + (aimFov - MODEL_FOV_HIP) * aim01(aim));
    }

    /**
     * 把「腰射姿态 → 举枪位移」按 aim 插进 {@code out}（用 {@link #ADS} 里那一份）。
     * 顺序必须是 {@code 平移 · 旋转}，与 {@link #transform} 一致。
     */
    public static void matrix(float aim, Matrix4f out) {
        matrix(aim, ADS[0], ADS[1], ADS[2], ADS[3], ADS[4], ADS[5], out);
    }

    /**
     * 同上，但举枪位移由调用方给（服务器侧算弹道时用：那边读不到客户端写的 {@link #ADS}）。
     *
     * <p>★ r88：乘法顺序改成 {@code Rz(横滚) · Trans(位移) · R(腰射姿态)}。
     * 矩阵里**最后一个乘上去的变换最先作用在模型点上**，所以这个顺序 = 「先给模型点套腰射姿态，
     * 再平移到位，最后绕<b>眼睛</b>（相机原点）横滚」。为什么横滚必须最后：举枪平移把
     * 瞄准参照点（照门顶 / 镜筒光轴）顶到了眼睛上，而绕眼睛旋转时**眼睛本身不动**
     * ⇒ 准星 / 光轴依旧钉在屏幕中心，只有枪身绕它甩开（就是 TaCZ 那种「枪身斜插在右下角」）。
     * r87 写成了「先平移后横滚」，那等于绕**模型原点**转：准星被甩出屏幕中心（用户反馈「瞄准不对」），
     * 手与枪也错开了（「手臂和枪分离」）。
     *
     * <p>★ r93：再多一个 {@code firePitch}（开火俯仰，度），它乘在**最后**（最先作用于模型点）
     * ⇒ 绕的枢轴是**手 / 握把**（姿态原点 = 原版手部基准），所以「枪管上抬、枪托下沉」，
     * 而不是整枪平移抬高。手臂走同一个 {@code transform()}，所以双手跟着一起动、不会脱手。
     */
    public static void matrix(float aim, float adsX, float adsY, float adsZ, float lift,
                              float rollDeg, Matrix4f out) {
        matrix(aim, adsX, adsY, adsZ, lift, rollDeg, 0.0F, out);
    }

    /** 带开火俯仰的重载（见 {@link #matrix(float, float, float, float, float, float, Matrix4f)}） */
    public static void matrix(float aim, float adsX, float adsY, float adsZ, float lift,
                              float rollDeg, float firePitch, Matrix4f out) {
        float a = aim01(aim);
        float k = 1.0F - a;
        out.identity();
        if (rollDeg != 0.0F) {
            out.rotateZ(rollDeg * a * Mth.DEG_TO_RAD);      // 绕眼睛（最先作用于结果）
        }
        out.translate(HIP_DX * k + adsX * a, HIP_DY * k + adsY * a + lift, HIP_DZ * k + adsZ * a);
        if (k > 1.0E-4F) {
            out.rotate(quat(k));                            // 腰射姿态：绕模型原点
        }
        if (firePitch != 0.0F) {
            out.rotateX(firePitch * Mth.DEG_TO_RAD);        // ★ 开火俯仰：绕手（最先作用在模型点上）
        }
    }

    /**
     * 同一个姿态作用在「相机空间向量」上（{@code GunFrame} 把模型点换成手位、
     * {@link WeaponMount} 把枪口/抛壳点换成世界坐标都走这里）。
     */
    public static void transform(float aim, Vector3f v) {
        transform(aim, ADS[0], ADS[1], ADS[2], ADS[3], ADS[4], ADS[5], v);
    }

    /** 同上，举枪位移由调用方给（服务器侧弹道）；顺序与 {@link #matrix} 严格一致 */
    public static void transform(float aim, float adsX, float adsY, float adsZ, float lift,
                                 float rollDeg, Vector3f v) {
        transform(aim, adsX, adsY, adsZ, lift, rollDeg, 0.0F, v);
    }

    /** ★ r93：带开火俯仰的重载 —— 俯仰**最先**作用（绕手/握把），与 {@link #matrix} 同序。
     *  这里用 JOML 的四元数（而不是手写三角函数），保证和 {@code matrix} 的 {@code rotateX}
     *  用的是同一套旋向 ⇒ 枪和手臂绝不会朝相反方向转。 */
    public static void transform(float aim, float adsX, float adsY, float adsZ, float lift,
                                 float rollDeg, float firePitch, Vector3f v) {
        float a = aim01(aim);
        float k = 1.0F - a;
        if (firePitch != 0.0F) {
            PITCH.set(0.0F, 0.0F, 0.0F, 1.0F)
                    .rotateX(firePitch * Mth.DEG_TO_RAD);
            PITCH.transform(v);
        }
        if (k > 1.0E-4F) {
            quat(k).transform(v);
        }
        v.x += HIP_DX * k + adsX * a;
        v.y += HIP_DY * k + adsY * a + lift;
        v.z += HIP_DZ * k + adsZ * a;
        if (rollDeg != 0.0F) {
            float r = rollDeg * a * Mth.DEG_TO_RAD;         // 绕眼睛（最后作用）
            float c = Mth.cos(r);
            float s = Mth.sin(r);
            float x = v.x * c - v.y * s;
            float y = v.x * s + v.y * c;
            v.x = x;
            v.y = y;
        }
    }

    /** 不带 lift/roll 的旧口径（手雷等不用举枪位移的调用点） */
    public static void transform(float aim, float adsX, float adsY, float adsZ, Vector3f v) {
        transform(aim, adsX, adsY, adsZ, 0.0F, 0.0F, v);
    }

    private static Quaternionf quat(float k) {
        return new Quaternionf().rotateXYZ(HIP_PITCH * k * Mth.DEG_TO_RAD,
                HIP_YAW * k * Mth.DEG_TO_RAD, HIP_ROLL * k * Mth.DEG_TO_RAD);
    }

    private static float aim01(double aim) {
        return (float) Mth.clamp(aim, 0.0D, 1.0D);
    }

    private GunPose() {
    }
}
