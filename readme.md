# 六相月灾 · Hexa Lunar Calamity

[![build](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml/badge.svg)](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml)

Minecraft **1.20.1 / Forge 47.4.x** 的月相灾变 + 现代射击玩法模组。
月相会改变夜晚的威胁强度，玩家则用枪械、弩弓与投掷物应对尸潮。

- 模组 ID：`hexalunar_calamity`｜版本：`1.0.0-r113`
- 武器模型：**GeckoLib 4.8.4 骨骼模型**（`geo/*.geo.json` + `animations/*.animation.json`，可在 Blockbench 里直接改）
- 创造模式页签：**六相月灾**

---

## 一、构建与部署

| 项目 | 说明 |
|---|---|
| 需要 | JDK **17**、**Gradle 8.14.5** |
| 依赖 | **GeckoLib 4.8.4**（`software.bernie.geckolib:geckolib-forge-1.20.1:4.8.4`，由 Gradle 自动拉取） |
| ⚠️ 重要 | ForgeGradle `[6.0,6.2)` **不支持 Gradle 9.x**，必须用 8.x |
| 产物 | `mod/build/libs/hexalunar_calamity-1.0.0-r113.jar` |
| 部署 | 复制到 `%APPDATA%\.minecraft\versions\1.20.1-Forge_47.4.23-2\mods\` |
| ⚠️ 运行前置 | **GeckoLib 4.8.4** 必须与 jar 一起放进 `mods/`（武器骨骼模型靠它渲染，缺了直接加载失败） |

`.vscode/tasks.json` 里已配好两个任务（含 Java 报错问题匹配器）：

| 任务 | 作用 |
|---|---|
| `mc_check` | `gradle compileJava` — 只做类型检查，不打包 |
| `mc_build` | `gradle build` + **自动复制 jar 到 mods 目录** |

> 仓库已带 Gradle Wrapper（固定 **8.14.5**）：CI 与本地都可以直接用 `mod\gradlew.bat build`（Linux/macOS 用 `./gradlew`）。
> 推送到 GitHub 后由 `.github/workflows/build.yml` 自动编译并上传 jar 产物；
> 若 `mod/build.gradle` 里的版本号还没有对应 tag，还会**自动打 `v1.0.0-rXX` 标签并创建 Release（附 jar）**。

手动执行等价命令：

```powershell
$env:JAVA_HOME='C:\Users\Administrator\.jdks\temurin-17'
& <gradle-8.14.5>\bin\gradle.bat build --console=plain
```

> VS Code 的 Java 语言服务器没有本工程的 Forge 类路径（会把 `net.minecraftforge.*` 全标红），
> **判断真假以 `gradle compileJava` 的输出为准**。

---

## 二、玩法

### 通用操作

| 输入 | 行为 |
|---|---|
| 右键按住 | 瞄准（各武器行为不同） |
| 左键 | 开火 / 投掷（按住连发由武器决定） |
| `R` | 换弹（AKM / **AWP 换弹匣** / 十字弩上弦，默认键位，可在设置里改）· **手里有已拔销 / 引信在烧的手雷时 = 紧急投掷**（立刻按准星丢出）|
| 右键按住（手雷 / 震爆弹） | **拔保险销**（1 秒）；拔销后**必须一直按住**（松手 / **切武器** 就点火）；销已拔出时可 **潜行 + 右键 1 秒** 插回销 |
| 潜行 + 右键 | **装/拆 AKM 顶部导轨上的瞄具**：副手拿着瞄具 = 装上（消耗一个），空着 = 拆下还给你 |

### 武器

| 武器 | 弹药 | 特性 |
|---|---|---|
| **AKM 突击步枪** | 7.62×39mm | **子弹 10 点伤害**（5 颗心）· 30 发弹匣 · 全自动（2 tick/发）· 后坐力累积影响散布 · 瞄准收紧散布 · **抛壳口会真抛黄铜空弹壳**（含硝烟）+ 枪口焰 · **顶部导轨**（可装红点/4 倍镜）· 退弹匣→上匣→拉栓的换弹动画 · **有效射程 60 格**（射程内平直，超出后下坠） |
| **战术十字弩** | 弩箭 | 弹匣供弹 · 按住连发 · **4 倍镜**：右键开镜时视野 ×1/4、圆形镜筒遮罩 + 十字分划，并自动隐藏手部模型 · 拉弦/装填箭矢为骨骼动画 · **拉弦时弓臂向内收缩**（r63，见下）· **上弦后弦贴回两弓臂之间**（不往后拉，见下）· **有效射程 40 格** |

> **十字弩外形（r61）**：换成参考网格 `模型/十字弩_v2.bbmodel` 那把**现代复合弩**（窄弓臂 + 高导轨 + 枪式握把 + 镜筒 + 线缆），
> 由 `tools/crossbow_vox.py` **表面体素化**成 824 个方块（逐格从原 512² 贴图采样 UV）。
> 骨骼名 / 握把原点 / 显示缩放都保持原样，所以武器动画、手部锚点不用重写。
| **AWP 栓动狙击枪**（r79 新增，**r114 用 `tools/awp_v2.py` 重建模型 + 动作照 TaCZ `ai_awp`**） | .338 狙击弹 | **单发 24 点伤害**（12 颗心，一枪基本带走）· **5 发弹匣 + 膛内 1 发**· 栓动（必须膛内有弹才能击发）· **每发后自动拉栓抛壳**（照 TaCZ `ai_awp`：拉机柄抬 **62°**、枪机后退 **1.90px**、**整枪向右侧倾 11.9° + 微抬 4.6°**、弹壳三轴翻滚抛向射手右侧，约 1.4 s 一发）· **8 倍镜**（右键抵肩）· 腰射散布大、抵肩几乎指哪打哪 · **有效射程 96 格**（射程内重力 0.004，比步枪弹更平）· **v2 模型 18 骨骼 / 180 方块**：**一整根八棱空洞枪管**（外 0.250 / 内孔 0.125 + 内壁膛线 + 八棱制退器两道泄气槽）· **空心镜筒 + 整片透明圆镜片（十字分划 + 中心点）**· **弹匣里 5 发看得见的子弹**（拉栓时托弹板顶到弹匣口 → 枪机推进膛 → 闭锁后看不见）· **持枪动画照 TaCZ 通用步枪 `rifle_default`**（idle 呼吸 / 走路摆动 / 冲刺时枪压低转到身侧）· 换弹时弹匣 **45° 翻转脱出** · 第一人称**双手：右手握把/拉栓、左手托护木** |
| **Kar98k 栓动步枪**（r105 新增，r107 改装填/弹药/伤害） | **7.62×59mm**（`ammo_762_59`，与莫辛-纳甘**共用同一发**；与 7.62×39、.338 都不通用） | **独立模型**：木托长枪 + 下弯拉机柄 + 自带 **4 倍镜筒**（`tools/kar98k_gen.py` 生成）· **单发 50 点伤害**（25 颗心，**爆头 ×1.85**）· 初速 5.7 · **5 发内置弹仓 + 膛内 1 发** · **一次击发一发**：每发后自动拉栓**带出弹壳抛掉**（拉机柄抬 **64°**——下弯柄再大就捅进镜筒、枪机后退 2.6px）· **`R` = 用手一发一发压进弹仓**（开栓 15 tick → 每发 12 tick → 关栓上膛 16 tick；模型里那一发从机匣上方落进弹仓、左手跟着往下按；被打断的那一发 30% 概率掉地）· **4 倍镜**：抵肩走 **AWP 那套整屏镜筒遮罩**（世界变焦 1/4）· 目前**只能创造页签取用**（还没进探险箱掉落/配方） |
| **莫辛-纳甘 M91/30 栓动步枪**（r106 新增） | **7.62×59mm**（`ammo_762_59`，与 7.62×39、.338 **都不通用**） | 右键抵肩（自带 4 倍镜）/ 左键击发 / `R` 逐发压弹 · **有效射程 84 格**（射程内重力 0.005）· **单发 26 点伤害**（13 颗心，**爆头 ×1.85**）· 初速 5.4 · **5 发固定弹仓**（无弹匣）：`R` = 开栓 15 tick → **每发 12 tick 一发一发压进弹仓** → 关栓上膛 16 tick；被打断的那一发有 30% 概率掉地（TaCZ `bullet_lost = 0.3`）· **拉栓自动「抽壳 → 抛壳 → 推下一发上膛」**（18 tick ≈ 0.85 s）· **出厂自带 4 倍镜**（整屏镜筒遮罩 + 世界变焦 1/4；拆掉镜筒就是**机瞄 ×2**）· 木托 + 发蓝钢 + 顶部导轨，**枪管加长**（整枪 22.4 模型像素 = 1.40 格）· **独立模型** `tools/mosin_gen.py` → 14 骨骼 / 97 方块 · **数值整套套用 TaCZ 的 Kar98k 配置** |
| **M1 加兰德半自动步枪**（r108 新增，**r112 重建模型，r113 改平行抬盖**） | **7.62×61mm**（`ammo_762_61`，与 7.62×39 / 7.62×59 / .338 **都不通用**） | **连射**（按住左键每 10 tick 一发；`tools/m1_garand_v2.py` 生成：**空心圆管枪管** + **空心觇孔环（透明玻璃十字线）** + **8 发可见漏夹**，**没有外露弹匣 / 拉机柄 / 导气杆**）· **单发 22 点伤害**（11 颗心，**爆头 ×1.5**）· 初速 5.15 · **8 发漏夹 + 膛内 1 发**（`R` = 右手把漏夹压进机匣 → 枪机释放一次上膛，**一个漏夹只拉一次栓**）· **每发自动「枪机后退 → 抛壳（射手右侧）→ 复进顶下一发」**（8 tick，不用自己拉栓）· **弹夹盖每发平行抬起一下、装填完成自动落回合上、打空不合上**（r113）· 打空最后一发**整只漏夹弹出「叮」一声** · **只有机瞄**（抵肩走 AKM 那套轻机瞄，视野 1/3）· 有效射程 72 格（射程内重力 0.0055）· **持枪参数照 TaCZ 步枪**（`zoom_model_fov = 45` / `iron_zoom = 1.33`） |
| **复合弓** | 复合弓箭 / 尸毒箭 | 右键蓄力（20 tick 满蓄），**三段拉弦动画**（0.65 / 0.9 蓄力切换模型）· 蓄力越高穿透与伤害越强 · 没普通箭时自动改用尸毒箭 · **有效射程 34 格** |

> **十字弩的弦（r60）**：上弦（已装填）后弦**不往后拉**，直接贴回两弓臂之间 ——
> 拉回去的弦心比弓臂梢**离镜头近 0.17 格**，透视放大后会像一根「∧」浮在弩上方（用户要求看不见）。
> 拉弦动作本身照旧（装填期间 `draw` 0→1，能看到弦被拉回），一上弦就弹回弓臂前面。
> 实现在 `client/CrossbowGeoModel.java`（`draw = cocked ? 0 : p/0.65`）。

> **十字弩的弓臂（r63~r65）**：拉弦时两弓臂**向内收 + 往射手方向后弯** ——
> 绕「贴导轨的内端」向内转 **8°**，同时整根弓臂**后滑 0.35**（只靠转的话外端主要只往内走，看着像贴在弩身上）：
> 外端实测**向内 0.51 + 向后 0.77**（模型像素）。
> **弓臂本身在 r65 被拉长加粗了一轮**（生成器 `LIMB_SX = 1.7` / `LIMB_SY = 1.25`，绕各自内端缩放）：
> 弓臂外端从 ±3.77 到 **±4.51**、跨度 **7.06 → 9.02**（另一份参考 `十字弩.bbmodel` 的弓臂是 ±6.8、
> 而机身带只 ±0.8，所以我们这版弓臂偏短、看着总像贴在弩身上）。
> 弦与凸轮盘的 pivot 就在弓臂梢上，所以它们跟着弓臂一起走（弦不会脱开）；
> 弦心 / 弩箭 / 左手的目标点共用同一份 `nockTravel(draw)`（弦锚点被弓臂带走的位移 + 弦绷直所需的后退），
> 这样弦内端永远正落在弦心上（拉满时偏差 0.00）。
> **击发/未拉弦时回到参考网格（图片）那个张开姿态**（`draw = 0` ⇒ 转角与后滑量都为 0）。
> 离线验算 + 出图：`python tools/_cb_flex.py [--bake 1.0]`。

### 光学瞄具（AKM 顶部导轨）

| 物品 | 开镜表现 |
|---|---|
| **红点瞄准镜** `red_dot_sight` | 只把屏幕正中画一个红点（与原版准星同心），**枪身照旧可见**，视野略微拉近（×0.88） |
| **4 倍瞄准镜** `scope_4x` | 开镜**不铺整屏遮罩**：枪本体与手臂一起抬起来瞄准（看得见枪与镜环），只叠对称十字分划；变焦是轻微的 ×0.72 |

- 两种瞄具的**光轴参照点**（模型 Y=4.07 / 4.28）写在 `weapon/WeaponMount.java` 里，
  举枪时会被顶到屏幕正中 —— 也就是说“瞄具装在哪，准镜就对哪”，**改模型高度必须同步改这里**
  （r67 把护木导轨齿顶抬到瞄准线 3.44，两个参照点也随之 +0.28）
- 目前只能在创造模式「六相月灾」页签取用（还没加合成配方）

> **AWP 的 8 倍镜（r79，r83 改样式）**：不是装在导轨上的配件，而是枪自带的 —— 按住右键抵肩，
> 把**镜筒光轴**顶到屏幕正中、**枪与手臂一起抬起来瞄准**（看得见枪与八棱镜环）；
> r83 起**不再铺整屏近黑遮罩**，只叠 **duplex 双柱式十字分划**（外侧粗柱 / 内侧细线（贯穿中心不断开）/
> 线上每 r/4 一个密位点 / 中心暖色亮点，见 `client/ClientEvents.java#drawCrossReticle`）。
> ⚠️ **变焦只能给轻微的（×0.72 ≈ 1.4 倍）**：原版第一人称手持渲染用的是**同一个投影矩阵**
> （`ItemInHandRenderer` 里没有自己的 perspective）⇒ 强变焦（1/8、1/4）会把枪本体一起放大 4~8 倍、
> 糊满全屏（vanilla 望远镜正因此把手藏起来）。试过的「在眼睛处乘 1/倍率反向缩放」方案在游戏里不可靠
> （r83 实测把枪缩成了一根细针），已回退。要真正做到「强变焦 + 看得见枪」，必须改成
> **自己用独立投影画枪并立刻 flush**（cancel `RenderHandEvent`，自己调 BEWLR + 手臂）。
> 整屏镜筒遮罩现在只剩十字弩在用。
> 光轴参照点 = 模型 Y 3.15（`WeaponMount.AWP_SCOPE_Y`，必须与 `tools/awp_v2.py` 打印的 `SCOPE_Y` 一致）。

> **Kar98k 的 4 倍镜（r105）**：与 AWP 同一套「整屏镜筒遮罩」开镜（`ClientEvents.scoping` 对
> `Kar98kItem` 直接返回 true ⇒ 走 `maskScoping`，把枪与手臂一起藏掉、只留镜筒 + 分划 + 蓝圈），
> 区别只有倍率：`Kar98kItem.SCOPE_ZOOM = 4.0`（世界变焦 1/4；AWP 现在也是 4 倍）。
> 光轴参照点 = 模型 Y **4.40**（`WeaponMount.KAR98K_SCOPE_Y` = 镜筒方块 y 3.95…4.85 的中心
> = geo 里 `scope` 骨骼 pivot 的 y，**必须与 `tools/kar98k_gen.py` 一致**）；
> 枪模投影 FOV 是 `GunPose.MODEL_FOV_AIM_KAR98K = 40`（AKM 45 / AWP 25）。
> 注意它和 AWP 不同的一点：**抵肩时枪本体不画**（整屏遮罩），所以那些举枪位移数只影响
> 「开镜射击时枪口/抛壳点的世界坐标」，画面上看不到枪抬起来的过程。

> **莫辛-纳甘的 4 倍镜 / 机瞄（r106）**：镜筒**出厂就拧在顶部导轨上**（`MosinRifleItem.SCOPE_ZOOM = 4.0`），
> 抵肩走 **AWP / Kar98k 那套整屏镜筒遮罩**（`ClientEvents.scoping` 只在
> `MosinRifleItem.sight(stack) == Sights.SCOPE` 时返回 true ⇒ 枪与手臂一起藏掉、只留镜筒 + 分划 + 蓝圈）；
> **潜行 + 右键把镜拆下来就换机瞄** —— 视野放大 **2 倍**
> （`MosinRifleItem.IRON_ZOOM = 2.0`，对齐 TaCZ `kar98_display.json` 的 `iron_zoom = 2`；AKM 是 1.33），
> 这时 `scoping()` 为 false ⇒ **枪身照旧渲染**、看得见木托与枪管。
> 光轴参照点 = 镜筒中心 **3.44**（`WeaponMount.MOSIN_SCOPE_Y`）/ 机瞄 **2.72**（`MOSIN_IRON_Y`），
> **必须与 `tools/mosin_gen.py` 的 `SCOPE_Y` / `IRON_Y` 一致**；
> 枪模投影 FOV = `GunPose.MODEL_FOV_AIM_MOSIN = 25`（TaCZ `zoom_model_fov = 25`）。

### 双手持枪（第一人称）

原版对**非空物品**只画物品、不画手臂（`renderArmWithItem` 里只有空手才走 `renderPlayerArm`），
所以枪看着像浮在空中。现在主手拿 AKM / 十字弩 / **AWP** 时，用**玩家自己的皮肤**另外补画两条手臂：
**右手始终握在握把上**，左手则按动作走（见 `client/WeaponArms.java`）：

| 武器 | 左手动作（按换弹读条推进） |
|---|---|
| **AKM** | 托护木 → 抓住弹匣抽出来（跟着弹匣下坠/前倾）→ 满弹匣升上来时扶着往上推 → 换到拉机柄拉栓上膛 → 回护木 |
| **十字弩** | 托护木 → 抓住弩弦往后拉（跟着弦心）→ 松手下去取箭 → 把箭推上箭槽 → 回护木 |
| **AWP** | 托护木（**拉栓时不动**，栓动步枪的支撑手就该留在原地）→ 换弹时伸手抓弹匣、跟着它下坠/前倾 → 回护木 |
| **Kar98k** | 托护木（拉栓时不动，同上）→ **逐发压弹时抬到机匣上方，跟着每一发往下按**（它没有可拆弹匣，弹仓底板不动；位置量着几何挑：y 3.60→3.05 在机匣顶与 4 倍镜筒之间）→ 回护木；右手平时握把，**拉栓 / 开栓关栓时抓下弯拉机柄**跟着枪机抬起/后退 |
| **莫辛-纳甘** | **左手全程扶枪**（托前托把枪端稳，不参与装填）；**逐发压弹改由右手**：手从拉机柄移到机匣上方（x +0.50，避开 4 倍镜筒），一发一发往下按（弹仓式，没有可拆弹匣）。右手平时握**腕部**，**拉栓 / 开栓 / 关栓时抓下弯拉机柄**跟着枪机抬起（90°）/ 后退（2.3px） |
| **M1 加兰德** | **左手全程扶枪**（加兰德换弹本来就是单手压漏夹）；**右手**平时握托颈、**射击时不动**（枪机是导气杆自己动的），换弹时抬到机匣上方把 **8 发漏夹**压下去、再抓住拉机柄跟着枪机复进（「拉一次栓」那一下） |

- 手的目标点写在各自 GeoModel 里（模型像素），经 `client/GunFrame.java` 换成相机空间；
  `GunFrame` 记的是 `move` 骨骼（含**举枪位移**与**开火后坐**），所以手臂自动跟着枪一起动，
  不需要在手臂代码里重复任何武器逻辑
- **枪稳在手里、开火时双手跟着一起顿**（r59）：
  - 原版对非空物品会套一段「**攻击挥动**」（`applyItemArmAttackTransform`，最多 `rotX −80°`），
    而 `LivingEntity#swing` 在 swingTime 过半时会重置 ⇒ **按住左键就一直重触发**；
    全自动射击时枪就一直在手里上下点头。现在用 Forge 的
    `IClientItemExtensions#applyForgeHandTransform` 接管这一步（只保留手部基准平移，见 `client/WeaponHandGrip.java`）
  - `move` 骨骼只允许在**开火**那一瞬动（后坐：沿枪管方向**平行后拖** 1.35px，弩 0.95px）；
    走路 / 待机 / 换弹 / 拉栓 / 拨保险这些动画推的位移与俯仰（idle ±0.11、run ±0.5、run_fast ±0.9 像素 + 3~5°）
    一律收平 —— 枪不再在手里晃
  - **位移只留 Z（前后），X/Y 与角度一律清零（r62）**：用户要求「只前后动、不上下动」——
    fire 动画自己还推了 +0.15px 的 Y（上下）、reload 推 −1.2px / +7°，全部收掉；
    后坐就是纯后拖，冲量衰减后自己滑回去 ⇒ **真实的后坐感来自沿枪管的往复**
  - **镜头的后坐反馈只留给开火（r62）**：`camera` 骨骼只在 `firing()` 时叠到视角上，
    换弹 / 拉栓（含换完弹那一下）镜头是稳定的，不再“换完弹再上下动一下”
  - **举枪位移 / 后坐只在「拿在手上」时生效（r62/r63）**：GeckoLib 的 `setCustomAnimations`
    对 **GUI 图标 / 掉落物 / 展示框**一样会跑 ⇒ 不加判断的话开火时**物品栏里的图标也往后跟**
    （用户反馈）；现在按 `ItemDisplayContext` 只在第一/第三人称推骨骼（`*GeoRenderer.handPass`）
  - **图标现在是彻底的静态姿态（r63）**：非手持语境直接走 `*GeoModel.staticPose()` —— 举枪位移、
    后坐、换弹的弹匣/枪机、抛壳、弩弦全部归位。r62 只门控了「举枪位移与后坐」，而
    「开火中」是**本地玩家的全局状态**，所以图标还是会跟着移动（用户反馈「7 格物品栏里 akm 发射时还是往后移动」）；
    弩的箭是否显示改看被渲染那把弩自己的 `cockedNow`，不再拿本地玩家的换弹进度去画图标
  - **手臂与枪的同步靠 frame 捕获（r63/r64）**：`WeaponArms` 是在 `RenderHandEvent` 里、**比物品先画**，
    所以「渲染时再捕获 frame」永远只能拿到**上一帧**的值 —— 开火那一瞬枪和手差一帧（用户：
    「akm 发射和手臂都多一帧上下晃动一下」）。现在把 move 骨骼的姿态收成**一份共用数学**
    （`AkmGeoModel.computeMovePose` / `CrossbowGeoModel.captureNow`），手臂画之前先自己算当前帧：
    开枪那一瞬间枪和手一定同拍
  - **视角不再点头（r64）**：`camera` 空骨骼会被 `ClientEvents.applyAkmCamera` 叠到视角上，
    而动画给它的角度是**阶跃**的 ⇒ 每开一发**整个视角（连枪和双臂）上下点一下头**，
    就是用户说的「多一帧上下晃」。现在 `AkmGeoModel.zeroCamera()` 一律清零，后坐只保留沿枪管的平移
  - **动画推在 `move` 上的 Z 也不放行（r64）**：以前开火时给动画的 Z 放行，而动画位置是
    「首帧跳到位、末帧跳回去」的阶跃 ⇒ 每发都让枪顿一下。现在 Z 只由 `WeaponAnim` 的冲量驱动
    （开火那一 tick 加上去、之后每 tick ×0.55 衰减，天生平滑）
  - **枪身角度一律保持「平行」（r60）**：任何动画给 `move` 推的角度（fire 的 −2.8°、reload 的 +7°）
    都会让枪和双手一起低头/抬头，所以开火与瞄准时 `move` 的角度都清零；后座**只后拖不给俯仰**
  - **肩点必须放在画面外（r65）**：肩点原来在 `z≈−0.42`（离相机只有 0.42 格），为了够到枪还要把手臂
    拉到 1.7 倍长 ⇒ 屏幕上就是**一大片皮肤色梯形把枪遮住**（用户录屏里的主要问题）。
    现在肩点放到画面下缘外、约 0.8 格处，肩距≈0.9 格（拉伸只有 ~1.2 倍），手臂粗细再乘 0.85
  - **后坐走的是 **`move` 骨骼**（不是 display/pose），而手臂读的就是 `move` ⇒
    **开火时双手一定跟着枪动**，不用在手臂那边再补一套
- 手臂摆放：手臂方块在 pose 坐标里是 **原点端=肩、局部 +0.75 格端=手**，所以「把手放到 H」= 原点平移 `H − R·(方块局部 x 中心, 0.75·s, 0)`；
  只沿长度方向拉伸（`pose.scale(1,s,1)`），粗细保持原版。注意右臂方块局部 x 中心是 **−0.375**、左臂（mirror）是 **+0.375**，不补偿手就偏半个方块
- 离线核对：`mod/tools/_armstory.py akm|crossbow` 会按进度渲出故事板（枪 + 双臂），
  改手位不用反复进游戏
- **AWP 是唯一的「右手干活」武器（r80~r82）**：右手平时握把（食指在扳机上），**拉栓时抬起来抓拉机柄**
  —— 手的落点与枪机**共用同一份数学**（`boltLiftAt` / `boltBackAt`：抬 62° + 后退 1.9 像素），
  所以手永远不脱手，拉完自动回握把；左手全程托着护木，只在换弹时去抓弹匣
  - 拉栓还带 **6 帧缓冲**（`AwpRifleItem.BOLT_DELAY`）：击发后右手先留在握把上扣扳机，
    **拉栓音效也晚 6 帧响**，不会和枪声糊在一起
  - ★ **扣扳机是程序化推的**：`animation.awp.fire` 那段 11° 键帧**永远轮不到**
    （击发同一帧就开始拉栓，控制器优先级 bolt > fire），现在按 `fireWindow` 推 `trigger` 骨骼
- ★ **第一人称持枪与 AKM 同一套规则**：`move` 骨骼**不做任何额外旋转**，枪管轴线始终平行于视线
  （`AwpGeoModel.computeMovePose` 三个角度恒为 0），枪口 / 抛壳点的世界坐标直接用模型点（`WeaponMount.awp`）
  · r82 曾为了「屏幕上的轴线水平」给过 `HIP_PITCH = -14°`，但那等于让枪在世界里真的朝下 14°
  （用户反馈「枪口下垂」），**已去掉**；以后要调屏幕上的倾斜感请改 display 旋转并同步 `WeaponMount`
- ★ **display 平移按「轴线重合」定**：`awp.json` 的 firstperson TY `4.22 → **1.575**`
  （= `AKM_TY + (AKM 轴线 Y 1.75 − AWP 轴线 Y 1.575)`）⇒ 两把枪的枪管轴线在屏幕上**完全重合**（都是 39.1°），
  也就是「AWP 用 AKM 的持枪方式」。注意 AWP 的握把比它的枪管轴线低 2.65（AKM 的握把正好就在轴线上），
  所以这样摆以后**双手会比 AKM 低 0.165 格** —— 模型原点不同带来的必然结果，不是 bug；
  `mod/tools/_awp_arms.py` 会复核双臂可达性（当前拉伸 0.58~1.31x，硬门槛 0.1~3.0）
- **离线第一人称预览器（r82）**：`python mod/tools/_awpfp.py <geo> <tex> out.png
  [--aim --kick --bp --pitch --hands --rot]` —— 按原版手持变换链从**眼睛**做透视渲染
  （Z-buffer + 透视正确 UV），渲染结果与游戏截图逐像素级对得上，调手持姿态再也不必开游戏；
  `--hands` 会把两条手臂画成方块，校核「手有没有连在枪上」。扫角度用 `mod/tools/_awpscan.py`

> **获取途径**：六把武器本体可在原版探险箱里按概率开出（附赠一份对应弹药）—— 常见箱 6%（地牢 / 矿井 / 神庙 / 前哨 / 村庄武器商…）、稀有箱 16%（古城 / 林宅 / 末地城 / 宝藏 / 堡垒…），权重 复合弓 6 : 十字弩 3 : AKM 1 : **AWP 1** : **莫辛-纳甘 2** : **M1 加兰德 2**（稀有箱 3 : 4 : 3 : **2** : **4** : **4**，莫辛配 10 / 15 发 7.62×59mm、M1 配 10 / 15 发 7.62×61mm）；也可在创造模式「六相月灾」页签直接取用（**Kar98k 目前只能这样拿**）。

