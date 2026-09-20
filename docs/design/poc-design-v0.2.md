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
> 它**继承**上述两个 `FROZEN` baseline，但**不得重新解释或覆盖** FROZEN Discovery 的任何内容。
>
> **当前状态**：`DRAFT`。本版本只建立设计骨架、继承已冻结的 Discovery Baseline、并登记待设计事项。**本轮不代表设计已完成**，也未获得 `APPROVED` / `FROZEN`。

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

> 本节待设计。以下为占位说明，**不重新定义 P0 / P1**。

### P0 设计目标

`DESIGN PENDING`

> P0 范围以 `FROZEN` Discovery Brief §11 为准（缺料分析 → 采购建议 → HITL）。本节**不重新定义 P0 / P1**，只登记待设计的设计目标。

### POC 成功边界

`DESIGN PENDING`

> 成功标准以 `FROZEN` Discovery Brief §16 为准；失败条件以 §17 为准。

### In Scope

`DESIGN PENDING`

### Out of Scope

`DESIGN PENDING`

> P1 能力（RAG、高级供应商比较、自然语言供应链查询、自动报告）以 `FROZEN` Discovery Brief §12 为准。

---

## 2. P0 Business Rules

> 本节各项均对应 `FROZEN` Discovery Validation v0.1 中的 Open Design Backlog。**本轮不定义任何规则内容。**

### 2.1 Shortage Definition

**对应：** `VB-14`

**Status:** `DESIGN PENDING`

> FROZEN source 中的原问题：「缺料」在业务上如何定义？（依据 `K-BR-1`；关联 `G-07`）

### 2.2 Available Inventory / Safety Stock

**对应：** `VB-15`

**Status:** `DESIGN PENDING`

> FROZEN source 中的原问题：安全库存如何计算？（关联 `G-04`）

### 2.3 Substitute Material

**对应：** `VB-16`

**Status:** `DESIGN PENDING`

> FROZEN source 中的原问题：替代料如何处理？（关联 `G-05`）

### 2.4 Scrap / Loss

**对应：** `VB-17`

**Status:** `DESIGN PENDING`

> FROZEN source 中的原问题：损耗率规则？（关联 `G-03`）

### 2.5 MOQ / Purchase Recommendation Quantity

**对应：** `VB-18`

**Status:** `DESIGN PENDING`

> FROZEN source 中的原问题：采购最小批量（MOQ）是否影响采购建议？（关联 `G-10`）

### 2.6 Effective Inbound

**Status:** `DESIGN PENDING`

记录：该规则**需要在本阶段正式定义**。

本轮**不得**自行定义算法。

> 相关背景（属 FROZEN baseline，不重新解释）：`FROZEN` Discovery Brief §20 已将该口径划归 `POC Design v0.2`；`FROZEN` Discovery Validation v0.1 已在 `VR-005` 中确认 Purchase Order / Inbound 数据可得，但明确"**不得**在本阶段定义「有效在途」的最终业务算法"。

### 2.7 Supplier Risk / Evidence

**对应：** `VB-27`

**Status:** `DESIGN / VALIDATION PENDING`

`H3` 仍为 `TBD`。

> FROZEN source 中的原问题：风险判断是否依赖个人经验？（`HYPOTHESIS` / `TBD`；关联 `G-06`、`G-11`）

---

## 3. System Boundary

> 本章节只建立结构。**不填入具体技术组件。**

未来需要说明：

| 待说明项 | Status |
| --- | --- |
| POC responsibility | `DESIGN PENDING` |
| external system boundary | `DESIGN PENDING` |
| write boundary | `DESIGN PENDING` |
| failure boundary | `DESIGN PENDING` |

> 继承约束（不重新定义）：Source-system write = `DENIED`；Production write-back = `OUT OF SCOPE`（见 §5 Design Principles → Integration）。

---

## 4. Data & Integration Design

