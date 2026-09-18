package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.entity.PiercingArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * 复合弓：右键按住 = 瞄准蓄力，松开右键满蓄射击；
 * 左键 = 按当前蓄力直接击发（准度随蓄力提高）。
 * 无普通箭时自动改用尸毒箭。
 *
 * <p>GeckoLib 真骨骼：13 根骨骼（弓把/握把/瞄具/稳定杆/上下弓片/上下凸轮/弦两段/弦中心/箭）。
 * 动作动画：{@code reload}（R 键搭箭）、{@code draw}（右键按住拉弦，拉满后保持不回弹）、
 * {@code release}（松手/击发，弦回弹 + 箭飞出去）。
 */
public class CompoundBowItem extends Item implements WeaponAmmo, GeoItem {

    /** 左键连点的最小间隔（tick），客户端按此节奏发开火包 */
    public static final int FIRE_INTERVAL = 8;

    /** 动画名前缀与控制器名（规矩同 SuperbWarfare BOCEK：animation.<id>.<state>） */
    public static final String ANIM_PREFIX = "animation.compound_bow.";
    public static final String C_IDLE = "idleController";
    public static final String C_FIRE = "fireController";
    public static final String C_RELOAD = "reloadController";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    public CompoundBowItem(Properties properties) {
        super(properties);
    }

