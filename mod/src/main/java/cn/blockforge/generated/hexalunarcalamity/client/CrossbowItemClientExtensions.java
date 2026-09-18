package cn.blockforge.generated.hexalunarcalamity.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
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

    /**
     * 接管第一人称手持变换（见 {@link WeaponHandGrip}）：去掉原版给物品套的攻击挥动
     * （左键射击时弩会在手里上下点头）。按住右键拉弦/开镜那套仍然交回原版。
     */
    @Override
    public boolean applyForgeHandTransform(PoseStack poseStack, LocalPlayer player, HumanoidArm arm,
                                           ItemStack itemInHand, float partialTick,
                                           float equipProcess, float swingProcess) {
        return WeaponHandGrip.apply(poseStack, player, arm, itemInHand, equipProcess);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return CrossbowGeoRenderer.get();
    }
}
