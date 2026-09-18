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

        float p = localReloadProgress();
        driveMagazine(p);
        driveBolt(p);
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
        if (p > 0.85F) {
            float t = (p - 0.85F) / 0.15F;
            float back = t < 0.5F ? ease(t / 0.5F) : (1.0F - ease((t - 0.5F) / 0.5F));
            bolt.setPosZ(back * BOLT_TRAVEL);
        } else {
            bolt.setPosZ(0.0F);
        }
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
    private static float localReloadProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof AkmRifleItem)) return -1.0F;
        return AkmRifleItem.reloadProgress(stack, player.level().getGameTime());
    }
}
