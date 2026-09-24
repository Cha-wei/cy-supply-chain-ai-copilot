# POC Design v0.2

**Document:** POC Design
**Version:** v0.2
**Status:** `DRAFT`
**Phase:** POC Design
**Entry Gate:** `READY`

**继承的 FROZEN baseline：**

- `docs/discovery/discovery-brief-v0.1.1.md`（v0.1.1，`FROZEN`）
- `docs/discovery/discovery-validation-v0.1.md`（v0.1，`FROZEN`，Human-approved，Frozen Date 2026-09-21）

> **文档性质**：本文件是 **POC Design 阶段的 Canonical Source**。
>
> **Authority clarification**：本文件继续作为 POC Design 的 parent / overall canonical design document；显式 externalized 的 topic spec 是其 concern 的唯一 canonical source，本文件对该 concern 只保留导航 / 状态入口。
>
> 它**继承**上述两个 `FROZEN` baseline，但**不得重新解释或覆盖** FROZEN Discovery 的任何内容。
>
> **当前状态**：`DRAFT`。本文档继承已冻结的 Discovery Baseline，并已包含若干已经 Human-approved、状态为 `DESIGN RESOLVED` 的 P0 business rules；**尚未解决的设计项继续登记为 `DESIGN PENDING` / `NOT STARTED`**。
>
> **`DESIGN RESOLVED` 不代表 `IMPLEMENTED`，也不代表 `TESTED`**；本文档**未获得** `APPROVED` / `FROZEN`，也**仍未包含**任何 implementation code。

---

## Language Convention

本文档采用：

- **正式说明默认中文。**

以下保留 English：

- technical identifiers
- code elements
- filenames / paths
- API / DB fields
- Git / GitHub metadata
- formal status words
- necessary technical terms

例如：`DRAFT`、`FROZEN`、`READY`、`Adapter`、`HITL`、`RBAC`、`Rule Engine`、`Mock API`。

不强行全部翻译为中文，也不把整篇文档写成英文。

---

## Design Principles Inherited from Discovery

本节登记**已经成立的设计约束**，**不扩展为具体 Architecture**。

### 事实与计算

Structured facts 来自受控数据源 / Tool。

LLM **不创造**：

- Inventory
- BOM
- Purchase Order
- Lead Time
- Supplier Performance
- deterministic calculation result

确定性问题**优先使用 deterministic logic**。

### AI Boundary

LLM 主要负责：

- natural-language understanding
- orchestration
- explanation
- recommendation presentation

**不得**让 LLM 替代可确定性实现的业务计算。

### HITL

AI **可以**生成：

- Procurement Recommendation
- Procurement Request Draft

AI **不可以**：

- Approve
- Formal Submit
- Create Purchase Order
- Override Approval

**最终采购决策属于 Human。**

### Integration

当前 POC Integration baseline：

- **Controlled Export / Snapshot**
- Source-system write：**`DENIED`**
- Production write-back：**`OUT OF SCOPE`**

### Simulation Boundary

> **Fake the enterprise environment, not the product behavior.**

**模拟：**

- enterprise data
- ERP / WMS / PLM logical environment
- enterprise integration interface

**真实实现：**

- application behavior
- deterministic business logic
- Tool orchestration
- HITL
- permissions
- tests / evals
- audit behavior

---

## 1. Design Goals & Scope

> **Current canonical wording（Issue #112）：** 以下四项依据 FROZEN Discovery、GSD-1 ～ GSD-7 与 current-main composition 定稿；S-1 ～ S-14 verification 全部 PASS，closure 见 §1.18 ～ §1.20。
> **历史读取边界：** §1.1 ～ §1.17 的 Review、candidate、各 Issue 的 current-state / registration 时点记录保留；其中旧 PENDING / NOT AUTHORIZED / NOT EXECUTED 不代表本次 closure 后状态。已批准 Decision 与 §1.7 criteria 的约束继续有效；最新执行状态以 §1.20 为准。

### P0 设计目标

**Design Status:** `DESIGN RESOLVED`

依据 [FROZEN Discovery Brief](../discovery/discovery-brief-v0.1.1.md) §10 ／ §11（FZ-1 ／ FZ-2），本 POC 的设计目标是：让 AI 基于企业已有生产计划、BOM、库存、在途采购与必要供应商信息，完成**受控**的跨系统数据获取，通过**确定性业务规则**计算缺料风险，生成**有数据依据、可解释、可追溯**的采购建议。

P0 保持 **缺料分析 → 采购建议 → HITL** 单一闭环。AI 组织和解释确定性结果，只生成 **Procurement Request Draft**；Human 在 POC 内 Review / Modify / Approve / Reject，正式业务系统执行在 POC write boundary 之外（Discovery Brief §11；[FROZEN Discovery Validation](../discovery/discovery-validation-v0.1.md) VR-004 ／ VR-007；§3.6 ～ §3.8）。受控意味着只访问授权数据和工具；可解释意味着说明所用数据与风险依据；可追溯意味着可复现 Tool、数据、规则与建议形成过程。

按 GSD-2 的 **strict limited-reference** 边界：§2 支撑确定性业务计算，§3 支撑受控系统／读写／草稿边界，§4 的六份 canonical specs 支撑数据／验证／映射／integration，§5 支撑 AI／确定性逻辑／Tool／Agent 职责。详细 authority 仍在这些章节及 §4 routing 指向的 specs；此处不复制公式、字段、contract 或 implementation detail，也不把 supporting design 提升为新目标或成功证据。

### POC 成功边界

**Design Status:** `DESIGN RESOLVED`

继承 Discovery Brief §16 ／ §17，按 GSD-3（§1.13）采用三层责任／证据成熟度模型：

- **Layer 1 — Design-time success boundary：** 定义目标、scope、确定性规则、受控系统／数据／AI 职责与安全、解释、追溯要求，以及 §6 ～ §9 应尊重的 dependency expectations；本层只能证明 design boundary defined。
- **Layer 2 — Runtime / test evidence boundary：** 后续 implementation、integration 与 §9 需提供系统按批准设计实际运行的证据；本节不定义具体 test case、dataset、harness、threshold、rubric 或 scoring。
- **Layer 3 — Business-value evidence boundary：** 后续需依据真实客户／流程 baseline 证明明确业务改善；模拟设计、Demo 可运行、单项 test pass 均不能替代该证据。

**FROZEN §16 全部 success dimensions 的责任映射：** 三层不是互斥 bucket，同一维度可以同时有 design obligation 与 evidence obligation。

| FROZEN dimension | Layer 1：设计责任 | Layer 2：未来 runtime / test evidence | Layer 3：业务价值关系 |
| --- | --- | --- | --- |
| 数据正确 | 受控且正确的数据来源，LLM 不创造库存／订单／价格事实；§3、§4、§5 | 证明实际数据获取、validation、mapping、import 符合批准设计 | 技术正确不单独证明业务改善 |
| 计算正确 | §2 确定性规则；相同输入稳定、一致、可复现 | 证明实际实现与批准规则一致且结果可复现 | 计算通过不单独证明业务改善 |
| 工具正确 | §5 授权 Tool 与 Agent 职责；无明显无意义或越权调用 | 证明 Tool selection / runtime behavior 正确、受控 | 调用通过不单独证明业务改善 |
| 可解释 | 关键风险必须有数据依据与规则依据；§5 evidence fidelity | 证明解释不篡改结果、不静默补齐缺失／无效证据 | 解释效果的真实改善由业务 evidence 证明 |
| 安全 | 未经人工批准禁止高风险写操作；当前 POC source WRITE = DENIED，人工批准也不解除该边界 | 证明 Human／workflow／permission 边界实际 enforce，fail-closed 有证据 | 安全控制不替代业务价值证明 |
| 业务价值 | 保留至少一种明确改善的目标与 evidence obligation，不预设数值 | runtime evidence 可支撑业务评价，但不能单独证明真实收益 | 与当前流程比较，至少证明减少系统切换、减少人工汇总、降低分析时间、提高异常解释效率等一种明确改善；真实 KPI 数值须等待客户真实 baseline |

**Failure / reassessment boundary（FROZEN §17，完整保留其条件语义）：** 以下是后续判断是否应继续扩大 POC／重新评估的条件，**不是已发生事实**：关键生产、BOM、库存和采购数据无法可靠获取；主数据无法建立稳定关联；现有 MRP / ERP 已能高效完成全部缺料分析时不应重复建设；业务发生频率极低可能导致投入回报不足；引入 Agent 后流程更复杂、执行步骤更多、业务人员负担反而增加时需要重新评估技术方案。这些条件不被删除、弱化或并入自创 success score。

```
Design closure
≠ Implemented
≠ Runtime validated / Tested
≠ Business value proven / accepted
≠ POC SUCCESS
≠ Production-ready

POC success = NOT CLAIMED
```

`POC SUCCESS` 是 evidence claim；后续须依 Human-approved acceptance / evidence policy，综合 applicable runtime-test evidence **＋** business-value evidence 与 FROZEN success dimensions 的满足情况。本节不创建最终 success gate，不宣称真实客户 baseline、usage frequency、adoption 或 business acceptance 已取得；FROZEN H3 / H4 状态不因 downstream simulated design 改变。

### In Scope

**Design Status:** `DESIGN RESOLVED`

按 GSD-4（§1.14）组织，三类只用于明确业务能力、支撑责任与控制义务，不构成新授权：

| Canonical category | 内容与 authority | 边界 |
| --- | --- | --- |
| P0 capability scope | 缺料分析、采购建议及风险证据、Procurement Request Draft 与 POC 内 Human Review / Modify / Approve / Reject；Discovery Brief §10 ／ §11，§2、§3.2 ／ §3.6 ～ §3.8、§5.3 ～ §5.4 ／ §5.15 | §2.7 Supplier Risk 只支撑 P0 风险证据，不是 P1 高级供应商比较／自动选择；§5.3 六类 SIMULATED questions 只解释 P0 outputs，不是 P1 广义自然语言供应链查询 |
| Supporting infrastructure | Controlled Export / Snapshot、canonical data / dictionary、import / validation / mapping / Adapter conceptual boundary、Controlled Tool 与 Agent responsibility；Discovery Validation VR-007，§3、§4 routing 指向六份 canonical specs、§5.13 ～ §5.14 | 为既有 P0 提供支撑，不成为新 P0 capability；不选择技术组件，不授权 implementation |
| Quality / safety boundary | 确定性、正确性、explainability、traceability、evidence fidelity、permission、fail-closed、auditability；Discovery Brief §10 ／ §16，§3.9 ～ §3.10、data-validation.md §4.4.2 ～ §4.4.13、§5.5 ～ §5.10、§1.14 GSD-4.3 | 是控制／证据义务，不是新业务场景；不定义 test harness / KPI / threshold，不推进 §7 ／ §9 ／ §10 |

相关事实可以同时承担 supporting 与 quality obligation；上述表按主要职责定位，详细规则保持原 canonical authority，避免重复定义。

### Out of Scope

**Design Status:** `DESIGN RESOLVED`

保持 **Out of Scope ≠ P1 ≠ Prohibited ≠ Deferred**（GSD-5，§1.15）。下表逐项以已批准 category semantics 与原始 authority 重新核验；**不采用**旧 §1.4 C 的固定 routing order、first-match 或互斥 bucket 规则，也不自动接受其 candidate placements。

| Primary classification | 具体事项 | Canonical authority 与重新核验理由 |
| --- | --- | --- |
| Out of Scope | 完整 ERP / MRP 替代 | Discovery Brief §19 Scope Validation 明确 POC 不承担该职责；属于业务范围排除，不是待实现承诺 |
| Out of Scope | 正式 ERP Purchase Request / Purchase Order execution、Production write-back 业务能力 | Discovery Brief §11 P0-3、Discovery Validation VR-007 C、§3.1 ～ §3.2 ／ §3.6 ～ §3.8；POC 提供 Draft／Human interaction，正式执行在外部 |
| P1 | 企业知识库／RAG；高级供应商比较；自然语言供应链查询；自动供应链分析报告 | Discovery Brief §12 四项后续增强；不属于第一阶段 POC 成败核心，不提升为 P0，也不是永久排除或禁止 |
| Prohibited | 绕过 Controlled Export 直连源系统／Production DB，扩大 source access | Discovery Validation VR-007、§3.3 ～ §3.4 ／ §3.10；当前明确禁止的访问路径，不是普通 Deferred backlog |
| Prohibited | 执行 source-system write／Production write API，AI Approve／Formal Submit／Create Purchase Order／Override Approval，绕过 Human／workflow／permission boundary | Discovery Validation VR-004 ／ VR-007、§3.5 ／ §3.7 ～ §3.9、§5.10 ／ §5.15；当前行为禁止；Human 在 POC Approve 不授予生产执行能力 |
| Prohibited | LLM 自行创造结构化业务事实、改写确定性结果、以猜测或旧聊天伪装当前事实、越权调用 Tool | Discovery Brief §16、§5.6 ～ §5.10 ／ §5.12 ～ §5.14；已批准 hard boundaries，不新增禁止项 |
| Prohibited | 将 SIMULATED 证据表述为真实客户／企业事实 | Discovery Validation §2、§5.0 ／ §5.17；证据来源不能因设计完成被升级 |
| Deferred | §6 完整 HITL workflow；§7 RBAC／Data Scope／Tool Permission／Secret Handling；§8 audit／observability；§9 具体 tests／eval／acceptance method | 各章明确列为未来设计，GSD-6（§1.16）只登记依赖；§7 Read / Write Boundary 已 resolved，不能被整体退回 pending |
| Deferred | §10 Architecture／framework／database／API／deployment／ADR 的后续决定 | §10 与全局 Explicit Non-Decisions；本次不作选型，不要求 §10 永远无 ADR |
| Deferred | runtime／source-specific／Adapter realization、具体 source table / column 与真实 ERP mapping | §3.14、master-data-mapping.md §4.5.24 ～ §4.5.25、adapter-boundary.md §4.6.21 ～ §4.6.22；当前未实现／未授权，不等于永久排除，也不承诺一定实施 |

**跨维度关系：** Production write-back 的“业务能力在范围外”与“执行写操作被禁止”分别说明 scope 和 behavior，二者在上表各自有明确 primary classification，指向同一 §3 authority，不重复定义规则，也不因未来工作暂缓而削弱当前禁令。HITL 等 responsibility 属 In Scope，其详细设计为 Deferred；这描述 scope 与 design maturity 两个维度，不把它排除出 POC。已批准 JSON serialization 不列为 Deferred（冲突处置见 §1.19 B）。

**Downstream dependency expectations（GSD-6）：**

| 下游 | §1 要求其尊重的责任 | 独立现状 |
| --- | --- | --- |
| §6 | 保持 Draft／Human Review / Modify / Approve / Reject 与 external execution 的边界，不绕过重新审批要求 | 完整 workflow / state machine `DESIGN PENDING` |
| §7 | 保持 user／scope／Tool／workflow／POC policy 权限交集和 secrets 边界 | Read / Write Boundary `DESIGN RESOLVED`；RBAC、Data Scope、Tool Permission、Secret Handling `DESIGN PENDING` |
| §8 | 追溯业务决策、Tool、规则版本、Human approval 与 failure | 具体 audit / observability `DESIGN PENDING` |
| §9 | 提供适用的确定性、integration、AI Eval、HITL／business acceptance evidence | 具体测试／评估设计 `DESIGN PENDING`；本节不定义 harness、KPI、threshold |
| §10 | 后续技术决策遵循 Options → Trade-offs → Recommendation → Human Approval → ADR | 当前 `No ADR created yet.`；本次不选择 Architecture |

`Downstream pending ≠ Automatic §1 closure blocker`；`Dependency expectation ≠ Downstream design completion`。以上仅规定需尊重的高层责任，不定义实现机制；§1 closure 不传递为 §6 ～ §10 resolved 或 implementation authorization。后续若发现真实 scope 冲突，应经独立 Design Change／Human Decision／canonical synchronization 处理，不得静默反向改写目标。

### 1.1 Review Authority / Scope（review-only）

> **本节为 review-only Design Review 产出，不是 approved policy。**
> `Review Finding` ≠ approved policy；`Candidate Option` ≠ selected option；
> `Proposed Closure Criteria` ≠ Human-approved closure criteria；
> **只有 Human Decision 才能把候选转为 canonical policy。**

```
Review Type    = 独立 Design Review（只产出 Review Finding）
Review Object  = §1 Design Goals & Scope（当前 4 项 = DESIGN PENDING）
Decision Power = NONE —— 本 Review 不作出任何 Human Decision
Write Scope    = §1 内 review-only 子结构（＋ project-index navigation-only sync）
Status Change  = NONE（§1 保持 DESIGN PENDING）
```

本 Review **只**做：① 从 `FROZEN` Discovery 提取 §1 必须继承的 scope ／ success ／ failure 约束；
② 从 current canonical `§2` ～ `§5` 提取会影响 §1 表述的已批准 downstream design facts；
③ 区分 inherited fact ／ approved downstream fact ／ design gap ／ Human Decision Required；
④ 建立 candidate options ／ trade-offs；⑤ 提出 candidate minimum closure criteria；
⑥ 列出需 Human 逐项裁定的问题。

本 Review **不做**：选择 final option、修改 P0 ／ P1、把 §1 推进为 `DESIGN RESOLVED`、
设计 `§6` ～ `§10` 或 implementation、修改 `FROZEN` Discovery。

**identifier 约定（本节局部，不与既有 identifier family 冲突）：**
`FZ-*` = inherited `FROZEN` constraint；`GSF-*` = §1 Review Finding；`S-*` = candidate closure criterion；
`GSD-*` = Human Decision Required 条目；`§1 Option 0 ／ 1 ／ 2` = 本节 candidate conceptual approach
（**不**沿用 `§4.3` ／ `§10` 等其他章节的 Option 编号）。

### 1.2 Inherited FROZEN Constraints（不得重新打开）

| # | 继承约束（`FROZEN`） | 来源 |
| --- | --- | --- |
| `FZ-1` | **Problem Statement**：AI 基于企业已有生产计划、BOM、库存、在途采购与必要供应商信息，完成**受控**的跨系统数据获取，通过**确定性业务规则**计算缺料风险，并生成**有数据依据、可解释、可追溯**的采购建议。三个核心要求 = **受控** ／ **可解释** ／ **可追溯** | Discovery Brief `§10` |
| `FZ-2` | **P0 = 一条业务闭环**：缺料分析（P0-1）→ 采购建议（P0-2）→ Human-in-the-loop（P0-3）。AI **只能**生成**采购申请草稿**，**不得**直接产生正式采购执行 | `§11` |
| `FZ-3` | **P1 = 后续增强**：企业知识库 ／ RAG、高级供应商比较、自然语言供应链查询、自动供应链分析报告 —— **不属于**第一阶段 POC 成败核心 | `§12` |
| `FZ-4` | **成功标准**：`POC 成功 ≠ Demo 能够运行`；至少覆盖 数据正确 ／ 计算正确 ／ 工具正确 ／ 可解释 ／ 安全 ／ 业务价值；LLM 不得自行生成库存 ／ 订单 ／ 价格等事实；相同输入下确定性计算稳定、一致、可复现；不得明显无意义或越权调用工具；关键风险必须含数据依据 ＋ 规则依据；未经人工批准禁止高风险写操作；至少证明一种明确业务改善；**真实 KPI 数值必须等待客户真实 baseline** | `§16` |
| `FZ-5` | **失败 ／ 重估条件**（`FROZEN` failure boundary，**不是**当前已发生事实）：关键数据无法可靠获取；主数据无法稳定关联；现有 `MRP` ／ `ERP` 已高效解决全部目标问题；使用频率过低；AI ／ Agent 使流程更复杂、步骤更多、业务负担上升 | `§17` |

> `FZ-1` ～ `FZ-5` 为**已冻结的继承事实** —— 本 Review **不得**重新设计、重新解释、改变其语义，
> 也**不得**把 `FZ-4` 的 success dimensions 写成已达成、把 `FZ-5` 的 failure conditions 写成已发生事实。
> `FROZEN` `§19`（v0.2 Entry Criteria）的 P0 scope 表述（`缺料分析 → 采购建议 → HITL`、`POC 不承担完整 ERP/MRP 替代职责`）
> 与 `FZ-2` 一致，作为 inherited 参照，**不**新增 scope 语义。

### 1.3 Current Approved Downstream Facts（`§2` ～ `§5`）

| 章节 | 已批准 downstream design fact | 当前状态 |
| --- | --- | --- |
| `§2` | P0 business rules `§2.1` ～ `§2.7` **全部** `DESIGN RESOLVED`（`BR-SHORTAGE-001` ／ `BR-INVENTORY-001` ／ `BR-SUBSTITUTE-001` ／ `BR-REQUIREMENT-001` ／ `BR-PROCUREMENT-001` ／ `BR-INBOUND-001` ／ `BR-SUPPLIER-RISK-001`）；本节范围内无 `DESIGN PENDING` 项；并明确**不表示** `POC Design v0.2` 整体完成 | `DESIGN RESOLVED` |
| `§3` | System Boundary：Integration Pattern = **Controlled Export / Snapshot**；`READ` **只能**经 controlled exported snapshot；`WRITE = DENIED`；`Production Write-back = OUT OF SCOPE`；`Implementation Status = NOT STARTED` | `DESIGN RESOLVED` |
| `§4` | Canonical Data Model ／ Data Dictionary ／ Snapshot ／ Import Contract ／ Data Validation ／ Master Data Mapping ／ Adapter Boundary **全部** `DESIGN RESOLVED`（`§4` 现有 **0** 个 `DESIGN PENDING` 子领域）；`Adapter Boundary` 为 **conceptual closure** —— 其 runtime ／ source-specific realization 仍 `NOT IMPLEMENTED` 且**未**获 implementation 授权 | `DESIGN RESOLVED`（conceptual） |
| `§5` | AI ／ Tool Boundary：`LLM` ／ deterministic business logic ／ `Tool` ／ Agent orchestration 四层的 responsibility ／ behavioral boundary `DESIGN RESOLVED`；`§5.3` 登记 **6 个 P0 User Questions** 的 **`SIMULATED`** high-frequency question baseline（`SC-EXPLAIN-001`）；`Implementation Status = NOT STARTED`；`FROZEN` `H4` **未** resolved | `DESIGN RESOLVED`（boundary） |
| `§6` ／ `§7` ／ `§8` ／ `§9` | HITL state machine ／ `RBAC`-`Data Scope`-`Tool Permission`-`Secret Handling` ／ Audit & Observability ／ Test & AI Eval | `DESIGN PENDING`（`§7` 仅 `Read / Write Boundary` 为 `DESIGN RESOLVED`） |
| `§10` | Architecture Decisions | **尚无正式 ADR**；技术栈未决定 |

> **必须区分（candidate interpretation，供 Human 裁定）：** 上述 `DESIGN RESOLVED` **只**表示
> **conceptual ／ canonical design boundary 已定义**，**不表示** `IMPLEMENTED` ／ `TESTED` ／
> business accepted ／ production-ready（与 `§3` ／ `§5` 头部及 `§7` ／ `§8` ／ `§9` status boundary 一致）。
> 因此 §1 **不得**因为 `§2` ～ `§5` 已 `DESIGN RESOLVED` 就宣称 POC success 已满足（见 `S-9`）。

### 1.4 Scope Composition Review

**A. §1 的职责边界（Q1 —— candidate）**

§1 **应只**登记：

```
POC design goals（goal 层，不是 architecture 层）
POC success boundary（design-time ／ evidence ／ business-value 分层）
In Scope（P0 capability scope ＋ supporting design ／ quality ／ safety infrastructure 的分类）
Out of Scope（business out-of-scope ／ deferred ／ prohibited ／ P1 四类分离）
与 §2 ～ §10 的 composition ／ dependency boundary
```

§1 **不得**成为：architecture 章节、产品需求大全、implementation plan、测试计划、客户验收结果。
以上为 **candidate**；最终职责边界由 `GSD-1` ／ `GSD-2` 裁定。

**B. In Scope 候选分类（Q4 —— candidate）**

| 分类 | 候选内容 | 与 `FROZEN` 的关系 |
| --- | --- | --- |
| **P0 capability scope** | deterministic 缺料分析（需求 ／ 预计可用量 ／ 预计缺口 ／ 基础风险）；采购建议；`Procurement Request Draft`；POC 内 Human `Review` ／ `Modify` ／ `Approve` ／ `Reject`；explanation（解释结果） | 直接对应 `FZ-1` ／ `FZ-2`（P0-1 ／ P0-2 ／ P0-3） |
| **P0 supporting data capability** | Controlled Export ／ Snapshot 数据获取；Data Validation；Master Data Mapping；Adapter conceptual boundary；`Stable Source Evidence Locator` ／ `Mapping ／ Resolution Basis` | `FZ-1`「受控」＋「可追溯」的实现方式；`FZ-2` 的输入前提 |
| **P0 quality ／ safety boundary** | fail-closed；traceability；evidence requirement；determinism；no silent exclusion；Human approval before high-risk write | `FZ-1`「可解释 ／ 可追溯」＋ `FZ-4` 的 数据正确 ／ 计算正确 ／ 工具正确 ／ 安全 |
| **不是 In Scope 的新业务场景** | 任何不在 `FROZEN` `§11` P0 闭环内的业务场景（例如完整 MRP 替代、Production 采购执行、P1 能力） | 违反 `FZ-2` ／ `FZ-3` |

> **candidate 要求：** supporting design ／ quality ／ safety infrastructure **只**作为 **supporting infrastructure** 登记，
> **不得**被改写成新的 P0 business scenario（见 `S-3` ／ `S-4`）。

**C. Out of Scope 候选分类（Q5 —— candidate）**

四类**必须分开**，不得压平为一个「都不做」：

> **current-state（Issue #102）：** **四类分离**本身已由 **`GSD-5`** Human Approval 登记为 canonical
> classification model（见 **`§1.15`**）；本节以下的**分类规则、具体条目归类与判定顺序**仍为本 Review 的
> **candidate** 内容，final §1 Out of Scope canonical wording 属后续独立 Design Change ／ Closure。
> **`GSD-7`（Issue #106）的 `S-4` 明确：** 本节的固定判定顺序、先命中者为准、现有 candidate item
> placement 与 bucket routing 细节**不**因该 criterion 被自动批准；未来 Closure PR 若使用它们，
> **必须**基于 `GSD-5` 已批准的四类语义重新验证（见 **`§1.7`** ／ **`§1.17`**）。

**分类规则（candidate）：** 四个 label 是**互斥 bucket**，**不是**同一 item 可重复落入的维度标签。
每条候选 item **只**归入一个 bucket；判定按以下顺序进行，先命中者为准：

```
1. Prohibited（hard boundary —— 行为禁止）
   —— 该行为是否被 current approved canonical text（§3 hard boundary ／ FZ-4 等）明确禁止？
2. P1
   —— 该能力是否属 FZ-3 列出的后续增强？
3. Deferred
   —— 该事项是否属本 POC 范围，但当前设计层未完成（§6 ～ §10）或 implementation 未开始？
4. Business scope out-of-scope
   —— 其余：不属于本 POC 业务闭环的业务能力 ／ 结果
```

| 分类 | 判定问题（互斥） | 候选内容 | canonical 依据 |
| --- | --- | --- | --- |
| **Business scope out-of-scope**（业务能力 ／ 结果**不属**本 POC） | 「本 POC **是否提供**该业务能力 ／ 结果？」→ **否** | 正式 `ERP` `Purchase Request` ／ `Purchase Order` execution；完整 `ERP` ／ `MRP` replacement；其他明确不属 P0 闭环的业务结果（例如完整供应链 Copilot 平台能力） | `FZ-2`（P0 = 缺料分析 → 采购建议 → HITL；AI 只产出采购申请草稿）；`FROZEN` `§19`（POC 不承担完整 ERP ／ MRP 替代职责） |
| **Deferred**（本 POC 范围内、当前**未完成**） | 「该事项是否属本 POC 范围，但当前设计 ／ 实现**未完成**？」→ **是** | `§6` HITL state machine；`§7` `RBAC` ／ `Data Scope` ／ `Tool Permission` ／ `Secret Handling`；`§8` audit ／ observability；`§9` test ／ eval ／ acceptance method；`§10` Architecture ／ ADR；implementation | `§6` ～ `§10` status boundary（`DESIGN PENDING` ／ `No ADR created yet`）；`§3` ／ `§5` `Implementation Status = NOT STARTED` |
| **Prohibited**（hard boundary —— **行为禁止**） | 「**执行该行为**是否被 current approved canonical text **明确禁止**？」→ **是** | direct source-system ／ Production DB access（即**绕过 Controlled Export**）；在本 POC 当前 `§3` boundary 下执行 production write-back ／ write API 调用；未经人工批准的高风险写操作；LLM 自行生成库存 ／ 订单 ／ 价格事实；silent exclusion ／ silent normalization；把 unsupported ／ unresolved 压平为正常 missing | `§3`（`READ` 只能经 controlled exported snapshot；`WRITE = DENIED`；`Production Write-back = OUT OF SCOPE`）；`FZ-1`「受控」；`FZ-4`（LLM 不得自行生成事实；未经人工批准禁止高风险写操作）；`§4` 已批准 policy（no silent exclusion ／ normalization；absent ≠ unresolved） |
| **P1**（后续增强） | 「该能力是否属 `FZ-3` 列出的后续增强？」→ **是** | 企业知识库 ／ RAG；高级供应商比较；自然语言供应链查询；自动供应链分析报告 | `FZ-3`；**不属于**第一阶段 POC 成败核心 |

**去重说明（消除隐式重叠 —— 每条 item 只归一 bucket）：**

- **`direct source-system ／ Production DB access` 只登记于 `Prohibited`。** 它在直觉上也像「业务范围之外」，
  但在 current canonical text 中它是**被明确禁止的行为**（`§3` read boundary；`AC-1` ／ `AC-2`），
  因此按判定顺序第 1 条归入 **Prohibited**，**不**再重复出现在 Business scope out-of-scope。
  同一禁止路径的另一种表述（**绕过 Controlled Export**）已在**同一** bucket 内合并为**同一** item，不再跨 bucket 出现。
