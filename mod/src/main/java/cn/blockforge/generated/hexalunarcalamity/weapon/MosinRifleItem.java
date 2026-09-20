package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.client.MosinAnimState;
import cn.blockforge.generated.hexalunarcalamity.client.MosinItemClientExtensions;
import cn.blockforge.generated.hexalunarcalamity.entity.BulletEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.List;
import java.util.function.Consumer;

/**
 * 莫辛-纳甘 M91/30 栓动步枪（7.62x59，出厂自带 4 倍镜）。
 *
 * <h2>数值来源：TaCZ 的 Kar98k 配置</h2>
 * 导出自 {@code D:/mcmod/src/main/libs/[永恒枪械工坊：零] tacz-1.20.1-1.1.8-hotfix.jar}
 * （见 {@code mod/build/tacz_kar98/} 与 {@code tools/_tacz_probe.py}）：
 * <ul>
 *   <li>{@code kar98_display.json}：{@code zoom_model_fov = 25}（→ {@code GunPose.MODEL_FOV_AIM_MOSIN}）、
 *       {@code iron_zoom = 2}（→ {@link #IRON_ZOOM}）、{@code transform} 只给缩放
 *       （旋转/位移用模型内定位组 ⇒ 我们的 ADS 只做平移）</li>
 *   <li>{@code kar98_data.json}：{@code bolt_action_time 0.85s}（→ {@link #BOLT_TICKS}）、
 *       {@code aim_time 0.2s}、{@code reload.loop 0.68s / feed 2.85~3.5s}（→ 逐发压弹节奏）、
 *       弹伤 26 / 爆头 1.85（→ {@code BulletEntity.MOSIN_DAMAGE}）、{@code bullet_lost 0.3}</li>
 *   <li>{@code scope_98k_data.json}：{@code zoom 4.25} → 我们挂 4 倍镜（{@link #SCOPE_ZOOM}）</li>
 *   <li>{@code kar98_geo.json}：{@code idle_view (2, 9.8125, 17.0)} → {@code iron_view (0, 8.75, 17.5)}
 *       ⇒ 举枪 = 「X 归零 + 上抬，几乎不前后走」（→ {@link WeaponMount#MOSIN_AIM_DZ}）</li>
 * </ul>
 *
 * <h2>★ 装填方式：一发一发压进弹仓（不是换弹匣）</h2>
 * 莫辛是**弹仓式**（内藏 5 发，没有可拆弹匣），子弹要用手一发一发从机匣上方压进去。
 * 所以这里的换弹不是「一次性换弹匣」，而是一条**逐发时间轴**：
 * <pre>
 *   开栓（{@link #BOLT_OPEN_TICKS}）→ 每发 {@link #LOAD_TICKS} × 需要几发 → 关栓上膛（{@link #BOLT_CLOSE_TICKS}）
 *   每一发到点：消耗 1 发弹药、弹仓 +1、响一声「咔」，模型里那一发从机匣上方落进弹仓
 *   关栓那一刻：从弹仓推一发进弹膛（弹仓 −1、膛内 +1）—— 与拉栓后的「再上膛」同一条规则
 * </pre>
 * 中途被打断（丢下枪 / 再按一次 R）时，正在压的那一发按 TaCZ 的 {@code bullet_lost = 0.3} 规则
 * 有 {@link #BULLET_LOST_CHANCE} 概率掉在地上（已经压进去的留在弹仓里）。
 *
 * <h2>拉栓循环：抽壳 → 抛壳 → 再上膛</h2>
 * 击发后自动：抬柄转栓 → 枪机后退把空弹壳**带出来** → 弹壳被抛壳挺顶出去（模型里 {@code casing}
 * 骨骼往 +X 翻滚飞出）→ 枪机推回闭锁，同时把弹仓里下一发**顶进弹膛**（{@code finishBolt}：
 * 弹仓 −1、膛内 +1）。没弹了就只闭锁、膛内留空。
 *
 * <h2>NBT</h2>
 * <pre>
 *   HlcMag / HlcChamber        弹仓余弹 0..5 / 膛内是否有弹
 *   HlcBoltUntil / HlcBoltSfx  拉栓结束刻 / 拉栓音效该响的那一刻
 *   HlcFireAt                  最后一次击发时刻（扣扳机动画窗口）
 *   HlcLoadAt / HlcLoadNeed    逐发装填的开始刻 / 这次要压几发
 *   HlcLoadDone                这次已经压进去几发（用于逐发消耗弹药）
 *   HlcSight                   瞄具档位（默认 4 倍镜，见 {@link #sight}）
 * </pre>
 */
