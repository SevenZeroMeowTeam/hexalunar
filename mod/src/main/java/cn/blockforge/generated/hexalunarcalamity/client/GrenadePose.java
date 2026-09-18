package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.FlashbangItem;
import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.model.GeoModel;

/**
 * 手雷 / 震爆弹的第一人称「动作 + 手位」数学（碎片手雷与震爆弹共用同一份）。
 *
 * <p>为什么要单独一份：这两个模型过去只在 {@code setCustomAnimations} 里推保险销与压把，
 * 手里那点动作是**没有**的（{@code WeaponPose} 那套 display 增量对 GeckoLib 物品不生效），
 * 于是拔销时看不出手上在用力、也看不到手。现在：
 * <ul>
 *   <li>{@code move} 骨骼按拔销进度 / 投掷冲量 / 走路摆动程序化推（手腕外翻、抬手、甩手）</li>
 *   <li>同一份姿态存进 {@link #FRAME}，让 {@link WeaponArms} 把**手臂**画在正确的位置上</li>
 *   <li>给出左右手的**模型点**：右手握弹体、左手抓保险销的拉环（并随销一起外移）</li>
 * </ul>
 *
 * <p>坐标口径与 {@link GunFrame} / {@code WeaponMount} 一致（模型像素 → 相机空间，1 格 = 16），
 * 模型的 display 是**单位变换**（{@code models/item/frag_grenade.json}、{@code flashbang.json}
 * 的 firstperson_righthand 全是 0/1），所以 display 平移与缩放都按 0 / 1 记。
 *
 * <p>离线验算：{@code python tools/_gren_story.py mud|flashbang}（出「雷 + 双臂」故事板）。
 */
public final class GrenadePose {

    // ------------------------------------------------------------------ 每个型号的差异
    /** 销被拉出的最大距离（模型像素） */
    private static final float PIN_PULL_FRAG = 1.05F;
    private static final float PIN_PULL_FLASH = 1.15F;
    /** 压把弹开角度（度） */
    private static final float SPOON_DEG_FRAG = 38.0F;
    private static final float SPOON_DEG_FLASH = 42.0F;

    /** 右手握点（模型像素）：弹体右后下方的表面 —— 由 tools/_gren_story.py 校验 */
    private static final float[] RIGHT_FRAG = {1.55F, -0.50F, 1.05F};
    private static final float[] RIGHT_FLASH = {1.60F, -2.20F, 1.15F};
    /** 左手抓点（模型像素）：保险销**拉环圆心**（从 geo 量出来的） */
    private static final float[] RING_FRAG = {0.0F, 2.68F, -1.65F};
    private static final float[] RING_FLASH = {0.0F, 2.28F, -2.86F};

    // ------------------------------------------------------------------ move 骨骼姿态
    /** 拔销：手腕外翻（度）+ 抬腕（度）+ 抬手 / 往身前（模型像素） */
    private static final float PIN_ROT_Z_DEG = 16.0F;
    private static final float PIN_ROT_X_DEG = -8.0F;
    private static final float PIN_POS_Y = 1.6F;
    private static final float PIN_POS_Z = 0.8F;
    /** 投掷：向前上方甩出去（度 / 模型像素）—— 只在出手那一瞬 */
    private static final float THROW_ROT_X_DEG = -34.0F;
    private static final float THROW_POS_Y = 2.6F;
    private static final float THROW_POS_Z = -3.6F;
    /** 走路摆动 / 呼吸（比持枪小，手里就一颗雷） */
    private static final float WALK_ROT_Z_DEG = 1.6F;
    private static final float WALK_POS_Y = 0.7F;
    private static final float BREATH_POS_Y = 0.5F;
    /** 引信快烧完时的抖（度） */
    private static final float SHAKE_ROT_Z_DEG = 3.2F;

    /**
     * 手雷专用的肩点（相机空间，格）。
     *
     * <p>比持枪那套（{@code WeaponArms.SHOULDER_*}）更靠外、更靠下：雷就攥在离相机 0.7 格的地方，
     * 肩点要是还在 ±0.8，手臂方块会横在画面正中间挡住雷（离线故事板里一眼可见）。
     */
    public static final float[] SHOULDER_R = {0.88F, -1.18F, -1.02F};
    public static final float[] SHOULDER_L = {-0.72F, -1.18F, -1.00F};

    /** 当前帧 move 姿态（骨骼与手臂共用 ⇒ 手不会比雷晚一帧） */
    private static final float[] MOVE = new float[6];
    /** 手臂读的当前帧变换 */
    static final GunFrame FRAME = new GunFrame();
    /** 压把弹开的平滑值（按型号分开，避免两把武器互相拉扯） */
    private static final float[] SPOON = new float[2];

