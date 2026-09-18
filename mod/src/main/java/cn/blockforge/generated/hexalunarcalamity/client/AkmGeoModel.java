package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * AKM 的 GeckoLib 模型定义 + 程序化骨骼细节。
 *
 * <h2>资源</h2>
 * <ul>
 *   <li>几何 {@code geo/akm.geo.json}：67 方块 / 14 骨骼 / 512² 逐面 UV</li>
 *   <li>贴图 {@code textures/models/akm_geo.png}</li>
 *   <li>动画 {@code animations/akm.animation.json}（控制器 {@code main}）</li>
 * </ul>
 *
 * <h2>骨骼</h2>
 * {@code root → move → body → barrel / sights / handguard / dust_cover / bolt /
 * magazine / trigger / grip / stock / selector / camera}。<br>
 * 朝向：枪口 = -Z（北）、上 = +Y、原点 = 握把。
 *
 * <h2>为什么还要程序化推骨骼</h2>
 * JSON 时间轴是「固定秒数」，而实际换弹时长由 {@link AkmRifleItem#RELOAD_TICKS} 决定，
 * 两者对不上就会出现"动画演完了弹匣还没插回去"。所以换弹期间这里按
 * {@link AkmRifleItem#reloadProgress} 直接推 {@code magazine} / {@code bolt}，
 * 保证退匣、插匣、拉栓和真正的换弹读条严格同步；其余状态仍交给动画 JSON。
 */
public class AkmGeoModel extends GeoModel<AkmRifleItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/akm.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/akm_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/akm.animation.json");

    /** 弹匣掉出机匣的距离（模型像素）—— 不再做实体手，所以行程加大到真的离开枪身 */
    private static final float MAG_DROP = 9.8F;
    /** 弹匣退匣时前后倾角（度） */
    private static final float MAG_TILT = 34.0F;
    /** 拉机柄行程（模型像素，AK 约 10cm ≈ 1.8；bolt_pull 动画里走到 2.9） */
    private static final float BOLT_TRAVEL = 1.9F;

    /**
     * 当前这一遍渲染的枪上装了哪个瞄具（由 {@link AkmGeoRenderer} 从被渲染的 ItemStack 读 NBT 设入）。
     * GeckoLib 的 item animatable 是物品本身（单例），拿不到“手上那一把”的 NBT，所以走这条路。
     */
    static int sightNow = cn.blockforge.generated.hexalunarcalamity.weapon.Sights.IRON;

    /**
     * 当前这一帧的枪本体变换（给第一人称手臂用，见 {@link GunFrame}）。
     * 里面含举枪（ADS）的位移，所以手臂不用再自己算一套 ADS。
     */
    static final GunFrame frame = new GunFrame();

    /** move 骨骼 pivot（geo 里的值） */
    private static final float MOVE_PX = 0.0F;
    private static final float MOVE_PY = 1.75F;
    private static final float MOVE_PZ = 0.0F;

    @Override
    public ResourceLocation getModelResource(AkmRifleItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(AkmRifleItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(AkmRifleItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(AkmRifleItem animatable, long instanceId,
                                    AnimationState<AkmRifleItem> animationState) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return;

        // ------------------------------------------------------------------
        // 瞄准稳定性 + 举枪对心：
        //  · move 骨骼：idle 会缓慢摆 ±0.45°、run/run_fast 周期性摆到 ±4.8°、换弹还要低头 +7°
        //    —— 这些角度都会让「照门—准星」那条瞄准线离开屏幕中心（画面里就是枪口斜着朝下）。
        //  · 举枪还要把整把枪**挪到屏幕中心**：骨骼位移和 display 平移是同一套单位（模型像素），
        //    所以直接把 WeaponMount 算出来的 display 增量加在 move 上就等价于改 display —— 而且
        //    这条路径一定生效（display 包装器对 GeckoLib 物品不生效）。
        //  · camera 空骨骼：fire/bolt/reload 动画用它推镜头（后座上跳等），但动画跑完后 GeckoLib
        //    会把最后一帧留在骨骼上 → 镜头被永久歪掉/压低，所以「没有动作在跑」时每帧把它清零。
        // ------------------------------------------------------------------
        float aim = Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.AKM).aim, 0.0F, 1.0F);
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move != null && aim > 0.001F) {
            float k = 1.0F - aim;
            move.setRotX(move.getRotX() * k);
            move.setRotY(move.getRotY() * k);
            move.setRotZ(move.getRotZ() * k);
            Player local = Minecraft.getInstance().player;
            float aimDx = local == null ? WeaponMount.AKM_AIM_DX : WeaponMount.akmAimDx(local);
            move.setPosX(move.getPosX() * k + aimDx * aim);
            // ★ 举枪参照点随瞄具变：机械瞄具 3.44 / 红点 3.79 / 4 倍镜 4.00
            move.setPosY(move.getPosY() * k + WeaponMount.akmAimDy(sightNow) * aim);
            move.setPosZ(move.getPosZ() * k + WeaponMount.AKM_AIM_DZ * aim);
        }
        CoreGeoBone cam = getAnimationProcessor().getBone("camera");
        if (cam != null && !AkmAnimState.action()) {
            cam.setRotX(0.0F);
            cam.setRotY(0.0F);
            cam.setRotZ(0.0F);
        }

        // 瞄具：只显示当前装的那个（没装就两个都藏）
        CoreGeoBone dot = getAnimationProcessor().getBone("dot_sight");
        CoreGeoBone scope = getAnimationProcessor().getBone("scope_4x");
        if (dot != null) dot.setHidden(sightNow != cn.blockforge.generated.hexalunarcalamity.weapon.Sights.DOT);
        if (scope != null) scope.setHidden(sightNow != cn.blockforge.generated.hexalunarcalamity.weapon.Sights.SCOPE);

        captureFrame(move);
        float p = localReloadProgress();
        driveMagazine(p);
        driveBolt(p);
        net.minecraft.client.multiplayer.ClientLevel lvl = Minecraft.getInstance().level;
        driveCasings(lvl == null ? 0L : lvl.getGameTime());
    }

    // ------------------------------------------------------------------ 抛壳（从弹壳槽抛出空弹壳）
    /** 弹壳初速（模型像素 / tick）：往右上方、略往后 */
    private static final float CASE_VX = 0.75F;
    private static final float CASE_VY = 1.50F;
    private static final float CASE_VZ = 0.50F;
    /** 弹壳下落（像素 / tick²） */
    private static final float CASE_G = 0.14F;
    /** 翻滚角速度（度 / tick）：绕 Z 翻得最快，看起来就是空壳在打转 */
    private static final float CASE_SPIN_Z = 42.0F;
    private static final float CASE_SPIN_X = 22.0F;
    private static final float CASE_SPIN_Y = 12.0F;

    /**
     * 弹壳从弹壳槽（抛壳口）抛出的动画。
     *
     * <p>模型里有 {@code casing_0..3} 四根骨骼轮流用：第 slot 根演「第 slot 枚弹壳」，
     * 年龄 = 现在 − 那枚弹壳抛出的时刻（{@link AkmAnimState#shotTime}）。
     * 全自动 2 tick/发时同时有 4~6 枚在空中，看起来就是一串在外冒；飞满
     * {@link AkmAnimState#EJECT_TICKS} 就藏起来。
     */
    private void driveCasings(long now) {
        for (int i = 0; i < AkmAnimState.CASE_SLOTS; i++) {
            CoreGeoBone casing = getAnimationProcessor().getBone("casing_" + i);
            if (casing == null) continue;
            float t = now - AkmAnimState.shotTime(i);
            if (t < 0.0F || t > AkmAnimState.EJECT_TICKS) {
                casing.setHidden(true);
                continue;
            }
            casing.setHidden(false);
            casing.setPosX(CASE_VX * t);
            casing.setPosY(CASE_VY * t - 0.5F * CASE_G * t * t);
            casing.setPosZ(CASE_VZ * t);
            casing.setRotZ(t * CASE_SPIN_Z * Mth.DEG_TO_RAD);
            casing.setRotX(t * CASE_SPIN_X * Mth.DEG_TO_RAD);
            casing.setRotY(t * CASE_SPIN_Y * Mth.DEG_TO_RAD);
        }
    }

    /** 把 move 骨骼当前状态存进 {@link #frame}（手臂要跟着枪一起动，含举枪位移） */
    private void captureFrame(CoreGeoBone move) {
        float ox = 0.0F, oy = 0.0F, oz = 0.0F, rx = 0.0F, ry = 0.0F, rz = 0.0F;
        if (move != null) {
            ox = move.getPosX();
            oy = move.getPosY();
            oz = move.getPosZ();
            rx = move.getRotX();
            ry = move.getRotY();
            rz = move.getRotZ();
        }
        frame.capture(WeaponMount.AKM_TX, WeaponMount.AKM_TY, WeaponMount.AKM_TZ, 1.0F,
                MOVE_PX, MOVE_PY, MOVE_PZ, ox, oy, oz, rx, ry, rz);
    }

    // ------------------------------------------------------------------ 换弹：退匣 → 新匣 → 卡紧

    /** 弹匣相对「到位」的下移量（模型像素，> 0 = 已经退出来） */
    private static float magDropAt(float p) {
        if (p < 0.18F) return 0.0F;                                            // 就位
        if (p < 0.42F) return MAG_DROP * ease(Mth.inverseLerp(p, 0.18F, 0.42F)); // 退匣
        if (p < 0.55F) return MAG_DROP;                                        // 空窗
        if (p < 0.82F) return MAG_DROP * (1.0F - ease(Mth.inverseLerp(p, 0.55F, 0.82F)));  // 新匣上行
        return -0.22F * Mth.sin(((p - 0.82F) / 0.18F) * (float) Math.PI);      // 卡紧：过冲一下
    }

    /** 退匣过程的弹匣前后倾角（度），左手要跟着一起斜 */
    private static float magTiltAt(float p) {
        if (p < 0.18F) return 0.0F;
        if (p < 0.42F) return -MAG_TILT * ease(Mth.inverseLerp(p, 0.18F, 0.42F));
        if (p < 0.55F) return -MAG_TILT;
        if (p < 0.82F) return -MAG_TILT * (1.0F - ease(Mth.inverseLerp(p, 0.55F, 0.82F)));
        return 0.0F;
    }

    private void driveMagazine(float p) {
        if (p < 0.0F) return;
        CoreGeoBone mag = getAnimationProcessor().getBone("magazine");
        if (mag == null) return;
        mag.setPosY(-magDropAt(p));
        mag.setRotX(magTiltAt(p) * Mth.DEG_TO_RAD);
    }

    /** 换弹最后一段拉栓上膛（没在换弹时交给 bolt_pull 动画） */
    private void driveBolt(float p) {
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt == null || p < 0.0F) return;
        bolt.setPosZ(boltBack(p) * BOLT_TRAVEL);
    }

    /** 枪机后拉量 0..1（换弹最后一段拉栓上膛） */
    private static float boltBack(float p) {
        if (p <= 0.85F) return 0.0F;
        float t = (p - 0.85F) / 0.15F;
        return t < 0.5F ? ease(t / 0.5F) : (1.0F - ease((t - 0.5F) / 0.5F));
    }

    // ------------------------------------------------------------------ 左手动作（模型像素）
    // ★ 手臂本身在 WeaponArms 里画；这里只回答「左手这一刻该在枪的哪个位置」，
    //   所以换弹动作（弹匣下坠前倾、枪机后拉）的数学只有一份。
    /** 托护木（平时） */
    private static final float[] ARM_HANDGUARD = {0.0F, 2.05F, -6.30F};
    /** 弹匣握点（匣体中部左侧） */
    private static final float[] ARM_MAG = {-0.50F, -0.20F, -4.30F};
    /** 拉机柄（枪机右侧那个把） */
    private static final float[] ARM_BOLT = {0.70F, 2.64F, -3.54F};
    /** magazine 骨骼 pivot（geo 里的值） */
    private static final float MAG_PX = 0.0F;
    private static final float MAG_PY = 1.45F;
    private static final float MAG_PZ = -3.78F;
    private static final float[] TMP_A = new float[3];
    private static final float[] TMP_B = new float[3];

    /** 左手在模型像素空间的目标：换弹时跟着弹匣走 → 再抓拉机柄 → 回护木 */
    static float[] leftHandPx(float p, float[] out) {
        if (p < 0.0F) return copy(ARM_HANDGUARD, out);
        if (p < 0.10F) {                       // 从护木移到弹匣
            magPoint(p, TMP_A);
            return lerp(ARM_HANDGUARD, TMP_A, ease(p / 0.10F), out);
        }
        if (p < 0.82F) return magPoint(p, out);   // 抽空匣 / 插新匣（跟着弹匣一起走）
        if (p < 0.90F) {                       // 换上机柄
            magPoint(p, TMP_A);
            boltPoint(p, TMP_B);
            return lerp(TMP_A, TMP_B, ease((p - 0.82F) / 0.08F), out);
        }
        if (p < 0.97F) return boltPoint(p, out);  // 拉栓
        boltPoint(p, TMP_B);                   // 回护木
        return lerp(TMP_B, ARM_HANDGUARD, ease((p - 0.97F) / 0.03F), out);
    }

    /** 弹匣上的握点（跟着弹匣一起下移 + 前倾） */
    private static float[] magPoint(float p, float[] out) {
        float drop = magDropAt(p);
        float tilt = magTiltAt(p) * Mth.DEG_TO_RAD;
        float dx = ARM_MAG[0] - MAG_PX;
        float dy = ARM_MAG[1] - MAG_PY;
        float dz = ARM_MAG[2] - MAG_PZ;
        float c = Mth.cos(tilt);
        float s = Mth.sin(tilt);
        out[0] = MAG_PX + dx;
        out[1] = MAG_PY + (dy * c - dz * s) - drop;
        out[2] = MAG_PZ + (dy * s + dz * c);
        return out;
    }

    /** 拉机柄上的握点（跟着枪机后拉一起走） */
    private static float[] boltPoint(float p, float[] out) {
        copy(ARM_BOLT, out);
        out[2] += boltBack(p) * BOLT_TRAVEL;
        return out;
    }

    private static float[] copy(float[] src, float[] out) {
        System.arraycopy(src, 0, out, 0, 3);
        return out;
    }

    private static float[] lerp(float[] a, float[] b, float t, float[] out) {
        for (int i = 0; i < 3; i++) out[i] = a[i] + (b[i] - a[i]) * t;
        return out;
    }

    // ------------------------------------------------------------------ 换弹动作（不做实体手）
    // ★ 用户要求不要实体手方块 ⇒ 换弹/拉栓完全靠**枪自身的动作**表现：
    //   空弹匣被抽出来（下移 + 前倾 + 继续往下掉出视野）、满弹匣从下方升上来卡回弹匣井、
    //   枪机后拉复进；配合 reload 动画里 move 的低头/侧倾，一眼就能看出在换弹。
    //   （magDropAt 的行程已加大到 MAG_DROP=9.8，就是为了让它真的离开枪身。）

    /** 平滑（smoothstep） */
    private static float ease(float t) {
        float x = Mth.clamp(t, 0.0F, 1.0F);
        return x * x * (3.0F - 2.0F * x);
    }

    /** 本地玩家主手 AKM 的换弹进度；没拿 / 没换弹返回 -1 */
    static float localReloadProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof AkmRifleItem)) return -1.0F;
        return AkmRifleItem.reloadProgress(stack, player.level().getGameTime());
    }
}
