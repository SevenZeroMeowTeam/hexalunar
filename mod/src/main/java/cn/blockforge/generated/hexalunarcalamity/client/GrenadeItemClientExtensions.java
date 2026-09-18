package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * 碎片手雷的客户端扩展：手臂姿态沿用 {@link WeaponArmPose#GRENADE}（投掷准备/握持），
 * 同时挂上 GeckoLib 的骨骼渲染器。
 */
public final class GrenadeItemClientExtensions implements IClientItemExtensions {

    public static final GrenadeItemClientExtensions INSTANCE = new GrenadeItemClientExtensions();

    private GrenadeItemClientExtensions() {
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return WeaponArmPose.GRENADE.getArmPose(entity, hand, stack);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return GrenadeGeoRenderer.get();
    }
}
