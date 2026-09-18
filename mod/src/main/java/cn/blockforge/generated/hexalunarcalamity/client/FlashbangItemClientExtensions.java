package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * 震爆弹的客户端扩展：手臂姿态沿用 {@link WeaponArmPose#GRENADE}，并挂上 GeckoLib 骨骼渲染器。
 */
public final class FlashbangItemClientExtensions implements IClientItemExtensions {

    public static final FlashbangItemClientExtensions INSTANCE = new FlashbangItemClientExtensions();

    private FlashbangItemClientExtensions() {
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return WeaponArmPose.GRENADE.getArmPose(entity, hand, stack);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return FlashbangGeoRenderer.get();
    }
}