- **`Production write-back` 在 `§3` 中有两个不同 canonical 表述**：`Production Write-back = OUT OF SCOPE`（**scope 维度**）
  与 `WRITE = DENIED`（**behavior 维度**）。本候选表把**行为禁止**归入 `Prohibited`，并**以 `§3` 的 scope 表述作为其依据引用**，
  **不**把同一对象登记为两个 bucket 的 item。若 Human 希望将其显式拆成两条 item（capability exclusion ＋ behavior prohibition），
  由 `GSD-5` 裁定；本 Review **不**自行选择该拆法。

**D. Scope drift check（Q6 —— 以 `§2` ～ `§5` 为对象）**

| # | 检查项 | 与 `FROZEN` P0 的关系 | 核验结论 |
| --- | --- | --- | --- |
| 1 | deterministic shortage analysis | P0-1 核心（`§2.1` `BR-SHORTAGE-001`） | **P0 capability scope**；无扩张 |
| 2 | available inventory ／ safety stock | P0-1 计算要素（`§2.2` `BR-INVENTORY-001`） | 同上；无扩张 |
| 3 | substitute material | P0-1 计算要素（`§2.3` `BR-SUBSTITUTE-001`） | 同上；无扩张 |
| 4 | requirement ／ scrap-loss | P0-1 计算要素（`§2.4` `BR-REQUIREMENT-001`） | 同上；无扩张 |
| 5 | effective inbound | P0-1 输入（`§2.6` `BR-INBOUND-001`；对应 `§11`「有效在途」） | 同上；无扩张 |
| 6 | procurement recommendation ／ `MOQ` | P0-2（`§2.5` `BR-PROCUREMENT-001`） | **P0 capability scope**；无扩张 |
| 7 | supplier risk ／ risk evidence | `§11` P0-2 输出已含「风险证据」⇒ `§2.7` `BR-SUPPLIER-RISK-001` 属 **P0-2 的 risk-evidence 维度**，**不是** `§12` P1「高级供应商比较」 | **无扩张**；但 §1 wording 必须显式区分（`GSF-4`） |
| 8 | explanation ／ LLM 解释 | `FZ-1`「可解释」＋ `§11` P0-1「AI 负责组织和解释结果」 | **P0 capability scope**；无扩张 |
| 9 | `§5.3` 的 6 个 P0 User Questions | 属 **P0 explanation ／ interaction support** 的 `SIMULATED` baseline；**不等于** `§12` P1「自然语言供应链查询」 | **无扩张**；P1 **未**升级为 P0（`GSF-4`） |
| 10 | `Procurement Request Draft` | P0-3 核心输出（`§11`） | **P0 capability scope**；无扩张 |
| 11 | POC 内 Human `Review` ／ `Modify` ／ `Approve` ／ `Reject` | P0-3；**不**等于 Production execution（`§3` `WRITE = DENIED`） | 无扩张；`§6` state machine 仍 `DESIGN PENDING`（属 deferred） |
| 12 | Controlled Export ／ Snapshot | `FZ-1`「受控」的数据获取方式 | **supporting infrastructure**；不是新业务场景 |
| 13 | Data Validation ／ Master Data Mapping ／ Adapter conceptual boundary | `FZ-1`「可追溯」＋ `FZ-4`「数据正确」的实现边界 | **supporting infrastructure**；不是新业务场景 |
| 14 | fail-closed ／ traceability ／ evidence | `FZ-1` ＋ `FZ-4` 的 quality ／ safety boundary | **supporting infrastructure**；不是新业务场景 |

**核验结论：** 以 current approved `§2` ～ `§5` 为准，**未发现**任何无法由 `FROZEN` baseline ＋
current approved design 解释的 scope expansion；亦**未发现**需要新增 P0 场景的已批准内容。
（`§5` 的 `SIMULATED` question baseline、`Supplier Risk`、`Adapter` ／ `Package Assembly`、
POC 内 Human approval、Data Validation ／ Mapping 均落在上表第 7 ～ 14 行的既有边界内。）

**E. §1 closure 依赖 ／ 不依赖什么（Q7 —— candidate）**

```
可能需要在 §1 本层关闭：
  goals wording；P0 ／ P1 boundary mapping；In ／ Out scope；success boundary semantics；
  failure boundary relationship；current downstream composition consistency

明确留给其他层：
  §6 HITL state machine；§7 detailed RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling；
  §8 audit ／ observability details；§9 concrete test ／ eval ／ acceptance method；
  §10 Architecture ／ ADR；implementation

candidate 判断：
  上述 pending layers 不阻止 §1 conceptual closure —— §1 只需登记 goal ／ boundary ／
  interface ／ dependency expectation，而不设计这些层；
  但 §1 closure 依赖这些层继续保持诚实的 DESIGN PENDING 表述（不得声称已完成）。
```

### 1.5 Gap / Conflict Findings

| # | 类型 | Finding | 影响 |
| --- | --- | --- | --- |
| `GSF-1` | **Design gap** | §1 当前**只有占位符**：P0 设计目标 ／ POC 成功边界 ／ In Scope ／ Out of Scope 四项均为 `DESIGN PENDING`，缺少 design-level 的 goal 与 scope boundary | POC 总目标 ／ success ／ scope 在 design 层无 canonical boundary；`§6` ～ `§10` 缺少上层 composition 参照 |
| `GSF-2` | **Navigation drift（non-blocking）** | `docs/project-index.md` 的 pending-area wording 只指向 `§5` ～ `§9`，**未**列入 `§1 Design Goals & Scope`（其 `DESIGN PENDING` 为真实状态） | 冷启动导航可能误判 §1 已完成；本 PR 做**最小 navigation-only sync** |
| `GSF-3` | **Wording risk** | `FROZEN` `§16` 同时包含 design 可支撑的 success dimensions、runtime ／ test evidence 要求与 business-value 要求；若 §1 只用一层「成功标准」表述，`§2` ～ `§5 DESIGN RESOLVED` 容易被误读为 POC 已成功 | 需在 §1 采用**分层** success boundary（`S-5` ／ `GSD-3`） |
| `GSF-4` | **Wording risk** | `§5.3` 的 6 个 P0 questions 与 `§12` P1「自然语言供应链查询」、`§2.7` `Supplier Risk` 与 P1「高级供应商比较」在字面上接近 | §1 必须显式区分 P0 support 与 P1 能力，避免被误读为 P1 已升级为 P0（`S-2`） |
| `GSF-5` | **Wording risk** | Out of Scope 若只列一份清单，`business out-of-scope` ／ `deferred` ／ `prohibited` ／ `P1` 四类会被压平 | 需按四类分开登记（`S-4` ／ `GSD-5`） |
| `GSF-6` | **Verification result（non-finding）** | `§2` ～ `§5` scope drift check（1.4 D，14 项）**未发现**未登记的 scope expansion 或 blocking scope conflict | 无需在本层修复；作为 `S-7` ／ `S-14` 的证据 |
| `GSF-7` | **Dependency boundary（non-blocking）** | `§6` ～ `§10` 仍 `DESIGN PENDING` ／ `No ADR created yet` | 需在 §1 登记 dependency expectation；**不**阻止 §1 conceptual closure（1.4 E ／ `GSD-6`） |

> 本 Review **未**发现需要 blocking escalation 的 scope contradiction；
> `GSF-1` ～ `GSF-7` 均为**待 Human 裁定的 design gap ／ wording ／ navigation 事项**。

### 1.6 Candidate Options / Trade-offs

> **这些原为 candidate conceptual approaches**；其中 **`§1 Option 2` 已由 `GSD-1`（Issue #94）选为 Human-selected closure model**（见 **`§1.11`**），`Option 0` ／ `Option 1` ／ 其他 **未被选择**。
> `§1 Option 0 ／ 1 ／ 2` 为本节局部编号，**不**沿用其他章节的 Option 编号。

| Option | 含义 | 好处 | 风险 ／ 代价 | 对 `§6` ～ `§10` 的影响 |
| --- | --- | --- | --- | --- |
| **`§1 Option 0`** | **Keep §1 placeholders** —— 保持现状，不做 §1 canonical closure | 零新增；无新决策负担 | POC 总目标 ／ success ／ scope 继续缺少 design-level canonical boundary；`GSF-1` 持续存在；success 分层与 In ／ Out scope 分类继续缺失 | `§6` ～ `§10` 继续无上层 goal ／ scope 参照；后续 closure 仍需回到本问题 |
| **`§1 Option 1`** | **Minimal inherited-scope registration** —— 只把 `FROZEN` `§10` ／ `§11` ／ `§12` ／ `§16` ／ `§17` 转写为 design 层的 goal ／ scope ／ success boundary ／ failure boundary ／ dependency pointers，**不重新发明业务范围** | 最小、与 inherited baseline 一致性最高；直接消除 `GSF-1` | 未登记与 `§2` ～ `§5` 的 composition；success boundary 分层与 In ／ Out scope 分类仍可能含糊（`GSF-3` ／ `GSF-5`） | 为 `§6` ～ `§10` 提供 goal ／ scope 参照，但不显式登记依赖关系 |
| **`§1 Option 2`**（**`SELECTED`（`GSD-1` ／ Issue #94）**） | **Inherited scope ＋ downstream composition contract** —— 在 `§1 Option 1` 基础上进一步登记：`§2` ～ `§5` 如何实现 ／ 支撑 P0；`§6` ～ `§10` 哪些仍为 pending dependency；§1 conceptual closure 是否可在这些 dependency 未完成时成立；`design closure ≠ implemented ≠ tested ≠ business accepted ≠ production-ready` 的层次关系 | 消除 `GSF-1` ／ `GSF-3` ／ `GSF-5` ／ `GSF-7`；为后续 closure 与其他层提供显式 composition 边界 | 登记内容最多；需 Human 裁定若干 wording boundary（`GSD-2` ／ `GSD-3` ／ `GSD-5`） | 明确 `§6` ～ `§10` 的 dependency expectation，**不**设计它们 |
| **其他** | 由 Human 提出的其他 conceptual approach | —— | —— | —— |

> **Reviewer Recommendation（非 Human Decision、非 canonical policy、不构成选择）：**
> 就 trade-off 完整性而言，`§1 Option 2` 覆盖 `GSF-1` ／ `GSF-3` ／ `GSF-5` ／ `GSF-7` 最完整；
> `§1 Option 1` 为最小可行方案；`§1 Option 0` 不能消除 `GSF-1`。
> 该 recommendation **不**登记为任何 Decision，最终选择由 `GSD-1` 裁定。
>
> **current-state（Issue #94）：** `GSD-1` 已 **`REGISTERED`** —— 选择 **`§1 Option 2`**（见 **`§1.11`**）。
> 上表其余内容仍为其时的 candidate 描述，**未**因该选择而改写；`§1 Option 2` 的具体 canonical wording
> 仍待 `GSD-8` 裁定（**`GSD-2` ～ `GSD-7` 已于 Issue #96 ／ #98 ／ #100 ／ #102 ／ #104 ／ #106 分别登记 wording boundary、success boundary layering、In Scope canonical categories、Out of Scope 四类分离、downstream dependency relationship 与 mandatory minimum closure criteria**，见 **`§1.12`** ／ **`§1.13`** ／ **`§1.14`** ／ **`§1.15`** ／ **`§1.16`** ／ **`§1.17`**），§1 四项 top-level status **仍为 `DESIGN PENDING`**。

### 1.7 Minimum Closure Criteria（Human-approved —— `GSD-7` ／ Issue #106）

> **`S-1` ～ `S-14` = Human-approved MANDATORY MINIMUM CLOSURE CRITERIA**（`GSD-7` ／ Issue #106）。
> `S-1` ～ `S-3` ／ `S-5` ／ `S-6` ／ `S-8` ／ `S-10` ／ `S-12` 保持原核心语义；
> `S-4` ／ `S-7` ／ `S-9` ／ `S-11` ／ `S-13` ／ `S-14` 已按 `GSD-7` 修订（修订内容见各行）。

| # | Criterion | 类别 |
| --- | --- | --- |
| `S-1` | **P0 Goal integrity：** `§1` 的 P0 Goal 与 `FROZEN` Problem Statement（`FZ-1`）／ `§11`（`FZ-2`）一致，且**不得**改变 P0 闭环（缺料分析 → 采购建议 → HITL） | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-2` | **P1 must not be promoted into P0：** `FZ-3` P1 **不得**升级为 P0；`§5.3` `SIMULATED` question baseline 与 `§2.7` `Supplier Risk` **不得**被写成 P1 已进入 P0 | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-3` | **No scope inflation via In Scope：** In Scope **不得**新增 `FROZEN` 之外的 business scenario；supporting infrastructure ／ quality ／ safety boundary **不得**被写成新 P0 capability | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-4` | **Four-way separation without silently approving old candidate routing rules：** 必须保持 `Out of Scope ≠ P1 ≠ Prohibited ≠ Deferred`；每个具体 item 必须有明确 **canonical authority** 与 **primary classification**；存在跨维度关系时**必须**显式说明，**不得**产生隐式重复、语义冲突或 authority inflation。**本 criterion 不自动批准旧 `§1.4 C` candidate 中的固定判定顺序、先命中者为准、现有 candidate item placement 或 bucket routing 细节** —— 未来 §1 Closure PR 如需使用这些 routing 细节，**必须**基于 `GSD-5` 已批准的四类语义重新验证 | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-5` | **Success dimensions must be fully mapped：** `FROZEN` `§16` success dimensions **全部**映射到 `GSD-3` 已批准的三层 Success Boundary（design-time ／ runtime-test evidence ／ business-value evidence）三层；**不得**把 design-time completion 写成 POC success | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-6` | **Failure ／ reassessment boundary must be preserved：** `FROZEN` `§17` failure ／ reassessment boundary **完整保留**，**不得**删除、弱化、改写，也**不得**伪装成已验证事实 | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-7` | **Revalidate `§2` ～ `§5` composition against current main：** Closure PR **必须**基于**当时 current main**重新核验 current `§2` ～ `§5` 与 P0 Goal ／ Scope 是否存在 unresolved composition conflict；**不得**只依赖历史 `§1.4 D` ／ `GSF-6` 旧结论。要求 `Current-main composition check = PASS`、`Unresolved §2～§5 blocking conflict = NONE`；若出现新冲突，**必须**登记并解决，未解决前 closure gate = **FAIL** | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-8` | **Downstream dependency responsibility must be explicit：** `§6` ～ `§10` pending dependencies 的责任边界清楚，符合 `GSD-6`：`Downstream pending ≠ Automatic §1 closure blocker`；`Dependency expectation ≠ Downstream design completion` | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-9` | **Explicit lifecycle ／ evidence separation：** §1 **必须**显式保持 `Design closure ≠ Implemented ≠ Runtime validated ／ Tested ≠ Business value proven ／ accepted ≠ POC SUCCESS ≠ Production-ready`；并与 `GSD-3` 一致：`POC SUCCESS` 需要 **runtime-test evidence ＋ business-value evidence** | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-10` | **No invented real-world evidence：** **不得**发明真实 KPI、客户 baseline、usage frequency、adoption、production-system fact 或 business-value evidence | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-11` | **`§1` Closure PR must not choose Architecture ／ technology：** §1 Closure PR 本身**不得**选择 Architecture ／ framework ／ database ／ API ／ deployment，**不得**创建或修改 ADR，也**不得**替 `§10` 做技术选型。**本 criterion 不要求 `§10` 永远保持 No ADR** —— `§10` 按其 own current canonical status 独立存在；`§1 closure ≠ Architecture decision` | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-12` | **`FROZEN` Discovery integrity：** **不得**修改或重新解释 `FROZEN` Discovery，**不得**改写 P0 ／ P1，**不得**用 downstream implementation 反向覆盖 `FROZEN` scope authority | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-13` | **Current-state ／ `project-index.md` must match actual closure result：** `docs/project-index.md` 与其他 current-state navigation **必须**与 closure 结果一致 —— `closure gate PASS ⇒ §1 actual canonical status must be synchronized consistently`；`closure gate FAIL ⇒ §1 remains DESIGN PENDING`；**不得**出现 document ／ index ／ current-state 相互矛盾 | MANDATORY MINIMUM CLOSURE CRITERION |
| `S-14` | **No unresolved blocking scope conflict：** closure gate 要求 `Unresolved blocking scope conflict = NONE`；若发现新的 blocking scope conflict，**即使已经登记／已有 Issue 或 mitigation proposal**，只要仍未解决 ⇒ `Closure gate = FAIL`、`§1 remains DESIGN PENDING`；**不得**用「已登记 blocker」替代「已解决 blocker」 | MANDATORY MINIMUM CLOSURE CRITERION |

**Closure Gate Semantics（`GSD-7` APPROVED）：**

```
S-1 = PASS ／ … ／ S-14 = PASS  → §1 closure gate = PASS
任一 S-* = FAIL                 → §1 closure gate = FAIL → §1 remains DESIGN PENDING
```

**不得** partial-pass。

**Criteria approval ≠ criteria already satisfied：**

```
Criteria approved
≠ Criteria verified PASS
≠ Closure executed
≠ §1 DESIGN RESOLVED
```

本 Decision **只**批准 criteria 本身 —— **不**表示 `S-1` ～ `S-14` 当前已全部 PASS，
也**不**表示 closure 已执行、§1 已 `DESIGN RESOLVED` 或 `GSD-8` 已授权。见 **`§1.17`**。

### 1.8 Human Decision Required

| # | Human Decision Question | Options | Trade-offs ／ 说明 | 影响 |
| --- | --- | --- | --- | --- |
| `GSD-1` | §1 采用哪种 conceptual closure model？ | `§1 Option 0` ／ `Option 1` ／ `Option 2` ／ 其他 | 见 1.6 | §1 是否进入后续独立 Design Change ／ Closure |
| `GSD-2` | P0 Design Goal 的 canonical wording boundary | ① 只继承 `FROZEN` 表述；② 继承 ＋ 引用 `§2` ～ `§5` 作为「如何满足 P0」的 approved downstream facts（限定引用深度）**← `SELECTED`（`REGISTERED`，Issue #96；**strict limited-reference interpretation**）** | ② 更具可审计的 composition，但需界定引用范围，避免把 downstream design 写成 goal 本身 | §1 goal 段落形态 |
| `GSD-3` | POC Success Boundary 的层次结构 | ① design-time ／ runtime-test evidence ／ business-value evidence 三层**← `SELECTED`（`REGISTERED`，Issue #98）**；② 其他分层 | 三层与 `FZ-4` 各项一一映射，且天然阻止「已成功」误读 | §1 success 段落语义（`S-5` ／ `S-9`） |
| `GSD-4` | In Scope 的 canonical categories | ① P0 capability scope ＋ supporting infrastructure ＋ quality ／ safety boundary 三类**← `SELECTED`（`REGISTERED`，Issue #100）**；② 其他 | ① 直接支撑 `S-3`，避免 supporting infrastructure 被读成新 P0 场景 | §1 In Scope 结构 |
| `GSD-5` | Out of Scope ／ P1 ／ Prohibited ／ Deferred 的分类方式 | ① 四类分离**← `SELECTED`（`REGISTERED`，Issue #102）**；② 其他 | 四类分离支撑 `S-4`，避免「都不做」式压平 | §1 Out of Scope 结构 |
| `GSD-6` | `§6` ～ `§10` remaining pending 是否阻止 §1 conceptual closure？ | ① 不阻止，§1 只登记 interface ／ dependency expectation**← `SELECTED`（`REGISTERED`，Issue #104）**；② 阻止，需先完成相关层；③ 条件性 | ① 与「§1 是 goal ／ scope 层」一致；② 会把 §1 与多章设计耦合 | §1 closure 时点与顺序 |
| `GSD-7` | 是否接受 proposed minimum closure criteria `S-1` ～ `S-14`？ | 接受 ／ 调整 ／ 拒绝**← `SELECTED`（`REGISTERED`，Issue #106：**调整后接受**，`S-1` ～ `S-14` = Human-approved mandatory minimum closure criteria）** | 若调整，需给出替代 criteria | §1 后续 closure gate |
| `GSD-8` | 是否授权后续独立 §1 Design Change ／ Closure PR？ | **AUTHORIZE（REGISTERED，Issue #112；见 §1.18）** | 授权后方可由该 PR 登记 §1 的 canonical goal ／ scope 与状态转换 | §1 是否可离开 `DESIGN PENDING` |

> **current-state（Issue #94 ／ #96 ／ #98 ／ #100 ／ #102 ／ #104）：** `GSD-1` = **`REGISTERED`**（**`§1 Option 2`**，见 **`§1.11`**）；
> `GSD-2` = **`REGISTERED`**（**Option ② —— FROZEN inheritance ＋ limited downstream composition references**，**strict limited-reference interpretation**，见 **`§1.12`**）；
> `GSD-3` = **`REGISTERED`**（**Option ① —— design-time ／ runtime-test evidence ／ business-value evidence 三层 POC Success Boundary**，见 **`§1.13`**）；
> `GSD-4` = **`REGISTERED`**（**Option ① —— P0 capability scope ／ supporting infrastructure ／ quality ／ safety boundary 三类 In Scope canonical categories**，见 **`§1.14`**）；
> `GSD-5` = **`REGISTERED`**（**Option ① —— Out of Scope ／ P1 ／ Prohibited ／ Deferred 四类分离**，见 **`§1.15`**）；
> `GSD-6` = **`REGISTERED`**（**Option ① —— `§6` ～ `§10` remaining pending 不阻止 §1 conceptual closure；§1 只登记 interface ／ dependency expectations**，见 **`§1.16`**）；
> `GSD-7` = **`REGISTERED`**（**调整后接受 `S-1` ～ `S-14`；`S-1` ～ `S-14` = Human-approved mandatory minimum closure criteria**，见 **`§1.7`** ／ **`§1.17`**）；
> **`GSD-8` = `REGISTERED`（AUTHORIZE，Issue #112）**；本次 closure verification 与 current status 见 **§1.19 ～ §1.20**。

**已被 `FROZEN` 唯一决定、因此**不**列为 Human Decision 的事项：**

```
P0 闭环 = 缺料分析 → 采购建议 → HITL（FZ-2）
P1 能力集合 = RAG ／ 高级供应商比较 ／ 自然语言供应链查询 ／ 自动报告（FZ-3）
success dimensions 集合 = 数据正确 ／ 计算正确 ／ 工具正确 ／ 可解释 ／ 安全 ／ 业务价值（FZ-4）
failure ／ reassessment conditions 集合（FZ-5）
不得发明真实 KPI ／ baseline（FZ-4）
不得发生未经人工批准的高风险写操作（FZ-4）
不得把正式采购执行纳入 P0（FZ-2）
```

> 上述内容为 **inherited constraint**，**不得**被重新包装成新的 Human Decision。
> `GSD-1` ～ `GSD-8` 为**有限、可逐项裁定**的清单；本 Review **未**作出其中任何一项决定。

### 1.9 Explicit Non-Decisions

本 Review **不创建**：

```
§1 approved goal ／ scope ／ success boundary 文字（仅 candidate structure 与 criteria）
P0 ／ P1 的任何修改
success 已达成 ／ failure 已发生的任何声明
真实 KPI ／ customer baseline ／ adoption ／ frequency evidence
§6 HITL state machine 设计
§7 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 设计
§8 audit event schema ／ observability implementation
§9 concrete tests ／ eval harness ／ acceptance method
§10 Architecture ／ framework ／ database ／ API ／ deployment 选择
ADR
implementation code ／ schema ／ Mock API ／ Mock Dataset
```

**本 Review 的 status 边界（自我核验）：**

```
未选择任何 §1 Option
未修改 P0 ／ P1
未把 §1 推进为 DESIGN RESOLVED
未修改 §2 ～ §5 任何已批准 policy
未修改 FROZEN Discovery
未新增 Validation Reason ／ Category ／ status enum ／ carrier
```

### 1.10 Current Status（本 Review 时点）

> **历史 snapshot，保留不回写。** 本块及其下旧 current-state 描述已由 Issue #112 的 **§1.20 Current Status** supersede，不代表 latest state。

```
§1 P0 设计目标                      = DESIGN PENDING   ← 本 Review 未推进；GSD-1 registration 亦未推进
§1 POC 成功边界                     = DESIGN PENDING   ← 本 Review 未推进；GSD-1 registration 亦未推进
§1 In Scope                        = DESIGN PENDING   ← 本 Review 未推进；GSD-1 registration 亦未推进
§1 Out of Scope                    = DESIGN PENDING   ← 本 Review 未推进；GSD-1 registration 亦未推进
§1 closure model（GSD-1）           = REGISTERED（§1 Option 2 —— Inherited scope ＋ downstream composition contract）
§1 P0 Goal wording boundary（GSD-2）= REGISTERED（Option ② ＋ strict limited-reference interpretation；见 §1.12）
§1 POC Success Boundary（GSD-3）    = REGISTERED（Option ① —— design-time ／ runtime-test evidence ／ business-value evidence 三层；见 §1.13）
§1 In Scope categories（GSD-4）     = REGISTERED（Option ① —— P0 capability scope ／ supporting infrastructure ／ quality ／ safety boundary 三类；见 §1.14）
§1 Out of Scope classification（GSD-5）= REGISTERED（Option ① —— Out of Scope ／ P1 ／ Prohibited ／ Deferred 四类分离；见 §1.15）
§1 closure dependency（GSD-6）      = REGISTERED（Option ① —— §6 ～ §10 remaining pending 不阻止 §1 conceptual closure；见 §1.16）
§1 closure criteria（GSD-7）        = REGISTERED（S-1 ～ S-14 = Human-approved mandatory minimum closure criteria；S-1 ～ S-14 verification = NOT EXECUTED）
GSD-8                              = PENDING
Dedicated §1 Closure PR            = NOT AUTHORIZED
§6 ～ §10 status                    = 各自 current canonical status 独立保持（本 Decision 未修改）
POC success                        = NOT CLAIMED（需 runtime-test evidence ＋ business-value evidence；真实 KPI 需真实客户 baseline）
S-1 ～ S-14                        = Human-approved mandatory minimum closure criteria（verification 未执行）
§2 P0 Business Rules               = DESIGN RESOLVED
§3 System Boundary                 = DESIGN RESOLVED（Implementation = NOT STARTED）
§4 Data & Integration Design       = DESIGN RESOLVED（0 个 DESIGN PENDING 子领域）
§5 AI ／ Tool Boundary              = DESIGN RESOLVED（Implementation = NOT STARTED；H4 未 resolved）
§6 HITL ／ §8 Audit ／ §9 Test      = DESIGN PENDING
§7 Permission & Security           = PARTIAL（Read ／ Write Boundary = DESIGN RESOLVED；其余 DESIGN PENDING）
§10 Architecture                   = 尚无正式 ADR
POC Design v0.2                    = DRAFT
```

**本 Review 不作出任何 Human Decision。**
**本 Review 未创建任何 runtime artifact ／ 未选择 architecture ／ 未修改 `FROZEN` Discovery。**

> **current-state（Issue #94 ／ #96 ／ #98 ／ #100 ／ #102 ／ #104）：** `GSD-1` = **`REGISTERED`**（`§1 Option 2`，见 **`§1.11`**）；
> `GSD-2` = **`REGISTERED`**（Option ② ＋ strict limited-reference interpretation，见 **`§1.12`**）；
> `GSD-3` = **`REGISTERED`**（Option ① —— 三层 POC Success Boundary，见 **`§1.13`**）；
> `GSD-4` = **`REGISTERED`**（Option ① —— 三类 In Scope canonical categories，见 **`§1.14`**）；
> `GSD-5` = **`REGISTERED`**（Option ① —— 四类分离，见 **`§1.15`**）；
> `GSD-6` = **`REGISTERED`**（Option ① —— downstream pending 不阻止 §1 conceptual closure，见 **`§1.16`**）；
> `GSD-7` = **`REGISTERED`**（调整后接受 `S-1` ～ `S-14`；见 **`§1.7`** ／ **`§1.17`**）；
> `GSD-8` = **`PENDING`**；`S-1` ～ `S-14` = **Human-approved mandatory minimum closure criteria（`Criteria approved ≠ Criteria verified PASS`）**；
> Dedicated §1 Closure PR = **`NOT AUTHORIZED`**；§1 四项 top-level status **仍为 `DESIGN PENDING`**；
> **POC success = NOT CLAIMED**。

### 1.11 Human Decision Record —— `GSD-1`（`SIMULATED POC Design Policy` ＋ `Human-approved`）

**Registration Status：`REGISTERED`**

依据 **Issue #94 Human Decision**。本记录**只**登记已批准的 `GSD-1`（§1 conceptual closure model），
并执行最小必要 current-state synchronization —— **不**决定 `GSD-2` ～ `GSD-8`、
**不**接受 `S-1` ～ `S-14`、**不**推进 §1 四项 top-level status、**不**写 final §1 canonical wording、
**不**设计 `§6` ～ `§10`、**不**选择 Architecture ／ implementation、**不**修改 `FROZEN` Discovery。

```
Decision Scope     = §1.8 `GSD-1`（§1 conceptual closure model）
Decision Authority = Human（Issue #94）
Selected Option    = §1 Option 2 —— Inherited scope ＋ downstream composition contract
Write Scope        = docs/design/poc-design-v0.2.md §1
```

**`GSD-1.1` Selected model（APPROVED）**

`§1 Option 2` 为 §1 的 **Human-selected conceptual closure model**：§1 后续 canonical design 应同时承担：

```
① 继承 FROZEN Discovery 的上层边界
   —— §10 Problem Statement ／ §11 P0 Scope ／ §12 P1 Scope ／
      §16 success dimensions ／ §17 failure ／ reassessment boundary（即 FZ-1 ～ FZ-5）

② 登记 current downstream composition
   —— §2 ～ §5 如何支撑 ／ 实现 P0 的 design intent；
      只引用 approved downstream facts；
      不把 downstream design 细节复制成新的 §1 goal；
      不改变任何已批准 §2 ～ §5 policy

③ 登记 remaining dependency boundary
   —— §6 ～ §10 哪些仍为 pending dependencies；明确其与 §1 的关系；
      §1 只登记 composition ／ dependency expectation，不替代这些章节做设计

④ 显式区分状态层次（见 GSD-1.2）
```

**`GSD-1.2` Status layering（APPROVED）**

```
§1 DESIGN RESOLVED
≠ §6 ～ §10 DESIGN RESOLVED
≠ IMPLEMENTED
≠ TESTED
≠ BUSINESS ACCEPTED
≠ POC SUCCESS
≠ PRODUCTION-READY
```

**`GSD-1.3` 明确未决定（保留为 pending Human Decision）**

