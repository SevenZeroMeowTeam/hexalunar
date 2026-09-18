package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 十字弩上弦动画：按 {@code WeaponAnim.CROSSBOW.reload}（0..1）逐帧算出弩箭与左手的位移。
 *
 * <p>节奏（与 {@link CrossbowWeaponItem#RELOAD_TICKS} = 30 tick 对应）：
 * <ol>
 *   <li>0.00 – 0.62：左手抓住弦中点往后拉（模型本体切到 pulling_0/1/2 三段弦形）</li>
 *   <li>0.45 – 0.95：弩箭从后方滑进箭槽（与拉弦后半段重叠，看起来像「拉满的同时推箭入槽」）</li>
 *   <li>0.80 – 1.00：左手松手撤走，弩箭留槽</li>
 * </ol>
 * 上弦完成后（{@code st.loaded}）弩箭常驻箭槽，直到击发才消失。
 *
 * <p>做法与 {@link AkmPartAnim} 一致：只平移顶点前 3 个 float，法线不动，光照自然正确。
 */
public final class CrossbowPartAnim {

    private static final int TICKS = CrossbowWeaponItem.RELOAD_TICKS;
    /** 每个顶点 8 个 int：xyz(3 float) + color + uv + light + normal */
    private static final int VERTEX_STRIDE = 8;

    /** 弦静止时中点的模型坐标（两凸轮之间平直横跨） */
    private static final float STRING_REST_Y = 3.64F;
    private static final float STRING_REST_Z = 1.80F;
    /** 弦拉到弦爪上的位置 —— 与建模脚本里的 STRING_LATCH 一致 */
    private static final float STRING_LATCH_Y = 3.60F;
    private static final float STRING_LATCH_Z = -2.50F;

    /** 拉弦阶段与推箭阶段在 0..1 进度里的分界 */
    private static final float PULL_END = 0.62F;
    private static final float BOLT_START = 0.45F;
    private static final float BOLT_END = 0.95F;
    private static final float HAND_RELEASE = 0.80F;
    /** 弩箭入场时的后方/上方偏移（模型坐标） */
    private static final float BOLT_IN_Z = 3.4F;
    private static final float BOLT_IN_Y = 0.55F;
    /** 松手后左手再往后撤一点 */
    private static final float HAND_EXIT_Z = 1.4F;

    /** 缓存槽：0..TICKS = 上弦中；+1 = 已上弦（弩箭留槽）；+2 = 空 */
    private static final int SLOT_LOADED = TICKS + 1;
    private static final int SLOT_EMPTY = TICKS + 2;
    private static final List<BakedQuad>[] BOLT_CACHE = new List[SLOT_EMPTY + 1];
    private static final List<BakedQuad>[] HAND_CACHE = new List[SLOT_EMPTY + 1];

    private CrossbowPartAnim() {
    }

    /** 资源重载会重新烘焙模型，缓存的顶点引用了失效 sprite，必须清空 */
    @SuppressWarnings("unchecked")
    public static void invalidate() {
        java.util.Arrays.fill(BOLT_CACHE, null);
        java.util.Arrays.fill(HAND_CACHE, null);
    }

    private static int slot(WeaponAnim.State st) {
        if (st.reload < 0.0F) {
            return st.loaded ? SLOT_LOADED : SLOT_EMPTY;
        }
        return Mth.clamp(Math.round(st.reload * TICKS), 0, TICKS);
    }

    /** 当前帧是不是「第一人称、且没在举弩」—— 举弩时原版自己会画手臂，别叠两个左手 */
    private static boolean firstPersonFreeHand(WeaponAnim.State st) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.screen != null || mc.player == null) return false;
        if (mc.getCameraEntity() != mc.player) return false;
        if (!mc.options.getCameraType().isFirstPerson()) return false;
        return !mc.player.isUsingItem();
    }

    /** 弩箭分件：上弦后半段滑入，挂弦后常驻 */
    public static List<BakedQuad> boltQuads(RandomSource rand) {
        BakedModel model = CrossbowPartModels.bolt();
        if (model == null) return Collections.emptyList();
        WeaponAnim.State st = WeaponAnim.of(WeaponAnim.Kind.CROSSBOW);
        int slot = slot(st);
        List<BakedQuad> cached = BOLT_CACHE[slot];
        if (cached != null) return cached;

        float t = st.reload;
        List<BakedQuad> result;
        if (t >= 0.0F && t < BOLT_START) {
            result = Collections.emptyList();               // 还没推箭
        } else {
            float k = t < 0.0F ? 1.0F : Mth.clamp((t - BOLT_START) / (BOLT_END - BOLT_START), 0.0F, 1.0F);
            k = k * k * (3.0F - 2.0F * k);                  // 平滑进出
            List<BakedQuad> source = model.getQuads(null, null, rand);
            result = (k >= 1.0F) ? source : translate(source,
                    0.0F, (1.0F - k) * BOLT_IN_Y, (1.0F - k) * BOLT_IN_Z);
        }
        BOLT_CACHE[slot] = result;
        return result;
    }

    /** 左手分件：跟着弦中点走，拉满后松手撤走；只在第一人称、手空着时出现 */
    public static List<BakedQuad> handQuads(RandomSource rand) {
        BakedModel model = CrossbowPartModels.hand();
        if (model == null) return Collections.emptyList();
        WeaponAnim.State st = WeaponAnim.of(WeaponAnim.Kind.CROSSBOW);
        if (st.reload < 0.0F || !firstPersonFreeHand(st)) return Collections.emptyList();
        int slot = slot(st);
        List<BakedQuad> cached = HAND_CACHE[slot];
        if (cached != null) return cached;

        float t = st.reload;
        List<BakedQuad> result;
        if (t > HAND_RELEASE) {
            result = Collections.emptyList();               // 松手撤走
        } else {
            float k = Mth.clamp(t / PULL_END, 0.0F, 1.0F);  // 拉弦进度
            float dz = STRING_LATCH_Z - STRING_REST_Z;      // < 0：往射手方向
            float dy = STRING_LATCH_Y - STRING_REST_Y;
            float exit = Mth.clamp((t - 0.70F) / 0.10F, 0.0F, 1.0F) * HAND_EXIT_Z;
            List<BakedQuad> source = model.getQuads(null, null, rand);
            result = translate(source, 0.0F, k * dy, k * dz + exit);
        }
        HAND_CACHE[slot] = result;
        return result;
    }

    private static List<BakedQuad> translate(List<BakedQuad> source, float dx, float dy, float dz) {
        List<BakedQuad> out = new ArrayList<>(source.size());
        for (BakedQuad quad : source) {
            out.add(translate(quad, dx, dy, dz));
        }
        return out;
    }

    /** 只平移位置（顶点前 3 个 float），其余字节原样拷贝 —— 法线不变，故光照正确 */
    @Nullable
    private static BakedQuad translate(BakedQuad quad, float dx, float dy, float dz) {
        int[] src = quad.getVertices();
        int[] dst = new int[src.length];
        System.arraycopy(src, 0, dst, 0, src.length);
        for (int i = 0; i + 2 < dst.length; i += VERTEX_STRIDE) {
            dst[i] = Float.floatToRawIntBits(Float.intBitsToFloat(src[i]) + dx);
            dst[i + 1] = Float.floatToRawIntBits(Float.intBitsToFloat(src[i + 1]) + dy);
            dst[i + 2] = Float.floatToRawIntBits(Float.intBitsToFloat(src[i + 2]) + dz);
        }
        return new BakedQuad(dst, quad.getTintIndex(), quad.getDirection(), quad.getSprite(),
                quad.isShade());
    }
}
