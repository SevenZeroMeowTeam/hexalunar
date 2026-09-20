package cn.blockforge.generated.hexalunarcalamity.effect;

import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;

import java.nio.charset.StandardCharsets;
import java.util.UUID;

/**
 * 眩晕：震爆弹命中后的短暂失能。
 *
 * <p>移动速度接近归零、攻击速度大幅下降，玩家还会被强制结束疾跑。
 * 客户端另外用镜头晃动 + 视野呼吸表达「天旋地转」，见 {@code ClientEvents}。
 */
public class StunEffect extends MobEffect {

    public StunEffect() {
        super(MobEffectCategory.HARMFUL, 0xFFC94D);
        // 1.20.1 的 addAttributeModifier 第二参必须是合法 UUID 字符串，
        // 用名字派生保证跨存档稳定且互不冲突。
        this.addAttributeModifier(Attributes.MOVEMENT_SPEED, key("stun_speed"),
                -0.94D, net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_TOTAL);
        this.addAttributeModifier(Attributes.ATTACK_SPEED, key("stun_attack"),
                -0.70D, net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_TOTAL);
    }

    private static String key(String name) {
        // ★ 用 MOD_ID：Q 弹版与原版**同时安装**时，两边的属性修饰符 UUID 必须不同，
        //   否则同一个实体的同一属性会被对方的修饰符顶掉（同一 UUID 不能重复挂）
        return UUID.nameUUIDFromBytes((cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity.MOD_ID
                + ":" + name).getBytes(StandardCharsets.UTF_8)).toString();
    }

    @Override
    public void applyEffectTick(LivingEntity entity, int amplifier) {
        if (entity instanceof Player player && player.isSprinting()) {
            player.setSprinting(false);
        }
    }

    @Override
    public boolean isDurationEffectTick(int duration, int amplifier) {
        return true;
    }
}