```
GSD-2 P0 Design Goal canonical wording boundary            = PENDING
GSD-3 POC Success Boundary 分层                            = PENDING
GSD-4 In Scope canonical categories                        = PENDING
GSD-5 Out of Scope ／ P1 ／ Prohibited ／ Deferred 分类方式   = PENDING
GSD-6 §6 ～ §10 pending 是否阻止 §1 conceptual closure       = PENDING
GSD-7 是否接受 S-1 ～ S-14                                  = PENDING
GSD-8 是否授权后续独立 §1 Design Change ／ Closure PR         = PENDING
```

> 上列各项**不因本 Decision 被推定**；`S-1` ～ `S-14` 继续为 **candidate（not Human-approved）**。

**`GSD-1.4` `FROZEN` boundaries preserved（保持）**

本 Decision **未**修改 `FROZEN` Discovery，**未**修改 Problem Statement，**未**新增 ／ 删除 ／ 重定义 P0 场景，
**未**将 P1 升级为 P0，**未**改变 P0 闭环（缺料分析 → 采购建议 → HITL），**未**把正式采购执行纳入 P0，
**未**发明真实客户 KPI ／ baseline ／ usage frequency ／ adoption evidence，
**未**把 `FROZEN` failure conditions 写成已发生事实。`FZ-1` ～ `FZ-5` 保持原样。

**`GSD-1.5` Downstream design boundaries preserved（保持）**

本 Decision **未**修改 `§2` ～ `§5` approved design；**未**设计 `§6` HITL state machine、
`§7` `RBAC` ／ `Data Scope` ／ `Tool Permission` ／ `Secret Handling`、`§8` Audit & Observability、
`§9` Test & AI Eval；**未**选择 `§10` Architecture；**未**创建 ADR；
**未**选择 framework ／ database ／ API ／ auth ／ deployment；**未**写 implementation code ／ schema ／
Mock API ／ Mock Dataset。

**`GSD-1.6` 非声明（保持）**

本 Decision **不**构成 §1 closure、**不**授权 implementation、**不**改变 `§6` ～ `§10` status、
**不**改变 `POC Design v0.2 = DRAFT`。

**执行状态（本 Registration 时点）**

```
GSD-1                             = REGISTERED（§1 Option 2 —— Inherited scope ＋ downstream composition contract）
GSD-2 ～ GSD-8                    = PENDING
S-1 ～ S-14                       = candidate（not Human-approved）
§1 P0 设计目标                     = DESIGN PENDING ← 本 Decision 不推进状态
§1 POC 成功边界                    = DESIGN PENDING ← 本 Decision 不推进状态
§1 In Scope                       = DESIGN PENDING ← 本 Decision 不推进状态
§1 Out of Scope                   = DESIGN PENDING ← 本 Decision 不推进状态
POC Design v0.2                   = DRAFT
```

### 1.12 Human Decision Record —— `GSD-2`（`SIMULATED POC Design Policy` ＋ `Human-approved`）

**Registration Status：`REGISTERED`**

依据 **Issue #96 Human Decision**。本记录**只**登记已批准的 `GSD-2`（P0 Design Goal 的 canonical wording
authority 与引用深度），并执行最小必要 current-state synchronization —— **不**决定 `GSD-3` ～ `GSD-8`、
**不**接受 `S-1` ～ `S-14`、**不**写 final §1 canonical wording、**不**推进 §1 四项 top-level status、
**不**创建 §1 closure gate、**不**修改 `FROZEN` Discovery 与 `§2` ～ `§5` approved policy。

```
Decision Scope     = §1.8 `GSD-2`（P0 Design Goal canonical wording boundary）
Decision Authority = Human（Issue #96）
Selected Option    = Option ② —— FROZEN inheritance ＋ limited downstream composition references
Interpretation     = strict limited-reference
Write Scope        = docs/design/poc-design-v0.2.md §1
```

**`GSD-2.1` Goal authority（APPROVED）**

P0 Design Goal 的**唯一业务目标来源**仍是 `FROZEN` Discovery：`§10` POC Problem Statement 与 `§11` P0 Scope。
§1 后续 canonical wording **不得**通过 downstream design 创建新的业务目标、扩大 P0、改变 P0 闭环或重新解释 `FROZEN`。

```
P0 Design Goal = design-level expression of FROZEN Problem Statement ＋ P0 Scope
P0 Design Goal ≠ summary of every downstream design detail
```

**`GSD-2.2` Allowed downstream references（APPROVED）**

§1 P0 Design Goal ／ composition 说明**允许有限引用** current Human-approved downstream facts，
**仅**用于说明「当前设计**如何支撑**既有 `FROZEN` Goal」：

```
§2 —— deterministic business rules support the business calculation
§3 —— controlled system boundary ／ read-write boundary ／ draft-only boundary
§4 —— canonical data ／ validation ／ mapping ／ integration boundary
§5 —— AI ／ deterministic logic ／ Tool ／ Agent responsibility boundary
```

这些引用**只能**作为 **composition pointers ／ approved supporting facts**；authoritative 内容仍在各 downstream 章节。

**`GSD-2.3` Prohibited reference depth（APPROVED）**

§1 **不得复制或展开**：

```
具体 BR-* deterministic rule formulas ／ calculation detail
字段级 data dictionary
schema ／ carrier ／ enum ／ Validation Reason ／ Category
Snapshot ／ Import Contract 详细条款
Adapter ／ Package Assembly 详细 responsibility contract
mapping rule ／ mapping_basis 详细语义
concrete source-field mapping
Tool ／ API ／ function schema
implementation detail
Architecture ／ technology choice
§6 ～ §10 尚未 Human-approved 的具体设计
```

若必须理解某细节，应**引用 authoritative downstream section**，而不是把它复制到 §1。

**`GSD-2.4` Downstream facts are not new Goal（APPROVED）**

```
approved downstream fact
≠ new P0 Goal
≠ new P0 scenario
≠ scope expansion
```

例：`Controlled Export ／ Snapshot` 是支撑「受控数据获取」的 approved design fact，**不是**新的 P0 business goal；
`Data Validation ／ Mapping ／ Adapter` 是 supporting infrastructure，**不是**新的 P0 business scenario；
`§5` AI ／ Tool boundary 是「如何满足可解释 ／ 可控」的 responsibility design，**不是**新的 P0 business outcome。

**`GSD-2.5` Downstream facts are not success evidence（APPROVED）**

```
§2 ～ §5 DESIGN RESOLVED
≠ POC success achieved
```

§1 **不得**因引用 approved downstream design 就声称：data correctness 已被 runtime 证明；
deterministic calculations 已被测试通过；Tool selection ／ runtime behavior 已验证；business value 已证明；
customer baseline 已取得；POC 已 success；production-ready。上述属后续 `GSD-3` ／ `§9` ／
implementation ／ test ／ business evidence 等边界。

**`GSD-2.6` Intended canonical shape（保持 —— 不构成 final wording）**

本 Decision **只**批准 **wording boundary ／ reference depth**，**不**批准最终句子。后续 §1 Design Change
可形成类似以下结构：

```
P0 Design Goal
  = FROZEN-derived goal statement

Supporting composition
  - §2 defines deterministic business calculation
  - §3 defines controlled system / write boundary
  - §4 defines canonical data & integration boundary
  - §5 defines AI / Tool responsibility boundary

Authoritative details remain in §2 ～ §5.
```

具体 final canonical wording **仍待后续独立 Design Change ／ Closure**，**不得**在本 registration task 中提前定稿。

**`GSD-2.7` 明确未决定（保留为 pending Human Decision）**

```
GSD-3 POC Success Boundary 分层                        = PENDING
GSD-4 In Scope canonical categories                    = PENDING
GSD-5 Out of Scope ／ P1 ／ Prohibited ／ Deferred 分类方式 = PENDING
GSD-6 §6 ～ §10 pending 是否阻止 §1 conceptual closure  = PENDING
GSD-7 是否接受 S-1 ～ S-14                              = PENDING
GSD-8 是否授权后续独立 §1 Design Change ／ Closure PR     = PENDING
```

> 上列各项**不因本 Decision 被推定**；`S-1` ～ `S-14` 继续为 **candidate（not Human-approved）**。

**`GSD-2.8` `FROZEN` ／ downstream boundaries preserved（保持）**

本 Decision **未**修改 `FROZEN` Discovery 与 Problem Statement；**未**新增 ／ 删除 ／ 重定义 P0 场景；
**未**把 P1 升级为 P0；**未**改变 P0 闭环（缺料分析 → 采购建议 → HITL）；**未**把正式采购执行纳入 P0；
**未**发明真实客户 KPI ／ baseline ／ frequency ／ adoption evidence；**未**把 `FROZEN` failure conditions
写成已发生事实。**未**修改 `§2` ～ `§5` approved policy；**未**把 downstream summary 变成 duplicate
canonical source；**未**设计 `§6` ～ `§9`；**未**选择 `§10` Architecture；**未**创建 ADR；
**未**写 implementation code ／ schema ／ API ／ runtime；**未**选择 framework ／ DB ／ auth ／ deployment；
**未** blanket-authorize implementation。

**执行状态（本 Registration 时点）**

```
GSD-1                             = REGISTERED（§1 Option 2 —— Inherited scope ＋ downstream composition contract）
GSD-2                             = REGISTERED（Option ② ＋ strict limited-reference interpretation）
GSD-3 ～ GSD-8                    = PENDING
S-1 ～ S-14                       = candidate（not Human-approved）
§1 P0 设计目标                     = DESIGN PENDING ← 本 Decision 不推进状态
§1 POC 成功边界                    = DESIGN PENDING ← 本 Decision 不推进状态
§1 In Scope                       = DESIGN PENDING ← 本 Decision 不推进状态
§1 Out of Scope                   = DESIGN PENDING ← 本 Decision 不推进状态
POC Design v0.2                   = DRAFT
```

### 1.13 Human Decision Record —— `GSD-3`（`SIMULATED POC Design Policy` ＋ `Human-approved`）

**Registration Status：`REGISTERED`**

依据 **Issue #98 Human Decision**。本记录**只**登记已批准的 `GSD-3`（POC Success Boundary 的三层结构与
claim semantics），并执行最小必要 current-state synchronization —— **不**决定 `GSD-4` ～ `GSD-8`、
**不**接受 `S-1` ～ `S-14`、**不**写 final §1 canonical success wording、**不**定义具体 test ／ KPI ／
threshold ／ Eval harness、**不**推进 §1 四项 top-level status、**不**创建 §1 closure gate、
**不**修改 `FROZEN` Discovery 与 `§2` ～ `§5` approved policy。

```
Decision Scope     = §1.8 `GSD-3`（POC Success Boundary layering）
Decision Authority = Human（Issue #98）
Selected Option    = Option ① —— design-time ／ runtime-test evidence ／ business-value evidence 三层
Write Scope        = docs/design/poc-design-v0.2.md §1
```

该分层用于把 `FROZEN` `§16` 的 success dimensions 放入正确责任层，避免把 `DESIGN RESOLVED` 误写成 `POC SUCCESS`。

**`GSD-3.1` Layer 1 —— Design-time success boundary（APPROVED）**

本层回答：**设计上是否已经定义清楚「系统必须如何满足 POC 目标与成功条件」**。可覆盖的 design-time boundary 包括
`FROZEN` Problem Statement ／ P0 ／ P1 boundary、deterministic business-rule definitions、controlled system boundary、
canonical data ／ validation ／ mapping ／ integration boundary、AI ／ deterministic logic ／ Tool ／ Agent
responsibility boundary、`§6` ～ `§9` 应满足的 responsibility ／ dependency expectations、以及
safety ／ traceability ／ explainability ／ fail-closed 等设计要求。

本层**只能**证明 `design boundary defined`；**不能证明** runtime data correctness、deterministic calculation
correctness under implementation、Agent ／ Tool runtime behavior、actual authorization enforcement、test pass、
business-value improvement、customer acceptance、POC success、production readiness：

```
Design-time boundary satisfied
≠ Runtime validated
≠ Business value proven
≠ POC success
```

**`GSD-3.2` Layer 2 —— Runtime ／ test evidence boundary（APPROVED）**

本层回答：**实现完成后，系统是否真的按设计正确运行**。至少应能由未来 `§9 Test & AI Eval`、
implementation ／ integration testing 与 runtime evidence 去证明 `FROZEN` `§16` 的技术与行为维度：

```
Data correctness        —— 结构化业务数据来自正确、授权的数据来源；不由 LLM 自行生成库存 ／ 订单 ／ 价格等业务事实；
                           data validation ／ mapping ／ import behavior 与 approved design 一致
Calculation correctness —— 相同输入下 deterministic shortage ／ procurement ／ risk calculation 稳定、一致、可复现；
                           implementation 与 approved business rules 一致
Tool correctness        —— Agent 调用正确、授权的 Tool；无无意义调用；不越权；不绕过 controlled path
Explainability ／
evidence fidelity       —— 关键结论有数据依据 ＋ 规则依据；explanation 不篡改 deterministic results；
                           missing ／ invalid ／ unavailable evidence 不被静默补全
Safety ／ permission
enforcement             —— 高风险行为受 Human ／ workflow ／ permission boundary 控制；
                           current POC hard boundaries 在 runtime 被真正 enforce；fail-closed 可被验证
```

本层负责 **evidence**；`§1` **不**自行定义具体测试实现。

**`GSD-3.3` Layer 3 —— Business-value evidence boundary（APPROVED）**

本层回答：**该 POC 是否对真实业务产生了值得继续投入的改善**。继承 `FROZEN` `§16`：至少应证明一种明确业务改善
（减少系统切换 ／ 减少人工汇总 ／ 降低分析时间 ／ 提高异常解释效率 ／ 其他经真实客户确认的改善）。限制：

```
不得现在发明 KPI 数值
customer baseline 必须来自真实客户 ／ 真实流程 evidence
usage frequency ／ adoption ／ business acceptance 不得由模拟设计直接推出
business-value evidence 不得由「设计完成」或「Demo 能运行」替代

Demo runs ≠ Business value proven
Simulated design evidence ≠ Real customer business-value evidence
```

**`GSD-3.4` Mapping to `FROZEN` `§16`（APPROVED）**

`FROZEN` `§16` success dimensions **不变**（数据正确 ／ 计算正确 ／ 工具正确 ／ 可解释 ／ 安全 ／ 业务价值）；
本 Decision **不修改**这些 dimensions，只登记其责任分层：

```
Design-time layer              = defines how each dimension must be supported
Runtime ／ test evidence layer = proves data ／ calculation ／ tool ／ explainability ／ safety behavior in implementation
Business-value evidence layer  = proves actual workflow ／ business improvement against real baseline
```

部分 dimension 可同时拥有 design obligation ＋ runtime evidence obligation；三层**不是**把 success dimensions
机械拆成互斥 bucket，而是 **evidence maturity ／ responsibility layers**。

**`GSD-3.5` POC success claim rule（APPROVED）**

> **`POC SUCCESS` 是 evidence claim，不是 design status。**

**不得**从以下任一事实单独推出 `POC SUCCESS`：`§1 DESIGN RESOLVED`；`§2` ～ `§5 DESIGN RESOLVED`；
`§6` ～ `§10` 未来 `DESIGN RESOLVED`；Architecture ADR 完成；implementation complete；Demo 可运行；
单一 test pass；单一 simulated scenario pass。

真正的 POC success claim 必须基于后续 Human-approved acceptance ／ evidence policy，至少综合 applicable
runtime ／ test evidence、applicable business-value evidence 与 `FROZEN` success dimensions 的满足情况。
本 Decision **不定义最终 success gate**，只定义分层与 claim boundary。

**`GSD-3.6` Relationship to `§9`（APPROVED）**

本 Decision 只定义 **`§9` 未来需要提供什么类别的 evidence**；**不设计** concrete test cases、test datasets、
pass ／ fail thresholds、deterministic unit-test ／ integration-test implementation、AI Eval rubric、judge model、
scoring system、acceptance threshold、CI test tooling、eval framework —— 均属未来 `§9 Test & AI Eval` 的独立设计。

**`GSD-3.7` Relationship to business baseline（APPROVED）**

不改变 `FROZEN` 要求「实际 KPI 数值必须等待真实客户 baseline」。当前**不得**创建
「节省 30% 时间」／「减少 50% 人工操作」／「准确率 95%」／「业务接受率 90%」等无真实 evidence 的具体 KPI；
**可以**定义未来需要比较的 **evidence category**，但**不得**捏造 measurement result。

**`GSD-3.8` Failure ／ reassessment boundary（保持）**

`FROZEN` `§17` failure ／ reassessment conditions 保持独立（data unavailable ／ unreliable；master-data linkage
unstable；existing `ERP` ／ `MRP` already solves the problem efficiently；usage frequency too low；
AI ／ Agent makes the process more complex or burdensome）。本 Decision **不**把这些条件写成已发生事实，
也**不**自动将其并入 success score —— 它们仍是 **future reassessment ／ stop-or-rethink boundary**。

**`GSD-3.9` 明确未决定（保留为 pending Human Decision）**

```
GSD-4 In Scope canonical categories                    = PENDING
GSD-5 Out of Scope ／ P1 ／ Prohibited ／ Deferred 分类方式 = PENDING
GSD-6 §6 ～ §10 pending 是否阻止 §1 conceptual closure  = PENDING
GSD-7 是否接受 S-1 ～ S-14                              = PENDING
GSD-8 是否授权后续独立 §1 Design Change ／ Closure PR     = PENDING
```

> 上列各项**不因本 Decision 被推定**；`S-1` ～ `S-14` 继续为 **candidate（not Human-approved）**。
> 本 Decision 亦**不**决定 final §1 success wording、final POC acceptance gate、
> test ／ eval implementation、KPI ／ thresholds、Architecture ／ implementation。

**`GSD-3.10` Boundaries preserved（保持）**

本 Decision **未**修改 `FROZEN` Discovery、`§16` success dimensions、`§17` failure conditions、
Problem Statement ／ P0 ／ P1；**未**发明 KPI ／ baseline ／ business evidence；
**未**把 simulated evidence 伪装成 real business evidence。**未**修改 `§2` ～ `§5` approved design；
**未**设计 `§6` ～ `§9` 具体实现；**未**选择 `§10` Architecture；**未**创建 ADR；
**未**写 implementation ／ tests ／ eval harness；**未**选择 framework ／ scoring ／ judge model ／ test tooling。

**执行状态（本 Registration 时点）**

```
GSD-1                             = REGISTERED（§1 Option 2 —— Inherited scope ＋ downstream composition contract）
GSD-2                             = REGISTERED（Option ② ＋ strict limited-reference interpretation）
GSD-3                             = REGISTERED（Option ① —— design-time ／ runtime-test evidence ／ business-value evidence 三层）
GSD-4 ～ GSD-8                    = PENDING
S-1 ～ S-14                       = candidate（not Human-approved）
§1 P0 设计目标                     = DESIGN PENDING ← 本 Decision 不推进状态
§1 POC 成功边界                    = DESIGN PENDING ← 本 Decision 不推进状态
§1 In Scope                       = DESIGN PENDING ← 本 Decision 不推进状态
§1 Out of Scope                   = DESIGN PENDING ← 本 Decision 不推进状态
POC success                       = NOT CLAIMED
POC Design v0.2                   = DRAFT
```

### 1.14 Human Decision Record —— `GSD-4`（`SIMULATED POC Design Policy` ＋ `Human-approved`）

**Registration Status：`REGISTERED`**

依据 **Issue #100 Human Decision**。本记录**只**登记已批准的 `GSD-4`（In Scope 的 canonical organization
structure），并执行最小必要 current-state synchronization —— **不**决定 `GSD-5` ～ `GSD-8`、
**不**接受 `S-1` ～ `S-14`、**不**新增任何 P0 ／ business scenario、**不**写 final §1 In Scope canonical wording、
**不**决定 Out of Scope ／ P1 ／ Prohibited ／ Deferred 分类、**不**推进 §1 四项 top-level status、
**不**做 Architecture ／ implementation 选择、**不**修改 `FROZEN` Discovery 与 `§2` ～ `§5` approved policy。

```
Decision Scope     = §1.8 `GSD-4`（In Scope canonical categories）
Decision Authority = Human（Issue #100）
Selected Option    = Option ① —— P0 capability scope ＋ supporting infrastructure ＋ quality ／ safety boundary 三类
Write Scope        = docs/design/poc-design-v0.2.md §1
```

本 Decision 只决定 **In Scope 的 canonical organization structure**，**不**新增任何 P0 业务目标、场景、能力或
success claim。

**`GSD-4.1` Category 1 —— P0 capability scope（APPROVED）**

承载 **`FROZEN` Discovery 已批准的 P0 业务能力及其被 §1 合法继承的 scope**。边界：

```
只能来自已批准的 FROZEN P0 ／ Problem Statement ／ P1 boundary，
以及已批准 downstream design 对这些 P0 能力的受限 supporting facts
不得因本次分类新增新业务场景
不得把 supporting infrastructure 或 quality ／ safety requirement 反向提升成新的 P0 capability
不得把未批准 candidate 写成 canonical P0 scope
不得借 GSD-4 重写或扩大 FROZEN scope

In Scope classification ≠ New P0 capability authorization
```

**`GSD-4.2` Category 2 —— Supporting infrastructure（APPROVED）**

承载 **为已批准 P0 capability 提供必要支撑的系统 ／ 数据 ／ integration ／ Agent ／ Tool 等 supporting design
obligations**；目的是避免把这些必要支撑误读成「新的业务目标」。边界：

```
supporting infrastructure 必须可追溯到已批准 P0 capability 或其必要 design dependency
「In Scope」只表示它属于当前 POC 的设计 ／ 实现边界，不表示它本身成为新的 P0
不得因其被列为 In Scope 而扩大业务范围
不得在本 Decision 中选择具体 Architecture ／ framework ／ database ／ API ／ deployment
不得在本 Decision 中创建 runtime implementation authorization

Supporting infrastructure in scope
≠ New business scope
≠ New P0
≠ Architecture choice
≠ Implementation authorization
```

**`GSD-4.3` Category 3 —— Quality ／ safety boundary（APPROVED）**

承载 **当前 POC 必须满足的 quality ／ safety ／ control obligations**，可包括当前 canonical design 已批准或继承的
约束类别：explainability ／ traceability；permission ／ authorization boundary；fail-closed ／ fail-safe expectation；
deterministic ／ evidence fidelity requirement；auditability；data ／ calculation ／ Tool correctness expectations；
其他已批准的 quality ／ safety obligations。边界：

```
本 category 是 quality ／ control boundary，不是新的业务功能列表
不得把 quality ／ safety requirement 误写成新的 P0 capability
不得在本 Decision 中补定义具体 test case ／ threshold ／ KPI ／ Eval harness
不得因此声明 POC SUCCESS
不得因此把 §7 ／ §9 ／ §10 等尚未完成的设计状态自动推进

Quality ／ safety in scope
≠ New business capability
≠ Test pass
≠ POC success
```

**`GSD-4.4` Category semantics（APPROVED）**

```
P0 capability scope      = what business capability the POC is intended to support
Supporting infrastructure = what enabling system ／ data ／ integration ／ Agent ／ Tool boundary
                            is required to support that approved capability
Quality ／ safety boundary = what non-functional ／ control ／ evidence ／ safety obligations
                            the POC must satisfy
```

三类用于 **canonical organization ／ readability ／ auditability**；**不要求**成为互斥技术 bucket；
某些 design fact 可同时具有 supporting ＋ quality obligation，但其 canonical placement **必须**避免重复定义或
scope inflation；分类结构本身**不改变** `FROZEN` authority；final §1 In Scope wording 仍属后续独立
Design Change ／ Closure 工作。

**`GSD-4.5` Relationship to `GSD-5`（保持）**

本 Decision **不决定** Out of Scope、P1、Prohibited、Deferred —— 仍属 **`GSD-5`**。因此当前**不得**借 GSD-4：
把任何内容放入 final Out of Scope；关闭 P1；创建新的 prohibited list；创建新的 deferred list；
决定四类之间的 final classification rule。

**`GSD-4.6` Relationship to `GSD-6` ～ `GSD-8`（保持）**

本 Decision **不决定** `GSD-6`（§6 ～ §10 remaining pending 是否阻止 §1 conceptual closure）、
`GSD-7`（是否接受 `S-1` ～ `S-14`）、`GSD-8`（是否授权后续独立 §1 Design Change ／ Closure PR）。因此：

```
GSD-5 ～ GSD-8 = PENDING
S-1 ～ S-14 = candidate（not Human-approved）
§1 four top-level status = DESIGN PENDING
POC Design v0.2 = DRAFT
POC success = NOT CLAIMED
```

**`GSD-4.7` Boundaries preserved（保持）**

本 Decision **未**修改 `FROZEN` Discovery、Problem Statement ／ P0 ／ P1；**未**新增业务目标 ／ 场景 ／ capability；
**未**把 supporting infrastructure 或 quality ／ safety obligations 变成新的 P0；**未**发明 KPI ／ baseline ／
business evidence；**未**把 simulated design evidence 写成 real business evidence。**未**修改 `§2` ～ `§5` 已批准
design policy；**未**提前决定 `§6` ～ `§10` remaining design；**未**选择 Architecture；**未**创建 ADR；
**未**写 runtime implementation；**未**定义具体 test ／ eval ／ KPI；**未**创建 credential ／ secret；
**未**推进 §1 four top-level status。

**执行状态（本 Registration 时点）**

```
GSD-1                             = REGISTERED（§1 Option 2 —— Inherited scope ＋ downstream composition contract）
GSD-2                             = REGISTERED（Option ② ＋ strict limited-reference interpretation）
GSD-3                             = REGISTERED（Option ① —— design-time ／ runtime-test evidence ／ business-value evidence 三层）
GSD-4                             = REGISTERED（Option ① —— P0 capability scope ／ supporting infrastructure ／
                                     quality ／ safety boundary 三类 In Scope canonical categories）
GSD-5 ～ GSD-8                    = PENDING
S-1 ～ S-14                       = candidate（not Human-approved）
§1 P0 设计目标                     = DESIGN PENDING ← 本 Decision 不推进状态
§1 POC 成功边界                    = DESIGN PENDING ← 本 Decision 不推进状态
§1 In Scope                       = DESIGN PENDING ← 本 Decision 不推进状态
§1 Out of Scope                   = DESIGN PENDING ← 本 Decision 不推进状态
POC success                       = NOT CLAIMED
POC Design v0.2                   = DRAFT
```

### 1.15 Human Decision Record —— `GSD-5`（`SIMULATED POC Design Policy` ＋ `Human-approved`）

**Registration Status：`REGISTERED`**

依据 **Issue #102 Human Decision**。本记录**只**登记已批准的 `GSD-5`（Out of Scope / P1 / Prohibited / Deferred
四类分离的 canonical classification model），并执行最小必要 current-state synchronization ——
**不**决定 `GSD-6` ～ `GSD-8`、**不**接受 `S-1` ～ `S-14`、**不**新增 ／ 删除 ／ 重定义 P1、
**不**新增 prohibited item、**不**新增 deferred item、**不**新增 business scenario ／ P0、
**不**写 final §1 Out of Scope canonical wording、**不**推进 §1 四项 top-level status、
**不**做 Architecture ／ implementation 选择、**不**修改 `FROZEN` Discovery 与 `§2` ～ `§5` approved policy。

```
Decision Scope     = §1.8 `GSD-5`（Out of Scope ／ P1 ／ Prohibited ／ Deferred classification）
Decision Authority = Human（Issue #102）
Selected Option    = Option ① —— 四类分离
Write Scope        = docs/design/poc-design-v0.2.md §1
```

本 Decision 只决定 **§1 Out of Scope 相关 canonical classification structure**，用于区分不同「当前不进入 P0
正常实现路径」的原因；**不新增**任何具体 Out of Scope ／ P1 ／ Prohibited ／ Deferred 条目，
也**不**改变其现有 authority。

**`GSD-5.1` Category 1 —— Out of Scope（APPROVED）**

表示 **当前 POC 明确不覆盖的业务范围 ／ 能力 ／ 场景**。边界：必须可追溯到 `FROZEN` Discovery 或已批准 canonical
design 中已经存在的 scope boundary；不得新增「当前不做」的业务内容；不得把仅仅「尚未设计」或「暂缓实现」的事项
误归为 Out of Scope；不得把 Prohibited 与 Deferred 压平成 Out of Scope。

```
Out of Scope ≠ Deferred ≠ Prohibited ≠ P1
```

**`GSD-5.2` Category 2 —— P1（APPROVED）**

表示 **业务上有价值、已被 Discovery 识别，但优先级低于 P0、当前不属于 P0 主闭环的能力 ／ 场景**。
边界：P1 的 authority 仍来自 `FROZEN` Discovery；本 Decision **不新增 P1、不删除 P1、不提升 P1 为 P0**；
不得因为「当前不做」就把 P1 改写成永久 Out of Scope；不得把 P1 误写成 Prohibited。

```
P1 ≠ Prohibited ≠ Permanently Out of Scope ≠ P0
```

**`GSD-5.3` Category 3 —— Prohibited（APPROVED）**

表示 **在当前 POC boundary 下明确禁止发生的行为 ／ 越界 ／ 实现路径**；语义重点是**当前 canonical boundary
明确不允许** —— 不是「以后再做」、不是「优先级低」、不是「还没设计」。可承载的内容**只能**来自已经批准的
prohibited ／ hard-boundary facts（例如：不得由 LLM 自行生成库存 ／ 订单 ／ 价格等结构化业务事实；
不得绕过 Human ／ workflow ／ permission boundary；不得越权调用 Tool；
不得把 simulated evidence 伪装成 real customer evidence；其他已经批准的 hard prohibition）。
边界：本 Decision **不新增任何新的 prohibited rule**，只能把已有 canonical prohibition 按分类结构归位；
不得将 Deferred ／ P1 错判为 Prohibited；不得借 Prohibited 扩张 governance。

```
Prohibited = currently disallowed by approved boundary
≠ backlog ≠ deferred work ≠ lower-priority scope
```

**`GSD-5.4` Category 4 —— Deferred（APPROVED）**

