package cn.blockforge.generated.hexalunarcalamity.effect;

import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;

/**
 * 尸毒：周期性伤害、减速、加速饥饿。对亡灵无效（施加端已过滤）。
 */
public class CorpsePoisonEffect extends MobEffect {

    public CorpsePoisonEffect() {
        super(MobEffectCategory.HARMFUL, 0x6B8E23);
        // 1.20.1 的 addAttributeModifier 第二参会被 UUID.fromString 解析，
        // 必须传合法 UUID 字符串；这里用名字做 MD5 派生，保证跨存档稳定且互不冲突。
        this.addAttributeModifier(Attributes.MOVEMENT_SPEED, modifierKey("poison_speed"),
                -0.18D, net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_TOTAL);
        this.addAttributeModifier(Attributes.ATTACK_DAMAGE, modifierKey("poison_strength"),
                -0.10D, net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_TOTAL);
    }

    private static String modifierKey(String name) {
        return java.util.UUID.nameUUIDFromBytes(
                ("hexalunar_calamity:" + name).getBytes(java.nio.charset.StandardCharsets.UTF_8)).toString();
    }

    @Override
    public void applyEffectTick(LivingEntity entity, int amplifier) {
        if (!entity.level().isClientSide) {
            entity.hurt(entity.damageSources().magic(), 1.0F + amplifier);
            if (entity instanceof Player) {
                // 尸毒侵蚀饱腹感：给玩家续一段饥饿效果
                entity.addEffect(new net.minecraft.world.effect.MobEffectInstance(
                        MobEffects.HUNGER, 60, Math.max(0, amplifier)));
            }
        }
    }

    @Override
    public boolean isDurationEffectTick(int duration, int amplifier) {
        int interval = 40 >> amplifier;
        if (interval <= 0) return duration % 2 == 0;
        return duration % interval == 0;
    }
}
