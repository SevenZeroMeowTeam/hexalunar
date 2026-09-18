package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.entity.BoltEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * 十字弩：右键按住瞄准（举弩），左键射击弩箭。
 *
 * <p><b>上弦（装填）</b>：每次击发后弦复位，必须重新上弦才能再射。上弦只要背包里
 * （含弹药盒）有弩箭即可，不需要手上拿着箭；耗时 {@link #RELOAD_TICKS} ≈ 1.5 秒，
 * 期间模型播放「弦拉回 + 弓臂内弯 + 弩箭滑入箭槽」的动画。
 */
public class CrossbowWeaponItem extends Item implements WeaponAmmo, GeoItem {

    /** 动画名前缀与控制器名（照 SuperbWarfare BOCEK 规范：animation.<id>.<state>） */
    public static final String ANIM_PREFIX = "animation.crossbow.";
    public static final String C_MOVE = "moveController";
    public static final String C_FIRE = "fireController";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    // ------------------------------------------------------------ GeckoLib
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, C_MOVE, 3, this::movePredicate));
        controllers.add(new AnimationController<>(this, C_FIRE, 0, this::firePredicate));
    }

    /** 待机 / 跑动摆动（拉弦装弹是连续的，在 CrossbowGeoModel 里按 reloadProgress 程序化驱动） */
    private PlayState movePredicate(AnimationState<CrossbowWeaponItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (sprintIng()) {
            return event.setAndContinue(RawAnimation.begin().thenLoop(
                    ANIM_PREFIX + (sprintFastNow() ? "run_fast" : "run")));
        }
        return event.setAndContinue(RawAnimation.begin().thenLoop(ANIM_PREFIX + "idle"));
    }

    /** 放箭：单独一层，播完即停 */
    private PlayState firePredicate(AnimationState<CrossbowWeaponItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (cn.blockforge.generated.hexalunarcalamity.client.CrossbowAnimState.firing()) {
            return event.setAndContinue(RawAnimation.begin().thenPlay(ANIM_PREFIX + "fire"));
        }
        return PlayState.STOP;
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    private static boolean sprintIng() {
        return cn.blockforge.generated.hexalunarcalamity.client.CrossbowAnimState.sprinting();
    }

    private static boolean sprintFastNow() {
        return cn.blockforge.generated.hexalunarcalamity.client.CrossbowAnimState.sprintFast();
    }

    /** 左键按住时的连发间隔（tick），客户端按此节奏发送开火包 */
    public static final int FIRE_INTERVAL = 5;

    /** 上弦耗时（tick），约 1.5 秒 */
    public static final int RELOAD_TICKS = 30;

    private static final String TAG_COCKED = "HlcCocked";
    private static final String TAG_RELOAD_UNTIL = "HlcReloadUntil";

    public CrossbowWeaponItem(Properties properties) {
        super(properties);
    }

    // ------------------------------------------------------------------ 上弦状态

    /** 是否正在上弦 */
    public static boolean reloading(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getLong(TAG_RELOAD_UNTIL) > gameTime;
    }

    /** 上弦进度 0..1；没在上弦返回 -1 */
    public static float reloadProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null) return -1.0F;
        long until = tag.getLong(TAG_RELOAD_UNTIL);
        if (until <= gameTime) return -1.0F;
        return Mth.clamp(1.0F - (until - gameTime) / (float) RELOAD_TICKS, 0.0F, 1.0F);
    }

    /** 是否已上弦（弦挂在弦爪上、弩箭在箭槽里） */
    public static boolean cocked(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getBoolean(TAG_COCKED);
    }

    /** 开始上弦：背包/弹药盒里有弩箭就行 */
    private boolean tryStartReload(Level level, Player player, ItemStack stack) {
        long now = level.getGameTime();
        if (reloading(stack, now)) return false;
        if (AmmoUtil.count(player, AmmoType.BOLT) <= 0) return false;
        CompoundTag tag = stack.getOrCreateTag();
        tag.putLong(TAG_RELOAD_UNTIL, now + RELOAD_TICKS);
        tag.putBoolean(TAG_COCKED, false);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.RELOAD.get(), SoundSource.PLAYERS, 0.9F, 1.18F);
        return true;
    }

    /** R 键手动上弦（服务端） */
    @Override
    public void serverReload(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (level.isClientSide) return;
        if (reloading(stack, level.getGameTime()) || cocked(stack)) return;
        if (!tryStartReload(level, player, stack)) {
            player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
        }
    }

    /** 走时间完成上弦（服务端）：弦挂上、弩箭入槽 */
    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (level.isClientSide) return;
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_RELOAD_UNTIL)) return;
        if (reloading(stack, level.getGameTime())) return;
        tag.remove(TAG_RELOAD_UNTIL);
        tag.putBoolean(TAG_COCKED, true);
        // 弦到位 / 箭入槽的机械声
        level.playSound(null, entity.getX(), entity.getY(), entity.getZ(),
                ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.55F, 1.45F);
    }

    @Override
    public AmmoType ammoType() {
        return AmmoType.BOLT;
    }

    /** 客户端：第三人称手臂姿态（双手举弩 / 开镜时端平） */
    @Override
    public void initializeClient(java.util.function.Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.CrossbowItemClientExtensions.INSTANCE);
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
        long now = level.getGameTime();
        // 上弦中不能射
        if (reloading(stack, now)) return;
        // 弦没挂上：先自动上弦（背包有弹药的话）
        if (!cocked(stack)) {
            if (!tryStartReload(level, player, stack)) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return;
        }
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
        // 击发后弦复位：立刻开始下一轮上弦（背包还有弩箭时）
        stack.getOrCreateTag().putBoolean(TAG_COCKED, false);
        tryStartReload(level, player, stack);
    }
}
