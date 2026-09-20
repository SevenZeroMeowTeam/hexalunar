package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.FlashbangItem;
import cn.blockforge.generated.hexalunarcalamity.item.FragGrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil;
import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

import java.util.EnumMap;
import java.util.Map;
import java.util.Random;

/**
 * 手持物品的「动作」状态机（纯客户端、纯程序化）。
 *
 * <p>参考 SuperbWarfare 那类枪械模组的表现：枪会随开火后坐、举枪有过渡、换弹有整套起伏、
 * 手雷拔销时手腕要用力。区别是它的模型是 GeckoLib 骨骼动画，我们的是静态 OBJ，
 * 所以这里用的是<b>程序化变换</b>：把动作折算成 display 的 rotation / translation 增量，
 * 由 {@link WeaponPose} 在渲染时叠加（详见 {@link AnimatedWeaponModel}）。
 *
 * <p>所有冲量都按「每 tick 乘一个衰减系数」的方式回弹，不需要复杂的曲线：
 * <pre>
 *   recoil  开火瞬间 +0.55，之后每 tick ×0.55
 *   aim     举枪/开镜用 0.3/tick 逼近目标值
 *   draw    按蓄力 tick 直接映射 0..1
 *   pin     拔销进度直接取 GrenadeItem 的状态
 * </pre>
 */
public final class WeaponAnim {

    /**
     * 有动作的武器种类（★ r105：追加 {@code KAR98K}；★ r106：追加 {@code MOSIN}；
     * ★ r108：追加 {@code M1_GARAND} —— **只能往后加**，中间插值会打乱所有武器的状态）
     */
    public enum Kind { AKM, AWP, CROSSBOW, BOW, GRENADE, FLASH, KAR98K, MOSIN, M1_GARAND }

    /** 每种武器一份运行时状态（同一时刻只有手上那把在推进，其余衰减归零） */
    public static final class State {
        /** 后坐冲量 */
        public float recoil;
        /** 后坐带来的随机偏航 -1..1 */
        public float recoilYaw;
        /** 举枪 / 开镜过渡 0..1 */
        public float aim;
        /** 拉弦 0..1 */
        public float draw;
        /** 放箭回弹 0..1 */
        public float release;
        /** 拔销 / 插销进度 0..1 */
        public float pin;
        /** 投掷甩手 0..1 */
        public float throwKick;
        /** 换弹 / 上弦进度 0..1，< 0 表示没在进行 */
        public float reload = -1.0F;
        /** 弩是否已挂弦（箭在槽里）；给渲染层拼弩箭用 */
        public boolean loaded;
        /** 上一 tick 是否在使用（用来检测「放箭」那一刻） */
        public boolean wasUsing;
        /** 松手时的蓄力，决定放箭回弹多猛 */
        public float lastCharge;
        /**
         * ★ Q 弹版：果冻弹簧（开火时打冲量 ⇒ 枪像果冻一样挤压拉伸 + 上下弹一下）。
         * 非 Q 版里没人读它（javac 会把 Q 分支折叠掉），所以留着不影响普通版。
         */
        public final Jelly jelly = new Jelly();
    }

    private static final Map<Kind, State> STATES = new EnumMap<>(Kind.class);
    private static final Random RNG = new Random();

    static {
        for (Kind kind : Kind.values()) {
            STATES.put(kind, new State());
        }
    }

    public static State of(Kind kind) {
        return STATES.get(kind);
    }

    /** 状态是否「安静」——安静时不做任何变换，避免平白多算矩阵 */
    public static boolean isIdle(State st) {
        return st.recoil < 0.002F && Math.abs(st.recoilYaw) < 0.002F && st.aim < 0.002F
                && st.draw < 0.002F && st.release < 0.002F && st.pin < 0.002F
                && st.throwKick < 0.002F && st.reload < 0.0F;
    }

