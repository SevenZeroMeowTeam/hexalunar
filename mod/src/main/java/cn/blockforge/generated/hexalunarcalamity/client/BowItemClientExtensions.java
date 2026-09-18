package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * 复合弓的客户端扩展：手臂姿态沿用 {@link WeaponArmPose#BOW}（拉弓姿势），
 * 同时挂上 GeckoLib 的骨骼渲染器 —— 第一人称 / 第三人称都能看到弓与拉弦动作。
 */
public final class BowItemClientExtensions implements IClientItemExtensions {

    public static final BowItemClientExtensions INSTANCE = new BowItemClientExtensions();

    private BowItemClientExtensions() {
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return WeaponArmPose.BOW.getArmPose(entity, hand, stack);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return BowGeoRenderer.get();
    }
}