### 弹药与弹药盒

| 物品 | 容量 | 获取 |
|---|---|---|
| 弩箭 | — | 木棍 + 燧石 ×4 |
| 复合弓箭 | — | 木棍 + 燧石 + 线 ×4 |
| 尸毒箭 | — | 复合弓箭 + 尸毒萃取剂 ×2 |
| 7.62×39mm | — | 火药 + 铁粒 ×6 |
| **.338 狙击弹** | — | 火药 + 铁锭 ×4（**AWP 专用**，与 7.62 都不通用）|
| **7.62×59mm** (`ammo_762_59`) | — | 火药 + 铁锭 ×4（无序，**莫辛-纳甘 / Kar98k 共用**，与 7.62×39、.338 **都不通用**）|
| **7.62×61mm** (`ammo_762_61`) | — | 火药 + 铁锭 ×4（无序，**M1 加兰德专用**，与 7.62×39 / 7.62×59 / .338 **都不通用**）|
| 弩箭 / 箭矢 / 步枪弹药盒 | 64 / 96 / 300 | 同一形状 `ppp/p■p/iii`，**中心槽放对应弹药**（三个配方靠中心材料区分，不会互相冲突） |
| **.338 弹药盒** | 120 | 同上形状，**中心槽放 .338 狙击弹**；快捷栏 HUD 占第 4 格 |
| **7.62×59mm 弹药盒** | **150** | 同上形状（`ppp/p■p/iii`，与 `ammo_box_sniper` 同款），**中心槽放 7.62×59mm 子弹**；快捷栏 HUD 占第 5 格 |
| **7.62×61mm 弹药盒** | **128** | 同上形状，**中心槽放 7.62×61mm 子弹**（钢蓝灰标签带，与 7.62×39 无带 / 7.62×59 红棕带区分）；快捷栏 HUD 占第 6 格 |
| 创造弹药箱 | ∞ | 创造页；**放在物品栏（快捷栏 / 背包 / 副手）里就生效**：六把武器无限供弹，不用手持、不用切弹种 |

### 投掷物

| 物品 | 效果 |
|---|---|
| **碎片手雷 `mud`** | 半径 4.5 格爆炸伤害（最高 14，按距离衰减）+ 短暂缓慢 |
| **震爆弹 `mtx`** | 半径 6 格：**致盲 + 眩晕**（缓慢 III / 反胃 / 虚弱，时长随距离衰减），近距离额外 4 点伤害 |

**操作流程（两者相同）**：

1. **按住右键 1 秒** → 拔出保险销（咔哒声 + 提示）。**拔销途中松手** = 销还没出来，自动插回
2. **拔销之后必须一直按住右键**：压杆被手压着、撞针不会释放 —— 这时可以**潜行 + 右键 1 秒**把销插回去反悔
3. ★ **一松手（没及时按住 / 手滑）⇒ 撞针击发、引信立刻点燃**（r77 写实规则）：
   **5 秒内必须左键丢出去**，不然就在掌心爆（`GrenadeBlasts.detonateInHand`）；
   引信点着后插不回销了，**收回背包 / 换到别的格子也照样烧**，到点炸在身上
4. **左键丢出** —— 飞行中继续读秒，撞到方块弹一下、撞到生物不会停，引信说了算
5. ★ **按 `R` 紧急投掷**（r78）：只要手上（主手或副手）有一颗已拔销 / 引信在烧的雷就丢它
   —— 主手举着枪、副手那颗雷在烧时也能救急（`grenadeInEitherHand`）

| 手雷状态 | 行为 |
|---|---|
| 插着销 | 完全安全，拿多久都行 |
| 销已拔出、**手压着压杆**（按住右键） | 引信未点；可投出，也可潜行 + 右键把销插回 |
| **销已拔出、手松开了** | ★ **撞针击发、引信点燃**（5 秒）—— 丢出去，或在手里爆 |
| **销已拔出、切武器 / 收回背包** | ★ 同样算「脱手」 ⇒ **撞针击发、引信点燃**（r78，`gripped()` 判定）|
| 引信燃烧中（`ARMED`） | 手里 / 背包 / 护甲里都继续烧；右键想插销会被拒绝 |
| **主手举着枪 + 副手有活雷** | 默认按键轮不到它 ⇒ **按 `R` 紧急投掷**（按准星丢出）|
| 开界面 / 切手持物（被动中止） | 手还抓着，**不点火** |

### 月相

六种月相（血月 / 蓝月 / 黄月 + 各自的**超级**版本）**随机出现**，各有专属的月亮颜色与天空颜色
（自画的月盘 + 天穹染色，见 `client/MoonSkyRenderer.java`）：

- ★ **不再是按夜数轮转**（r75）：每夜独立掷骰、六相同权重 ⇒ **可能连着两夜同一个月相，
  也可能几十夜都不出月相**；基础概率 **25%**，连续 10 夜没出之后每夜 +1%（上限 60%）。
  连续无月概率：3 夜 42% / 5 夜 24% / 10 夜 5.6% / 15 夜 1.2% / 20 夜 0.17%
- 月升时全服弹标题与提示、客户端同步（`MoonManager` → `ModNetwork.syncToAll`）

| 月相 | 月亮颜色 | 天顶 / 地平线 | 效果 |
|---|---|---|---|
| **血月** | `#FF4A38` 红 | `#1C0608` / `#521114` | **四波尸潮**（每波 6/9/13/18 只·人）+ **亡灵随时间进化**（黄昏 ×1 → 天亮 ×2）+ **晚上不能睡觉** |
| **蓝月** | `#AECBFF` 淡青蓝 | `#06101F` / `#143A6E` | **玩家获得幸运 I**（僵尸没有任何加成）|
| **黄月** | `#FFD35E` 金 | `#141005` / `#453512` | **作物加速生长**（每 20 tick 催一次）|
| **超级血月** | `#FF6E52` + 大光晕 | `#28070B` / `#6E1616` | 同上 + **尸潮 ×1.5** + **巨箭弹幕** + 长夜不眠 |
| **超级蓝月** | `#D2E8FF` + 大光晕 | `#08142E` / `#1C4A88` | **玩家获得幸运 II** |
| **超级黄月** | `#FFE9A0` + 大光晕 | `#1C1608` / `#57431A` | 作物生长更快（每 7 tick）+ **巨箭弹幕** |

- **尸潮细节（r74）**：固定 **4 波**（波间隔 6 秒），开波与每波都有 action bar 播报；
  **第 14 天（含 28 / 42…）那晚**开波概率 0.35 → 0.75 且规模再 ×1.5；
  **天亮自动收尾**：按离玩家最近排序，每个玩家只留 4 只徘徊者，其余清除，留下的**白天不燃烧**
- **管理指令（OP 2 级 / 单人开作弊，`/hlc` 是简写别名）**：

| 指令 | 作用 |
|---|---|
| `/hexalunar moon set <blood_moon\|blue_moon\|yellow_moon\|super_blood\|super_blue\|super_yellow\|none>` | 强制指定月相（今夜不再掷骰）|
| `/hexalunar moon clear` | 清除月相 = 今夜无月 |
| `/hexalunar moon random` | 立刻按随机规则掷一次 |
| `/hexalunar moon info` | 看状态（已入夜次数 / 当前月相 / 概率 / 连旱夜数 / 尸潮）|
| `/hexalunar moon list` | 列出全部月相 id |
| `/hexalunar moon chance <0~1>` | 改每晚出月相的概率（写进存档）|
| `/hexalunar horde start \| stop \| wave <1~4>` | 手动开 / 停尸潮、单放某一波 |
| `/hexalunar barrage` | 立刻触发巨箭弹幕 |

伴随六种特殊感染者：自爆尸、喷吐尸、蛮兵尸、巨尸、突袭骷髅、剧毒骷髅。

---

## 三、项目结构

```
mod/
├── src/main/java/cn/blockforge/generated/hexalunarcalamity/
│   ├── weapon/     枪械、弩、弓、**瞄具**、射击数学（AkmRifleItem / **AwpRifleItem** / WeaponMount / Sights / Ballistics / WeaponFx）
│   ├── item/       弹药盒、创造弹药箱、解毒剂、手雷（GrenadeItem）
│   ├── entity/     弹丸与投掷物（子弹、弩箭、箭矢、手雷 GrenadeEntity）+ 特殊感染者
│   ├── client/     输入、FOV/瞄准、HUD、**GeckoLib 模型与渲染器**（*GeoModel / *GeoRenderer）、物品属性注册
│   ├── net/        网络包（月相同步 / 命中反馈 / 开火 / 装填）
│   ├── registry/   物品、实体、音效、效果、创造页签
│   └── moon/       月相管理（MoonPhase / MoonManager / MoonPhaseData / **MoonCommands**）+ 月相效果（**MoonBlessings**）+ 僵尸进化（ZombieEvolution）
└── src/main/resources/
    ├── assets/hexalunar_calamity/geo/         ★ GeckoLib 骨骼模型（.geo.json）
    ├── assets/hexalunar_calamity/animations/  ★ GeckoLib 动画（.animation.json）
    ├── assets/hexalunar_calamity/             OBJ/MTL 旧模型、贴图（含 *_glowmask.png）、语言、音效
    ├── assets/minecraft/atlases/              ★ 方块图集扩展（见下）
    └── data/hexalunar_calamity/               配方

tools/  开发辅助脚本（见第五节）
```

---

## 四、踩过的坑（改模型/资源前务必读）

1. **Forge 的 OBJ 顶点单位是「方块」**
   `ObjLoader` 把 OBJ 的 `v` 坐标直接当方块塞进 `BakedQuad`，**不除以 16**。
   Blockbench 导出的 0..16 坐标在游戏里就是 **16 格大** —— 症状是 GUI 图标被甩到格子角落只剩裁剪碎片、手持模型离手一格像"漂浮"。
   → 所有 OBJ 必须 `÷16` 并让几何**居中在 (0.5, 0.5, 0.5)**（`ItemRenderer` 会无条件 `translate(-0.5,-0.5,-0.5)`）。
   工具：`tools/obj_normalize.py`

2. **自定义方块图集只能放 `assets/minecraft/atlases/blocks.json`**
   `SpriteResourceLoader` 只会读 `minecraft:atlases/blocks.json` 这一个位置（多包叠加），
   放在 `assets/<你的命名空间>/atlases/` 里的文件**根本不会被加载**。
   目录源写法：`{"type":"directory","source":"models","prefix":"models/"}`（`source`/`prefix` 都是必填）。

3. **`firstperson_lefthand` 要和右手条目同旋转、同平移**
   镜像由 MC 自己施加，把 yaw 取反会让副手模型穿进镜头。

4. **拉弦动画＝两件事缺一不可**
   `UseAnim.BOW`（决定手部/持弓姿态）＋ `pull`/`pulling` 物品属性 + 模型 `overrides`（决定弦的形变）。
   弩必须也用 `UseAnim.BOW`：原版 FP 的 `case CROSSBOW` 只认 `items.crossbow`，模组弩用 `CROSSBOW` 会完全没有手持动作。

5. **`AbstractArrow` 的重力写死在 `tick()` 里**（每 tick 减 0.05），没有可覆盖的 `getGravity()`。
   开镜后射击距离变远会明显下坠脱靶 → 在 `tick()` 里先把 0.05 补回去。

6. **手雷引信用 `inventoryTick`**
   它是原版对背包内每个物品每 tick 的钩子，因此拔销后换手、丢回背包都不会"断表"。
   （已知边界：按 Q 丢到地上的掉落物形态不走该钩子。）

7. 物品属性（`pull` / `pulling`）在 `FMLClientSetupEvent` 里 `ItemProperties.register`；
   用自己命名空间时，**JSON 谓词键要写全名**（`hexalunar_calamity:pull`）。

8. `MobEffect.addAttributeModifier` 必须传 **UUID**，传资源名字符串会触发 FATAL 注册回滚。

9. **GeckoLib 物品的 `display` 包装不生效**
   GeckoLib 的 GeoItem 自己控制变换，套 `BakedModelWrapper` 去改 `display` 没有用。
   举枪/瞄准一律改**骨骼位移**（`CoreGeoBone#setPosX/Y/Z`）；骨骼位移在 display 的 scale **之内**，
   所以“想让骨骼等价于 display 平移 t”要给 `d = t / S`（复合弓 `S=0.75` 必须 ×4/3，AKM `S=1` 两者相等）。

10. **`handleAnimations` 会把没动画的骨骼拉回初始快照**
    `tickAnimation` 先写骨骼，再按 `getBoneResetTime()` 把非动画骨骼归位 —— 所以要在 `setCustomAnimations`
    里做“读-改-写”，别指望跨帧累加（也因此每帧都会重算，不需要自己存状态）。

11. **`UseAnim.BOW` 会给物品额外叠一段“拉弓”位移**
    原版 `ItemInHandRenderer` 对 `UseAnim.BOW` 的额外变换：平移 ±0.28 格 + rotX −13.9° +
    rotY 35.3°/−45° + rotZ −9.8° + z 轴拉伸 20%。枪一旦被套上就会歪着斜、枪托被拉长。
    枪械请用 `UseAnim.NONE`；弓/弩要拉弦效果才用 `BOW`。

12. **物品 NBT 要主动喂给 GeoModel**
    GeoItem 的 animatable 是**物品单例**（不是这一个 ItemStack），所以“装了哪个瞄具”这类 NBT
    要在 `GeoItemRenderer#renderByItem(stack, …)` 里存到静态字段，再给 model 的 `setCustomAnimations` 读。

13. **模型共面会 z-fighting 闪烁**
    两个方块的面完全重合时（例：后移的瞄具底座与机匣盖同为 `±0.42`），渲染会闪；把里面那层缩 0.02 就好。

14. **JOML 的 `Matrix3f` 9 参数构造是「列优先命名」**
    `new Matrix3f(m00, m01, m02, m10, …)` 里的 `m01` 是**第 0 列第 1 行**。照 `(x, y, z)` 的顺序
    把三个基向量写进去，拿到的是**转置矩阵**（= 反向旋转）。第一人称手臂用它就会整条翻到相机后面去、
    被近平面切一刀 → 屏幕上一大片皮肤色（r57 的 bug）。建正交基要**一列一列地填**：
    `new Matrix3f().setColumn(0, x).setColumn(1, y).setColumn(2, z).getNormalizedRotation(q)`。
    离线自查：`mod/tools/_joml_probe/`（`JomlProbe` 验 JOML 约定、`ArmSim` 算手臂方块落点）。

15. **原版会给第一人称的「非空物品」套一段攻击挥动**
    `ItemInHandRenderer#renderArmWithItem` 的物品分支 = `applyItemArmTransform`（手部基准
    `(±0.56, −0.52 − 0.6·equip, −0.72)`）+ `applyItemArmAttackTransform`（挥剑用的，最多 `rotX −80°`）。
    而 `LivingEntity#swing` 在 swingTime 过半时会重置 ⇒ **按住左键（全自动射击）就一直重触发**，
    枪会在手里不停上下点头。枪械要接管这一步：`IClientItemExtensions#applyForgeHandTransform`
    返回 `true` = 原版跳过它自己那些变换（物品照旧渲染，只是少一段 pose）。
    自己补画的第一人称手臂是跟着骨骼走的，跟不到这段 pose 变换 ⇒ 不接管就会「枪在手心里自己晃」。
    举弓类姿态（十字弩按住右键拉弦）仍要交回原版（`UseAnim.BOW` 那套位移本来就是给弓写的）。

16. **GeckoLib 画不了网格 ⇒ 参考网格要「表面体素化」**
    GeckoLib 4.8.4 的 `PolyMesh` 只在 `loading/json/raw/` 里（只解析），渲染侧的 `GeoBone` 只有
    `getCubes()` ⇒ **poly_mesh 导进来能加载但看不见**（AKM 当时就是这么撞的）。所以 mesh 参考模型
    只能体素化。两种做法在 `tools/` 里都有：
    · `akm_voxel_gen.py`（**单层壳**参考）：射线沿 +X 穿越，按「穿入/穿出」成对填充 —— 会把内部填实；
    · `crossbow_vox.py`（**多部件、互相重叠**的参考）：射线成对填充会把空隙一起填掉、薄壁被吸成大块，
      渲染出来是一坨乱方块 ⇒ 改成**表面体素化**（沿三角面密采样、采样点落在哪格就标记哪格），
      既贴合轮廓、方块数又少，视觉上一样（里面看不见）。
    另外 mesh 的 UV 要看是哪种空间（归一化 / 分辨率单位 / 像素）：
    用 `sqrt(uv面积 / 3D面积)` 算出来的「平均密度」在长条面上是不准的，
    体素面直接取**标称密度**（`step × 贴图/分辨率`）观感最好（详见 `crossbow_vox.py` 里的 `uv_space()`）。

17. **GeckoLib 的 `setCustomAnimations` 对「GUI 图标 / 掉落物 / 展示框」一样会跑**
    它只认「渲染这个物品」，不认语境。所以往 `move` 骨骼上推的**举枪位移**与**开火后坐**
    会把**物品栏里的图标**也一起推走（用户反馈：开火时「物品栏物品也随之后移」）。
    正确做法是让渲染器按 `ItemDisplayContext` 记一个 `handPass`（第一/第三人称 = true，
    GUI / GROUND / FIXED = false），模型里再决定推不推骨骼
    （见 `AkmGeoRenderer.isHand()` + `*GeoModel.handPass`）；
    瞄准/拉弦这类「手持姿态」在第三人称也是要看的，所以判据要含第三人称，不能只判第一人称。
    ★ **只把「后坐」门控起来是不够的**（r62 就只做到这一步）：
    · `firing()` / 换弹进度 / 拉弦进度都是**本地玩家的全局状态**，非手持语境下它们一样是真的
      ⇒ 动画推在 `move` 上的 Z、弹匣下坠、弩弦回拉都会一起跑到图标上（r63 才收干净：非手持走 `staticPose()`）；
    · 更隐蔽的是**手臂用的 `GunFrame` 也会被覆盖**：第一人称手臂在 `RenderHandEvent` 里比物品**先**画，
      读的是上一帧的捕获值，而图标那一遍（通常在关卡之后渲染）会把空值写进去
      ⇒ 下一帧手臂按「无举枪、无后坐」摆位，看起来就是「枪在动、手不跟着」。
      所以 frame 必须只在 `handPass` 为真时捕获。
    ★ **即使只在手持语境捕获，也还是差一帧**（r64 用户反馈「akm 发射和手臂都多一帧上下晃动一下」）：
    手臂比物品先画，「渲染时捕获」拿到的永远是上一帧的值。正确做法是把骨骼姿态写成**一份共用数学**
    （纯函数：`AkmGeoModel.computeMovePose`），手臂画之前先自己算当前帧 ⇒ 枪与手同拍。
18. **别让「动画的阶跃位移」直接驱动任何东西**
    动画键值在「开播首帧」与「结束那一帧」是**跳变**的，直接把它当位置用就是每一发都顿一下。
    两个真实病例（r64）：
    · `camera` 空骨骼被 `ClientEvents.applyAkmCamera` 叠到视角上 ⇒ 每开一发整个视角（含模型与双臂）
      上下点一下头 —— 修法：一律清零，要「后坐上跳」就用冲量自己做平滑；
    · `move` 骨骼的 Z 在开火时给动画放行 ⇒ 枪在动画首/末帧跳一下 —— 修法：Z 只由冲量驱动。
    结论：**位置只用能自己控阶跃的量（冲量/插值），动画键值只当「要不要演动作」的开关**。

19. **javac 只报「找不到符号」而 `tools/_check.py` 会把明细过滤掉**
    r75 一次报 13 个「找不到符号」但看不出原因，真因有两个：
    · **`Component` 接口没有 `withStyle()`**（只有 `MutableComponent` 有）⇒ 辅助方法声明返回 `Component` 时，
      调用处 `.withStyle(...)` 全栈编译不过；把返回类型改成 `MutableComponent` 即可。
    · **局部变量会遮蔽同名方法**：`ServerLevel level = level(src);` 里正在声明的 `level`
      从声明处就开始生效 ⇒ 右边的 `level(src)` 被当成访问变量 ⇒ 一行代码 13 个错误。方法改名 `targetLevel`。
    取明细：`cmd /c "gradlew.bat compileJava --offline --console=plain > build\err.log 2>&1"` 再读日志
    （`--offline` 顺带绕开本机偶发的依赖卡网络）。改完记得用 `get_errors`（语言服务器）交叉核对。

20. **★ 枪管轴线与视线平行 ⇒ 它在屏幕上「必然是斜的」（这是透视，不是模型歪）**
    一阶近似：相机在眼睛处朝 −Z，枪管轴线上离相机 t 处的点投影屏幕坐标 ∝ `offset / t`
    ⇒ **近端（枪托）远远偏离画面中心、远端（枪口）贴着中心**。实测 AWP 屏幕倾角 **21.6°**
    （AKM 更斜 **40°**，因为它的 display TY 更低、枪整体更靠下）。
    所以「枪看着斜着往上翘、枪托往下掉」不是模型长歪了，也**不能靠挪 display 平移修** ——
    只能给一个**俯仰角**：让枪管轴线不再与视线平行，它的收敛点就会离开屏幕中心。
    AWP 用 `AwpGeoModel.HIP_PITCH = -14°`（绕 `move` pivot 下压），轴线在屏幕上变成水平（-0.2°）；
    **举枪时必须归零**（镜筒光轴不能歪），**第三人称也不加**（`AwpGeoRenderer.firstPerson`）。
    ⚠️ 加了角度以后，**枪口 / 抛壳点的世界坐标必须同步转**（`WeaponMount.awpHipPitch`），
    否则弹道与枪口焰会和枪管对不上（这个项目的弹道是从模型点出发的）。
    离线定位：`python mod/tools/_awpfp.py <geo> <tex> out.png [--pitch -14]`（会打印轴线倾角）、
    `mod/tools/_awpscan.py`（扫角度）。

21. **`setCustomAnimations` 在动画控制器之后跑 ⇒ 程序化推骨骼一定赢，但也可能「让动画白播」**
    GeckoLib 的顺序是：控制器挑一段动画 → 按时间写骨骼 → 再调 `setCustomAnimations` 让你覆盖。
    所以「控制器选了 `bolt` 动画」和「我在 `setCustomAnimations` 里把 `bolt` 骨骼设成我算的值」
    完全不冲突 —— 后者是最终值（AWP 的拉栓/抛壳/弹匣/扳机全靠这条）。
    **反面**：某段动画的骨骼如果**每一根**都被程序化覆盖，那它就等于没播。
    AWP 的 `animation.awp.fire` 就这么消失过 —— 击发**同一帧**就开始拉栓，控制器优先级 `bolt > fire`
    ⇒ 那段 11° 扣扳机键帧**永远轮不到**。要用「按下扳机的进度」就把窗口时间存进 NBT
    （`HlcFireAt` + `AwpRifleItem.fireWindow`），再自己推骨骼。

22. **参考包坐标系与本项目相反时，要把旋转「烘进几何」，不能挂在根骨骼上**
    AWP 参考包是 **X = 枪口向前**，本项目是 **枪口 = −Z**。看着最省事的做法是加一根 `rotY = 90°`
    的根骨骼 —— 但**子骨骼的位移是写在父级局部系里的**：`move` 骨骼往 Z 推会变成「往侧面推」、
    抬枪会变成歪着抬。正确做法是在生成几何时就把 `R_y(+90°)` 乘进每个顶点
    （见 `tools/awp_gen.py`：`(x, y, z) → (z, y, -x)`），导出的 geo 里**没有任何根旋转**，
    后续动画/骨骼位移的语义才和 AKM、十字弩一致。

---

## 五、开发辅助工具（`tools/`）

