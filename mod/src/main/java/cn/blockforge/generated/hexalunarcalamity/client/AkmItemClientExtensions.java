package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * AKM 的客户端扩展：手臂姿态沿用 {@link WeaponArmPose#AKM}（双手持握 / 抵肩），
 * 同时挂上 GeckoLib 的骨骼渲染器。
 */
public final class AkmItemClientExtensions implements IClientItemExtensions {

    public static final AkmItemClientExtensions INSTANCE = new AkmItemClientExtensions();

    private AkmItemClientExtensions() {
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return WeaponArmPose.AKM.getArmPose(entity, hand, stack);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return AkmGeoRenderer.get();
    }
}
