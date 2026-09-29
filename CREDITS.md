# CREDITS · 鸣谢与第三方资源清单

《六相月灾 / HexaLunar Calamity》（mod id `hexalunar_calamity`）的**资源来源与许可总表**。
配合根目录 [`LICENSE`](LICENSE) 阅读。

> **一句话总览**
> - **代码 = MIT**（版权 2026 **七零喵团队**）
> - **美术 / 音频资产 = CC BY 4.0**（署名：**七零喵团队**《六相月灾》）
> - 第三方内容各按自己的许可（见第二节）
> - **本模组不打包任何第三方 jar**，也不包含 TaCZ 的任何素材

---

## 一、本项目原创内容

| 内容 | 位置 | 版权 | 许可 |
|---|---|---|---|
| Java 源码（枪械 / 弹道 / 月相 / 变异亡者 / 投掷物 / 合成） | `mod/src/main/java/**` | 七零喵团队 | **MIT** |
| 数据与配方（`data/**`、战利品修饰器、`lang/**`） | `mod/src/main/resources/data/**` | 七零喵团队 | **MIT** |
| GeckoLib 骨骼模型（`.geo.json`） | `.../assets/hexalunar_calamity/geo/**` | 七零喵团队 | **CC BY 4.0** |
| 动画（`.animation.json`） | `.../assets/hexalunar_calamity/animations/**` | 七零喵团队 | **CC BY 4.0** |
| 贴图 / UI 图标（含 `.obj`+`.mtl` 伴随贴图） | `.../assets/hexalunar_calamity/textures/**` | 七零喵团队 | **CC BY 4.0** |
| 音效（射击 / 换弹 / 拉栓 / 爆炸 / 警报等） | `.../assets/hexalunar_calamity/sounds/**` | 七零喵团队 | **CC BY 4.0** |
| TaCZ 枪包（AWP 试点） | `mod/tacz_pack/**` | 七零喵团队 | **CC BY 4.0**（其中 Python 生成器与说明文字为 **MIT**） |
| 生成 / 体检工具（`tools/**`、`mod/tools/**`） | 仓库根、`mod/` | 七零喵团队 | **MIT** |
| 文档（`readme.md`、`mod/README.md`、本文件） | 仓库根、`mod/` | 七零喵团队 | **CC BY 4.0** |

### CC BY 4.0 署名格式（转载我们的模型 / 贴图 / 音效时照抄一行即可）

> 模型 / 贴图 / 音效：**七零喵团队**《六相月灾》(HexaLunar Calamity)，
> <https://github.com/SevenZeroMeowTeam/hexalunar> ，许可 CC BY 4.0（若修改过请注明）。

CC BY 4.0 许可全文：<https://creativecommons.org/licenses/by/4.0/>（中文：<https://creativecommons.org/licenses/by/4.0/legalcode.zh-hans>）
**没有 NC / ND 限制**：可商用、可修改、可再分发，只需署名 + 标明改动。

---

## 二、第三方代码与库（运行时依赖，**未打包**）

| 名称 | 用途 | 本模组要求的版本 | 许可 | 是否随本模组分发 |
|---|---|---|---|---|
| Minecraft Forge | 模组加载器 | `47.4.x` | LGPL-2.1（以官方仓库 `LICENSE.txt` 为准） | ❌ 玩家自装 |
| GeckoLib | 骨骼模型 / 动画渲染前置 | `4.8.4` | MIT（以官方仓库 `LICENSE` 为准） | ❌ 玩家自装 |
| TaCZ（永恒枪械工坊：零） | **仅 `mod/tacz_pack/**` 枪包需要**，作为枪包运行时前置 | `1.1.8-hotfix` 实测 | 见其官方发布页 | ❌ 玩家自装，**本模组未包含其任何文件** |

> 说明：本模组是普通 Forge 模组，依赖由玩家自行放入 `mods/`，因此**不涉及**这些库的再分发。
> Q 弹版（`hexalunar_calamity_q`）依赖完全相同。

---

