package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.monster.Zombie;

/**
 * ★ Q 弹版：**Q 版僵尸**（大头 + 短手短腿的矮胖造型）。
 *
 * <h2>为什么要自己写几何（而不只是缩放原版模型）</h2>
 * 原版僵尸模型头 8³、身高 32 模型单位；「Q 版」的关键是**头身比**（这里头 12³、全身 23 单位 ≈ 1.35 格），
 * 而且头变大方块后原版贴图的展开区（32×16）装不下 12³ 的头
 * ⇒ 必须**自己定义 UV 布局 + 自己画一张 64×64 的 Q 版皮肤**
 * （生成脚本 {@code tools/q_chibi_zombie_tex.py}，贴图 {@code textures/entity/q_chibi_zombie.png}）。
 *
 * <h2>UV 布局（脚本按同一张表画贴图，改模型必须同步改脚本）</h2>
 * <pre>
 *   head       12×12×12 @ (0, 0)     展开 48×24，正面在 (12, 12) 12×12
 *   body        6× 6× 5 @ (0, 26)    展开 22×11，正面在 (5, 31)  6×6
 *   right_arm   4× 8× 4 @ (0, 38)    展开 16×12，正面在 (4, 42)
 *   left_arm    4× 8× 4 @ (18, 38)   同上
 *   right_leg   4× 5× 4 @ (0, 51)    展开 16×9， 正面在 (4, 56)
 *   left_leg    4× 5× 4 @ (18, 51)
 * </pre>
 * 坐标是「y 向下、脚底在 y=24」（与原版人形模型同一套空间，渲染器统一 -1.501 偏移）。
 *
 * <p>手臂的「僵尸前伸」姿势是本类自己摆的（{@link #setupAnim}），不继承 {@code ZombieModel}
 * —— 那个类的 {@code setupAnim} 会把手臂硬拽到 x=±5，和这里的 6 宽身子对不上。
 *
 * <p>泛型 {@code T extends Zombie}：这样 {@code QChibiZombieRenderer<BomberZombie>} 才能满足
 * {@code HumanoidMobRenderer<T, M extends HumanoidModel<T>>} 的类型约束（渲染器注册要精确到具体生物类型）。
 */
public class QChibiZombieModel<T extends Zombie> extends HumanoidModel<T> {

    /** 模型层 id（在 {@code ModClient} 里注册，Q 弹版才用得到） */
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "q_chibi_zombie"), "main");

    /**
     * ★ Q 版骷髅也复用**同一套 chibi 几何**（同一张 UV 表 ⇒ 换一张骨头皮肤就行）：
     * 行为由原版 {@code SkeletonModel} 提供（拉弓瞄准/走路摆手），几何用这一层。
     * 单独一个层 id 只是为了让骷髅能自己 bake 一份、不被僵尸的染色影响。
     */
    public static final ModelLayerLocation SKELETON_LAYER = new ModelLayerLocation(
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "q_chibi_skeleton"), "main");

    public QChibiZombieModel(ModelPart root) {
        super(root);
    }

    /** 几何（尺寸必须与 {@code tools/q_chibi_zombie_tex.py} 的 UV 表一致） */
    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        // 大头：Q 版的灵魂（12³，坐在肩膀上）
        root.addOrReplaceChild("head", CubeListBuilder.create()
                        .texOffs(0, 0).addBox(-6.0F, -12.0F, -6.0F, 12.0F, 12.0F, 12.0F),
                PartPose.offset(0.0F, 13.0F, 0.0F));
        root.addOrReplaceChild("hat", CubeListBuilder.create(), PartPose.ZERO);
        // 矮胖身子（6 宽 5 深：比头窄，头会「盖」在身子上，正是 Q 版的比例）
        root.addOrReplaceChild("body", CubeListBuilder.create()
                        .texOffs(0, 26).addBox(-3.0F, -6.0F, -2.5F, 6.0F, 6.0F, 5.0F),
                PartPose.offset(0.0F, 19.0F, 0.0F));
        // 短手臂（4×8×4，肩点在 y=14）
        root.addOrReplaceChild("right_arm", CubeListBuilder.create()
                        .texOffs(0, 38).addBox(-2.0F, -1.0F, -2.0F, 4.0F, 8.0F, 4.0F),
                PartPose.offset(-5.0F, 14.0F, 0.0F));
        root.addOrReplaceChild("left_arm", CubeListBuilder.create()
                        .texOffs(18, 38).addBox(-2.0F, -1.0F, -2.0F, 4.0F, 8.0F, 4.0F),
                PartPose.offset(5.0F, 14.0F, 0.0F));
        // 短腿（4×5×4，脚底在 y=24）
        root.addOrReplaceChild("right_leg", CubeListBuilder.create()
                        .texOffs(0, 51).addBox(-2.0F, -5.0F, -2.0F, 4.0F, 5.0F, 4.0F),
                PartPose.offset(-1.8F, 24.0F, 0.0F));
        root.addOrReplaceChild("left_leg", CubeListBuilder.create()
                        .texOffs(18, 51).addBox(-2.0F, -5.0F, -2.0F, 4.0F, 5.0F, 4.0F),
                PartPose.offset(1.8F, 24.0F, 0.0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /**
     * 姿势：走 / 站的摆动沿用 {@link HumanoidModel}，另外把两条手臂摆成僵尸经典的**前伸**，
     * 并加一点 Q 弹的「晃手」——手臂随呼吸轻轻上下摆，看起来软乎乎的。
     */
    @Override
    public void setupAnim(T entity, float limbSwing, float limbSwingAmount, float ageInTicks,
                          float netHeadYaw, float headPitch) {
        super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);
        float sw = Mth.cos(limbSwing * 0.6662F) * 0.7F * limbSwingAmount;
        this.rightArm.xRot = -((float) Math.PI * 0.5F) + 0.12F * Mth.sin(ageInTicks * 0.09F) + sw;
        this.leftArm.xRot = -((float) Math.PI * 0.5F) - 0.12F * Mth.sin(ageInTicks * 0.09F) - sw;
        this.rightArm.zRot = 0.10F * Mth.cos(ageInTicks * 0.09F);
        this.leftArm.zRot = -0.10F * Mth.cos(ageInTicks * 0.09F);
        // 大头随呼吸轻微点動（Q 弹感）
        this.head.xRot += 0.05F * Mth.sin(ageInTicks * 0.12F);
    }
}
