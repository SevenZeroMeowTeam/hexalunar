package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.cache.texture.AutoGlowingTexture;
import software.bernie.geckolib.core.animatable.GeoAnimatable;
import software.bernie.geckolib.renderer.GeoRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.HashMap;
import java.util.Map;

/**
 * 会动的光泽层（流光 / 自发光）。
 *
 * <p>做法：再渲染一遍模型，但换成 <b>发光遮罩贴图</b>（{@code <贴图>_glowmask.png}，
 * 由 {@code tools/gen_glowmask.py} 从贴图里挑出"抛光高光"那部分像素生成）+
 * GeckoLib 的自发光渲染类型（{@link AutoGlowingTexture#getRenderType}，
 * 加法混合、无视光照），并把**每帧的 alpha 做成两个不同周期的脉动叠加**：
 * 慢的一层像呼吸、快的一层像光在表面扫过 —— 于是"光滑反光"的部位在暗处也亮，
 * 而且一直在轻微流动。
 *
 * <p>再叠一个武器动作增益：开火（{@code recoil}）、举枪（{@code aim}）、拉弦（{@code draw}）时
 * 流光会明显变亮，手感上"枪管热起来了"。
 *
 * <p>注册方式：GeckoLib 4.8.4 的 {@code GeoRenderer#getRenderLayers()} 是个 default 方法，
 * 直接在渲染器里重写返回自己的层即可（不需要 addRenderLayer）。
 */
public class GlossGlintLayer<T extends GeoAnimatable> extends GeoRenderLayer<T> {

    /** 慢脉动（呼吸）周期，tick */
    private static final float PULSE_PERIOD = 54.0F;
    /** 快扫过周期，tick（与呼吸周期互质，叠起来不会规律重复） */
    private static final float SWEEP_PERIOD = 19.0F;

    private static final Map<ResourceLocation, RenderType> TYPES = new HashMap<>();

    private final ResourceLocation glowmask;
    private final float maxAlpha;
    @Nullable
    private final WeaponAnim.Kind kind;

    public GlossGlintLayer(GeoRenderer<T> renderer, ResourceLocation glowmask, float maxAlpha,
                           @Nullable WeaponAnim.Kind kind) {
        super(renderer);
        this.glowmask = glowmask;
        this.maxAlpha = maxAlpha;
        this.kind = kind;
    }

    /** 按贴图基名取发光遮罩位置，例如 {@code mask("akm_geo")} → textures/models/akm_geo_glowmask.png */
    public static ResourceLocation mask(String base) {
        return new ResourceLocation(HexaLunarCalamity.MOD_ID,
                "textures/models/" + base + "_glowmask.png");
    }

    @Override
    public void render(PoseStack poseStack, T animatable, BakedGeoModel model, RenderType renderType,
                       MultiBufferSource bufferSource, VertexConsumer buffer, float partialTick,
                       int packedLight, int packedOverlay) {
        Level level = Minecraft.getInstance().level;
        if (level == null || maxAlpha <= 0.01F) {
            return;
        }
        float t = level.getGameTime() + partialTick;
        float pulse = 0.5F + 0.5F * Mth.sin(t * Mth.TWO_PI / PULSE_PERIOD);
        float sweep = 0.5F + 0.5F * Mth.sin(t * Mth.TWO_PI / SWEEP_PERIOD + 1.7F);
        float alpha = maxAlpha * (0.42F + 0.40F * pulse + 0.18F * sweep);
        if (kind != null) {
            WeaponAnim.State st = WeaponAnim.of(kind);
            alpha *= 1.0F + 2.4F * st.recoil + 1.4F * st.aim + 1.0F * st.draw;
        }
        if (alpha <= 0.01F) {
            return;
        }
        getRenderer().reRender(model, poseStack, bufferSource, animatable, type(), buffer,
                partialTick, packedLight, packedOverlay, 1.0F, 1.0F, 1.0F,
                Mth.clamp(alpha, 0.0F, 1.0F));
    }

    private RenderType type() {
        return TYPES.computeIfAbsent(glowmask, AutoGlowingTexture::getRenderType);
    }
}
