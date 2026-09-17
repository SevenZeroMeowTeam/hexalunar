package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.entity.BulletEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

/**
 * AKM：高射速大弹匣（30 发），使用 7.62x39 子弹。
 * 右键按住 = 瞄准（抵肩），空仓时右键 = 手动装填；
 * 左键单发点射，按住左键全自动连发（每 2 tick 一发）；
 * 持续射击会积累热量放大散布，瞄准能显著压散布，打空自动装填。
 */
public class AkmRifleItem extends Item implements WeaponAmmo {

    public static final int MAG_SIZE = 30;
    public static final int RELOAD_TICKS = 40;
    /** 全自动射速：客户端按此间隔发开火包 */
    public static final int FIRE_INTERVAL = 2;

    private static final int HEAT_DECAY_IDLE_TICKS = 12;

    public AkmRifleItem(Properties properties) {
        super(properties);
    }

    @Override
    public AmmoType ammoType() {
        return AmmoType.RIFLE;
    }

    /** 客户端：第三人称手臂姿态（双手握持 / 抵肩） */
    @Override
    public void initializeClient(java.util.function.Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.WeaponArmPose.AKM);
    }

    public static int mag(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0 : tag.getInt("HlcMag");
    }

    public static void setMag(ItemStack stack, int value) {
        stack.getOrCreateTag().putInt("HlcMag", Mth.clamp(value, 0, MAG_SIZE));
    }

    public static boolean reloading(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getLong("HlcReloadUntil") > gameTime;
    }

    /** 换弹进度 0..1（供客户端手持动画使用）；没在换弹返回 -1 */
    public static float reloadProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null) return -1.0F;
        long until = tag.getLong("HlcReloadUntil");
        if (until <= gameTime) return -1.0F;
        float left = (float) (until - gameTime);
        return Mth.clamp(1.0F - left / RELOAD_TICKS, 0.0F, 1.0F);
    }

    /** 右键：空仓时装填，否则进入瞄准姿态 */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (mag(stack) == 0 && !reloading(stack, level.getGameTime())) {
            if (tryStartReload(level, player, stack)) {
                player.startUsingItem(hand);
                return InteractionResultHolder.success(stack);
            }
            if (!level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return InteractionResultHolder.fail(stack);
        }
        player.startUsingItem(hand);
        return InteractionResultHolder.success(stack);
    }

    private boolean tryStartReload(Level level, Player player, ItemStack stack) {
        if (level.isClientSide) return true;
        int available = Math.min(MAG_SIZE - mag(stack), AmmoUtil.count(player, AmmoType.RIFLE));
        if (available <= 0) return false;
        stack.getOrCreateTag().putLong("HlcReloadUntil", level.getGameTime() + RELOAD_TICKS);
        // 换弹开始：卸弹匣 / 插弹匣的机械声
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_RELOAD.get(), SoundSource.PLAYERS, 1.0F,
                0.94F + level.random.nextFloat() * 0.12F);
        return true;
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BOW;
    }

    @Override
    public void appendHoverText(ItemStack stack, Level level,
                                java.util.List<net.minecraft.network.chat.Component> tips,
                                net.minecraft.world.item.TooltipFlag flag) {
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.akm_controls")
                .withStyle(net.minecraft.ChatFormatting.GRAY));
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.range_hint", (int) Ballistics.AKM_RANGE)
                .withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
    }

    /** 装填完成后自动退出装填姿态（瞄准可继续） */
    @Override
    public void onUseTick(Level level, net.minecraft.world.entity.LivingEntity living,
                          ItemStack stack, int remaining) {
        if (!(living instanceof Player player) || level.isClientSide) return;
        CompoundTag tag = stack.getTag();
        if (tag != null && tag.contains("HlcReloadUntil") && !reloading(stack, level.getGameTime())) {
            player.releaseUsingItem();
        }
    }

    /** 左键（服务端）：全自动击发一发 */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (reloading(stack, level.getGameTime())) return;
        if (mag(stack) <= 0) {
            if (!tryStartReload(level, player, stack) && !level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return;
        }
        boolean aiming = player.isUsingItem() && player.getUseItem() == stack;
        fire(level, player, stack, hand, aiming);
    }

    /** R 键（服务端）：战术装填——弹匣未满也能补弹，满仓/换弹中/无弹则忽略 */
    @Override
    public void serverReload(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (level.isClientSide || reloading(stack, level.getGameTime())) return;
        if (mag(stack) >= MAG_SIZE) return;
        if (!tryStartReload(level, player, stack)) {
            player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
        }
    }

    private void fire(Level level, Player player, ItemStack stack, InteractionHand hand, boolean aiming) {
        setMag(stack, mag(stack) - 1);
        CompoundTag tag = stack.getOrCreateTag();
        int heat = Mth.clamp(tag.getInt("HlcHeat") + 1, 0, 30);
        tag.putInt("HlcHeat", heat);
        tag.putLong("HlcLastShot", level.getGameTime());

        // 腰射散布大，瞄准压到很小；连射热量再放大散布
        float spread = (aiming ? 0.16F : 0.85F) + heat * 0.045F;
        BulletEntity bullet = new BulletEntity(level, player);
        bullet.setPos(player.getEyePosition().add(player.getLookAngle().scale(0.7D)));
        bullet.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F,
                aiming ? 5.0F : 4.5F, spread);
        level.addFreshEntity(bullet);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_SHOT.get(), SoundSource.PLAYERS, 1.1F,
                0.97F + level.random.nextFloat() * 0.08F);
        // 枪口火花
        if (level instanceof net.minecraft.server.level.ServerLevel server) {
            var pos = player.getEyePosition().add(player.getLookAngle().scale(0.9D));
            server.sendParticles(net.minecraft.core.particles.ParticleTypes.SMALL_FLAME,
                    pos.x, pos.y, pos.z, aiming ? 1 : 2, 0.05, 0.05, 0.05, 0.0);
        }
    }

    private void finishReload(Level level, Player player, ItemStack stack) {
        int want = MAG_SIZE - mag(stack);
        int got = 0;
        // 弹药盒优先供弹
        got += AmmoUtil.takeFromBox(player, AmmoType.RIFLE, want);
        if (got < want) {
            got += AmmoUtil.takeFromInventory(player, AmmoType.RIFLE.get(), want - got);
        }
        setMag(stack, mag(stack) + got);
        player.swing(InteractionHand.MAIN_HAND);
        // 换弹完成：拉栓闭锁的脆响
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 1.0F,
                0.98F + level.random.nextFloat() * 0.08F);
    }

    @Override
    public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity,
                              int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (level.isClientSide || !(entity instanceof Player player)) return;
        CompoundTag tag = stack.getTag();
        if (tag == null) return;
        // 装填计时结束：上弹（无需继续按住右键）
        if (tag.contains("HlcReloadUntil") && tag.getLong("HlcReloadUntil") <= level.getGameTime()) {
            tag.remove("HlcReloadUntil");
            finishReload(level, player, stack);
        }
        // 停火后热量自然衰减
        if (tag.getInt("HlcHeat") > 0
                && level.getGameTime() - tag.getLong("HlcLastShot") >= HEAT_DECAY_IDLE_TICKS) {
            tag.putInt("HlcHeat", tag.getInt("HlcHeat") - 1);
        }
    }
}
