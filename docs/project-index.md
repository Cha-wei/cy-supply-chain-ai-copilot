# Project Index（项目导航索引）

**Document:** Project Index
**Version:** v0.1
**Status:** `DRAFT`
**Doc Type:** Navigation Index —— **非** Canonical Source

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

| 文件 | 职责 | 层级 |
| --- | --- | --- |
| `AGENTS.md` | 项目 Hard Rules、Context Recovery、Project Standards | Hard Rules |
| `CONTRIBUTING.md` | 工程 Workflow：DoR / DoD、Git & GitHub、Testing & Validation、Documentation、Delivery Report、Rule Conflict | 一般 Workflow |

- 规则优先级（Rule Precedence）与规则冲突处理：canonical definition 见 `CONTRIBUTING.md` §1 ／ §12，**本文档不复制其内容**。
- `CONTRIBUTING.md` 当前 approved baseline = **v0.4**（`APPROVED`，**未** `FROZEN`）。

---

## 3. Business Baseline Navigation

| 文档 | 版本 | 状态 | 用途 |
| --- | --- | --- | --- |
| `docs/discovery/discovery-brief-v0.1.1.md` | v0.1.1 | **`FROZEN`** | 业务基线（Discovery Brief） |
| `docs/discovery/discovery-validation-v0.1.md` | v0.1 | **`FROZEN`**（Human-approved，Frozen Date `2026-09-21`） | Discovery Validation Phase Canonical Source（验证台账） |

- 二者为**已冻结的继承事实**；使用与修改约束见 `AGENTS.md` 第 2 条及各自文档头部的冻结规则，**本文档不复制**。

---

## 4. Canonical Design Navigation

| 文档 | 状态 |
| --- | --- |
| `docs/design/poc-design-v0.2.md` | **`DRAFT`** —— **POC Design 阶段 Canonical Source** |
| [Canonical Data Model](design/specs/data-integration/canonical-data-model.md) | **`DESIGN RESOLVED`** —— Canonical Data Model concern 的 standalone canonical spec |
| [Data Dictionary](design/specs/data-integration/data-dictionary.md) | **`DESIGN RESOLVED`** —— Data Dictionary concern 的 standalone canonical spec |
| [Snapshot / Import Contract](design/specs/data-integration/snapshot-import-contract.md) | **`DESIGN RESOLVED`** —— Snapshot / Import Contract concern 的 standalone canonical spec |
| [Data Validation](design/specs/data-integration/data-validation.md) | **`DESIGN RESOLVED`** —— Data Validation concern 的 standalone canonical spec |
| [Master Data Mapping](design/specs/data-integration/master-data-mapping.md) | **`DESIGN RESOLVED`** —— Master Data Mapping concern 的 standalone canonical spec |
| [Adapter Boundary](design/specs/data-integration/adapter-boundary.md) | **`DESIGN RESOLVED`** —— Adapter Boundary concern 的 standalone canonical spec |

`POC Design v0.2` 继承上述两个 `FROZEN` baseline，**不修改、不重新解释** FROZEN Discovery。

---

## 5. Major Design State（仅高层状态 ＋ 定位入口）

> 只记录**状态与入口**，**不复制**设计内容。状态以 `main` 为准。

