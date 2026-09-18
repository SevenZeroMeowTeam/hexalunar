package cn.blockforge.generated.hexalunarcalamity.moon;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.DoubleArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * 月灾管理指令（OP 2 级 / 单人开作弊）：
 *
 * <pre>
 * /hexalunar moon set &lt;blood_moon|...|none&gt;   强制指定月相（今夜不再掷骰）
 * /hexalunar moon clear                        清除月相 = 今夜无月
 * /hexalunar moon random                       立刻按随机规则掷一次
 * /hexalunar moon info                          查看状态（夜数 / 月相 / 概率 / 连旱 / 尸潮）
 * /hexalunar moon list                          列出全部月相 id
 * /hexalunar moon chance &lt;0~1&gt;                  设置每晚出月相的概率
 * /hexalunar horde start | stop | wave &lt;n&gt;      手动开关尸潮 / 单放某一波
 * /hexalunar barrage                            立刻触发巨箭弹幕
 * </pre>
 *
 * <p>`/hlc` 是同一棵指令树的简写别名。
 */
@Mod.EventBusSubscriber
public final class MoonCommands {

    /** 权限等级：2 = OP / 单人开启作弊 */
    private static final int PERMISSION = 2;

    @SubscribeEvent
    public static void onRegisterCommands(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> dispatcher = event.getDispatcher();
        dispatcher.register(tree("hexalunar"));
        dispatcher.register(tree("hlc"));
    }

    private static LiteralArgumentBuilder<CommandSourceStack> tree(String root) {
        return Commands.literal(root)
                .requires(src -> src.hasPermission(PERMISSION))
                .then(Commands.literal("moon")
                        .then(Commands.literal("set")
                                .then(Commands.argument("phase", StringArgumentType.word())
                                        .suggests((ctx, builder) -> SharedSuggestionProvider.suggest(
                                                phaseIds(), builder))
                                        .executes(ctx -> setMoon(ctx.getSource(),
                                                StringArgumentType.getString(ctx, "phase")))))
                        .then(Commands.literal("clear")
                                .executes(ctx -> setMoon(ctx.getSource(), "none")))
                        .then(Commands.literal("random")
                                .executes(ctx -> rollMoon(ctx.getSource())))
                        .then(Commands.literal("info")
                                .executes(ctx -> info(ctx.getSource())))
                        .then(Commands.literal("list")
                                .executes(ctx -> list(ctx.getSource())))
                        .then(Commands.literal("chance")
                                .then(Commands.argument("value", DoubleArgumentType.doubleArg(0.0D, 1.0D))
                                        .executes(ctx -> setChance(ctx.getSource(),
                                                DoubleArgumentType.getDouble(ctx, "value"))))))
                .then(Commands.literal("horde")
                        .then(Commands.literal("start")
                                .executes(ctx -> startHorde(ctx.getSource())))
                        .then(Commands.literal("stop")
                                .executes(ctx -> stopHorde(ctx.getSource())))
                        .then(Commands.literal("wave")
                                .then(Commands.argument("wave",
                                                IntegerArgumentType.integer(1, MoonManager.HORDE_WAVES))
                                        .executes(ctx -> wave(ctx.getSource(),
                                                IntegerArgumentType.getInteger(ctx, "wave"))))))
                .then(Commands.literal("barrage")
                        .executes(ctx -> barrage(ctx.getSource())));
    }

    /* ------------------------------------------------------------------ 子命令 */