表示 **属于当前系统 ／ POC 后续可能需要，但经已批准 design ／ governance 明确推迟到后续阶段再决定或实现的事项**。
典型语义包括：具体 Architecture ／ framework ／ database ／ API ／ deployment；real source physical field ／
table discovery；某些 runtime realization；具体 carrier ／ encoding ／ implementation mechanism；
其他已批准为 deferred 的技术或实现项。边界：本 Decision **不新增任何 Deferred item**，只允许继承当前 canonical
design 中已经明确为 deferred ／ pending-to-later 的事项；Deferred 不等于 Out of Scope、不等于 Prohibited、
**不表示**已经授权未来 implementation、**不表示**该事项最终一定会做。

```
Deferred ≠ Out of Scope ≠ Prohibited ≠ Implementation authorization ≠ Commitment to implement
```

**`GSD-5.5` Classification semantics（APPROVED）**

```
Out of Scope = 当前 POC 不覆盖
P1           = 已识别但优先级低于 P0，当前不进入 P0 主闭环
Prohibited   = 当前 boundary 明确禁止
Deferred     = 属于未来可能需要决定 ／ 实现，但当前阶段刻意推迟
```

分类目的：防止把所有「现在不做」的内容压成同一种语义；保持 **scope ／ priority ／ prohibition ／ deferral**
四种不同 authority；提高 canonical wording 的可读性与审计性；防止 implementation Agent 把 Deferred 当成永远不做、
把 Prohibited 当成普通 backlog、把 P1 误写成 permanently out of scope。

**`GSD-5.6` Authority and anti-expansion rule（APPROVED）**

本 Decision 只决定 **分类框架**；每个具体条目必须继续继承其原始 authority：

```
Out of Scope item → 来自 FROZEN ／ approved scope boundary
P1 item           → 来自 FROZEN Discovery
Prohibited item   → 来自 approved hard boundary ／ safety ／ governance rule
Deferred item     → 来自 approved design deferral ／ governance decision

Classification ≠ New authority ≠ New scope ≠ New prohibition ≠ New deferral
```

若某个条目没有现成 canonical authority，本 Task **不得**自行创建。

**`GSD-5.7` Relationship to `GSD-6` ～ `GSD-8`（保持）**

本 Decision **不决定** `GSD-6`（§6 ～ §10 remaining pending 是否阻止 §1 conceptual closure）、
`GSD-7`（是否接受 `S-1` ～ `S-14`）、`GSD-8`（是否授权后续独立 §1 Design Change ／ Closure PR）。因此：

```
GSD-6 ～ GSD-8 = PENDING
S-1 ～ S-14 = candidate（not Human-approved）
§1 four top-level status = DESIGN PENDING
POC Design v0.2 = DRAFT
POC success = NOT CLAIMED
```

**`GSD-5.8` Boundaries preserved（保持）**

本 Decision **未**修改 `FROZEN` Discovery、Problem Statement ／ P0 ／ P1；**未**新增或删除 P1；
**未**把 P1 提升为 P0；**未**新增业务场景 ／ capability；**未**新增 prohibited business behavior；
**未**把 existing `FROZEN` scope 重写成新的 exclusion；**未**发明 KPI ／ baseline ／ business evidence。
**未**修改 `§2` ～ `§5` 已批准 design policy；**未**提前决定 `§6` ～ `§10` remaining design；
**未**选择 Architecture；**未**创建 ADR；**未**写 runtime implementation；**未**定义 concrete test ／ eval ／ KPI；
**未**创建 credential ／ secret；**未**推进 §1 four top-level status。

**执行状态（本 Registration 时点）**

```
GSD-1                             = REGISTERED（§1 Option 2 —— Inherited scope ＋ downstream composition contract）
GSD-2                             = REGISTERED（Option ② ＋ strict limited-reference interpretation）
GSD-3                             = REGISTERED（Option ① —— design-time ／ runtime-test evidence ／ business-value evidence 三层）
GSD-4                             = REGISTERED（Option ① —— P0 capability scope ／ supporting infrastructure ／
                                     quality ／ safety boundary 三类 In Scope canonical categories）
GSD-5                             = REGISTERED（Option ① —— Out of Scope ／ P1 ／ Prohibited ／ Deferred 四类分离）
GSD-6 ～ GSD-8                    = PENDING
S-1 ～ S-14                       = candidate（not Human-approved）
§1 P0 设计目标                     = DESIGN PENDING ← 本 Decision 不推进状态
§1 POC 成功边界                    = DESIGN PENDING ← 本 Decision 不推进状态
§1 In Scope                       = DESIGN PENDING ← 本 Decision 不推进状态
§1 Out of Scope                   = DESIGN PENDING ← 本 Decision 不推进状态
POC success                       = NOT CLAIMED
POC Design v0.2                   = DRAFT
```

### 1.16 Human Decision Record —— `GSD-6`（`SIMULATED POC Design Policy` ＋ `Human-approved`）

**Registration Status：`REGISTERED`**

依据 **Issue #104 Human Decision**。本记录**只**登记已批准的 `GSD-6`（`§6` ～ `§10` remaining pending 与
§1 conceptual closure 的 dependency relationship），并执行最小必要 current-state synchronization ——
**不**决定 `GSD-7` ／ `GSD-8`、**不**接受 `S-1` ～ `S-14`、**不**推进 §1 四项 top-level status、
**不**创建或执行 §1 closure gate、**不**修改 `§6` ～ `§10` 的 current canonical status、
**不**替 downstream 做具体设计、**不**做 Architecture ／ implementation 选择、
**不**修改 `FROZEN` Discovery 与 `§2` ～ `§5` approved policy。

```
Decision Scope     = §1.8 `GSD-6`（§6 ～ §10 remaining pending 是否阻止 §1 conceptual closure）
Decision Authority = Human（Issue #104）
Selected Option    = Option ① —— 不阻止；§1 只登记 interface ／ dependency expectations；
                     §6 ～ §10 downstream design status 独立保持
Write Scope        = docs/design/poc-design-v0.2.md §1
```

```
§1 conceptual closure
≠ §6 ～ §10 DESIGN RESOLVED
≠ downstream implementation complete
≠ implementation authorization
≠ POC SUCCESS
```

本 Decision 只决定 **closure dependency relationship**，**不**执行 closure，**不**推进任何 status。

**`GSD-6.1` §1 responsibility boundary（APPROVED）**

§1 是 **Design Goals & Scope layer**，负责回答：为什么做这个 POC；P0 goal ／ success boundary；In Scope；
Out of Scope ／ P1 ／ Prohibited ／ Deferred 的 canonical boundary；以及下游设计必须满足的高层
interface ／ dependency expectation。§1 **不负责**：

```
替 §6 HITL Workflow 完成具体交互 ／ approval ／ workflow design
替 §7 Permission & Security 完成 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling
替 §8 Audit & Observability 完成具体 audit event schema ／ observability implementation
替 §9 Test & AI Eval 完成 test case ／ dataset ／ threshold ／ eval harness
替 §10 Architecture Decisions 选择 framework ／ database ／ API ／ deployment ／ ADR

§1 may define what downstream layers must respect
but must not define how those layers are concretely implemented
```

**`GSD-6.2` Non-blocking rule（APPROVED）**

`§6` ～ `§10` 中仍存在 `DESIGN PENDING` ／ unresolved ／ deferred 内容，**不自动阻止** §1 conceptual closure。
理由：§1 的 closure target 是 goal ／ scope boundary completeness；downstream sections 的职责是基于该
goal ／ scope 做进一步设计；若要求 `§6` ～ `§10` 全部先完成才允许 §1 closure，会形成不必要的反向依赖。

```
Downstream pending ≠ Automatic §1 closure blocker
```

该 non-blocking rule **不表示** downstream pending 可以被忽略 —— 它们继续以各自章节的 current canonical
status 存在。

**`GSD-6.3` Interface ／ dependency expectation rule（APPROVED）**

§1 可以登记「下游章节为了符合已批准 Goal ／ Scope 必须满足什么高层责任 ／ interface ／ dependency
expectation」，但这些 expectation **必须**：只描述 **what must be respected ／ preserved**；
不定义具体 runtime mechanism；不选择具体 architecture ／ framework ／ library ／ database ／ API；
不定义 concrete security implementation；不定义 concrete Agent orchestration；
不定义 concrete test ／ eval implementation；不把 downstream pending 偷换成已完成。

```
Dependency expectation ≠ Downstream design completion
```

**`GSD-6.4` Downstream status independence（APPROVED）**

本 Decision **不改变** `§6` ～ `§10` 的任何 current canonical status：

```
仍为 DESIGN PENDING 的项 → 继续 DESIGN PENDING
PARTIAL 的项            → 继续 PARTIAL
§10 Architecture        → 仍无正式 ADR
implementation          → 继续未授权

§1 DESIGN RESOLVED does not transitively resolve §6 ～ §10
```

本 Task 本身更**不允许**把 §1 改为 `DESIGN RESOLVED`。

**`GSD-6.5` Future conflict ／ change handling（APPROVED）**

若后续 `§6` ～ `§10` 的具体设计发现与 §1 canonical goal ／ scope 存在真实冲突：不得静默偏离 §1；
不得反向把 downstream implementation 事实写成新的 scope authority；应通过独立 Design Change ／
Human Decision ／ canonical synchronization 处理。

```
Future downstream discovery may trigger Design Change
but does not justify indefinite §1 closure blocking today
```

**`GSD-6.6` Relationship to `GSD-7`（保持）**

本 Decision **不接受** `S-1` ～ `S-14`。`GSD-7` 仍专门决定是否接受 ／ 调整 ／ 拒绝 proposed minimum
closure criteria `S-1` ～ `S-14`。因此：`GSD-7 = PENDING`；`S-1` ～ `S-14 = candidate（not Human-approved）`。
本 Decision 只回答「downstream pending 是否是 blocker」，**不**回答「§1 的 closure criteria 是否已被批准」。

**`GSD-6.7` Relationship to `GSD-8`（保持）**

本 Decision **不授权**独立 §1 Design Change ／ Closure PR。`GSD-8` 仍专门决定是否授权后续独立 §1
Design Change ／ Closure PR 执行 canonical wording ＋ closure verification ＋ conditional status
transition。因此：`GSD-8 = PENDING`；`Dedicated §1 Closure PR authorization = NOT GRANTED`。

**`GSD-6.8` Status ／ success boundary（保持）**

本 Decision 不改变：

```
§1 P0 设计目标       = DESIGN PENDING
§1 POC 成功边界      = DESIGN PENDING
§1 In Scope          = DESIGN PENDING
§1 Out of Scope      = DESIGN PENDING
POC success          = NOT CLAIMED
POC Design v0.2      = DRAFT
```

并明确：`§1 DESIGN RESOLVED ≠ Implementation authorized`；`§1 DESIGN RESOLVED ≠ Runtime validated`；
`§1 DESIGN RESOLVED ≠ POC SUCCESS`。

**`GSD-6.9` Boundaries preserved（保持）**

本 Decision **未**修改 `FROZEN` Discovery、Problem Statement ／ P0 ／ P1；**未**新增业务场景 ／ capability；
**未**改写 `FROZEN` scope authority；**未**发明 KPI ／ baseline ／ business evidence。
**未**修改 `§2` ～ `§5` 已批准 design policy；**未**替 `§6` ～ `§10` 做具体设计；
**未**把 downstream pending 改写成 resolved；**未**修改 `§6` ～ `§10` 的 current canonical status；
**未**选择 Architecture ／ framework ／ database ／ API ／ deployment；**未**创建 ADR；
**未**写 runtime implementation；**未**定义 concrete test ／ eval ／ KPI；**未**创建 credential ／ secret；
**未**推进 §1 four top-level status。

**执行状态（本 Registration 时点）**

```
GSD-1                             = REGISTERED（§1 Option 2 —— Inherited scope ＋ downstream composition contract）
GSD-2                             = REGISTERED（Option ② ＋ strict limited-reference interpretation）
GSD-3                             = REGISTERED（Option ① —— design-time ／ runtime-test evidence ／ business-value evidence 三层）
GSD-4                             = REGISTERED（Option ① —— P0 capability scope ／ supporting infrastructure ／
                                     quality ／ safety boundary 三类 In Scope canonical categories）
GSD-5                             = REGISTERED（Option ① —— Out of Scope ／ P1 ／ Prohibited ／ Deferred 四类分离）
GSD-6                             = REGISTERED（Option ① —— §6 ～ §10 remaining pending 不阻止 §1 conceptual closure；
                                     §1 只登记 interface ／ dependency expectations）
GSD-7 ／ GSD-8                    = PENDING
S-1 ～ S-14                       = candidate（not Human-approved）
Dedicated §1 Closure PR           = NOT AUTHORIZED
§1 P0 设计目标                     = DESIGN PENDING ← 本 Decision 不推进状态
§1 POC 成功边界                    = DESIGN PENDING ← 本 Decision 不推进状态
§1 In Scope                       = DESIGN PENDING ← 本 Decision 不推进状态
§1 Out of Scope                   = DESIGN PENDING ← 本 Decision 不推进状态
§6 ～ §10 status                    = 各自 current canonical status 独立保持（本 Decision 未修改）
POC success                       = NOT CLAIMED
POC Design v0.2                   = DRAFT
```

### 1.17 Human Decision Record —— `GSD-7`（`SIMULATED POC Design Policy` ＋ `Human-approved`）

**Registration Status：`REGISTERED`**

依据 **Issue #106 Human Decision**。本记录**只**登记已批准的 `GSD-7`（调整后接受 `S-1` ～ `S-14` 并
canonicalize 为 §1 mandatory minimum closure criteria），并执行最小必要 current-state synchronization ——
**不**决定 `GSD-8`、**不**授权或执行 §1 Closure PR、**不**声明 `S-1` ～ `S-14` 已全部 PASS、
**不**推进 §1 四项 top-level status、**不**写 final §1 canonical wording、
**不**替 `§6` ～ `§10` 做具体设计、**不**做 Architecture ／ implementation 选择、
**不**修改 `FROZEN` Discovery 与 `§2` ～ `§5` approved policy。

```
Decision Scope     = §1.8 `GSD-7`（proposed minimum closure criteria `S-1` ～ `S-14`）
Decision Authority = Human（Issue #106）
Selected Option    = 调整后接受 —— `S-1` ～ `S-14` 全部 canonicalize 为
                     Human-approved MANDATORY MINIMUM CLOSURE CRITERIA
Write Scope        = docs/design/poc-design-v0.2.md §1
```

**`GSD-7.1` Criteria canonicalization（APPROVED）**

`§1.7` 的 `S-1` ～ `S-14` 已由 **candidate** 转为 **Human-approved mandatory minimum closure criteria**：

```
S-1 ～ S-3 ／ S-5 ／ S-6 ／ S-8 ／ S-10 ／ S-12 = 核心语义保持
S-4 ／ S-7 ／ S-9 ／ S-11 ／ S-13 ／ S-14        = 按本 Decision 修订（见 GSD-7.2 ～ GSD-7.7）
```

**`GSD-7.2` `S-4` —— four-way separation without silently approving old candidate routing rules（APPROVED）**

保持 `Out of Scope ≠ P1 ≠ Prohibited ≠ Deferred`；每个具体 item 必须有明确 **canonical authority** 与
**primary classification**；跨维度关系必须显式说明，不得产生隐式重复、语义冲突或 authority inflation。
**本 criterion 不自动批准旧 `§1.4 C` candidate 中的固定判定顺序、先命中者为准、现有 candidate item
placement 或 bucket routing 细节**；未来 §1 Closure PR 如需使用这些 routing 细节，**必须**基于 `GSD-5`
已批准的四类语义重新验证。

**`GSD-7.3` `S-7` —— revalidate `§2` ～ `§5` composition against current main（APPROVED）**

Closure PR **必须**基于**当时 current main**重新核验 current `§2` ～ `§5` 与 P0 Goal ／ Scope 是否存在
unresolved composition conflict；**不得**只依赖历史 `§1.4 D` ／ `GSF-6` 旧结论：

```
Current-main composition check = PASS
Unresolved §2 ～ §5 blocking conflict = NONE
```

若出现新冲突，**必须**登记并解决；未解决前 closure gate = **FAIL**。

**`GSD-7.4` `S-9` —— explicit lifecycle ／ evidence separation（APPROVED）**

§1 **必须**显式保持：

```
Design closure
≠ Implemented
≠ Runtime validated ／ Tested
≠ Business value proven ／ accepted
≠ POC SUCCESS
≠ Production-ready
```

并与 `GSD-3` 保持一致：`POC SUCCESS` 需要 **runtime-test evidence ＋ business-value evidence**。

**`GSD-7.5` `S-11` —— §1 Closure PR must not choose Architecture ／ technology（APPROVED）**

§1 Closure PR 本身**不得**选择 Architecture ／ framework ／ database ／ API ／ deployment，
**不得**创建或修改 ADR，也**不得**替 `§10` 做技术选型。**本 criterion 不要求 `§10` 永远保持 No ADR** ——
`§10` 按其 own current canonical status 独立存在。

```
§1 closure ≠ Architecture decision
```

**`GSD-7.6` `S-13` —— current-state ／ `project-index.md` must match actual closure result（APPROVED）**

```
If closure gate PASS → §1 actual canonical status must be synchronized consistently
If closure gate FAIL → §1 remains DESIGN PENDING
```

**不得**出现 document ／ index ／ current-state 相互矛盾。

**`GSD-7.7` `S-14` —— no unresolved blocking scope conflict（APPROVED）**

Closure gate 要求 `Unresolved blocking scope conflict = NONE`。若发现新的 blocking scope conflict，
**即使已经登记 ／ 已有 Issue 或 mitigation proposal**，只要仍未解决：

```
Closure gate = FAIL
§1 remains DESIGN PENDING
```

**不得**用「已登记 blocker」替代「已解决 blocker」。

**`GSD-7.8` Closure gate semantics（APPROVED）**

`S-1` ～ `S-14` 全部是 mandatory minimum criteria，**必须全部 PASS**：

```
S-1 = PASS ／ … ／ S-14 = PASS  → §1 closure gate = PASS
任一 S-* = FAIL                 → §1 closure gate = FAIL → §1 remains DESIGN PENDING
```

**不得** partial-pass。

**`GSD-7.9` Criteria approval ≠ criteria already satisfied（APPROVED）**

```
Criteria approved
≠ Criteria verified PASS
≠ Closure executed
≠ §1 DESIGN RESOLVED
```

本 Decision **只**批准 criteria 本身 —— **不**表示 `S-1` ～ `S-14` 当前已全部 PASS，
也**不**表示 closure 已执行、§1 已 `DESIGN RESOLVED` 或 `GSD-8` 已授权。

**`GSD-7.10` Relationship to `GSD-8`（保持）**

本 Decision **不决定** `GSD-8`：

```
GSD-8 = PENDING
Dedicated §1 Closure PR authorization = NOT GRANTED
```

只有未来 `GSD-8` Human Decision 明确授权后，才允许独立 Closure PR 写 final canonical wording、
执行 `S-1` ～ `S-14` verification，并根据 PASS ／ FAIL 决定是否 transition §1 status。

**`GSD-7.11` Status boundary（保持）**

本 Decision 不改变：

```
§1 P0 设计目标       = DESIGN PENDING
§1 POC 成功边界      = DESIGN PENDING
§1 In Scope          = DESIGN PENDING
§1 Out of Scope      = DESIGN PENDING
POC success          = NOT CLAIMED
POC Design v0.2      = DRAFT
```

**`GSD-7.12` Boundaries preserved（保持）**

本 Decision **未**修改 `FROZEN` Discovery、Problem Statement ／ P0 ／ P1；**未**新增业务场景 ／ capability；
**未**发明 KPI ／ baseline ／ business evidence；**未**修改 `§2` ～ `§5` approved design policy；
**未**替 `§6` ～ `§10` 做具体设计；**未**修改 `§6` ～ `§10` current canonical status；
**未**做 Architecture ／ implementation 选择；**未**创建 ADR；**未**写 runtime implementation；
**未**定义 concrete test ／ KPI ／ threshold ／ Eval harness；**未**创建 credential ／ secret；
**未**推进 §1 four top-level status；**未**授权或执行 §1 Closure PR。

**执行状态（本 Registration 时点）**

```
GSD-1 ～ GSD-6                    = REGISTERED
GSD-7                             = REGISTERED（调整后接受 S-1 ～ S-14）
GSD-8                             = PENDING
S-1 ～ S-14                       = Human-approved mandatory minimum closure criteria（verification = NOT EXECUTED）
Dedicated §1 Closure PR           = NOT AUTHORIZED
§1 P0 设计目标                     = DESIGN PENDING ← 本 Decision 不推进状态
§1 POC 成功边界                    = DESIGN PENDING ← 本 Decision 不推进状态
§1 In Scope                       = DESIGN PENDING ← 本 Decision 不推进状态
§1 Out of Scope                   = DESIGN PENDING ← 本 Decision 不推进状态
POC success                       = NOT CLAIMED
POC Design v0.2                   = DRAFT
```

---

### 1.18 Human Decision Record —— GSD-8（Issue #112）

**Registration Status：`REGISTERED`**

```
Decision Authority  = Human（Issue #112）
Selected Option     = AUTHORIZE dedicated §1 Design Change / Closure PR
Registration Status = REGISTERED
```

本授权只允许本 PR 编写四项 final canonical wording、执行 §1.7 mandatory gate 并按真实结果同步状态。
`GSD-8 REGISTERED ≠ Closure Gate PASS ≠ §1 DESIGN RESOLVED`：前者不自动推出后两者；后两者仅在 §1.19 全部 criterion 实际 PASS 后登记。授权不包含 implementation、Architecture、runtime validation、business acceptance、POC SUCCESS 或 production readiness。

### 1.19 Section 1 Closure Verification（Issue #112）

**Verification base：** current `main @ bc391bd3eaf481c9fdc94a1586703ae19992778a`。读取该版本的 FROZEN inputs、GSD-1 ～ GSD-7、§2 ～ §5 current canonical authority 与 §6 ～ §10 independent status；§4 通过六份 standalone specs 核验，parent stub 不替代规范正文。以下为本次重新核验，**不以历史 §1.4 D／GSF-6 结论替代**。

#### 1.19 A. Current-main composition evidence

| 输入与 exact canonical reference | 本次与 FROZEN P0 / final §1 的 composition 核验 | Result |
| --- | --- | --- |
| §2.1 ～ §2.6，特别是 §2.1.1 ／ §2.1.3、§2.2.1、§2.3.1、§2.4.1、§2.5.1 ／ §2.5.15、§2.6.1 | 需求／库存／替代供给／有效在途支撑 P0-1；数量建议支撑 P0-2，保持 draft／Human decision；不是生产执行或完整 MRP 替代 | PASS |
| §2.7.0 ／ §2.7.14 ～ §2.7.18、§5.3 Q4 ／ §5.4 | Supplier Risk 是 P0 采购建议的 risk evidence；不选择／排名 Supplier、不修改采购数量；SIMULATED design 不证明 H3 | PASS |
| §3.1 ～ §3.10 ／ §3.14；Discovery Validation VR-004 ／ VR-007 | Controlled Export / Snapshot、read-only／draft-only、fail-closed 与 FROZEN 一致；POC 内 Human approval 不解除 source WRITE = DENIED | PASS |
| [canonical-data-model.md](specs/data-integration/canonical-data-model.md) §4.1.1 ～ §4.1.2 ／ §4.1.12 | 既有规则需要的业务实体及关联；不创建新业务能力，source unknown 不等于 conceptual boundary 未定义 | PASS |
| [data-dictionary.md](specs/data-integration/data-dictionary.md) §4.2.1 ／ §4.2.17 | canonical field semantics 支撑同一 P0，不是 database／API／ERP schema 或已验证数据 | PASS |
| [snapshot-import-contract.md](specs/data-integration/snapshot-import-contract.md) §4.3.1 ／ §4.3.21 ～ §4.3.22 ／ §4.3.28 ～ §4.3.29 | immutable／traceable input 支撑受控数据路径，JSON 已批准；contract closure 不证明 import runtime；全局冲突按 B 实际同步后重检 | PASS |
| [data-validation.md](specs/data-integration/data-validation.md) §4.4.1 ～ §4.4.3 ／ §4.4.6 ／ §4.4.9 ～ §4.4.13 ／ §4.4.101 | validation／readiness／failure isolation 支撑数据正确性；package、capability、business failure 保持区分，不重定义 §2 business rules | PASS |
| [master-data-mapping.md](specs/data-integration/master-data-mapping.md) §4.5.24 ～ §4.5.25 | conceptual identity／relationship／source-semantic resolution 支撑既有 P0；不声称真实 ERP field 已知或 mapping runtime 完成 | PASS |
| [adapter-boundary.md](specs/data-integration/adapter-boundary.md) §4.6.2 AC-1／AC-2／AC-22、§4.6.21 ～ §4.6.22 | controlled exported inputs 下的 Adapter／Assembly／Import ownership 支撑 integration；不授予 production access、权限设计或 implementation | PASS |
| §5.0 ～ §5.4 ／ §5.6 ～ §5.15 ／ §5.17 ～ §5.19 | 六类 P0 questions 解释确定性 output，不是 P1 广义查询；LLM 不创造事实，Tool／Agent 不绕过权限／HITL；H4 不因 SIMULATED design 被 resolved | PASS |

#### 1.19 B. Conflict assessment and actual synchronization

| Finding | 对 S-7 / S-13 / S-14 的影响 | 本次处理与最终结论 |
| --- | --- | --- |
| current-main §4 与 snapshot-import-contract.md §4.3.21 ～ §4.3.22 明确 JSON 已决定；全局 Explicit Non-Decisions 却称 concrete file format 尚未决定 | 是真实 current-state contradiction；若照搬，§1 Deferred 会错误包含已决定事项，且 current-state 不一致。仅登记 finding 不足以 PASS | 为满足本次 closure，删除全局未决定清单中的过期项，并明确引用既有 PR #51 Decision／PR #52 closure 与 §4.3.22；未重新选择格式、未修改 spec。实际修正后不再有该 blocking contradiction |
| §2 总览仍把 §4 列为未完成，与 current §4 六项 DESIGN RESOLVED 不一致 | 会把 supporting design current state 误报为 pending，影响 S-7 / S-13 的 composition／同步 | 仅在 §2 总览移除该过期 pending bullet，增加 current §4 routing／状态引用；不改任何 §2 规则或 §4 policy。修正后一致 |
| 旧 §1 Review／GSD registration 中 GSD-8 PENDING、§1 DESIGN PENDING、verification NOT EXECUTED；snapshot-import-contract.md §4.3.29 的旧 Adapter pending snapshot | 这些是各自时点记录，不是新的业务 scope conflict；不能删改历史或把历史当 latest state | §1 顶部与 §1.10 明确历史边界，latest §1 状态集中到 §1.20；spec §4.3.29 已显式以 Issue #90 supersede，latest Adapter status 在 §4.6.21 ～ §4.6.22。历史继续保留，非 blocking |
| FROZEN H3／H4 未确认、真实 ERP fields 未知、runtime 未实现、§6 ～ §10 pending | 是已明确的 evidence／implementation／downstream dependency boundary，不自动构成 §1 goal／scope blocker | 按 GSD-2／GSD-3／GSD-6 保留，不伪造证据、不把依赖推进为完成；§1 conceptual closure 不等于这些事项已满足 |

以上同步严格限于本次 closure 所需的两份允许文件；§4 specs 全部只读。既有 JSON 决策仍由 standalone spec 唯一持有；本 PR 不创建新的 Architecture／serialization policy。未发现需要新 Human policy 才能分类的 final §1 item。

#### 1.19 C. S-1 ～ S-14 verification

| Criterion | Result | Exact canonical evidence | Rationale / blocking impact |
| --- | --- | --- | --- |
| S-1 | PASS | 本节顶部 P0 设计目标；Discovery Brief §10 ／ §11；§1.12 GSD-2.1 ～ GSD-2.6 | FZ-1／FZ-2 与单一 P0 闭环保留；downstream 仅作 supporting pointers；无 blocking impact |
| S-2 | PASS | 顶部 In Scope／Out of Scope；Discovery Brief §12；§2.7.14 ～ §2.7.18；§5.3 ～ §5.4 | 明确区分 risk evidence／P0 explanations 与 P1 comparison／广义查询；未提升 P1；无 blocking impact |
| S-3 | PASS | 顶部 In Scope 三类；§1.14 GSD-4.1 ～ GSD-4.4；§1.19 A | supporting／quality 均可追溯到既有 P0，没有新增业务场景或能力；无 blocking impact |
| S-4 | PASS | 顶部 Out of Scope 逐项 authority 表及跨维度说明；§1.15 GSD-5.1 ～ GSD-5.6 | 按批准四类语义重新分类，无固定先后／first-match；scope／behavior／maturity 关系显式，不采用旧候选规则；无 blocking impact |
| S-5 | PASS | 顶部 POC 成功边界六行映射；Discovery Brief §16；§1.13 GSD-3.1 ～ GSD-3.4 | 六个 dimensions 完整映射三层责任／evidence，不把 design completion 写成成功；无 blocking impact |
| S-6 | PASS | 顶部 Failure / reassessment boundary；Discovery Brief §17；§1.13 GSD-3.8 | 五类失败／重估条件完整保留、未弱化、未写成已发生；无 blocking impact |
| S-7 | PASS | §1.19 A 十行 current-main evidence 与 B 实际 conflict synchronization；各行所列 §2／§3／六份 §4 specs／§5 | 已重新核验 current base；两处 current-state contradiction 已实际修正；Current-main composition check = PASS，Unresolved §2 ～ §5 blocking conflict = NONE |
| S-8 | PASS | 顶部 Downstream dependency expectations；§1.16 GSD-6.1 ～ GSD-6.5；§6 ～ §10 | 每层责任／独立状态明确，只说明 what must be respected；无 automatic closure blocker |
| S-9 | PASS | 顶部 POC 成功边界；§1.13 GSD-3.5；§1.17 GSD-7.4 | 完整区分 design／implementation／runtime-test／business-value／POC SUCCESS／production-ready；success 需两类 evidence；无 blocking impact |
| S-10 | PASS | 顶部 POC 成功边界；Discovery Validation §2 ／ §3.1；§2.7.0；§5.0 ／ §5.17 | 不引入 KPI 数值、真实客户 baseline、usage／adoption 或企业事实，SIMULATED 保持原来源；无 blocking impact |
| S-11 | PASS | 顶部 Deferred／dependency 表；§1.18 授权边界；§10；全局 Explicit Non-Decisions | 本次无 framework／DB／API／deployment／Agent／LLM／ADR 选择；JSON 仅恢复既有批准状态；无 blocking impact |
| S-12 | PASS | Discovery Brief §10 ～ §12 ／ §16 ～ §17 ／ §19；Discovery Validation §2 ／ VR-004 ／ VR-007；§1.12 | FROZEN 文件未改、业务 authority 未反转、P0／P1 未重定义；无 blocking impact |
| S-13 | PASS | 四项顶部 Design Status；§1.8 GSD-8 navigation；§1.20；project-index.md §5 ～ §6；§1.19 B | 全部 PASS 才同步四项 resolved；index／latest block／parent 摘要一致，旧时点显式标为历史；无 blocking impact |
| S-14 | PASS | 顶部四项 final wording；§1.19 A／B；§1.15；§1.17 GSD-7.7 ～ GSD-7.8 | 无新增 scope policy，已发现 blocking contradictions 已实际修正而非只登记；Unresolved blocking scope conflict = NONE |

