package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.GunPose;
import org.joml.Vector3f;

/**
 * 当前这一帧「枪本体」的变换：{@code move} 骨骼（位移 + 绕 pivot 的旋转）+ 物品 display 的平移/缩放。
 *
 * <p><b>为什么需要它</b>：第一人称的手臂（{@link WeaponArms}）要把手放在枪的某个点上
 * （握把 / 护木 / 弹匣 / 拉机柄 / 弩弦）。可枪不是固定不动的——举枪（ADS）会把整把枪挪到
 * 屏幕正中，换弹 / 跑步 / 开火动画也在推 {@code move} 骨骼。手必须跟着一起动。
 *
 * <p><b>为什么是上一帧</b>：GeckoLib 的骨骼是在**物品渲染时**才算出来的，而手臂在
 * {@code RenderHandEvent} 里就画了（比物品早）。所以模型在算完骨骼后把结果存到这里，
 * 手臂读的是上一帧的值 —— 晚一帧跟随，肉眼看不出来（枪也是同一套数据推的）。
 *
 * <p><b>变换链</b>（与 {@code WeaponMount} 同一口径，单位：模型像素 → 格）：<br>
 * {@code p1 = pivot + pos + R(rot)·(p − pivot)}，{@code 相机 = ARM(±0.56,-0.52,-0.72) + (t + S·p1)/16}
 */
public final class GunFrame {

    private boolean valid;
    /** display 平移（模型像素） */
    private float tx;
    private float ty;
    private float tz;
    /** display 缩放 */
    private float scale = 1.0F;
    /** move 骨骼 pivot（模型像素） */
    private float pivotX;
    private float pivotY;
    private float pivotZ;
    /** move 骨骼位移（模型像素） */
    private float posX;
    private float posY;
    private float posZ;
    /** move 骨骼旋转（弧度） */
    private float rotX;
    private float rotY;
    private float rotZ;
    /**
     * 捕获这一帧时的「举枪进度」（0 腰射 / 1 举枪）。
     *
     * <p>它决定枪身那段 {@link GunPose} 姿态（腰射时枪身偏出去、举枪收回正），
     * 所以必须和这一帧的枪一起记下来：用当前值而不是捕获时的值，手就会在过渡期间脱手。
     */
    private float aim = 1.0F;

    /** 由各武器的 GeoModel 在算完 {@code move} 骨骼后调用 */
    void capture(float dispTx, float dispTy, float dispTz, float dispScale,
                 float pivotX, float pivotY, float pivotZ,
                 float posX, float posY, float posZ,
                 float rotX, float rotY, float rotZ) {
        capture(dispTx, dispTy, dispTz, dispScale, pivotX, pivotY, pivotZ,
                posX, posY, posZ, rotX, rotY, rotZ, 1.0F);
    }

    /** 带举枪进度的版本（枪械用；手雷这类不叠 GunPose 的走上面那个重载） */
    void capture(float dispTx, float dispTy, float dispTz, float dispScale,
                 float pivotX, float pivotY, float pivotZ,
                 float posX, float posY, float posZ,
                 float rotX, float rotY, float rotZ, float aimNow) {
        this.aim = aimNow;
        WeaponDiag.frameAim = aimNow;                 // 诊断用（枪与手臂共用同一份 aim）
        this.tx = dispTx;
        this.ty = dispTy;
        this.tz = dispTz;
        this.scale = dispScale;
        this.pivotX = pivotX;
        this.pivotY = pivotY;
        this.pivotZ = pivotZ;
        this.posX = posX;
        this.posY = posY;
        this.posZ = posZ;
        this.rotX = rotX;
        this.rotY = rotY;
        this.rotZ = rotZ;
        this.valid = true;
    }

    /** 模型像素点 → 相机空间（格）；还没捕获过返回 null（那一帧干脆不画手臂） */
    public float[] toCamera(float x, float y, float z, float[] out) {
        if (!valid) return null;
        float c1 = (float) Math.cos(rotX);
        float s1 = (float) Math.sin(rotX);
        float c2 = (float) Math.cos(rotY);
        float s2 = (float) Math.sin(rotY);
        float c3 = (float) Math.cos(rotZ);
        float s3 = (float) Math.sin(rotZ);
        // R = Rx·Ry·Rz
        float DX = x - pivotX;
        float DY = y - pivotY;
        float DZ = z - pivotZ;
        float ox = (c2 * c3) * DX + (-c2 * s3) * DY + s2 * DZ;
        float oy = (s1 * s2 * c3 + c1 * s3) * DX + (-s1 * s2 * s3 + c1 * c3) * DY + (-s1 * c2) * DZ;
        float oz = (-c1 * s2 * c3 + s1 * s3) * DX + (c1 * s2 * s3 + s1 * c3) * DY + (c1 * c2) * DZ;
        // display 那一段（平移 + 缩放）先算成相机空间向量，再过 GunPose 的姿态
        // （与枪的 pose 链同序：Trans(ARM) · GunPose · Trans(display) · R · S · 模型点）
        Vector3f v = new Vector3f((tx + scale * (pivotX + posX + ox)) / 16.0F,
                (ty + scale * (pivotY + posY + oy)) / 16.0F,
                (tz + scale * (pivotZ + posZ + oz)) / 16.0F);
        GunPose.transform(aim, v);
        out[0] = (float) WeaponArms.ARM_X + v.x;
        out[1] = WeaponArms.baseY() + v.y;
        out[2] = (float) WeaponArms.ARM_Z + v.z;
        return out;
    }
}
