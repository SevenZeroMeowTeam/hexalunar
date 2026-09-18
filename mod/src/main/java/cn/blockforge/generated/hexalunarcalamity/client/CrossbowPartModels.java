package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.client.event.ModelEvent;
import org.jetbrains.annotations.Nullable;

import java.util.Map;

/**
 * 十字弩分件模型（弩箭 / 左手）的注册与缓存。
 *
 * <p>本体（{@code models/item/crossbow.obj}）现在只含弩身；弩箭与「拉弦的左手」拆成了
 * 独立 OBJ，由 {@link CrossbowPartAnim} 在渲染时按上弦进度给顶点加位移，再拼到本体上：
 * <ul>
 *   <li><b>弩箭</b>：上弦后半段从后方滑进箭槽，弦挂好后一直留在槽里，击发后才消失</li>
 *   <li><b>左手</b>：只在第一人称、且没在举弩（举弩时原版会画手臂）时出现，
 *       跟着弦的中点从静止位置一路拉到弦爪上，拉完松手撤走</li>
 * </ul>
 *
 * <p>这两个模型没有任何物品引用，必须用 Forge 的 {@link ModelEvent.RegisterAdditional}
 * 显式登记，否则烘焙阶段不会加载。
 */
public final class CrossbowPartModels {

    private static final org.slf4j.Logger LOGGER =
            org.slf4j.LoggerFactory.getLogger(HexaLunarCalamity.MOD_ID);

    public static final ResourceLocation BOLT_ID =
            ResourceLocation.fromNamespaceAndPath(HexaLunarCalamity.MOD_ID, "item/crossbow_bolt_part");
    public static final ResourceLocation HAND_ID =
            ResourceLocation.fromNamespaceAndPath(HexaLunarCalamity.MOD_ID, "item/crossbow_hand_part");

    @Nullable
    private static BakedModel bolt;
    @Nullable
    private static BakedModel hand;

    private CrossbowPartModels() {
    }

    /** 让烘焙阶段把分件也加载进来（模组总线事件） */
    public static void registerAdditional(ModelEvent.RegisterAdditional event) {
        event.register(BOLT_ID);
        event.register(HAND_ID);
    }

    /** 烘焙完成后抓取分件模型（键可能是 {@code ...#standalone} / {@code ...#inventory}，只比对路径） */
    public static void capture(Map<ResourceLocation, BakedModel> models) {
        BakedModel boltFound = null;
        BakedModel handFound = null;
        for (Map.Entry<ResourceLocation, BakedModel> entry : models.entrySet()) {
            ResourceLocation id = entry.getKey();
            if (!HexaLunarCalamity.MOD_ID.equals(id.getNamespace())) continue;
            String path = id.getPath();
            if (path.contains("crossbow_bolt_part")) {
                if (boltFound == null) boltFound = entry.getValue();
            } else if (path.contains("crossbow_hand_part")) {
                if (handFound == null) handFound = entry.getValue();
            }
        }
        bolt = boltFound;
        hand = handFound;
        CrossbowPartAnim.invalidate();
        if (boltFound == null || handFound == null) {
            LOGGER.warn("十字弩分件没找全（弩箭={} 左手={}），上弦动画会退回只有弦/弓臂的动作",
                    boltFound != null, handFound != null);
        } else {
            LOGGER.info("十字弩分件已就绪：弩箭 + 左手");
        }
    }

    @Nullable
    public static BakedModel bolt() {
        return bolt;
    }

    @Nullable
    public static BakedModel hand() {
        return hand;
    }
}