**Closure Gate = `PASS`（14 / 14 PASS，0 FAIL；无 partial-pass）。** 此结果仅为 §1 conceptual goal／scope closure，非 runtime／business validation。

### 1.20 Current Status（Issue #112 Closure 后）

```
GSD-1 ～ GSD-7                    = REGISTERED（原批准约束保持）
GSD-8                             = REGISTERED（AUTHORIZE）
Dedicated §1 Design Change / Closure PR = AUTHORIZED（Issue #112）
S-1 ～ S-14 verification           = PASS（14 / 14，0 FAIL）
Current-main composition check    = PASS
Unresolved §2 ～ §5 blocking conflict = NONE
Unresolved blocking scope conflict = NONE
§1 Closure Gate                   = PASS
§1 P0 设计目标                     = DESIGN RESOLVED
§1 POC 成功边界                    = DESIGN RESOLVED
§1 In Scope                       = DESIGN RESOLVED
§1 Out of Scope                   = DESIGN RESOLVED
§6 ～ §10                         = 各自 current canonical status 独立保持
Implementation authorization      = NOT GRANTED
POC success                       = NOT CLAIMED
POC Design v0.2                    = DRAFT
```

**State transition：** 本次四项 `DESIGN PENDING → DESIGN RESOLVED` 仅由 §1.19 全部 mandatory criteria PASS 支持，不由 GSD-8 授权本身推出。未宣称 implemented、runtime validated／tested、business accepted 或 production-ready。后续 Coordinator Review／Human merge decision 独立于本次 Agent 执行结果。

---

## 2. P0 Business Rules

> 本节各项均对应 `FROZEN` Discovery Validation v0.1 中的 Open Design Backlog。
>
> **当前状态**：`§2.1` ～ `§2.7` **全部 business-rule sections** 现已 `DESIGN RESOLVED`（均 Human-approved）：
> `§2.1` `BR-SHORTAGE-001`；`§2.2` `BR-INVENTORY-001`；`§2.3` `BR-SUBSTITUTE-001`；
> `§2.4` `BR-REQUIREMENT-001`；`§2.5` `BR-PROCUREMENT-001`；`§2.6` `BR-INBOUND-001`；
> `§2.7` `BR-SUPPLIER-RISK-001`。
>
> **本节范围内仍为 `DESIGN PENDING` 的项**：无。
>
> > **范围限定**：以上**仅**表示
> >
> > ```
> > Section 2 P0 Business Rules = DESIGN RESOLVED
> > ```
> >
> > **不表示** `POC Design v0.2` **整体完成**。
> >
> > **已可声明：**
> >
> > ```
> > Discovery-carried Design Backlog = RESOLVED
> > ```
> >
> > 即所有原先从 Discovery 带入 `POC Design` 的 `VB` backlog 均已完成 Design resolution。
> >
> > **current-state synchronization（Issue #112）：** `§4` 六个专题均已 `DESIGN RESOLVED`，以 §4 routing 所指 standalone canonical specs 为准；本句仅同步状态，不改变任何规则或授权 implementation。
> >
> > **但仍存在以下未完成设计：**
> >
> > - `§6` HITL Workflow
> > - `§7` remaining Permission & Security（除 `Read / Write Boundary` 外）
> > - `§8` Audit & Observability
> > - `§9` Test & AI Eval
> > - `§10` Architecture Decisions

### 2.1 Shortage Definition

**Rule ID:** `BR-SHORTAGE-001`

**Backlog:** `VB-14`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

#### 2.1.1 Business Definition

**「缺料」不是判断当前账面库存是否小于需求。**

缺料判断必须基于：

```
某 Plant
+ 某 Material
+ 某 Required Date
```

**截至该需求日期的累计可用供给，是否能够覆盖累计物料需求。**

**Calculation Grain：**

```
plant_id
+ material_code
+ required_date
```

**默认：不得跨 Plant 自动共享或借用库存。**

> Warehouse 在同一 Plant 内**是否以及如何汇总**，属于 `VB-15`，**本 Task 不定义**。

#### 2.1.2 Deterministic Rule

概念公式：

```
ProjectedAvailable(t)
  = OpeningUsableInventory
  + CumulativeEffectiveInbound(<= t)
  + CumulativeApprovedSubstituteSupply(<= t)
  - CumulativeGrossRequirement(<= t)
```

其中 `t = required_date`。

该公式**必须**按照：

```
plant_id
→ material_code
→ required_date ascending
```

进行**累计**计算。

**不得对每个需求日期独立重复使用同一份库存。**

#### 2.1.3 Dependency Boundary

以下输入的**含义**由本规则引用，但其**具体计算方式不在本 Task 定义**：

| 输入 | 归属 | 状态 |
| --- | --- | --- |
| `OpeningUsableInventory` | **`BR-INVENTORY-001` / §2.2** | **`DESIGN RESOLVED`** |
| `SafetyStock` | **`BR-INVENTORY-001` / §2.2** | **`DESIGN RESOLVED`** |
| `CumulativeEffectiveInbound` | **`BR-INBOUND-001` / §2.6** | **`DESIGN RESOLVED`** |
| `CumulativeApprovedSubstituteSupply` | **`BR-SUBSTITUTE-001` / §2.3** | **`DESIGN RESOLVED`** |
| `CumulativeGrossRequirement` | **`BR-REQUIREMENT-001` / §2.4** | **`DESIGN RESOLVED`** |

因此：

> `BR-SHORTAGE-001` 的 **Shortage Classification 设计可以 `DESIGN RESOLVED`**，且其**五项核心依赖现已全部解决**：
>
> - `OpeningUsableInventory`、`SafetyStock` ← **`BR-INVENTORY-001`**
> - `CumulativeEffectiveInbound` ← **`BR-INBOUND-001`**
> - `CumulativeApprovedSubstituteSupply` ← **`BR-SUBSTITUTE-001`**
> - `CumulativeGrossRequirement` ← **`BR-REQUIREMENT-001`**
>
> 因此可以声明：
>
> > **Shortage Engine core dependency chain = `DESIGN COMPLETE`**
>
> 但**必须明确**：`DESIGN COMPLETE` **≠** `IMPLEMENTED` **≠** `TESTED` **≠** production-ready。
>
> **仍不得声称**：`IMPLEMENTED`、`TESTED`、或**可运行**。

#### 2.1.4 Classification States

定义四个**确定性**状态：

**A. `NORMAL`**

- **条件：** `ProjectedAvailable >= SafetyStock`
- **含义：** 供给覆盖需求，且并未跌破 Safety Stock。

**B. `BUFFER_BREACH`**

- **条件：** `0 <= ProjectedAvailable < SafetyStock`
- **含义：** 当前仍能满足需求，但 Safety Stock buffer 已被侵蚀。

> **注意：`BUFFER_BREACH` 不是 `SHORTAGE`。**

**C. `SHORTAGE`**

- **条件：** `ProjectedAvailable < 0`
- **含义：** 截至该 Required Date，累计可用供给已经不足以覆盖累计需求。

**D. `DATA_INCOMPLETE`**

当完成分类所必需的**关键输入无法可靠取得**时：

**不得**返回 `NORMAL` / `BUFFER_BREACH` / `SHORTAGE`，而返回 **`DATA_INCOMPLETE`**。

该状态表示：**计算无法可靠完成** —— **不是业务风险等级**。

#### 2.1.5 Quantity Definitions

```
ShortageQty = max(0, -ProjectedAvailable)
```

```
BufferGap   = max(0, SafetyStock - ProjectedAvailable)
```

> **注意**：当 `ProjectedAvailable >= 0` 但 `ProjectedAvailable < SafetyStock` 时，则 `ShortageQty = 0`。
>
> 即：**Safety Stock breach 不得被错误解释为实际生产缺料。**

#### 2.1.6 Time-based Results

```
FirstShortageDate
  = 按 required_date ascending，最早满足 ProjectedAvailable < 0 的日期
```

```
FirstBufferBreachDate
  = 按 required_date ascending，最早满足 ProjectedAvailable < SafetyStock 的日期
```

如果从未满足对应条件：`result = null / not present`。

> 具体代码表现形式留待 **implementation**。

#### 2.1.7 `DATA_INCOMPLETE` Principle

至少记录以下原则：

如果关键输入存在无法解析的情况，例如：

- material mapping missing
- BOM unresolved
- required_date missing
- inventory snapshot unusable
- dependent calculation cannot provide reliable value

则：**不得由 LLM 或 deterministic engine 自行猜测或补值。**

**必须返回 `DATA_INCOMPLETE`。**

> **注意**：本 Task **不定义**完整 Data Quality error taxonomy，只定义该 **classification safety rule**。

#### 2.1.8 Decision Table

| Condition | Classification |
| --- | --- |
| Required critical data unavailable | `DATA_INCOMPLETE` |
| `ProjectedAvailable < 0` | `SHORTAGE` |
| `0 <= ProjectedAvailable < SafetyStock` | `BUFFER_BREACH` |
| `ProjectedAvailable >= SafetyStock` | `NORMAL` |

**优先级：`DATA_INCOMPLETE` 优先于所有业务分类。**

#### 2.1.9 Acceptance Examples

以下为 **deterministic examples**。

**Example A — `NORMAL`**

| 输入 | 值 |
| --- | --- |
| Usable Inventory | 100 |
| Effective Inbound | 50 |
| Gross Requirement | 100 |
| Safety Stock | 30 |

`ProjectedAvailable = 100 + 50 - 100 = 50`

**Expected：** `NORMAL`，`ShortageQty = 0`，`BufferGap = 0`

**Example B — `BUFFER_BREACH`**

| 输入 | 值 |
| --- | --- |
| Usable Inventory | 100 |
| Effective Inbound | 40 |
| Gross Requirement | 120 |
| Safety Stock | 30 |

`ProjectedAvailable = 100 + 40 - 120 = 20`

**Expected：** `BUFFER_BREACH`，`ShortageQty = 0`，`BufferGap = 10`

**Example C — `SHORTAGE`**

| 输入 | 值 |
| --- | --- |
| Usable Inventory | 100 |
| Effective Inbound | 40 |
| Gross Requirement | 160 |
| Safety Stock | 30 |

`ProjectedAvailable = 100 + 40 - 160 = -20`

**Expected：** `SHORTAGE`，`ShortageQty = 20`

**Example D — Cumulative calculation**

| 输入 | 值 |
| --- | --- |
| Opening Inventory | 100 |
| Effective Inbound | 0 |
| Safety Stock | 0 |

`2026-10-10`：Demand = 80 → Cumulative `ProjectedAvailable = 100 - 80 = 20`

**Expected：** `NORMAL`

`2026-10-15`：Additional Demand = 60 → Cumulative Demand = 140 → `ProjectedAvailable = 100 - 140 = -40`

**Expected：** `SHORTAGE`

**`FirstShortageDate`：`2026-10-15`**

> **必须明确：不得错误计算为 `100 >= 80` 与 `100 >= 60`** —— 因为这样会**重复使用同一份库存**。

**Example E — `DATA_INCOMPLETE`**

场景：Material mapping cannot be resolved.

**Expected：** `DATA_INCOMPLETE`

**不得输出** `NORMAL` / `BUFFER_BREACH` / `SHORTAGE`。

#### 2.1.10 AI Boundary

**Shortage Classification 必须由 deterministic logic 产生。**

正确链路：

```
Structured Data
↓
Deterministic Shortage Engine
↓
Classification + Quantities + Evidence
↓
LLM
↓
Explanation
```

LLM **可以**：

- 解释为什么缺料
- 解释缺多少
- 解释什么时候开始缺
- 总结主要 Supply / Demand evidence

LLM **不可以**：

- 自己决定是否 `SHORTAGE`
- 自己修改 `ProjectedAvailable`
- 猜测缺失数据
- 自己产生 `SafetyStock`
- 自己产生 `Effective Inbound`

#### 2.1.11 Risk Boundary

**`BR-SHORTAGE-001` 只定义 Shortage Classification。**

**不得在本规则定义**：`HIGH RISK`、`MEDIUM RISK`、`LOW RISK`、Supplier Risk Score、Risk Severity。

这些属于 **`VB-27`（Supplier Risk / Risk Evidence）**。

因此：

- **`SHORTAGE` ≠ `HIGH RISK`**
- **`BUFFER_BREACH` ≠ `MEDIUM RISK`**

**不得建立未经批准的映射。**

> 关联的 FROZEN 原问题：「缺料」在业务上如何定义？（依据 `K-BR-1`；关联 `G-07`）

### 2.2 Available Inventory / Safety Stock

**Rule ID:** `BR-INVENTORY-001`

**Backlog:** `VB-15`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

#### 2.2.1 Calculation Grain

`OpeningUsableInventory` 的计算粒度：

```
plant_id
+ material_code
+ inventory_snapshot_time
```

**默认：不得跨 Plant 自动共享库存。**

> 跨 Plant transfer / rebalancing **不属于本规则自动能力**。
>
> 如果未来需要，必须作为**独立 Supply Event / Design Rule** 处理。

#### 2.2.2 OpeningUsableInventory

定义：

```
OpeningUsableInventory
  = 同一 Plant 内
    所有符合 POC Inventory Scope
    且状态允许使用的 On-hand Inventory 之和
```

概念公式：

```
OpeningUsableInventory = Σ EligibleOnHandQty
```

其中：`EligibleOnHandQty` **只来自允许的 Inventory Status**。

> **不得直接使用 `Book Inventory Total` 作为 `OpeningUsableInventory`。**

#### 2.2.3 Inventory Status Eligibility

当前 POC 采用**保守规则**。

**A. `AVAILABLE`**

- **Eligibility:** **100%**
- **处理：** 计入 `OpeningUsableInventory`。

**B. `INSPECTION`**

- **Eligibility:** **0%**
- **处理：** **不计入** `OpeningUsableInventory`。
- **原因：** 尚未完成质量放行，POC **不提前假定**其可用于生产。

**C. `FROZEN`**

- **Eligibility:** **0%**
- **处理：** **不计入** `OpeningUsableInventory`。
- **原因：** 冻结库存当前**不可用于缺料覆盖**。

**D. Unknown / Invalid Status**

**不得猜测其可用性。**

结果：`DATA_INCOMPLETE` 或明确的 **Data Quality Issue**。

**不得静默归类为 `AVAILABLE`。**

#### 2.2.4 Warehouse Aggregation

同一个 Plant 内：**只聚合被纳入 POC Inventory Scope 的 Warehouse。**

例如 `Plant-A`：

| Warehouse | 状态 | 数量 |
| --- | --- | --- |
| Warehouse-01 | `AVAILABLE` | 100 |
| Warehouse-02 | `AVAILABLE` | 30 |
| Warehouse-QA | `INSPECTION` | 40 |
| Warehouse-FR | `FROZEN` | 20 |

则：

- **Book Inventory = 190**
- **`OpeningUsableInventory` = 130**
- **Excluded Inventory = 60**

**注意：**

- 当前规则**不因为 Warehouse 不同就禁止同 Plant 聚合**。
- 但：Warehouse **必须属于同一 Plant**，且位于**当前 POC Inventory Scope** 中。
- **不同 Plant 的库存：不得自动聚合。**

#### 2.2.5 Safety Stock Baseline

当前 POC 采用：**Configured Safety Stock**

粒度：

```
plant_id
+ material_code
```

定义：

```
SafetyStock = 由业务配置提供的非负数量
```

**当前不设计**：

- statistical safety stock
- service-level calculation
- demand variability model
- lead-time variability model
- dynamic safety stock
- AI-generated safety stock

> 这些**均不属于本 Task**。

#### 2.2.6 Zero vs Missing

**必须严格区分：`SafetyStock = 0` 与 `SafetyStock = missing`。**

**`SafetyStock = 0`**

表示业务**明确配置**为：无 Safety Stock buffer。

**这是合法值。**

**`SafetyStock = missing`**

表示**必要配置缺失**。

**不得默认成 0。**

应导致：**`DATA_INCOMPLETE`**。

**不得让 LLM 或 Rule Engine 猜测默认值。**

#### 2.2.7 Safety Stock Must Not Be Double-counted

**明确禁止：**

```
OpeningUsableInventory = Inventory - SafetyStock      ← 禁止
```

因为 `BR-SHORTAGE-001` 已经使用 `SafetyStock` 作为 **Classification Threshold**：

```
ProjectedAvailable >= SafetyStock        → NORMAL
0 <= ProjectedAvailable < SafetyStock    → BUFFER_BREACH
ProjectedAvailable < 0                   → SHORTAGE
```

因此**正确关系**：

```
Inventory
↓
OpeningUsableInventory
↓
ProjectedAvailable
↓
compare with SafetyStock
```

**`SafetyStock` 是 Classification Threshold，不是 Opening Inventory 的预先扣减项。**

> 否则会导致 **Safety Stock double counting**。

#### 2.2.8 Negative Inventory

当前 POC 对 `on_hand_qty < 0` 采用**保守规则**。

**不得自动** `clamp to 0`。

**不得自行解释成**正常可用库存。

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**。

**原因**：负库存可能来源于：

- posting delay
- inventory discrepancy
- data quality issue
- unresolved business condition

> 其具体业务含义**不在本 Task 定义**。

#### 2.2.9 Data Quality Safety Rule

如果以下关键数据**无法可靠取得**：

- `material_code` unresolved
- `plant_id` unresolved
- warehouse ownership unresolved
- `inventory_status` missing / invalid
- `on_hand_qty` invalid
- `inventory_snapshot_time` missing
- `SafetyStock` missing

则：**不得产生正常业务分类输入。**

输出应进入：**`DATA_INCOMPLETE`**。

> **注意**：本 Task **不设计**完整 Data Quality taxonomy，只定义**库存输入的 fail-safe behavior**。

#### 2.2.10 Acceptance Examples

以下为 **deterministic examples**。

**Example A — Eligible warehouses**

`Plant-A` / `MAT-001`：

| Warehouse | 状态 | 数量 |
| --- | --- | --- |
| Warehouse-01 | `AVAILABLE` | 100 |
| Warehouse-02 | `AVAILABLE` | 30 |
| Warehouse-QA | `INSPECTION` | 40 |
| Warehouse-FR | `FROZEN` | 20 |

**Expected：**

- **Book Inventory = 190**
- **`OpeningUsableInventory` = 130**

**Example B — `BUFFER_BREACH` interaction**

| 输入 | 值 |
| --- | --- |
| `OpeningUsableInventory` | 130 |
| Effective Inbound | 0 |
| Gross Requirement | 105 |
| `SafetyStock` | 30 |

`ProjectedAvailable = 130 + 0 - 105 = 25`

**Expected：** `BUFFER_BREACH`，`ShortageQty = 0`，`BufferGap = 5`

**Example C — `SafetyStock = 0`**

`OpeningUsableInventory = 100`，`SafetyStock = 0`

该配置**合法**。

**不得解释为 missing。**

**Example D — `SafetyStock` missing**

`SafetyStock = missing`

**Expected：** `DATA_INCOMPLETE`

**不得默认成 0。**

**Example E — Negative Inventory**

`Warehouse-01`：`AVAILABLE = -5`

**Expected：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得自动变成 0。**

**Example F — Cross Plant**

| Plant | `AVAILABLE` |
| --- | --- |
| `Plant-A` | 20 |
| `Plant-B` | 100 |

计算 `Plant-A` 时：**`OpeningUsableInventory` = 20**

**不得自动得到 120。**

#### 2.2.11 AI Boundary

**库存可用性判断必须由 deterministic rules 决定。**

LLM **不可以**：

- 将 `INSPECTION` 猜成 `AVAILABLE`
- 将 `FROZEN` 库存释放
- 将 missing `SafetyStock` 默认成 0
- 将负库存改成 0
- 跨 Plant 自动借库存
- 猜测 Warehouse 所属 Plant

LLM **可以**解释：

- 为什么某库存未被计入
- 哪些 Warehouse 被排除
- 为什么返回 `DATA_INCOMPLETE`

> 关联的 FROZEN 原问题：安全库存如何计算？（关联 `G-04`）

### 2.3 Substitute Material

**Rule ID:** `BR-SUBSTITUTE-001`

**Backlog:** `VB-16`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

> 关联的 FROZEN 原问题：替代料如何处理？（关联 `G-05`）

#### 2.3.1 Business Definition

本规则回答：

> 某 Target Material 在某个 `required_date` 之前，可以从**已批准的替代关系**获得多少**等效供给**。

**Core Principle — 替代料不得由 AI 自行推断。**

只有**同时满足**以下**全部**条件的替代供给，才可以进入：

```
CumulativeApprovedSubstituteSupply
```

1. **明确存在 Substitute Relationship**（来自受控数据源中**已登记**的关系）；
2. 该 relationship **已 `APPROVED`**；
3. `source`（Substitute Material）与 `target`（Target Material）**可可靠映射**；
4. **同一 Plant**；
5. `source` inventory 符合 **`BR-INVENTORY-001`** 的 eligible inventory rule（`AVAILABLE`）；
6. **存在明确 allocation**。

上述任一条件不满足，或无法可靠判断，该替代供给**不得计入**。

如果因此无法可靠完成计算：**`DATA_INCOMPLETE`**（见 §2.3.11）。

#### 2.3.2 Calculation Grain

`CumulativeApprovedSubstituteSupply` 按以下粒度计算，与 **`BR-SHORTAGE-001`** 对齐：

```
plant_id
+ target_material_code
+ required_date
```

**不得跨 Plant 合并或借用**替代供给。

#### 2.3.3 Directional Relationship

**替代关系必须是有方向的。**

```
Target Material A
  ← can be covered by
Substitute Material B
```

即：**A 可被 B 替代。**

**不代表：B 可以被 A 替代。**

**不得自动建立双向关系。**

**不得**根据以下任何依据**创建**替代关系：

- name similarity
- description similarity
- LLM reasoning
- embedding similarity

替代关系**只能**来自受控数据源中**已登记**的 Substitute Relationship。

> 本 Task **不设计**该关系的维护 / 录入流程。

#### 2.3.4 Minimum Relationship Attributes

一个 Substitute Relationship 概念上至少需要：

| Attribute | 含义 |
| --- | --- |
| `plant_id` | 该替代关系适用的 Plant |
| `target_material_code` | 被覆盖的 Target Material |
| `substitute_material_code` | 提供覆盖的 Substitute Material |
| `substitution_ratio` | 换算率（见 §2.3.6） |
| `approval_status` | 审批状态（见 §2.3.5） |

这些是 **canonical business attributes**。

**本 Task 不定义**：

- database schema
- ERP field mapping
- API contract

#### 2.3.5 Approval Requirement

**只有**：

```
approval_status = APPROVED
```

的关系**可以参与** shortage calculation。

其他状态，例如：

- `PENDING`
- `REJECTED`
- `UNKNOWN`

**不得进入** Approved Substitute Supply。

如果 `approval_status` **缺失**或**无法可靠判断**：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得由 LLM 自动批准。**

> 本 Task **不定义** approval workflow（由谁批准、通过什么流程批准、如何记录审批人）。

#### 2.3.6 `substitution_ratio` Canonical Semantic

`substitution_ratio` 表示：

> **1 unit Substitute Material 可以覆盖多少 unit Target Material Requirement。**

例如：

```
substitution_ratio = 1.0
```

表示：

```
1 B
  → equivalent to 1 A
```

```
substitution_ratio = 0.5
```

表示：

```
1 B
  → equivalent to 0.5 A
```

定义：

```
EquivalentTargetQty
  = AllocatedSubstituteQty × substitution_ratio
```

**要求：**

```
substitution_ratio > 0
```

**注意语义方向**：这是 **substitute → target** 的换算率，**不是** target → substitute。

如果 `substitution_ratio` **missing** 或 **invalid**（包含 `<= 0`）：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得猜测。**

**不得**：

- `clamp`
- **默认成 `1.0`**
- 自动改成其他数值
- 让 LLM 修正

#### 2.3.7 Explicit Allocation

**不得**将 Substitute Material 的**全部库存**自动视为 Target Material 的供给。

**必须存在明确 allocation：**

```
AllocatedSubstituteQty
```

例如：

```
MAT-B AVAILABLE = 100

Human-approved allocation:
  60 MAT-B
    → MAT-A
```

则：

```
AllocatedSubstituteQty = 60
```

**而不是** `100`。

**要求：**

```
AllocatedSubstituteQty >= 0
```

`AllocatedSubstituteQty = 0` 是**合法值**，表示该替代关系在本需求窗口内**未分配**任何数量。

但 `AllocatedSubstituteQty` **missing** 或 **invalid** 表示必要 allocation 信息**缺失**：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得默认成 0。**

> 本 Task **不定义** allocation 的产生方式（人工配置 / 计划系统 / 算法），只要求 allocation **可追溯**。

#### 2.3.8 Eligible Source Supply

当前 POC 第一版**只允许**使用：

```
同一 Plant
+ BR-INVENTORY-001 判定为 AVAILABLE 的 Substitute Inventory
```

参与 allocation。

**不得自动使用**：

- `INSPECTION`
- `FROZEN`
- Future Substitute Inbound
- Cross-Plant Inventory

这些如未来需要，**必须通过后续独立 Design Change 引入**。

> 关于 `AVAILABLE` / `INSPECTION` / `FROZEN` 的判定口径，见 **`BR-INVENTORY-001` / §2.2**，本规则**不重新定义**。

#### 2.3.9 Same Plant Boundary

Target Material 与 Substitute Supply **默认必须属于同一 `plant_id`**。

例如：

```
Target               = Plant-A / MAT-A
Substitute Inventory = Plant-B / MAT-B
```

**不得直接计入。**

跨 Plant **必须先形成独立的**：

```
transfer / supply event
```

**本 Task 不设计该机制。**

如果 Plant 映射无法可靠判断：`DATA_INCOMPLETE` ＋ **Data Quality Issue**。

#### 2.3.10 No Double Allocation

**同一份 Substitute Supply 不得被重复分配。**

必须满足：

```
Σ AllocatedSubstituteQty
  <= EligibleSubstituteSupply
```

例如：

```
MAT-B AVAILABLE = 100

  60 → MAT-A
  40 → unallocated
```

则**已分配的 60 不得同时**：

- 分配给其他 Target（例如 `MAT-C`）；
- 作为**未分配** Substitute Supply；
- 被多个 shortage **同时重复消费**；
- 继续作为 `MAT-B` **自身可自由使用的完整** Available Supply。

如果约束被违反（例如 `60 → MAT-A` 且 `50 → MAT-C`，合计 `110 > 100`）：

**处理：** `DATA_INCOMPLETE` ＋ **Allocation Conflict**

**不得 silently over-allocate。**

**Supply Conservation / Reservation Constraint**

一旦 `AllocatedSubstituteQty` 被分配给某 Target Material，该数量**必须**从 Source Material 在**相同有效需求窗口**内仍可自由使用的 **Eligible Supply Pool** 中**保留 / 扣除**。

因此，**已分配数量不得同时**：

- 分配给其他 Target；
- 作为**未分配** Substitute Supply；
- 被多个 shortage **重复消费**；
- 继续作为 Source Material 自身**可自由使用的完整** Available Supply。

定义：

```
RemainingUnallocatedSourceSupply
  = EligibleSubstituteSupply
  - Σ AllocatedSubstituteQty
```

要求：

```
RemainingUnallocatedSourceSupply >= 0
```

> 这**只是 supply-conservation invariant**，**不是**新的 optimization / allocation algorithm。

**与 `BR-INVENTORY-001` 的关系**

`BR-INVENTORY-001` 定义的是**原始 eligible inventory baseline**（见 §2.2）。

本规则**不修改** `BR-INVENTORY-001` 的原始定义。

但当某部分 `AVAILABLE` inventory **已形成有效 Substitute Allocation** 时，后续 shortage evaluation **不得**继续把该**已分配数量**视为 Source Material 的 **uncommitted supply**。

本节只建立 **`BR-SUBSTITUTE-001` 的 allocation reservation constraint**，**不重新定义** `BR-INVENTORY-001`。

**时间边界（Demand Window）**

该 reservation **只作用于 allocation 有效的 demand window**。

由于本 Task **不设计复杂 allocation timing engine**：

如果**无法可靠判断** allocation 与 Source Material **自身需求窗口是否重叠**：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得同时把 supply 计入两边。**

> 本 Task **只定义约束**。**不得设计**：
>
> - optimization algorithm
> - allocation priority
> - shortage prioritization
> - auto scheduling

#### 2.3.11 Zero vs Missing

必须区分两种**语义完全不同**的情况：

**A. 没有批准的 Substitute Relationship**

如果业务**明确**：Target Material **没有** Approved Substitute

则：

```
ApprovedSubstituteSupply = 0
```

这是**合法状态**，**不得**返回 `DATA_INCOMPLETE`。

**B. Substitute data 无法可靠取得**

如果**存在**替代关系，但出现以下任一情况：

- `substitution_ratio` missing / invalid
- `approval_status` unknown
- allocation qty invalid
- source material unresolved
- target material unresolved
- plant mapping unresolved

则：

**`DATA_INCOMPLETE`**

**不得默认成 0。**

#### 2.3.12 Deterministic Formula

对于**每一个有效 allocation** `i`：

```
EquivalentTargetQty(i)
  = AllocatedSubstituteQty(i) × substitution_ratio(i)
```

随后：

```
CumulativeApprovedSubstituteSupply(<= t)
  = Σ EquivalentTargetQty(i)
```

**仅包含**同时满足以下条件的 allocation：

- approved relationship
- same Plant
- eligible `AVAILABLE` source inventory
- explicit allocation
- allocation 对当前 `required_date` **有效**

**本 Task 不设计复杂 allocation timing engine。**

