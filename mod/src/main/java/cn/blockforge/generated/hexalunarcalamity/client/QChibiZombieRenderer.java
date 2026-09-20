package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.monster.Zombie;

/**
 * ★ Q 弹版：**Q 版僵尸渲染器** —— 换上 {@link QChibiZombieModel}（大头矮胖）+
 * Q 版皮肤，并叠上「果冻」式的**挤压拉伸 + 小跳**。
 *
 * <h2>Q 弹晃动怎么做的</h2>
 * 全部是**无状态**的（不需要给每只怪存弹簧，渲染器天然是逐帧的）：
 * <ul>
 *   <li><b>走路</b>：{@code walk}（水平速度归一化）× {@code sin(2.4 × walkDist)} ⇒ 一步一压一弹；
 *       同时按 {@code |sin(walkDist)|} 抬一点高度 ⇒ 一颠一颠地小跳</li>
 *   <li><b>受伤</b>：{@code hurtTime} 上叠一记更快的抖动（被打时「噗」一下）</li>
 *   <li><b>站着</b>：极慢的呼吸式压弹，让静止时也软乎乎的</li>
 * </ul>
 * 挤压是**关于脚底**做的（{@code scale} 发生在模型空间、原点在脚底）⇒ 压扁时脚不会陷进地里。
 *
 * <p>泛型 {@code T extends Zombie}：注册时要精确到具体生物类型
 * （{@code EntityRendererProvider<BomberZombie>} 不接受 {@code EntityRenderer<Zombie>}）。
 */
public class QChibiZombieRenderer<T extends Zombie> extends HumanoidMobRenderer<T, QChibiZombieModel<T>> {

    /** Q 版僵尸皮肤（由 {@code tools/q_chibi_zombie_tex.py} 按模型的 UV 表画出来） */
    public static final ResourceLocation ZOMBIE_TEXTURE = new ResourceLocation(
            HexaLunarCalamity.MOD_ID, "textures/entity/q_chibi_zombie.png");

    /** 走路压弹幅度（0.11 ≈ 最高时压扁 11%） */
    private static final float WALK_SQUASH = 0.11F;
    /** 走路小跳高度（格） */
    private static final float WALK_HOP = 0.085F;
    /** 静止呼吸幅度 */
    private static final float IDLE_SQUASH = 0.045F;
    /** 受伤抖动幅度 */
    private static final float HURT_SQUASH = 0.16F;

    private final ResourceLocation texture;
    private final float scaleFactor;

    /** 自爆尸（默认）：Q 版僵尸皮肤 + 橙标识层 + 原体型 */
    public QChibiZombieRenderer(EntityRendererProvider.Context ctx) {
        this(ctx, ZOMBIE_TEXTURE, 0xFFB45A, 120, 1.0F);
    }

    /**
     * 通用 Q 版僵尸：皮肤 / 染色标识 / 体型缩放都可配 —— 弓手尸、桶尸、巨尸共用这一个渲染器。
     *
     * @param tintAlpha 0 = 不加染色标识层（巨尸就是原样，没有标识）
     * @param scale     渲染缩放（巨尸 1.9，其余 1.0）
     */
    public QChibiZombieRenderer(EntityRendererProvider.Context ctx, ResourceLocation texture,
                                int tintRgb, int tintAlpha, float scale) {
        super(ctx, new QChibiZombieModel<>(ctx.bakeLayer(QChibiZombieModel.LAYER)), 0.45F);
        this.texture = texture;
        this.scaleFactor = scale;
        if (tintAlpha > 0) {
            // 各变种的标识层沿用原版那套（Q 版也一眼能认出是哪只）
            addLayer(new VariantTintLayer(this, tintRgb, tintAlpha));
        }
    }

    @Override
    public ResourceLocation getTextureLocation(T entity) {
        return texture;
    }

    @Override
    protected void setupRotations(T entity, PoseStack pose, float ageInTicks, float bodyYaw,
                                  float partialTick) {
        super.setupRotations(entity, pose, ageInTicks, bodyYaw, partialTick);
        // ★ 走路时一颠一颠的小跳（单位：格）
        QChibi.hop(entity, pose, WALK_HOP);
    }

    @Override
    protected void scale(T entity, PoseStack pose, float partialTick) {
        if (scaleFactor != 1.0F) {
            pose.scale(scaleFactor, scaleFactor, scaleFactor);
        }
        QChibi.squash(entity, pose, partialTick, WALK_SQUASH, IDLE_SQUASH, HURT_SQUASH);
    }
}
