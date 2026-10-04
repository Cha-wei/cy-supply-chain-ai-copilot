# C3.1 — Apple Premium Light / Visual rationale

Human 已选择 C3；本轮只有这一版 refinement，不重新提出 C1/C2/C3 候选。此文件仅记录展示层视觉，不是 canonical 业务设计。

## 设计意图

保留 C3 的连续工作区、左侧依据与右侧人工决策关系、克制的编辑感。减轻重量来自整个系统：浅石墨工具栏、暖中性画布、暖白工作区、低对比决策面、柔和蓝灰操作，以及相同的弹窗/控件语言。没有 sidebar、KPI card grid 或新增业务模块。

导航从重色块变成应用工具栏，品牌与导航保持同一基线。它仍比内容表面深一层，但不再以白字深底抢走注意力。决定区通过轻微色阶与连续边界区分，内部不再堆叠卡片。

## Typography rationale

采用用户指定系统栈：-apple-system, BlinkMacSystemFont, SF Pro Text, PingFang SC, Hiragino Sans GB, Microsoft YaHei UI, system-ui, sans-serif。仅引用字体名称，不引入或分发 Apple 字体文件。

当前 Windows Chromium 实测为 Microsoft YaHei UI；C3.1 页面未请求 woff/ttf/otf。macOS 会依赖其本地系统字体，尚未做实机像素等价验证。历史入口仍保留其原有字体，不属于本轮方案。

中文与数字共享字体家族；数字采用 tabular-nums、60px 主数字、25px 关系数字、15px单位，单位回落到400字重。中文标题不再负tracking，正文15px/1.8行高；辅助12–13px，英文模拟标识11px。通过层级与间距体现秩序，不靠独立展示字体。

文案从“确定性计算结果”改为“根据当前供需与采购策略计算”，从字段堆叠转为“为什么建议采购100件？”的阅读起点。Evidence先给解释摘要，再分需求/采购策略；完整五项事实及原始字段只在查看完整依据中呈现。没有增加采购规则。

## Color / material rationale

| 层级 | C3.1 token | 用途 |
|---|---|---|
| Canvas | #edeeeb | 暖中性、减少原C3的灰沉感 |
| Primary workspace | #fdfdfb | 连续暖白阅读平面 |
| Toolbar | rgba(210,215,217,.68) | 保留graphite色相，降低明度反差 |
| Decision surface | #f5f6f3 | 轻微色阶区分人工判断区域 |
| Primary action | #486d84 | 比原C3蓝灰更清透，保留克制 |
| Transient / Modal | 暖白97% + 局部blur | 聚焦临时预览，正文不玻璃化 |

阴影只用于工作区与临时弹窗；内部用轻分隔，减少逐行表格边框。控件9px、决策面14px、工作区20px、弹窗22px圆角。次要操作采用透明表面与细轮廓，主要操作保持唯一明显的实色。

## Motion / boundaries

150–220ms统一语言：工具栏/按钮颜色、工作区4px进入、disclosure展开、弹窗轻微scale。AI职责改为原位展开，不为一句解释打断阅读。人工审核与草稿只有静态预览；没有批准提交、真实Draft state change或runtime调用。

Reduced motion直接呈现终态并保留焦点与文字。首屏高度只针对默认收起状态；主动展开依据或解释后允许自然增长与滚动。

## Human review question

检查整页是否达到“更轻，但保留Premium”的平衡，以及中文阅读是否比C3自然。此轮不选择其它概念、不开始完整Demo interaction implementation。