如果 allocation **无法可靠关联**当前需求窗口：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

> allocation 与需求窗口的关联机制属 **canonical business meaning 之后的 source mapping**，进入后续 **Data Dictionary / Adapter Design**。

#### 2.3.13 Acceptance Examples

以下为 **deterministic examples**。

**Example A — 1:1 substitute**

| 字段 | 值 |
| --- | --- |
| MAT-B AVAILABLE | 100 |
| Approved allocation to MAT-A | 60 |
| `substitution_ratio` | 1.0 |

**Expected：**

- `EquivalentTargetQty = 60`

**Example B — Conversion ratio**

| 字段 | 值 |
| --- | --- |
| `AllocatedSubstituteQty` | 60 |
| `substitution_ratio` | 0.8 |

**Expected：**

- `EquivalentTargetQty = 48`

**Example C — Relationship not approved**

| 字段 | 值 |
| --- | --- |
| `approval_status` | `PENDING` |

**Expected：**

- **不得计入** Approved Substitute Supply

**Example D — Cross Plant**

| 字段 | 值 |
| --- | --- |
| Target | Plant-A / MAT-A |
| Substitute | Plant-B / MAT-B |

**Expected：**

- **不得直接计入**

**Example E — No substitute exists**

业务**明确**无 Approved Substitute。

**Expected：**

- `ApprovedSubstituteSupply = 0`
- **不得**返回 `DATA_INCOMPLETE`

**Example F — Missing ratio**

Approved relationship exists，但 `substitution_ratio` **missing**。

**Expected：**

- `DATA_INCOMPLETE`

**Example G — No double allocation**

| 字段 | 值 |
| --- | --- |
| Eligible MAT-B | 100 |
| Allocation | 60 → MAT-A；50 → MAT-C |

**Expected：**

- **`INVALID`**

因为：

```
110 > 100
```

必须：

- `DATA_INCOMPLETE`
- ＋ **Allocation Conflict**

**不得 silently over-allocate。**

**Example H — Source supply conservation**

| 字段 | 值 |
| --- | --- |
| MAT-B AVAILABLE | 100 |
| Allocation | 60 MAT-B → MAT-A |
| `substitution_ratio` | 1.0 |

**Expected：**

- `MAT-A ApprovedSubstituteSupply = 60`
- `RemainingUnallocatedSourceSupply(MAT-B) = 40`

对于**同一有效需求窗口**：

- `MAT-B` **不得继续按 `100` 作为完全未承诺 supply 使用**。

如果**无法可靠判断** allocation 与 `MAT-B` **自身需求窗口是否重叠**：

- `DATA_INCOMPLETE`

#### 2.3.14 AI Boundary

**Alternative supply eligibility、allocation 与 quantity 必须由 deterministic logic 决定。**

LLM **不可以**：

- 创建 substitute relationship
- 批准 substitute relationship
- 猜 `substitution_ratio`
- 自行决定 allocation qty
- 跨 Plant 自动调货
- 自动决定 shortage priority
- 重复使用同一 supply

LLM **可以**解释：

- 哪个 Substitute 被批准
- 分配了多少
- conversion 后等效多少
- 为什么某替代料未被计入
- 为什么出现 `DATA_INCOMPLETE`

#### 2.3.15 Source-field Boundary

**本规则定义 business semantic，而不是 source schema。**

因此**不得创建**：

- ERP field mapping
- API Contract
- database column definition
- adapter implementation
- allocation engine
- optimization engine

例如 `substitution_ratio`、`approval_status`、`AllocatedSubstituteQty` **只是 canonical business meaning**。

其 **source mapping** 进入后续 **Data Dictionary / Adapter Design**。

### 2.4 Scrap / Loss

**Rule ID:** `BR-REQUIREMENT-001`

**Backlog:** `VB-17`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

#### 2.4.1 Business Definition

本规则回答：

> 在某个 Production Requirement 下，某 Material 为满足生产**所需要准备的 Gross Material Requirement 是多少**。

原则：

先依据：

```
Production Requirement
× BOM Component Quantity
```

计算**净物料需求**，再依据**明确配置的 `loss_rate`** 放大为 **Gross Requirement**。

**不得让 LLM 自行估算需求或损耗率。**

#### 2.4.2 Calculation Grain

计算**至少对齐**：

```
plant_id
+ material_code
+ required_date
```

并能够**追溯到**：

```
Production Requirement
+ BOM relationship
```

**不得跨 Plant 合并需求。**

#### 2.4.3 BaseRequirement

定义：

```
BaseRequirement = ProductionQty × BOMComponentQty
```

其中：

```
ProductionQty    >= 0
BOMComponentQty  >= 0
```

**示例：**

```
ProductionQty   = 100
BOMComponentQty = 2
→ BaseRequirement = 200
```

**注意**：本规则**只使用已经可靠解析的 BOM input**。

**不得在本 Task 设计**：

- BOM version selection
- BOM validity selection
- BOM explosion algorithm
- ERP source-field mapping

如果**无法可靠确定适用 BOM**：**`DATA_INCOMPLETE`**。

#### 2.4.4 `loss_rate` Canonical Semantic

正式定义 POC 中 `loss_rate` 表示：

> **预计投入总量中会发生损耗的比例。**

因此：

```
loss_rate = 0.05
```

表示：**预计投入量的 5% 会损耗**。

**这是 POC 的 canonical business semantic。**

**不得将其混淆为**"在净需求上额外加 5%"。

如果未来真实系统中的字段语义是 `markup`、`allowance`、`scrap add-on` 或其他定义，**必须**在后续 **Data Mapping / Adapter 层**转换为本规则的 canonical semantic。

**不得偷偷改变本公式。**

#### 2.4.5 GrossRequirement Formula

定义：

```
GrossRequirement = BaseRequirement / (1 - loss_rate)
```

前提：

```
0 <= loss_rate < 1
```

**示例：**

```
BaseRequirement = 200
loss_rate       = 0.05
→ GrossRequirement = 200 / 0.95 = 210.526315...
```

#### 2.4.6 `loss_rate` Validation

**合法范围：**

```
0 <= loss_rate < 1
```

**合法示例：** `0`、`0.03`、`0.15`

**非法示例：** `-0.05`、`1.0`、`1.2`

**非法值处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得**：

- `clamp`
- 自动改为 0
- 自动改成最大值
- 让 LLM 修正

#### 2.4.7 Zero vs Missing

**必须严格区分：`loss_rate = 0` 与 `loss_rate = missing`。**

**`loss_rate = 0`**

表示：业务**明确配置为无损耗**。

**这是合法值。**

**`loss_rate = missing`**

表示：**必要业务配置缺失**。

**处理：** `DATA_INCOMPLETE`

**不得默认成 0。**

**不得让 LLM 或 Rule Engine 猜测。**

#### 2.4.8 Quantity Precision Boundary

本规则产生 **canonical `GrossRequirement` quantity**。

**本 Task 不定义**：

- `ceil`
- `floor`
- `round`
- integer packaging rule
- UOM-specific precision
- pack size rounding

例如：

```
GrossRequirement = 210.526315...
```

本规则**保持该 canonical quantity**。

**不得本轮自行变成 `210` 或 `211`。**

> 具体 quantity precision / rounding 由**后续明确 Design Rule** 决定。

#### 2.4.9 CumulativeGrossRequirement

对同一 `plant_id` + `material_code`，按 `required_date ascending` 累计：

```
CumulativeGrossRequirement(<= t) = Σ GrossRequirement   where required_date <= t
```

**示例：**

```
2026-10-10  GrossRequirement = 100
2026-10-15  GrossRequirement = 70
```

则：

```
CumulativeGrossRequirement(<= 2026-10-10) = 100
CumulativeGrossRequirement(<= 2026-10-15) = 170
```

**不得把每个日期当成彼此独立需求。**

#### 2.4.10 Substitute Boundary

本规则**只负责原目标 Material 的需求侧计算**。

**不得**因为存在 Substitute Material 而降低 `BaseRequirement` 或 `GrossRequirement`。

替代料属于**供给侧** `CumulativeApprovedSubstituteSupply`，由 **`BR-SUBSTITUTE-001` / §2.3**（`VB-16`）单独设计。

因此必须保持 **`GrossRequirement` 与 `Substitute Supply` 两个概念分离**。

**不得 double counting。**

#### 2.4.11 Data Quality / Fail-safe

如果以下关键输入**无法可靠取得**：

- ProductionQty missing / invalid
- `ProductionQty < 0`
- BOM unresolved
- BOMComponentQty missing / invalid
- `BOMComponentQty < 0`
- `loss_rate` missing
- `loss_rate` invalid
- `plant_id` unresolved
- `material_code` unresolved
- `required_date` missing / invalid

则：**`DATA_INCOMPLETE`**

**不得**：

- 猜测 BOM
- 猜测 `loss_rate`
- 猜测 `required_date`
- 自动填默认值
- 让 LLM 补业务事实

> 本 Task **不设计**完整 Data Quality taxonomy，只定义**本规则的 fail-safe behavior**。

#### 2.4.12 Acceptance Examples

以下为 **deterministic examples**。

**Example A — No loss**

| 输入 | 值 |
| --- | --- |
| ProductionQty | 100 |
| BOMComponentQty | 2 |
| `loss_rate` | 0 |

**Expected：**

- `BaseRequirement = 200`
- `GrossRequirement = 200`

**Example B — 5% loss**

| 输入 | 值 |
| --- | --- |
| ProductionQty | 100 |
| BOMComponentQty | 2 |
| `loss_rate` | 0.05 |

**Expected：**

- `BaseRequirement = 200`
- `GrossRequirement = 200 / 0.95 = 210.526315...`

**不得自动 round / ceil。**

**Example C — Missing loss rate**

`loss_rate = missing`

**Expected：** `DATA_INCOMPLETE`

**不得默认成 0。**

**Example D — Invalid loss rate**

`loss_rate = 1.0`

**Expected：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**Example E — BOM unresolved**

`ProductionQty = 100`，BOM cannot be reliably resolved

**Expected：** `DATA_INCOMPLETE`

**不得让 LLM 猜 `BOMComponentQty`。**

**Example F — Cumulative requirement**

| required_date | GrossRequirement |
| --- | --- |
| `2026-10-10` | 100 |
| `2026-10-15` | 70 |

**Expected：**

- `CumulativeGrossRequirement(<= 2026-10-10) = 100`
- `CumulativeGrossRequirement(<= 2026-10-15) = 170`

**Example G — Substitute must not reduce requirement**

Original Material `GrossRequirement = 100`；存在 Substitute Supply = 30。

**Expected：** `GrossRequirement` 仍然 **= 100**

**不得自动改成 70。**

> Substitute Supply 的影响由 **`BR-SUBSTITUTE-001` / §2.3**（supply-side rule）单独处理。

#### 2.4.13 AI Boundary

`BaseRequirement`、`GrossRequirement`、`CumulativeGrossRequirement` **必须由 deterministic logic 产生**。

LLM **不可以**：

- 生成 `loss_rate`
- 修改 `ProductionQty`
- 修改 `BOMComponentQty`
- 猜 BOM
- 选择 BOM version
- 对 `GrossRequirement` 自行 round
- 用 Substitute Supply 修改需求端

LLM **可以**解释：

- `BaseRequirement` 如何得到
- `loss_rate` 如何影响 `GrossRequirement`
- 为什么返回 `DATA_INCOMPLETE`
- 某日期累计需求如何形成

> 关联的 FROZEN 原问题：损耗率规则？（关联 `G-03`）

### 2.5 MOQ / Purchase Recommendation Quantity

**Rule ID:** `BR-PROCUREMENT-001`

**Backlog:** `VB-18`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

> 关联的 FROZEN 原问题：采购最小批量（MOQ）是否影响采购建议？（关联 `G-10`）

#### 2.5.1 Business Definition

本规则回答：

> 当 Shortage Engine 已确认某 Material 存在**真实 `SHORTAGE`** 时，POC 应建议采购**多少数量**。

当前 POC 采用**保守原则**：

只有：

```
Classification = SHORTAGE
```

才生成 **numeric Purchase Recommendation**。

以下状态当前 POC **不自动生成采购数量建议**：

- `NORMAL`
- `BUFFER_BREACH`

其中 `BUFFER_BREACH` **只是 Safety Stock buffer 被侵蚀**，**并不等同于实际缺料**。

**不得为了恢复 Safety Stock 自动创建采购需求。**

#### 2.5.2 Recommendation Trigger

必须先由 **`BR-SHORTAGE-001`** 产生：

```
Classification = SHORTAGE
```

以及：

```
ShortageQty > 0
```

才进入本规则。

| Classification | 本规则行为 |
| --- | --- |
| `NORMAL` | **No Purchase Recommendation** |
| `BUFFER_BREACH` | **No Purchase Recommendation**（当前 POC 不自动执行 buffer replenishment） |
| `SHORTAGE` | Quantity Rule applicable |
| `DATA_INCOMPLETE` | **No Numeric Recommendation** |

对于 `DATA_INCOMPLETE`：**不得由 LLM 猜测采购数量。**

#### 2.5.3 FirstShortageDate Boundary

当前 POC 第一版对每个：

```
plant_id
+ material_code
```

在一次 shortage analysis run 中，**只依据 `FirstShortageDate`** 形成**一条**基础采购数量建议。

定义：

```
RecommendationNeedDate
  = FirstShortageDate
```

```
BasePurchaseNeed
  = ShortageQty at FirstShortageDate
```

**原因：** 当前 POC **尚未设计**完整的 **time-phased replenishment loop**。

如果对每个未来 shortage date 分别创建采购建议，却不把先前 recommendation **重新投入未来 supply calculation**，可能产生：

```
double counting
+
duplicate recommendation
```

因此当前版本**只生成**：

```
one baseline recommendation
  per plant_id + material_code
  per analysis run
```

#### 2.5.4 BasePurchaseNeed

定义：

```
BasePurchaseNeed
  = ShortageQty at FirstShortageDate
```

其中 `ShortageQty` 已由 **`BR-SHORTAGE-001`** 定义为：

```
ShortageQty
  = max(0, -ProjectedAvailable)
```

**不得重新计算 shortage。**

**不得**将 `BufferGap` 加入 `BasePurchaseNeed`。

即：

```
BasePurchaseNeed
  ≠ ShortageQty + BufferGap
```

当前 POC 的采购建议**只覆盖实际缺口**，**不自动恢复 Safety Stock buffer**。

#### 2.5.5 ApplicableMOQ Canonical Semantic

`ApplicableMOQ` 表示：

> 针对当前采购建议所适用的**最小采购数量约束**。

这是 **canonical business input**。

当前 Task **不决定**它真实来源于：

- Supplier-Material Master
- Contract
- Purchasing Info Record
- ERP proprietary field
- 其他采购主数据

真实 **source mapping** 留给后续 **Data Dictionary ＋ Adapter Design**。

#### 2.5.6 MOQ Zero vs Missing

必须**严格区分**：

```
ApplicableMOQ = 0
```

与：

```
ApplicableMOQ = missing
```

**A. `ApplicableMOQ = 0`**

表示业务**明确确认**：当前 recommendation **不存在**最小采购数量约束。

这是**合法值**。

**B. `ApplicableMOQ = missing`**

表示对于一个**已经触发 `SHORTAGE`** 的采购建议，必要的 MOQ 信息**无法可靠取得**。

**处理：** `DATA_INCOMPLETE`

**不得**：

- 默认成 0
- 猜测 MOQ
- 使用经验值
- 让 LLM 补值

#### 2.5.7 MOQ Validation

要求：

```
ApplicableMOQ >= 0
```

如果：

```
ApplicableMOQ < 0
```

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得**：

- `clamp`
- absolute value
- 自动改为 0

#### 2.5.8 RecommendedPurchaseQty

**只有在**：

```
Classification = SHORTAGE
```

**且所有必要输入可靠时**：

定义：

```
RecommendedPurchaseQty
  = max(
      BasePurchaseNeed,
      ApplicableMOQ
    )
```

同时定义：

```
MOQAdjustmentQty
  = RecommendedPurchaseQty - BasePurchaseNeed
```

要求：

```
MOQAdjustmentQty >= 0
```

#### 2.5.9 Meaning of MOQ Adjustment

必须明确：

**`MOQAdjustmentQty` 不是 `ShortageQty`。**

例如：

```
ShortageQty     = 30
ApplicableMOQ   = 100
```

则：

```
BasePurchaseNeed       = 30
RecommendedPurchaseQty = 100
MOQAdjustmentQty       = 70
```

其中：

- `30` = **实际计算缺口**
- `70` = **为满足 MOQ 而额外增加的采购数量**

**不得**将 `100` 描述为「**实际缺料 100**」。

解释必须保持：

```
business shortage
与
commercial purchasing constraint
```

**分离**。

#### 2.5.10 MOQ Does Not Mean Order Multiple

本规则中的 MOQ **只表示**：

```
Minimum Order Quantity
```

**不得**把它扩展解释为：

- pack size
- order multiple
- carton quantity
- pallet quantity
- integer rounding
- UOM conversion

因此本 Task **不定义**：

```
ceil(qty / multiple) × multiple
```

也**不定义** `round` / `ceil` / `floor` 或任何 packaging / quantity precision rule。

这些如果未来需要，**必须作为独立 Design Rule**。

#### 2.5.11 Quantity Precision Boundary

`BasePurchaseNeed` 与 `RecommendedPurchaseQty` 当前保持 **canonical quantity**。

例如：

```
BasePurchaseNeed = 10.5
ApplicableMOQ    = 8
```

则：

```
RecommendedPurchaseQty = 10.5
```

**不得自行**：

```
ceil → 11
```

除非未来有明确的 **UOM / precision / packaging rule**。

#### 2.5.12 Lead Time Boundary

`FROZEN` P0-2 要求采购建议中包含**供应周期 / Lead Time**。

但本规则当前**只定义** Purchase Recommendation Quantity。

因此：

`Lead Time` **可以**作为 recommendation 的**解释性 / planning input**，

但本 Task **不允许**用 Lead Time **偷偷修改** `RecommendedPurchaseQty`。

本 Task **不定义**：

- Order Date
- Release Date
- Expedite Date
- Late-order policy
- Dynamic Lead Time

如果 `Need Date` 与 `Lead Time` 显示正常采购**可能已经来不及**，后续**可以**形成：

```
risk / feasibility evidence
```

但**不得**在本 Task **自行改变采购数量算法**。

#### 2.5.13 Supplier Boundary

本 Task **不进行** Supplier Selection。

**不得**因为：

```
Supplier A MOQ = 50
Supplier B MOQ = 100
```

**自行选择** Supplier A。

因此：

`ApplicableMOQ` **必须**作为**已可靠确定**的 canonical input 提供给本规则。

如果 MOQ 取值**依赖尚未确定的 Supplier**，且**无法可靠确定**：

```
ApplicableMOQ = UNKNOWN / missing
```

则：

`DATA_INCOMPLETE`

**不得**让 LLM 选择 Supplier **只是为了得到一个 MOQ**。

Supplier selection / ranking 属于**其他 Design Scope**。

#### 2.5.14 Recommendation Output Semantics

采购建议至少必须能够区分：

- Material
- Plant
- `RecommendationNeedDate`
- `BasePurchaseNeed`
- `ShortageQty`
- `ApplicableMOQ`
- `MOQAdjustmentQty`
- `RecommendedPurchaseQty`

并保留以下 **P0-2 要求所需信息**的**引用能力**：

- Current Inventory
- Effective Inbound
- Lead Time
- Risk Evidence

**注意：** 本 Task **不设计最终 API / DB Schema**，这里只定义 **canonical business meaning**。

#### 2.5.15 Human-in-the-loop Boundary

`RecommendedPurchaseQty` **只是**：

```
Recommendation
```

**不是**：

```
ApprovedPurchaseQty
```

AI / Rule Engine **可以**生成 Procurement Recommendation。

AI **可以**据此生成 Procurement Request Draft。

但最终：

- 修改数量
- 批准
- 拒绝
- 正式提交

属于 **Human / Business Workflow**。

因此：

```
RecommendedPurchaseQty
  ≠ ApprovedPurchaseQty
  ≠ PurchaseOrderQty
```

#### 2.5.16 Deterministic Examples

以下为 **deterministic examples**。

**Example A — Shortage below MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 30 |
| ApplicableMOQ | 100 |

**Expected：**

- `BasePurchaseNeed = 30`
- `RecommendedPurchaseQty = 100`
- `MOQAdjustmentQty = 70`

**Example B — Shortage above MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 120 |
| ApplicableMOQ | 100 |

**Expected：**

- `BasePurchaseNeed = 120`
- `RecommendedPurchaseQty = 120`
- `MOQAdjustmentQty = 0`

**Example C — Explicit no MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 40 |
| ApplicableMOQ | 0 |

**Expected：**

- `RecommendedPurchaseQty = 40`
- `MOQAdjustmentQty = 0`

**Example D — Missing MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 40 |
| ApplicableMOQ | missing |

**Expected：**

- `DATA_INCOMPLETE`
- **No Numeric Recommendation**
- **不得默认 MOQ = 0**

**Example E — BUFFER_BREACH**

| 字段 | 值 |
| --- | --- |
| Classification | `BUFFER_BREACH` |
| ShortageQty | 0 |
| BufferGap | 20 |
| ApplicableMOQ | 100 |

**Expected：**

- **No Purchase Recommendation**

**不得**生成 `RecommendedPurchaseQty = 100`。

**不得**为了恢复 Safety Stock **自动创建采购建议**。

**Example F — NORMAL**

| 字段 | 值 |
| --- | --- |
| Classification | `NORMAL` |

**Expected：**

- **No Purchase Recommendation**

**Example G — DATA_INCOMPLETE**

| 字段 | 值 |
| --- | --- |
| Classification | `DATA_INCOMPLETE` |

**Expected：**

- **No Numeric Recommendation**

**Example H — First shortage only**

| 字段 | 值 |
| --- | --- |
| `FirstShortageDate` | `2026-10-10` |
| ShortageQty at `2026-10-10` | 30 |
| Later projected shortage at `2026-10-20` | 80 |
| ApplicableMOQ | 50 |

**Expected for current POC：**

- `BasePurchaseNeed = 30`
- `RecommendedPurchaseQty = 50`
- `RecommendationNeedDate = 2026-10-10`

**不得**在同一次分析中自动再生成第二条 `2026-10-20` recommendation。

**原因：** 完整 **time-phased replenishment loop** 尚未设计。

#### 2.5.17 AI Boundary

**数量规则必须由 deterministic logic 决定。**

LLM **不可以**：

- 猜 `ShortageQty`
- 猜 MOQ
- 把 `BUFFER_BREACH` 当 `SHORTAGE`
- 为了满足 MOQ 自行选择 Supplier
- 自行 round quantity
- 自行创建第二个未来采购建议
- 将 `MOQAdjustmentQty` 描述成真实缺口
- 自动批准 `RecommendedPurchaseQty`

LLM **可以**解释：

- 为什么建议采购
- `ShortageQty` 是多少
- MOQ 为什么放大了数量
- `MOQAdjustmentQty` 是多少
- 为什么没有生成采购建议
- 为什么返回 `DATA_INCOMPLETE`

#### 2.5.18 Integration with Existing Rules

本规则**必须引用** `BR-SHORTAGE-001`，而**不是重新定义**：

- `ProjectedAvailable`
- `ShortageQty`
- `FirstShortageDate`
- `Classification`

输入关系：

```
BR-SHORTAGE-001
        ↓
Classification
ShortageQty
FirstShortageDate
        ↓
BR-PROCUREMENT-001
        ↓
RecommendedPurchaseQty
```

**不得修改**以下规则的业务定义：

- `BR-INVENTORY-001`
- `BR-INBOUND-001`
- `BR-SUBSTITUTE-001`
- `BR-REQUIREMENT-001`

### 2.6 Effective Inbound

**Rule ID:** `BR-INBOUND-001`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。
>
> **本规则没有独立 `VB` 编号。** 它是 `POC Design v0.2` 中已经明确登记的设计项。**不得为了方便自行创建新的 `VB` ID。**

#### 2.6.1 Business Definition

**不是所有"未收货采购订单"都可以计入 `ProjectedAvailable` 的未来 Supply。**

某笔 inbound 只有**同时满足**以下四项：

1. PO / inbound status eligible
2. 存在正数 `RemainingInboundQty`
3. `effective_arrival_date` 可可靠取得
4. `effective_arrival_date <= required_date`

才可以计入：`CumulativeEffectiveInbound(<= required_date)`

#### 2.6.2 RemainingInboundQty

定义：

```
RemainingInboundQty = ordered_qty - received_qty
```

要求：

```
ordered_qty  >= 0
received_qty >= 0
RemainingInboundQty >= 0
```

如果：

```
received_qty > ordered_qty
```

**不得**：

- `clamp`
- 自动改成 0
- 猜测业务含义

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

#### 2.6.3 PO / Inbound Status Eligibility

当前 POC 使用以下**保守分类**：

**A. `OPEN`**

**Eligible: YES**

前提：`RemainingInboundQty > 0` 且 arrival date 满足 `required_date` 边界。

**B. `CONFIRMED`**

**Eligible: YES**

前提同上。

**C. `PARTIALLY_RECEIVED`**

**Eligible: YES**

但**只计入** `RemainingInboundQty`。

**不得再次计入已 received 的数量。**

**D. `CANCELLED`**

**Eligible: NO**

不得计入未来供给。

**E. `CLOSED` / `COMPLETED`**

**Eligible: NO**

作为未来 inbound **不再计入**。

**原因：** 如果已收货，其结果应体现在 **Inventory**，而不是继续作为未来 Supply **重复计算**。

**F. Unknown / Invalid Status**

**不得猜测。**

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

#### 2.6.4 `effective_arrival_date`

定义：

`effective_arrival_date` 是 POC 中用于判断：

> "该 inbound 是否能够在某 Required Date 前成为有效供给"

的**标准化业务日期**。

**当前只定义其业务语义。**

**不得在本 Task 决定**它具体来自：

- `promised_date`
- `confirmed_date`
- `planned_delivery_date`
- `ETA`
- ERP proprietary field

具体 **source-field mapping** 留给后续：**Data Dictionary ＋ Adapter Contract**。

#### 2.6.5 Date Boundary

对于 Required Date = `t`：

只有 `effective_arrival_date <= t` 的 **eligible** inbound 可以进入 `CumulativeEffectiveInbound(<= t)`。

如果 `effective_arrival_date > t`，则**不得计入该日期的 Supply**。

> 它可以在**更晚的 required_date 重新参与累计计算**。

如果 `effective_arrival_date` **missing / invalid**，则：**`DATA_INCOMPLETE`**。

**不得假设为** `today`、`required_date`、`PO creation date` 或**任何默认日期**。

#### 2.6.6 Deterministic Formula

```
EffectiveInboundQty(i, t) = RemainingInboundQty(i)
  only if status(i) is eligible
     AND effective_arrival_date(i) <= t
```

否则：

```
EffectiveInboundQty(i, t) = 0
```

随后：

```
CumulativeEffectiveInbound(<= t) = Σ EffectiveInboundQty(i, t)
```

**按以下粒度，与 `BR-SHORTAGE-001` 的计算粒度对齐：**

```
plant_id
+ material_code
+ required_date
```

#### 2.6.7 Plant / Material Boundary

Inbound **必须**能够可靠映射到：

```
plant_id
+ material_code
```

**不得**：

- 自动跨 Plant 使用 PO
- 将无法映射的 PO 归入当前 material
- 让 LLM 猜测 PO 对应哪个物料或 Plant

如果映射失败：`DATA_INCOMPLETE` ＋ **Data Quality Issue**。

#### 2.6.8 No Double Counting

必须防止**两类** double counting：

**A. Received quantity double counting**

已收货数量**不得同时存在于** `Inventory` ＋ `Future Inbound`。

因此：`PARTIALLY_RECEIVED` **只使用** `RemainingInboundQty`。

**B. `CLOSED` / `COMPLETED` double counting**

已完成 PO **不得继续作为未来 inbound 计入**。

#### 2.6.9 Acceptance Examples

以下为 **deterministic examples**。

**Example A — Eligible `OPEN` PO**

| 字段 | 值 |
| --- | --- |
| Required Date | `2026-10-15` |
| status | `OPEN` |
| ordered_qty | 100 |
| received_qty | 0 |
| effective_arrival_date | `2026-10-12` |

**Expected：**

- `RemainingInboundQty = 100`
- `EffectiveInboundQty(<= 2026-10-15) = 100`

**Example B — Arrival after requirement**

| 字段 | 值 |
| --- | --- |
| Required Date | `2026-10-15` |
| status | `CONFIRMED` |
| ordered_qty | 80 |
| received_qty | 0 |
| effective_arrival_date | `2026-10-20` |

**Expected：** `EffectiveInboundQty(<= 2026-10-15) = 0`

> 该 PO **可在更晚 required_date 重新参与计算**。

**Example C — Partial receipt**

| 字段 | 值 |
| --- | --- |
| status | `PARTIALLY_RECEIVED` |
| ordered_qty | 100 |
| received_qty | 40 |
| effective_arrival_date | `<= required_date` |

**Expected：**

- `RemainingInboundQty = 60`
- `EffectiveInboundQty = 60`

**不得计入 100。**

**Example D — Cancelled**

| 字段 | 值 |
| --- | --- |
| status | `CANCELLED` |
| ordered_qty | 100 |
| received_qty | 0 |
| effective_arrival_date | `<= required_date` |

**Expected：** `EffectiveInboundQty = 0`

**Example E — Missing arrival date**

| 字段 | 值 |
| --- | --- |
| status | `OPEN` |
| ordered_qty | 100 |
| received_qty | 0 |
| effective_arrival_date | `missing` |

**Expected：** `DATA_INCOMPLETE`

**不得自行给默认日期。**

**Example F — Invalid quantity**

`ordered_qty = 100`，`received_qty = 120`

**Expected：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得**：`RemainingInboundQty = -20` 然后继续参与计算。

**Example G — Cumulative inbound**

Required dates：`2026-10-10`、`2026-10-20`

| PO | Remaining | arrival |
| --- | --- | --- |
| PO-001 | 50 | `2026-10-08` |
| PO-002 | 80 | `2026-10-15` |

**Expected：**

- `CumulativeEffectiveInbound(<= 2026-10-10) = 50`
- `CumulativeEffectiveInbound(<= 2026-10-20) = 130`

