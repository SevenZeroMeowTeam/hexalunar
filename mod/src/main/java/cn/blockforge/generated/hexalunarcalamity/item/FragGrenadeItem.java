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
 * 碎片手雷：拔销 1 秒、引信 5 秒，落点爆炸对周围生物造成破片伤害。
 *
 * <p>GeckoLib 真骨骼（6 根：root → move → body → fuze → spoon / pin）。
 * 动画配置照 SuperbWarfare BOCEK 的规范（{@code animation.<id>.<state>}）：
 * <ul>
 *   <li>{@code animation.mud.idle / run / run_fast}：循环</li>
 *   <li>{@code animation.mud.throw}：投掷那一下（play_once）</li>
 * </ul>
 * 「拔保险销」与「压把弹开」是连续动作，由 {@code GrenadeGeoModel} 每帧读
 * {@code GrenadeItem.clientPullProgress} 程序化驱动骨骼（同它家 BocekItemModel 的做法）。
 */
public class FragGrenadeItem extends GrenadeItem implements GeoItem {

    public static final String ANIM_PREFIX = "animation.mud.";
    public static final String C_MOVE = "moveController";
    public static final String C_THROW = "throwController";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    public FragGrenadeItem(Properties properties) {
        super(properties, Kind.FRAG, 1.15F);
    }

    // ------------------------------------------------------------ GeckoLib
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, C_MOVE, 3, this::movePredicate));
        controllers.add(new AnimationController<>(this, C_THROW, 0, this::throwPredicate));
    }

    /** 待机 / 跑动摆动 */
    private PlayState movePredicate(AnimationState<FragGrenadeItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (sprinting()) {
            return event.setAndContinue(RawAnimation.begin().thenLoop(
                    ANIM_PREFIX + (sprintFast() ? "run_fast" : "run")));
        }
        return event.setAndContinue(RawAnimation.begin().thenLoop(ANIM_PREFIX + "idle"));
    }

    /** 投掷：从「已拔销」变成「不在手上」的那一小段窗口 */
    private PlayState throwPredicate(AnimationState<FragGrenadeItem> event) {
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
        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.GrenadeItemClientExtensions.INSTANCE);
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