> 本章节只建立未来子章节。当前只写 `DESIGN PENDING`。**不得创建实际 Schema / Contract。**

| 子章节 | Status |
| --- | --- |
| Canonical Data Model | `DESIGN PENDING` |
| Data Dictionary | `DESIGN PENDING` |
| Snapshot / Import Contract | `DESIGN PENDING` |
| Data Validation | `DESIGN PENDING` |
| Master Data Mapping | `DESIGN PENDING` |
| Adapter Boundary | `DESIGN PENDING` |

> 继承约束（不重新定义）：Integration Pattern = **Controlled Export / Snapshot**。具体文件格式（CSV / JSON / Parquet）与 Adapter Contract 属本阶段待设计事项，**本轮未决定**。

---

## 5. AI / Tool Boundary

> 本章节只建立未来需要设计的职责。**不得选择 Agent Framework。**

未来需要设计的职责：

| 职责 | Status |
| --- | --- |
| LLM | `DESIGN PENDING` |
| deterministic business logic | `DESIGN PENDING` |
| Tool | `DESIGN PENDING` |
| Agent orchestration | `DESIGN PENDING` |

**明确：LLM 不直接自由访问 Production Database。**

> 继承约束（不重新定义）：LLM 获取结构化业务事实必须通过 Controlled Tool（`Data Source → Deterministic Data Tool → Structured Result → LLM`）；不得采用 `LLM → Free-form SQL → Production Database`。

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

---

## 7. Permission & Security

> 本章节只建立未来需要设计的内容。**不得本轮设计实现方案。**

未来需要设计：

| 项 | Status |
| --- | --- |
| RBAC | `DESIGN PENDING` |
| Data Scope | `DESIGN PENDING` |
| Tool Permission | `DESIGN PENDING` |
| Read / Write Boundary | `DESIGN PENDING` |
| Secret Handling | `DESIGN PENDING` |

**继承：`Human Capability may be greater than Agent Capability`。**

> 继承约束（不重新定义）：`AI Effective Permission = User Permission ∩ Data Scope ∩ Tool Permission ∩ Workflow State ∩ POC Policy`；不得将真实企业 credentials 放入 Git，不得将 secrets 写入 prompt / logs。

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

> 本节登记并**保留**以下条目，**不得自行关闭**。

| Backlog ID | 归属 | Status |
| --- | --- | --- |
| `VB-14` | P0 Business Rules（见 §2.1 Shortage Definition） | `NOT STARTED` |
| `VB-15` | P0 Business Rules（见 §2.2 Available Inventory / Safety Stock） | `NOT STARTED` |
| `VB-16` | P0 Business Rules（见 §2.3 Substitute Material） | `NOT STARTED` |
| `VB-17` | P0 Business Rules（见 §2.4 Scrap / Loss） | `NOT STARTED` |
| `VB-18` | P0 Business Rules（见 §2.5 MOQ / Purchase Recommendation Quantity） | `NOT STARTED` |
| `VB-27` | Supplier Risk / Risk Evidence（见 §2.7） | `NOT STARTED` |
| `VB-28` | AI Explanation / User Questions | `NOT STARTED` |
| `VB-29` | 见下方说明 | `NOT STARTED` |

**归属说明：**

- `VB-14` ～ `VB-18` → **P0 Business Rules**
- `VB-27` → **Supplier Risk / Risk Evidence**
- `VB-28` → **AI Explanation / User Questions**
- `VB-29` → 后续根据 `FROZEN` Validation 中的**原定义**映射，**不得猜测或改写其含义**。

> **`VB-29` 的 FROZEN 原定义（逐字引用，未改写）**：
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
- concrete file format
- Mock API design

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
- 本文档**不包含**任何技术栈选择、Architecture Decision 或 ADR。
- 本文档**不包含**具体业务规则定义、Schema、Contract、Mock API、Mock Dataset 或任何实现代码。
- 本轮只表示：**POC Design phase has formally started.**
