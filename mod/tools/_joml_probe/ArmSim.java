import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * 手臂摆放模拟器：把「修好之后」的 WeaponArms.drawArm 数学原样抄一遍，
 * 算出两只手臂方块的 8 个角在相机空间的位置，再按 70° FOV / 16:9 投影到屏幕，
 * 用来离线确认手臂不会糊屏（z 越过 0 = 跑到相机后面去了 = r57 那个 bug）。
 *
 * <p>数值取自 AKM / 十字弩的实际 display 与瞄准点，肩点也用 WeaponArms 里的常数。
 */
public class ArmSim {

    static final float ARM_X = 0.56f, ARM_Y = -0.52f, ARM_Z = -0.72f;
    static final float ARM_LEN = 0.75f, HALF = 0.375f;
    static final float[] SHOULDER_R = {0.62f, -0.70f, -0.42f};
    static final float[] SHOULDER_L = {0.05f, -0.72f, -0.50f};
    static final float ROLL_R = 155f, ROLL_L = 24f;
    /** 宽高比与垂直 FOV（原版默认 70°，屏 1920x1080） */
    static final float VFOV = 70f, ASPECT = 1920f / 1080f;

    /** 与修好后的 WeaponArms.drawArm 一致：返回 origin(3) 与四元数，并打印方块包围盒 */
    static void drawArm(boolean right, float[] hand, float[] shoulder, float rollDeg, String tag) {
        Vector3f y = new Vector3f(hand[0] - shoulder[0], hand[1] - shoulder[1], hand[2] - shoulder[2]);
        float dist = y.length();
        if (!(dist > 1.0E-4f) || dist > 4.0f) {
            System.out.println(tag + ": 距离异常 " + dist + " → 不画");
            return;
        }
        float s = dist / ARM_LEN;                              // 与 Java 一致：不夹取
        y.div(dist);
        Vector3f ref = new Vector3f(0, 1, 0);
        if (Math.abs(y.dot(ref)) > 0.95f) ref.set(0, 0, -1);
        Vector3f z = new Vector3f(y).cross(ref).normalize();
        Vector3f x = new Vector3f(y).cross(z).normalize();
        float r = rollDeg * (float) Math.PI / 180f;
        float cr = (float) Math.cos(r), sr = (float) Math.sin(r);
        Vector3f xr = new Vector3f(x).mul(cr).add(new Vector3f(z).mul(sr));
        Vector3f zr = new Vector3f(z).mul(cr).sub(new Vector3f(x).mul(sr));
        Quaternionf q = new Matrix3f().setColumn(0, xr).setColumn(1, y).setColumn(2, zr)
                .getNormalizedRotation(new Quaternionf());
        float dx = right ? -HALF : HALF;                       // 方块局部 x 中心
        Vector3f origin = new Vector3f(
                hand[0] - (xr.x * dx + y.x * ARM_LEN * s),
                hand[1] - (xr.y * dx + y.y * ARM_LEN * s),
                hand[2] - (xr.z * dx + y.z * ARM_LEN * s));

        // 方块局部：右臂 x[-0.5,-0.25]，左臂 x[0.25,0.5]，y[0,0.75]，z[-0.125,0.125]
        float[] xs = right ? new float[]{-0.5f, -0.25f} : new float[]{0.25f, 0.5f};
        float zmin = 1e9f, zmax = -1e9f;
        float sxmin = 1e9f, sxmax = -1e9f, symin = 1e9f, symax = -1e9f;
        float tanHalf = (float) Math.tan(Math.toRadians(VFOV / 2));
        for (float lx : xs) {
            for (float ly : new float[]{0f, 0.75f}) {
                for (float lz : new float[]{-0.125f, 0.125f}) {
                    Vector3f v = new Vector3f(lx, ly * s, lz);
                    q.transform(v);
                    v.add(origin);
                    zmin = Math.min(zmin, v.z);
                    zmax = Math.max(zmax, v.z);
                    if (v.z < -1e-3f) {                        // 在相机前面才能投影
                        float ndcX = (v.x / -v.z) / (tanHalf * ASPECT);
                        float ndcY = (v.y / -v.z) / tanHalf;
                        sxmin = Math.min(sxmin, ndcX);
                        sxmax = Math.max(sxmax, ndcX);
                        symin = Math.min(symin, ndcY);
                        symax = Math.max(symax, ndcY);
                    }
                }
            }
        }
        System.out.printf("%s: dist=%.3f s=%.3f  z=[%.3f,%.3f] %s%n",
                tag, dist, s, zmin, zmax, zmin > -0.02f ? "★ 越过/贴上相机 = 糊屏" : "OK（都在相机前面）");
        if (sxmin < 1e8f) {
            System.out.printf("     屏幕 x %s   y %s  (屏幕右 = +2, 上 = +2)%n",
                    rect(sxmin, sxmax), rect(symin, symax));
            System.out.printf("     → 像素 %s x  %s y%n",
                    px(sxmin, sxmax, 1920), px(symin, symax, 1080));
        }
    }

    static String rect(float a, float b) {
        return String.format("[%.2f, %.2f]", a, b);
    }

    static String px(float a, float b, int total) {
        return String.format("[%.0f, %.0f]", (a + 1f) / 2f * total, (b + 1f) / 2f * total);
    }

    /** 模型像素 → 相机空间（GunFrame.toCamera） */
    static float[] toCamera(float[] t, float scale, float[] px, float[] pivot) {
        return new float[]{
                ARM_X + (t[0] + scale * px[0]) / 16f,
                ARM_Y + (t[1] + scale * px[1]) / 16f,
                ARM_Z + (t[2] + scale * px[2]) / 16f};
    }

    public static void main(String[] args) {
        float[] akmT = {-2.6f, 1.4f, 1.8f};
        float[] zeroPivot = {0, 1.75f, 0};   // move pivot（pos/rot 都按 0 算：静止不动时）
        System.out.println("--- AKM 静止（左手托护木 / 右手握把）---");
        float[] akmR = toCamera(akmT, 1f, new float[]{0f, 0.55f, -0.15f}, zeroPivot);
        float[] akmL = toCamera(akmT, 1f, new float[]{0f, 2.05f, -6.30f}, zeroPivot);
        line("右手", akmR);
        drawArm(true, akmR, SHOULDER_R, ROLL_R, "AKM 右臂");
        line("左手", akmL);
        drawArm(false, akmL, SHOULDER_L, ROLL_L, "AKM 左臂");

        System.out.println("\n--- 十字弩 静止（左手扶弦）---");
        float[] cbT = {0f, 0f, 0f};
        float[] cbR = toCamera(cbT, 0.8f, new float[]{0f, -0.90f, 0.60f}, zeroPivot);
        float[] cbL = toCamera(cbT, 0.8f, new float[]{0.26f, 0.22f, -5.20f}, zeroPivot);
        line("右手", cbR);
        drawArm(true, cbR, SHOULDER_R, ROLL_R, "弩 右臂");
        line("左手", cbL);
        drawArm(false, cbL, SHOULDER_L, ROLL_L, "弩 左臂");
    }

    static void line(String who, float[] p) {
        System.out.printf("%s 手点(相机空间格) = (%.3f, %.3f, %.3f)%n", who, p[0], p[1], p[2]);
    }
}
