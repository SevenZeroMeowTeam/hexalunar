package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.renderer.block.model.ItemTransforms;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.client.model.BakedModelWrapper;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * 给武器模型套一层「会动」的包装：渲染时把 {@link WeaponPose} 算出的动作增量
 * 叠到模型 JSON 的 display 上。
 *
 * <p>为什么这样做而不是去 Mixin {@code ItemInHandRenderer}：display 参数就是我们
 * 调模型时用的那套数（rotation 用度、translation 用 1/16 方块），左右手镜像、第三人称、
 * GUI 全交给原版；而且 {@code getTransforms()} 每次渲染都会被调用，天然就是逐帧动画的入口。
 *
 * <p><b>AKM 额外做的事</b>：它现在是分件模型（枪身 + 弹匣 + 拉机柄），光靠 display 只能整体动。
 * 所以这里再把 {@link AkmPartAnim} 变换过的弹匣/拉机柄面拼到枪身后面，
 * 实现「弹匣拔出/推入 + 拉机柄回拉闭锁」—— 仍然不需要 Mixin、不需要额外前置。
 */
public class AnimatedWeaponModel extends BakedModelWrapper<BakedModel> {

    private final WeaponAnim.Kind kind;

    public AnimatedWeaponModel(BakedModel originalModel, WeaponAnim.Kind kind) {
        super(originalModel);
        this.kind = kind;
    }

    @Override
    public ItemTransforms getTransforms() {
        return WeaponPose.animate(kind, originalModel.getTransforms());
    }

    /**
     * AKM：把弹匣与拉机柄的面按当前换弹进度平移后拼进来。
     * 十字弩：拼上「弩箭」与「拉弦的左手」。
     * 其他武器、非物品渲染（方块状态）一律直接透传。
     */
    @Override
    public List<BakedQuad> getQuads(@Nullable BlockState state, @Nullable Direction side,
                                    RandomSource rand) {
        List<BakedQuad> base = originalModel.getQuads(state, side, rand);
        if (state != null || side != null) {
            return base;
        }
        List<BakedQuad> extra = new ArrayList<>();
        if (kind == WeaponAnim.Kind.AKM) {
            // AKM 已改用 GeckoLib 真骨骼渲染（AkmGeoRenderer + geo/akm.geo.json），
            // 弹匣/拉机柄由骨骼动画驱动，这里不再拼件。
        } else if (kind == WeaponAnim.Kind.CROSSBOW) {
            extra.addAll(CrossbowPartAnim.boltQuads(rand));
            extra.addAll(CrossbowPartAnim.handQuads(rand));
        }
        if (extra.isEmpty()) {
            return base;
        }
        List<BakedQuad> merged = new ArrayList<>(base.size() + extra.size());
        merged.addAll(base);
        merged.addAll(extra);
        return merged;
    }
}