| 脚本 | 用途 |
|---|---|
| `akm_v3.py` / `bow_v3.py` / `grenade_v3.py` / `flashbang_v3.py` | **武器/投掷物模型生成器**（几何 + 逐面 UV 贴图 + 自检），产物写到 `build/*.geo.json` / `*.png`；自检会打印骨骼名、瞄准线水平/居中、弦端点、导轨高度余量（**十字弩 r61 起改用下表的 `crossbow_vox.py` 体素化**，`crossbow_v3.py` 仅作历史参考） |
| `boxlib.py` | 上面各生成器共用的几何/上色库（倒角、圆角、椭圆、螺栓、通风口、布纹…） |
| `install_models.py` | 把 `build/*.geo.json` + `*.png` 装进 `assets/.../geo` 与 `textures/models`（先备份旧文件） |
| `gen_glowmask.py` | 按亮度阈值自动生成自发光遮罩 `*_glowmask.png`（**改完贴图必跑**） |
| `geo2bbmodel.py` | 把 `.geo.json` 反导成 `.bbmodel`，方便在 Blockbench 里看/改 |
| `bbmcp.py` | Blockbench MCP 的 JSON-RPC 直连客户端（`list` / `call` / `batch` / `schema`） |
| `bbpush.py` | 把 geo + 贴图推进正在运行的 Blockbench 工程（现在的模型迭代主力） |
| `_ads_check.py` | 离线验算举枪对心：按 `WeaponMount` 的变换链算出锚点落在屏幕哪里（要 0.00% / 0.00%） |
| `_gren_pin.py` | 手雷 / 震爆弹**保险销行为**离线自检：核对手持状态机规则（尤其是「手里攥着永远不点燃引信」这条硬保证）、检查语言键，并把状态转移表打印出来 |
| `_moon_r74.py` | 月相系统离线自检：月相数值（蓝=幸运 / 黄=催作物 / 血=四波尸潮）、尸潮规模推演、**随机出现与连旱概率**、指令树完整性 |
| `_joml_probe/`（Java） | 第一人称手臂离线验算：`JomlProbe` 验 JOML 旋转约定（`Matrix3f` 构造顺序 / `rotateAxis` 语义），`ArmSim` 按 `WeaponArms` 同一套数学算出双臂方块 8 个角在相机空间的位置并投影到屏幕，顺带告警「是否越过相机平面」（越过了就是糊屏） |
| `crossbow_vox.py` | 把**参考网格**（`模型/十字弩_v2.bbmodel`，11 个 mesh 部件）**表面体素化**成 GeckoLib 方块模型：逐格从原贴图采 UV、按 mesh 名分骨骼、弦/弦心/弩箭另外用方块画；末尾打印并自检「拉满时两段弦内端是否正好落在弦心」。`--step` 调体素大小（0.45 → ~820 方块） |
| `_cb_flex.py` | 十字弩**弓臂内收**的离线验算 + 姿态烘焙：打印「弓臂外端往内/往后走了多少」「弦内端相对弦心的偏差」，`--bake 1.0` 能把该姿态烘成 `build/cb_flex_*.geo.json` 直接用 `geo_texview.py` 出图。<br>★ 常数（`FLEX_DEG` / `FLEX_PX` / `FLEX_PZ`）必须与 `client/CrossbowGeoModel.java` 一致 |
| `_scopemock.py` | 离线复刻倍镜遮罩绘制数学出 PNG（调分划参数不用反复进游戏） |
| `gen_sight_icons.py` | 生成红点 / 4 倍镜的物品图标 PNG |
| `awp_gen.py` | **AWP 模型生成器**：把参考包 `模型/AWP_Printstream_Minecraft` 转成 GeckoLib 用的 geo + 贴图（烘 `R_y(+90°)`、缩放 0.75、逐面 UV 重映射、重排成 512² 图集 @19 像素/单位），再按本项目的骨骼/动画约定做二次造型（机匣瘦身、枪管加长、倍镜改八边形、扳机拆骨骼、弹壳双段、点阵明细…）；末尾打印骨骼表 / 包围盒 / 图集密度 / 关键模型点。**流光遮罩由它自己画**（参考图几乎全白，`gen_glowmask.py` 的百分位法失效，那个脚本已排除 awp） |
| `install_awp_sounds.py` | 把 `模型/` 里用户提供的音频改名拷进 `sounds/weapon/`（`awp枪声.ogg` / `AWP狙击步枪换弹音效.ogg` / **`拉栓上膛.ogg`**）|
| `gen_ammo338_icons.py` | 画 `.338 狙击弹` 与 `.338 弹药盒` 的 16×16 图标（并出大图预览）|
| `_awpfp.py` | ★ **第一人称离线预览器**：按原版手持变换链（`ItemInHandRenderer` + `ItemRenderer` 的 display）从**眼睛**做**透视**渲染（Z-buffer + 透视正确 UV），与游戏截图逐像素级对得上。`--aim / --kick / --bp / --pitch / --hands / --rot / --h --aspect` 可复现举枪 / 后坐 / 拉栓 / 下压角 / 双臂，并打印**枪管轴线在屏幕上的倾角**（调姿态不用开游戏）|
| `_awpscan.py` | 扫描「俯仰角 ↦ 枪管轴线屏幕倾角」（display 旋转 / `move` 骨骼旋转两套都算），用来定腰射下压角 |
| `_awp_arms.py` | AWP 双手**可达性校核**：把手部落点换算到相机空间，检查肩距是否在 `drawArm` 的 (0.1, 3.0) 格内、拉伸倍率多少、在画面哪个位置 |
| `_awpanim.py` | 把某段动画按时间点烘成静态 geo 再出图（拉栓 / 抛壳 / 换弹 / 开镜的**故事板**）|
| `kar98k_gen.py` | **Kar98k 模型生成器**（r105，r107 加弹）：程序化画木托长枪 + 下弯拉机柄 + 自带 4 倍镜筒 + 机匣里的黄铜弹壳（`casing` 骨骼）+ **压弹时那一发**（`round_in` 骨骼，7.62×59 弹壳/弹肩/弹头三段，弹头朝 −Z），一次输出 `geo/kar98k.geo.json`（11 骨骼 / 29 方块）+ `textures/models/kar98k_geo.png` + `textures/models/kar98k_geo_glowmask.png`（流光遮罩只留钢 / 镜筒 / 镜片 / 黄铜四条色带，木托不发光）。末尾打印骨骼表与包围盒 —— **`WeaponMount.KAR98K_*` 与 `Kar98kGeoModel` 的模型点都要照着这份打印量** |
| `m1_garand_gen.py` | **M1 加兰德模型生成器**（r108，**已被 `m1_garand_v2.py` 取代，别跑**）：整木托（胡桃木）+ 上下两片木护木包住枪管 + 机匣 + **右侧长导气杆** + 大觇孔照门 + 机瞄 + 扳机护圈环 + 黄铜弹壳 + **8 发漏夹**（`clip_in` 骨骼） |
| `m1_garand_v2.py` | ★ **M1 加兰德模型生成器 v2**（r112，**r113 改平行抬盖**）：12 骨骼 / 71 方块 / 512² 逐面 UV = **八棱空心枪管（带黑色膛底堵头）** + **八棱空心觇孔环 + 透明玻璃十字线** + **整体平行抬起的弹夹盖**（`cover`，纯平移不转角度）+ **实体顶桥**（照门座坐它上面）+ **8 发黄铜子弹的漏夹**（压在机匣内部）+ **八棱圆盘旋钮**照门，另生成 6 条空动画；末尾打印**自检**（空心管 / 瞄准线 / 漏夹不越机匣 / 盖板与桥齐平 / **抛壳轨迹不穿盖板**）与关键模型点。<br>用法：`python tools/m1_garand_v2.py`（跑完 `geo2bbmodel m1_garand` + `bbpush`）；自检汇总用 `python tools/_m1check.py`（写 `build/_m1check.txt`，终端直接看中文会乱码） |
| `gen_ammo762_61_icons.py` | 画 **7.62×61mm（M1 加兰德）** 子弹与弹药盒的 16×16 图标（细长瓶颈弹壳 + 铜被甲尖弹头；弹盒 = 军绿铁盒 + **钢蓝灰标签带**）|
| `_oggdur.py` | 不装第三方库读 Ogg 时长（解析 page 的 granule / 采样率）—— 配音效前先量长度，再用 `playSound` 的 pitch 对齐动作时长 |
| `fp_preview.py` | 第一人称 / GUI / 第三人称离线预览：读模型 JSON 的 `display` + OBJ，按游戏同样的矩阵光栅化出 PNG，并打印屏幕像素包围盒。<br>调手持姿态用它：`python fp_preview.py --json akm.json --obj akm.obj --ctx firstperson_righthand --rot 0,0,0 --trans=-5,-3,4.5 --scale=0.5 --out t.png` |
| `obj_normalize.py` | OBJ 顶点 ÷16（单位修复），自动留 `.unit16bak` 备份 |
| `bbmodel_to_obj.py` | Blockbench `.bbmodel`（网格模型）→ OBJ + MTL，自动 ÷16、居中、UV 归一化 |
| `weapon_string.py` / `bow_gen_pull.py` | 生成拉弦变体：在原模型两梢之间补一条会被拉成 V 形的弦 |
| `scale_weapons.py` | 批量改所有武器（含拉弦变体）的 `gui` / `firstperson_*` scale |
| `obj_rotate.py` | 绕几何中心旋转 OBJ 顶点（`--x/--y/--z`），用于把模型长轴对齐到原版物品的 Y 轴约定 |
| `recipe_audit.py` | 合成表静态体检：JSON 合法性、物品/标签存在性、pattern 自检、配方冲突、无产出物品 |
| `lang_audit.py` | 翻译键体检：代码里用到的 key 是否在 `zh_cn`/`en_us` 都存在、中英是否对齐 |
| `log_audit.py` | 日志体检：扫 `mod/logs`（含轮转 `.gz`）捞出模组相关堆栈/报错，汇总关键信号 |
| `github_ip.py` | 扫 GitHub 可用 IP（TCP + 真 TLS 握手双重验证），`--apply` 写 hosts |
| `push.py` | 一键推送：**先扫 IP → 写 hosts → 再 push**，失败自动重扫重试（`-m` 可顺便提交，中文安全） |

---

## 六、常用参数速查