public class MosinRifleItem extends Item implements WeaponAmmo, GeoItem {

    // ---------------------------------------------------------------- 数值
    /** 弹仓容量（M91/30 的 5 发弹仓）—— 关栓上膛后是「弹仓 4 + 膛内 1」= 身上最多 5 发 */
    public static final int MAG_SIZE = 5;
    /** 拉栓耗时（tick）：TaCZ kar98k {@code bolt_action_time = 0.85s} ≈ 17 tick，取 18 */
    public static final int BOLT_TICKS = 18;
    /** 击发到抬手拉栓之间的停顿（tick）：右手先留在握把上扣扳机，拉栓音效也晚这么多帧响 */
    public static final int BOLT_DELAY = 5;
    /** 一次完整的栓动循环（击发 → 拉栓 → 可再击发） */
    public static final int CYCLE_TICKS = BOLT_DELAY + BOLT_TICKS;
    /** 扣扳机动画窗口（tick） */
    public static final int FIRE_TICKS = 7;
    /** 子弹初速（格/tick）：7.62x59 介于 AKM（≤5.0）与 AWP（6.2）之间 ⇒ BulletEntity 走「栓动步枪」档 */
    public static final float BULLET_SPEED = 5.4F;

    // ---------------------------------------------------------------- 逐发压弹
    /** 开栓阶段（tick）：转栓 + 把枪机拉到底，之后才开始压弹 */
    public static final int BOLT_OPEN_TICKS = 15;
    /** 每一发的压入耗时（tick）：TaCZ kar98k 的 {@code loop = 0.68s} ≈ 14 tick，取 12 稍紧凑 */
    public static final int LOAD_TICKS = 12;
    /** 关栓上膛阶段（tick）：推枪机进膛 + 转栓闭锁 */
    public static final int BOLT_CLOSE_TICKS = 16;
    /** 这一发的压入进度超过它时被打断，才可能掉弹（TaCZ kar98k {@code bullet_lost = 0.3}） */
    public static final float BULLET_LOST_AT = 0.35F;
    /** 掉弹概率（与 TaCZ 的 {@code bullet_lost} 同值） */
    public static final float BULLET_LOST_CHANCE = 0.30F;

    // ---------------------------------------------------------------- 放大倍率
    /** 4 倍镜（TaCZ {@code scope_98k} 的 {@code zoom = 4.25}） */
    public static final float SCOPE_ZOOM = 4.0F;
    /** 机瞄（TaCZ kar98k {@code iron_zoom = 2}，AKM 是 1.33） */
    public static final float IRON_ZOOM = 2.0F;

    // ---------------------------------------------------------------- 动画
    public static final String GEO_CONTROLLER = "main";

    private static final RawAnimation PLAY_IDLE = RawAnimation.begin().thenLoop("idle");
    private static final RawAnimation PLAY_RUN = RawAnimation.begin().thenLoop("run");
    private static final RawAnimation PLAY_RUN_FAST = RawAnimation.begin().thenLoop("run_fast");
    private static final RawAnimation PLAY_FIRE = RawAnimation.begin().thenPlay("fire");
    private static final RawAnimation PLAY_BOLT = RawAnimation.begin().thenPlay("bolt");
    private static final RawAnimation PLAY_RELOAD = RawAnimation.begin().thenPlay("reload");

    // ---------------------------------------------------------------- NBT
    private static final String TAG_MAG = "HlcMag";
    private static final String TAG_CHAMBER = "HlcChamber";
    private static final String TAG_BOLT_UNTIL = "HlcBoltUntil";
    private static final String TAG_BOLT_SFX = "HlcBoltSfx";
    private static final String TAG_FIRE_AT = "HlcFireAt";
    /** 逐发压弹：这次装填的开始刻 / 要压几发 / 已经压了几发 */
    private static final String TAG_LOAD_AT = "HlcLoadAt";
    private static final String TAG_LOAD_NEED = "HlcLoadNeed";
    private static final String TAG_LOAD_DONE = "HlcLoadDone";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    public MosinRifleItem(Properties properties) {
        super(properties);
    }