#### 2.6.10 AI Boundary

**Inbound eligibility 与 quantity 必须由 deterministic logic 决定。**

LLM **不可以**：

- 把 `CANCELLED` PO 当供给
- 猜 arrival date
- 猜 PO status
- 修改 `received_qty`
- 修改 `ordered_qty`
- 跨 Plant 借用 inbound
- 决定 source ERP 字段映射

LLM **可以**解释：

- 哪些 inbound 被计入
- 哪些被排除
- 为什么某 PO 晚于 `required_date`
- 为什么返回 `DATA_INCOMPLETE`

#### 2.6.11 Source-field Boundary

**本规则定义 business semantic，而不是 source schema。**

因此**不得创建**：

- ERP field mapping
- API Contract
- database column definition
- adapter implementation

例如 `effective_arrival_date` **只是 canonical business meaning**。

其 **source mapping** 进入后续 **Data Dictionary / Adapter Design**。

> 相关背景（属 FROZEN baseline，不重新解释）：`FROZEN` Discovery Brief §20 已将该口径划归 `POC Design v0.2`；`FROZEN` Discovery Validation v0.1 已在 `VR-005` 中确认 Purchase Order / Inbound 数据可得，但明确"**不得**在本阶段定义「有效在途」的最终业务算法"。

### 2.7 Supplier Risk / Evidence

**Rule ID:** `BR-SUPPLIER-RISK-001`

**Backlog:** `VB-27`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

**Validation Source:** `SC-RISK-001` / Human-approved `SIMULATED` design evidence

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED` **≠** `FROZEN` Discovery `H3` resolved。

> 关联的 FROZEN 原问题：风险判断是否依赖个人经验？（`HYPOTHESIS` / `TBD`；关联 `G-06`、`G-11`）

#### 2.7.0 Design Evidence Record — SC-RISK-001

| 字段 | 内容 |
| --- | --- |
| Scenario | `SC-RISK-001` — Supplier Risk Judgment |
| Evidence Type | `SIMULATED` |
| Evidence Source | Human-approved |
| Role | Simulated Procurement / Supply Chain Owner |
| Purpose | support design of deterministic Supplier Risk Evidence |

**必须声明**：该 Scenario

- **不是**云南 CY 集团真实供应商事实；
- **不是** `PUBLIC FACT`；
- **不是**对真实企业风险流程的确认；
- **不修改** `FROZEN` `H3` status；
- **只**作为模拟 POC 的 **downstream design input**。

**场景内容**：两个物料均 `ShortageQty = 50`，`RecommendationNeedDate` 距当前分析日 **20 days**。

```
Supplier A:
  StandardLeadTimeDays   = 10
  DeliveryPerformance    = 97%
  QualityPerformance     = 99%

Supplier B:
  StandardLeadTimeDays   = 35
  DeliveryPerformance    = 84%
  QualityPerformance     = 94%
```

**Human-approved simulated business judgment：** 虽然 `ShortageQty` 相同，两者业务风险**不应被视为相同**。Supplier B 因

- `Standard Lead Time` **超过剩余需求时间**；
- `Delivery Performance` **较差**；
- `Quality Performance` **较差**；

**需要更高关注**。

**POC 目标：** 将此类经验判断拆成

```
deterministic risk evidence
+
transparent policy
+
AI explanation
```

**不得让 LLM 自行生成风险事实。**

#### 2.7.1 Rule Purpose

本规则回答：

> 对于一个 `supplier_id` + `material_code`，当前已知的供应商事实，可以形成哪些 **deterministic ＋ explainable Risk Evidence**。

本规则**不得**回答：

> 「应该选择哪个 Supplier？」

**不得**进行：

- Supplier Ranking
- Automatic Supplier Selection

#### 2.7.2 Risk Evaluation Grain

风险评估**至少**按：

```
supplier_id
+ material_code
```

执行。

当 `Plant` context 对业务含义必要时，保留 `plant_id` 作为 **evaluation context**。

**不得**把多个 Supplier 的数据**合并成一个共同风险值**。

每个 Supplier **必须独立**形成自己的 **Supplier Risk Evidence Card**。

#### 2.7.3 Input Baseline

继承 `VR-006` 已确认可得的 **conceptual data**：

- `supplier_id`
- `material_code`
- `standard_lead_time_days`
- `delivery_performance`
- `quality_performance`
- `period`
- `updated_at`

并使用：

```
RecommendationNeedDate
```

作为 **Lead Time Feasibility** 的需求时间基准。

**必须保留 `period`** —— **不得只记录 performance value 而丢失 measurement period**。

因此：

```
delivery_performance
与
quality_performance
```

**必须对应一个可可靠识别的**：

```
PerformancePeriod
```

**不得自行定义真实**：

- ERP / SRM schema
- field mapping
- API contract

这些属于后续 **Data Dictionary / Adapter Design**。

> `period` 的完整性要求见 **§2.7.23 Performance Period Context**。
> Supplier-Material relationship eligibility 要求见 **§2.7.24 Supplier-Material Relationship Eligibility**。

#### 2.7.4 DaysUntilNeed

定义：

```
DaysUntilNeed
  = RecommendationNeedDate
  - AnalysisDate
```

要求：

```
DaysUntilNeed >= 0
```

如果出现以下任一情况：

- `RecommendationNeedDate` missing / invalid
- `AnalysisDate` missing / invalid
- `DaysUntilNeed < 0`

则：

```
LeadTimeRisk = DATA_INCOMPLETE
```

**不得自行猜日期。**

#### 2.7.5 Lead Time Feasibility Risk

第一版 **`SIMULATED` POC Policy**：

如果：

```
StandardLeadTimeDays > DaysUntilNeed
```

则：

```
LeadTimeRisk = HIGH
```

如果：

```
StandardLeadTimeDays <= DaysUntilNeed
```

则：

```
LeadTimeRisk = LOW
```

**注意：** 本版本**不定义** `MEDIUM` Lead Time Risk。**不得自行增加** buffer / grace period。

例如：

| DaysUntilNeed | StandardLeadTimeDays | Expected |
| --- | --- | --- |
| 20 | 35 | `LeadTimeRisk = HIGH` |
| 20 | 10 | `LeadTimeRisk = LOW` |

#### 2.7.6 Delivery Performance Risk

以下 threshold 是 **Human-approved `SIMULATED` POC policy**，**不是**真实 CY 企业 threshold。

```
DeliveryPerformance >= 95%                → LOW
90% <= DeliveryPerformance < 95%          → MEDIUM
DeliveryPerformance < 90%                 → HIGH
```

要求输入能够被**规范化**为 `0–100%` 或等价 canonical percentage。

本 Task **不设计** source-field normalization implementation。

#### 2.7.7 Quality Performance Risk

同样属于 **Human-approved `SIMULATED` POC policy**。

```
QualityPerformance >= 98%                 → LOW
95% <= QualityPerformance < 98%           → MEDIUM
QualityPerformance < 95%                  → HIGH
```

#### 2.7.8 OverallSupplierRisk

当前 POC **不使用 weighted score**。

**不得设计**：

```
0.4 × Lead Time
+ 0.35 × Delivery
+ 0.25 × Quality
```

或**任何未经验证的权重**。

定义：

```
OverallSupplierRisk
  = max severity
    of all reliable required dimensions
```

**Severity order：**

```
LOW < MEDIUM < HIGH
```

例如：

```
LeadTimeRisk = LOW
DeliveryRisk = MEDIUM
QualityRisk  = LOW
```

则：

```
OverallSupplierRisk = MEDIUM
```

例如：

```
LeadTimeRisk = HIGH
DeliveryRisk = LOW
QualityRisk  = LOW
```

则：

```
OverallSupplierRisk = HIGH
```

#### 2.7.9 Complete-data Requirement

第一版 POC **只有在三个维度**：

- `LeadTimeRisk`
- `DeliveryRisk`
- `QualityRisk`

**都能够可靠判定时**，才输出：

```
OverallSupplierRisk = LOW / MEDIUM / HIGH
```

如果**任一** required dimension：

- missing
- invalid
- unresolved

则：

```
OverallSupplierRisk = DATA_INCOMPLETE
```

**但**：已可靠取得的 **individual Risk Evidence 仍允许展示**。

**不得因为一项缺失而丢弃其他可靠事实。**

#### 2.7.10 Zero / Valid Extreme vs Missing

必须区分：

```
真实合法极值
```

与：

```
missing
```

例如：

```
DeliveryPerformance = 0%
```

如果数据**被可靠确认**，这是**合法但极差**的 performance：

```
DeliveryRisk = HIGH
```

而：

```
DeliveryPerformance = missing
```

表示**无法判断**：

```
DeliveryRisk = DATA_INCOMPLETE
```

`QualityPerformance` **同理**。

**不得将 missing 默认成 0。**

#### 2.7.11 Risk Evidence Card

每个 `supplier_id` + `material_code` 形成**独立 Risk Evidence Card**。

至少包含以下 **canonical meaning**：

- `supplier_id`
- `material_code`
- `RecommendationNeedDate`
- `AnalysisDate`
- `DaysUntilNeed`
- `StandardLeadTimeDays`
- `LeadTimeRisk`
- `PerformancePeriod`
- `PerformanceUpdatedAt`
- `DeliveryPerformance`
- `DeliveryRisk`
- `QualityPerformance`
- `QualityRisk`
- `OverallSupplierRisk`
- Evidence Status / completeness

本 Task **不定义**：

- API Schema
- DB Schema
- JSON format
- UI layout

这里**只定义业务语义**。

#### 2.7.12 Evidence Explainability

Risk Evidence **必须能够解释**：

> 为什么得到该 Risk Level。

例如：

```
OverallSupplierRisk = HIGH
```

**Evidence：**

- Need in 20 days
- Standard Lead Time = 35 days
- Lead Time gap = 15 days
- `LeadTimeRisk = HIGH`
- Delivery Performance = 84%
- `DeliveryRisk = HIGH`
- Quality Performance = 94%
- `QualityRisk = HIGH`

**不得只输出** `HIGH` 而**没有 evidence**。

#### 2.7.13 Deterministic Examples

以下为 **deterministic examples**（对应 `SC-RISK-001`）。

**Example A — Supplier A**

| 字段 | 值 |
| --- | --- |
| `DaysUntilNeed` | 20 |
| `StandardLeadTimeDays` | 10 |
| `DeliveryPerformance` | 97% |
| `QualityPerformance` | 99% |

**Expected：**

- `LeadTimeRisk = LOW`
- `DeliveryRisk = LOW`
- `QualityRisk = LOW`
- `OverallSupplierRisk = LOW`

**Example B — Supplier B**

| 字段 | 值 |
| --- | --- |
| `DaysUntilNeed` | 20 |
| `StandardLeadTimeDays` | 35 |
| `DeliveryPerformance` | 84% |
| `QualityPerformance` | 94% |

**Expected：**

- `LeadTimeRisk = HIGH`
- `DeliveryRisk = HIGH`
- `QualityRisk = HIGH`
- `OverallSupplierRisk = HIGH`

**注意：** 这两个结果**只表示**：

```
两张独立 Supplier Risk Evidence Cards
```

**不得自动输出**：

```
Supplier A should be selected
```

或：

```
Supplier A ranks #1
```

**Example C — Performance period missing**

| 字段 | 值 |
| --- | --- |
| `supplier_id` | `SUP-A` |
| `material_code` | `MAT-A` |
| `DeliveryPerformance` | 97% |
| `QualityPerformance` | 99% |
| `period` | missing |

**Expected：**

- `DeliveryRisk = DATA_INCOMPLETE`
- `QualityRisk = DATA_INCOMPLETE`
- `OverallSupplierRisk = DATA_INCOMPLETE`

**不得**因为 `97%` / `99%` 数值看起来很好就输出 `LOW`。

**Example D — Relationship unresolved**

Supplier exists；Material exists；但 **Supplier-Material Relationship 无法可靠确认**。

**Expected：**

- Risk Evidence Status = `DATA_INCOMPLETE`

**不得自动**把该 Supplier 视为此 Material 的候选供应商。

#### 2.7.14 Boundary with Supplier Selection

即使同一个 Material 存在多个 Supplier：

```
Supplier A → LOW
Supplier B → HIGH
```

系统当前**只能展示**：

- `Supplier A` Risk Evidence
- `Supplier B` Risk Evidence

**不得自动**：

- 排名
- 推荐 Winner
- 自动选择 Supplier
- 自动把 LOW Risk Supplier 绑定进采购建议
- 根据 Risk 修改 `RecommendedPurchaseQty`

Supplier comparison / ranking / advanced supplier intelligence **保持在**：

```
P1 / Future scope
```

除非后续**单独 Human-approved Design Change**。

#### 2.7.15 Boundary with Procurement Quantity

`BR-SUPPLIER-RISK-001` **不得改变** `BR-PROCUREMENT-001` 的 `RecommendedPurchaseQty`。

例如：

```
SupplierRisk = HIGH
```

**不得自动**：

- 增加采购数量
- 减少采购数量
- 拆单
- 改 MOQ
- 选备用供应商

`Risk Evidence` 是**决策支持输入**，**不是采购数量算法的一部分**。

#### 2.7.16 Missing / Invalid Input Fail-safe

以下情况应明确处理：

| 输入情况 | 对应维度 |
| --- | --- |
| `supplier_id` unresolved | `DATA_INCOMPLETE` |
| `material_code` unresolved | `DATA_INCOMPLETE` |
| `RecommendationNeedDate` missing / invalid | `LeadTimeRisk = DATA_INCOMPLETE` |
| `AnalysisDate` missing / invalid | `LeadTimeRisk = DATA_INCOMPLETE` |
| `StandardLeadTimeDays` missing / invalid | `LeadTimeRisk = DATA_INCOMPLETE` |
| `StandardLeadTimeDays < 0` | `LeadTimeRisk = DATA_INCOMPLETE` |
| `DeliveryPerformance` missing / invalid | `DeliveryRisk = DATA_INCOMPLETE` |
| `DeliveryPerformance < 0%` | `DeliveryRisk = DATA_INCOMPLETE` |
| `DeliveryPerformance > 100%` | `DeliveryRisk = DATA_INCOMPLETE` |
| `QualityPerformance` missing / invalid | `QualityRisk = DATA_INCOMPLETE` |
| `QualityPerformance < 0%` | `QualityRisk = DATA_INCOMPLETE` |
| `QualityPerformance > 100%` | `QualityRisk = DATA_INCOMPLETE` |
| `period` missing / invalid（而 performance value 存在） | `DeliveryRisk` / `QualityRisk` = `DATA_INCOMPLETE` |
| Supplier-Material Relationship 无法可靠确定 | Risk Evidence Status = `DATA_INCOMPLETE` |

`OverallSupplierRisk`：**`DATA_INCOMPLETE`**

**不得**：

- 猜测
- `clamp`
- 默认 `LOW`
- 默认 0
- 默认 100
- 让 LLM 补值

#### 2.7.17 Deterministic Logic Boundary

以下**必须由 deterministic logic 产生**：

- `DaysUntilNeed`
- `LeadTimeRisk`
- `DeliveryRisk`
- `QualityRisk`
- `OverallSupplierRisk`
- Evidence completeness

**LLM 不参与 risk classification。**

#### 2.7.18 AI Boundary

LLM **可以**：

- 解释为何风险是 `LOW` / `MEDIUM` / `HIGH`
- 将结构化 Risk Evidence 转成自然语言
- 说明哪些输入缺失
- 说明为什么 `OverallSupplierRisk = DATA_INCOMPLETE`
- 对比用户**明确指定**的两个 Risk Evidence Cards 的事实差异

LLM **不可以**：

- 猜 performance
- 猜 lead time
- 修改 thresholds
- 创建新的 threshold
- 自行生成权重
- 自动 Supplier Ranking
- 自动 Supplier Selection
- 把 simulated threshold 说成真实企业规则
- 把 Risk Level 当成事实来源

#### 2.7.19 Threshold Governance

必须明确：以下 thresholds

```
Delivery:  95 / 90
Quality:   98 / 95
```

是 **Human-approved `SIMULATED` POC policy**。

**不是**：

- `PUBLIC FACT`
- 真实客户政策
- 行业标准

未来如果改变 thresholds，属于 **Business Rule Change**，**必须**：

```
Human Approval
+
versioned / traceable change
```

**不得由 Agent / LLM 自行调整。**

#### 2.7.20 H3 / Validation Relationship

必须明确记录：`SC-RISK-001` 为 **Human-approved `SIMULATED` downstream design evidence**。

它支持：

> 「存在将经验型风险判断结构化为 deterministic risk evidence 的设计价值」

**但**：`FROZEN` Discovery Validation v0.1 中

```
H3 = TBD
```

**保持不变。**

**不得在本文件声称**：`FROZEN` `H3` 已被正式修改为 `PARTIALLY CONFIRMED`。

**可以记录**：如果未来 Human 决定正式更新 `H3` validation status，应通过：

```
新的 Validation Version / Addendum
```

完成。

> 即：本 Task **不修改** `FROZEN` Validation，**不把本 Task 的设计规则倒写成历史 Discovery 事实**。

#### 2.7.21 G-06 / G-11 Relationship

继承 `FROZEN` source：

```
G-06 = 部分 RESOLVED
G-11 = 部分 RESOLVED
```

本 Task **不修改 `FROZEN` 文档**。

设计层完成后，**可以**说明：`VB-27` 的 **Design Gap 已解决**。

但**不得**写成：`FROZEN` Discovery 中的 `G-06` / `G-11` 已经被回写成 `RESOLVED`。

保持以下**两个层级分离**：

```
Validation baseline
与
Design resolution
```

#### 2.7.22 Source-field Boundary

**本规则定义 business semantic，而不是 source schema。**

因此**不得创建**：

- ERP / SRM field mapping
- API Contract
- database column definition
- adapter implementation
- risk engine implementation
- ranking engine

例如 `delivery_performance`、`quality_performance`、`standard_lead_time_days`
**只是 canonical business meaning**。

其 **source mapping** 进入后续 **Data Dictionary / Adapter Design**。

#### 2.7.23 Performance Period Context

`VR-006` 的 Supplier Performance baseline 中已存在：

- `supplier_id`
- `period`
- `delivery_performance`
- `quality_performance`
- `updated_at`

因此 `delivery_performance` 与 `quality_performance` **必须对应一个可可靠识别的**：

```
PerformancePeriod
```

**它可能代表某个明确的统计窗口，但本 Task 不决定**：

- 30 days
- 90 days
- 12 months
- rolling window
- fiscal period

这些真实 **period policy** 留给后续 **Data Mapping / Business Rule refinement**。

**本 Task 不得自行发明固定统计周期。**

**Performance Evidence Completeness**

如果：

```
delivery_performance 有值
但对应 period 无法可靠确定
```

则：

```
DeliveryRisk = DATA_INCOMPLETE
```

如果：

```
quality_performance 有值
但对应 period 无法可靠确定
```

则：

```
QualityRisk = DATA_INCOMPLETE
```

**不得**把：

```
"97% but period unknown"
```

视为**完整可靠**的 Risk Evidence。

`updated_at` **不能替代** performance measurement period。

> 本 Task **不定义** performance freshness threshold / maximum age / rolling window。
> 这些仍属于后续 Design。

#### 2.7.24 Supplier-Material Relationship Eligibility

`VR-006` 已存在：

```
Supplier-Material Relationship
```

以及：

```
sourcing_status
```

因此补充一个 **eligibility boundary**：

Risk Evidence 的业务上下文**必须能够确认** `supplier_id` 与 `material_code` **存在可可靠识别的
Supplier-Material Relationship**。

**不得**因为 Supplier Master 中存在某 Supplier，就**自动认为**其可以供应任意 Material。

`sourcing_status` 用于判断该 relationship 是否属于**当前可评估的 candidate relationship**。

本 Task **不定义**具体 `sourcing_status` enum / vocabulary。

**不得自行发明** `APPROVED` / `ACTIVE` / `QUALIFIED` 等真实 source status。

只定义：如果 **relationship eligibility 无法可靠确定**：

```
Risk Evidence Status = DATA_INCOMPLETE
```

**不得由 LLM 猜测供应资格。**

**Important Boundary**

Relationship eligibility：

```
≠ Supplier Ranking
≠ Supplier Selection
≠ Supplier Recommendation
```

它**只回答**：

> 「这个 supplier-material relationship 是否具有足够可靠的业务上下文进入 Risk Evidence evaluation。」

即使**两个 relationship 都 eligible**：

```
Supplier A = LOW
Supplier B = HIGH
```

仍然：

- **不得自动排名**
- **不得自动选择**
- **不得绑定到采购建议**

> 本 Task **不定义** supplier qualification workflow。
> 这些仍属于后续 Design。

---

## 3. System Boundary

**Backlog:** `VB-29`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

**Validation Source:** `VR-007` / `SC-INT-001`（`FROZEN`，Human-approved `SIMULATED`）＋ `VB-29` Human Approval

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。
>
> 本节只定义 **conceptual boundary**；**不选择**技术组件 / deployment / API Gateway / database / framework。

**待说明项状态：**

| 待说明项 | Status |
| --- | --- |
| POC responsibility | **`DESIGN RESOLVED`** |
| external system boundary | **`DESIGN RESOLVED`** |
| write boundary | **`DESIGN RESOLVED`** |
| failure boundary | **`DESIGN RESOLVED`** |

> 继承约束（不重新定义）：Source-system write = `DENIED`；Production write-back = `OUT OF SCOPE`（见 §5 Design Principles → Integration）。

**VB-29 Design Decision：**

```
VB-29 = DESIGN RESOLVED

POC 可以且应采用：
  Read-only source integration
  +
  Draft-only business action

无需 Production system write permission。
```

> `YES` = **当前模拟 POC 的 Design Decision**，**不代表**真实 CY 生产系统已经验证。

#### 3.1 Source Baseline（FROZEN Reference）

引用 `FROZEN` Discovery Validation：**`VR-007`** / **`SC-INT-001`**。

其中已确认：

```
Integration Pattern = Controlled Export / Snapshot
```

**Source System Boundary：**

| 操作 | 边界 |
| --- | --- |
| `READ` | **allowed only through controlled exported snapshot** |
| `WRITE` | **`DENIED`** |

```
Production Write-back = OUT OF SCOPE
```

> **不得修改 `FROZEN` source。** 本节只引用其已确认结论，**不重新解释、不扩大**。

#### 3.2 POC Responsibility

POC **负责**：

- 只读地获取**已导出的**业务数据快照；
- 运行 deterministic business rules（§2）；
- 生成 **Explanation / Recommendation / Draft**（§5）；
- 支持 Human Review / Modify / Approve / Reject（**POC 内部**）。

POC **不负责**：

- 写入任何 source system；
- 执行正式业务动作；
- 替代企业系统的记录职责。

#### 3.3 External System Boundary

POC **不直接读取 Production DB**。

POC business data **只能**通过以下链路进入 POC：

```
Simulated Enterprise Sources
      ↓
Controlled Export
      ↓
POC Data Landing Zone
```

Agent / LLM **不得**：

- direct Production DB access
- free-form SQL to Production
- bypass Controlled Export
- 扩大 source access

#### 3.4 Read Boundary

**POC 不直接读取 Production DB。**

读取**只能**通过 **Controlled Export / Snapshot** 产物（`POC Data Landing Zone`）进行。

**不得**：

- 假设存在真实 Production API 或 direct DB access；
- 绕过 Controlled Export 直连源系统；
- 以「只读」为由扩大 source access 范围。

#### 3.5 Write Boundary

**Source-system write：**

```
DENIED
```

POC **不允许**：

- 修改 Inventory
- 修改 Production Plan
- 修改 Purchase Order
- 修改 Supplier Master
- 修改 BOM
- 创建真实 Purchase Requisition
- 创建真实 Purchase Order
- 调用 Production write API
- 直接写 ERP / WMS / PLM

#### 3.6 Draft Boundary

AI Copilot **可以**生成：

```
Procurement Request Draft
```

Draft **只存在**于：

```
POC / Draft Boundary
```

必须明确：

```
POC Draft
  ≠ ERP Purchase Request
  ≠ Purchase Order
```

Draft **不产生**真实业务系统副作用。

#### 3.7 Human Approval Boundary

Human **可以**在 POC 中：

- Review
- Modify
- Approve
- Reject

但必须明确：

```
Human Approval
  ≠ Production Execution
```

Human 在 POC 中 Approve 后：**允许**状态变为：

```
APPROVED
```

但**不得**因此：

- 自动写入 ERP
- 自动创建 PO
- 自动提交 Production workflow

真实业务执行仍：

```
OUTSIDE POC WRITE BOUNDARY
```

#### 3.8 POC State vs Enterprise State

必须区分：

```
POC internal state
与
Enterprise source-system state
```

例如：

```
POC Draft = APPROVED
```

**不意味着**：

```
ERP Purchase Request exists
```

也**不意味着**：

```
Purchase Order created
```

**不得**将 POC 状态变化描述为**企业系统写入成功**。

#### 3.9 Effective Permission Boundary

继承：

```
AI Effective Permission
  = User Permission
  ∩ Data Scope
  ∩ Tool Permission
  ∩ Workflow State
  ∩ POC Policy
```

即使 Human 本人拥有真实业务系统写权限：

```
Human Capability
  可以高于
Agent Capability
```

Agent **仍不得**获得 Production write capability。

#### 3.10 Failure / Safety Boundary

如果：

- Controlled Snapshot unavailable
- Data Landing Zone unavailable
- required Tool unavailable

则：**POC 应 fail closed。**

**不得**：

- 切换成 Production direct access
- 尝试 Production DB
- 尝试 write API
- 让 LLM 使用旧数据**伪装当前事实**

**只允许**：

- 报告 unavailable
- `DATA_INCOMPLETE`
- Tool failure

#### 3.11 Integration with §5 AI / Tool Boundary

保持：

```
LLM does not create business truth
```

以及：

```
Data Source
      ↓
Deterministic Data Tool
      ↓
Structured Result
      ↓
LLM
```

`VB-29` **不改变** §5 AI / Tool Boundary。

#### 3.12 Integration with §6 HITL Workflow

本 Task **只为未来 §6 建立硬边界**：

- Draft
- Review
- Modify
- Approve
- Reject

**都可以存在**于 POC 内。

但：

```
execution boundary = OUTSIDE POC
```

**不得本轮设计完整 HITL state machine。**

#### 3.13 Acceptance Examples

以下为 **conceptual examples**。

**Example A — Generate Draft**

AI generates Procurement Request Draft.

**Expected：**

- POC Draft created
- ERP / source system：**`UNCHANGED`**

**Example B — Human Approves**

Human approves POC Draft.

**Expected：**

- POC workflow state：`APPROVED`
- Production ERP：**`UNCHANGED`**
- **不得**自动创建 Purchase Order

**Example C — User asks AI to submit**

User：「直接帮我下单。」

**Expected：**

- AI **不执行** Production write
- **可以**说明：正式业务执行**超出当前 POC write boundary**

**Example D — Snapshot unavailable**

Controlled Snapshot unavailable.

**Expected：**

- **fail closed**
- **不得**切换到 direct DB / Production API
- **不得**使用旧 conversation data **伪装成当前企业事实**

**Example E — Human has production authority**

Human user 本身拥有 Production write 权限。

**Expected：**

- Agent Capability **仍受 POC Policy 限制**
- Agent **不因此**获得 Production write capability

#### 3.14 Status Boundary

本节 `DESIGN RESOLVED` **只代表**：

```
conceptual boundary 已定义
```

**不代表**：

- 真实 ERP write integration 已设计
- Adapter / Connector 已实现
- 技术组件 / deployment / API Gateway / database / framework 已选择
- tested / production-ready

> 本 Task **不得设计真实 ERP write integration**。

---

## 4. Data & Integration Design

> 本章节建立 POC 的 Data & Integration Design。**不得创建实际 Schema / Contract。**

| 子章节 | Status |
| --- | --- |
| [Canonical Data Model](specs/data-integration/canonical-data-model.md) | **`DESIGN RESOLVED`** |
| [Data Dictionary](specs/data-integration/data-dictionary.md) | **`DESIGN RESOLVED`** |
| [Snapshot / Import Contract](specs/data-integration/snapshot-import-contract.md) | **`DESIGN RESOLVED`** |
| [Data Validation](specs/data-integration/data-validation.md) | **`DESIGN RESOLVED`** |
| [Master Data Mapping](specs/data-integration/master-data-mapping.md) | **`DESIGN RESOLVED`** |
| [Adapter Boundary](specs/data-integration/adapter-boundary.md) | **`DESIGN RESOLVED`**（Closure Validation 见 **§4.6.21**；Design Review 见 **§4.6**） |

> 继承约束（不重新定义）：Integration Pattern = **Controlled Export / Snapshot**。
> 具体文件格式 = **JSON**（**`Serialization Format` = `DESIGN RESOLVED`**，见 **§4.3.22**）；
> **`Adapter Boundary`** 已由 **Issue #90 Closure Validation = `PASS`** 登记为 **`DESIGN RESOLVED`**（见 **§4.6.21**）；**`Adapter Contract` 的 implementation ／ realization** 仍属后续独立授权事项（**不**由本 closure 授权）。
>
> **current-state 更新：** `Serialization Format` 已由 **PR #51 Human Decision** 登记为 **JSON**
> （single JSON strategy；manifest = independent artifact ＋ JSON），并经
> **PR #52 Closure Re-run = `PASS`** 后**现为 `DESIGN RESOLVED`**（见 **§4.3.22**）。
> `Physical Dataset Layout` 已由 **PR #53 Human Decision** 登记、并经 **本层 Closure Validation = `PASS`**
> 后**现为 `DESIGN RESOLVED`**（见 **§4.3.23**）。
> `Field Carrier Mapping` 已由 **PR #63 Human Decision ＋ Supplementary Human Naming Decision** 登记、
> 并经 **Closure Re-run = `PASS`** 后**现为 `DESIGN RESOLVED`**（见 **§4.3.25** ／ **§4.3.27**）。
> `Final Import Contract` 已由 **Issue #66 Human Decision（Bundle 1 ～ 6）** 登记、
> 并经 **本层 Closure Validation = `PASS`** 后**现为 `DESIGN RESOLVED`**（见 **§4.3.28** ／ **§4.3.29**）；
> 因而 **`Snapshot / Import Contract` overall 现为 `DESIGN RESOLVED`**。
> **`Adapter Contract` 的实现 ／ realization 仍待后续独立授权**（design 层已 closure；`DESIGN RESOLVED ≠ IMPLEMENTED`）。

> **注意**：`Data Validation` 完成**仅**表示 **conceptual validation design complete**；
> **不代表** implemented / data validated / tested。
>
> §4 现有 **0 个 `DESIGN PENDING` 设计子领域**：
>
> - `Adapter Boundary` 已由 **Issue #90 Closure Validation = `PASS`** 登记为 **`DESIGN RESOLVED`**（Design Review 见 **§4.6**；Closure Validation 见 **§4.6.21**）
>
> （`Snapshot / Import Contract` 已由 **Issue #66 Closure = `PASS`** 关闭 ——
> 见 **§4.3.28** ／ **§4.3.29**；`Master Data Mapping` 已由 **PR #48 Human Decision** 授权并关闭 ——
> 见 **§4.5.25** ／ **§4.5.22 Final Master Data Mapping Closure Implementation Record**。）
>
> **设计层 closure ≠ implemented ／ tested ／ production-ready** —— **不得**据此声称整个 §4 已实现 ／ 已验证，也**不得**声称 `POC Design v0.2 overall` 已完成。

**Legacy routing:** `§4.1 ～ §4.6` 及其 `§4.x.y` references 均通过上表和对应 stub 解析到 standalone spec；各 spec 保留原 section numbering，并作为对应 concern 的唯一 current canonical source。

### 4.1 Canonical Data Model

- **Design Status:** `DESIGN RESOLVED`。
- **Canonical spec:** [Canonical Data Model](specs/data-integration/canonical-data-model.md)。
- **Legacy mapping:** `§4.1.1 ～ §4.1.12` 编号在 standalone spec 中保持不变。
- 本节仅为 **navigation/status stub**，不是第二份 normative source。

---

### 4.2 Data Dictionary

- **Design Status:** `DESIGN RESOLVED`。
- **Canonical spec:** [Data Dictionary](specs/data-integration/data-dictionary.md)。
- **Legacy mapping:** `§4.2.1 ～ §4.2.17` 编号在 standalone spec 中保持不变。
- 本节仅为 **navigation/status stub**，不是第二份 normative source。

---

### 4.3 Snapshot / Import Contract —— Package Envelope & Import Atomicity

- **Design Status:** `DESIGN RESOLVED`。
- **Canonical spec:** [Snapshot / Import Contract](specs/data-integration/snapshot-import-contract.md)。
- **Legacy mapping:** `§4.3.1 ～ §4.3.29` 编号在 standalone spec 中保持不变。
- 本节仅为 **navigation/status stub**，不是第二份 normative source。

---

### 4.4 Data Validation —— Capability Readiness & Failure Semantics

- **Design Status:** `DESIGN RESOLVED`。
- **Canonical spec:** [Data Validation](specs/data-integration/data-validation.md)。
- **Legacy mapping:** `§4.4.1 ～ §4.4.101` 编号在 standalone spec 中保持不变。
- 本节仅为 **navigation/status stub**，不是第二份 normative source。

---

### 4.5 Master Data Mapping

- **Design Status:** `DESIGN RESOLVED`。
- **Canonical spec:** [Master Data Mapping](specs/data-integration/master-data-mapping.md)。
- **Legacy mapping:** `§4.5.1 ～ §4.5.25` 编号在 standalone spec 中保持不变。
- 本节仅为 **navigation/status stub**，不是第二份 normative source。

---

### 4.6 Adapter Boundary

- **Design Status:** `DESIGN RESOLVED`（conceptual closure）。
- **Implementation / runtime realization:** `NOT IMPLEMENTED`。
- **Canonical spec:** [Adapter Boundary](specs/data-integration/adapter-boundary.md)。
- **Legacy mapping:** `§4.6.1 ～ §4.6.22` 编号在 standalone spec 中保持不变；本文档中其他 `§4.6.x` textual references 均通过此 mapping 解析到该 spec。
- 本节仅为 **navigation/status stub**，不是第二份 normative source。

---

## 5. AI / Tool Boundary

**Backlog:** `VB-28`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

**Validation Source:** `SC-EXPLAIN-001` / Human-approved `SIMULATED` downstream design evidence

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED` **≠** `FROZEN` Discovery `H4` resolved。
>
> 本节为 `VB-28` 的 **Canonical Design**。本 Task **未指派** `BR-*` Rule ID —— **不得为了方便自行创建**。