| 想改什么 | 位置 |
|---|---|
| **武器形状 / 贴图** | `mod/tools/akm_v3.py`（弩 `crossbow_vox.py`（体素化参考网格）、弓 `bow_v3.py`、手雷 `grenade_v3.py`、震爆弹 `flashbang_v3.py`、**AWP `awp_v2.py`**）→ 再跑 `install_models.py` + `gen_glowmask.py`（awp 的遮罩由 `awp_v2.py` 自己画，不用跑后者）|
| **AWP 腰射姿态 / 屏幕斜不斜** | `client/AwpGeoModel.java` 的 `HIP_PITCH`（**-14°**，举枪时 ×(1-aim) 归零、第三人称不加）+ `weapon/WeaponMount.java` 的 `AWP_HIP_PITCH` / `awpHipPitch()`（**两处必须一致**，后者给枪口/抛壳取点用）；离线扫角 `tools/_awpscan.py`、看效果 `tools/_awpfp.py --pitch -14` |
| **AWP 数值（弹匣 / 时序 / 弹道）** | `weapon/AwpRifleItem.java`（`MAG_SIZE` 5 · `RELOAD_TICKS` 44 · `BOLT_TICKS` 22 · `BOLT_DELAY` 6 · `CYCLE_TICKS` 28 · `BULLET_SPEED` 6.2 · `SCOPE_ZOOM` 8）+ `Ballistics.AWP_RANGE` / `AWP_IN_RANGE_GRAVITY` + `BulletEntity.SNIPER_DAMAGE`（24；用初速 >5.5 识别狙击弹）|
| **AWP 栓动 / 抛壳 / 扳机 / 手** | `client/AwpGeoModel.java`：`boltLiftAt` / `boltBackAt`（**骨骼与右手共用**）、`BOLT_LIFT` 62° / `BOLT_BACK` 1.9px、抛壳轨迹常数（`CASE_T0/T1` / `CASE_VX/Y/G` / 三轴翻滚）、`triggerPullAt`（按 `fireWindow` 推扳机）；左手目标 `ARM_SUPPORT`（**不要放到 z<-4.2**，那儿是露出的枪管 + 折叠两脚架）|
| **Kar98k 数值 / 模型点** | `weapon/Kar98kItem.java`（`MAG_SIZE` 5 · `BOLT_TICKS` 20 · `BOLT_DELAY` 6 · `BULLET_SPEED` **5.7** ⇒ 伤害 **50**（`BulletEntity.KAR98K_DAMAGE`，爆头 ×1.85）· `SCOPE_ZOOM` 4.0 · 逐发压弹 `BOLT_OPEN_TICKS` 15 / `LOAD_TICKS` 12 / `BOLT_CLOSE_TICKS` 16 / `BULLET_LOST_CHANCE` 0.30）+ `weapon/WeaponMount.java` 的 `KAR98K_*`（枪口 {0, 2.25, −13.60} / 抛壳口 / 镜筒光轴 **4.40** / 举枪平移 −8.96 & +3.92 & −3.00）+ `client/Kar98kGeoModel.java`（`BOLT_LIFT` **64°**（下弯柄，θ>71° 会捅进镜筒）· `BOLT_BACK` 2.6 · 抛壳轨迹 · 压弹 `LOAD_DROP` 1.70 / `FEED_T0` 0.55 · 手臂落点 `ARM_GRIP` / `ARM_SUPPORT` / `ARM_LOAD` + `ARM_PRESS`）、`WeaponHandGrip.KAR98K_FIRE_PITCH` 5.5；**改模型必跑 `tools/kar98k_gen.py`，再照打印值同步这几处** |
| **M1 加兰德数值 / 模型点** | `weapon/M1GarandItem.java`（`MAG_SIZE` **8** · `FIRE_INTERVAL` 10（连射）· `BOLT_TICKS` 8（自动枪机循环）· `BULLET_SPEED` **5.15** ⇒ 伤害 **22**（`BulletEntity.M1_DAMAGE`，爆头 ×1.5）· 换弹 `CLIP_PUSH_TICKS` 22 + `CLIP_CLOSE_TICKS` 10）+ `weapon/WeaponMount.java` 的 `M1_*`（枪口 {0, 2.30, −13.60} / 抛壳口 / **瞄准线 3.10** / 举枪平移 −8.96 & +5.22 & +2.30）+ `client/M1GarandGeoModel.java`（`BOLT_BACK` 2.4 · `CLIP_DROP` 2.25 · 抛壳轨迹 · 手臂落点 `ARM_GRIP` / `ARM_SUPPORT` / `ARM_CLIP` + `ARM_PRESS`）、`WeaponHandGrip.M1_FIRE_PITCH` 3.5、`Ballistics.M1_RANGE` 72；持枪参数 `GunPose.MODEL_FOV_AIM_M1` 45（TaCZ AK47）。**改模型必跑 `tools/m1_garand_gen.py`，再照打印值同步这几处** |
| **瞄具挂点高度 / 举枪对心** | `weapon/WeaponMount.java`（`SIGHT_Y` = 照门顶/准星顶/**导轨齿顶** = 3.44、`AKM_DOT_Y` / `AKM_SCOPE_Y` / `akmAimDy`）—— **必须**与生成器 `akm_v3.py` 里的 `SIGHT_Y` / `RAIL_LIFT` 及 `build_dot_sight` / `build_scope_4x` 的注释值一致 |
| **红点 / 倍镜显示逻辑** | `client/AkmGeoModel.java`（`sightNow` 隐藏骨骼 + 举枪位移）+ `client/ClientEvents.java`（`scoping` / `drawRedDot` / `drawScopeOverlay`） |
| **枪口/抛壳位置、射击方向** | `weapon/WeaponMount.java`（`AKM_MUZZLE` / `AKM_EJECT`）+ `AkmRifleItem.fire()`；子弹从模型点出发、朝准星收敛点飞（收敛上限 = **归零距离**：举枪 16 / 腰射 24 格，`tools/_akm_ballistic.py` 验算） |
| **手持动作幅度 / 速度** | `client/WeaponAnim.java`（冲量大小与衰减）+ `client/WeaponPose.java`（折算成 display 增量的数值） |
| **后坐幅度 / 镜头反馈强度** | 各 `client/*GeoModel.java` 的 `KICK_BACK` 与 `kick` 计算（AKM 1.35px / 弩 0.95px）；`camera` 骨骼只在 `firing()` 时叠加，换弹期间镜头必须为零 |
| **谁的手持变换被接管** | `client/WeaponHandGrip.java`（`applyForgeHandTransform` 的返回与基准平移）+ 各 `client/*ItemClientExtensions.java` |
| **骨骼该不该被推（渲染语境）** | `client/AkmGeoRenderer.java#isHand` + 各 `*GeoModel.handPass`：GUI 图标 / 掉落物 / 展示框一律不推 |
| **双手持枪的手臂摆位** | `client/WeaponArms.java`（肩点 / 臂长 / 握把锚点）+ 各 `*GeoModel` 里的手部目标点；离线核对 `tools/_armstory.py` |
| 手持动作是否生效 | `client/AnimatedWeaponModel.java` + `ModClient.onModifyBakingResult`；日志里会打“手持动作动画已启用：包装了 N 个武器模型” |
| AKM 弹匣容量 / 换弹时长 / 射速 / 散布 | `weapon/AkmRifleItem.java`（`MAG_SIZE` / `RELOAD_TICKS` / `FIRE_INTERVAL` / `fire()`） |
| 弩的倍镜倍率 | `weapon/CrossbowWeaponItem.java` 的 `SCOPE_ZOOM`（`4.0F` = 4 倍）；开镜 FOV 由 `ClientEvents` 用 `1/SCOPE_ZOOM` 计算 |
| **弩上弦 / 装填时机** | `weapon/CrossbowWeaponItem.java`：`RELOAD_TICKS`（上弦时长）、`tryStartReload()`（真正开始上弦，只有 R 键与右键两个入口）、`serverFire()`（击发后**只复位不复装**）、`cocked()`（图标/弩箭显隐就靠它） |
| 手雷拔销时长 / 引信时长 / 投掷力道 | `item/GrenadeItem.java`（`PIN_TICKS` 20 / `FUSE_TICKS` 100 / **`AUTO_BACK_TICKS` 30（刚拔完就松手 ⇒ 自动插回销）** / `THROW_LIFT_DEG` 上抬角 / `THROW_INACCURACY`）；**各弹种初速**在 `FragGrenadeItem`（1.30）与 `FlashbangItem`（1.38）的构造参数 |
| **手雷动作与手（拔销/投掷/左手拉环）** | `client/GrenadePose.java`（move 骨骼姿态 / 左右手模型点 / 手雷专用肩点）+ `client/WeaponArms.renderGrenade`；离线故事板 `tools/_gren_story.py mud\|flashbang` |
| 手雷引信、伤害、效果半径 | `entity/GrenadeEntity.java` |
| 三武器的有效射程与超距下坠 | `weapon/Ballistics.java`（`AKM_RANGE` / `BOLT_RANGE` / `BOW_RANGE` 与各 `*_IN_RANGE_GRAVITY`） |
| 武器手持姿态 / 物品栏图标大小 | 各 `models/item/*.json` 的 `display`，或跑 `tools/scale_weapons.py` |
| **弩弓臂内收 / 后弯 / 长短 / 弦粗细** | `client/CrossbowGeoModel.java` 的 `FLEX_DEG` / `FLEX_BACK` / `FLEX_PX` / `FLEX_PZ`（**内收量**与**弦拉动量**是两个自变量：上膛后 flexAmt=1、draw=0 ⇒ 弓臂保持内敛）；**弓臂长度/粗细**与**弦/弦心/尾羽的尺寸**在 `tools/crossbow_vox.py`（`LIMB_SX` / `LIMB_SY` / 画弦处的 `th` / 弦心与尾羽的 box）；`SKIP_MESHES` 决定哪些参考网格**不**生成方块（弦与线缆必须跳过，否则就是“又厚又分叉”）（改完跑生成器，它会把新的 TIP_X / FLEX_PX / FLEX_PZ 打印出来；再手动装 `crossbow_geo.*`）|
| **第一人称手臂大小 / 位置** | `client/WeaponArms.java` 的 `SHOULDER_R/L`（必须放在画面外，否则一片色块挡住枪）、`THICK`、`ROLL_R/L`；离线故事板 `tools/_armstory.py akm|crossbow` |
| **开火时的视角反馈** | `client/AkmGeoModel.java#zeroCamera`（清零 = 不点头）+ `client/ClientEvents.java#applyAkmCamera`（camera 骨骼→视角的管道）；要做「后坐上跳」就在 `computeMovePose` 里用冲量自己做 |
| **月相效果** | 颜色（月亮/光晕/天顶/地平线/雾色/全屏叠色/尘埃）全在 `moon/MoonPhase.java` 枚举里；蓝月幸运 / 黄月催作物 / 血月不眠 + 天亮收尾在 `moon/MoonBlessings.java`；四波尸潮在 `moon/MoonManager.java`；改配色跑一遍 `tools/_moonsky_mock.py` |
| **月相出现概率 / 随机规则** | `moon/MoonManager.java`（`DEFAULT_MOON_CHANCE` 0.25、`DROUGHT_GRACE` 10、`DROUGHT_STEP` 0.01、上限 0.60）+ 存档字段 `MoonPhaseData.moonChance`（也可用 `/hexalunar moon chance` 改） |
| **新增月相 / 改指令** | 枚举加一项（`moon/MoonPhase.java`：7 个颜色参数 + `superMoon`）+ `lang` 补 `moon.<id>` / `moon.title.<id>`；指令树在 `moon/MoonCommands.java` |

---

## 七、更新日志（本次开发）

> 版本 `1.0.0-r121`

- ★★ **r121：修「子弹看不见」（只占格子一小角）+ AKM/AWP 拉栓改右手、抛壳靠右**

  **① 3D 物品模型的几何必须居中在 (0.5, 0.5, 0.5)**（用户截图：子弹挤在格子右下角一小块，
  看上去就是「看不见」）：MC 渲染物品模型时会先 `translate(-0.5, -0.5, -0.5)` ——
  它**假定模型几何占满 `(0,0,0)~(1,1,1)` 这一个方块**，靠这个平移把方块中心摆到格子中心。
  而弹药的**原点在几何中心**（坐标约 ±4.2 像素 = ±0.26 格）⇒ 再被减 0.5 格就整体跑到
  格子**左下后方**去了。
  · 为什么 display 的 `translation` 补不了：`ItemTransform.apply` 的顺序是
    **先 translate、再 rotate**，而旋转是绕模型原点的 ⇒ 平移补不了旋转后的偏移，
    必须在**几何**里偏移。
  · 改法：`tools/ammo_v3.py` 新增 `center_on_grid()`，把所有元素的 `from/to` 与
    `rotation.origin` 一起 **+8 像素（= +0.5 格）** ⇒ 几何中心正好落在 `(8, 8, 8)` 像素。
  · ★ 这个坑在 r118/r120 没暴露，是因为那时模型加载失败、MC 画的是「缺失模型」占位（全格大）；
    一旦模型能正常加载，居中问题才显现出来。

  **② AKM 拉栓从「左手」改到「右手」**（用户：「akm，awp 拉栓应该都在右手位置」）：
  拉机柄在枪身**右侧**（`ARM_BOLT.x = +0.70`），而它一直是由 `leftHandPx` 驱动的
  ⇒ 屏幕上看到的是「左边那只手在拉栓」。现在拉机柄交给新增的 `AkmGeoModel.rightHandPx`，
  **左手只管弹匣**（插完就回护木）—— 与 AWP / Kar98k / 莫辛 / M1 的分工、
  以及真枪 AK「左手换弹匣、右手拉机柄」的操作完全一致。

  **③ 弹壳从更靠右的地方起飞**（用户：「抛壳也一样（在左侧）」）：
  弹壳骨骼自己的 pivot 在**枪的**坐标系里已经是右侧，但枪身被 display 往屏幕左摆了 5/16 格，
  结果第一帧看上去仍贴着中线 ⇒ 新增 `CASE_X0` 起始偏移：
  AKM **+0.20**（从 x ≈ 1.15 起飞）、AWP **+0.40**（从 x ≈ 0.60，已在机匣右壁外面）。
  世界抛壳点同步外移：AKM `0.95 → 1.05`、AWP `0.78 → 0.92`；
  AWP 拉机柄握点也外移一点（`BOLT_GRIP_DX` 0.70 → **0.82**）。

  **④ 左侧/右侧的坐标系依据**（免得下次再猜）：`WeaponMount.toWorld` 里
  `lx = s*ARM_X + v.x` 乘的是 `right = look × up`（射手右侧），`AKM / AWP` 的
  `firstperson_righthand.rotation` 都是 `[0,0,0]`，`WeaponArms.SHOULDER_R.x = +0.55`
  ⇒ **模型 +X = 相机 +X = 屏幕右侧**（数学上确认过）。

- ★★ **r120：修「弹药在物品栏里是紫黑方块」**（用户截图：`.338` / `7.62×54R` / `.30-06`
  三格全是品红黑格）。**两个独立的坑，都是 r118 引入 3D 物品模型时埋的**：

  **① `rotation` 角度非法（真凶）**：MC 的 `BlockElement` 只接受
  **-45 / -22.5 / 0 / 22.5 / 45** 五个角度值（`BlockElement$Deserializer` 里硬编码），
  而八棱柱用 `angle = i*45` 生成 0/45/90/135/… ⇒
  `JsonParseException: Invalid rotation 90.0 found` ⇒ **整个模型 JSON 解析失败**。
  ⚠️ 游戏日志的表现极具误导性：
  `Failed to load model hexalunar_calamity:models/item/ammo_338.json` +
  `Unable to load model … FileNotFoundException: …ammo_338.json`
  —— 看着就是「文件没打进 jar」（实测**在** jar 里，md5 也对），
  真因藏在两条日志之间的**异常堆栈**里。查这类问题一定要带 `-Context` 看堆栈。
  · 改法：不用 90/135/… 去「转」板——法线朝 ±Z 的边用「薄在 Z」的板、朝 ±X 的边用
    「薄在 X」的板（靠 `from/to` 换轴向，而不是转 90°）、斜边绕**板自身中心**转 ±45°
    （135° 与 −45° 形状等价）⇒ 8 块板只用 0/±45 三个合法角度就拼出正八边形，
    几何与旧版**逐像素一致**（新旧渲染对比验证过）。
  · 生成器新增 `check_rotations()` 自检：非法角度直接抛异常，不再流到游戏里。

  **② `parent: item/generated` 会吃掉 elements**：`item/generated` 的根模型是
  `builtin/generated` ⇒ `ModelBakery` 会调 `ItemModelGenerator` 重新生成元素，
  而那个生成器只认 `#layer0..#layer4` 纹理（我们的面引用 `#0`）⇒ 产出 elements 为空的模型。
  · 改法：新增 `models/item/ammo_3d_base.json`（`parent = block/block` + 完整的物品
    display 八姿势），三个弹药模型改 parent 它。
  · 连带：变成 BlockModel 后贴图走**方块图集** ⇒ 在
    `assets/minecraft/atlases/blocks.json` 登记 `item/ammo_338` / `item/ammo_762_59` /
    `item/ammo_762_61` 三个 sprite（与 OBJ 武器贴图同一套机制）。

  **③ 新增体检脚本 `tools/ammo_audit.py`**：扫所有 `models/item/*.json` 里**带 elements**
  的模型，报告 parent 是否会触发 ItemModelGenerator、rotation 角度/轴是否合法
  （当前只有三颗弹药是 3D 物品模型，全部 OK）。

- ★★ **r119：十字弩重新设计 —— 弦恢复平行线 / 弓臂向外扩展 / 拉弦内收 / 左手上箭**
  （用户：「使用 blockbench 重新设计模型，**弦恢复平行线**，**弓臂向外扩展**，有拉弦动画，
  拉弦弓臂向内收缩，**左手上箭**，对照图 5 进行设计」）。

  **① 弦恢复平行线（根因修复）**：以前每段弦的**几何长度被写死 6.221**（前身是 r71 那根
  刻意做成 `tip_x + 0.85`「越过中线形成交叉」的「线缆」），而半跨只有 5.371 ⇒
  **未拉弦时两段弦就在中线附近重叠交叉**，渲染出来是「两条斜线」而不是一条弦
  —— 这正是用户说的「不是平行线」。现在每段几何长**改成正好 = 半跨**：
  静止时两段严格共线 ⇒ **一条笔直的平行弦**；而「拉满时长度不够」由**骨骼 scaleX** 补上
  （`hypot(x, DRAW_DZ) / TIP_X` ≈ 0.90 —— 真弓里对应凸轮放线）。
  ★ 顺手删掉了 `STRING_LEN` / `PHI_RAD` 两个常量：弦长不再固定，
  转角 φ 与伸缩量每帧由 `stringPhi` / `stringStretch` 解析求出。

  **② 弓臂向外扩展**：生成器 `LIMB_SX` 2.05 → **2.40**（跨度 10.32 → 11.61 模型像素）。
  弦半跨 / 锚点 X 同时**改用弓臂网格的外缘**（原来取参考网格里那条比弓臂长 0.85 的
  string 网格）⇒ 弦端点正好搭在弓臂梢（凸轮）上、不再悬在弓臂外面：
  `TIP_X` 5.371 → **5.805**。

  **③ 拉弦动画（弓臂向内收缩）**：`nockTravel` 改成解析式
  `锚点平面位移 + draw·DRAW_DZ`（拉满 = **1.80** 模型像素；旧版用固定弦长反解，
  实际拉到 3.12 像素、远超设计值）；弓臂仍绕「贴导轨的内端」内转 **13°**、整体后滑 0.35
  ⇒ 外端**向内 + 向后**收，上膛后保持内敛、击发才弹回。

  **④ 左手上箭**：弩箭骨骼在 p ∈ (0.70, 0.84) 期间**跟着左手位移**从导轨下方升到箭槽
  （旧版要等到 p > 0.84 才在导轨上凭空出现，手是空着比划的）；
  `leftHandPx` 因此拆出「指定进度」重载，避免箭比手晚一帧。

  **⑤ 规模与自检**：模型 824 → **953 方块**（15 骨骼）；生成器新增两条自检：
  「拉满时两段弦的内端落在弦心」「静止时两段共线」（不过就退出码 1）。
  预览用 `tools/geo_texview.py`（正前方 `--yaw 0 --pitch 0` 看弦是不是一条直线，
  斜视 `--yaw 20 --pitch 25` 看弓臂外扩与弦端点）。

- ★★ **r118：三种弹药的模型重新设计（2D 图标 → 3D 立体子弹）**
  （用户：「**.338，7.62x59，7.62x61 子弹模型需要重新设计并建模**」）。
  以前 `.338` / `7.62×59` / `7.62×61` 都是 `item/generated` 的**平面图**（一张 16² png
  里画两发斜放的子弹），拿在手里、扔在地上、放进展示框都是**一张纸片**。
  现在换成**真正的 3D 物品模型** —— 用原版 `elements`（**不动 Java、不加 GeckoLib**）。

  **① 生成器 `tools/ammo_v3.py`**：
    1. **造型**（从下往上）：底缘（**八棱盘** + 底火）→ 壳身（**八棱柱**，8 块绕 Y 轴
       旋转的薄板 —— 与武器上的八棱枪管 / 镜筒同一套审美）→ 壳肩收口 → 弹头
       （三段递减 + 尖端）。共 20 个元素。
    2. **原点放在几何中心**：物品模型的 `(0,0,0)` 在物品栏里就是格子中心，
       从 `y=0` 往上长的话整颗子弹会吊在格子上半部（第一版就踩了）。
    3. **三种弹按真实口径区分**（1 模型像素 ≈ 11 mm）：
       · `.338 Lapua`（8.6×70 mm）：总高 **9.00** 单位（56% 格子）
       · `7.62×54R`（莫辛 / Kar98k）：总高 **8.00**；★ 它是**凸缘弹**，底缘单独放大一圈
       · `.30-06`（7.62×61，M1）：总高 **7.80**
       ⇒ 拿在手里一眼能分出型号。
    4. **贴图**各自 64×64、逐面 UV（脚本自己装箱）：黄铜壳身带柱面明暗、铜被甲弹头、
       底缘下表面画一圈深色底火。

  **② 新工具 `tools/jsonmodel_view.py`**：离线渲染**原版 JSON 物品模型**（不用开游戏）——
     读 `elements`（含绕 Y 轴旋转）→ 背面剔除 → **按元素**排序（按单个面排序会在小方块
     交错时画错层）→ 正交投影 + **棱边描线**（不描线的话「平均色填面」会把八棱柱糊成
     一根方柱，根本看不出形状）。`--yaw / --pitch / --zoom / --size` 随便转。

  ⚠️ 两个坑（都踩过）：
    · 壳肩 / 壳颈的方块尺寸**必须小于八棱柱的内切圆**（`case_d × 0.924`）——
      用 `case_d − 0.10` 仍比内切圆宽，会从筒壁里凸出来。
    · 收口别拆成一堆小段（`sh0/sh1/neck/tip0/tip1/tip2` 六段）：等轴视角下每段的顶面
      都是一片「斜片」，整体看着很碎 —— 三段（肩 / 弹头主体 / 尖）就够。

- ★ **r117：修「倍镜有明显间隙」**（用户莫辛-纳甘游戏截图标注「倍镜有明显间隙修复它」）。
  **根因**：莫辛 v3 的镜座（`sc_mnt`）**只在装填口之后**（`PORT_Z1…RCV_Z1`）有一块，
  镜筒在**机匣前半**那一大段下面是空的 —— 那里只留了一条矮导轨 `sc_rail_f`（顶到 2.34），
  而镜筒底在 `SCOPE_Y − SC_RO = 2.96` ⇒ 中间 0.62 的缝在玩家那个斜下视角里能**穿过枪身看到背景**。
  **修法**：
  1. **莫辛**（`tools/mosin_m9130_v3.py`）：补一段与机匣同宽的支架 `sc_mnt_f`
     （装填口**之前**、从 `RCV_TOP` 一直托到镜筒底），原来那条矮导轨被它取代；
     **装填口（`PORT_Z0…PORT_Z1`）上方仍然开敞** —— 压弹那一发要从那儿垂直落进弹仓，不能堵。
  2. **AWP**（`tools/awp_v2.py`）：镜座从「两个 0.44 宽的窄环座」改成**两段长座**
     （`sc_mnt_f` / `sc_mnt_b`，装填口前后各一段，x ±0.30、从导轨顶连到镜筒底）；
     顺带去掉「镜环」—— 镜筒现在是一根干净的等径筒 + 两段座（面数 1086 → 990）。
     装填口那段留空：弹匣里那一发要从那儿看得见，而机匣右壁的抛壳窗也在同一段 z 上。
  3. 用 `geo_texview.py --yaw 345 --pitch 18`（玩家那个斜下视角）出图逐轮核对 ——
     这个角度才看得见「镜筒与枪身之间的缝」，侧视图看不出来。两个生成器自检 **0 失败**。

- ★ **r116：据用户游戏截图修两处**（截图标注：「倍镜看起来有明显分叉」＋「所有武器自动抛壳为
  绿色箭头位置，抛壳方向应该为蓝色箭头位置」）。
  1. **抛壳特效回到枪身右侧**：r115 把 `WeaponMount.AWP_EJECT` 的 x 从 0.90 压到 **0.30**
     （几乎回到枪身中线）—— 屏幕上看着还是「从枪身中间冒出来」，用户再次反馈。
     现在五把枪统一取**机匣半宽再往外一点**（模型 **+X = 射手右侧**，这条从 r107 起就是对的）：
     AKM 0.95（原值）/ AWP **0.78** / Kar98k 0.55→**0.80** / 莫辛 0.62→**0.90** / M1 0.33→**0.85**。
     模型内的空壳位置（r115 挪到右侧抛壳窗）保持不动。
  2. **倍镜不再「分叉」**（`tools/awp_v2.py`）：镜筒原来有四段不同外径 —— 物镜 `SC_RO+0.05` /
     变倍环 `+0.03` / 目镜 `+0.03` / **镜环 `+0.07`** ⇒ 四个台阶；从玩家那个斜下视角看就是
     「筒上又叠了一层」（用户截图里那个分叉）。现在**整根筒的外径统一**（最粗最细只差 0.02），
     镜环也几乎与筒齐平（只靠颜色区分）；镜座从「两根细立柱」加宽成**整块座**
     （x ±0.30 / z 0.44，筒与机匣之间是实在的座子）。
  3. 用 `tools/geo_texview.py … --yaw 345 --pitch 18`（= 玩家第一人称那个斜下视角）逐轮出图核对 ——
     这个角度才是看镜筒层叠的角度，侧视图看不出来。模型自检仍 **0 失败**。

- ★ **r115：修「武器抛壳位置在左侧」**（用户：「修复武器抛壳位置为右侧，不是左侧」）。
  **根因**：最近重建的三把枪（`tools/awp_v2.py` / `tools/m1_garand_v2.py` /
  `tools/mosin_m9130_v3.py`）都把空弹壳（`casing` 骨骼的方块）放在了**膛内中线 x=0**，
  而更早的版本与 `kar98k`（pivot x = **0.30**）都放在**机匣右侧的抛壳口**
  —— 斜后上方看过去，弹壳就是从「枪身中间/偏左」冒出来的（用户看到的就是这个）。
  上一次「抛壳改右侧」的修复（b39c2db）改的是**世界粒子方向**（删掉了 `ejectCasing` 里
  那句 `.scale(-1)`），当时提交信息里还特意记录了「各枪 `casing` pivot 全在 +X
  （awp 0.32 / kar98k 0.30 / m1 0.42 / mosin 0.62）」—— 这次是**模型端**又退回了中线。
  **修法**（三把枪统一，弹壳几何与骨骼 pivot 一起挪）：
  1. **AWP**：机匣右壁在抛壳窗位置**留洞**（`rcv_r` 拆成前后两段 `rcv_r_f` / `rcv_r_b`，
     窗口 z 与顶部装填口一致 = −2.90…−2.10），空弹壳挪进右窗（`CASE_X = 0.20`，
     z −2.85…−2.25）；`WeaponMount.AWP_EJECT` 从 `{0.90, 1.39, −0.60}`（机匣右**外**侧、
     机匣**后**部，与模型对不上）改到与模型同源的 `{0.30, 1.575, −2.50}`
     ⇒ 世界里的黄铜壳也从右侧抛壳窗出来。
  2. **M1 加兰德**：空弹壳挪到**右侧抛壳口**（x 0.10…0.30、z −1.65…−1.15，正对右壁缺口
     z −1.75…−0.45）；它的 `M1_EJECT`（0.33, 2.88, −1.05）本来就在右侧，不用改。
  3. **莫辛-纳甘**：右壁同样开**抛壳窗**（`rcv_r` 拆两段，窗口 = 装填口 z −3.40…−2.25）
     ＋ 空弹壳贴右内壁（x 0.00…0.26）；`MOSIN_EJECT`（0.62, 2.10, −1.95）不变。
  4. **顺带**修 `awp_v2.py` 自检的「悬空件」误报：`touch()` 先把每个轴按 `[min, max]`
     归一化再比区间 —— 否则 `(_sx*0.23, _sx*0.07)` 这种**逆序**坐标在 `_sx=−1` 时
     会被当成空区间，于是 `mz_slotr0/r1`、`bp_foot_r` 被误报为「悬空的孤立方块」。
     AWP 生成器自检现在 **0 失败**。

- ★★ **r114：AWP 整体重建（模型 v2）+ 动作与持枪动画照 TaCZ 的精密国际 `ai_awp`**
（用户：「根据图片用 blockbench 建模……**枪管为圆形空洞枪管**、**弹匣可以看见子弹**、
**拉完栓看不见弹匣里面子弹**、**瞄准镜也是圆型空心内部透明玻璃和十字线**……
**打一下拉一下栓把空弹壳带出抛出，带入新的子弹推入发射**……**套用 TaCZ 精密国际 awm 的手持动画**」）。

  **① 新生成器 `tools/awp_v2.py`**（照参考图 `模型/AWP_Printstream_Minecraft` 重建，**18 骨骼 / 180 方块 / 512² 逐面 UV**）：
    1. **枪管 = 一整根八棱空洞壁**：外径全程 0.250 / 内孔 0.125、内壁再贴 **8 段膛线**，
       「枪口→膛底」整条轴线上没有任何方块（自检逐点扫过），膛底一颗黑堵头 ⇒ 看进去是**有膛线的深孔**；
       枪口是**八棱制退器**（两道泄气槽只开在两侧面，不堵膛）。
    2. **瞄准镜 = 空心镜筒 + 整片透明圆镜片**：筒身只按变倍环分两段、首尾相接，
       前后镜片**背景 alpha = 0**（方角直接丢弃 ⇒ 是圆的不是方的），目镜那片刻**十字分划 + 中心红点**；
       镜座改成坐在机匣后桥上的**一整块实心块**（不再有「两根细腿」的缝）。
    3. **弹匣里 5 发看得见的子弹**：`round_in`（最上一发）+ `mag_r1..mag_r4`，**5 根独立骨骼**。
    4. **自检**（`tools/_awp2check.py` → `build/_awp2check.txt`）：枪口↔膛底轴线是空的 OK ·
       镜筒内通 + 镜片整片透明含十字线（透明 106 px / 十字 48 px / 无多余实心块）OK ·
       5 发都在匣内且不穿底 OK · **闭锁盖住抛壳口、后拉 1.90 后让开** OK。

  **② Java 端适配 v2 骨骼**（`client/AwpGeoModel`）：
    · 旧的 `magazine_rounds`（一根骨骼装 3 个方块）**作废**，改成按 NBT 余弹一根根控 `round_in` / `mag_r1..mag_r4`：
      **闭锁时全藏**（枪机体盖住装填口，从外面本来就看不见）→ **拉栓时露出来**
      （托弹板把最上一发顶到弹匣口）→ **枪机回位时把它推进膛，推到底就从弹匣里消失**
      ⇒ 正好是用户要的「弹匣看得见子弹 / 拉完栓看不见」；打一发少一发也自动跟着 `HlcMag` 走。
    · 拉机柄握点跟着新几何挪到球头中心 (1.31, 1.365)，抛壳「抽出距离」跟枪机行程一起收到 1.90。

  **③ 拉栓 / 换弹照 TaCZ `ai_awp`**（TaCZ 里没有单独的 `awp`，只有**精密国际 `ai_awp`**，
    它的 `ai_awp_display.json` 写了 `use_default_animation: "rifle"` ⇒ 持枪就是**通用步枪**那一套）：
    · `bolt` 段：拉机柄转 **60°**（取 62°）、**整枪 rotation Z 11.87°（向右侧倾）**、
      rotation X 4.59°（微抬）、position Y −0.80（按枪长折半取 −0.40）——
      **枪与双手一起歪**（走 `move` 骨骼 + `GunFrame`，手臂不会脱手）
    · `shoot` 段：枪口上抬 7.94° ⇒ `AWP_FIRE_PITCH` 6.0（另有一路镜头后坐，所以不取满）
    · `reload_tactical` / `reload_empty`：弹匣是**翻转着**脱出的（它的 rotation Z 到 −131°）⇒ 我们取 45°
    · 枪机后退量不照搬（TaCZ 那把枪更长）：用新几何自检扫出来的 **1.90**

  **④ 持枪动画 = TaCZ 通用步枪 `rifle_default`**（新增 `WeaponMount.awpHoldPose`，与 M1 同一份数值）：
    idle 呼吸（rotX ±0.8° / rotY ±0.5° / rotZ ±0.9° / posY ±0.10）、walk 轻摆，
    **冲刺时枪压低并转到射手右侧**（rotX −35.6° / rotY −44.6° / rotZ 31.4°，位移按枪长 ×0.63）；
    抵肩时全部收掉（镜筒光轴必须精确落在屏幕中心）。
    **枪口 / 抛壳点的世界坐标走同一份姿态**（`WeaponMount.awpHoldPoint`）⇒ 跑动时枪口焰与弹道不会与枪身脱开。
    新工具 `tools/_ai_awp_times.py`（看 TaCZ `ai_awp` 某段的关键帧 / 长度）。

- ★ **r113：M1 加兰德的弹夹盖改成「整体平行抬起」**（用户：「漏匣上盖是平行的」「打开时也保持平行」「抛壳也如此」）。
r112 是绕机匣后缘**翻开** 55°，这轮改成**沿 Y 竖着平抬 0.40 像素**，**三个角度恒为 0** ⇒
关上时与机匣顶 3.00 齐平、打开时和关上时**同形同向**（俯视就是一块升起的平板）。
  1. **机匣顶分前后两段**：前段 z −1.98…−0.78 = **可抬起的盖板**（漏夹就从这儿压进去），
     后段 z −0.78…1.10 = **实体顶桥**（不动，照门座坐在它上面）—— 真枪也是这个布局
     （弹夹口只在照门座**前面**，座子后面是实心机匣桥）。抬升是纯竖直运动 ⇒
     与照门座 / 觇孔环（z −0.70…0.14，y 2.96…3.92）**零干涉**。
  2. **抛壳走的也是这条让出来的口子**：抬 0.40 后盖板底 3.28 − 机匣顶 3.00 = 缝 **0.28**，
     黄铜空壳直径 0.20 ⇒ 出得来；空壳照旧从**射手右侧（+X）** 抛（`CASE_VX/VY/BACK` 没动）。
     为了不刮到正在升起的盖板：**盖板先抬（枪机进度 0.26 抬满）、空壳后出现（0.14 起）**，
     空壳本体从 z −2.45…−1.95 后移到 **−2.50…−2.00**（就位在弹膛里）。
  3. **新增自检**：`tools/m1_garand_v2.py` 自检 5 验「盖板抬起后与机匣顶的缝 ≥ 空壳直径」
     「盖板与实体桥齐平无缝隙」「漏夹落在盖板开口内」，**自检 5b 用 Java 同一套公式复算
     空壳整条飞行轨迹**，确认全程不碰盖板；新工具 `tools/_m1check.py` 一键跑完并落成 UTF-8 报告
     `build/_m1check.txt`（26 行自检、**0 失败**）。
  4. **顺带**：照门高低旋钮由方块改成**八棱圆盘 + 一字槽 + 中心螺丝**（同参考照）；
     `ARM_CLIP`（换弹时右手下压点）的 z 由 −0.90 改为 **−1.40**（正对盖板开口中心）；
     `M1GarandGeoModel` 里删掉 `COVER_DEG`，换成 `COVER_LIFT = 0.40F` +
     `cover.setPosY(开合量 × COVER_LIFT)`（`staticPose` 也一并归零）。
  5. 版本 `1.0.0-r113`，jar `hexalunar_calamity-1.0.0-r113.jar`（**BUILD SUCCESSFUL**，Q 版 q3 同步重建）。

- ★★ **r112：M1 加兰德整体重建（模型 v2）+ 三轮用户标注修复**。新生成器 `tools/m1_garand_v2.py`
  （旧的 `m1_garand_gen.py` 已在文件头标注「已被取代，别跑」），12 骨骼 / 67 方块 / 402 面 /
  512² 逐面 UV，几何与贴图全部重做：
  1. **空心圆管枪管**：`tube_z()` 用 8 段斜置小盒拼八棱**空心**管（外径 0.21 / 内孔 0.11），
     枪口正视是一圈管壁 + 中间黑洞（孔底另有黑色八棱堵头 ⇒ 有膛深）。
  2. **照门 = 圆型空心 + 透明玻璃 + 十字线**：`ap` 八棱空心环（内孔 0.62 单位）+ 孔内 `rs_glass`，
     该方块贴图**背景 alpha = 0**（cutout 直接丢弃），只画暗蓝镜片边 + 1px 深色十字分划 + 中心亮点。
     **觇孔圆心 = 准星片顶 = 模型 Y 3.44**（r108 是 3.10）；`python tools\_ads_check.py m1_aim`
     验算仍是 **0.00% / 0.00%**（枪管轴 −8.27%）。
  3. **弹夹盖 `cover`**（机匣后端铰链，绕 X 转 +55° 翻开）：每打一发随气动枪机翻开一下放空壳、
     装填完成自动合上、**打空不合上**（空仓挂机）。用户标注「这块多余」⇒ 已把盖板改成
     **与机匣顶齐平、不比机匣宽**（x ±0.46 / y 2.88…3.00），删掉两道加强筋与唇边。
  4. **漏夹 + 8 发可见子弹**：`clip_in`（侧壁只包下半截）+ `clip_rounds`（8 发黄铜子弹，一发 0.0755）。
     装填时整只抬到机匣上方 1.75（y 3.63…4.32）⇒ 8 发全看得见；盖上/压进去后 Java 把两根骨骼
     一起隐藏 ⇒ 合上看不见里面。★ 漏夹整套**压在机匣内部**（底 1.88 ≥ 弹仓井底 1.55、
     顶 2.574 ≤ 枪机底 2.58）—— 用户标注「这个位置不要漏出来」就是它原来下半截从机匣底下伸出来。
  5. **没有外露弹匣 / 拉机柄 / 导气杆**（用户三轮标注）：删 `magazine` 底板方块、删凸出的拉机柄、
     删右侧那根长导气杆（「这个位置也不需要」）；侧边只剩木材与枪管。
  6. **枪身收窄约 23%**（「枪身可以细一点」）：机匣外半宽 0.60→0.46、漏夹口 0.24→0.20、枪托 0.66→0.54、
     护木 0.56→0.46、枪管外径 0.25→0.21、觇孔环 0.58→0.48。**轴线 Y=2.30 与瞄准线 3.44 一点没动**
     ⇒ `WeaponMount.M1_T*` 不改，只有 `M1_EJECT` 的 x 跟随抛壳窗 0.42→0.33。
  7. **枪托与握把是一整块木头**（「M1 加兰德没有握把和枪托一体」）：去掉原来那块独立深色握把块，
     枪托改成 细托颈（1.40）→ 逐渐加高的托底（2.20）连续三段；右手握点移到托颈前下角 `(0, 1.45, 2.55)`。
  8. **持枪动画 = TaCZ 通用步枪 `rifle_default`**（TaCZ 里没有 M1）：取 idle（呼吸 rotX ±0.8°/rotZ ±0.9°/
     位移 ±0.10）、walk_aiming（走路轻摆）、run（**枪压低并转到射手右侧** rotX −35.6°/rotY −44.6°/
     rotZ +31.4°，位置按枪长 38→21 折算 ×0.55）三段均值，写在 `WeaponMount.m1HoldPose`；
     **骨骼渲染与弹道共用同一份**（`m1HoldPoint` 用与 GeckoLib 渲染器逐字相同的
     `new Quaternionf().rotationXYZ(...)`），举枪时按 aim 整套收掉。
  9. 生成器自检新增：漏夹不许露在机匣外、机匣下方最低点、盖板张开会不会穿过觇孔环、
     镜片像素够不够画十字线；Q 版（`tools/qgen.py`）同步（clip/cover 不参与加粗，
     锚点改到管壁 —— 枪口轴心现在是空的洞）。
- ★ **据 `mod/logs` 现场日志修 Q 版「缺贴图」刷屏**：
  `Missing textures in model hexalunar_calamity_q:item/crossbow_hand_part:`
  → `hexalunar_calamity:models/crossbow`。根因：`build.gradle` 的 `prepareQResources`
  把基础命名空间搬成 Q 命名空间时**只替换 `**/*.json`**，`.mtl` 里的
  `map_Kd hexalunar_calamity:models/crossbow` 没换 ⇒ 指向已不存在的命名空间。
  现改成 `*.json / *.mtl / *.obj` 一起替换，并用 `tools/_jarread.py` 核对 Q 版 jar 里的
  `crossbow.mtl` 与 `textures/models/crossbow.png` 都对上了。
  日志里其余告警（`Object did not get ID it asked for`、`Missing data pack mod:hexalunar_calamity_q`、
  `Skipping Entity with id hexalunar_calamity_q:*`）都是「在同一个存档里来回装卸 Q 版 jar / 增删物品」
  的固有现象，不是代码 bug —— 想两个版本都玩请**各用一个存档**。

- ★ **据 `mod/logs` 的现场日志修掉三处问题**。日志是 **GBK** 编码的（`latest.log` / `debug.log`
  + 三个 `.gz` 归档），按 UTF-8 读会全是乱码；筛掉诊断行之后，属于本模组的其实只有 **8 行**。
  1. ★ **补回两个缺失的物品模型** —— 日志里唯一的资源级报错：
     `Unable to load model: 'hexalunar_calamity:ammo_762_61#inventory' … FileNotFoundException:
     hexalunar_calamity:models/item/ammo_762_61.json`（`ammo_box_762_61` 同）。
     r108 加 M1 加兰德时这两个物品的**注册、配方、战利品表、语言、贴图全齐了**，唯独漏了
     `models/item/*.json` ⇒ 背包与手里会渲染成紫黑「缺模型」方块。已照同族 7.62x59 补齐
     （`ammo_762_61.json` / `ammo_box_762_61.json`），现在 **28 个注册物品 0 缺模型**。
  2. ★ **`[HLCDIAG]` 诊断刷屏改成默认关闭**（`client/WeaponDiag`）：它是当初查「枪飘在手右上方、
     和手臂分离」时加的现场记录器，注释自己写着「正常玩可以无视」，但 `ClientEvents` 里是
     **无条件调用**的 —— 每秒往日志写一行，同时往游戏目录 `hexalunar_diag.txt` 追加一行
     （渲染线程上的阻塞文件 IO），而那个文件还会跨启动无限增长。现在只有加
     **`-Dhexalunar.diag=true`** 才记录；关闭时顺手复位累加器
     （`WeaponArms.externalPoseDelta` 用 `Math.max` 累加，没人复位会一路涨到 `Float.MAX`），
     开启时每次会话首次写入前先清空诊断文件。
  3. ★ **删掉「包装了 0 个武器模型」那层死代码**（`client/ModClient`）：`AnimatedWeaponModel`
     包装的认领函数 `kindOfModel()` **每一个分支都 `return null`**（AKM / AWP / Kar98k / 莫辛 /
     M1 / 十字弩 / 复合弓 / 手雷后来全改成了 GeckoLib 骨骼渲染）⇒ 循环一次都没进过、`wrapped`
     恒为 0，那行日志会把人往「这里坏了」带偏。已删掉死循环与误报日志，保留必须的
     `CrossbowPartModels.capture`，并清掉因此不再使用的 import 与 logger。
- **日志里还有、但不属于本仓库所以没动的**：`hcdservercore` 缺 `fake_ore` / `broken_fake_ore`
  模型、以及 20×20 非 2 的幂贴图（那是另一个模组 *Hallzmine's Crafting Dead Server Core*）；
  `Shader rendertype_entity_translucent_emissive could not find sampler named Sampler2`
  （本模组**没有任何 core shader 资源**，来自别的模组 / 资源包覆盖）；
  `Registry minecraft:item: Object did not get ID it asked for` 是**往已有存档新增物品**造成的
  Forge 注册表 ID 漂移 —— 被点名的正好是每一轮新加的物品（r106 是 kar98k / mosin /
  ammo_762_59、r108 是 m1_garand / ammo_762_61 / ammo_box_762_61），Forge 按名字重映射，
  **不是代码缺陷**；`Can't keep up! … 243 ticks behind` 是整合包进世界时的卡顿。
- **验证**：`gradlew compileJava --offline` 与 `gradlew build --offline` 均 **BUILD SUCCESSFUL**，
  产物 `hexalunar_calamity-1.0.0-r110.jar`（已确认 jar 内含两个新模型 JSON）。

> 版本 `1.0.0-r109`

- ★ **Q 弹版构建开关**：`gradlew build -Pqmode=true` ⇒ mod id **`hexalunar_calamity_q`**、
  显示名「六相月灾 · Q弹版」，与普通版**可以同时安装**（id 不同互不冲突）。代码只有一份，
  差别全在 `build.gradle`（`BuildInfo.Q_MODE`，javac 常量折叠 ⇒ 非 Q 版里 Q 分支的**调用点**
  直接消失，细节见下文「字节码级验证」）+ `src/qresources` 覆盖层；`prepareQResources` 会把
  基础命名空间的 `assets/` `data/` 整体搬到 Q 命名空间，再叠 Q 版文件。
- **Q 版资源**：Q 版 AKM 骨骼模型
  （`qresources/assets/hexalunar_calamity_q/geo/akm.geo.json` + 贴图 + 流光遮罩，
  `tools/q_akm_gen.py` 生成）、Q 版僵尸贴图（`tools/q_chibi_zombie_tex.py`）、
  Q 版自爆尸模型层（`client/QChibiZombieModel` / `QChibiZombieRenderer`，
  配 `client/Jelly` 的果冻晃动）。Q 版自爆尸的渲染分支由 `BuildInfo.Q_MODE` 选择
  （见 `client/ModClient#onRegisterRenderers`）。
- ★ **q2：Q 版 4 倍镜往后挪到机匣上**（用户实机截图反馈「倍镜太靠前，把它挪到红框里」）：
  Q 版第一版把 `scope_4x` 摆在了**护木正上方**（镜筒 z −7.10..−4.10、物镜座到 −7.30），
  而原版 AKM 的 4 倍镜是**骑在机匣盖后段**的（镜筒 −4.98..−3.50、底座 −5.30..−3.30）
  ⇒ 实机里就是「倍镜飞在枪管前面」。修法：`tools/q_akm_gen.py` 新增
  **`SCOPE_SETBACK = 2.70`**，把镜筒 + 两个镜座 + 两个镜环连同骨骼 pivot **整体 +z（朝射手）平移**：
  镜筒落到 **z[−4.60, −1.20]**、物镜座 [−4.60, −4.20]、目镜座 [−1.60, −1.20]。
  - **光轴仍是 `SCOPE_Y = 4.28`**，`WeaponMount.AKM_SCOPE_Y` 只认 Y、**Java 没有任何 z 依赖**
    ⇒ 一行 Java 都没改，开镜 FOV / 贴脸锚点不受影响（`AkmGeoModel#applySights` 只用骨骼名做显隐）。
  - 生成器结尾新增自检并打印：**镜筒前端让开红点**（−4.60 > 红点后端 −5.05 ✓）、
    **后端仍在机匣上**（−1.20 < 枪托前端 2.20 ✓）；想再微调只改 `SCOPE_SETBACK` 一个数
    （1.0 = 1 模型像素 = 1/16 格，变大更靠后）。
  - 出货前用 `tools/qjar_check.py` + 一段 `build/_jarscope.py` 核对**jar 里**的 geo 确实是
    `scope_4x z=[−4.60, −1.20] / pivot Y=4.28`（防止覆盖层没生效、把旧模型发出去）。
- ★★ **q3：Q 版造型铺满全部内容**（8 个模型 + 6 种特殊感染者），出货版本 `1.0.0-q3`。
  - **武器/投掷物统一由 `tools/qgen.py` 批量 Q 化**（不再一个个手搓）：AWP、复合弓、
    十字弩（871 方块那份 `crossbow_geo`）、闪光弹、手雷、莫辛、Kar98k、M1 加兰德
    （Q 版 AKM 仍是手搓的那份）。贴图同步做 Q 化调色（`Color×1.28 / Brightness×1.10 / Contrast×1.06`），
    流光遮罩沿用基础版。
  - ★ **为什么这样变胖是安全的**（Q 版最硬的约束是**锚点一个都不能动**）：
    <br>① 只放大 **X/Y**、**Z 一个面都不动** ⇒ 枪口端面 / 抛壳口 / 弹匣井 / 拉机柄 /
    箭杆出膛点全部原地不动（`WeaponMount` 里那些 `*_MUZZLE` / `*_EJECT` 直接受用）；
    <br>② 每个方块**绕自身几何中心**放大 ⇒ 所有高度中心不变 ⇒ **红点圆心 / 4x 光轴 /
    各枪 `*_SCOPE_Y` 逐字不动**（这是开镜时"瞄准线顶到眼睛"的参照）；
    <br>③ 只放大不缩小 ⇒ 任何原本在方块**内部**的锚点（握把/护木/弹匣 pivot 等）仍然在内部；
    <br>④ 骨骼名 / 骨骼数 / 每骨骼方块数 / pivot 全部保留 ⇒ GeckoLib 的换弹·拉栓·抛壳动画
    与各 `*GeoModel` 的程序化驱动**一行都不用改**；
    <br>⑤ 仿射变换保共面性 ⇒ 基础版没有共面重叠面的话，变胖后也不会新冒出 z-fighting。
  - **两处例外**：瞄具骨骼（`sight*` / `scope*` / `dot_sight`）**只加宽不加高**（`FLATY`）——
    它们的高度就是 Java 里的瞄具线，加高会把瞄准参照点顶偏；枪托尾段用 `tail=(z_from, k)`
    朝机匣收短（那一段没有任何锚点）。加粗倍率写在 `qgen.py` 的 `CONFIG` 里
    （步枪 `kx≈1.6 / ky≈1.5`、投掷物 `1.5/1.44`），想更 Q 就改这一张表。
  - **自检**：`qgen.py` 每跑一个模型都会逐条验（骨骼集合一致、方块数一致、每个方块 X/Y 中心没动、
    尺寸只增不减、Z 面没动、瞄具骨骼 Y 高度逐字不变、锚点仍在骨骼内），任何一条不过就**不写文件**、
    退出码 1；出货前再用 `build/_jarq3.py` 拆 **jar 里**的 9 个 geo 复核一遍
    （枪口点在骨骼内、瞄具骨骼 Y 未动、11 张贴图/遮罩齐全、两张怪物皮肤在）。
  - ★ **6 种特殊感染者全部 Q 化**（原来只有自爆尸）：
    - 僵尸系（自爆 / 弓手 / 桶 / 巨尸）共用 `QChibiZombieRenderer`，染色与体型沿用原配置
      （弓手 `0x59C46B`、桶尸 `0x6E6E78`、巨尸 1.9 倍且不带标识层）；
    - 骷髅系（冲刺 / 剧毒）新增 `QChibiSkeletonRenderer`：**几何复用同一套 chibi 大头矮胖身子**
      （`QChibiZombieModel.SKELETON_LAYER`），行为仍交给原版 `SkeletonModel`
      ⇒ 拉弓瞄准姿势不用自己写；皮肤是新的骨头版 `textures/entity/q_chibi_skeleton.png`
      （`tools/q_chibi_skeleton_tex.py`，同一张 UV 表：骷髅脸/眼窝/牙/肋骨）。
    - 「果冻」逻辑抽到 `client/QChibi`（无状态：走路挤压 + 小跳 + 受伤抖动 + 静止呼吸），
      两种渲染器共用；老存档里的怪一进游戏就变 Q，不碰任何 NBT。
    - 查原版签名踩的坑记一笔：1.20.1 的 `SkeletonRenderer` **不是泛型类**、写死
      `AbstractSkeleton`，而且它的构造器第 2~4 个参数是 **ModelLayerLocation**（不是模型实例），
      覆写的方法参数类型是 `AbstractSkeleton`（`javap` 核过才改对）。
  - 顺手把 Q 版 AKM 的红点镜片圆心从 4.075 校正到**恰好 4.07**（`AKM_DOT_Y`），
    现在 9 个模型的所有瞄具锚点都是逐字精确的。
- **这一轮做到哪一步（样板先行）**：只做了 **1 把枪 + 1 只怪**当样板 —— Q 版 AKM（`tools/q_akm_gen.py`）
  与 Q 版自爆尸（`client/QChibiZombieModel` / `QChibiZombieRenderer` + `tools/q_chibi_zombie_tex.py`），
  先把「Q 版造型」与「Q 弹晃动」两套机制跑通、上手看手感；确认后再把剩下 7 把枪 / 2 种投掷物 /
  6 种特殊感染者 / 图标与 HUD 整体铺开。**Q 版 AKM 保留了原 AKM 的全部锚点**
  （膛线 Y=1.75、枪口 z=−11.60、准星 3.44、光点 4.07、镜 4.28、抛壳口 (0.95,2.62,−2.30)、
  握把 (0,0.55,−0.15)、护木 (0,2.05,−6.30)、弹匣轴 (0,1.45,−3.78)、枪机 (0.70,2.64,−3.54)），
  所以**武器侧一行 Java 都没改** —— 同一套 `AkmGeoModel` / `WeaponMount` / `WeaponArms` /
  `AkmRifleItem` 直接驱动这个矮胖模型（`q_akm_gen.py` 结尾会把这些锚点逐条打印出来自检）。
- **Q 弹手感来自哪**（两处都只在 Q 版生效，见下面的字节码验证）：
  - **枪**：`client/Jelly` 弹簧（开火给冲量 `punch`，每 tick 按 0.82 衰减、1.15 刚度回位）
    → `GunPose.matrix` 绕握把做**挤压拉伸** `1+0.05j / 1−0.16j / 1+0.10j`，
    再叠 `0.055·j` 的 Y 向弹跳（`client/WeaponHandGrip#pushAds`）。开镜冲量 0.55、腰射 0.85。
    ★ 缩放只作用于**枪身矩阵**，手部摆位与弹道（`GunPose#transform`）不受影响
    ⇒ 不会出现「手被压扁」或弹道跟着偏。
  - **怪**：`QChibiZombieRenderer` 用走路相位做**无状态**的挤压拉伸
    （走路 0.11 / 待机 0.045 / 受击 0.16）与蹦跳（0.085），不依赖任何实体 NBT
    ⇒ 老存档里已有的僵尸也会一起变 Q。
- **怎么装 / 怎么切**：两个 jar **同名内容、不同 mod id**，实战里**建议一次只放一个**
  （同时装会出现两套创造模式页签与两批怪）：
  - 普通版：`gradlew build --offline` ⇒ `build/libs/hexalunar_calamity-1.0.0-rXXX.jar`
  - Q 弹版：`gradlew build --offline -Pqmode=true` ⇒ `build/libs/hexalunar_calamity_q-1.0.0-q2.jar`
  - 两个都丢进 `.minecraft/mods/` 也能起来（id 不同、属性修饰符 UUID 已错开），
    想切回普通版就把 Q 版 jar 移出 `mods/`。
- **要改名 / 改版号**：只动 `build.gradle` 里 qmode 分支的 `modId` / `modName` / `version`
  三个字面量 + `src/qresources` 下的目录名；Java 侧全部走 `HexaLunarCalamity.MOD_ID` 与
  `BuildInfo.Q_MODE`，**没有任何硬编码命名空间**（`SimpleArrowRenderer` / `StunEffect` /
  `CorpsePoisonEffect` 里的旧字面量也已换成 `MOD_ID`）。
  ★ 普通版那行 `version = '1.0.0-rXXX'` 必须留在**行首**（发版 CI 用 sed 读它），
  qmode 的覆盖写在它后面。
- **字节码级验证（`javap -v` 反汇编两个 jar 的 `ModClient`）**：两个 jar 的
  `onRegisterRenderers` 方法体里**都没有** `getstatic BuildInfo.Q_MODE` —— 常量在编译期就折掉了，
  不存在运行期分支：
  | jar | BOMBER_ZOMBIE 绑到的 lambda | 说明 |
  | --- | --- | --- |
  | `hexalunar_calamity`（普通） | `lambda$onRegisterRenderers$4` → `tintedZombie` | 原版僵尸渲染器 |
  | `hexalunar_calamity_q`（Q 版） | `lambda$onRegisterRenderers$5` → `QChibiZombieRenderer` | Q 版矮胖渲染器 |
  javac 仍会**留下没人引用的那个合成 lambda 方法体**（普通版里是 `$5`，Q 版里是 `$6`），
  它只存在于方法表、没有任何 `MethodHandle` 指向它 ⇒ **运行期零影响**，不必当成「没折掉」。
  另外 `onRegisterLayerDefinitions` 在两个 jar 里都无条件注册了 Q 僵尸的模型层
  （无害：普通版没有任何渲染器去取它）。资源侧则是**硬隔离**：
  普通版 191 条 `assets/hexalunar_calamity/**`、0 条 Q 命名空间；Q 版反过来
  （192 条 `hexalunar_calamity_q/**`、0 条基础命名空间）。
- ★ **出货前自检脚本 `tools/qjar_check.py`**（`python tools/qjar_check.py`，退出码非 0 即有 FAIL）：
  按 **jar 本体**体检，专治「构建成功但产物不可用」——
  1. **zip 完整性 / class 数量**：今天真踩过两次 —— `hexalunar_calamity-1.0.0-r110.jar` 曾出现
     「有资源、**0 个 class**」（两个 Gradle 构建共用同一个 `build/` 目录并发跑，jar 任务抓到了
     空的 classes 输出），部署到 `mods/` 的 `hexalunar_calamity-1.0.0-r109.jar` 则是**非法 zip**
     （1.1MB 截断包，Forge 会直接报无效模组）；
  2. `mods.toml` 的 modId / version / displayName 与 jar 内资源命名空间是否自洽；
  3. 扫全部 `.json` / `.mcmeta` / `.toml`，确认**零跨命名空间引用**（Q 版里不得残留
     `hexalunar_calamity:`，普通版里不得出现 `hexalunar_calamity_q:`）；
  4. Q 版样板资源（Q AKM 骨骼 + 贴图 + 流光遮罩、Q 僵尸贴图）是否就位、普通版是否混入；
  5. 有 `javap` 时反汇编 `ModClient`，确认常量折叠后 BOMBER_ZOMBIE 绑的是
     普通版 `$4`(tintedZombie) / Q 版 `$5`(QChibiZombieRenderer)。
  **并发构建会互相踩 `build/`**：跑完两个版本后最好各检查一次，或串行构建。

> 版本 `1.0.0-r108`

- ★★ **新武器：M1 加兰德（M1 Garand）半自动步枪**（`m1_garand`，`weapon/M1GarandItem.java`
  + `client/M1GarandGeoModel.java` + `tools/m1_garand_gen.py`）——按用户给的照片做的。
  - **模型**：`tools/m1_garand_gen.py` 程序化生成木托长枪（胡桃木托 + **上下两片木护木把枪管包住**，
    这是它与 Kar98k 最大的外观差别）+ 机匣 + **右侧长导气杆（op-rod）** + 大觇孔照门 + 机瞄 + 扳机护圈环。
    `geo/m1_garand.geo.json`（**10 骨骼 / 29 方块** / 128² 分带贴图 + 流光遮罩）、
    贴图 `textures/models/m1_garand_geo.png`。整枪 **20.9 模型像素 = 1.306 格**（枪口 z=−13.60、托底 z=+7.30）。
    ★ **同时导出 Blockbench 工程** `模型/hexalunar_m1_garand.bbmodel`（内嵌贴图，打开即改），
    顺手也把上一轮的 Kar98k 导成了 `模型/hexalunar_kar98k.bbmodel`。
  - ★ **连射（半自动）**：按住左键每 `FIRE_INTERVAL = 10` tick 一发（不用自己拉栓）——
    每发都由**导气杆自动完成「枪机后退 → 带出空弹壳抛向右上 → 复进闭锁、顶下一发上膛」**
    （`BOLT_TICKS = 8`）。用户要的「**拉一次栓即可**」= 一个漏夹只拉一次栓（换弹最后那一下），
    之后 8 发全靠自动循环。空仓时枪机**停在后位**（M1 打空的样子）。
  - ★ **换弹：右手把 8 发漏夹压进机匣**（与 Kar98k 一样是「手动压弹」，不是换弹匣）：
    `CLIP_PUSH_TICKS = 22`（右手把漏夹从机匣上方压下去，模型里漏夹抬高 2.25 px 跟着手落进弹仓）
    → `CLIP_CLOSE_TICKS = 10`（**枪机释放、复进闭锁上膛**，右手抓拉机柄跟着复进）。
    收尾一次性吃掉 **8 发** 7.62x61：**弹仓 7 + 膛内 1**。
    漏夹**只能打空后**整体压入（真枪如此），打空最后一发时整只漏夹弹出、响一声 M1 标志性的「叮」
    （`clipPing`，用拉栓音效调高音调代替 —— 公用音频里没有专门的 ping）。
  - ★ **新增独立弹种 7.62x61mm**（`ammo_762_61` + `ammo_box_762_61`，`AmmoType.GARAND`
    / 别名 `RIFLE_762_61`，弹盒容量 **128**、HUD 第 6 格）：与 7.62x39、7.62x59、.338 **都不通用**。
    配方与其它弹药一致（子弹 = 火药 + 铁锭无序 ×4；弹盒 = `ppp/pRp/iii`），
    图标 `tools/gen_ammo762_61_icons.py`（细长瓶颈弹壳 + 铜被甲尖弹头；弹盒是**钢蓝灰标签带**，
    与 7.62x39 无带、7.62x59 红棕带区分开）。
  - **伤害 22 / 爆头 ×1.5**（`BulletEntity.M1_DAMAGE` / `SEMI_HEADSHOT_MULTIPLIER`）：
    初速 **5.15** ⇒ 分档表新增 **M1 档**（`>5.08 && ≤5.30`）；半自动连射所以单发刻意低于栓动枪
    （AKM 10 / **M1 22** / 莫辛 26 / Kar98k 50 / AWP 75）。弹道另起一组
    `Ballistics.M1_RANGE = 72` 格、`M1_IN_RANGE_GRAVITY = 0.0055`。
  - ★★ **「套用 TaCZ 步枪持枪」怎么落地的**（用户问能不能套 TaCZ 的持枪动画）：
    扒了 `tacz-1.20.1-1.1.8-hotfix.jar` 里 `tacz_default_gun` 的 AK47/M4A1 配置
    （见 `build/tacz_rifle/`，`tools/_tacz_probe.py` 可读）：TaCZ 的枪**display 只给缩放**，
    持枪姿态全靠模型内定位组 + `iron_zoom` + `zoom_model_fov`，而**这两套参数我们本来就在用**。
    所以 M1 直接取 **TaCZ 步枪那一档：`zoom_model_fov = 45`（AK47 的值，M4A1 是 55）、
    `iron_zoom = 1.33`**（`GunPose.MODEL_FOV_AIM_M1` / 走 `ClientEvents.IRON_ZOOM`），
    举枪位移照 TaCZ 的 `iron_view`（`idle_view z 13.75 → iron_view z 10.156`，收 3.59 单位、
    **无任何旋转**）按枪长比例取 `M1_AIM_DZ = 1.8`。★ 但 TaCZ 的**逐帧动画文件搬不过来**：
    `ak47.animation.json` 虽然是 bedrock 格式，键的却是它自己的骨骼
    （`righthand` / `lefthand` / `constraint` / `mag_and_bullet` / `bullet_in_barrel` / `safety3` …），
    我们的枪是 `root / move / body / bolt / casing / …` ⇒ 硬套等于一段动画一根骨骼都找不到（= 没播）。
    能复用的是**持枪参数与节奏**，M1 的可见动作全部程序化（枪机循环 / 抛壳 / 压漏夹 / 双手）。
  - **瞄具**：只有机瞄（无镜）⇒ 抵肩走 AKM 那一套「轻机瞄」（视野 1/3、看得见枪身），
    ★ 瞄准线 = **准星片顶 = 照门觇孔中心 = 模型 Y 3.10**（`WeaponMount.M1_IRON_Y`），
    举枪对心实测 **X 0.00% / Y 0.00%**；腰射时枪管轴的相机空间偏移与 AKM **完全相同**（同一构图）。
  - **第一人称双手**（`client/WeaponArms.renderM1Garand` + `M1GarandGeoModel`）：
    平时右手握托颈、左手托前托；**射击时右手不跟着枪机跑**（枪机是导气杆自己动的）；
    换弹时右手抬到机匣上方压漏夹、再抓拉机柄复进；**左手全程扶枪**。
  - **战利品**：普通武器箱权重 **2**（配 10 发）、稀有武器箱权重 **4**（配 15 发）。
  - **音效**：枪声复用 AWP 枪声（音调更高）、枪机循环 / 漏夹到位 / 释放闭锁复用拉栓上膛、
    漏夹弹出的「叮」用同一音频调高音调；**没有**拷贝 TaCZ 的音频资源。

> 版本 `1.0.0-r107`

- ★★ **Kar98k 按用户要求重做装填 / 弹药 / 伤害**（`weapon/Kar98kItem.java` + `client/Kar98kGeoModel.java`
  + `tools/kar98k_gen.py` + `entity/BulletEntity.java`）：
  - **弹种换成 7.62×59mm**（`AmmoType.RIFLE_762_59`，就是莫辛那发 `ammo_762_59` 的**别名常量** ——
   不是新枚举项，所以 `values()`、快捷栏 HUD 格位、弹药盒全都不受影响）。.338 现在只有 AWP 用。
  - **装填 = 用手一发一发压进弹仓**（原来是一次性 40 tick 的「压桥夹」）：与莫辛同一套逐发时间轴
    `开栓 15 tick → 每发 12 tick × 需要几发 → 关栓上膛 16 tick`；每一发到点消耗 1 发弹药、弹仓 +1、
    响一声轻「咔」；**正在压的那一发被打断时有 30% 概率掉地**（TaCZ `bullet_lost = 0.3` 规则），
    已经压进去的留在弹仓里；压弹途中再按一次 `R` = 停下。
  - **模型新增 `round_in` 骨骼**（`kar98k_gen.py`，7.62×59 弹壳 / 弹肩 / 弹头三段、弹头朝 −Z）：
    压弹时那一发**从机匣上方（y≈3.40，正好在机匣顶 3.00 与 4 倍镜筒底 3.95 之间）落进弹仓**，
    关栓时再被枪机顶进弹膛；`z=−1.75` 是特意挑的 —— 弹尾要留在桥夹槽（z −1.2…0.9）**前面**，
    否则抬起来时弹壳尾部会被桥夹槽挡掉一截。
  - **装填全程枪机敞开**：`Kar98kGeoModel` 的 `bolt` 骨骼改由 `loadBoltTurn/loadBoltBack` 驱动
    （与击发后的拉栓循环共用同一根骨骼），**右手全程握着拉机柄**、**左手抬到机匣上方
    跟着每一发往下按**（`ARM_LOAD` y 3.60→3.05 + `ARM_PRESS`，位置是量着几何挑的，不穿镜筒也不穿机匣）。
  - **伤害 50**（用户指定）：初速 6.0 → **5.7** ⇒ `BulletEntity` 新增一档
    `kar98k()`（`>5.55 && ≤5.9`）= `KAR98K_DAMAGE` **50**、爆头 **×1.85**、弹道走 7.62×59 那一组
    （`MOSIN_RANGE` 84 格 / 0.005）；分档线相应改成 5.25 / 5.55 / 5.9（AKM ≤5.0 / 莫辛 5.4 /
    Kar98k 5.7 / AWP 6.2）。**一次击发一发 + 自动拉栓带出弹壳抛掉**不变（`CYCLE_TICKS` 26）。
  - 语言键与 tooltip 同步：`kar98k_controls` 现在写「一次一发 / 每发自动拉栓带出弹壳 / `R` 逐发压弹
    （7.62×59，弹仓 5 发）」，`range_hint` 取 84 格；`ClientWeaponInput.weaponBusy` 跟着改用
    `Kar98kItem.loading(...)`。
  - ⚠️ 顺带记一笔：`kar98k_gen.py` 的 `bone()` 已按 bedrock 规范**省略根骨骼的 `parent` 键**
    （写成 `"parent": null` 会让 GeckoLib 报 "parent to be a string, was null" 并崩客户端）。

> 版本 `1.0.0-r106`

- ★ **新武器：莫辛-纳甘 M91/30 栓动步枪**（`mosin_nagant`，`weapon/MosinRifleItem.java`）。
  - **模型**由 `tools/mosin_gen.py` 程序化生成：`geo/mosin.geo.json`（**14 骨骼 / 97 方块**）、
    `textures/models/mosin_geo.png`（**512² 逐面 UV**）、`animations/mosin.animation.json`。
    木托 + 发蓝钢 + 顶部导轨 + **出厂自带 4 倍镜**（镜筒就架在导轨上，拆掉后可用机瞄）；**枪管加长**：
    枪口 z = **−16.78**，整枪 **22.4 模型像素 = 1.40 格**（露出枪管 3.0 单位）。
    骨骼：`root / move / body / barrel / handguard / bolt / magazine / round_in / trigger /
    scope / scope_elev / scope_wind / casing / camera` —— ★ 与 AWP / Kar98k **不是同一套**
    （多了 `handguard` 与专门放「正在压的那一发」的 `round_in`，少了 `bipod` / `scope_adjust`）
    ⇒ `animations/mosin.animation.json` 必须独一份，**不能复用 `awp.animation.json`**。
  - **数值整套套用 TaCZ 的 Kar98k 配置**（从 `tacz-1.20.1-1.1.8-hotfix.jar` 导出，见
    `mod/build/tacz_kar98/` 与 `tools/_tacz_probe.py`）：`kar98_display.json` 的
    `zoom_model_fov = 25`（→ `GunPose.MODEL_FOV_AIM_MOSIN`）、`iron_zoom = 2`（→ `IRON_ZOOM`，
    **机瞄视野 1/2**，AKM 是 1.33）、`scope_98k_data.json` 的 `zoom = 4.25`（→ 我们挂 4 倍镜
    `SCOPE_ZOOM`）、`kar98_data.json` 的 `bolt_action_time 0.85s`（→ `BOLT_TICKS = 18`）、
    弹伤 26 / 爆头 1.85（→ `BulletEntity.MOSIN_DAMAGE` / `BOLT_HEADSHOT_MULTIPLIER`）、
    `bullet_lost = 0.3`；后坐俯仰取 `recoil.pitch` 峰值 3.8° 的上整
    （`WeaponHandGrip.MOSIN_FIRE_PITCH = 4.0`）。
  - ★ **新增独立弹种 7.62x59mm**（`ammo_762_59` + `ammo_box_762_59`，`AmmoType.MOSIN`，
    弹盒容量 **150**、HUD 第 5 格）：与 AKM 的 7.62x39、AWP 的 .338 **都不通用**。
    配方与其它弹药一致 —— 子弹 = 火药 + 铁锭（无序）×4；弹盒 = 木板围框 + **中心放该弹** + 三铁锭
    （`ppp/pRp/iii`，与 `ammo_box_sniper` 同款）；图标 `tools/gen_ammo_762_59_icons.py`。
  - ★★ **伤害分三档**（`BulletEntity`，全部按「首个 tick 捕获的出膛速度」判，主客两侧一致、不多加同步字段）：
    AKM **≤5.0 → 10 点**；**莫辛 5.4 → 26 点、爆头 ×1.85**；AWP **>5.9 → 75 点、爆头 ×2.0**。
    弹道另起一组：`Ballistics.MOSIN_RANGE = 84` 格、`MOSIN_IN_RANGE_GRAVITY = 0.005`
    （AKM 60 / 0.006，AWP 96 / 0.004）。
  - ★★ **装填 = 用手一发一发压进弹仓**（弹仓式，没有可拆弹匣）：按 `R` 后时间轴 =
    开栓 **15 tick** → **每发 12 tick × 需要几发** → 关栓上膛 **16 tick**。每一发到点都会
    消耗 1 发弹药、弹仓 +1、响一声轻「咔」，模型里那一发（`round_in` 骨骼）**从机匣上方落进弹仓**；
    关栓那一刻再从弹仓推一发进弹膛。中断规则照 TaCZ 的 `bullet_lost = 0.3`：正在压的那一发
    超过 **35%** 进度被打断时有 **30%** 概率掉在地上（**已经压进去的留在弹仓里**）；
    丢下枪换物品会自动停，装填中再按一次 `R` 也停。
  - ★★ **拉栓循环 = 抽壳 → 抛壳 → 再上膛**：击发后自动抬柄转栓 **90°**（莫辛是下弯柄，柄头最高 Y≈2.77，
    而镜筒底面在 3.08 ⇒ 比 Kar98k 的 64° 能抬得更足）→ 枪机后退 **2.3 px** 把空弹壳抽出来 →
    弹壳往机匣**右侧（+X，抛壳口那一侧）**翻滚抛出（`casing` 骨骼，`CASE_VX 4.6` / 三轴翻滚）→
    枪机推回闭锁并把弹仓里下一发顶进弹膛（`finishBolt`：弹仓 −1、膛内 +1）。
  - **开镜**：装了 4 倍镜 = **整屏镜筒遮罩**（与 AWP / 十字弩同一套）+ 世界变焦 1/4；
    **潜行 + 右键拆掉镜子就是机瞄**（视野放大 2 倍、看得见枪身）。举枪时隐藏原版准星。
  - **第一人称双手**（`client/WeaponArms.renderMosin` + `MosinGeoModel`）：右手握**腕部**
    （拉栓 / 开栓时抓下弯拉机柄），左手托前托（**逐发压弹时抬到机匣正上方跟着那一发往下压**）；
    第三人称走双端枪 / 举枪姿势（`WeaponArmPose.MOSIN`）。
  - **音效**：枪声复用 AWP 枪声（音调略高）、拉栓 / 关栓复用 `拉栓上膛.ogg`、每发压弹一声轻「咔」；
    **没有**拷贝 TaCZ 的音频资源。
  - **战利品箱子**：普通武器箱权重 **2**（配 10 发）、稀有武器箱权重 **4**（配 15 发）。
  - 版本号 `1.0.0-r106`（`mod/build.gradle`），产物 `hexalunar_calamity-1.0.0-r106.jar`。

> 版本 `1.0.0-r105`

- ★ **新武器：Kar98k 栓动步枪**（`kar98k`，`weapon/Kar98kItem.java` + `client/Kar98kGeoModel.java`）。
  - **模型**由 `tools/kar98k_gen.py` 程序化生成（木托长枪 + 下弯拉机柄 + **自带 4 倍镜筒**）：
    `geo/kar98k.geo.json`（**10 骨骼** / 128² 分带贴图）+ `textures/models/kar98k_geo.png`。
    骨骼名为 `body / barrel / bolt / magazine / trigger / casing / scope / bipod / move / root`，
    **沿用 AWP 那一套** ⇒ 动画**直接复用 `animations/awp.animation.json`**，六段一条都不用重写。
  - **与 AWP 的三个差别**（都由 `kar98k.geo.json` 量出来）：
    · 拉机柄是**下弯柄**，抬升角只给 **64°**（`Kar98kGeoModel.BOLT_LIFT`）—— 柄头挂在 x≈1.25 / y≈1.75，
      绕 bolt pivot（y=2.95）抬起来很快顶到 4 倍镜筒底面（y=3.95），算下来 θ>71° 就穿模，取 64° 留 7° 余量；
    · 枪机后退 **2.6 px**（AWP 4.2）：机匣短（z −2.4…1.2）、枪机本体 3.0 长，退 2.6 正好把枪机抽出机匣；
    · 右手握点取**下弯柄的柄头**（`BOLT_GRIP_DX/DY`），抬柄时手跟着一起抬高。
  - **数值**：初速 **6.0**（AWP 6.2）⇒ 与 AWP 同属「狙击弹」那一档（`>5.9`），
    **伤害 / 弹道按 .338 算**；`MAG_SIZE = 5`、`RELOAD_TICKS = 40`、`BOLT_TICKS = 20`、
    `BOLT_DELAY = 6`、`CYCLE_TICKS = 26`。
  - **4 倍镜**：`Kar98kItem.SCOPE_ZOOM = 4.0`，抵肩即走 **AWP 那套整屏镜筒遮罩**
    （`ClientEvents.scoping` 对 `Kar98kItem` 直接返回 true ⇒ 枪与手臂一起藏掉）；
    光轴参照点 = 模型 Y **4.40**（`WeaponMount.KAR98K_SCOPE_Y` = 镜筒方块 y 3.95…4.85 的中心
    = geo 里 `scope` 骨骼 pivot 的 y）；枪模投影 FOV = `GunPose.MODEL_FOV_AIM_KAR98K = 40`。
  - ★★ **换弹 = 压桥夹**（没有可拆弹匣）：`animations/awp.animation.json` 的 `reload` 只 key 了
    `magazine` 一根骨骼（那是 AWP「抽弹匣」的键帧），所以换弹期间把该骨骼**显式归零**压掉那段键帧
    ⇒ 弹仓底板不动；换弹的手部动作改由 `Kar98kGeoModel.leftHandPx` 驱动 ——
    左手从护木抬到机匣左侧上方「压桥夹」（`ARM_CLIP`）。
  - ★ **`WeaponAnim.Kind` 追加 `KAR98K`**（★ 这个枚举**只能往后加**，中间插值会打乱所有武器的动画状态）。
  - 目前**只能在创造模式「六相月灾」页签取用**（还没进探险箱掉落与配方）。

> 版本 `1.0.0-r104`

- **修正 r103 的一处误改**：`WeaponMount.fireDir(entity, level, from, minDist, maxDist)`
  的后两个参数是**睐准辅助距离**，不是伤害；
  上一轮把它改成 75 相当于把 AWP 的辅助距离拉到 75 格 ⇒ 已还原
  为 `aiming ? 40.0D : 24.0D`。
- **AWP 真正的伤害常量**：`BulletEntity.SNIPER_DAMAGE` 24.0F → **75.0F**（.338）。
- **新增爆头判定**（`BulletEntity.onHitEntity`）：狙击弹命中头部盒
  \uff08命中点 y ≥ 实体 `getEyeY() - 高度×0.12`）时 × **2.0** →
  **150 点**：正常僵尸爆头**一枪带走**；只有血量特别厚的（CD 进化僵尸等）
  才需要补枪（用户要求）。倍率只作用于狙击弹，AKM 不受影响。


> 版本 `1.0.0-r103`

- **AWP（.338）伤害 24/40 → 75 点**（`weapon/AwpRifleItem`：`WeaponMount.fireDir(..., 75.0D)`）：
  按用户要求固定 **75 点**（37.5 颗心），不再区分抵肩/腰射。
- **倍镜 8 倍 → 4 倍**（`client/ClientEvents`：`SCOPE_8X_ZOOM = 4.0F`）。
- **枪模 FOV 套用 TaCZ kar98k**：`GunPose.MODEL_FOV_AIM_AWP` 35 → **25**
  （TaCZ 对照：AK47 = 45、ai_awp = 35、kar98 = **25** ⇒ 开镜时枪身放大更多）。
  参考数据（TaCZ `tacz_default_gun`，实测）：`kar98_display.json` 的 `iron_zoom = 2`、
  `zoom_model_fov = 25`；`kar98_geo.json`（57 骨骼 / 128² 贴图）定位组
  `idle_view = (2, 9.8125, 17)`、`iron_view = (0, 8.75, 17.5)`
  ⇒ 机瞄时枪左移 2、上抬 1.06、朝射手收 0.5（与 AK47/M4A1 同一规律）。
- **待办（下一轮）**：按用户照片在 Blockbench 里做 **Kar98k 模型**（木质枪托/护木 + 拉栓 + 4 倍镜筒）
  并替换 `geo/awp.geo.json`；新模型必须沿用现有骨骼名（root/move/body/barrel/scope/bolt/casing/
  magazine/trigger/bipod）才能继续吃现有动画，同时要重调手臂/枪口/弹道的模型参照点。


> 版本 `1.0.0-r102`

- ★★ **月相与 Crafting Dead Survival 同步**（新增 `moon/CraftingDeadCompat.java`、改 `moon/MoonManager.java`）：
  - 用户要求：「需要同步 craftingdead 的月相」。
  - 现状：Crafting Dead Survival（modId `craftingdeadsurvival`）自己有一整套**同名同构**的月相 ——
    `MoonEventType`: `NONE / BLOOD_MOON / BLUE_MOON / YELLOW_MOON / SUPER_BLOOD_MOON /
    SUPER_BLUE_MOON / SUPER_YELLOW_MOON`，规则写死在 `forDay(day)`（已从它的字节码里读出）：
    ```
    day % 28 == 6  → 蓝月        7  → 超级蓝月    13 → 血月
             20 → 黄月           21 → 超级黄月    27 → 超级血月    其余 → NONE
    ```
    它还有 `ApocalypseManager.getMoonEvent(Level)`（会参考它自己的 `/moon` 手动指令）、
    客户端 `MoonDataHolder.getEventType()`（`SyncMoonDataMessage` 同步）。两边各转各的时，
    它 HUD 显示"月相: 满月"、我们 HUD 显示"黄月"，天上颜色也对不上。
  - 做法：**装了 CD 时，今夜月相完全以 CD 为准** —— 服务端在选相那一步调
    `ApocalypseManager.getMoonEvent(level)`（反射，**软依赖**：不把它写进 build.gradle，
    找不到类/方法就自动退回本模组原来的概率轮转），把 CD 的枚举名映射到我们的 `MoonPhase`
    （`BLOOD_MOON → 血月` … `SUPER_* → 超级*`，`NONE → 无月之夜`）。
    随后本模组的公告 / 尸潮 / 加成 / 天空着色 / HUD 与 CD 的 HUD 自然全部一致。
  - 保留两个**显式覆盖**：`/hexalunar moon set <相位>`（`data.forced`）依旧最高优先级；
    `/hexalunar moon roll` 仍然走本模组自己的随机轮转（玩家主动要"另一个月相"时用）。
  - 日志证据（一次）：`[HLCMOON] 检测到 Crafting Dead Survival —— 月相将跟随它` +
    `[HLCMOON] 月相已与 Crafting Dead 同步：BLOOD_MOON ⇒ 血月`。
  - 注意：同步的是**月相本身**（哪一晚是什么月），两边各自的月相**效果**（我们催作物/给幸运/开尸潮，
    CD 自己的进化与尸潮）会同时生效 —— 这是"同步"的预期结果；若只想要视觉一致、不要效果叠加，
    可以再加一个配置开关单独关掉我们的效果。

### 另：整合包环境修复（据 `mod/logs` + `crash-reports`，不属于模组代码）

- **07:29 FML 崩溃**（`crash-2026-09-20_07.29.13-fml.txt`）：
  `-- MOD craftingdeadsurvival -- Caused by: NoClassDefFoundError: kotlin/NoWhenBranchMatchedException`
  ⇒ **缺 KotlinForForge**。用户 07:29:59 补上 `kotlinforforge-4.12.0-all.jar` 后 CD 已能正常加载。
- **08:08 服务器崩溃**（`crash-2026-09-20_08.08.48-server.txt`）：
  `WritingException → FileSystemException: ...serverconfig\craftingdead-server.toml: 另一个程序正在使用此文件`
  ⇒ Forge 保存 CD 的 server config 时**文件被占用**（多为同时开了两个实例 / 杀毒瞬时扫描）。
  文件本身完好（12,624 B，与其 `.bak` 一致）⇒ 直接重开即可；反复出现就删掉
  `saves/<世界>/serverconfig/craftingdead-server.toml` 让它重建。
- **`hcdservercore`（`craftingdeadloot-1.20.1-3.jar`）5 张战利品表整表解析失败** ⇒ 那些战利品方块
  **空手**（日志里 `Couldn't parse element loot_tables:...` + `unknown string 'craftingdead:multi_paint'`）。
  原因：表里引用了 24 个 CD 1.9.5 里不存在的 id。修复（已落地到用户世界）：
  在 `saves/新的世界/datapacks/hcd_loot_fix/` 放一个**数据包**覆盖这 5 张表 ——
  - **改名**：`splint`/`cure_syringe`/`rbi_syringe` → `craftingdeadsurvival:`；
    `red_dot_sight` → **`hexalunar_calamity:red_dot_sight`**（本模组物品）；
    `magnum_magazine` → `craftingdead:magnum_ammunition`；`m1garand_magazine` → `craftingdead:m1garand_ammunition`
  - **剔除**（CD 里确实没有）：`trenchgun`、`trenchgun_shells`、`pipe_grenade`、`scarh`、`broad_sword`、`multi_paint`
  - CD 的**配件**（`attachment.craftingdead.*`：acog/eotech/hp_scope/lp_scope/bipod/tactical_grip/suppressor）
    核对后是**真物品**，全部保留。
  - 一键重跑脚本：`tools/fix_craftingdead_loot.py`（读 CD 系模组的 lang/tags 建白名单后改写表 + 写数据包）。

> 版本 `1.0.0-r101`

- ★ **修复右下角弹药框被截断**（`client/ClientEvents.drawAmmoHud`）：
  - 现象：AWP 的 `"4+1 / ∞"` 里那个 ∞ 跑到框外（用户截图）。
  - 原因：背景框**写死 78 宽**（`g.fill(x-6, y-5, x+72, y+19)`），而 AWP 的弹匣串比 AKM 的
    `"30 / ∞"` 多一个 `+1` ⇒ 文字比框宽。
  - 修法：框宽改成 `22 + font.width(line) + 8`（图标 + 实测文字宽 + 右边距），整框从屏幕右边
    留 10px 右对齐 ⇒ 以后任何弹数/文案都不会再溢出。
- ★★ **修月相天空与月亮配色**（`moon/MoonPhase.java`、`client/MoonSkyRenderer.java`）：
  - 用户要求：**黄月/超级黄月**天空与月亮都要**黄**；**蓝月/超级蓝月**都要**蓝**；
    **血月/超级血月**都要**大红**。
  - 原因：月亮色（`moonColor`）本来就是对的，但**天穹色 `skyTop/skyHorizon` 写得太黑** ——
    黄月原本是 `0x141005`（RGB 20,16,5 ≈ 全黑）、血月 `0x1C0608`、蓝月 `0x06101F`
    ⇒ 叠在夜空上几乎看不见，所以整体没有"黄月/蓝月/血月"的氛围。
  - 修法：
    | 相位 | skyTop（天顶） | skyHorizon（地平线） | moon（月盘） |
    |---|---|---|---|
    | 血月 | `0x5A0C0E` | `0xB01818` | `0xFF3030` |
    | 蓝月 | `0x0C2258` | `0x2A5ABE` | `0x88B8FF` |
    | 黄月 | `0x4E3C0C` | `0xB08A1E` | `0xFFD35E` |
    | 超级血月 | `0x7A1012` | `0xD01818` | `0xFF5A46` |
    | 超级蓝月 | `0x142E78` | `0x3A74E0` | `0xB8D8FF` |
    | 超级黄月 | `0x634D10` | `0xD8AC28` | `0xFFE070` |
    天穹不透明度同时上调（天顶 0.42→**0.55**、地平线 0.60→**0.72**），超级相位本来就更高。
  - 另外新增一次性日志，方便从日志确认这套着色真的在画（每个相位只打一条）：
    `[HLCMOON] 天穹/月盘着色生效：黄月（超级=false） skyTop=#4E3C0C skyHorizon=#B08A1E moon=#FFD35E`
  - 实现方式没变（仍是 `RenderLevelStageEvent.Stage.AFTER_SKY` 自绘天穹 + 月盘，
    位于原版天空之后、地形之前，见 `LevelRenderer` L1155→L1158）。

> 版本 `1.0.0-r100`

- ★★ **AKM 机瞄套用 TaCZ AK47 的定位组**（`weapon/WeaponMount.java`）：
  - 用户问「我们自己的 AKM 可不可以套用 TaCZ 的 AK47 机瞄」⇒ 可以。TaCZ 的 `ak47_display.json`
    原话：「**旋转和位移使用模型内定位组**」，机瞄姿态写在 `ak47_geo.json` 的两个组里：
    | 组 | pivot (x, y, z) | 含义 |
    |---|---|---|
    | `idle_view`（腰射） | `(2.5, 12, 13.75)` | z 最大 = 枪离眼最远 |
    | `iron_view`（机瞄） | `(0, 10.8875, 10.15625)` | **朝射手收 3.59 单位**、上抬 1.11、右移归零 |
    三把枪规律一致（M4A1 收 3.8 / Glock 收 0.75，全都**右移归零 + 上抬**），
    而且 **`iron_view` 没有任何旋转**（枪管正对视线，不歪）。
  - 差距所在：我们原来的 `AKM_AIM_DZ = -3.0` 是**往枪口方向推**（越举越远、屏幕上越小），
    方向与 TaCZ 正好相反。
  - 修法：`AKM_AIM_DZ` 改成 **+1.8**（相对 `akm.json` 腰射位移的**增量**）。TaCZ 的 3.59 是相对
    它 38 单位长的枪，我们这把约 19 单位 ⇒ 按比例取一半。相对旧值相当于**把枪拉近 4.8 px ≈ 0.3 格**，
    机瞄时枪在屏幕上有明显变大、更贴手；刻意没取满（r88 试过增量 +4.0：眼睛被塞进机匣、后摇板铺满屏幕）。
  - AWP 那条 `AWP_AIM_DZ = -3.5` 没动：它的开镜已经被 r99 改成整屏镜筒（枪根本不画），
    真要改可以随时按同一张表对齐。
  - 我们 ADS 的**旋转本来就是 0**（`GunPose.matrix` 里腰射的 yaw/pitch 会随 aim 淡出，
    AKM 的 ADS 横滚 r94 起就是 0）⇒ 与 TaCZ `iron_view` 的「零旋转」天然一致。

> 版本 `1.0.0-r99`

- ★★ **AKM 装 4 倍镜开镜 = 整屏镜筒（藏枪藏手）**（`client/ClientEvents.java`）：
  - 用户要求：「AKM 安装倍镜时右键瞄准隐藏手和模型」。截图里当时枪身、手臂都还在画面里，
    只有分划 + 蓝圈叠在上面。
  - 修法：`maskScoping(player)` 直接改成 `scoping(player)` —— 它已经覆盖
    **AWP**（抵肩即 8 倍镜）、**十字弩**（上弦后 4 倍镜）、以及 **AKM 且瞄具 == `Sights.SCOPE`**；
    ⇒ 这三者开镜时枪与手臂一起藏掉，只留镜筒遮罩 + 分划 + 蓝色镜圈（与 AWP/十字弩同一套实现）。
  - **机瞄 / 红点仍然看得见枪**（用户先前明确要的构图，图 1），不受影响。
- ★★ **机瞄（ADS）手臂糊住准星的问题：肩点按 aim 外推**（`client/WeaponArms.java`）：
  - 原因：举枪时枪模投影从 `MODEL_FOV_HIP = 76°` 收到 `MODEL_FOV_AIM = 45°`（≈**1.69 倍放大**），
    而肩点离眼睛只有 0.78~0.80 格 ⇒ 两条手臂在 ADS 里被放大成一大片皮肤色楔子，正糊在准星上
    （用户截图里那块大粉色就是它）。
  - 修法：新增 `ADS_SHOULDER_PUSH = 1.55`，在 `render(...)` 里按 `WeaponAnim.of(kind).aim`
    把肩点向量整体外推 ⇒ 手臂在 ADS 与腰射下的**视觉粗细/长度一致**，准星不再被糊住。
    腰射（aim=0）与手雷（不带 aim）行为不变。

> 版本 `1.0.0-r98`

- **AKM / AWP 腰射持枪构图按用户标注调整**（`weapon/WeaponMount.java`、`models/item/akm.json`、
  `models/item/awp.json`、`weapon/GunPose.java`）：
  - 用户标注图（第 3 张）：「akm 那个红框应该在蓝色箭头的地方贴着手臂」+「蓝框里的手臂应该在
    双红框位置」⇒ 两边都要**向画面中心收**：枪往**左下**、手臂往**右上**。
  - **枪械 display 第一人称平移**：AKM `(-2.6, 1.4, 1.8) → (-5.0, -0.6, 1.8)`；
    AWP 同步保持「与 AKM 同一套持枪」的规则 `(-2.6, 1.575, 0.5) → (-5.0, -0.425, 0.5)`
    （左右手两份都改）。约等于屏幕上把枪往左下搬 ~80 px。
  - **腰射枪模 FOV**：`GunPose.MODEL_FOV_HIP` **70 → 76** ⇒ 屏幕上的枪与手臂一起向中心收，
    枪也略小一点，不再顶到右下角。举枪（ADS）不受影响：照门/准星靠**平移**对齐，
    `AKM_AIM_DX/DY`、`AWP_AIM_DX/DY` 都是从 display 常量**推导**出来的（改一处自动跟随），
    弹道（枪口/抛壳世界坐标）同理 ⇒ 不会出现「改了持枪位置导致打不准」。
  - 同一轮把 `tools/_awpfp.py`、`tools/_fp_ads3.py` 里的默认 display 值同步到新数值，
    离线预览器继续和游戏一致。
  - 诊断继续保留：进游戏拿枪站几秒，`hexalunar_diag.txt` 里 `MISMATCH=false` 就说明
    「模型里的平移」与「代码常数」仍然一致（这是这套推导能成立的前提）。

> 版本 `1.0.0-r97`

- ★★ **十字弩弦：删掉 r71 的「线缆」，让弦真正收口成内 V**（`geo/crossbow_geo.geo.json`、
  `tools/crossbow_vox.py`、`client/CrossbowGeoModel.java` 注释）：
  - 现场：每个 `string_*` 骨骼里其实**有两条线**：
    `PAT_STRING`（米白，真正的弦，`size[0]=5.6646 = hypot(TIP_X, DRAW_DZ)`）与
    `PAT_CABLE`（深灰，r71 按参考照片加的"线缆"，`cable_len = tip_x + 0.85 = 6.221`，
    生成器注释原话「**越过中线 0.85 像素 ⇒ 形成交叉**」）。
  - 根因：r89 只把 Java 的 `STRING_LEN` 从 5.665 改成 **6.221**（那是**线缆**的长度），方块没动
    ⇒ Java 解的 φ 让**线缆**正好落到弦心并交叉，而**米白的弦短 0.56 收不到弦心**
    —— 就是用户说的「外 V 字型」。`_cb_flex.py` 的自检之所以显示 0.00，是因为它按 6.221 算，
    恰好验的是那根线缆。
  - 修法：geo 与生成器里**每条弦骨骼只留一根弦**、长度统一 **6.221**（= Java `STRING_LEN`，
    左右两条分别从各自锚点画到枢轴，y/z 与弦心对齐），r71 的两根线缆整段删除；
    `_cb_flex.py` 复跑：拉满时弦内端 = 弦心 (0.00, +0.22)，偏差 **(0.00, 0.00)** ✓
  - 记档：`tools/crossbow_vox.py` 顶部新增 `STRING_LEN_RUNTIME = 6.221` 常量并写明
    「必须与 Java 一致」，避免以后再各改一边。

> 版本 `1.0.0-r96`

- ★★ **「枪飘在手右上方、和手臂分离」：加「干净 pose 基准」防护**（`client/WeaponArms.java`、
  `client/ClientEvents.java`、`client/WeaponHandGrip.java`）：
  - 现场线索：用户装了 **TaCZ 1.1.8 + SimpleBedrockModel**，它俩的
    `FirstPersonRenderHandler` **挂在同一个 `RenderHandEvent` 上**，给自家枪做第一人称渲染时会
    **直接改事件里的 `PoseStack`**。拿我们的 AKM 时它 `Optional` 为空、什么都没画，
    **但改动可能已经留在栈上** ⇒ 之后原版那一遍 `renderArmWithItem`（枪）和我们补画的手臂
    一起被这段残留平移/缩放带走 —— 正是用户截图里那个姿态。
  - 修法：新增 **HIGHEST 优先级**的 `onRenderHandEarly`，在**还没人被任何人动过**时记下
    `poseStack.last()` 的 pose/normal；随后在画手臂（`WeaponArms.drawArm`）和给枪摆位
    （`WeaponHandGrip.apply`，即 `applyForgeHandTransform` 里）之前，把 `last()` **覆盖回这份干净矩阵**
    ⇒ 枪与手永远共用同一份基准。没有任何外部篡改时它就是一次无副作用的复制（向后兼容）。
  - 同时把**篡改量**（矩阵元素最大绝对差）写进诊断：日志里 `poseDelta=` 非 0 即坐实有别的模组
    在动手持 pose（`WeaponDiag` 还会额外打一条 `[HLCDIAG] ★ 检测到外部手持渲染篡改 PoseStack`）。
- **诊断器 `WeaponDiag` 再修一处时间窗错位**：以前只打 tick 时刻的 `heldWeapon`，而
  `applyCalled/armsCalled` 是过去一秒累积的 ⇒「held=akm 但 arms=false」可能只是换枪过程中的错位
  （上一份日志就把我误导过一次）。现在渲染侧把**渲染那一刻**的物品记进 `renderedItem`，
  日志同时打 `held=`（tick 时刻）与 `render=`（渲染时刻），两边同一时刻可比。

> 版本 `1.0.0-r95`

- ★★ **修致命崩溃：自定义 `ArmPose` 必须在模组构造期创建**（据用户提供的 `mod/logs/latest.log`）：
  - 日志里那条 FATAL：
    `java.lang.ArrayIndexOutOfBoundsException: Index 10 out of bounds for length 10`
    → `HumanoidModel.poseRightArm(HumanoidModel.java:234)`（`switch (this.rightArmPose)`）
    → 由 TaCZ 的第一人称手臂渲染链（`RenderHelper.renderFirstPersonArm`）触发。
  - 根因：javac 给 `switch (枚举)` 生成的 `$SwitchMap` 表按**建表那一刻** `ArmPose.values().length`
    定长；世界里第一只人形生物（含我们自己的僵尸）被渲染时表就定成 **10** 长，
    而我们的第 11 个常量 `HEXALUNAR_RIFLE_AIM`（ordinal **10**）是**懒加载**创建的
    （第一次 `getArmPose` 才触发类初始化）⇒ 索引 10 越界 ⇒ 整个游戏 FATAL。
  - 修法：`HexaLunarCalamity` 构造函数在客户端把 `clientBootstrapping = true` 后主动触碰
    `WeaponArmPose`（`initArmPoses()`）——**在任何渲染之前**把枚举常量建出来，之后建的表就是
    11 长；万一本类仍被懒加载（窗口已关），直接退回原版 `CROSSBOW_HOLD`，**姿势朴素也绝不崩游戏**。
    创建失败的兜底也从静默改成打日志。
- **诊断器 `WeaponDiag` 修两处自己带歪数据的 bug**（同一份日志暴露的）：
  - 模型里读到的 display 平移是**格**（= 模型像素/16），`WeaponMount` 常数是**模型像素** ——
    以前拿「格」比「像素」，于是 `held=awp/akm` 全都误报 `MISMATCH=true`。现在按枪各自换算后再比
    （日志实测：AKM `(0.09*16, 0.11*16)` 与常数完全一致 ⇒ 模型与常数本来就是对的）。
  - `armsCalled` 以前只有 `renderAkm` 会置位，AWP / 十字弩那一支永远是 `false`（看着像"手臂没画"）；
    现在三个 `render*` 都置位。

> 版本 `1.0.0-r94`

- **AWP 也按 TaCZ 的配置对齐**（参考 `ai_awp_display.json` + `scope_standard_8x_display.json`）：
  > TaCZ 仓库里**没有**叫 `awm` 的文件 —— AWP/AWM 在他们那儿就是 **`ai_awp`**，倍镜是
  > `attachments/scope_standard_8x`。

  | TaCZ 字段（ai_awp / scope_standard_8x） | 含义 | 我们 |
  |---|---|---|
  | `zoom_model_fov: 35` | 举枪时枪模投影 FOV | ★ 本次对齐：`GunPose.modelFov(true, aim)` ⇒ AWP 用 **35**（AK47 保持 45） |
  | `iron_zoom: 1.5` | 机瞄放大（**没装镜**时） | 我们 AWP 自带 8 倍镜、抵肩即看镜 ⇒ 无此态 |
  | 倍镜 `zoom: [5, 10]` / `"scope": true` | 看镜放大 5~10 倍、真·镜筒 | ✅ 我们用 8 倍（落在他们区间内），且 r91 起就是整屏镜筒 |
  | 倍镜 `views_fov: 20` | 看镜时枪模 20° | 那时整把枪被镜筒遮住，用不上（已在代码注释里记下） |
  | `transform.scale` 无 firstperson 项 | 第一人称模型 1.0 倍 | ✅ 我们的 display scale = 1.0 |
  | `show_crosshair`（默认关） | 举枪隐藏准星 | ✅ r92 已对齐 |
  | `bolt_shell_ejecting_time: 0.4` | 拉栓/抛壳时机 0.4 s | 我们 `AwpRifleItem.BOLT_DELAY` = 6 tick = 0.3 s（要 0.4 s 就说一声，一行改） |
- `GunPose.modelFov(boolean awp, double aim)` 新增：**各枪自己的举枪模型 FOV**（AK 45 / AWP 35），
  腰射统一 70。参数用 `boolean` 而不是 `WeaponAnim.Kind`，避免 weapon 包反向依赖 client 包
  （`GunPose.transform` 在服务端算弹道时也会被调用，签名里出现客户端类有炸专用服务器的风险）。

> 版本 `1.0.0-r93`

- **AWP 开火后坐改成「枪托微微下沉 + 枪管微微上抬」的绕手俯仰**（用户要求）：
  - `GunPose` 的举枪姿态层新增第 6 个分量 **`firePitch`（开火俯仰，度）**，乘在**最后**
    （`Rz(横滚)·Trans(位移)·R(腰射姿态)·Rx(firePitch)`）⇒ 它最先作用在模型点上、**枢轴是姿态原点
    （原版手部基准 ≈ 握把）**：正角时枪管（前端 −Z）上抬、枪托（后端 +Z）下沉。
    `transform()`（手臂 / 枪口 / 弹道都走它）同步加了同一段，所以**双手绕同一点一起动、不会脱手**。
  - `WeaponHandGrip`：AWP 的 `pushAds` 从「整枪 `AWP_FIRE_LIFT` 平抬」改成
    **`AWP_FIRE_PITCH = 6° × 后坐量`**（抵肩 ≈2.5°、腰射 ≈3.6°，再按 ×0.55/tick 衰减 ⇒ 一记短促的枪口一跳）。
    平抬会把枪托也抬起来，正好和「枪托下沉」相抵，所以改成 0。
  - `AwpGeoModel.computeMovePose` 仍全零（骨骼不参与），后坐全部在姿态层算一份；
    镜头那一份 `ClientEvents.applyRecoilKick` 保留（视角晃动）。
  - 调参：嫌夸张就改 `WeaponHandGrip.AWP_FIRE_PITCH`（6 → 4），想要更猛就往上加。

> 版本 `1.0.0-r92`

- **AKM 持枪对齐 TaCZ 的 AK47 配置**（参考 `MCModderAnchor/TACZ`
  `assets/tacz/custom/tacz_default_gun/assets/tacz/display/guns/ak47_display.json`）：
  | TaCZ 字段 | 含义 | 我们 |
  |---|---|---|
  | `iron_zoom: 1.33` | 机瞄世界放大 | ✅ `ClientEvents.IRON_ZOOM` 已是 1.33 |
  | `zoom_model_fov: 45` | 举枪时枪模单独投影 FOV | ✅ `GunPose.MODEL_FOV_AIM` 已是 45 |
  | `show_crosshair: false` | 举枪隐藏准星 | ★ 本次对齐：拿枪抵肩时收掉原版准星（`onRenderGuiOverlay`） |
  | `transform` 只给 `scale`，注释写明「**旋转和位移使用模型内定位组**」 | 举枪=纯平移、枪身不横滚 | ★ 本次对齐：`WeaponMount.akmAdsRoll` 恒返回 **0**（r88 的机瞷 15°/红点 8° 横滚去掉） |
  - 去掉横滚后，举枪只剩平移 ⇒ 照门—准星（或红点）那条线永远钉在屏幕中心，枪身正着端在眼前
    —— 就是用户图 1 那种持枪；`rollComp` 那段补心位移在 0 度时自动跳过，不用删。
  - 复合弓例外：拉弓时保留准星（要看目标）。

> 版本 `1.0.0-r91`

- **AWP 开镜改用十字弩那一套「整屏镜筒」实现**（`client/ClientEvents.java`，用户要求）：
  - `maskScoping` 重新把 **AWP 8 倍镜**算进去（与十字弩同一支）：{@link #onRenderHand} 在抵肩时
    直接把枪与手臂一起藏掉（像原版望远镜），只留圆形镜筒 —— 镜筒外近黑遮罩 + 镜缘暗角 +
    镜内分划 + **蓝色镜圈**（蓝圈画在镜筒半径上，就是一圈蓝色镜缘）。
  - `drawScopeReticle(g, ringR, limitedToRing)` 新增「只画圈内」模式：整屏镜筒（十字弩 / AWP）
    的十字只留在镜筒内，不再往黑色遮罩上画外段粗线；AKM 4 倍镜仍是「看得见枪」那一支
    （十字贯穿整屏 + 蓝圈取短边 20%）。
  - r90 曾把 AWP 改成「只叠分划、看得见枪」，本次按用户要求回退成整屏镜筒。

> 版本 `1.0.0-r90`

- **★★ 输入状态只认「真实鼠标事件」：修掉「断点/alt-tab 回来左键不发射」与「按住右键进不了机瞄」**
  （`client/ClientWeaponInput.java`）：
  - 根因是 `GLFW.glfwGetMouseButton` 给的是 **GLFW 缓存的按钮状态**：调试器断点、alt-tab、
    点到别的窗口时鼠标松开事件落在别的窗口上 ⇒ 缓存**永远停在“按下”**。于是
    ① 半自动武器（AWP / 复合弓）再也等不到一次「新的按下」，② 原版
    `LivingEntity#startUsingItem` 里那句 `if (... && !this.isUsingItem())` 让**之后每一次右键都失效**
    ——用户拿图报的「枪飘在手右上方、和手臂分离」「按住右键没有进入机瞄」都由此而来。
  - 现在 `attackPressed` / `usePressed` **只由 `InputEvent.MouseButton` 维护**，GLFW 只作为
    「已经收到过真实按下」时的兜底；松开事件**永远**处理（连界面开着时也处理），
    窗口重新获得焦点时整套状态复位。
  - 每 tick 兜底 `clearStuckUse()`：右键没按着、手上武器又不在换弹/拉弦，却还卡在
    `isUsingItem()` ⇒ 主动 `releaseUsingItem`，右键不会因为一次丢事件永久坏掉。
- **倍镜分划改成「蓝色圆圈 + 白色十字线」**（`client/ClientEvents.java`，用户图 2 的样式）：
  - 白十字贯穿整屏（圈内细、圈外粗）、每 `r/4` 一颗密位点、中心一颗暖色点；
  - ★ 新增 `drawScopeRing()`：`0xFF0099FF` 蓝色圆环（与用户标注同色）。AWP 8 倍 / AKM 4 倍镜
    半径取短边的 **20%**（就是用户图上画的那个比例）；十字弩的整屏镜筒传镜筒半径进去，蓝圈正好压在镜筒边缘。
  - ★ **AWP 不再走整屏镜筒遮罩**（`maskScoping` 只认十字弩）：用户图上镜外世界、枪、手全都看得见，
    所以 AWP 抵肩 = 只叠分划 + 蓝圈，枪与手臂照常渲染。
- **十字弩「弦」收口**（`client/CrossbowGeoModel.java`，上一轮未编译进 jar）：
  `STRING_LEN` 5.665 → **6.221**（= geo 里弦方块的真实长度）。拉满时两段弦的内端此前停在
  弦心前 0.56 px，看着就是「V 没合上/交叉过线」；现在由几何解出的 φ 让内端**精确落在弦心上**
  （`tools/_cb_flex.py` 自带数值自检，实跑偏差 0.00）。
- **新增现场诊断 `client/WeaponDiag.java`**：「枪 / 手错位」这类只能在游戏里复现的问题，
  每秒往 **游戏目录 `hexalunar_diag.txt`**（同时进日志 INFO）写一行：手上是什么、有没有装瞄具、
  `isUsingItem` / `getUseAnimation`、`aim` / `equip` / `attackAnim` / `swinging`、举枪位移、
  **从烘焙模型里读到的 display 平移**对比 `WeaponMount` 常数（不一致会 WARN）、
  以及这一帧 `applyForgeHandTransform` / 补画手臂有没有真的被调用。

> 版本 `1.0.0-r88`

- **右键瞄准构图重塑 + 「动画盖掉代码姿态」根治**（`weapon/GunPose.java`、`weapon/WeaponMount.java`、
  `client/WeaponHandGrip.java`、各 `animations/*.json`）：
  - ★★ **横滚绕眼睛**：`GunPose.matrix` 的乘法顺序改成 `横滚 · 平移 · 腰射姿态`（JOML 里最后一个乘上去的
    最先作用在模型点上）。举枪平移已经把瞄准参照点（照门顶 / 镜筒光轴）顶到眼睛上，绕眼睛旋转时
    该点不动 ⇒ **准星永远在屏幕中心**，只有枪身绕它甩向右下。r87 写成「先平移后横滚」= 绕模型原点转，
    准星被甩飞、手与枪错开（用户反馈「瞄准不对」「手臂和枪分离」）。`transform()`（手臂 / 枪口 /
    弹道都走它）同步改成同一顺序，三者不会脱节。
  - **AKM**：`AKM_AIM_DZ` 4.0 → **−3.0**、4 倍镜 `AKM_SCOPE_AIM_DZ` 5.0 → **−3.0**（负值 = 把枪往前推）。
    正方向加到 4~8 时眼睛在机匣/枪托内部，屏幕被后挡板铺满。
  - **横滚随瞄具**（`WeaponMount.akmAdsRoll`）：机瞷 15° / 红点 8° / 4 倍镜 0°。
  - **AWP**：`AWP_AIM_DZ` 7.5 → **−3.5**（目镜 0.68 格、枪托 0.60 格，镜筒与枪身都看得清）。
  - ★★ **删掉会盖代码姿态的动画通道**（GeckoLib 的动画在 `setCustomAnimations` 之后套）：
    `awp.bolt` / `awp.reload` 里的 `bolt`、`casing`，`crossbow.idle/run/run_fast/fire` 里的 `bolt`
    与 `fire` 里的 `nock` / `string_left` / `string_right` / `move`。删掉之后 r87 的
    「拉栓行程 4.2 px」「抛壳方向翻到 −X」才真正生效；十字弩上膛后弩箭也不再被 anim 的 `y=−40` 藏住。

> 版本 `1.0.0-r87`

- **右键瞄准构图对齐 TaCZ（AKM / AWP）+ 拉栓与抛壳/自动上膛**（`weapon/GunPose.java`、`weapon/WeaponMount.java`、`client/WeaponHandGrip.java`）：
  - **AKM 举枪**：镜头前移 **1.4 → 4.0 px**，并新增 **绕视线横滚 7°**（`AKM_AIM_DZ` / `AKM_ADS_ROLL`）。
    横滚绕的是**眼点**，所以准星/光点仍钉在屏幕中心，但机匣被甩向视野**右下**、顶面露出来 —— 即 TaCZ 那种
    「枪身斜插进画面」的构图（原来是「一堵机匣墙」）。横滚在 `GunPose` 里统一施加，
    所以**渲染出的枪、手臂（`GunFrame`）、枪口/抛壳点的世界坐标**用的是同一个 `WeaponMount.toWorld(..., rollDeg)`
  - **AWP 举枪**：镜头前移 **6.0 → 7.5 px**（`AWP_AIM_DZ`），镜环更大、机匣本体基本落到近平面之后，消掉屏幕下方那片「白楔子」
  - **AWP 开火抬枪**：新增 `WeaponHandGrip.AWP_FIRE_LIFT = 2.0F`（× 后坐量），抬升量走**姿态层**（`GunPose.ADS[3]`）
    ⇒ **枪和双手一起抬**，不再是只有枪动
  - **AWP 拉栓更真**：枪机后退 **3.4 → 4.2 px**（`BOLT_BACK`）；右手拉机柄的落点与枪机**共用同一份数学**，手不会脱开
  - **抛壳方向翻转**（用户反馈原方向反了）：AKM `CASE_VX` 与 AWP `CASE_VX = −5.0` 均改为 **−X**，
    `WeaponFx.ejectCasing` 的右向量同步取反 ⇒ 弹壳往玩家**左前方**飞
  - **十字弩开火后自动上膛**：`CrossbowWeaponItem.AUTO_COCK_DELAY = 6`（帧）后自动开始 30 帧上弦（带上弦音效）

> 版本 `1.0.0-r82`

- **AWP：腰射姿态压平 + 补齐生存获取**
  - ★ **枪不再「斜着往上翘、枪托往下掉」**：枪管轴线与视线平行时，透视下它的投影必然收敛到
    屏幕正中（实测屏幕倾角 21.6°）。现在腰射给 `move` 骨骼 **`HIP_PITCH = -14°`** 的枪口下压角，
    轴线在屏幕上变成水平（-0.2°）；举枪线性归零、第三人称不加，
    **枪口 / 抛壳点的世界坐标同步转同一个角**（`WeaponMount.awpHipPitch`）
  - 新增 **`tools/_awpfp.py`（第一人称离线透视预览器）** + `tools/_awpscan.py`，本轮的角度就是它扫出来的
  - 补齐配方：`.338 狙击弹 ×4`（火药 + 铁锭）、`.338 弹药盒`（木板围框 + 中心弹 + 三铁锭）；
    AWP 进武器箱战利品池（常见箱权重 1 / 稀有箱 2，附 6 / 10 发 .338）
  - 修中文名错字：`AWP 德动狙击枪` → **`AWP 栓动狙击枪`**

> 版本 `1.0.0-r81`

- **AWP：拉栓音效 + 右手真的去拉栓 + 扣扳机看得见了**
  - 用户提供的 `模型/拉栓上膛.ogg` → `sounds/weapon/bolt_1.ogg`，新增音效事件 `ModSounds.BOLT`，
    **AKM 与 AWP 共用**（AKM 打空自动拉栓也补上了声音，以前只有动作没声）；装瞄具那声「咔」保留 `akm_bolt`
  - **击发后顿 6 帧（`BOLT_DELAY`）再拉栓**：这 6 帧右手还握在握把上扣扳机，**拉栓音效也晚 6 帧响**
    （`TAG_BOLT_SFX` 定时），不会和枪声糊在一起；`CYCLE_TICKS = 28`（≈1.4 s 一发，约 43 RPM）
  - **右手拉栓**：`rightHandPx` 把「相对 bolt pivot 的握点」按抬 62° 旋转 + 后退 1.9px，
    与枪机**共用同一份数学**（`boltLiftAt` / `boltBackAt`）—— 手永远不脱手
  - ★ **修正「扳机从来不扣」**：`animation.awp.fire` 那段 11° 键帧**永远轮不到**（击发同一帧就开
    始拉栓，控制器优先级 bolt > fire），现改成按 `fireWindow` **程序化推 `trigger` 骨骼**

> 版本 `1.0.0-r80`

- **AWP：第一人称双手**（`WeaponArms.renderAwp` + `AwpGeoModel.rightHandPx / leftHandPx`）
  - 右手握把（枪本来就画在右手位置），左手托在护木下方；换弹时左手跟着弹匣一起下坠、前倾
    （与弹匣骨骼共用 `magDropAt`，所以手与匣不会脱开）
  - 手臂经 `GunFrame` 换到相机空间 ⇒ 举枪 / 后坐 / 拉栓时**枪动、手一定跟着动**；
    离线可达性校核 `tools/_awp_arms.py`

> 版本 `1.0.0-r79`

- **AWP 栓动狙击枪整套接入**（参考包 `模型/AWP_Printstream_Minecraft`）
  - **模型**：`tools/awp_gen.py` 烘 `R_y(+90°)` + 缩放 0.75 + 逐面 UV 重映射 + 重排 512² 图集（19 px/单位），
    13 骨骼 / 58 方块 / 348 四边面；坐标约定：**枪口 = -Z、上 = +Y、原点 = 机匣中心、握把（`move`）在 (0, -1.07, 1.31)**
  - **弹道**：`.338` 初速 6.2 · **有效射程 96 格** · 射程内重力 0.004 · 命中 **24 点伤害**
    （`BulletEntity.SNIPER_DAMAGE`，用初速 >5.5 区分狙击弹，不必新增同步字段）
  - **8 倍镜**：`SCOPE_ZOOM = 8` + 圆形镜筒遮罩 + 新增 **duplex 双柱式十字分划**；HUD 显示「弹匣 + 膛内」
  - **弹药**：`.338 狙击弹` / `.338 弹药盒`（`AmmoType.SNIPER`，容量 120，快捷栏 HUD 第 4 格）
  - **音效**：用户提供的 `模型/awp枪声.ogg`、`模型/AWP狙击步枪换弹音效.ogg`（中文名由 `install_awp_sounds.py` 改名拷入）

> 版本 `1.0.0-r78`

- **手雷：切武器 = 松手（点火）、`R` 键紧急投掷**
  - 销已拔出后**切到别的武器 / 收回背包**，压杆同样算脱手 ⇒ 撞针击发、引信点燃
    （`gripped()` 判定；主手一举枪，副手那颗就等于被胳臂夹着）
  - 新增 **`R` 紧急投掷**：手上（主手或副手）有已拔销 / 引信在烧的雷时，`R` 不再是换弹而是
    立刻按准星丢出（`grenadeInEitherHand` + `serverThrow` 回退）—— 专门解决「拔完销正好碰到
    敌对生物、主手还举着枪」的处境

> 版本 `1.0.0-r77`

- **手雷 / 震爆弹：改成写实规则（撞针会真的击发）**
  - 拔销之后**必须一直按住右键**：一松手（没及时按住 / 手滑）⇒ `lightFuse()` 点燃引信，
    **5 秒内必须丢出去**，不然 `GrenadeBlasts.detonateInHand()` 在掌心起爆
  - 引信点着后插不回销了（`fuse_no_pin_back`）；**收回背包 / 换格也照样烧**，到点爆在身上
  - 新增网络包 `HOLD_CANCEL`：开界面 / 切手持物属于「手还抓着」，**不点火**
  - 副手的雷 + 主手枪械 = 被胳臂夹着（销自动弹回）—— 顺便避开「丢不出去只能等死」

> 版本 `1.0.0-r76`

- **修复 Mod 列表里的显示名乱码**：`build.gradle` 的 `mod_name` 曾被写坏成
  `閸忣厾娴夐張鍫绩`（UTF-8 双重编码），Mod 列表标题因此显示为乱码；现恢复为 `六相月灾`。
  新增 `tools/_namecheck.py`：直接读 **jar 里的 `META-INF/mods.toml`**，校验 displayName /
  description 的原始 UTF-8 字节（现在打印 `utf-8 bytes = e585ad e79bb8 e69c88 e781be` ✓）

> 版本 `1.0.0-r75`

- **月相改成随机 + 管理指令 + 手雷保险销手感**
  - 月相不再按夜数轮转：每夜独立掷骰（基础 25% + 旱情补偿），**可能连着两夜同一个月相，
    也可能连旱几十夜**；随时可用 `/hexalunar moon set|random|chance|info` 调用（`/hlc` 简写）
  - 尸潮波次推进移出血月分支 ⇒ 无月之夜用指令开的尸潮也能走完 4 波
  - 手雷 / 震爆弹：**刚拔完 1.5 秒内松手 ⇒ 保险销自动插回**；手里攥着（任何状态）
    **永远不点燃引信**（`ARMED` 只属于飞行中的抛射体，背包 / 副手 / 护甲里的雷一律折回安全态）

> 版本 `1.0.0-r74`

- **六相月灾重做：每个月相各管各的事**
  - **蓝月 / 超级蓝月 = 玩家的幸运 I / II**（`MoonBlessings` 每 40 tick 续 300 tick），
    **僵尸不再有任何加成** —— 旧版蓝月的移速修改器（`MoonSpawnEvents` 里的 `AttributeModifier`）已删
  - **黄月 / 超级黄月 = 只催作物**：每 20 / 7 tick 在玩家 18 格内抽 24 处作物替它们跑一次原版
    `randomTick`（`BlockTags.CROPS` / `SAPLINGS` 通吃）；**掉落翻倍已删**
  - **血月 / 超级血月 = 四波尸潮 + 亡灵随时间进化 + 不能睡觉**：
    尸潮固定 4 波（每波 6/9/13/18 只·人，间隔 6 秒，超级 ×1.5，第 14 天倍数那晚概率 0.75 且规模 ×1.5）；
    `ZombieEvolution.nightRamp()` 让进化概率黄昏 ×1 → 天亮 ×2；
    `PlayerSleepInBedEvent` → `NOT_POSSIBLE_NOW`；天亮 `dawnCleanup()` 清场只留 4 只孅徊者、白天不燃烧
  - HUD 第三行跟着月相走：蓝 = 幸运等级 / 黄 = 作物加速 / 血 = 进化% + 夜不能寐

> 版本 `1.0.0-r73`

- **十字弩：弦挂回弓臂桁上、上弦后弦成 V、图标也分两种姿态、离手自动退弦退箭**
  - **弦的位置（根因）**：`scale_limbs()` 原来按弓臂包围盒**中心**做 Y 方向放大（×1.25）⇒
    弓臂**桁部被抬高**，而弦还在参考高度 ⇒ 弦看上去掉在桁下面、两头也够不到桁。
    现改成**以弦面为锚点**放大：桁部原地不动、只有弓臂肚子变深。
    实测（生成器自检）：弓臂桁体素顶面 y 1.66｜弦面 y 1.70｜导轨顶面 y 1.60 ⇒ 弦正好挂在桁上、
    跟导轨顶面齐平（弩箭尾落在弦心上）。同时把弦/线缆的 `tip_x`/`str_y` 也回归参考值
    （弦半跨 5.371、弦面 1.700）。
  - **未上弦 = 未缩放的 U + 一条直线弦**（弦平行于导轨顶面）；**上弦后 = 缩小的 U + V 字形弦**：
    `draw = cocked ? 1.0F : …` —— 上弦完成后弦**保持拉着**（弦心/弩箭都在后位），击发才弹回（带弦震动）。
  - **图标（GUI / 掉落物 / 展示框）也分两种姿态**（`staticPose()` 按 `cockedNow`）：
    已上弦 → 弓臂内敛 + 弦成 V + 弩箭在槽；未上弦 → 弓臂张开 + 弦贴回弓臂之间 + 看不到弩箭。
  - **离手就自动退弦**（`CrossbowWeaponItem.inventoryTick`，判据是“主手/副手都不再拿着它”）：
    取消正在进行的上弦、`cocked` 置回 false，并**把已经上好弦的那支弩箭退回背包**
    （新增 `AmmoUtil.refund()`；创造模式/有创造弹药盒时不折腾），同时给一句提示。

> 版本 `1.0.0-r72`

- **十字弩：击发后不再自动上弦，什么时候装填由玩家决定**
  - `serverFire()` 末尾原来会立刻 `tryStartReload()`（“击发后弦复位：立刻开始下一轮上弦”）——
    现在**只把 `cocked` 置回 false 就停下**：弩箭不在箭槽、弦在初始位置、弓臂也回到张开姿态，
    图标（`staticPose()` + `cockedNow`）同步显示“未使用”样子（拿在手上 / 放在背包里都一样）。
  - **上弦入口改成两个都行**：`use()`（右键）——未上弦时右键 = 上弦装填（1.5 秒，拉弦 + 箭入槽）；
    上弦之后右键才是开镜瞮准；R 键（`serverReload`）仍旧可以用。
  - 未上弦时左键不再“自动上弦”，只空响 + 屏幕提示「未上弦：右键（或 R 键）上弦装填」
    （新语言条目 `message.hexalunar_calamity.need_cock`）；客户端也同步：没上弦时按住左键
    不会每 5 tick 刷一次请求（只在按下的那一下发一次）。
  - 跨包提示文案重写：`tooltip.hexalunar_calamity.crossbow_controls`

> 版本 `1.0.0-r71`

- **十字弩：按参考照片加回「两根线缆」（细线、交叉）**
  - 参考图（`模型/` 里的实物照片）上，两根线从两片弓臂梢斜向内、在弦前方**交叉**。
    现在在 `tools/crossbow_vox.py` 里给每侧再画一根 **0.07 像素的细线缆**（颜色 `COL_CABLE`，
    新色块 `PAT_CABLE`），它们就放在 `string_left` / `string_right` **骨骼内部** ⇒
    拉弦与弓臂内收时跟弦一起走（“使用时”的样子），静止时就是照片里那两根交叉的线（“未使用时”）。
    · 线缆长度 = 弓臂桁 + 0.85 像素（越过中线 ⇒ 交叉）；两根分别放在弦后方 0.50 / 0.66 像素、
      下方 0.26 像素处，交叉处一前一后，不会 z-fighting
  - 弦/弦心/尾羽尺寸与弓臂跨度同 r70（弦 0.07 像素、跨度 10.32）；改用它的纹理重生成后
    `crossbow_geo_glowmask.png` 也跟着重算（顺带把 r67 改了 AKM 贴图后一直没更新的
    `akm_geo_glowmask.png` 一起刷新，4% 像素的高光位置归位）
  - 离线核对：`python tools/_cb_flex.py`（弦/弦心/弩箭三者仍严格一致，四状态全 OK）

> 版本 `1.0.0-r70`

- **十字弩：弦细到 0.07 像素、拆掉假弦、弓臂再外扩、上完膛保持内敛**
  - **「又厚又分叉」的真凶找到了**：参考网格的 `string`（薄壳）与 `cables`（线缆）被体素化成
    **0.45 像素的方块串**，位置恰好压在运行时那根细弦旁边 ——
    string 在 y 1.67~1.74、|x| 到 5.37；cables 在 y 1.21~2.11、|x| 到 **5.82（比弓臂梢 5.16 还外）**。
    于是画面上是「一根细弦 + 一串粗方块」，弓臂内收时两者还会分开 ⇒ 看着就是厚 + 分叉。
    现在 `SKIP_MESHES = ('cables', 'string')`（参考 string 仍参与 TIP_X / NOCK_Z0 / 包围盒计算，
    只是不生成方块）：body 体素 **464 → 339**，body 里再无 |x|>2.2 的方块。
  - **弦与相关小件再收细**：弦方块截面 0.10 → **0.07 像素**（th 0.05 → 0.035）；
    弦心（缠绳）1.2×0.52×0.52 → **0.9×0.32×0.32**；弩箭尾羽 0.72×0.6×0.48 → **0.52×0.42×0.40**
    （从射手视角看，这三块才是「厚」的主因）。
  - **未使用时弓臂再向外扩**：`LIMB_SX` 1.9 → **2.05**（跨度 9.76 → **10.32** 像素，每侧再多探出 0.28）；
    同步 `CrossbowGeoModel.TIP_X` 4.978 → **5.371**、`STRING_LEN` 5.293 → **5.665**（`tools/_cb_flex.py` 同步）。
  - **上完膛保持内敛**：把「弓臂内收量」与「弦拉动量」拆成两个自变量（`flexAmt` / `draw`）：
    拉弦时 flexAmt 跟着 draw 走（0→1）；**装填完成（cocked）后 flexAmt 钉在 1** —— 弓臂不回弹，
    击发（cocked → false）之后才张开。弦本身仍按原设计在上膛后贴回两弓臂之间（draw = 0，
    否则弦心离镜头太近会像一根浮在弩上方的「∧」）。弦心 / 弩箭 / 左手三者的位移统一走
    `nockTravel(flexAmt, draw)`，仍然严格一致（离线自检四状态全 OK）。
  - 离线验算：`python tools/_cb_flex.py`（新增「上膛保持内敛」一行；出图用 `--bake 0 --flex 1`）

> 版本 `1.0.0-r69`

- **手雷 / 震爆弹：手上真的有动作了（拔销拽销、单手投掷、抛物线）**
  - **新增 `client/GrenadePose.java`**（碎片手雷与震爆弹共用一份）：把 `move` 骨骼姿态、左右手模型点、
    保险销 / 压把推法、手臂用的肩点全部收在这里。以前只有保险销与压把在动，
    手上完全没有动作 —— `WeaponPose` 那套 display 增量对 GeckoLib 物品**不生效**。
    · 拔销：手腕外翻 16° + 抬腕 8° + 抬手 1.6 / 前移 0.8（模型像素）；插销反向
    · 投掷：向前上方甩（rotX −34°、+Y 2.6、−Z 3.6）；拔了销以后手微微抖；另有走路摆动 + 呼吸
    · 压把：碎片手雷在背面绕 X 弹开 38°，震爆弹在 −X 侧绕 Z 弹开 42°（两个型号轴不同）
  - **第一人称双手**（`WeaponArms.renderGrenade`）：**右手**握在弹体上（模型点 1.55,−0.50,1.05；
    震爆弹 1.60,−2.20,1.15），**左手只在拔销 / 插销时伸进来抓拉环**（0,2.68,−1.65；0,2.28,−2.86），
    并跟着销一起往前移（1.05 / 1.15 像素）——**投掷时左手完全不出现**（要的就是「不是双手投掷」）。
    · 手雷专用肩点 ±(0.88, −1.18, −1.02)：雷就攥在离相机 0.7 格的地方，
      沿用持枪那套肩点会让手臂横在画面中间把雷挡住（离线故事板里一眼可见）
  - **第三人称也只有一只手**：`WeaponArmPose` 里非持雷那只手保持 `ITEM`；`WeaponPose` 的 display 增量
    也只加给右手（以前左右手都加，镜像后就是「双手一起拔销 / 一起扔」）
  - **图标不再跟着动**：两个渲染器加了 `handPass` 门控（GUI / 掉落物 / 展示框走静态姿态），
    销与压把只在「拿在手上」那遍推 —— 同 AKM 在 r64 的教训
  - **投掷力道与弧度**：初速 1.15→**1.30**（碎片手雷）/ 1.25→**1.38**（震爆弹，更轻扔更远），
    出手再加 **6° 上抬**（`GrenadeItem.THROW_LIFT_DEG`）；随机偏差 0.02→0.4（原版雪球是 1.0）
    ⇒ 平视扔出约 11 格、抬 10° 约 20 格，弹道是一条看得见的抛物线
  - **插回保险销改成「潜行 + 右键」**（`GrenadeItem.serverBeginHold` 要求 `isShiftKeyDown`）：
    以前随手右键就开始插销，丢出去前手一抖就把销插回去了；没按潜行会提示怎么插（中英文案同步）
  - 离线验算：`python tools/_gren_story.py mud|flashbang [--sh a|b|c]` → `build/_gren_mud.png`
    （上一排远景 0.45 格 / 下一排游戏视角；手心带一个小标记块，用来确认手搭在弹体 / 拉环上）

> 版本 `1.0.0-r68`

- **十字弩：弓臂再往外扩一点 + 拉弦变细**
  - **弓臂外扩**：`tools/crossbow_vox.py` 的 `LIMB_SX` **1.7 → 1.9**（弓臂/线缆/弦三个分件一起放，
    锚点仍是各自内端/ x=0）⇒ 弓臂外端 ±4.51 → **±4.88**、跨度 **9.02 → 9.76**（每侧再多探出 0.37 像素）。
    同步的 Java 常数：`CrossbowGeoModel.TIP_X` 4.454 → **4.978**、`STRING_LEN` 4.804 → **5.293**
    （= hypot(4.978, 1.80)，`tools/_cb_flex.py` 同步）；`FLEX_PX/FLEX_PZ`（弓臂弯折支点）没动，因为锚点在内端。
  - **弦变细**：画弦处的 `th` **0.075 → 0.05**（弦方块截面 0.15 → **0.10 像素** = 0.6 cm）。
    弦长/位置没变，所以拉弦数学与“弦内端落在弦心”的判据不受影响。
  - 自检：`python tools/crossbow_vox.py`（弦拉满内端 → X 0.0000 / Z −3.4000，目标一致 OK）、
    `python tools/_cb_flex.py`（拉满时外端向内 0.52 / 向后 0.82，弦内端与弦心偏差 0.00）。
  - 只换了弩的 geo（贴图 md5 未变，glowmask 不用重生）；没跑 `install_models.py`（会覆盖五行）。

> 版本 `1.0.0-r67`

- **AKM 瞄准线：“准星柱 = 照门 = 护木导轨顶面”三点共线 + 弹道归零**
  （用户反馈：手持 AKM 开火时弹道在准星下方；且举枪时应以「导管上方凸点（准星柱）与护木装倍镜的导轨顶面」为准）
  - **模型**（`tools/akm_v3.py`，新常数 `RAIL_LIFT = 0.28`）：护木顶部导轨的**齿顶从 Y=3.16 抬到 3.44**，
    与照门顶、准星柱顶同高（导轨座同时加高到 3.34，免得齿悬空）；两种瞄具整体跟着抬 0.28 ——
    红点圆心 3.79→**4.07**、4 倍镜光轴 4.00→**4.28**（`WeaponMount.AKM_DOT_Y/AKM_SCOPE_Y` 同步改）。
    因为举枪位姿只是纯平移（无旋转），模型里的水平线投影后仍是水平线 ⇒ 举枪时**三点精确落在屏幕中心那条水平线上**：
    离线验算 `tools/_ads_check.py akm_aim` ⇒ 照门顶 / 准星柱顶 / 导轨齿顶 **X +0.00% Y +0.00%**（枪管轴 −14.61% = 瞄具高出膛线 0.11 格，正常）。
  - **弹道**（`AkmRifleItem.fire()`）：枪口比眼睛低（腰射 0.32 格 / 举枪 0.11 格：枪口在枪管轴线上、瞄准线在导轨齿顶），
    而收敛距离上限原来写死 96 格 ⇒ 弹道几乎与准星射线平行、近距离就整段压低（5~60 格偏低 0.31~0.65 格）。
    改成当「归零距离」用：**举枪 16 格 / 腰射 24 格** ⇒ 5~60 格内最大偏差
    **0.65 → 0.26 格（腰射）**、**0.49 → 0.12 格（举枪）**；下限 8 格不变（太近时枪口横向偏移会被放大成大偏角）。
  - 验收工具 `tools/_akm_ballistic.py`：逐 tick 复刻 Java 的发射链（枪口模型点 → 收敛点 → 速度、再 `×0.99` 阻尼 + 重力），
    输出各距离上「弹道 y − 准星射线 y」（负 = 偏低），并扫描收敛上限 16/24/32/40/48/96 的腰射/举枪最差偏差。
  - 模型重生成后只手动装了 AKM 两个文件（`geo/akm.geo.json` md5 `0fa6a709`、`textures/models/akm_geo.png` md5 `920d278c`），
    没跑 `install_models.py`（它会一次性覆盖五把武器，会把弩/弓的现调数值冲掉）。

> 版本 `1.0.0-r66`

- **给每个月相加「月亮颜色 + 天空颜色」**：
  - 原版天空（天穹 + 日月）是在 `LevelRenderer.renderSky` 里用固定颜色画的，Forge 只给了雾色钩子，
    没有「改天穹/月盘颜色」的事件 ⇒ 在 **`Stage.AFTER_SKY`**（原版天空画完、地形之前）自己叠两层：
    · **天穹**：以相机为球心（该阶段的位姿原点就是相机，原版天体就是在 y=±100 画的）画一个半径 100 的球，
      顶点色从天顶色渐变到地平线色（下半球另封一层很淡的暗色，避免天地交界出现硬缝）；
    · **月盘**：照拄原版那两步旋转（`YP(-90°)` + `XP(时间×360°)`），在 **y=−100** 的平面上画
      本阶段颜色的圆盘（半径 20.6 > 原版 ±20，不透明 ⇒ 把原版月亮整个盖住），加三个同色系陨石坑，
      超级月相再叠一圈更大的叠加混合光晕
  - 两层都关掉深度测试/深度写入（天空在最远处、不写深度），地形随后照常把它们盖住；
    ★ 天穹的不透明度取 0.42~0.60，免得把原版星空压死
  - 全屏那层属相叠色（`skyTint`）**只留一半强度**（它同时给地形/生物上氛围色，全强度会把天空压成一片平色）
  - 配色离线预览（改色不用进游戏）：`python tools/_moonsky_mock.py` → `build/_moonsky_mock.png`

> 版本 `1.0.0-r65`

- **修「第一人称手臂巨大，一大片皮肤色挡住枪」**（用户录屏里的主要问题）：
  - 肩点原来在 `z≈−0.42`（离相机只有 0.42 格），而手在 `z≈−0.9` ⇒ 既要拉长 1.7 倍去够、近端又离镜头极近，
    屏幕上就是一大片梯形。现在肩点放到**画面下缘外约 0.8 格**（右 `x 0.55` / 左 `x −0.42`，两只手从
    下方两个角伸进来，像原版那样），肩距≈0.9 格（拉伸降到 ~1.2 倍），手臂粗细再乘 **0.85**
  - 离线可先看故事板：`python tools/_armstory.py akm`（`tools/_dblhold.py` 的肩点/粗细已与 Java 同步）
- **十字弩弓臂拉长加粗**（用户要求「像参考模型那样明显探出机身」）：
  - 参考 `模型/十字弩.bbmodel` 的弓臂是 ±6.8、而 `十字弩_v2`（现在用的这版）机身带就 ±2.8 ⇒
    弓臂只探出 0.76，看着就贴在弩身上。生成器新增 `LIMB_SX = 1.7` / `LIMB_SY = 1.25`：
    **弓臂（连同线缆、弦）绕各自内端横向拉长**（单侧分件绕内端、横跨两侧的绕 x=0，否则模型会不对称），
    外端 ±3.77 → **±4.51**、跨度 **7.06 → 9.02**；同时弩箭前端再前伸 0.5（弦心后退变多，不然拉满时箭头会缩进导轨）
  - 弦心 / 弩箭 / 左手的目标点改用**同一份** `nockTravel(draw)`（锚点被弓臂带走的位移 + 弦绷直所需的后退），
    弦内端永远精确落在弦心上（之前弓臂一放大就差了 0.36）

> 版本 `1.0.0-r64`

- **修「akm 发射和手臂都多一帧上下晃动一下」**（两个独立病因，两处都改了）：
  - **视角每发点一下头**：`camera` 空骨骼会被 `ClientEvents.applyAkmCamera` 叠到视角上，
    而动画给它的角度是**阶跃**的 ⇒ 整个视角（连枪和双臂）上下动一下。现在 `zeroCamera()` 一律清零；
    后坐只保留**沿枪管的平移**（这一条 r62 就该一起做，当时只拦了「换弹时别动镜头」）
  - **动画推在 `move` 上的 Z 也不放行**：以前只在「不在开火」时清零，于是动画首/末帧的跳变
    会让枪顿一下。现在 Z 只由 `WeaponAnim` 的冲量驱动（每 tick ×0.55 衰减，天生平滑）
  - **手臂改成算「当前帧」**：手臂比物品先画，靠渲染时捕获就永远差一帧（`akm 发射和手臂都` 里的「手臂」）；
    现在把 move 姿态收成一份共用数学（`computeMovePose`），手臂画之前先自己算 ⇒ 枪与手同拍
  - 十字弩同一套处理（`captureNow` + move 的 Z 只由后坐驱动）
- **十字弩弓臂改成「又向内又向后」**（用户要求「拉弦时弓臂向内收缩」且 r63 的 9° 太不明显）：
  - 内收角 9° → **8°**，另加**整根弓臂往射手方向后滑 0.35** ⇒ 外端实测**向内 0.49 + 向后 0.63**；
    只靠绕 Y 轴转的话外端主要只往内走（弓臂是「内端靠前、外端靠后」的斜杆），看上去就是贴着弩身
  - 弦与凸轮盘跟着弓臂走，弦心 / 弩箭的行程同步 +0.35（保持弦贴在弦心上，搭接量 0.49 仍在弦心方块内）

> 版本 `1.0.0-r63`

- **十字弩：拉弦时弓臂向内收缩**（用户要求「发射完为图片里那样，拉弦时弓臂向内收缩」）：
  - 两弓臂绕**贴导轨的内端**（模型像素 `(±1.50, -8.60)`）向内转，拉满 **9°**；
    外端因此往**内 0.55 + 后 0.31** 走，弓臂外缘宽度 7.06 → 6.24（收 **12%**）；
    `draw = 0`（未拉 / 已击发）时转角为 0 ⇒ 回到参考网格（图片）那个张开姿态
  - **弦与凸轮盘的 pivot 就在弓臂梢上**，所以它们跟着弓臂平移同样的位移（`δ = R(θ)(A−P)+P−A`），
    否则弦会跟弓臂脱开；实测弦内端相对弦心的偏差 (−0.55, +0.13)，仍在弦心方块内（±0.60 / ±0.26）
  - GeckoLib 的骨骼变换是 `pivot + pos + R(rot)·(p − pivot)`，所以「绕任意点转」是「原旋转 + pos 补偿」；
    新增 `tools/_cb_flex.py` 做离线验算与出图（`--bake` 出姿态 ×2 用 `geo_texview.py` 对比）
- **修「AKM 射击时手臂上下晃、不平行」**：手臂读的 `GunFrame` 被**图标那一遍**（GUI display）覆盖了 ——
  手臂在 `RenderHandEvent` 里比物品先画、读的是上一帧的捕获，而 r62 的门控让图标那一遍写入一套
  「无举枪、无后坐」的空值，于是枪动、手不跟着（右键瞄准时垂直错位最明显）。现在 frame **只在手持语境捕获**
- **修「物品栏里 AKM 发射时还是往后移动」**：r62 只门控了「后坐」，而 **`firing()` / 换弹进度是本地玩家的全局状态**，
  非手持语境里动画推在 `move` 上的 Z（以及弹匣下坠、弩弦回拉、抛壳）照样生效 ⇒ 现在非手持语境直接走
  `staticPose()`（静态一帧），弩的箭按被渲染那把弩自己的 `cockedNow` 决定看不看得到

> 版本 `1.0.0-r62`

- **后坐只前后动、不上下动**（用户要求「只前后动不是上下动」）：
  - `move` 骨骼上的垂直位移有三处来源 —— **fire 动画自带的 `+0.15px Y`**、r59 我加的 `KICK_UP`、
    以及 idle/run 的 Y —— 现在**全部清零**（`setPosX/Y(0)`、`setRotX/Y/Z(0)`），只留 Z；
    后坐 = 沿枪管**纯后拖**（AKM 1.35px / 弩 0.95px），冲量衰减后自己滑回去 ⇒ 真实的后坐感来自往复
  - 瞄具开镜只做**平移**（`PosX/PosY/PosZ`），不叠加任何角度 ⇒ 瞄准始终与枪管平行
- **物品栏图标不再跟着后坐跑**：GeckoLib 的 `setCustomAnimations` 对 **GUI 图标 / 掉落物 / 展示框**一样会跑，
  所以举枪位移与后坐会把**热栏里那把枪的图标**也往后推（用户反馈「物品栏物品也随之后移」）。
  现在渲染器按 `ItemDisplayContext` 记 `handPass`（第一/第三人称 = true，`AkmGeoRenderer.isHand()`），
  AKM / 十字弩 / 复合弓三个模型都按它决定推不推骨骼（详见第四节坑 17）
- **换弹 / 拉栓全程镜头稳定**：`camera` 骨骼原来在 `!firing()` 条件下才清零（换弹、拉栓也算「有动作」），
  所以换完弹那一下镜头会跟着 `bolt_pull` 的角度（0.6° / −1.1°）抖一下；
  现在**只有开火时**才把 camera 叠到视角上 ⇒ 换弹稳定、开火仍保留镜头后坐感

> 版本 `1.0.0-r61`

- **十字弩换成参考网格里那把现代复合弩**（用户要求按 `模型/十字弩_v2.bbmodel` 替换外形）：
  - 新增 `tools/crossbow_vox.py`：**表面体素化**（沿三角面密采样，采样点落在哪格就标记哪格）→
    824 个方块 / 14 骨骼，逐格从原 512² 贴图采 UV（避开「平均密度」在长条面上不准的问题，取标称密度 `step × 贴图/分辨率`）
  - 11 个 mesh 部件按名字分骨骼（弓片 → `prod_right/left`、机匣/导轨/线缆 → `body`、镜筒/握把/枪托各自成骨骼），
    **握把原点保持 (0, −0.95, 0.66)** ⇒ `WeaponArms` 的锚点、display 缩放都不用改
  - 弦面与拉弦行程重新推导：`TIP_X 6.0 → 2.62`、`DRAW_DZ 3.40 → 1.80`、`NOCK_Z0 −5.80 → −5.20`，
    弦长 = `hypot(2.62, 1.80)`，生成器自检「拉满时两段弦内端是否正好落在弦心」；弦 / 弦心 / 弩箭照旧用方块画（要能绕弓臂梢转）
  - 为什么不用 GeckoLib 的 `poly_mesh`：4.8.4 只解析不渲染（渲染侧 `GeoBone` 只有 `getCubes()`，见第四节坑 16）
- 贴图按 v2 原画重排到 480²，右边缘留一条色带给弦 / 弦心 / 弩箭 / 尾羽采样；`install_models.py` 的弩改为装 `crossbow_geo.*`

> 版本 `1.0.0-r60`

- **后坐与瞄准都保持「平行」**：原来我加的俯仰（AKM −3.2°、弩 −2.4°）加上动画自己给的角度
  （fire −2.8°、reload +7°、弩 +2.4°）会让枪和双手一起低头/抬头 —— 现在 `move` 的角度一律清零，
  后坐只后拖（+0.10px 轻微上抬），**枪口不上跳也不低头**，右键瞄准时模型也是水平的
- **十字弩上弦后弦不往后拉**（用户选择「贴在两弓臂之间」）：拉回去的弦心比弓臂梢**离镜头近 0.17 格**，
  透视放大约 17%，看起来像一根「∧」浮在弩上方 ⇒ `draw = cocked ? 0 : clamp(p/0.65,0,1)`，
  一上弦弦就弹回弓臂前面；拉弦动作本身照旧（装填期间 `draw` 0→1，能看到弦被拉回）

> 版本 `1.0.0-r59`

- **枪不再在手里晃**：原版对非空物品套的「攻击挥动」（`applyItemArmAttackTransform`，最多 `rotX −80°`）
  会被按住左键反复重触发（`LivingEntity#swing` 在 swingTime 过半时重置）⇒ 全自动射击时枪在手里不停点头。
  现在用 Forge 的 `IClientItemExtensions#applyForgeHandTransform` 接管（只保留手部基准平移，见 `client/WeaponHandGrip.java`）
- **开火时双手跟着枪一起动**：后坐改走 `move` 骨骼 —— 第一人称手臂读的就是 `move`（`client/GunFrame.java`），
  所以不需要在手臂那边重复任何武器逻辑；同时 idle / run / run_fast / 换弹 / 拉栓推的位移与俯仰一律收平
- 手臂基准 Y 跟着原版的「抬起物品」位移（`baseY() = ARM_Y − 0.6·equipNow`），切枪那几帧手也不脱把

> 版本 `1.0.0-r58`

- **AKM 抛壳动画**：抛出的是真的黄铜空弹壳（模型里 4 根 `casing_0..3` 骨骼 + 黄铜方块），
  不再只有粒子：
  - 每开一发的时刻记在 `client/AkmAnimState` 里（4 个槽轮流用），`AkmGeoModel.driveCasings`
    按「现在 − 那发的时刻」算这枚弹壳飞到哪了：右上方抛物线 + 绕 Z/X/Y 三轴翻滚，
    飞满 12 tick（≈0.6s）就 `setHidden`
  - 全自动 2 tick/发 ⇒ 同时有 4~6 枚空壳在空中，看起来就是一串往外冒弹壳
  - 弹壳真实尺寸只有 0.6px（看不见），模型里故意放大到 ~2.4px；原来的黄铜粒子/硝烟特效保留
    （第三人称与远处也能看到）
- `readme.md` / `mod/README.md` 同步到 r57

> 版本 `1.0.0-r56`

- **左手开始干活**（在 r54 的双臂基础上）：
  - **AKM**：托护木 → 抽出空弹匣（跟着弹匣一起下坠前倾）→ 满弹匣升上来时扶着往上推 →
    换到拉机柄拉栓上膛 → 回护木
  - **十字弩**：托护木 → 抓住弦往后拉（跟着弦心）→ 松手下去取箭 → 把箭推上箭槽 → 回护木；
    弩箭也改成在左手送到箭槽那一刻（p≈0.84）才出现，不再凭空冒出来
  - 新增 `client/GunFrame.java`：记下 `move` 骨骼（含举枪位移与各动画）的变换，
    手臂的目标点（模型像素）经它换成相机空间 ⇒ **手臂自动跟随举枪/换弹/开火动画**
  - `client/AkmArms.java` 升级为通用的 `client/WeaponArms.java`（双臂渲染 + 运行时摆位，
    不再靠离线算好的欧拉角），十字弩也补上了双臂
  - 新增 `mod/tools/_armstory.py`：按换弹进度渲故事板（枪 + 双臂），改手位不用反复进游戏
- `readme.md` / `mod/README.md` 同步到 r56

> 版本 `1.0.0-r55`

- **十字弩：白弦往玩家方向再拉 0.8**。拉弦行程 `DRAW_DZ` 2.60 → **3.40**
  （拉满时弦心从 z=−3.20 退到 **z=−2.40**），弩箭、弦心、凸轮盘一起跟着走：
  - 弦长必须 = `hypot(6.0, DRAW_DZ)`（6.54 → 6.896）：**两段内端只能在这个长度下才在 x=0 相遇**，
    否则拉满时弦会从中间断开（生成器 main() 里有自检会打印落点）
  - 弩箭跟着后移会让箭尖被弩身吞掉，所以箭杆/箭头同时前伸 0.8（`BOLT_EXT`），
    拉满时箭尖露出弓片前方仍然一样多
  - 凸轮盘转角按行程等比从 46° → 60°
- `readme.md` / `mod/README.md` 同步到 r55

> 版本 `1.0.0-r54`

- **子弹伤害改 10 点**：`entity/BulletEntity.java` 里提成常量 `BULLET_DAMAGE = 10.0F`
  （原来是散在 `onHitEntity` 里的 `9.0F`）
- **创造弹药盒改成“在物品栏里就生效”**：不再需要手持、也不再需要手动切弹种
  - 新增 `CreativeAmmoBoxItem.inInventory(player)`（扫快捷栏 + 背包 + 副手），
    `AmmoUtil.count/consumeOne/takeFromBox` 先问这一句，命中就直接 `Integer.MAX_VALUE` / 不扣弹
  - 删掉原来的“潜行右键轮换弹种”与 `HlcMode` NBT；tooltip 改成说明现在怎么用
- **双手持枪（第一人称双臂）**：新增 `client/AkmArms.java`，主手拿 AKM 时用玩家皮肤
  补画右手（握把）与左手（托护木），举枪时跟着枪一起挪；常数由 `tools/_dblhold.py` 离线算
- `readme.md` / `mod/README.md` 同步到 r54

> 版本 `1.0.0-r53`

- **武器模型全面重做**：四把武器 + 两种投掷物从「OBJ 网格 + display 变换」迁到
  **GeckoLib 4.8.4 骨骼模型**（`geo/*.geo.json` + `animations/*.animation.json`）：
  - AKM `bones 16 / cubes 128`、十字弩 `bones 14 / cubes 96`，另有复合弓、手雷 `mud`、震爆弹 `mtx`
  - 每个模型都有生成器（`tools/*_v3.py`）并带**自检**：骨骼名、瞄准线水平/居中、弦端点、导轨高度余量…
  - 512² 贴图由脚本逐面绘制，`tools/gen_glowmask.py` 自动出 `*_glowmask.png`
- **瞄准（ADS）数学收拢成一份单一真源** `weapon/WeaponMount.java`：
  模型像素 → 世界的完整变换链 `Trans(±0.56,-0.52,-0.72)·Trans(display/16)·R·S·(px/16)`，
  举枪时把「照门顶—准星顶」那条线顶到屏幕正中（`Tx=-8.96`、`Ty=8.32-S·anchorY`）：
  - **按瞄具改参照高度**：机械瞄具 3.44 / 红点 3.79 / 4 倍镜 4.00
  - 子弹从**枪口模型点**出发、朝准星落点飞（收敛距离夹 8..96 格），不再从屏幕中间斜着飞出来
  - 离线验算：`tools/_ads_check.py akm|akm_aim|bow|bow_draw`（0.00% / 0.00% 为过）
- **AKM 顶部导轨 + 两种光学瞄具**（新物品）：
  - **红点瞄准镜** `red_dot_sight`：开镜时枪身照旧可见，屏幕正中画红点
  - **4 倍瞄准镜** `scope_4x`：与十字弩同款整屏开镜（视野 ×1/4 + 圆形镜筒 + 十字分划）
  - 装/拆：**潜行 + 右键**（副手拿瞄具 = 装上，空手 = 拆下），状态存在物品 NBT（`weapon/Sights.java`）
- **枪械不再用 `UseAnim.BOW`**：原版对 `BOW` 的额外位移会把枪拉歪/拉长 → 改 `UseAnim.NONE`，
  举枪全部由 `move` 骨骼接管
- **开镜遮罩全程序化**：删掉整屏炫光贴图（曾把画面糊成白雾，两次反馈看不见生物），
  改为圆筒近黑遮罩 + 镜缘暗角 + 对称分划，镜内不叠任何白光
- **手部动作全部由武器本体表现**（不再有实体手方块）：
  AKM 退弹匣 → 空窗 → 新匣上行 → 拉栓；十字弩拉弦 / 装填箭矢由弦、弦卡与弩箭骨骼程序化驱动
- **月相/夜晚**：左上角天数 HUD（随月相上色）+ **僵尸进化**（`moon/ZombieEvolution.java`：
  生成即进化 3% 起每天 +1.4%、存活进化 1.2% 起每 8 秒掷一次，按天数解锁 弓箭手→爆破手→油桶兵→巨人）

> 版本 `1.0.0-r22`

- **倍镜十字不再挡视野**：原先的分划是从中心 6px 一直画到半径一半（480p 下约 100px）、
  不透明度 `0xB0`（69%）的纯白线 + 2×2 亮中心点，糊在目标上很挡视角；现改为：
  - 中心留白 9px，不再压住瞄准点
  - 分划总长压到 `min(r/3, 52)`（约为原来一半），内段 `0x74`、外段 `0x3C` 递淡，保留刻度感但不遮目标
  - 中心点缩小为 1px（`0x9C`），仍可精确对准
- 新增 `tools/scope_preview.py`：离线复刻倍镜遮罩绘制数学出 PNG，调分划参数不用反复进游戏

> 版本 `1.0.0-r21`

- **手持动作动画**（参考 SuperbWarfare 的表现，但用**程序化变换**实现，不引入 GeckoLib / Mixin）：
  - 新增 `client/WeaponAnim.java`（每 tick 推进的冲量状态机）、`client/WeaponPose.java`（折算 display 增量）、
    `client/AnimatedWeaponModel.java`（`BakedModelWrapper`，在 `ModelEvent.ModifyBakingResult` 给武器模型套上）
  - **AKM**：开火后坐（后拖 + 上抬 + 随机枪口偏摆，连发会累积）、举枪过渡、40 tick 换弹整套起伏
    （含插弹匣/拉机柄两次顿挫）、走路摆动与呼吸微漂
  - **复合弓**：拉弦把弓往身前拉、放箭向前回弹（回弹幅度按蓄力）
  - **十字弩**：开镜往画面中心收 + 开火后坐
  - **手雷 / 震爆弹**：拔销时手腕外翻使劲、引信越短抖得越厉害、出手向前上方甩
  - **第三人称手臂姿态**（`IClientItemExtensions#getArmPose`）：步枪 / 弩双手持握、瞄准改端平、手雷拔销后抬手持投
  - 数值全部用 `tools/fp_preview.py` 离线验过屏幕包围盒，不会把武器甩出画面
- **CI 自动发布**：`build.yml` 新增 release 作业 —— 推到 main 时若 `mod/build.gradle` 的版本号还没有对应 tag，
  自动打 `v1.0.0-rXX` 标签 + 建 Release 并附上 jar（版本号没变就跳过，不会重复发）

> 版本 `1.0.0-r20`

- **修复「一进世界就崩」**（日志实锤）：`GrenadeHud.render` 把 `GrenadeItem.heldGrenade()` 的 `null` 直接解引用，
  手里没手雷时每帧 NPE → `[Minecraft/FATAL]: Unreported exception thrown!` 直接崩客户端；
  `ModNetwork` 的开火/装填包也补上判空（客户端点完枪立刻切手，服务器就会 NPE）
- 新增 `tools/log_audit.py`：扫 `mod/logs`（含轮转 `.gz`）提取模组相关堆栈与关键信号
- 新增 `tools/github_ip.py` + `tools/push.py`：**每次推送自动扫描 GitHub 可用 IP**（TCP 通才再试真 TLS 握手，
  只信能完成 HTTPS 的节点）、写 hosts 并重试；VS Code 任务 `mc_push` / `mc_logs` / `mc_audit`

> 版本 `1.0.0-r19`

- **尸毒瓶获得途径**：新增配方「尸毒萃取剂 + 玻璃瓶 → 尸毒瓶 ×2」（之前无配方、也无掉落，只能创造模式拿）
- **喷吐尸掉落尸毒萃取剂**（1~2 个，受抢夺影响）—— 萃取剂不再只有剧毒骷髅一个来源
- **三把武器进箱子战利品**：新增 Forge 全局战利品修饰器 `hexalunar_calamity:weapon_cache`
  （`loot/WeaponCacheModifier.java` + `data/hexalunar_calamity/loot_modifiers/*.json` + `data/forge/loot_modifiers/global_loot_modifiers.json`），
  常见箱 6% / 稀有箱 16%，按权重抽取并附赠 8~20 发对应弹药
- 体检脚本 `tools/recipe_audit.py` 扩展为同时校验战利品修饰器（战利品表 id、物品 id、启用列表）

> 版本 `1.0.0-r18`

- **修复手持物品回归**（对照 `backup_20260917_700131` 逐项恢复）：
  - `akm/crossbow/compound_bow/bolt` 的 OBJ 又被还原成 0..16 单位（Forge 把 `v` 直接当方块 → 手里 16 倍大、离手漂浮），四把模型重新 ÷16 归一化，与拉弦变体 / 手雷模型回到同一单位
  - 三把武器的 `display` 手持参数与 `crossbow.json` / `compound_bow.json` 的 `overrides` 被改坏（拉弦变体成了死资源），按备份恢复
  - `crossbow.mtl` / `compound_bow.mtl` 丢了 `newmtl str`（弓弦材质），恢复
  - 十字弩 `getUseAnimation` 被改成 `UseAnim.CROSSBOW`：原版只有 `items.crossbow` 才走弩的姿势分支，模组弩会完全丢失手持/拉弦动作 → 改回 `UseAnim.BOW`
  - `ModClient` 丢了 `pull` / `pulling` 物品属性注册 → 拉弦动画（`pulling_0/1/2`）重新生效
  - `ModClient` 把子弹渲染器换成 `ThrownItemRenderer` → 恢复 `BulletRenderer`（弹尖朝向飞行方向）
  - `ModNetwork.sendReload()` 丢失导致 `ClientGunController` 编译失败；`ClientWeaponInput` 里重复处理 R 键会吞掉点击 → 恢复由 `ClientGunController` 统一处理
  - `CreativeAmmoBoxItem` 丢了 `inventoryTick` 自动切弹种 → 恢复（持枪时自动切到对应弹种，不再“持枪无弹”）
- **合成表**：`ammo_box_rifle` 的图案被改成 `iii/pmp/ppp`（与文档「三盒同形 `ppp/p•p/iii`」不一致）→ 恢复为 `ppp/p•p/iii`
- 新增体检脚本 `tools/recipe_audit.py`、`tools/lang_audit.py`、`tools/obj_rotate.py`

- **射击有效距离**：AKM 40 格 / 十字弩 60 格 / 复合弓 35 格 —— 射程内平直，超出后恢复重力下坠
- **第一人称手持放大**：AKM `0.68`、弩与弓 `0.62`（物品栏图标 `0.72`）
- 手雷压杆规则：握在手里不走表、离手开始 5 秒引信、潜行+右键插回保险销

- 修复 FATAL 注册回滚（`CorpsePoisonEffect` 改用 UUID）
- 修复枪械紫黑贴图：新增 `assets/minecraft/atlases/blocks.json`，OBJ 贴图迁到 `textures/models/`
- **修复模型 16 倍大与离手漂浮**：所有武器/弹丸 OBJ 归一化为方块单位并居中
- 复合弓：三段拉弦动画（程序生成的弓弦变体 + `pull`/`pulling` + `overrides`）
- 十字弩：`UseAnim.BOW` 手持姿态 + **4 倍镜**（视野 ×0.25、圆形镜筒、绿色十字线、开镜隐藏手模）
- 十字弩：弹道无重力（修复开镜打不中）+ 开镜零散布
- AKM：第一人称改为竖直握持；枪械模型整体放大（物品栏图标 0.42 → 0.72）
- 弹药盒：三个配方改为"同形不同芯"，tooltip 显示装填类型
- 新增投掷物：碎片手雷 `mud`、震爆弹 `mtx`（右键拔销 / 左键投掷 / 5 秒引信 / 背包内也会炸）
- 语言文件去重统一（中英）