    private GrenadePose() {
    }

    /** 手上那颗雷是哪一种（没拿返回 null） */
    public static WeaponAnim.Kind heldKind() {
        Player player = Minecraft.getInstance().player;
        if (player == null) return null;
        ItemStack stack = GrenadeItem.heldGrenade(player);
        if (stack == null) return null;
        return stack.getItem() instanceof FlashbangItem ? WeaponAnim.Kind.FLASH : WeaponAnim.Kind.GRENADE;
    }

    /** 手上那颗雷现在是哪个状态（没拿返回 -1） */
    private static int heldState() {
        Player player = Minecraft.getInstance().player;
        if (player == null) return -1;
        ItemStack stack = GrenadeItem.heldGrenade(player);
        return stack == null ? -1 : GrenadeItem.state(stack);
    }

    /**
     * 销**拔出来多少** 0..1（PRIMED / ARMED = 1）—— 用来决定保险销骨骼滑出的距离。
     *
     * <p>注意不能直接用 {@code clientPullProgress}：拔完销后它会被一直钉在 1.0（销保持拔出样子），
     * 拿它当「正在拔销」就会让左手一直挂在拉环上（投掷时也挂着 ⇒ 看着像双手投掷）。
     */
    private static float pinOutAmount() {
        switch (heldState()) {
            case GrenadeItem.STATE_PULLING:
                return Mth.clamp(GrenadeAnimState.pullProgress(), 0.0F, 1.0F);
            case GrenadeItem.STATE_REINSERTING:
                return 1.0F - Mth.clamp(GrenadeAnimState.reinsertProgress(), 0.0F, 1.0F);
            case GrenadeItem.STATE_PRIMED:
            case GrenadeItem.STATE_ARMED:
                return 1.0F;
            default:
                return 0.0F;
        }
    }

    /** 手**正在做动作**的程度 0..1（拔销中 / 插销中）—— 动作做完就归零，手跟着放松 */
    private static float pinAction() {
        switch (heldState()) {
            case GrenadeItem.STATE_PULLING:
                return Mth.clamp(GrenadeAnimState.pullProgress(), 0.0F, 1.0F);
            case GrenadeItem.STATE_REINSERTING:
                return 1.0F - Mth.clamp(GrenadeAnimState.reinsertProgress(), 0.0F, 1.0F);
            default:
                return 0.0F;
        }
    }

    /** 左手现在该不该出现在画面里：只在「拔销 / 插销」这两个动作里露手（投掷时绝不甩左手） */
    public static boolean leftHandActive() {
        int state = heldState();
        return state == GrenadeItem.STATE_PULLING || state == GrenadeItem.STATE_REINSERTING;
    }

