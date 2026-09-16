package cn.blockforge.generated.hexalunarcalamity.client;

/**
 * 震爆弹的客户端反馈状态：屏幕白光。
 *
 * <p>强度由服务端的 {@code ModNetwork.FlashBang} 包给出（0..1，越近越强、隔墙更弱），
 * 白光的持续时间随强度拉长，衰减到零后完全恢复。
 */
public final class ClientGrenadeState {

    private static int flashTicks = 0;
    private static int flashMax = 1;
    private static float flashStrength = 0.0F;

    private ClientGrenadeState() {}

    /** 服务端包处理（已在主线程） */
    public static void onFlash(float strength) {
        float s = Math.max(0.0F, Math.min(1.0F, strength));
        if (s <= 0.02F) return;
        int ticks = (int) (14.0F + 46.0F * s);
        if (ticks <= flashTicks && s <= flashStrength) return;
        flashTicks = ticks;
        flashMax = ticks;
        flashStrength = s;
    }

    /** 每客户端 tick 衰减一次 */
    public static void onClientTick() {
        if (flashTicks > 0) flashTicks--;
    }

    /** 当前白光的不透明度 0..1，用于铺满屏幕的白色遮罩 */
    public static float overlayAlpha() {
        if (flashTicks <= 0) return 0.0F;
        float k = flashTicks / (float) flashMax;
        // 起手最亮、尾段快速消退：白光只闪一下，之后交给致盲效果压暗屏幕
        return (float) Math.pow(k, 0.55D) * 0.92F * flashStrength;
    }

    /** 眩晕镜头：返回 0..1 的强度，随致盲与眩晕剩余时间衰减 */
    public static boolean flashActive() {
        return flashTicks > 0;
    }
}
