package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.entity.BulletEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * 子弹渲染：弹尖（贴图下端的小头）指向飞行方向。
 *
 * <p>原版 {@code ThrownItemRenderer} 会把投掷物永远正面朝向镜头，而 ammo_762 的贴图是
 * 竖着画的，于是飞出去看着就是“竖着的/反着的子弹”。这里用四元数把贴图的 −Y（弹尖）
 * 对齐到速度矢量，保证任何时候都是小头在前。
 */
public class BulletRenderer extends EntityRenderer<BulletEntity> {

    private static final ItemStack STACK = new ItemStack(ModItems.AMMO_762.get());

    private final ItemRenderer itemRenderer;

    public BulletRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.itemRenderer = context.getItemRenderer();
    }

    @Override
    public void render(BulletEntity entity, float entityYaw, float partialTick, PoseStack pose,
                       MultiBufferSource buffer, int packedLight) {
        Vec3 motion = entity.getDeltaMovement();

        pose.pushPose();
        if (motion.lengthSqr() > 1.0E-6D) {
            // 贴图 −Y 方向是弹尖：把它转到速度方向上 → 小头永远在前
            Vector3f direction = new Vector3f((float) motion.x, (float) motion.y, (float) motion.z)
                    .normalize();
            pose.mulPose(new Quaternionf().rotationTo(new Vector3f(0.0F, -1.0F, 0.0F), direction));
        }
        pose.scale(0.4F, 0.4F, 0.4F);
        this.itemRenderer.renderStatic(STACK, ItemDisplayContext.GROUND, packedLight,
                OverlayTexture.NO_OVERLAY, pose, buffer, entity.level(), entity.getId());
        pose.popPose();

        super.render(entity, entityYaw, partialTick, pose, buffer, packedLight);
    }

    @Override
    public ResourceLocation getTextureLocation(BulletEntity entity) {
        return TextureAtlas.LOCATION_BLOCKS;
    }
}
