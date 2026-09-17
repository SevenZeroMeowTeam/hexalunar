package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.entity.BoltEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

/**
 * 十字弩：右键按住瞄准（举弩），左键射击弩箭，持续按住左键每 5 tick 连发；
 * 瞄准状态下散布大幅收紧、初速更高。
 */
public class CrossbowWeaponItem extends Item implements WeaponAmmo {

    /** 左键按住时的连发间隔（tick），客户端按此节奏发送开火包 */
    public static final int FIRE_INTERVAL = 5;

    public CrossbowWeaponItem(Properties properties) {
        super(properties);
    }

    @Override
    public AmmoType ammoType() {
        return AmmoType.BOLT;
    }

    /** 客户端：第三人称手臂姿态（双手举弩 / 开镜时端平） */
    @Override
    public void initializeClient(java.util.function.Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.WeaponArmPose.CROSSBOW);
    }

    /** 倍镜放大倍率：4 倍 */
    public static final float SCOPE_ZOOM = 4.0F;

    /** 是否正通过倍镜瞄准：右键按住举弩即开镜（客户端 HUD / FOV / 遮手判定用） */
    public static boolean isScoping(net.minecraft.world.entity.LivingEntity entity) {
        return entity.isUsingItem()
                && entity.getUseItem().getItem() instanceof CrossbowWeaponItem;
    }

    /** 右键：进入瞄准姿态（不再直接击发） */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (AmmoUtil.count(player, AmmoType.BOLT) <= 0) {
            if (!level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return InteractionResultHolder.fail(stack);
        }
        player.startUsingItem(hand);
        return InteractionResultHolder.success(stack);
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        // 用 BOW 而不是 CROSSBOW：原版只有 items.crossbow 才走弩的姿势分支，
        // 模组弩用 CROSSBOW 会完全没有手部/举弩/拉弦动作（UseAnim.BOW 则能拿到握弓蓄力姿态）
        return UseAnim.BOW;
    }

    @Override
    public void appendHoverText(ItemStack stack, net.minecraft.world.level.Level level,
                                java.util.List<net.minecraft.network.chat.Component> tips,
                                net.minecraft.world.item.TooltipFlag flag) {
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.crossbow_controls")
                .withStyle(net.minecraft.ChatFormatting.GRAY));
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.range_hint", (int) Ballistics.BOLT_RANGE)
                .withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
    }

    /** 左键（服务端）：击发一发弩箭 */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (!AmmoUtil.consume(player, AmmoType.BOLT, 1)) {
            player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            return;
        }
        boolean aiming = player.isUsingItem() && player.getUseItem() == stack;
        BoltEntity bolt = new BoltEntity(level, player);
        bolt.setPos(player.getEyePosition().add(player.getLookAngle().scale(0.6D)));
        // 开镜时零散布、稍高初速：4 倍镜下打的是远目标，散布会让准星失准
        bolt.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F,
                aiming ? 4.0F : 3.4F, aiming ? 0.0F : 0.6F);
        bolt.setCritArrow(false);
        level.addFreshEntity(bolt);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.CROSSBOW_SHOT.get(), SoundSource.PLAYERS, 1.0F,
                0.95F + level.random.nextFloat() * 0.1F);
        player.swing(hand);
    }
}
