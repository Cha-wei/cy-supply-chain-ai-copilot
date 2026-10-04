# Portfolio Demo UI v0.1 — DESIGN

状态：REVIEW · 独立实验性 presentation 工作区 · 非业务 canonical document。

This document is non-canonical for business semantics.

It does not define:
- supply-chain business rules
- runtime architecture
- production capability
- POC success criteria

## 设计意图

单页 guided decision workspace。第一视线是采购建议，第二视线是它与缺料、MOQ 的关系，第三视线是 Human decision。固定叙事：Deterministic systems calculate. AI explains. Humans decide.

界面使用英文以方便 portfolio 演示。品牌、场景、事实与交互形成纵向阅读顺序；不引入 sidebar 或管理后台。Apple-inspired 体现在留白、对齐与字体层级，不复制 macOS。

## 视觉规格

- Typography：本地系统 sans-serif，不请求外部字体。页面标题 30–43px，section 21–23px，业务主数字 65–76px；正文 12–14px，紧凑 evidence metadata 9–11px。数字保持原始 fixture 字符串。
- Spacing：主列间隔 23px；solid surface 内边距 24–29px；主段落间距约 30px。最大容器 1376px。
- Color：暖灰背景 #f5f5f3，白色内容，#22282b 主文字；柔和绿仅承载 calculation / current context；蓝 #2871c4 仅用于 primary decision。
- Radius：内容 15px，操作 8px，确认 dialog 20px。
- Elevation：数据区仅极浅阴影与细边框。只有 dialog backdrop 使用 blur。
- Components：无嵌套多层 cards、无装饰图表。30/70 的细条仅可视化固定 fixture 比例，文字提供全部信息。

## 交互与状态

1. Scenario 为只读 SIMULATED fixture；accepted 标签旁明确注明 fixture states。
2. Recommendation 固定展示 30 / 30 / 100 / 70 / 100。Evidence 原生 details 默认折叠。
3. Explore explanation 显示预制解释与五个 facts，无 AI 请求。Unavailable switch 显示解释不可用，而 recommendation 保持 100，Human 可继续依据证据决策。
4. Approve as recommended 打开原生 modal dialog，可 Escape / close / backdrop 取消，确认后才生成展示用 approved Draft。dialog 自带焦点约束与焦点回归。
5. Reject 在本次展示 context 内终止决策，不产生 approved Draft。Reset 清空所有局部状态；刷新同样清空。
6. Draft 明确 DRAFT / ephemeral，标注 Human approval ≠ production execution；不含 supplier identity 或 PurchaseOrderQty。

这里的按钮仅改变 React presentation state，不能作为 Python HITL runtime evidence。当前 scope 不实现 quantity override 或 stale / re-review；这些已存在项目能力，第一里程碑不扩展全部表面。Supplier risk evidence 未投影，UI 明确缺省，不虚构风险等级。

## Loading / empty / error

本地固定 fixture 无远程加载，不显示伪造 loading。未请求 explanation 与未 approval Draft 使用真实空状态。AI unavailable 是用户显式选择的展示态；不伪造网络错误。没有真实 validation 执行，因此不提供上传或假校验入口。

## Responsive / accessibility

Desktop 两列，<=760px 单列，390px 无水平溢出。语义 headings、nav、button、details、dialog，checkbox 有可读标签；键盘 focus ring 3px；动态结果使用 live region；文字伴随颜色说明；支持 reduced motion。移动端保留 prototype 提示、header、fixture 标记与 explanation 的模拟性质说明。

## 禁止模式

大面积渐变、neon、装饰 KPI、通用聊天窗、伪实时数据、AI 计算采购量、未验证供应商风险、自动采购、ERP / PO / production / identity / durable audit 暗示。

## 事实与设计边界

输入 baseline：96b19ea。数量来源：`../tests/test_hitl_review.py::_FIXTURE_FACT_TEXT`；Q3关系：`../tests/test_explanation_q3.py::FIXTURE_KIND`。业务 authority 为 `../docs/design/poc-design-v0.2.md` 的 Q3、§6 / §6.1、Portfolio Technical Closure。UI 不修改这些文档或任何 Python runtime。

## 审查记录

实现采取 React / TypeScript / Vite、局部 CSS 与 lucide icons。没有当前需要的 shadcn/Tailwind 组件抽象，因此不引入；无 router/global state/backend。Impeccable 在当前可用技能中不存在，使用本规格进行人工式视觉自查。

Browser review：见 README 中的验证记录与可复现命令。下一关为 Human Design Review；本版本不自动 merge、接 runtime 或扩大业务模块。