    private static int setMoon(CommandSourceStack src, String id) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        if ("none".equalsIgnoreCase(id) || "clear".equalsIgnoreCase(id)) {
            MoonManager.commandSetPhase(level, null);
            src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.cleared")
                    .withStyle(ChatFormatting.GRAY), true);
            return 1;
        }
        MoonPhase phase = MoonPhase.byId(id);
        if (phase == null) {
            src.sendFailure(msg("command.hexalunar_calamity.moon.unknown", id));
            return 0;
        }
        MoonManager.commandSetPhase(level, phase);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.set", name(phase))
                .withStyle(ChatFormatting.GOLD), true);
        return 1;
    }

    private static int rollMoon(CommandSourceStack src) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        MoonPhase phase = MoonManager.commandRollPhase(level);
        if (phase == null) {
            src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.rolled_none")
                    .withStyle(ChatFormatting.GRAY), true);
        } else {
            src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.rolled", name(phase))
                    .withStyle(ChatFormatting.LIGHT_PURPLE), true);
        }
        return 1;
    }

    private static int info(CommandSourceStack src) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        MoonPhaseData data = MoonManager.get(level);
        MoonPhase phase = data.phase();
        boolean night = level.isNight();
        int chancePct = Math.round(MoonManager.effectiveChance(data) * 100.0F);
        Component phaseText = phase == null
                ? msg("command.hexalunar_calamity.moon.none")
                : name(phase);
        Component timeText = msg(night
                ? "command.hexalunar_calamity.time.night"
                : "command.hexalunar_calamity.time.day");
        Component hordeText = data.hordeActive
                ? msg("command.hexalunar_calamity.horde.state_active", data.hordeWave)
                : msg("command.hexalunar_calamity.horde.state_idle");

        src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.info1",
                data.nightCount, timeText, phaseText).withStyle(ChatFormatting.AQUA), false);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.info2",
                chancePct + "%", data.dryNights).withStyle(ChatFormatting.GRAY), false);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.info3", hordeText)
                .withStyle(ChatFormatting.GRAY), false);
        return 1;
    }

    private static int list(CommandSourceStack src) {
        src.sendSuccess(() -> msg("command.hexalunar_calamity.moon.list",
                String.join("  ", phaseIds())).withStyle(ChatFormatting.GRAY), false);
        return 1;
    }

    private static int setChance(CommandSourceStack src, double value) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        MoonPhaseData data = MoonManager.get(level);
        data.moonChance = (float) value;
        data.setDirty();
        int pct = (int) Math.round(value * 100.0D);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.chance.set", pct + "%")
                .withStyle(ChatFormatting.GOLD), true);
        return 1;
    }

    private static int startHorde(CommandSourceStack src) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        MoonManager.commandStartHorde(level);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.horde.started")
                .withStyle(ChatFormatting.DARK_RED), true);
        return 1;
    }

    private static int stopHorde(CommandSourceStack src) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        MoonManager.commandStopHorde(level);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.horde.stopped")
                .withStyle(ChatFormatting.GREEN), true);
        return 1;
    }

    private static int wave(CommandSourceStack src, int n) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        MoonManager.commandWave(level, n);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.horde.wave", n)
                .withStyle(ChatFormatting.RED), true);
        return 1;
    }

    private static int barrage(CommandSourceStack src) {
        ServerLevel level = targetLevel(src);
        if (level == null) return 0;
        MoonManager.commandBarrage(level);
        src.sendSuccess(() -> msg("command.hexalunar_calamity.barrage")
                .withStyle(ChatFormatting.GOLD), true);
        return 1;
    }

    /* ------------------------------------------------------------------ 工具 */

    /**
     * 月相只在主世界推进 ⇒ 指令一律作用到主世界。
     *
     * <p>★ 方法名别叫 `level`：调用处写 `ServerLevel level = level(src);` 时，
     * 局部变量的作用域从声明处就开始了，会遮住同名方法 ⇒ javac 报「找不到符号」。
     */
    @Nullable
    private static ServerLevel targetLevel(CommandSourceStack src) {
        return src.getServer().overworld();
    }

    private static List<String> phaseIds() {
        List<String> ids = new ArrayList<>(MoonPhase.ORDER.length + 1);
        for (MoonPhase phase : MoonPhase.ORDER) {
            ids.add(phase.id);
        }
        ids.add("none");
        return ids;
    }

    private static Component name(MoonPhase phase) {
        return Component.translatable("moon.title." + phase.id);
    }

    /** ★ 必须返回 MutableComponent：`Component` 接口没有 withStyle()，返回它就没法上色 */
    private static net.minecraft.network.chat.MutableComponent msg(String key, Object... args) {
        return Component.translatable(key, args);
    }

    private MoonCommands() {
    }
}