**职责边界状态：**

| 职责 | Status |
| --- | --- |
| LLM | **`DESIGN RESOLVED`** |
| deterministic business logic | **`DESIGN RESOLVED`** |
| Tool | **`DESIGN RESOLVED`** |
| Agent orchestration | **`DESIGN RESOLVED`** |

> 这里的 `DESIGN RESOLVED` **只代表 responsibility / behavioral boundary 已定义**。
>
> **不代表**：framework selected、tools implemented、orchestration implemented、
> prompts implemented、LLM selected、tested、production-ready。

**明确：LLM 不直接自由访问 Production Database。**

> 继承约束（不重新定义）：LLM 获取结构化业务事实必须通过 Controlled Tool（`Data Source → Deterministic Data Tool → Structured Result → LLM`）；不得采用 `LLM → Free-form SQL → Production Database`。

#### 5.0 Design Evidence Record — SC-EXPLAIN-001

| 字段 | 内容 |
| --- | --- |
| Scenario | `SC-EXPLAIN-001` — Shortage Analysis High-frequency Questions |
| Evidence Type | `SIMULATED` |
| Evidence Source | Human-approved |
| Role | Simulated Business Owner ＋ Simulated Procurement / Supply Chain User |
| Purpose | define P0 AI Explanation / User Question boundary |

**必须声明**：该场景

- **不是**云南 CY 集团真实用户访谈；
- **不是** `PUBLIC FACT`；
- **不证明**真实企业的信息解释成本；
- **不修改** `FROZEN` `H4 = TBD`；
- **只**作为模拟 POC 的 **downstream design input**。

该 Scenario 批准以下 **6 类 P0 User Questions** 作为 **`SIMULATED` high-frequency question baseline**。

**不得**描述为真实 CY 企业统计频率。

#### 5.1 Core AI Principle

正式定义：

```
LLM does not create business truth.
```

**LLM 的职责：**

- understand user intent
- request authorized structured facts
- explain deterministic results
- summarize evidence
- surface uncertainty
- generate clearly labeled **Draft** content when allowed

**Deterministic Logic / Controlled Tool 的职责：**

- business facts
- calculations
- classification
- business-rule results
- completeness / missing-data status

必须保持：

```
Facts / Calculation / Classification
  ≠ LLM-generated judgment
```

#### 5.2 Canonical Interaction Flow

定义**概念链路**：

```
User Question
      ↓
LLM / Agent understands intent
      ↓
Authorized Controlled Tool Request
      ↓
Structured Facts
      ↓
Deterministic Business Rules
      ↓
Structured Result + Evidence
      ↓
LLM Explanation
      ↓
Human
```

**禁止**：

```
User Question
      ↓
LLM guesses business facts
      ↓
Answer
```

继续继承：

```
Data Source
      ↓
Deterministic Data Tool
      ↓
Structured Result
      ↓
LLM
```

**不得采用**：

```
LLM
      ↓
Free-form SQL
      ↓
Production Database
```

#### 5.3 P0 Supported Question Baseline

**Q1 — Why is this material short?**

用户意图示例：「为什么这个物料会缺料？」

回答**必须来自** `BR-SHORTAGE-001` 及其**已解析 dependency results**。

可解释：

- `OpeningUsableInventory`
- Effective Inbound
- Approved Substitute Supply
- Gross Requirement
- Safety Stock
- `ProjectedAvailable`
- `FirstShortageDate`
- `ShortageQty`
- `Classification`

LLM **可以**解释计算结果。

**不得**：

- 重新发明计算公式
- 重新计算一套不同结果
- 篡改 deterministic result

**Q2 — Which materials need attention?**

用户意图示例：「现在有哪些物料需要处理？」

**必须基于明确状态过滤**：

- `SHORTAGE`
- `BUFFER_BREACH`
- `DATA_INCOMPLETE`
- `NORMAL`

例如用户明确问：「真正缺料的物料有哪些？」

**只能返回**：

```
Classification = SHORTAGE
```

**不得**将 `BUFFER_BREACH` 描述为**已经缺料**。

如果用户问：「哪些物料需要关注？」

**允许**展示多种状态，但**必须保留状态差异**，**不得**混成一个统一的「缺料」标签。

**Q3 — Why is the recommended purchase quantity X?**

用户意图示例：「为什么建议采购 100？」

**必须引用** `BR-PROCUREMENT-001`，并明确区分：

- `ShortageQty`
- `BasePurchaseNeed`
- `ApplicableMOQ`
- `MOQAdjustmentQty`
- `RecommendedPurchaseQty`

例如：

```
ShortageQty            = 30
RecommendedPurchaseQty = 100
MOQAdjustmentQty       = 70
```

**正确解释**：实际缺口为 `30`；由于 `MOQ = 100`，采购建议被调整为 `100`。

**禁止**：「实际缺料 100。」

**Q4 — Why is this supplier high risk?**

用户意图示例：「这个供应商为什么风险高？」

**必须引用** `BR-SUPPLIER-RISK-001`。

可解释：

- `DaysUntilNeed`
- `StandardLeadTimeDays`
- `LeadTimeRisk`
- `PerformancePeriod`
- `DeliveryPerformance`
- `DeliveryRisk`
- `QualityPerformance`
- `QualityRisk`
- `OverallSupplierRisk`
- Evidence completeness

**不得**进一步自动：

- Supplier Ranking
- Supplier Selection
- recommend a winner
- 修改 `RecommendedPurchaseQty`

**Q5 — Why can't the system give a conclusion?**

用户意图示例：「为什么现在不能给结果？」

当 deterministic result 为 `DATA_INCOMPLETE` 时，**必须展示具体 missing / invalid evidence**。

例如：

- `SafetyStock` missing
- `ApplicableMOQ` missing
- `PerformancePeriod` missing
- Material mapping unresolved
- Supplier-Material Relationship unresolved
- `substitution_ratio` missing

**不得**为了产生「完整回答」而**补值**。

**Q6 — Summarize this shortage case**

用户意图示例：「总结一下这个缺料案例，我接下来要看什么？」

LLM **可以**组织：

```
结论
  ↓
关键数量
  ↓
缺料原因
  ↓
Supplier Risk Evidence
  ↓
Data Quality / Missing Data
  ↓
Purchase Recommendation
  ↓
Human Decision Required
```

但**不得越过**：

- HITL
- Approval
- Write Boundary

#### 5.4 P0 Scope Boundary

必须明确：`VB-28` **并不实现**广义：

```
Natural Language Supply Chain Query
```

P0 **只支持**：围绕**已设计的 P0 deterministic outputs** 进行**受控查询与解释**。

以下仍属于 **P1 / Future scope**，例如：

- arbitrary cross-domain analytics
- unrestricted natural-language enterprise query
- advanced supplier comparison
- broad RAG-based business Q&A
- open-ended optimization

**不得**因为用户可以自然语言提问，就声称 P1 的 Natural Language Query 已完成。

#### 5.5 Standard Explanation Structure

当适用时，P0 Explanation 使用统一**语义结构**：

1. Answer
2. Evidence
3. Uncertainty / Missing Data
4. Human Decision Required

> **注意**：这是 **canonical response meaning**，**不是** API / JSON / UI schema。

**Answer** —— 回答用户的问题；**不得**与 deterministic result **冲突**。

**Evidence** —— 展示支持结论的结构化依据。包括适用的：

- business status
- quantities
- dates
- risk dimensions
- relevant rule result
- evidence completeness

**不得**添加 Tool 未提供、且 Repo 中无正式规则支持的业务事实。

**Uncertainty / Missing Data** —— **必须显式展示**：

- `UNKNOWN`
- missing
- invalid
- `DATA_INCOMPLETE`
- tool failure
- unresolved mapping

**不得隐藏。**

**Human Decision Required** —— 当结果涉及以下内容时：

- Procurement Recommendation
- Draft
- Supplier decision
- approval
- modify / reject / approve
- formal execution

**必须提醒用户**：哪些仍需要 Human 决策。

**不得**将 Recommendation 写成 Approved Decision。

#### 5.6 Evidence Fidelity Rule

定义：

```
LLM may paraphrase evidence,
but may not mutate evidence.
```

例如 Tool 返回 `ShortageQty = 30` —— LLM **不得**回答「约 50 件」。

Tool 返回 `Classification = BUFFER_BREACH` —— LLM **不得**回答「已经缺料」。

Tool 返回 `OverallSupplierRisk = DATA_INCOMPLETE` —— LLM **不得**根据部分 `LOW` evidence
自行宣布 `OverallSupplierRisk = LOW`。

#### 5.7 No Unsupported Fact Rule

核心 fail-safe：

**Tool / deterministic result 没有提供的业务事实，LLM 不得作为事实写入答案。**

**允许**明确说明：

> 「当前证据不足以判断。」

**禁止**以下内容替代缺失业务数据：

- reasonable guess
- likely
- probably
- industry-normal default
- model inference

#### 5.8 Partial Answer Rule

如果只有**部分可靠 evidence**：**允许**回答可靠部分。

**必须同时指出**：哪些结论无法形成。

例如：

```
LeadTimeRisk = HIGH
```

但：

```
PerformancePeriod missing
```

则**可以**解释：Lead Time 已显示 `HIGH` Risk。

但：`OverallSupplierRisk` 仍为 `DATA_INCOMPLETE`。

**不得**因为部分证据可靠就把整体结论**补全**。

#### 5.9 Tool Failure Boundary

如果：

- Controlled Tool unavailable
- timeout
- error
- invalid structured result

则：

**不得**使用模型记忆 / 旧回答代替当前业务事实。

应明确：

```
Current data unavailable
```

或

```
Tool failure
```

并说明：当前**不能可靠回答**哪些部分。

> 本 Task **不定义**：retry implementation、timeout value、circuit breaker、tool framework。
> 这些属于后续 **Architecture / Implementation**。

#### 5.10 Permission Boundary

继承：

```
AI Effective Permission
  = User Permission
  ∩ Data Scope
  ∩ Tool Permission
  ∩ Workflow State
  ∩ POC Policy
```

`VB-28` **不设计** RBAC implementation。

但**必须明确**：Agent / LLM **不得**因为用户自然语言请求**扩大**其 Data Scope 或 Tool Permission。

如果请求**超出当前权限**：**不得获取或泄露数据**。

> 本 Task **不定义**具体 `PERMISSION_DENIED` API contract。

#### 5.11 Out-of-Scope Question Handling

如果用户问题要求当前 P0 **未设计**的能力，例如：

- 「自动帮我选最优供应商」
- 「帮我给供应商排名」
- 「自动把订单下掉」
- 「跨所有企业数据自由分析」
- 「预测未来动态 Lead Time」

AI **不得临时创造规则**。

**必须说明**：该问题**超出当前 P0 已设计能力**，或需要 **Human-approved Future Design**。

#### 5.12 Deterministic / LLM Boundary

以下**不得由 LLM 决定**：

- `Classification`
- `ShortageQty`
- `FirstShortageDate`
- Safety Stock logic
- Substitute eligibility / quantity
- `GrossRequirement`
- `RecommendedPurchaseQty`
- MOQ adjustment
- `LeadTimeRisk`
- `DeliveryRisk`
- `QualityRisk`
- `OverallSupplierRisk`
- `DATA_INCOMPLETE` status
- permission
- approval status

这些来自：

```
deterministic rules
+
structured business facts
```

**LLM 负责**：

- intent understanding
- explanation
- summarization
- user-facing wording
- approved Draft generation

#### 5.13 Agent Orchestration Responsibility

只定义 **conceptual responsibility**，**不得选择 Agent Framework**。

**Agent 可以**：

- identify supported user intent
- determine which authorized business capability is needed
- request required structured result
- combine multiple authorized structured results
- pass structured evidence to LLM for explanation
- stop when required evidence is unavailable

**Agent 不可以**：

- invent Tool capability
- bypass Controlled Tool
- directly query Production DB
- bypass deterministic rule
- expand permissions
- convert missing evidence into facts

#### 5.14 Controlled Tool Responsibility

本 Task **不定义**实际 Tool names / API schema。只定义 **capability boundary**。

Controlled Tool **应负责提供**：

- structured business facts
- deterministic calculation results
- classifications
- relevant evidence
- missing / invalid state

而**不是**让 LLM 从自由文本数据中**自行重建业务计算**。

#### 5.15 Draft Generation Boundary

继承 P0：

**AI 可以**：Generate Procurement Request Draft。

但 Draft **必须基于**：**已取得的 structured deterministic result**。

Draft **必须明确**：

```
DRAFT
```

且：

```
RecommendedPurchaseQty
  ≠ ApprovedPurchaseQty
  ≠ PurchaseOrderQty
```

**LLM 不得**：

- Approve
- Formal Submit
- Create Purchase Order
- Override Human Approval

> 本 Task **不设计** §6 的完整 HITL 状态机。

#### 5.16 Acceptance Examples

以下为 **conceptual examples**。

**Example A — Shortage Explanation**

Structured result：

| 字段 | 值 |
| --- | --- |
| `Classification` | `SHORTAGE` |
| `OpeningUsableInventory` | 20 |
| `CumulativeEffectiveInbound` | 30 |
| `CumulativeApprovedSubstituteSupply` | 0 |
| `CumulativeGrossRequirement` | 80 |
| `ProjectedAvailable` | -30 |
| `FirstShortageDate` | `2026-10-10` |
| `ShortageQty` | 30 |

**Expected AI behavior：** 解释缺料由哪些 deterministic values 形成。

**不得改变** `ShortageQty = 30`。

**Example B — Buffer Breach**

```
Classification = BUFFER_BREACH
ShortageQty    = 0
```

User asks：「是不是已经缺料？」

**Expected：** 明确回答**尚未形成实际 shortage**，当前是 **Safety Stock buffer breach**。

**不得回答**：「是，已经缺料。」

**Example C — Purchase Recommendation**

```
ShortageQty            = 30
ApplicableMOQ          = 100
RecommendedPurchaseQty = 100
MOQAdjustmentQty       = 70
```

**Expected：** 解释**实际缺口 30**；**MOQ 导致建议采购量为 100**。

**不得说**：「实际缺料 100。」

**Example D — Partial Supplier Risk Evidence**

```
LeadTimeRisk        = HIGH
DeliveryRisk        = DATA_INCOMPLETE
QualityRisk         = DATA_INCOMPLETE
OverallSupplierRisk = DATA_INCOMPLETE
```

**Expected：** **允许**解释 Lead Time `HIGH` evidence。

**必须说明**：Overall Risk 尚**无法可靠确定**。

**不得**自动输出 `HIGH` Overall。

**Example E — Missing Data**

```
ApplicableMOQ = missing
```

**Expected：**

- **No Numeric Purchase Recommendation**
- 解释 **MOQ 信息缺失**

**不得**：`ApplicableMOQ = 0`。

**Example F — Unsupported Supplier Selection**

```
Supplier A Risk = LOW
Supplier B Risk = HIGH
```

User asks：「直接帮我选 A 下单。」

**Expected：** **可以**解释两者 Risk Evidence 差异。

**不得**：

- 自动选择 Supplier A
- 批准采购
- 正式下单

**Example G — Tool Failure**

Required controlled capability unavailable.

**Expected：** 明确说明当前**无法取得可靠实时结构化结果**。

**不得**引用旧聊天内容**伪装成当前事实**。

#### 5.17 H4 Relationship

必须记录：`SC-EXPLAIN-001` 提供的是

```
Human-approved SIMULATED
high-frequency question baseline
+
downstream design evidence
```

它支持当前 POC 设计 **AI Explanation capability**。

**但**：`FROZEN` Discovery Validation 中

```
H4 = TBD
```

**保持不变。**

**不得**写成 `H4 = PARTIALLY CONFIRMED`。

未来若正式更新 `H4`：**新的 Validation Version / Addendum ＋ Human Approval**。

> 即：本 Task **不修改** `FROZEN` Validation，**不把设计证据倒写成历史 Discovery 事实**。

#### 5.18 Status Semantics Boundary

本节各项 `DESIGN RESOLVED` **只代表**：

```
responsibility / behavioral boundary 已定义
```

**不代表**：

- framework selected
- tools implemented
- orchestration implemented
- prompts implemented
- LLM selected
- tested
- production-ready

#### 5.19 Source-field / Implementation Boundary

本 Task **只做 Design Boundary**。

因此**不得创建**：

- prompts / system prompts
- code
- tests / evals
- mock API
- tool implementation
- function schema
- JSON contract
- database schema
- UI
- agent graph
- workflow engine
- RAG
- vector DB
- ADR

本 Task **不选择**：

- Agent Framework
- LLM Provider / Model
- Vector Database / RAG Framework
- API Framework
- Tool Protocol / MCP implementation
- database
- deployment stack

---

## 6. HITL Workflow

> 本章节只建立未来需要设计的内容。**不得设计具体状态机。**

未来需要设计：

| 环节 | Status |
| --- | --- |
| Draft | `DESIGN PENDING` |
| Review | `DESIGN PENDING` |
| Modify | `DESIGN PENDING` |
| Approve | `DESIGN PENDING` |
| Reject | `DESIGN PENDING` |
| execution boundary | `DESIGN PENDING` |

> 继承约束（不重新定义）：AI 只能生成 Procurement Request Draft，**不得** Approve / Formal Submit / Create Purchase Order / Override Approval；审批后若 Supplier / Quantity / Price / Delivery Date 发生重大变更，须重新进入 Review / Approval。

> **`VB-29` 建立的硬边界（不改变上表 Status）**：
>
> `Draft` / `Review` / `Modify` / `Approve` / `Reject` **都可以存在**于 POC 内。
>
> 但：
>
> ```
> execution boundary = OUTSIDE POC
> ```
>
> 即 Human 在 POC 内 `Approve` **不等于** Production Execution；
> **不得**自动写入 ERP / 自动创建 PO / 自动提交 Production workflow。
>
> 本节**仍为 `DESIGN PENDING`** —— 完整 HITL state machine **不由 `VB-29` 设计**（见 §3.12）。

---

## 7. Permission & Security

> 本章节只建立未来需要设计的内容。**不得本轮设计实现方案。**

未来需要设计：

| 项 | Status |
| --- | --- |
| RBAC | `DESIGN PENDING` |
| Data Scope | `DESIGN PENDING` |
| Tool Permission | `DESIGN PENDING` |
| Read / Write Boundary | **`DESIGN RESOLVED`** |
| Secret Handling | `DESIGN PENDING` |

**继承：`Human Capability may be greater than Agent Capability`。**

> 继承约束（不重新定义）：`AI Effective Permission = User Permission ∩ Data Scope ∩ Tool Permission ∩ Workflow State ∩ POC Policy`；不得将真实企业 credentials 放入 Git，不得将 secrets 写入 prompt / logs。

> **`VB-29` 只解决 `Read / Write Boundary`（依据 `VR-007` ＋ `VB-29` Human Approval）** ——
> 见 §3 Read / Write / Draft / Failure Boundary。
>
> **其余项仍为 `DESIGN PENDING`**：RBAC / Data Scope / Tool Permission / Secret Handling。
>
> **不得因为 `VB-29` 完成就把整个 §7 标记为完成。**

---

## 8. Audit & Observability

> 本章节只建立未来需要覆盖的范围。

未来需要覆盖：

| 项 | Status |
| --- | --- |
| business decision trace | `DESIGN PENDING` |
| Tool invocation | `DESIGN PENDING` |
| rule version | `DESIGN PENDING` |
| Human approval | `DESIGN PENDING` |
| errors / failures | `DESIGN PENDING` |

---

## 9. Test & AI Eval

> 本章节只建立未来需要区分的测试层次。**不得创建测试代码。**

未来需要区分：

| 层次 | Status |
| --- | --- |
| deterministic unit tests | `DESIGN PENDING` |
| integration tests | `DESIGN PENDING` |
| AI Eval | `DESIGN PENDING` |
| HITL / business acceptance | `DESIGN PENDING` |

---

## 10. Architecture Decisions

重大 Architecture Decision **必须**经过：

```
Options
→ Trade-offs
→ Recommendation
→ Human Approval
→ ADR
```

**至少包含：** **Option 0 — keep current / do nothing**

**当前：`No ADR created yet.`**

---

## 11. Open Design Backlog

> 本节登记并**保留**以下条目。**未经 Human Approval 不得关闭**；`VB-14`、`VB-15`、`VB-16`、`VB-17`、`VB-18`、`VB-27`、`VB-28`、`VB-29` 已获得 Human Approval。

| Backlog ID | 归属 | Status |
| --- | --- | --- |
| `VB-14` | P0 Business Rules（见 §2.1 Shortage Definition）<br>→ **`BR-SHORTAGE-001` / §2.1** | **`DESIGN RESOLVED`** |
| `VB-15` | P0 Business Rules（见 §2.2 Available Inventory / Safety Stock）<br>→ **`BR-INVENTORY-001` / §2.2** | **`DESIGN RESOLVED`** |
| `VB-16` | P0 Business Rules（见 §2.3 Substitute Material）<br>→ **`BR-SUBSTITUTE-001` / §2.3** | **`DESIGN RESOLVED`** |
| `VB-17` | P0 Business Rules（见 §2.4 Scrap / Loss）<br>→ **`BR-REQUIREMENT-001` / §2.4** | **`DESIGN RESOLVED`** |
| `VB-18` | P0 Business Rules（见 §2.5 MOQ / Purchase Recommendation Quantity）<br>→ **`BR-PROCUREMENT-001` / §2.5** | **`DESIGN RESOLVED`** |
| `VB-27` | Supplier Risk / Risk Evidence（见 §2.7）<br>→ **`BR-SUPPLIER-RISK-001` / §2.7** | **`DESIGN RESOLVED`** |
| `VB-28` | AI Explanation / User Questions（见 §5 AI / Tool Boundary）<br>→ **`§5` ＋ `SC-EXPLAIN-001`** | **`DESIGN RESOLVED`** |
| `VB-29` | POC Integration Boundary（见 §3 System Boundary；§7 Read / Write Boundary）<br>→ **`§3` ＋ `§7` ＋ `VR-007` ＋ Human Approval** | **`DESIGN RESOLVED`** |

**已登记但不占用 `VB` 编号的设计项**（`POC Design v0.2` 内部的独立设计项）：

| Design Item | 归属 | Status |
| --- | --- | --- |
| `BR-INBOUND-001` | P0 Business Rules（见 §2.6 Effective Inbound） | **`DESIGN RESOLVED`** |

> **`§2.6 Effective Inbound` 没有独立 `VB` 编号** —— 它是 `POC Design v0.2` 中已经明确登记的设计项。
>
> **不得为了方便自行创建新的 `VB` ID。**

**归属说明：**

- `VB-14` ～ `VB-18` → **P0 Business Rules**
- `VB-27` → **Supplier Risk / Risk Evidence**
- `VB-28` → **AI Explanation / User Questions**
- `VB-29` → **POC Integration Boundary**；设计结论见 **§3 System Boundary** 与 **§7 Read / Write Boundary**；
  下方 `FROZEN` 原定义**仅作为历史 Validation baseline 引用**，**不修改其原始内容**。

> **`VB-29` 的 `FROZEN` 原定义（历史 Validation baseline，逐字引用，未改写）**：
>
> 以下引文**保持原始记录不变** —— 其中 `Current Evidence Status`（`HYPOTHESIS` / `H7`）与
> `Status`（`NOT STARTED`）**属于 `FROZEN` baseline 的历史状态**，
> **不得因为本 PR 已完成 Design Resolution 而改写**。
>
> `FROZEN` 源文件：`docs/discovery/discovery-validation-v0.1.md`
>
> | 字段 | 内容 |
> | --- | --- |
> | ID | `VB-29` |
> | Question | POC 是否可以只读 + 草稿方式接入，无需写入业务系统？ |
> | Current Evidence Status | `HYPOTHESIS`（H7） |
> | Why It Matters | §19 I3；安全边界 |
> | Evidence Needed | 接入边界确认 |
> | Suggested Validation Method | Interface / system assumption confirmation（Simulated） |
> | Owner | Human |
> | Status | `NOT STARTED` |
> | Blocks? | NO |
>
> 本文档**只引用其 ID 与 FROZEN source**，**不自行创造描述**。

---

## Explicit Non-Decisions

当前**明确尚未决定**：

- backend framework
- frontend framework
- Agent framework
- LangGraph usage
- database
- vector database
- cache
- message queue
- deployment platform
- cloud provider
- authentication implementation
- API style
- Mock API design

**已决定项（Issue #112 current-state synchronization）：** concrete file format／Serialization Format 已由 PR #51 Human Decision 选择 JSON，并经 PR #52 Closure Re-run；canonical authority 见 [snapshot-import-contract.md](specs/data-integration/snapshot-import-contract.md) §4.3.21 ～ §4.3.22。原“尚未决定”条目已移除；本次只消除过期状态矛盾，未重新选择格式。

**这些不是遗漏。**

它们需要在**后续 Design Task** 中，基于业务规则与实际 Architecture needs 决定。

---

## Document Control

**Document:** POC Design
**Version:** v0.2
**Status:** `DRAFT`
**Phase:** POC Design
**Entry Gate:** `READY`

**继承基线：**

- `docs/discovery/discovery-brief-v0.1.1.md`（`FROZEN`）
- `docs/discovery/discovery-validation-v0.1.md`（`FROZEN`）

- 本文档为 **POC Design 阶段的 Canonical Source**。
- 本文档**不修改、不重新解释**任何 `FROZEN` Discovery 内容。
- 本文档**不包含**任何技术栈选择；**尚未形成**正式的 Architecture Decision 或 ADR。
- 本文档当前**包含**已经 Human-approved、且状态为 `DESIGN RESOLVED` 的 P0 business rules。
- `DESIGN RESOLVED` **不代表** `IMPLEMENTED`，**不代表** `TESTED`，也**不代表** `APPROVED` 或 `FROZEN`。
- **尚未解决**的设计项继续保持 `DESIGN PENDING` / `NOT STARTED`，**不得视为已完成**。
- 本文档**仍未包含**任何 implementation code、Schema、Contract、Mock API 或 Mock Dataset。
- `POC Design v0.2` 当前**仍为 `DRAFT`**。
