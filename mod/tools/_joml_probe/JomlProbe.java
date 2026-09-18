import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * JOML 语义探针：确认 Matrix3f 9 参数构造 / getNormalizedRotation / rotateAxis 的约定，
 * 并比较「当前 WeaponArms.drawArm 的算法」与候选修法把手臂方块放到了哪里。
 */
public class JomlProbe {

    static float[] ARM = {0.56f, -0.52f, -0.72f};
    static float HALF = 0.375f;
    static float ARM_LEN = 0.75f;

    public static void main(String[] args) {
        // 取一个贴近实战的「肩 → 手」方向（右手握把）
        float[] hand = {0.3975f, -0.3981f, -0.6169f};
        float[] shoulder = {0.72f, -1.00f, -0.20f};
        Vector3f y = new Vector3f(hand[0] - shoulder[0], hand[1] - shoulder[1], hand[2] - shoulder[2]);
        float dist = y.length();
        float s = dist / ARM_LEN;
        y.div(dist);
        Vector3f ref = new Vector3f(0, 1, 0);
        if (Math.abs(y.dot(ref)) > 0.95f) ref.set(0, 0, -1);
        Vector3f z = new Vector3f(y).cross(ref).normalize();
        Vector3f x = new Vector3f(y).cross(z).normalize();
        System.out.printf("y = %s  s = %.4f%n", fmt(y), s);
        System.out.printf("x = %s%nz = %s%n", fmt(x), fmt(z));

        for (float rollDeg : new float[]{0f, 24f, 155f}) {
            float r = rollDeg * (float) Math.PI / 180f;
            float cr = (float) Math.cos(r), sr = (float) Math.sin(r);
            Vector3f xr = new Vector3f(x).mul(cr).add(new Vector3f(z).mul(sr));
            Vector3f zr = new Vector3f(z).mul(cr).sub(new Vector3f(x).mul(sr));

            System.out.println("\n=== roll " + rollDeg + " ===");
            // A: 现在的写法（9 参数构造 + getNormalizedRotation）
            Matrix3f mA = new Matrix3f(xr.x, y.x, zr.x, xr.y, y.y, zr.y, xr.z, y.z, zr.z);
            Quaternionf qA = mA.getNormalizedRotation(new Quaternionf());
            Vector3f aY = qA.transform(new Vector3f(0, 1, 0));
            Vector3f aX = qA.transform(new Vector3f(1, 0, 0));
            System.out.printf("A 9参数 : q=(%.3f,%.3f,%.3f,%.3f)  localY-> %s (期望 %s)   localX-> %s (期望 %s)%n",
                    qA.x, qA.y, qA.z, qA.w, fmt(aY), fmt(y), fmt(aX), fmt(xr));

            // B: 显式 setColumn（列 = 基向量的像）
            Matrix3f mB = new Matrix3f().setColumn(0, xr).setColumn(1, y).setColumn(2, zr);
            Quaternionf qB = mB.getNormalizedRotation(new Quaternionf());
            Vector3f bY = qB.transform(new Vector3f(0, 1, 0));
            Vector3f bX = qB.transform(new Vector3f(1, 0, 0));
            System.out.printf("B setCol: q=(%.3f,%.3f,%.3f,%.3f)  localY-> %s   localX-> %s%n",
                    qB.x, qB.y, qB.z, qB.w, fmt(bY), fmt(bX));

            // 手臂方块的 8 个角（模型局部：x[-0.375±0.125] 中心 -0.375、y[0,0.75]、z ±0.125）
            // 用 A 的写法：origin = hand - (xr*HALF + y*ARM_LEN*s)，然后 scale(1,s,1)
            Vector3f originA = new Vector3f(hand[0], hand[1], hand[2])
                    .sub(new Vector3f(xr).mul(HALF)).sub(new Vector3f(y).mul(ARM_LEN * s));
            float[] zRangeA = cornerZRange(originA, qA, s);
            System.out.printf("A 方块 z 范围: %.3f .. %.3f   (z>0 = 跑到相机后面了)%n", zRangeA[0], zRangeA[1]);

            Vector3f originB = new Vector3f(hand[0], hand[1], hand[2])
                    .sub(new Vector3f(xr).mul(HALF)).sub(new Vector3f(y).mul(ARM_LEN * s));
            float[] zRangeB = cornerZRange(originB, qB, s);
            System.out.printf("B 方块 z 范围: %.3f .. %.3f%n", zRangeB[0], zRangeB[1]);

            // C: rotationTo + rotateAxis
            Quaternionf qC = new Quaternionf().rotationTo(new Vector3f(0, 1, 0), y);
            Quaternionf qRoll = new Quaternionf().rotationAxis(r, 0, 1, 0);
            qC.mul(qRoll);
            Vector3f cY = qC.transform(new Vector3f(0, 1, 0));
            Vector3f cX = qC.transform(new Vector3f(1, 0, 0));
            System.out.printf("C rotTo*mulAxis: localY-> %s   localX-> %s (期望 %s)  %s%n",
                    fmt(cY), fmt(cX), fmt(xr), cY.dot(y) > 0.999f && cX.dot(xr) > 0.999f ? "OK" : "不匹配");
        }
    }

    /** 把手臂方块（局部 x[-0.5,-0.25] 中心 -0.375, y[0,0.75], z[-0.125,0.125]）变换后 z 的极值 */
    static float[] cornerZRange(Vector3f origin, Quaternionf q, float s) {
        float zmin = Float.MAX_VALUE, zmax = -Float.MAX_VALUE;
        for (float lx : new float[]{-0.5f, -0.25f}) {
            for (float ly : new float[]{0f, 0.75f}) {
                for (float lz : new float[]{-0.125f, 0.125f}) {
                    Vector3f v = new Vector3f(lx, ly * s, lz);   // scale(1,s,1) 在局部之后
                    q.transform(v);
                    float z = origin.z + v.z;
                    zmin = Math.min(zmin, z);
                    zmax = Math.max(zmax, z);
                }
            }
        }
        return new float[]{zmin, zmax};
    }

    static String fmt(Vector3f v) {
        return String.format("(%.3f,%.3f,%.3f)", v.x, v.y, v.z);
    }
}
