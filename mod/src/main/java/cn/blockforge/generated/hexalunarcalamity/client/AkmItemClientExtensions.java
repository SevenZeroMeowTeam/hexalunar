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

    /**
     * 接管第一人称手持变换（见 {@link WeaponHandGrip}）：原版会给非空物品套「攻击挥动」
     * （{@code applyItemArmAttackTransform}，最多 rotX −80°，按住左键还会一直重新触发），
     * 枪是全自动连发 → 枪会在手里不停上下点头，而补画的双手跟不上那段变换。
     */
    @Override
    public boolean applyForgeHandTransform(PoseStack poseStack, LocalPlayer player, HumanoidArm arm,
                                           ItemStack itemInHand, float partialTick,
                                           float equipProcess, float swingProcess) {
        return WeaponHandGrip.apply(poseStack, player, arm, itemInHand, equipProcess);
    }

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        return AkmGeoRenderer.get();
    }
}
