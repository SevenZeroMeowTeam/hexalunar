package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
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
    private static final ResourceLocation TEXTURE = new ResourceLocation(
            HexaLunarCalamity.MOD_ID, "textures/entity/q_chibi_zombie.png");

    /** 走路压弹幅度（0.11 ≈ 最高时压扁 11%） */
    private static final float WALK_SQUASH = 0.11F;
    /** 走路小跳高度（格） */
    private static final float WALK_HOP = 0.085F;
    /** 静止呼吸幅度 */
    private static final float IDLE_SQUASH = 0.045F;
    /** 受伤抖动幅度 */
    private static final float HURT_SQUASH = 0.16F;

    public QChibiZombieRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new QChibiZombieModel<>(ctx.bakeLayer(QChibiZombieModel.LAYER)), 0.45F);
        // 自爆尸的橙色标识层沿用原版那套（Q 版也一眼能认出是哪只）
        addLayer(new VariantTintLayer(this, 0xFFB45A, 120));
    }

    @Override
    public ResourceLocation getTextureLocation(T entity) {
        return TEXTURE;
    }

    /** 水平移动速度归一化成 0..1（≈ 是否在走、走得快不快） */
    private static float walkAmount(Zombie entity) {
        double d = entity.getDeltaMovement().horizontalDistance();
        return Mth.clamp((float) (d * 3.5D), 0.0F, 1.0F);
    }

    @Override
    protected void setupRotations(T entity, PoseStack pose, float ageInTicks, float bodyYaw,
                                  float partialTick) {
        super.setupRotations(entity, pose, ageInTicks, bodyYaw, partialTick);
        // ★ 走路时一颠一颠的小跳（单位：格）
        float walk = walkAmount(entity);
        if (walk > 0.02F) {
            pose.translate(0.0F, Math.abs(Mth.sin(entity.walkDist)) * WALK_HOP * walk, 0.0F);
        }
    }

    @Override
    protected void scale(T entity, PoseStack pose, float partialTick) {
        float walk = walkAmount(entity);
        // 走路：一步一压一弹；受伤：更快的抖动；静止：慢慢呼吸
        float squash = WALK_SQUASH * walk * Mth.sin(entity.walkDist * 2.4F)
                + IDLE_SQUASH * Mth.sin((entity.tickCount + partialTick) * 0.11F);
        if (entity.hurtTime > 0) {
            squash += HURT_SQUASH * (entity.hurtTime / 10.0F)
                    * Mth.sin((entity.tickCount + partialTick) * 1.7F);
        }
        squash = Mth.clamp(squash, -0.35F, 0.35F);
        // 体积大致守恒：竖着压多少，横向就胖多少
        pose.scale(1.0F + squash, 1.0F - squash * 1.15F, 1.0F + squash);
    }
}