| 设计领域 | 状态 | 入口 |
| --- | --- | --- |
| **POC Design Goals & Scope（§1）** | **`DESIGN RESOLVED`**（四项；conceptual closure） | [POC Design](design/poc-design-v0.2.md) §1 final wording；GSD-8 见 §1.18；closure 见 §1.19；current status 见 §1.20 |
| P0 Business Rules ／ System Boundary & Integration | **`DESIGN RESOLVED`** | §2；§3（status 见 §3.14）；§11 Open Design Backlog |
| Canonical Data Model ／ Data Dictionary | **`DESIGN RESOLVED`** | [canonical-data-model.md](design/specs/data-integration/canonical-data-model.md) §4.1；[data-dictionary.md](design/specs/data-integration/data-dictionary.md) §4.2 |
| **Snapshot / Import Contract overall** | **`DESIGN RESOLVED`** | [snapshot-import-contract.md](design/specs/data-integration/snapshot-import-contract.md) §4.3；status 见 §4.3.21 |
| ├ Package Envelope ／ Atomicity ／ Immutability ／ Analysis Run Linkage | `DESIGN RESOLVED` | [snapshot-import-contract.md](design/specs/data-integration/snapshot-import-contract.md) §4.3 |
| ├ Serialization Format | **`DESIGN RESOLVED`** | [snapshot-import-contract.md](design/specs/data-integration/snapshot-import-contract.md) §4.3.22 |
| ├ Physical Dataset Layout | **`DESIGN RESOLVED`** | [snapshot-import-contract.md](design/specs/data-integration/snapshot-import-contract.md) §4.3.23；closure 见 §4.3.24 |
| ├ Field Carrier Mapping | **`DESIGN RESOLVED`** | [snapshot-import-contract.md](design/specs/data-integration/snapshot-import-contract.md) §4.3.25；closure 见 §4.3.27 |
| └ Final Import Contract | **`DESIGN RESOLVED`** | [snapshot-import-contract.md](design/specs/data-integration/snapshot-import-contract.md) §4.3.28；closure 见 §4.3.29 |
| Data Validation | **`DESIGN RESOLVED`** | [data-validation.md](design/specs/data-integration/data-validation.md) §4.4；closure 见 §4.4.101 |
| Master Data Mapping | **`DESIGN RESOLVED`**（11 / 11 层） | [master-data-mapping.md](design/specs/data-integration/master-data-mapping.md) §4.5；status 见 §4.5.24；scope 见 §4.5.25 |
| **Adapter Boundary** | **`DESIGN RESOLVED`**（conceptual closure；implementation 未授权） | [Adapter Boundary](design/specs/data-integration/adapter-boundary.md)；closure 见 `adapter-boundary.md` §4.6.21 |
| AI / Tool Boundary、HITL、Permission & Security、Audit & Observability、Test & AI Eval | 见对应章节 status boundary；P0 AI Explanation 的最小 runtime architecture 已由 **ADR-002 `ACCEPTED`** 登记（decision only）；其 `§7` Secret Handling JIT prerequisite 已由 **Issue #180** 的 scoped closure 满足（`Secret Handling = DESIGN RESOLVED`（hosted P0 AI Explanation minimum only）；`§7 overall = NOT RESOLVED`；RBAC ／ Data Scope ／ Tool Permission 仍 `DESIGN PENDING`）；**`§5.3` Q3 explanation runtime core 已实现**（provider-neutral，见 `§5.20`，Issue #182）；**首个 hosted provider adapter（DeepSeek）已实现**（`§5.21`，Issue #184；implementation configuration，credential 仅从 process environment 读取，tests ／ CI 使用 stub transport；未声称 AI Eval ready ／ POC validated）；**Q3 manual opt-in live smoke entry point 已实现**（`§5.22`，Issue #186；thin、复用已 merge 的 adapter 与 validator，固定 SIMULATED projection，报告 sanitized；该记录中 `LIVE_SMOKE_NOT_RUN` 为 Issue #186 时点事实）；**DeepSeek Q3 live API contract smoke = `PASS`**（`§5.23`，Issue #188；Human 于 `main @ 31fab37` 以 process environment credential 真实执行一次 = `LIVE_SMOKE_PASS`：HTTP 200、真实 `/responses` envelope 经 merged parser、selection 经 merged validator、五个 Q3 量齐备、`uncertainty` 空、无 credential 泄漏观察；**单次观察（n = 1）**，未声称 AI Eval、provider ／ model quality、business accepted、production ready 或 `POC validated`） | §5 ～ §9（§5 status 见 §5.18；`§5.20` Q3 runtime record；`§5.21` DeepSeek adapter record；`§5.22` live smoke record；`§5.23` live API contract smoke validation record；§7 见 §7.1；§9 分层见 §9.1 ～ §9.4）；[ADR-002](architecture/adr-002-p0-ai-explanation-minimum-runtime.md) |
| Minimum Architecture / Code Start Gate | **ADR-001 ACCEPTED；CSG-1 ～ CSG-8 PASS**；仅第一批 deterministic tranche 授权；该 tranche 的五个 module 职责与 `§2.1` ～ `§2.7` rules 已实现并由 thin composition 串联（current state 见 §10.2）；`Unrestricted implementation` 仍未授权 | [ADR-001](architecture/adr-001-deterministic-core.md)；[POC Design §10.1](design/poc-design-v0.2.md#implementation-ready-minimum) ／ §10.2；更广泛 Architecture 仍未决定 |

**§4 现有 0 个 `DESIGN PENDING` 设计子领域**（`Adapter Boundary` 已由 Issue #90 Closure Validation = `PASS`
登记为 `DESIGN RESOLVED`；见 [adapter-boundary.md](design/specs/data-integration/adapter-boundary.md) §4.6.21）。
**设计层 closure ≠ implemented / tested / production-ready；不得据此声称整个 §4 已实现 / 已验证，
也不得声称 `POC Design v0.2 overall` 已完成。**

---

## 6. Current Phase / Next Gate

**当前 Phase：** `POC Design v0.2`（**`DRAFT`**，尚未 `APPROVED` / `FROZEN`）。

**当前工作阶段：** first deterministic tranche（`§10.1` B）的 **integration / acceptance closure**
—— 五个 module 职责与 `§2.1` ～ `§2.7` deterministic business rules 已实现，并由
`run_first_tranche_pipeline`（`snapshot_loader/first_tranche_pipeline.py`）按 canonical ordering
串联为 local / single-process / in-memory pipeline；current-state 记录见
[POC Design §10.2](design/poc-design-v0.2.md)。
`Unrestricted implementation = NOT AUTHORIZED`；`§6` ～ `§9` full closure = NOT CLAIMED；
`POC success = NOT CLAIMED`。

**更早：** `Code Start Gate` —— **PASS**（8 / 8）；仅第一批 deterministic tranche = **IMPLEMENTATION AUTHORIZED**。
Canonical authority 见 [POC Design §10.1](design/poc-design-v0.2.md#implementation-ready-minimum)；minimum Architecture 见 [ADR-001](architecture/adr-001-deterministic-core.md)。
该小节 `§10.1` F 的 `Implementation status = NOT STARTED` 是 Issue #116 时点记录（**不回写**）；
tranche 的实际实现状态以 [§10.2](design/poc-design-v0.2.md) 与 `main` 上的代码 / 测试为准。
本记录随 Issue #116 PR 合入 main 生效；此前 main 授权状态不变。§6 ～ §9 JIT blockers、§10 未覆盖选择继续保留；POC success = NOT CLAIMED。

**更早：** `§1 Design Goals & Scope` Closure —— **`PASS`**（S-1 ～ S-14 全部 PASS；GSD-8 = `REGISTERED`／`AUTHORIZE`）。
四项均为 `DESIGN RESOLVED`，authoritative 记录见 [POC Design](design/poc-design-v0.2.md) **§1.18 ～ §1.20**。
`POC success = NOT CLAIMED`；本 closure 不授权 implementation，不改变 §6 ～ §10 独立状态。

**更早：** `Adapter Boundary` Closure Validation —— **`PASS`**
（`Adapter Boundary` → **`DESIGN RESOLVED`**；authoritative 记录见 [adapter-boundary.md](design/specs/data-integration/adapter-boundary.md) **§4.6.21**；
本文档**不复制** closure rationale）。

**更早：** `Final Import Contract` Closure Validation —— **`PASS`**
（`Final Import Contract` 与 `Snapshot / Import Contract overall` 均 → **`DESIGN RESOLVED`**；
authoritative 记录见 [snapshot-import-contract.md](design/specs/data-integration/snapshot-import-contract.md) **§4.3.28** ／ **§4.3.29**）。

**其余 pending areas（`§6` ～ `§9` 对应章节的 status boundary，例如
`Permission & Security` 的 `RBAC` / `Data Scope` / `Tool Permission` / `Secret Handling`）** 见 **§5 Major Design State**；
`Adapter Boundary` 的 **implementation / Architecture / §7 / §8 等后续工作未由 closure 授权**，
须以独立、明确授权的 task / PR 进行（本文档**不建立**其执行顺序）。

任务完成／合并判定见 `CONTRIBUTING.md` §7 Definition of Done 与 §5 Git & GitHub Workflow。

---

## 7. Cold Start Protocol

**Context Recovery 的 canonical 顺序由 `AGENTS.md` `## Context Recovery` 与 `CONTRIBUTING.md` §4 定义。
本文档不重定义、不替代该顺序，也不排在 Hard Rules 之前。**

在 governance 已可靠加载后，可将本文档作为**导航辅助**，用于定位 current canonical docs 与 current phase；
其余信息按需逐层加载，**够用即停** —— **仅在**出现 ambiguity / contradiction 时，才读取更深历史。

---

## 8. Context Loading Principle

- **Reference over duplication：** 引用 canonical source，**不复制**其内容。
- **Progressive context loading：** 按需逐层加载，够用即停。
- **不得**默认读取：整个 repository、整个 `POC Design v0.2`、全部历史 PR / commit / closed issue。
- Durable project memory 与 Context Recovery 原则见 `AGENTS.md` `## Context Recovery` ／ `CONTRIBUTING.md` §4，**本文档不复制**。

---

## Document Control

**Document:** Project Index
**Version:** v0.1
**Status:** `DRAFT` —— 尚未 `APPROVED` / `FROZEN`
**Doc Type:** Navigation Index —— **非** Canonical Source

- 本文档**不替代**任何 canonical source，**不构成**新的项目事实或 Decision。
- 本文档内容为 snapshot；`main` 变化后**应同步更新**，但**不得**据此改写 canonical 文档。
- 冲突时以 canonical source 为准。
