package cn.blockforge.generated.hexalunarcalamity.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;

/**
 * ★ Q 弹版：**「果冻」通用的挤压拉伸 / 小跳** —— 给所有 Q 版怪（僵尸系、骷髅系）共用。
 *
 * <p>全部是**无状态**的：不需要给每只怪存弹簧，渲染器天然逐帧算，所以老存档里的怪
 * 一进游戏就自动变 Q，不用碰任何 NBT。
 *
 * <ul>
 *   <li><b>走路</b>：{@code walk}（水平速度归一化到 0..1）× {@code sin(2.4 × walkDist)}
 *       ⇒ 一步一压一弹；同时按 {@code |sin(walkDist)|} 抬一点高度 ⇒ 一颠一颠地小跳</li>
 *   <li><b>受伤</b>：{@code hurtTime} 上叠一记更快的抖动（被打时「噗」一下）</li>
 *   <li><b>站着</b>：极慢的呼吸式压弹，静止时也软乎乎</li>
 * </ul>
 * 挤压是**关于脚底**做的（{@code scale} 发生在模型空间、原点在脚底）⇒ 压扁时脚不会陷进地里；
 * 体积大致守恒（竖着压多少，横向就胖多少）。
 */
public final class QChibi {

    private QChibi() {
    }

    /** 水平移动速度归一化成 0..1（≈ 是否在走、走得快不快） */
    public static float walkAmount(LivingEntity entity) {
        double d = entity.getDeltaMovement().horizontalDistance();
        return Mth.clamp((float) (d * 3.5D), 0.0F, 1.0F);
    }

    /** 走路时一颠一颠的小跳（单位：格）。{@code hop} 是最大跳高 */
    public static void hop(LivingEntity entity, PoseStack pose, float hop) {
        float walk = walkAmount(entity);
        if (walk > 0.02F) {
            pose.translate(0.0F, Math.abs(Mth.sin(entity.walkDist)) * hop * walk, 0.0F);
        }
    }

    /**
     * 挤压拉伸。{@code walkSquash} / {@code idleSquash} / {@code hurtSquash} 是三种幅度，
     * 传 0 就是关掉那一路。
     */
    public static void squash(LivingEntity entity, PoseStack pose, float partialTick,
                              float walkSquash, float idleSquash, float hurtSquash) {
        float walk = walkAmount(entity);
        float squash = walkSquash * walk * Mth.sin(entity.walkDist * 2.4F)
                + idleSquash * Mth.sin((entity.tickCount + partialTick) * 0.11F);
        if (entity.hurtTime > 0 && hurtSquash > 0.0F) {
            squash += hurtSquash * (entity.hurtTime / 10.0F)
                    * Mth.sin((entity.tickCount + partialTick) * 1.7F);
        }
        squash = Mth.clamp(squash, -0.35F, 0.35F);
        pose.scale(1.0F + squash, 1.0F - squash * 1.15F, 1.0F + squash);
    }
}
