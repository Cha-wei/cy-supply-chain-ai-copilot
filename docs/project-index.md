# Project Index（项目导航索引）

**Document:** Project Index
**Version:** v0.1
**Status:** `DRAFT`
**Doc Type:** Navigation Index —— **非** Canonical Source
**Baseline:** `main @ b4d3bf76`

> 本文档用于新 Chat / 新 Agent 冷启动导航。内容为 **snapshot**，可能滞后于 `main`。

---

## 1. Purpose / Authority Boundary

本文档**只**是 **navigation index**，用于降低长期项目的冷启动 Context 成本。

**Authority Boundary：**

- 本文档**不是** canonical source，也**不是** Project Summary / Decision Log / Handoff Log /
  Architecture Doc / PR History / Commit History / 全量状态镜像。
- **Canonical source 是 `main` 上的正式文档与实际代码。**
- 与 canonical source **冲突时，canonical source 优先**。本文档**不得**被引用为设计依据。
- 本文档**不复制** Human Decision 全文、design rationale 全文、PR Review 全文或长篇历史记录。
- 本文档**不重新解释** `FROZEN` Discovery 内容。

**状态表述纪律：**

- `DESIGN RESOLVED` **不等于** `IMPLEMENTED`，**不等于** `TESTED`，也**不等于** `APPROVED` / `FROZEN`。
- **不得**把 `DESIGN PENDING` / `NOT STARTED` 表述为已完成。

---

## 2. Governance Navigation

| 文件 | 作用 | 层级 |
| --- | --- | --- |
| `AGENTS.md` | 项目 Hard Rules、Context Recovery、Project Standards | Hard Rules |
| `CONTRIBUTING.md` | 工程 Workflow：DoR / DoD、Git & GitHub、Testing & Validation、Documentation、Delivery Report、Rule Conflict | 一般 Workflow |

规则优先级（canonical definition 见 `CONTRIBUTING.md` §1）：
`事实完整性 / 安全 / FROZEN / 已批准 Decision` ＞ `AGENTS.md` Hard Rules ＞ `当前 Task 的明确限制` ＞ `专项规范文件` ＞ `CONTRIBUTING.md`。

`CONTRIBUTING.md` 当前 approved baseline = **v0.2**（`APPROVED`，**未** `FROZEN`）。

---

## 3. Business Baseline Navigation

| 文档 | 版本 | 状态 |
| --- | --- | --- |
| `docs/discovery/discovery-brief-v0.1.1.md` | v0.1.1 | **`FROZEN`** |
| `docs/discovery/discovery-validation-v0.1.md` | v0.1 | **`FROZEN`**（Human-approved，Frozen Date `2026-09-21`） |

- 二者是**已冻结的继承事实**：**不得修改**实质内容，**不得**把 `HYPOTHESIS` / `UNKNOWN` / `TBD` 表述为已确认事实。
- `discovery-validation-v0.1.md` 是 Discovery Validation Phase 的 Canonical Source（验证台账）。
- `E05`（真实 ERP 品牌 / 版本）、`E06`（WMS）、`E07`（BOM / PLM ownership）**仍为 `UNKNOWN`**。

---

## 4. Canonical Design Navigation

| 文档 | 状态 |
| --- | --- |
| `docs/design/poc-design-v0.2.md` | **`DRAFT`** —— **POC Design 阶段 Canonical Source** |

`POC Design v0.2` 继承上述两个 `FROZEN` baseline，**不修改、不重新解释** FROZEN Discovery。

---

## 5. Major Design State（仅高层状态 ＋ 定位入口）

> 只记录**状态与入口**，**不复制**设计内容。状态以 `main` 为准。