    /** 引信紧迫度 0..1（1 = 马上就要炸）—— 手里攥着时不烧引信，这里是「已拔销」的紧张感 */
    public static float fuseUrgency() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return 0.0F;
        ItemStack stack = GrenadeItem.heldGrenade(player);
        if (stack == null || GrenadeItem.state(stack) != GrenadeItem.STATE_ARMED) return 0.0F;
        int left = GrenadeItem.fuseLeft(stack, player.level().getGameTime());
        return Mth.clamp(1.0F - left / (float) GrenadeItem.FUSE_TICKS, 0.0F, 1.0F);
    }

    // ------------------------------------------------------------------ 姿态

    /**
     * move 骨骼当前帧的目标姿态：{posX, posY, posZ, rotX, rotY, rotZ}（模型像素 / 弧度）。
     * 骨骼与手臂读同一份，所以手跟着雷一起动、不会差一帧。
     */
    private static void computeMovePose(WeaponAnim.Kind kind, float[] out) {
        float pin = pinAction();
        float kick = Mth.clamp(WeaponAnim.of(kind).throwKick, 0.0F, 1.0F);
        float px = 0.0F;
        float py = 0.0F;
        float pz = 0.0F;
        float rx = PIN_ROT_X_DEG * pin + THROW_ROT_X_DEG * kick;
        float rz = PIN_ROT_Z_DEG * pin;
        py += PIN_POS_Y * pin + THROW_POS_Y * kick;
        pz += PIN_POS_Z * pin + THROW_POS_Z * kick;

        // 已经拔了销（引信还没点，手里不会响）：捏着的时候手微微地抖，读秒的紧张感
        float urgency = fuseUrgency();
        if (urgency <= 0.0F) urgency = 0.35F * pinOutAmount();
        Player player = Minecraft.getInstance().player;
        float t = (player == null ? 0.0F : player.tickCount) * 0.9F;
        if (urgency > 0.0F) {
            rz += (Mth.sin(t) * 2.6F + Mth.sin(t * 2.7F) * 1.2F) * urgency;
            px += Mth.sin(t * 1.7F) * 0.7F * urgency;
        }

        // 走路摆动 + 呼吸（很轻）
        if (player != null) {
            float speed = Mth.clamp(
                    (float) player.getDeltaMovement().horizontalDistance() * 3.6F, 0.0F, 1.0F);
            float phase = (float) player.walkDist;
            if (speed > 0.01F) {
                rz += Mth.sin(phase * 4.4F) * WALK_ROT_Z_DEG * speed;
                py -= Math.abs(Mth.cos(phase * 4.4F)) * WALK_POS_Y * speed;
            }
            py += Mth.sin(player.tickCount * 0.06F) * BREATH_POS_Y;
        }

        out[0] = px;
        out[1] = py;
        out[2] = pz;
        out[3] = rx * Mth.DEG_TO_RAD;
        out[4] = 0.0F;
        out[5] = rz * Mth.DEG_TO_RAD;
    }

    /**
     * 每个渲染帧驱动骨骼（由 {@code GrenadeGeoModel} / {@code FlashbangGeoModel} 在
     * 「拿在手上那一遍」调用；GUI 图标 / 掉落物 / 展示框不推，图标才不会跟着动）。
     */
    public static void drive(GeoModel<?> model, WeaponAnim.Kind kind) {
        computeMovePose(kind, MOVE);
        var ap = model.getAnimationProcessor();
        CoreGeoBone move = ap.getBone("move");
        if (move != null) {
            move.updatePosition(MOVE[0], MOVE[1], MOVE[2]);
            move.updateRotation(MOVE[3], MOVE[4], MOVE[5]);
        }

        // 保险销：沿 -Z（朝前）滑出去；插回销时滑回来
        CoreGeoBone pin = ap.getBone("pin");
        if (pin != null) {
            pin.setPosZ(-pinOutAmount() * pinPullDist(kind));
        }

        // 压把：销拔出 + 引信开始跑之后才弹开。碎片手雷的压把在背面（绕 X），
        // 震爆弹的压把在 -X 侧竖着（绕 Z），所以两个型号的轴不一样。
        CoreGeoBone spoon = ap.getBone("spoon");
        if (spoon != null) {
            int idx = spoonIndex(kind);
            float target = GrenadeAnimState.armed() || GrenadeAnimState.throwing() ? 1.0F : 0.0F;
            SPOON[idx] += (target - SPOON[idx]) * 0.25F;
            float deg = SPOON[idx] * spoonDeg(kind) * Mth.DEG_TO_RAD;
            if (kind == WeaponAnim.Kind.FLASH) {
                spoon.setRotZ(-deg);
            } else {
                spoon.setRotX(-deg);
            }
        }
    }

    /** 手臂（第一人称补画的双臂）用：把**当前帧**的姿态算进 {@link #FRAME}（同 AkmGeoModel.captureNow 的思路） */
    public static void captureNow(WeaponAnim.Kind kind) {
        computeMovePose(kind, MOVE);
        FRAME.capture(0.0F, 0.0F, 0.0F, 1.0F, 0.0F, 0.0F, 0.0F,
                MOVE[0], MOVE[1], MOVE[2], MOVE[3], MOVE[4], MOVE[5]);
    }

    // ------------------------------------------------------------------ 手位

    /** 右手握点（模型像素）：弹体右侧 */
    public static float[] rightHandPx(WeaponAnim.Kind kind, float[] out) {
        float[] src = kind == WeaponAnim.Kind.FLASH ? RIGHT_FLASH : RIGHT_FRAG;
        System.arraycopy(src, 0, out, 0, 3);
        return out;
    }

    /** 左手抓点（模型像素）：保险销拉环，随销被拔出一起往前（-Z）走 */
    public static float[] leftHandPx(WeaponAnim.Kind kind, float[] out) {
        float[] src = kind == WeaponAnim.Kind.FLASH ? RING_FLASH : RING_FRAG;
        System.arraycopy(src, 0, out, 0, 3);
        out[2] -= pinOutAmount() * pinPullDist(kind);
        return out;
    }

    private static float pinPullDist(WeaponAnim.Kind kind) {
        return kind == WeaponAnim.Kind.FLASH ? PIN_PULL_FLASH : PIN_PULL_FRAG;
    }

    private static float spoonDeg(WeaponAnim.Kind kind) {
        return kind == WeaponAnim.Kind.FLASH ? SPOON_DEG_FLASH : SPOON_DEG_FRAG;
    }

    private static int spoonIndex(WeaponAnim.Kind kind) {
        return kind == WeaponAnim.Kind.FLASH ? 1 : 0;
    }
}
