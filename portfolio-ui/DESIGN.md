# Portfolio Demo UI v0.2 — 三个视觉方向

状态：READY_FOR_REVIEW / 等待 Human Design Selection。v0.1 为 technical prototype only；其视觉已被 Human REJECTED。未选择最终方向。

This document is non-canonical for business semantics.
It does not define supply-chain business rules, runtime architecture, production capability, or POC success criteria.

## 本轮边界

仅设计探索，用同一 fixture 实现三个可在浏览器观看的高保真视觉稿；不是完整 UI implementation。v0.1 的入口、fixture、交互和测试保留。新增入口 `concepts.html?concept=A|B|C`，可切换方向并打开静态 explanation / evidence / review preview，永不形成 HumanDecision 或批准记录。

用户指定 A / B / C 方向优先于 Impeccable 随机方向建议。已经运行 context 与 concept-seed（seed aaca0575）；不引入额外候选或擅自选择。PRODUCT.md 仅存本轮用户明确给出的工具上下文，不成为业务事实源。

## Concept A — Apple Decision Canvas

**构图：** 白色无卡片画布，30 + 70 = 100 横向贯穿主区域；下方解释与审核分区，以一根细线分开。

**层级：** 数字96px → 中文标题32px → 解释18–20px → 正文14px → 辅助12px。蓝色仅落在100与必要操作。

**优势：** 最直接呈现业务矛盾，适合Portfolio Hero、简历截图；弱化工具外壳，让数量关系成为记忆点。

**取舍：** 更多证据需展开；信息密度低于C，未来复杂场景需要局部重排。

## Concept B — Spatial Supply Chain

**构图：** 深石墨蓝连续场域；左侧需求/供应与缺口，中间最低起订量节点，右侧唯一的浅色建议平面。连接线仅表达因果顺序，不构成复杂流程图。

**层级：** 浅色100结果平面 → 30缺口 → MOQ100策略节点 → 底部解释与人工决定。

**优势：** 能口述“供需缺口→采购策略→建议”，三者关系一眼可见，与A/C的版式明显不同。

**取舍：** 深色更适合屏幕展示，打印和长时间阅读不如A/C；轻微平面旋转需要审查可读性。

## Concept C — Executive Decision Workspace

**构图：** 暖白证据桌面，左宽右窄；左侧大100与四行只读依据，右侧浅灰连续审核区。无sidebar，无KPI网格。

**层级：** 建议100 → 左侧计算依据 / 右侧解释 → 人工审核 → 草稿预览。

**优势：** 最适合实际决策叙事；无需展开即可理解事实和权责，高信息密度仍可扫描。

**取舍：** Hero冲击弱于A，更接近工作台；1280宽时需要特别控制纵向节奏。

## 共用设计系统与工具

Tailwind v4 @theme 定义字号、颜色、字族、间距基础、圆角与状态；布局采用utility及@apply组合。Noto Sans SC Variable中文与Manrope Variable数字通过npm自托管，不请求在线字体。主要数字72–96px；正文14px；辅助>=12px。

shadcn/ui Tabs / Dialog / Button 从官方 new-york-v4 registry 取源，保留Radix键盘与焦点能力，修改导入路径、中文关闭按钮与样式。无默认Card组件。Sources: https://ui.shadcn.com/r/styles/new-york-v4/tabs.json 、dialog.json、button.json；MIT，shadcn。

所有视觉稿使用完全相同的src/fixture.ts，不改业务规则、不连接Python、没有真实AI请求、审批或采购执行。表面颜色不表达新业务状态。

## Motion concept（仅规格，不实现复杂动效）

- A：100以180ms淡入强调结论，30与70保持可见；不从0计数以免暗示重新计算。
- B：关系线按阅读顺序在220ms内展开；结果平面保持静止，不做parallax或弹跳。
- C：依据展开180ms，焦点留在触发器；未来审核确认使用180ms opacity transition。
- 三者未来Draft状态转换仅在真正的demo confirmation之后，180ms；当前只有静态preview。
- reduced motion：直接显示最终状态，保留焦点与文字反馈。

## Process / review

Impeccable 4.5.0技能已安装，engine 0.1.11 context与concept-seed成功。已读取new-work、craft-floor、critique、audit。

Concept Design：首稿已完成；浏览器1440/1280/390各三方向截图保存在design-reviews/initial/。
Impeccable Critique：已完成两个独立只读子代理评审，见 design-reviews/critique.md。
Revision → Impeccable Audit → Revision：已完成，见 design-reviews/audit.md；最终截图与测量位于 design-reviews/final/。
Human Design Selection：当前下一关；A为建议，不构成Human选型。

当前审阅范围不包括完整系统可用性、业务验证、runtime correctness或真实客户价值。