    @Nullable
    public static Kind kindOf(ItemStack stack) {
        if (stack == null || stack.isEmpty()) return null;
        Item item = stack.getItem();
        if (item instanceof AkmRifleItem) return Kind.AKM;
        if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem) {
            return Kind.AWP;
        }
        if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon.Kar98kItem) {
            return Kind.KAR98K;
        }
        if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem) {
            return Kind.MOSIN;                      // ★ r106
        }
        if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon.M1GarandItem) {
            return Kind.M1_GARAND;                  // ★ r108
        }
        if (item instanceof CrossbowWeaponItem) return Kind.CROSSBOW;
        if (item instanceof CompoundBowItem) return Kind.BOW;
        if (item instanceof FragGrenadeItem) return Kind.GRENADE;
        if (item instanceof FlashbangItem) return Kind.FLASH;
        return null;
    }

    /** 手上正在动作的那把（主手武器优先，其次副手手雷） */
    @Nullable
    public static Kind heldKind(Player player) {
        if (player == null) return null;
        ItemStack weapon = AmmoUtil.heldWeapon(player);
        if (weapon != null) return kindOf(weapon);
        ItemStack grenade = GrenadeItem.heldGrenade(player);
        if (grenade != null) return kindOf(grenade);
        return null;
    }

    /** 开火：后坐冲量 + 一点随机偏航（连发时会累积成枪口上扬） */
    public static void onFire(ItemStack stack, boolean aiming) {
        Kind kind = kindOf(stack);
        if (kind == null) return;
        State st = of(kind);
        float impulse = aiming ? 0.42F : 0.6F;
        st.recoil = Math.min(1.5F, st.recoil + impulse);
        st.recoilYaw = Mth.clamp(st.recoilYaw + (RNG.nextFloat() - 0.5F) * (aiming ? 0.5F : 0.9F), -1.0F, 1.0F);
        // ★ Q 弹版：开火打一个果冻冲量（抵肩时小一点，免得开镜晃得看不清）
        if (cn.blockforge.generated.hexalunarcalamity.BuildInfo.Q_MODE) {
            st.jelly.punch(aiming ? 0.55F : 0.85F);
        }
    }

    /** 手雷出手：甩手动作 */
    public static void onThrow() {
        for (Kind kind : new Kind[]{Kind.GRENADE, Kind.FLASH}) {
            of(kind).throwKick = 1.0F;
            of(kind).pin = 0.0F;
        }
    }

    /** 每客户端 tick 推进所有状态 */
    public static void tick(Minecraft mc) {
        Player player = mc.player;
        ItemStack held = ItemStack.EMPTY;
        Kind heldKind = null;
        if (player != null) {
            ItemStack weapon = AmmoUtil.heldWeapon(player);
            if (weapon != null) {
                held = weapon;
            } else {
                ItemStack grenade = GrenadeItem.heldGrenade(player);
                if (grenade != null) held = grenade;
            }
            heldKind = kindOf(held);
        }

        for (Map.Entry<Kind, State> entry : STATES.entrySet()) {
            Kind kind = entry.getKey();
            State st = entry.getValue();

            // ---- 冲量衰减（所有种类通用）----
            st.recoil *= 0.55F;
            st.recoilYaw *= 0.5F;
            st.release *= 0.5F;
            // ★ Q 弹版：果冻弹簧（衰减慢一点、相位匀速 ⇒ 能看见「弹回去」那一下）
            if (cn.blockforge.generated.hexalunarcalamity.BuildInfo.Q_MODE) {
                st.jelly.tick(0.82F, 1.15F);
            }
            st.throwKick *= 0.45F;

            boolean active = kind == heldKind && player != null;
            if (!active) {
                st.aim = approach(st.aim, 0.0F, 0.3F);
                st.draw = approach(st.draw, 0.0F, 0.35F);
                st.pin = 0.0F;
                st.reload = -1.0F;
                st.loaded = false;
                st.wasUsing = false;
                st.lastCharge = 0.0F;
                continue;
            }

            boolean using = player.isUsingItem() && player.getUseItem() == held;
            long gameTime = player.level() == null ? 0L : player.level().getGameTime();

            switch (kind) {
                case AKM -> {
                    st.aim = approach(st.aim, using ? 1.0F : 0.0F, 0.3F);
                    st.reload = AkmRifleItem.reloadProgress(held, gameTime);
                    st.wasUsing = using;
                }
                case AWP, KAR98K -> {
                    // ★★ r84：AWP 这个 case 以前**漏了** ⇒ {@code Kind.AWP.aim} 永远是 0，
                    //   「抵肩举枪（镜筒光轴顶到屏幕中心）」的姿态从来没生效过（以前开镜是整屏遮罩、
                    //   枪还藏着，所以看不出来）。现在开镜看得见枪了，一按右键枪必须抬到屏幕中央。
                    //   ★ r105：Kar98k 与 AWP 走同一套（举枪位移 + 开火俯仰），共用这一支。
                    st.aim = approach(st.aim, using ? 1.0F : 0.0F, 0.3F);
                    st.wasUsing = using;
                }
                case MOSIN -> {
                    // ★ r106 莫辛：与 AWP / Kar98k 同一套举枪位移（只平移）；
                    //   reload 那一路给的是**逐发压弹的总进度**（>0 = 正在压弹），给流光层/手臂用
                    st.aim = approach(st.aim, using ? 1.0F : 0.0F, 0.3F);
                    st.reload = cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem
                            .reloadProgress(held, gameTime);
                    st.wasUsing = using;
                }
                case M1_GARAND -> {
                    // ★ r108 M1 加兰德：机瞄⇒举枪位移只平移（TaCZ 步枪那一套）；
                    //   reload 给的是**压漏夹 + 枪机释放**的总进度（>0 = 正在换弹）
                    st.aim = approach(st.aim, using ? 1.0F : 0.0F, 0.3F);
                    st.reload = cn.blockforge.generated.hexalunarcalamity.weapon.M1GarandItem
                            .reloadProgress(held, gameTime);
                    st.wasUsing = using;
                }
                case CROSSBOW -> {
                    st.aim = approach(st.aim, using ? 1.0F : 0.0F, 0.35F);
                    // 上弦（装填）：进度喂给模型覆盖属性与分件动画
                    st.reload = CrossbowWeaponItem.reloadProgress(held, gameTime);
                    st.loaded = CrossbowWeaponItem.cocked(held);
                    st.wasUsing = using;
                }
                case BOW -> {
                    float charge = using
                            ? CompoundBowItem.pullProgress(player.getUseItemRemainingTicks()) : 0.0F;
                    st.draw = approach(st.draw, using ? charge : 0.0F, 0.4F);
                    // 松手那一刻：蓄得越满回弹越猛
                    if (st.wasUsing && !using) {
                        st.release = 0.6F + 0.4F * st.lastCharge;
                    }
                    if (using) st.lastCharge = charge;
                    st.wasUsing = using;
                }
                case GRENADE, FLASH -> {
                    int state = GrenadeItem.state(held);
                    float progress = GrenadeItem.progress(held);
                    st.pin = switch (state) {
                        case GrenadeItem.STATE_PULLING -> Mth.clamp(progress, 0.0F, 1.0F);
                        case GrenadeItem.STATE_ARMED -> 1.0F;
                        case GrenadeItem.STATE_REINSERTING -> Mth.clamp(1.0F - progress, 0.0F, 1.0F);
                        default -> 0.0F;
                    };
                    st.wasUsing = false;
                }
                default -> {
                }
            }
        }
    }

    private static float approach(float current, float target, float step) {
        if (current < target) return Math.min(target, current + step);
        if (current > target) return Math.max(target, current - step);
        return current;
    }

    private WeaponAnim() {}
}