    // ================================================================ GeckoLib
    /**
     * 动画状态机：优先级 拉栓 &gt; 装填 &gt; 扣扳机 &gt; 跑动 &gt; idle。
     * 全部 {@code setAndContinue}，同一状态每 tick 重复设置不会重置进度。
     */
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, GEO_CONTROLLER, 1, state -> {
            if (!MosinAnimState.held()) return state.setAndContinue(PLAY_IDLE);
            long now = MosinAnimState.now();
            ItemStack stack = MosinAnimState.heldStack();
            if (stack != null && bolting(stack, now)) return state.setAndContinue(PLAY_BOLT);
            if (stack != null && loading(stack, now)) return state.setAndContinue(PLAY_RELOAD);
            if (stack != null && fireWindow(stack, now) >= 0.0F) return state.setAndContinue(PLAY_FIRE);
            if (MosinAnimState.sprintFast()) return state.setAndContinue(PLAY_RUN_FAST);
            if (MosinAnimState.sprinting()) return state.setAndContinue(PLAY_RUN);
            return state.setAndContinue(PLAY_IDLE);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    @Override
    public void initializeClient(Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(MosinItemClientExtensions.INSTANCE);
    }

    /** 7.62x59 是莫辛专用弹，与 AKM 的 7.62x39、AWP 的 .338 都不通用 */
    @Override
    public AmmoType ammoType() {
        return AmmoType.MOSIN;
    }

    // ================================================================ 瞄具（出厂自带 4 倍镜）
    /**
     * 出厂就把 4 倍镜装在导轨上（用户要求「含 4 倍镜」）。
     *
     * <p>与 AKM 的差别：AKM 的 {@code Sights.sight()} 在没写过 NBT 时返回机瞄，
     * 而**莫辛默认返回 4 倍镜**；拆掉镜子会显式写入 {@code HlcSight = IRON}，
     * 所以拆了之后一直保持机瞄（见 {@link Sights#setExplicit}）。
     */
    public static int sight(ItemStack stack) {
        return Sights.sightDefault(stack, Sights.SCOPE);
    }

    // ================================================================ 弹仓 / 膛内弹 / 计时
    public static int mag(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0 : Mth.clamp(tag.getInt(TAG_MAG), 0, MAG_SIZE);
    }

    public static void setMag(ItemStack stack, int value) {
        stack.getOrCreateTag().putInt(TAG_MAG, Mth.clamp(value, 0, MAG_SIZE));
    }

    /** 膛内是否有弹（没有就打不响，得先拉栓上膛） */
    public static boolean chambered(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getBoolean(TAG_CHAMBER);
    }

    public static void setChambered(ItemStack stack, boolean value) {
        stack.getOrCreateTag().putBoolean(TAG_CHAMBER, value);
    }

    // ---------------------------------------------------------------- 拉栓
    public static boolean bolting(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.contains(TAG_BOLT_UNTIL) && tag.getLong(TAG_BOLT_UNTIL) > gameTime;
    }

    /**
     * 拉栓进度 0..1；没在拉栓（含「击发后、还没抬手」的停顿）返回 -1
     * （枪机位移 / 抛壳轨迹 / 右手抓拉机柄都按它算）。
     */
    public static float boltProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_BOLT_UNTIL)) return -1.0F;
        long left = tag.getLong(TAG_BOLT_UNTIL) - gameTime;
        if (left <= 0L || left > BOLT_TICKS) return -1.0F;   // 停顿期间：枪机不动、手还在握把上
        return Mth.clamp(1.0F - left / (float) BOLT_TICKS, 0.0F, 1.0F);
    }

    /** 扣扳机动画窗口进度 0..1；没在窗口内返回 -1 */
    public static float fireWindow(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_FIRE_AT)) return -1.0F;
        long age = gameTime - tag.getLong(TAG_FIRE_AT);
        if (age < 0 || age > FIRE_TICKS) return -1.0F;
        return age / (float) FIRE_TICKS;
    }

    // ---------------------------------------------------------------- 逐发压弹
    /** 这次装填总共要多少 tick（由「要压几发」决定） */
    public static int loadTotal(int need) {
        return BOLT_OPEN_TICKS + LOAD_TICKS * Math.max(0, need) + BOLT_CLOSE_TICKS;
    }

    /** 正在逐发装填（开栓 / 压弹 / 关栓，全过程都算） */
    public static boolean loading(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_LOAD_AT)) return false;
        return gameTime - tag.getLong(TAG_LOAD_AT) < loadTotal(tag.getInt(TAG_LOAD_NEED));
    }

    /** 装填总进度 0..1；没在装填返回 -1（HUD、手臂动作、动画控制器都用它） */
    public static float reloadProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_LOAD_AT)) return -1.0F;
        long elapsed = gameTime - tag.getLong(TAG_LOAD_AT);
        int total = loadTotal(tag.getInt(TAG_LOAD_NEED));
        if (elapsed < 0L || elapsed >= total) return -1.0F;
        return Mth.clamp(elapsed / (float) total, 0.0F, 1.0F);
    }

    /**
     * 枪机**转栓**量 0..1（装填途中）：开栓阶段前 40% 转上去，关栓阶段后 40% 转回来；
     * 没在装填返回 0。
     */
    public static float loadBoltTurn(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_LOAD_AT)) return 0.0F;
        long elapsed = gameTime - tag.getLong(TAG_LOAD_AT);
        int need = tag.getInt(TAG_LOAD_NEED);
        int inserts = LOAD_TICKS * Math.max(0, need);
        if (elapsed < 0L) return 0.0F;
        if (elapsed < BOLT_OPEN_TICKS) {
            return ease(Mth.clamp(elapsed / (float) (BOLT_OPEN_TICKS * 0.4F), 0.0F, 1.0F));
        }
        if (elapsed < BOLT_OPEN_TICKS + inserts) return 1.0F;
        float q = (elapsed - BOLT_OPEN_TICKS - inserts) / (float) BOLT_CLOSE_TICKS;
        if (q >= 1.0F) return 0.0F;
        return 1.0F - ease(Mth.clamp((q - 0.55F) / 0.45F, 0.0F, 1.0F));
    }

    /** 枪机**后退**量 0..1（装填途中）：开栓阶段后 60% 拉到底，关栓阶段前 55% 推回去 */
    public static float loadBoltBack(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_LOAD_AT)) return 0.0F;
        long elapsed = gameTime - tag.getLong(TAG_LOAD_AT);
        int need = tag.getInt(TAG_LOAD_NEED);
        int inserts = LOAD_TICKS * Math.max(0, need);
        if (elapsed < 0L) return 0.0F;
        if (elapsed < BOLT_OPEN_TICKS) {
            float p = elapsed / (float) BOLT_OPEN_TICKS;
            return ease(Mth.clamp((p - 0.4F) / 0.6F, 0.0F, 1.0F));
        }
        if (elapsed < BOLT_OPEN_TICKS + inserts) return 1.0F;
        float q = (elapsed - BOLT_OPEN_TICKS - inserts) / (float) BOLT_CLOSE_TICKS;
        if (q >= 1.0F) return 0.0F;
        return 1.0F - ease(Mth.clamp(q / 0.55F, 0.0F, 1.0F));
    }

    /**
     * **当前这一发**的压入进度 0..1（模型里那一发子弹从机匣上方落下去的量、左手跟着下压的量）；
     * 不在「压弹」那一段（开栓 / 关栓 / 没装填）返回 -1。
     */
    public static float loadRoundProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_LOAD_AT)) return -1.0F;
        long elapsed = gameTime - tag.getLong(TAG_LOAD_AT);
        int need = tag.getInt(TAG_LOAD_NEED);
        if (need <= 0) return -1.0F;
        long e = elapsed - BOLT_OPEN_TICKS;
        if (e < 0L) return -1.0F;
        int index = (int) (e / LOAD_TICKS);
        if (index >= need) return -1.0F;
        return (e % LOAD_TICKS) / (float) LOAD_TICKS;
    }

    /** 这次装填要压进弹仓的第几发（0 起）；不在压弹段返回 -1 */
    public static int loadRoundIndex(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_LOAD_AT)) return -1;
        long e = (gameTime - tag.getLong(TAG_LOAD_AT)) - BOLT_OPEN_TICKS;
        if (e < 0L) return -1;
        int index = (int) (e / LOAD_TICKS);
        return index >= tag.getInt(TAG_LOAD_NEED) ? -1 : index;
    }

    private static float ease(float t) {
        float x = Mth.clamp(t, 0.0F, 1.0F);
        return x * x * (3.0F - 2.0F * x);
    }

    // ================================================================ 右键
    /** 右键：潜行时装/拆 4 倍镜；空仓先压弹；其余进入抵肩瞄准 */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.isShiftKeyDown() && hand == InteractionHand.MAIN_HAND) {
            InteractionResultHolder<ItemStack> swapped = swapSight(level, player, stack);
            if (swapped != null) return swapped;
        }
        long now = level.getGameTime();
        if (mag(stack) == 0 && !chambered(stack) && !loading(stack, now) && !bolting(stack, now)) {
            if (tryStartLoad(level, player, stack)) {
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

    /** 装/拆瞄具；返回 null 表示「这次右键不是装/拆」，交回给下游逻辑 */
    private InteractionResultHolder<ItemStack> swapSight(Level level, Player player, ItemStack stack) {
        ItemStack off = player.getOffhandItem();
        int want = Sights.fromItem(off.getItem());
        int has = sight(stack);
        if (!level.isClientSide) {
            if (want != Sights.IRON && want != has) {
                Sights.setExplicit(stack, want);
                if (!player.getAbilities().instabuild) off.shrink(1);
                player.displayClientMessage(Component.translatable("msg.hexalunar_calamity.sight_on",
                        Component.translatable(Sights.key(want))), true);
            } else if (want == Sights.IRON && has != Sights.IRON) {
                player.getInventory().placeItemBackInInventory(Sights.itemOf(has));
                Sights.setExplicit(stack, Sights.IRON);          // ★ 显式写机瞄，别掉回「默认带镜」
                player.displayClientMessage(Component.translatable("msg.hexalunar_calamity.sight_off"), true);
            } else {
                return null;
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.55F, 1.25F);
        }
        return InteractionResultHolder.success(stack);
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    /** 枪一律 {@code NONE}：{@code BOW} 会被原版套一段「拉弓」位移，枪会歪着斜、枪托被拉长 */
    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.NONE;
    }

    /** 装填结束就自动松手（不必一直按着右键），瞄准可继续按住 */
    @Override
    public void onUseTick(Level level, LivingEntity living, ItemStack stack, int remaining) {
        if (!(living instanceof Player player) || level.isClientSide) return;
        CompoundTag tag = stack.getTag();
        if (tag != null && tag.contains(TAG_LOAD_AT) && !loading(stack, level.getGameTime())) {
            player.releaseUsingItem();
        }
    }

    // ================================================================ 开火
    /** 左键（服务端）：栓动——必须膛内有弹；打完自动「拉栓 → 抽壳抛壳 → 再上膛」 */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        long now = level.getGameTime();
        if (loading(stack, now) || bolting(stack, now)) return;      // 装填 / 拉栓中不能击发
        if (!chambered(stack)) {
            // 空膛：弹仓里还有弹就拉一下栓上膛（没击发，不用等扣扳机的停顿），没弹就压弹 / 空响
            if (mag(stack) > 0) {
                startBolt(level, player, stack, 0);
            } else if (!tryStartLoad(level, player, stack) && !level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return;
        }
        boolean aiming = player.isUsingItem() && player.getUseItem() == stack;
        fire(level, player, stack, aiming);
        setChambered(stack, false);
        startBolt(level, player, stack, BOLT_DELAY);                // 先扣扳机，再自动拉栓抛壳
    }

    private void fire(Level level, Player player, ItemStack stack, boolean aiming) {
        stack.getOrCreateTag().putLong(TAG_FIRE_AT, level.getGameTime());

        // 栓动步枪：腰射散布很大，抵肩（机瞄 2 倍 / 4 倍镜）几乎指哪打哪
        float spread = aiming ? 0.07F : 1.20F;

        Vec3 muzzle = WeaponMount.mosin(player, aiming, sight(stack), WeaponMount.MOSIN_MUZZLE);
        Vec3 dir = WeaponMount.fireDir(player, level, muzzle, 8.0D, aiming ? 40.0D : 24.0D);

        BulletEntity bullet = new BulletEntity(level, player);
        bullet.setPos(muzzle.x, muzzle.y, muzzle.z);
        bullet.shoot(dir.x, dir.y, dir.z, BULLET_SPEED, spread);
        level.addFreshEntity(bullet);

        // 音效复用 AWP 的枪声（全曲目唯一的大口径枪声），音调略高一点
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AWP_SHOT.get(), SoundSource.PLAYERS, 1.2F,
                1.02F + level.random.nextFloat() * 0.06F);

        if (level instanceof ServerLevel server) {
            WeaponFx.muzzleFlash(server, muzzle, dir, aiming);
            WeaponFx.ejectCasing(server,
                    WeaponMount.mosin(player, aiming, sight(stack), WeaponMount.MOSIN_EJECT), dir);
        }
    }

    /**
     * 开始栓动：{@code delay} 帧后枪机后退（把空弹壳带出来抛掉），再推回闭锁并上膛。
     *
     * @param delay 先让右手留在握把上扣扳机的帧数；拉栓音效同样晚这么多帧响
     */
    private void startBolt(Level level, Player player, ItemStack stack, int delay) {
        if (level.isClientSide) return;
        stack.getOrCreateTag().putLong(TAG_BOLT_UNTIL, level.getGameTime() + delay + BOLT_TICKS);
        if (delay <= 0) {
            boltSound(level, player);
        } else {
            stack.getOrCreateTag().putLong(TAG_BOLT_SFX, level.getGameTime() + delay);
        }
    }

    /** 拉栓上膛音效（与 AKM / AWP / Kar98k 共用 `拉栓上膛.ogg`） */
    private static void boltSound(Level level, Player player) {
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.BOLT.get(), SoundSource.PLAYERS, 0.95F,
                0.94F + level.random.nextFloat() * 0.05F);
    }

    /** 拉栓结束：枪机把弹仓里下一发顶进弹膛（弹仓 −1、膛内 +1），没弹就空膛 */
    private void finishBolt(Level level, Player player, ItemStack stack) {
        if (mag(stack) > 0) {
            setMag(stack, mag(stack) - 1);
            setChambered(stack, true);
        } else {
            setChambered(stack, false);
        }
    }

    // ================================================================ 逐发压弹
    /**
     * R 键（服务端）：开始逐发压弹；**正在装填时再按一次 = 停下**（已压进去的留在弹仓里）。
     */
    @Override
    public void serverReload(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (level.isClientSide) return;
        long now = level.getGameTime();
        if (loading(stack, now)) {
            cancelLoad(level, player, stack, true);
            return;
        }
        if (bolting(stack, now)) return;
        if (mag(stack) >= MAG_SIZE && chambered(stack)) return;     // 弹仓满且膛内有弹
        if (!tryStartLoad(level, player, stack)) {
            player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
        }
    }

    private boolean tryStartLoad(Level level, Player player, ItemStack stack) {
        if (level.isClientSide) return true;
        int need = MAG_SIZE - mag(stack);
        if (need <= 0) return false;
        if (AmmoUtil.count(player, AmmoType.MOSIN) <= 0) return false;
        long now = level.getGameTime();
        CompoundTag tag = stack.getOrCreateTag();
        tag.putLong(TAG_LOAD_AT, now);
        // 只有「打完枪机还开着」时才顺便多带一发上膛，否则按需要几发压几发
        tag.putInt(TAG_LOAD_NEED, Math.min(need, AmmoUtil.count(player, AmmoType.MOSIN)));
        tag.putInt(TAG_LOAD_DONE, 0);
        // 开栓 + 掏子弹的动静（AWP 那条换弹音频正好是「手在枪上忙活」的声音）
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AWP_RELOAD.get(), SoundSource.PLAYERS, 0.85F,
                1.08F + level.random.nextFloat() * 0.06F);
        return true;
    }

    /** 每一发落进弹仓：消耗 1 发弹药 + 一声「咔」 */
    private void insertRound(Level level, Player player, ItemStack stack) {
        if (!AmmoUtil.consume(player, AmmoType.MOSIN, 1)) return;
        setMag(stack, mag(stack) + 1);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.32F,
                1.45F + level.random.nextFloat() * 0.08F);
    }

    /** 装填收尾：关栓 → 把弹仓里一发推进弹膛（弹仓 −1、膛内 +1） */
    private void finishLoad(Level level, Player player, ItemStack stack) {
        stack.getOrCreateTag().remove(TAG_LOAD_AT);
        stack.getOrCreateTag().remove(TAG_LOAD_NEED);
        stack.getOrCreateTag().remove(TAG_LOAD_DONE);
        if (mag(stack) > 0) {
            setMag(stack, mag(stack) - 1);
            setChambered(stack, true);
        }
        boltSound(level, player);                                   // 关栓闭锁那一声
    }

    /**
     * 中断装填：正在压的那一发按 TaCZ 的 {@code bullet_lost} 规则有概率掉地上。
     *
     * @param playSfx 是否补一声「关栓」音效（玩家主动按 R 停下时响，换物品离开时不响）
     */
    private void cancelLoad(Level level, Player player, ItemStack stack, boolean playSfx) {
        CompoundTag tag = stack.getTag();
        if (tag == null) return;
        float rp = loadRoundProgress(stack, level.getGameTime());
        if (rp >= BULLET_LOST_AT && level.random.nextFloat() < BULLET_LOST_CHANCE) {
            AmmoUtil.consume(player, AmmoType.MOSIN, 1);            // 那一发掉地上了
        }
        tag.remove(TAG_LOAD_AT);
        tag.remove(TAG_LOAD_NEED);
        tag.remove(TAG_LOAD_DONE);
        if (playSfx) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.5F, 1.1F);
        }
    }

    // ================================================================ tick
    @Override
    public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity,
                              int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (level.isClientSide || !(entity instanceof Player player)) return;
        CompoundTag tag = stack.getTag();
        if (tag == null) return;
        long now = level.getGameTime();

        // ---- 逐发压弹：每压完一发就消耗一发弹药（掉帧时用 while 补齐） ----
        if (tag.contains(TAG_LOAD_AT)) {
            if (!selected) {
                cancelLoad(level, player, stack, false);            // 换走了 = 停下
            } else {
                long elapsed = now - tag.getLong(TAG_LOAD_AT);
                int need = tag.getInt(TAG_LOAD_NEED);
                if (elapsed >= loadTotal(need)) {
                    finishLoad(level, player, stack);
                } else {
                    int should = Mth.clamp((int) ((elapsed - BOLT_OPEN_TICKS) / LOAD_TICKS),
                            0, need);
                    int done = tag.getInt(TAG_LOAD_DONE);
                    while (done < should) {
                        insertRound(level, player, stack);
                        done++;
                        tag.putInt(TAG_LOAD_DONE, done);
                        if (mag(stack) >= MAG_SIZE) {                   // 弹仓满了就提前收尾
                            finishLoad(level, player, stack);
                            return;
                        }
                    }
                }
            }
        }

        if (tag.contains(TAG_BOLT_UNTIL) && tag.getLong(TAG_BOLT_UNTIL) <= now) {
            tag.remove(TAG_BOLT_UNTIL);
            finishBolt(level, player, stack);
        }
        // 拉栓音效的定时（比枪声晚 BOLT_DELAY 帧）
        if (tag.contains(TAG_BOLT_SFX) && tag.getLong(TAG_BOLT_SFX) <= now) {
            tag.remove(TAG_BOLT_SFX);
            boltSound(level, player);
        }
    }

    // ================================================================ 提示
    @Override
    public void appendHoverText(ItemStack stack, Level level, List<Component> tips, TooltipFlag flag) {
        tips.add(Component.translatable("tooltip.hexalunar_calamity.mosin_controls")
                .withStyle(ChatFormatting.GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.range_hint",
                (int) Ballistics.MOSIN_RANGE).withStyle(ChatFormatting.DARK_GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.mosin_ammo",
                mag(stack), MAG_SIZE, chambered(stack) ? 1 : 0).withStyle(ChatFormatting.DARK_GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.mosin_sight",
                Component.translatable(Sights.key(sight(stack)))).withStyle(ChatFormatting.DARK_GRAY));
    }
}