    // ------------------------------------------------------------ GeckoLib
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, C_IDLE, 3, this::idlePredicate));
        controllers.add(new AnimationController<>(this, C_FIRE, 0, this::firePredicate));
        controllers.add(new AnimationController<>(this, C_RELOAD, 0, this::reloadPredicate));
    }

    private static final String BOW_STATE =
            "cn.blockforge.generated.hexalunarcalamity.client.BowAnimState";

    /** 待机 / 拉弦 / 跑动；拉弦用 thenPlayAndHold，拉满后弦不会自己回弹 */
    private PlayState idlePredicate(AnimationState<CompoundBowItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (pulling()) {
            return event.setAndContinue(RawAnimation.begin().thenPlayAndHold(ANIM_PREFIX + "pull"));
        }
        if (sprinting()) {
            return event.setAndContinue(RawAnimation.begin().thenLoop(
                    ANIM_PREFIX + (sprintFast() ? "run_fast" : "run")));
        }
        return event.setAndContinue(RawAnimation.begin().thenLoop(ANIM_PREFIX + "idle"));
    }

    /** 放箭：单独一层，播完即停，不占用 idle 那层 */
    private PlayState firePredicate(AnimationState<CompoundBowItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (held() && firing()) {
            return event.setAndContinue(RawAnimation.begin().thenPlay(ANIM_PREFIX + "fire"));
        }
        return PlayState.STOP;
    }

    /** 搭箭（换弹） */
    private PlayState reloadPredicate(AnimationState<CompoundBowItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (held() && reloading()) {
            return event.setAndContinue(RawAnimation.begin().thenPlay(ANIM_PREFIX + "reload"));
        }
        return PlayState.STOP;
    }

    // 客户端标志都在 client.BowAnimState（客户端类），这里只做布尔转发，
    // 免得把 Minecraft 引到通用侧（专用服务器会 NoClassDefFoundError）
    private static boolean held() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.held();
    }

    private static boolean pulling() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.pulling();
    }

    private static boolean sprinting() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.sprinting();
    }

    private static boolean sprintFast() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.sprintFast();
    }

    private static boolean firing() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.firing();
    }

    private static boolean reloading() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.reloading();
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    @Override
    public AmmoType ammoType() {
        return AmmoType.ARROW;
    }

    /** 客户端：手臂姿态（原版按 UseAnim.BOW 自己给拉弓姿势）+ GeckoLib 骨骼渲染 */
    @Override
    public void initializeClient(java.util.function.Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.BowItemClientExtensions.INSTANCE);
    }

    /** 右键：搭箭 → 拉弦。*/    
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (AmmoUtil.count(player, AmmoType.ARROW) <= 0 && !hasPoisonArrow(player)) {
            if (!level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return InteractionResultHolder.fail(stack);
        }
        player.startUsingItem(hand);
        return InteractionResultHolder.success(stack);
    }

    private boolean hasPoisonArrow(Player player) {
        for (ItemStack stack : player.getInventory().items) {
            if (stack.is(ModItems.POISON_ARROW.get())) return true;
        }
        return false;
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    /**
     * ★ 不能用 {@code UseAnim.BOW}：原版 {@code ItemInHandRenderer} 会对 BOW 的物品再套一段拉弓位移
     * （rotX -13.9° / rotY 35.3°→-45° / rotZ -9.8° + z 轴拉伸 20%），弓就变成斜的、也不是「垂直拿在手上」
     * 了；而且那段位移和我们要的举弓对心互相打架。
     * 拉弓手臂姿势改为 {@link cn.blockforge.generated.hexalunarcalamity.client.WeaponArmPose#BOW}
     * 自己返回 {@code BOW_AND_ARROW}（与 UseAnim 无关），举弓对心由 {@code BowGeoModel} 推 move 骨骼做。
     */
    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.NONE;
    }

    @Override
    public void appendHoverText(ItemStack stack, Level level,
                                java.util.List<net.minecraft.network.chat.Component> tips,
                                net.minecraft.world.item.TooltipFlag flag) {
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.bow_controls")
                .withStyle(net.minecraft.ChatFormatting.GRAY));
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.range_hint", (int) Ballistics.BOW_RANGE)
                .withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
    }

    /** 供 HUD / 视野缩放使用：由剩余使用 tick 换算蓄力成数 */
    public static float pullProgress(int remainingUseTicks) {
        return BowItem.getPowerForTime(72000 - remainingUseTicks);
    }

    /** 松开右键：弦回弹，并以当前蓄力射击（放箭动画由客户端标志驱动） */
    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
        if (!(entity instanceof Player player) || level.isClientSide) return;
        int useTime = this.getUseDuration(stack) - timeLeft;
        float pull = BowItem.getPowerForTime(useTime);
        if (pull < 0.15F) return;
        shoot(player, stack, level, InteractionHand.MAIN_HAND, pull);
    }

    /** R 键：搭箭（客户端标志由 ClientGunController 设置，这里只做服务端确认） */
    @Override
    public void serverReload(Player player, ItemStack stack, InteractionHand hand) {
        // 弓没有弹匣，搭箭完全由动画表达；服务端无需额外处理
    }

    /** 左键（服务端）：按当前瞄准蓄力击发，最低保底 0.35 成数 */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        float pull = 0.35F;
        if (player.isUsingItem() && player.getUseItem() == stack) {
            int useTime = this.getUseDuration(stack) - player.getUseItemRemainingTicks();
            pull = Math.max(pull, BowItem.getPowerForTime(useTime));
        }
        shoot(player, stack, level, hand, pull);
    }

    /** 实际击发：pull 为 0~1 蓄力成数 */
    private void shoot(Player player, ItemStack stack, Level level, InteractionHand hand, float pull) {
        boolean poison = false;
        if (!AmmoUtil.consume(player, AmmoType.ARROW, 1)) {
            // 改用尸毒箭
            if (AmmoUtil.takeFromInventory(player, ModItems.POISON_ARROW.get(), 1) > 0) {
                poison = true;
            } else {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
                return;
            }
        }

        PiercingArrowEntity arrow = new PiercingArrowEntity(level, player);
        // ★ 箭从**弓的搭箭点**射出、朝准星落点飞（同 AKM 那套）：画面上箭才是从弓上发出去的，
        //   而不是从屏幕中间飞出来。拉弓时弓已经被举到位（BowGeoModel 的对心偏移），两边一致。
        Vec3 from = WeaponMount.bow(player, pull > 0.02F, WeaponMount.BOW_ARROW);
        Vec3 dir = WeaponMount.fireDir(player, level, from, 6.0D, 64.0D);
        arrow.setPos(from.x, from.y, from.z);
        arrow.shoot(dir.x, dir.y, dir.z, 2.6F + 1.4F * pull, 1.0F - pull);
        arrow.setBaseDamage(5.0D + 7.5D * pull * pull);
        arrow.setPierceLevel((byte) 2);
        arrow.setCritArrow(pull >= 1.0F);
        arrow.setToxic(poison);
        level.addFreshEntity(arrow);

        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.BOW_SHOT.get(), SoundSource.PLAYERS, 1.0F,
                Mth.clamp(0.9F + pull * 0.25F, 0.8F, 1.3F));
        player.swing(hand);
    }
}
