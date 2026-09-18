package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.moon.MoonPhase;
import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Matrix4f;

/**
 * 月相的**天空颜色 + 月亮颜色**（r66）。
 *
 * <h2>为什么自己画</h2>
 * 原版的天空（天穹 + 太阳/月亮）是在 {@code LevelRenderer.renderSky} 里用固定颜色画的，
 * Forge 只给了雾色（{@code ViewportEvent.ComputeFogColor}）这类钩子，没有「改天穹/月盘颜色」的事件；
 * 而 {@code Stage.AFTER_SKY} 正好在原版天空画完之后、地形之前 ⇒ 在这儿自己叠一层**天穹染色**、
 * 再盖一个**本阶段颜色的月盘**即可（月盘比原版的 ±20 稍大一点，把原版月亮整个盖住）。
 *
 * <h2>坐标系</h2>
 * {@code AFTER_SKY} 时的位姿栈 = 「世界视角矩阵」，**原点就是相机**（原版天体就是在 y=±100 画的，
 * 见 {@code LevelRenderer.renderSky}）。所以：
 * <ul>
 *   <li>天穹：直接以原点为球心画一个下半封口的球（半径与原版一致 100）；</li>
 *   <li>月盘：照抄原版那两步旋转
 *       （{@code YP(-90°)} + {@code XP(时间 {0..1} × 360°)}），然后在 <b>y = −100</b> 的平面上画圆盘
 *       —— 原版月亮就在这个位置、这个平面上。</li>
 * </ul>
 * 两层都关掉深度测试/深度写入（天空在最远处、且不写深度），地形随后照常把它们盖住。
 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, value = Dist.CLIENT)
public final class MoonSkyRenderer {

    /** 天穹半径（与原版 skyBuffer 一致） */
    private static final float SKY_R = 100.0F;
    /** 月盘半径：原版月亮是 ±20 的方片，我们画 20.6 的圆盘 ⇒ 整个盖住它 */
    private static final float MOON_R = 20.6F;
    /** 分段数 */
    private static final int SEG = 48;
    /** 月盘所在平面的高度（原版：太阳 +100 / 月亮 −100） */
    private static final float MOON_Y = -100.0F;

    /** 天顶不透明度 / 地平线不透明度（不盖死星空） */
    private static final float SKY_TOP_A = 0.42F;
    private static final float SKY_HORIZON_A = 0.60F;
    /** 地平线以下那一圈（避免天地交界处出现硬缝） */
    private static final float SKY_BELOW_A = 0.16F;

    @SubscribeEvent
    public static void onRenderStage(RenderLevelStageEvent event) {
        if (event.getStage() != RenderLevelStageEvent.Stage.AFTER_SKY) return;
        MoonPhase phase = activePhase();
        if (phase == null) return;
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null) return;

        PoseStack pose = event.getPoseStack();
        pose.pushPose();
        try {
            drawSky(pose, phase);
            // 与 LevelRenderer.renderSky 完全相同的两步：YR -90° + XR（时间 × 360°）
            pose.mulPose(Axis.YP.rotationDegrees(-90.0F));
            pose.mulPose(Axis.XP.rotationDegrees(level.getTimeOfDay(event.getPartialTick()) * 360.0F));
            drawMoon(pose, phase);
        } finally {
            pose.popPose();
            RenderSystem.setShaderColor(1.0F, 1.0F, 1.0F, 1.0F);
            RenderSystem.enableDepthTest();
            RenderSystem.depthMask(true);
            RenderSystem.enableCull();
            RenderSystem.disableBlend();
        }
    }

    // ------------------------------------------------------------------ 天穹

    /** 以相机为球心的天穹：天顶色 → 地平线色的竖直渐变（顶点色插值），下半球用一层很淡的暗色封住 */
    private static void drawSky(PoseStack pose, MoonPhase phase) {
        Matrix4f m = pose.last().pose();
        RenderSystem.setShader(GameRenderer::getPositionColorShader);
        RenderSystem.setShaderColor(1.0F, 1.0F, 1.0F, 1.0F);
        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        RenderSystem.disableCull();
        RenderSystem.depthMask(false);
        RenderSystem.disableDepthTest();

        BufferBuilder buf = Tesselator.getInstance().getBuilder();
        buf.begin(VertexFormat.Mode.TRIANGLES, DefaultVertexFormat.POSITION_COLOR);
        for (int i = 0; i < SEG; i++) {
            float a0 = (float) (i * Math.PI * 2.0 / SEG);
            float a1 = (float) ((i + 1) * Math.PI * 2.0 / SEG);
            float x0 = (float) Math.cos(a0) * SKY_R;
            float z0 = (float) Math.sin(a0) * SKY_R;
            float x1 = (float) Math.cos(a1) * SKY_R;
            float z1 = (float) Math.sin(a1) * SKY_R;
            // 上半球（天顶 → 地平线）
            vertex(buf, m, 0.0F, SKY_R, 0.0F, phase.skyTop, SKY_TOP_A);
            vertex(buf, m, x0, 0.0F, z0, phase.skyHorizon, SKY_HORIZON_A);
            vertex(buf, m, x1, 0.0F, z1, phase.skyHorizon, SKY_HORIZON_A);
            // 下半球（地平线 → 天底），很淡的一层，防止天地交界出现硬边
            vertex(buf, m, x0, 0.0F, z0, phase.skyHorizon, SKY_HORIZON_A);
            vertex(buf, m, 0.0F, -SKY_R, 0.0F, phase.skyTop, SKY_BELOW_A);
            vertex(buf, m, x1, 0.0F, z1, phase.skyHorizon, SKY_HORIZON_A);
        }
        BufferUploader.drawWithShader(buf.end());
    }

    // ------------------------------------------------------------------ 月盘

    /**
     * 月盘：先在 y = {@link #MOON_Y} 的平面上画几圈**叠加混合的光晕**，再画一圈**不透明**的圆盘
     * （不透明才能真正盖住原版月亮），最后点几块陨石坑免得看着像一张色纸。
     */
    private static void drawMoon(PoseStack pose, MoonPhase phase) {
        Matrix4f m = pose.last().pose();
        RenderSystem.setShader(GameRenderer::getPositionColorShader);
        RenderSystem.setShaderColor(1.0F, 1.0F, 1.0F, 1.0F);
        RenderSystem.disableCull();
        RenderSystem.depthMask(false);
        RenderSystem.disableDepthTest();

        // ---- 光晕（叠加混合）----
        RenderSystem.enableBlend();
        RenderSystem.blendFunc(GlStateManager.SourceFactor.SRC_ALPHA,
                GlStateManager.DestFactor.ONE);
        BufferBuilder buf = Tesselator.getInstance().getBuilder();
        buf.begin(VertexFormat.Mode.TRIANGLES, DefaultVertexFormat.POSITION_COLOR);
        float glow = MOON_R * (phase.superMoon ? 2.35F : 1.8F);
        ring(buf, m, MOON_R * 1.02F, glow, phase.moonHalo, phase.superMoon ? 0.42F : 0.30F);
        BufferUploader.drawWithShader(buf.end());

        // ---- 月盘（不透明，盖住原版月亮）----
        RenderSystem.disableBlend();
        buf.begin(VertexFormat.Mode.TRIANGLES, DefaultVertexFormat.POSITION_COLOR);
        discAt(buf, m, MOON_R, phase.moonColor, 1.0F, 0.0F, 0.0F);
        // 陨石坑（同色系深浅）：位置固定 ⇒ 每天看到的月面纹理一致
        discAt(buf, m, MOON_R * 0.22F, darker(phase.moonColor, 0.82F), 1.0F,
                MOON_R * 0.34F, -MOON_R * 0.26F);
        discAt(buf, m, MOON_R * 0.15F, darker(phase.moonColor, 0.88F), 1.0F,
                -MOON_R * 0.30F, MOON_R * 0.30F);
        discAt(buf, m, MOON_R * 0.11F, lighter(phase.moonColor, 1.08F), 1.0F,
                -MOON_R * 0.14F, -MOON_R * 0.44F);
        BufferUploader.drawWithShader(buf.end());
    }
    private static void discAt(BufferBuilder buf, Matrix4f m, float r, int rgb, float alpha,
                              float cx, float cz) {
        for (int i = 0; i < SEG; i++) {
            float a0 = (float) (i * Math.PI * 2.0 / SEG);
            float a1 = (float) ((i + 1) * Math.PI * 2.0 / SEG);
            vertex(buf, m, cx, MOON_Y, cz, rgb, alpha);
            vertex(buf, m, cx + (float) Math.cos(a0) * r, MOON_Y, cz + (float) Math.sin(a0) * r,
                    rgb, alpha);
            vertex(buf, m, cx + (float) Math.cos(a1) * r, MOON_Y, cz + (float) Math.sin(a1) * r,
                    rgb, alpha);
        }
    }

    /** 光晕环（内圈 alpha、外圈 0。叠加混合 ⇒ 看着是发光） */
    private static void ring(BufferBuilder buf, Matrix4f m, float rIn, float rOut, int rgb,
                             float alpha) {
        for (int i = 0; i < SEG; i++) {
            float a0 = (float) (i * Math.PI * 2.0 / SEG);
            float a1 = (float) ((i + 1) * Math.PI * 2.0 / SEG);
            float c0 = (float) Math.cos(a0);
            float s0 = (float) Math.sin(a0);
            float c1 = (float) Math.cos(a1);
            float s1 = (float) Math.sin(a1);
            vertex(buf, m, c0 * rIn, MOON_Y, s0 * rIn, rgb, alpha);
            vertex(buf, m, c1 * rIn, MOON_Y, s1 * rIn, rgb, alpha);
            vertex(buf, m, c0 * rOut, MOON_Y, s0 * rOut, rgb, 0.0F);
            vertex(buf, m, c1 * rIn, MOON_Y, s1 * rIn, rgb, alpha);
            vertex(buf, m, c0 * rOut, MOON_Y, s0 * rOut, rgb, 0.0F);
            vertex(buf, m, c1 * rOut, MOON_Y, s1 * rOut, rgb, 0.0F);
        }
    }

    private static void vertex(BufferBuilder buf, Matrix4f m, float x, float y, float z,
                               int rgb, float alpha) {
        buf.vertex(m, x, y, z)
                .color(((rgb >> 16) & 0xFF) / 255F, ((rgb >> 8) & 0xFF) / 255F,
                        (rgb & 0xFF) / 255F, alpha)
                .endVertex();
    }

    private static int darker(int rgb, float f) {
        return scale(rgb, f);
    }

    private static int lighter(int rgb, float f) {
        return scale(rgb, Math.min(1.0F, f));
    }

    private static int scale(int rgb, float f) {
        int r = (int) Math.min(255.0F, ((rgb >> 16) & 0xFF) * f);
        int g = (int) Math.min(255.0F, ((rgb >> 8) & 0xFF) * f);
        int b = (int) Math.min(255.0F, (rgb & 0xFF) * f);
        return (r << 16) | (g << 8) | b;
    }

    /** 只在夜晚且同步到有效月相时画 */
    private static MoonPhase activePhase() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || !mc.level.isNight()) return null;
        return ClientMoonState.phase();
    }

    private MoonSkyRenderer() {
    }
}
