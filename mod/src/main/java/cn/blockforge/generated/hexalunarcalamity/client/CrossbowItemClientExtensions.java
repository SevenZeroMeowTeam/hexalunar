package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * 十字弩的客户端扩展：手臂姿态沿用 {@link WeaponArmPose#CROSSBOW}，
 * 并挂上 GeckoLib 骨骼渲染器（拉弦装弹的骨骼动画在 CrossbowGeoModel 里程序化驱动）。
 */
public final class CrossbowItemClientExtensions implements IClientItemExtensions {

    public static final CrossbowItemClientExtensions INSTANCE = new CrossbowItemClientExtensions();

    private CrossbowItemClientExtensions() {
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return WeaponArmPose.CROSSBOW.getArmPose(entity, hand, stack);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return CrossbowGeoRenderer.get();
    }
}