## 三、与 TaCZ 的关系（合规声明，2026-09 修订）

- **没有**复制、修改、再分发 TaCZ 的模型 / 贴图 / 音效 / 动画 / Lua / 数据包；
  TaCZ 的 jar 与官方枪包（`assets/tacz/custom/tacz_default_gun/**`）**不在本仓库、也不在 Release 里**。
- 参考的是**数据格式与接口行为**，目的是**互操作性**（让我们的 AWP 能作为一个 TaCZ 枪包运行）、
  以及**玩法与动画手感的对标**（研究其官方数值，不看它的美术资产）：
  - 枪包目录结构与 `gunpack.meta.json` 字段
  - `display/*.json` 的 `transform` / `muzzle_flash` / 音效引用规则
  - 动画轨道语义（`static` / `main` / `additive` 轨道的替换 vs 叠加差异）、状态机行为（`state_machine` 参数名）
  - 数值标定参考（持枪姿态、开镜倍率、拉栓/换弹的时序手感）
- 研究用的字节码 / JSON 转储只保存在本地 `mod/build/`（`.gitignore` 已排除 `mod/build/`），
  **不入库、不随 Release 分发**。
- `mod/tacz_pack/hexalunar_gun_pack/**` 里的模型、贴图、音效、动画 **100% 本项目自制**。

---

## 四、⚠️ 待核实清单（维护者请逐条确认，确认后把「待核实」改成结论）

> 规则：**本项目自己声明的 MIT / CC BY 4.0 不能覆盖第三方素材**。
> 来源不明或不允许再分发的，直接从仓库移除（`git rm`），不要留在历史里等 Release。

| 素材 | 现状 | 需要确认的事 | 结论（待填） |
|---|---|---|---|
| `mod/模型/awp枪声.ogg` | 已入库；是 `sounds/weapon/awp_shot_1.ogg` 的音频源文件 | □ 自制 / 合成 □ 素材站（补站名 + 原作者 + 许可 + 链接）□ 其他 | **待核实** |
| `mod/模型/AWP狙击步枪换弹音效.ogg` | 已入库；对应 `awp_reload_1.ogg` | 同上 | **待核实** |
| `mod/模型/拉栓上膛.ogg` | 已入库；对应 `bolt_1.ogg` | 同上 | **待核实** |
| `mod/模型/AWP_Printstream_Minecraft/**`（含 `使用说明.md`、`awp_printstream.png`、`bedrock/*.json`） | 已入库；说明文档自述「根据参考图（CS:GO/CS2 **AWP \| Printstream** 皮肤）制作」，含换弹 + 8 倍镜骨骼 | □ 本项目自制「风格致敬」→ 建议在包里注明「同人风格模型，与 Valve 无关、非官方皮肤」 □ 来自第三方 → 补作者 + 许可，否则移出 | **待核实** |
| `mod/模型/*.bbmodel`（`hexalunar_*`：akm / awp / kar98k / crossbow / compound_bow / flashbang / mud / m1_garand / mosin …） | 已入库 | □ 确认全部为本项目自制（默认按自制处理） | 视为自制 |
| `mod/模型/mosin_m9130/**`、`AWP_Printstream_Minecraft/*.png` 之外的本地产物 | **未入库**（本地参考/中间产物） | 无需处理 | — |
| 未来新增的每个 `.ogg` / `.png` / `.bbmodel` | — | 入库前先确认来源，并在本文件登记 | — |

**音频来源的合规提醒**：从素材站取的音效应是 **CC0 / CC BY / Public Domain** 之类可再分发的许可，
并把「站点 + 原作者 + 许可 + 链接」写进上表；**禁止**使用从游戏 / 影视 / 商业素材包里提取的音效
（例如直接截取别款游戏的枪声）—— 那属于未经许可的再分发。

---

## 五、反馈与致谢

- 问题与建议：<https://github.com/SevenZeroMeowTeam/hexalunar/issues>
- 感谢 Minecraft、Forge、GeckoLib 的维护者，以及所有在开发期提供反馈的玩家。