| 设计领域 | 状态 | 入口 |
| --- | --- | --- |
| P0 Business Rules ／ System Boundary & Integration | **`DESIGN RESOLVED`** | §2；§3（status 见 §3.14）；§11 Open Design Backlog |
| Canonical Data Model ／ Data Dictionary | **`DESIGN RESOLVED`** | §4.1；§4.2 |
| **Snapshot / Import Contract overall** | **`DESIGN PENDING`** | §4.3；status 见 §4.3.21 |
| ├ Package Envelope ／ Atomicity ／ Immutability ／ Analysis Run Linkage | `DESIGN RESOLVED` | §4.3 |
| ├ Serialization Format | **`DESIGN RESOLVED`** | §4.3.22 |
| ├ Physical Dataset Layout | **`DESIGN PENDING`** | §4.3（`Physical Dataset Layout Design Review` ＋ `Human Decision Record`） |
| ├ Field Carrier Mapping | **`DESIGN PENDING`** | 尚未设计 |
| └ Final Import Contract | **`DESIGN PENDING`** | 尚未设计 |
| Data Validation | **`DESIGN RESOLVED`** | §4.4；closure 见 §4.4.101 |
| Master Data Mapping | **`DESIGN RESOLVED`**（11 / 11 层） | §4.5；status 见 §4.5.24；scope 见 §4.5.25 |
| **Adapter Boundary** | **`DESIGN PENDING`** | §4 子章节状态表 |
| AI / Tool Boundary、HITL、Permission & Security、Audit & Observability、Test & AI Eval | 见对应章节 status boundary | §5 ～ §9（§5 status 见 §5.18） |
| Architecture Decisions | **尚无正式 ADR**；技术栈明确未决定 | §10；`## Explicit Non-Decisions` |

**§4 仍有 2 个 `DESIGN PENDING` 子领域：** `Snapshot / Import Contract`、`Adapter Boundary`。
**不得声称整个 §4 已完成。**

---

## 6. Current Phase / Next Gate

**当前 Phase：** `POC Design v0.2`（**`DRAFT`**，尚未 `APPROVED` / `FROZEN`）。

**最近下一设计 Gate：** `Physical Dataset Layout` Implementation PR ——
由 **PR #53 Human Decision（决定 10）条件性授权**：

```
只有当 Human-approved layout decisions = fully registered
     且 L-1 ～ L-11 = ALL PASS
     且 New Blocking Contradiction = NONE
才允许  Physical Dataset Layout   DESIGN PENDING → DESIGN RESOLVED
```

该层当前执行状态：`Human Decision = RECORDED`；`Implementation = NOT YET EXECUTED`；
`Physical Dataset Layout Closure = NOT YET EXECUTED`；`L-1 ～ L-11 = HUMAN APPROVED FOR IMPLEMENTATION`。

**其后仍待设计：** `Field Carrier Mapping`、`Final Import Contract`、`Adapter Boundary`。

**Merge 到 `main` 是永久 Human Gate；Agent 不得自行 merge。**

---

## 7. Cold Start Protocol

默认读取顺序（**渐进式**，够用即停）：

1. `docs/project-index.md`
2. `AGENTS.md` / `CONTRIBUTING.md`
3. 当前 active Task（Issue / PR / Task 描述）
4. 该 Task 明确引用的 canonical sections
5. current `git diff` / PR / CI 状态
6. **仅在**出现 ambiguity / contradiction 时，才读取更深历史

---

## 8. Context Loading Principle

- **Reference over duplication：** 引用 canonical source，**不复制**其内容。
- **Progressive context loading：** 按需逐层加载，够用即停。
- **不得**默认读取：整个 repository、整个 `POC Design v0.2`、全部历史 PR / commit / closed issue。
- Repository 是 durable project memory；**conversation history 不是**恢复项目状态的必需依赖。

---

## Document Control

**Document:** Project Index
**Version:** v0.1
**Status:** `DRAFT` —— 尚未 `APPROVED` / `FROZEN`
**Doc Type:** Navigation Index —— **非** Canonical Source
**Baseline:** `main @ b4d3bf76`

- 本文档**不替代**任何 canonical source，**不构成**新的项目事实或 Decision。
- 本文档内容为 snapshot；`main` 变化后**应同步更新**，但**不得**据此改写 canonical 文档。
- 冲突时以 canonical source 为准。
