package cn.blockforge.generated.hexalunarcalamity.item;

import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * 震爆弹：拔销 1 秒、引信 5 秒，爆点不炸方块不破片，
 * 靠强光和巨响让范围内生物眩晕（几乎无法移动）并致盲。
 *
 * <p>GeckoLib 真骨骼（6 根，同碎片手雷那套）：
 * 动画配置照 SuperbWarfare BOCEK 规范：{@code animation.flashbang.idle / run / run_fast}（loop）、
 * {@code animation.flashbang.throw}（play_once）；拔销与压把弹开由 {@code FlashbangGeoModel}
 * 每帧读 {@code GrenadeItem.clientPullProgress} 程序化驱动。
 */
public class FlashbangItem extends GrenadeItem implements GeoItem {

    public static final String ANIM_PREFIX = "animation.flashbang.";
    public static final String C_MOVE = "moveController";
    public static final String C_THROW = "throwController";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    public FlashbangItem(Properties properties) {
        super(properties, Kind.FLASH, 1.25F);
    }

    // ------------------------------------------------------------ GeckoLib
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, C_MOVE, 3, this::movePredicate));
        controllers.add(new AnimationController<>(this, C_THROW, 0, this::throwPredicate));
    }

    private PlayState movePredicate(AnimationState<FlashbangItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (sprinting()) {
            return event.setAndContinue(RawAnimation.begin().thenLoop(
                    ANIM_PREFIX + (sprintFast() ? "run_fast" : "run")));
        }
        return event.setAndContinue(RawAnimation.begin().thenLoop(ANIM_PREFIX + "idle"));
    }

    /** 投掷：从「已拔销」变成「不在手上」的那一小段窗口 */
    private PlayState throwPredicate(AnimationState<FlashbangItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (throwing()) {
            return event.setAndContinue(RawAnimation.begin().thenPlay(ANIM_PREFIX + "throw"));
        }
        return PlayState.STOP;
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    /** 客户端：投掷手臂姿态 + GeckoLib 骨骼渲染 */
    @Override
    public void initializeClient(java.util.function.Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.FlashbangItemClientExtensions.INSTANCE);
    }

    // 客户端标志都在 client.GrenadeAnimState，这里只做布尔转发
    private static boolean throwing() {
        return cn.blockforge.generated.hexalunarcalamity.client.GrenadeAnimState.throwing();
    }

    private static boolean sprinting() {
        return cn.blockforge.generated.hexalunarcalamity.client.GrenadeAnimState.sprinting();
    }

    private static boolean sprintFast() {
        return cn.blockforge.generated.hexalunarcalamity.client.GrenadeAnimState.sprintFast();
    }
}
