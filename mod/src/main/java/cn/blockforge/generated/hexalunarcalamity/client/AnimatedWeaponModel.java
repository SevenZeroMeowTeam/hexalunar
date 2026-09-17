package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.renderer.block.model.ItemTransforms;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraftforge.client.model.BakedModelWrapper;

/**
 * 给武器模型套一层「会动」的包装：渲染时把 {@link WeaponPose} 算出的动作增量
 * 叠到模型 JSON 的 display 上。
 *
 * <p>为什么这样做而不是去 Mixin {@code ItemInHandRenderer}：display 参数就是我们
 * 调模型时用的那套数（rotation 用度、translation 用 1/16 方块），左右手镜像、第三人称、
 * GUI 全交给原版；而且 {@code getTransforms()} 每次渲染都会被调用，天然就是逐帧动画的入口。
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
}
