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
 * AWP 的客户端扩展：手臂姿态用 {@link WeaponArmPose#AWP}（双手持握 / 举镜），
 * 第一人称手持变换交给 {@link WeaponHandGrip}（挡掉原版那段「攻击挥动」），
 * 渲染器用 GeckoLib 的 {@link AwpGeoRenderer}。
 */
public final class AwpItemClientExtensions implements IClientItemExtensions {

    public static final AwpItemClientExtensions INSTANCE = new AwpItemClientExtensions();

    private AwpItemClientExtensions() {
    }

    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return WeaponArmPose.AWP.getArmPose(entity, hand, stack);
    }

    @Override
    public boolean applyForgeHandTransform(PoseStack poseStack, LocalPlayer player, HumanoidArm arm,
                                           ItemStack itemInHand, float partialTick,
                                           float equipProcess, float swingProcess) {
        return WeaponHandGrip.apply(poseStack, player, arm, itemInHand, equipProcess);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return AwpGeoRenderer.get();
    }
}
