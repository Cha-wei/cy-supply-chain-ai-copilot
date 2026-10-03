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
| AI / Tool Boundary、HITL、Permission & Security、Audit & Observability、Test & AI Eval | 见对应章节 status boundary；P0 AI Explanation 的最小 runtime architecture 已由 **ADR-002 `ACCEPTED`** 登记（decision only）；**`§6` minimal Review ／ Modify（M1 override）／ Approve ／ Reject boundary ＋ read-only review projection ＋ non-canonical Human decision record ＋ stale ／ re-review contract = `DESIGN RESOLVED`（scoped；design-only，Issue #198；in-process、无 persistence ／ RBAC ／ audit ／ ERP write-back；`§6` overall 仍 `DESIGN PENDING`（`Draft` scoped semantics = `DESIGN RESOLVED`（`§6.1`，Issue #210）＋ `Draft runtime = IMPLEMENTED`（`§10.6` I，Issue #214）；remaining overall gap 指向完整 workflow ／ state machine、execution boundary **实现**、持久化与身份强制执行等）；不构成 business acceptance evidence；`§9.4` 的 scoped acceptance ／ evidence boundary = `DESIGN RESOLVED`（scoped；design-only，Issue #218 ／ `HD-HITL-ACCEPT-R2`）；其 **scoped `SIMULATED` behavioral acceptance evidence 已刻意执行并 observed conformant**（execution revision `bd17a1d`；Issue #220 ／ `HD-HITL-ACCEPT-R3`；`A-1` ～ `A-11` mapping 与 observed result 见 `§9.4`）；其 **scoped business acceptance judgement 后由 designated POC business reviewer（`Cha`）于 `2026-10-03 16:39 UTC+08:00` 作出并 canonical 登记**（Issue #222 ／ `HD-HITL-ACCEPT-R4`；judgement 逐字原文见 `§9.4`），该 judgement **只**接受 scoped HITL 行为层面的 evidence，**仍不**构成 real-customer acceptance ／ business-value evidence ／ usage ／ adoption evidence ／ production acceptance ／ `POC SUCCESS`，亦**不**使 `§6` ／ `§7` ／ `§8` closure）**；其 `§7` Secret Handling JIT prerequisite 已由 **Issue #180** 的 scoped closure 满足（`Secret Handling = DESIGN RESOLVED`（hosted P0 AI Explanation minimum only）；`§7 overall = NOT RESOLVED`；RBAC ／ Data Scope ／ Tool Permission 仍 `DESIGN PENDING`）；**`§5.3` Q3 explanation runtime core 已实现**（provider-neutral，见 `§5.20`，Issue #182）；**首个 hosted provider adapter（DeepSeek）已实现**（`§5.21`，Issue #184；implementation configuration，credential 仅从 process environment 读取，tests ／ CI 使用 stub transport；未声称 AI Eval ready ／ POC validated）；**Q3 manual opt-in live smoke entry point 已实现**（`§5.22`，Issue #186；thin、复用已 merge 的 adapter 与 validator，固定 SIMULATED projection，报告 sanitized；该记录中 `LIVE_SMOKE_NOT_RUN` 为 Issue #186 时点事实）；**DeepSeek Q3 live API contract smoke = `PASS`**（`§5.23`，Issue #188；Human 于 `main @ 31fab37` 以 process environment credential 真实执行一次 = `LIVE_SMOKE_PASS`：HTTP 200、真实 `/responses` envelope 经 merged parser、selection 经 merged validator、五个 Q3 量齐备、`uncertainty` 空、无 credential 泄漏观察；**单次观察（n = 1）**，未声称 AI Eval、provider ／ model quality、business accepted、production ready 或 `POC validated`）；**`§9.3` AI Eval = `DESIGN PENDING`**（原 `JIT-BLOCKED` 限定已由 ADR-002 runtime 实现事实推翻，见 Issue #190；`§9.4` HITL ／ business acceptance 层当时未变；该层的 scoped acceptance ／ evidence boundary 后续已由 Issue #218 ／ `HD-HITL-ACCEPT-R2` 登记为 `DESIGN RESOLVED`（scoped；design-only），其 scoped `SIMULATED` behavioral evidence 后由 Issue #220 ／ `HD-HITL-ACCEPT-R3` 刻意执行并登记为 observed conformant，其 scoped business acceptance judgement 后由 Issue #222 ／ `HD-HITL-ACCEPT-R4` 登记（designated POC business reviewer = `Cha`））；**Q3 per-observation AI Eval contract ／ evidence boundary = `DESIGN RESOLVED`**（**scoped to Q3 concern only**；`AI Eval` overall 仍 `DESIGN PENDING`；per-observation、无新增 AI Eval result enum ／ status token、无 aggregate quality gate，见 `§9.3`，Issue #192）；**Q3 full-composition hosted observation 的 operator tooling 已实现**（`scripts/q3_full_composition_observation.py`，Issue #194；固定自备 SIMULATED fixture、由 `explain_q3(...)` 驱动的完整 composition、recording transport ／ provider seam、sanitized record）；**real full-composition hosted observation = observed once（n = 1）**（`§9.3` 的 Issue #196 validation ／ current-state follow-up；Human 于 `main @ a28da0b` 以 process environment credential 显式真实执行一次，tool exit code `0`：`request_count = 1`、HTTP 200、形成 checkable structured selection、经 merged parser ／ validator 接受、由完整 `explain_q3(...)` 产出 `EXPLAINED`、deterministic recommendation 未变、无 mismatch finding；**per-observation only**，无 AI Eval verdict、无 provider ／ model quality 或 aggregate 结论） | §5 ～ §9（§5 status 见 §5.18；`§5.20` Q3 runtime record；`§5.21` DeepSeek adapter record；`§5.22` live smoke record；`§5.23` live API contract smoke validation record；§7 见 §7.1；§9 分层见 §9.1 ～ §9.4；`§9.3` Issue #192 Q3 per-observation contract ／ Issue #196 first full-composition hosted observation record；`§6` Issue #198 minimal Review ／ decision boundary record）；[ADR-002](architecture/adr-002-p0-ai-explanation-minimum-runtime.md) |
| Minimum Architecture / Code Start Gate | **ADR-001 ACCEPTED；CSG-1 ～ CSG-8 PASS**；仅第一批 deterministic tranche 授权；该 tranche 的五个 module 职责与 `§2.1` ～ `§2.7` rules 已实现并由 thin composition 串联（current state 见 §10.2）；`Unrestricted implementation` 仍未授权 | [ADR-001](architecture/adr-001-deterministic-core.md)；[POC Design §10.1](design/poc-design-v0.2.md#implementation-ready-minimum) ／ §10.2；更广泛 Architecture 仍未决定 |
| **HD-3 quantity override minimum contract** | **`DESIGN RESOLVED`（design-only；Issue #204）** —— Human Decision **HD-3 Option A′**：input ＝ exact base-10 decimal string（复用既有 exact quantity semantics；不得 binary float ／ scientific notation ／ locale ／ thousands ／ fixed scale ／ precision policy ／ round ／ quantize ／ truncate）；`override_quantity > 0`（`= 0` 与 `< 0` **INVALID**；「本次不采购」须用既有 Reject）；`approved_value >= ApplicableMOQ`（不得绕过 MOQ，且 **不**修改 `ApplicableMOQ` ／ deterministic `RecommendedPurchaseQty` ／ `MOQAdjustmentQty`）；非法值 ⇒ **decision-level fail closed**（无 decision record、无 deterministic mutation、instance 保持 review-in-progress）；不得 round ／ quantize ／ clamp ／ normalize ／ auto-adjust-to-MOQ；方向不限、**无** additional maximum cap；reason 必填；最终 decision ＝ `approve` ＋ `override_flag = true` ＋ `approved_value = Human override quantity` ＋ deterministic value preserved（**不新增** `modify` kind ／ enum ／ status）；HD-4 stale 不变。`HD-3 semantic gate = CLOSED`；**runtime = `IMPLEMENTED`（§10.5 G，Issue #208）**；Architecture re-entry ／ New ADR ／ `§7` ／ `§8` trigger = **NOT REQUIRED ／ NOT TRIGGERED** | [POC Design §10.4](design/poc-design-v0.2.md#hd-3-quantity-override-contract)；`§6` 第 5 项；`§2.5` ／ `§2.5.15`；`§4.3.25` C-5 |
| **§6 Procurement Request Draft runtime tranche（Code Start gate）** | **`REGISTERED`（scoped implementation authorization；Issue #212）** —— Human Decision **`HD-DRAFT-R1`**（Runtime Architecture ＝ **Option A**：existing Python package ＋ deterministic ／ local Draft assembly ＋ in-process ＋ ephemeral ＋ non-canonical Draft ＋ 消费既有 `ReviewInstance` ／ `AnalysisRun` ／ `HumanDecision` surfaces ＋ no new dependency ／ persistence ／ Web ／ API ／ workflow engine ／ network ／ egress ／ hosted LLM ／ credential ／ RBAC-identity-data-scope-Tool-permission enforcement ／ audit platform ／ production execution ／ ERP write；**ADR = NOT REQUIRED** —— local ／ low blast-radius ／ reversible ／ 无新长期基础设施或技术承诺，不是 waiver ／ 非 Human Decision 替代 ADR ／ 不继承 ADR-001 ／ 002 scope）＋ **`HD-DRAFT-R2`**（scoped tranche ＝ `existing ReviewInstance ／ AnalysisRun → initial ephemeral Draft（quantity = deterministic RecommendedPurchaseQty）→ applicable HumanDecision exists ⇒ Draft truthfully reflects approved_value → Reject ／ stale ／ new AnalysisRun lifecycle`，严格遵守 `§6.1` D1 ～ D5）；`Draft Runtime Code Start Gate = **PASS**（7 PASS ＋ 2 NOT TRIGGERED ＋ 1 NOT REQUIRED；0 blocking gate items）`；`Draft Runtime Tranche = **IMPLEMENTATION AUTHORIZED**`；`Draft runtime = **IMPLEMENTED**（§10.6 I，Issue #214）；IMPLEMENTED ≠ VALIDATED`；`hosted LLM wording = OUT OF SCOPE`（未来引入须重新进入 Architecture ／ egress gate，不得继承 `ADR-002`）；Architecture re-entry conditions（persistence ／ DB、Web ／ API ／ workflow engine、network ／ provider egress、hosted LLM、RBAC ／ identity ／ data-scope ／ Tool-permission enforcement、cross-process ／ service ／ multi-client、new long-lived dependency ／ infrastructure、production execution ／ ERP write、Tool protocol ／ Agent framework）见 `§10.6` E；`§7` ／ `§8` = **NOT TRIGGERED**；`§9.4` **于该 tranche ／ Issue 时点不推进**（其后由 Issue #218 登记为 `DESIGN RESOLVED`（scoped；design-only））；Required Test obligations 以 contract completeness 口径登记于 `§10.6` G | [POC Design §10.6](design/poc-design-v0.2.md#draft-runtime-code-start-gate)；`§6.1`；`§10.4` ／ `§10.5` |
| **§6 Procurement Request Draft（scoped semantic design）** | **`DESIGN RESOLVED`（scoped to Draft generation only；design-only；Issue #210，Human Decision D1 ～ D5）** —— Draft 初始使用 deterministic `RecommendedPurchaseQty`；Human decision 后：approve-as-is ⇒ `approved_value` = deterministic 值，explicit override ⇒ Human override 值（`§10.4`），reject ⇒ **不**形成 approved Draft；deterministic 值**永不**改变且**不**被写回；必须保持 `DRAFT` ＋ `RecommendedPurchaseQty ≠ ApprovedPurchaseQty ≠ PurchaseOrderQty`，不得表述为 formal Purchase Request ／ Purchase Order ／ submitted record ／ production execution；`RecommendationNeedDate` 仅作**只读原样**值，**supplier identity 不进入 Draft**，Supplier Risk Evidence 仅作 Review evidence，supplier ranking ／ selection 继续 `OUT OF SCOPE`；Draft = **per-ReviewInstance ／ per-AnalysisRun 的 ephemeral artifact**（new AnalysisRun ⇒ old Draft stale ／ non-actionable、stale 不得 approve ／ 不得复活、rejected terminal、approved 绑定对应 `HumanDecision`、override 不跨 run 继承）；generation boundary = structured business values **只**来自 deterministic result ＋ **applicable** `HumanDecision`（**when one exists**；initial Draft 可只基于 deterministic result，Human decision 尚未存在时不要求），Human decision 出现后任何 decision-derived value **只能**来自对应 `HumanDecision`，**LLM 永远仅 wording ／ presentation**；Draft = **non-canonical ／ ephemeral ／ POC runtime artifact**（非 enterprise entity ／ ERP PR ／ PO ／ persistent record ／ enterprise truth），不新增 canonical enum ／ status；**不 persistence ⇒ 不触发 §8**；`§7` ／ Architecture re-entry = **NOT TRIGGERED ／ NOT REQUIRED**（本 scoped design）；hosted LLM 生成 Draft wording 须在 implementation 前**重新判断** Architecture ／ egress（**不得**继承 ADR-002）；`Draft runtime = IMPLEMENTED（§10.6 I，Issue #214）；IMPLEMENTED ≠ VALIDATED；Unrestricted implementation = NOT AUTHORIZED` | [POC Design §6.1](design/poc-design-v0.2.md#procurement-request-draft-boundary)；`§5.15`；`§3.2` ／ `§3.6` ～ `§3.8`；`§2.5.15` |
| **Quantity override runtime tranche（Code Start gate ＋ implementation）** | **`REGISTERED` ＋ `IMPLEMENTED`（scoped tranche only）** —— Issue #206：read-only readiness assessment 完成，`Quantity Override Runtime Code Start Gate = **PASS**（7 PASS ＋ 2 NOT TRIGGERED ＋ 1 NOT REQUIRED；0 blocking gate items）`；`Quantity Override Runtime Tranche = **IMPLEMENTATION AUTHORIZED**`（**仅**该 scoped tranche）＋ **已实现**（Issue #208；`ReviewInstance.approve_with_override`，`snapshot_loader/hitl_review.py`；current state 见 `§10.5` G）；override 输入 = exact finite base-10 decimal string（既有 `parse_exact_quantity` ／ `ExactQuantity`），要求 `> 0` ＋ `>= ApplicableMOQ` ＋ reason 必填，exact `Fraction` approved_value，**无** float ／ round ／ quantize ／ clamp ／ normalize ／ auto-adjust-to-MOQ；非法值 ⇒ decision-level fail closed（无 decision、review 保持 OPEN、deterministic 不变、可重试）；decision 仍为 `approve` ＋ `override_flag = true`（**不新增** `modify` kind ／ enum ／ status）；边界 = existing Python package ＋ in-process ＋ ephemeral ＋ no new dependency ／ persistence ／ network ／ egress ／ identity-permission enforcement ／ ERP-production write；`§7` ／ `§8` / `§10` = NOT TRIGGERED ／ NOT REQUIRED；`IMPLEMENTED ≠ VALIDATED`；`Unrestricted implementation = NOT AUTHORIZED` | [POC Design §10.5](design/poc-design-v0.2.md#quantity-override-code-start-gate)（A ～ G）；`§10.4`；`§10.3`；`§6` |
| **§6 HITL reduced runtime tranche（Code Start gate ＋ implementation）** | **`REGISTERED` ＋ `IMPLEMENTED`（reduced tranche only）** —— Human Decision（`HD-HITL-R1` ／ `HD-HITL-R2`，Issue #200）：Option A runtime architecture boundary = **HUMAN APPROVED**；**不新建 ADR**（独立 Human Architecture disposition，非 ADR-001 ／ 002 scope 继承）；reduced first HITL coding tranche = **IMPLEMENTATION AUTHORIZED**（仅该 tranche）＋ runtime 已实现（Issue #202；`snapshot_loader/hitl_review.py`，in-process ／ ephemeral ／ non-canonical；current state 见 `§10.3` J）；`quantity override ／ Modify` = **`OUT OF SCOPE`（本 reduced tranche；HD-3 语义见 Issue #204 ／ `§10.4`）**；`Code Start Gate` = **PASS**（reduced tranche）；`§7` ／ `§8` JIT blocker = **NOT TRIGGERED**（严格 in-process ／ 无 persistence ／ 无 egress scope 下）；`§10.3` H 的 32 项 Required Test obligations ＋ R1 ～ R10 regression cases ＋ B1 ～ B9 explanation binding cases 已由 deterministic SIMULATED `unittest` 覆盖；explanation AnalysisRun runtime binding 已实现（`ExplanationResult.analysis_run` 由 `explain_q3` 在全部 outcome path 绑定；provider-facing projection 仍不含 AnalysisRun；无额外 egress，见 `§10.3` J D）；`IMPLEMENTED ≠ VALIDATED`；`§6` overall 仍 `DESIGN PENDING`、`§7` ／ `§8` overall 不 closure、`§9.4` **在该 tranche ／ Issue 时点仍 `JIT-BLOCKED`**；其 scoped acceptance ／ evidence boundary 后续由 Issue #218 登记为 `DESIGN RESOLVED`（scoped；design-only）；无 business acceptance ／ durable approval ／ production-readiness claim | [POC Design §10.3](design/poc-design-v0.2.md#minimal-hitl-tranche-gate)（C ／ H ／ J ／ J D）；semantic authority 见 `§6`（Issue #198 record）；`§10.1` A ～ F ／ §10.2 |

**§4 现有 0 个 `DESIGN PENDING` 设计子领域**（`Adapter Boundary` 已由 Issue #90 Closure Validation = `PASS`
登记为 `DESIGN RESOLVED`；见 [adapter-boundary.md](design/specs/data-integration/adapter-boundary.md) §4.6.21）。
**设计层 closure ≠ implemented / tested / production-ready；不得据此声称整个 §4 已实现 / 已验证，
也不得声称 `POC Design v0.2 overall` 已完成。**

---

## 6. Current Phase / Next Gate

**当前 Phase：** `POC Design v0.2`（**`DRAFT`**，尚未 `APPROVED` / `FROZEN`）。

**当前工作阶段：** **§9.4 scoped POC business acceptance judgement = 已由 Human-designated reviewer 作出并
canonical 登记** —— Human 于 Issue #222 作出 **`HD-HITL-ACCEPT-R4 = APPROVED`**：指定 POC business reviewer
（`Cha`）并授权其对 Issue #220 登记的 `A-1` ～ `A-11` scoped `SIMULATED` HITL behavioral evidence 作出一次
显式 scoped judgement；reviewer 已于 `2026-10-03 16:39 UTC+08:00` 作出该 judgement，其**逐字原文**与
project-level claim boundary 已登记于
[POC Design §9.4](design/poc-design-v0.2.md#hitl-business-acceptance)（docs-level canonical time-point record）。
该 judgement **只**接受上述 scoped HITL 行为层面的 evidence：**不**构成 real-customer acceptance ／
business-value evidence ／ usage ／ adoption evidence ／ production acceptance ／ `POC SUCCESS`；
designation 仅为 project-governance assignment（**不**建立 runtime identity ／ account ／ RBAC ／ permission
enforcement ／ durable role）。

**Current policy：** Human-approved minimum POC SUCCESS acceptance / evidence policy 已登记（Issue #224；
R1 ～ R5）；唯一 authority 见 [POC Design §9.7](design/poc-design-v0.2.md#minimum-poc-success-policy)。
policy registration ≠ evidence refresh ≠ final acceptance ≠ POC SUCCESS。

Q3 coverage / repetition / failure plan 已登记（Issue #226）；见 [§9.7 D.1](design/poc-design-v0.2.md#q3-coverage-plan)。

Q3 hosted coverage evidence 已登记（Issue #230；[§9.7 D.2](design/poc-design-v0.2.md#q3-hosted-refresh-evidence)），
仅针对 exact accepted revision `00272580…`；registration commit 不自动成为 evidence execution revision。
**Next Gate（current）：** final refresh = IN PROGRESS / NOT COMPLETE；处置剩余 applicable gaps（Windows
symlink local refresh gap 保留），取得真实 customer/process baseline 与 business-value evidence、适用 judgement /
FROZEN §17 disposition，再提交 final package 供 Human acceptance。
当前 baseline = NOT AVAILABLE，Layer 3 = BLOCKED，business-value evidence = NOT PRODUCED，POC SUCCESS = NOT CLAIMED；
§6 / §7 / §8 / §9.3 overall 不机械 closure。

保持（不变）：

```text
§6 overall                  = DESIGN PENDING
§7 overall                  = NOT RESOLVED
§8                          = NOT CLOSED
Unrestricted implementation = NOT AUTHORIZED
production execution        = OUTSIDE POC
source ／ production WRITE   = DENIED
POC success                 = NOT CLAIMED
```

**更早：** **§9.4 scoped HITL behavioral acceptance evidence = produced ／ observed** —— Human 于 Issue #220 作出
**`HD-HITL-ACCEPT-R3 = APPROVED`**，授权并完成一次 **intentional acceptance execution**：现有 `SIMULATED`
deterministic tests（`tests.test_hitl_review` ＋ `tests.test_hitl_draft`）在实际执行 revision
`bd17a1d7b11e90c3c2fe29cb00746101d25606d1` 上刻意执行并 observed conformant（`Ran 100 tests … OK`；
0 failures ／ 0 errors ／ 0 skipped），`A-1` ～ `A-11` 的 evidence mapping 与 observed result 已 canonical 登记于
[POC Design §9.4](design/poc-design-v0.2.md#hitl-business-acceptance)。executed revision 仅为 execution
provenance metadata（`≠ commit-SHA freshness binding ≠ rule-version binding ≠ cross-execution equivalence
guarantee`）；`rule ／ code-version freshness = NOT RESOLVED` 不变。

**更早：** **§9.4 scoped acceptance ／ evidence boundary design** —— Human 于 Issue #218 作出
**`HD-HITL-ACCEPT-R2 = APPROVED`**，登记 `§9.4 = DESIGN RESOLVED（scoped；design-only）`：既有四类 upper-level
evidence obligation（`O-1` ～ `O-4`）保留，并展开为 `SC-1` ～ `SC-6` subordinate scenario ／ evidence checks 与
`A-1` ～ `A-11` 最小 acceptance scenario matrix；`§7` ／ `§8` applicability ＝ `NOT a prerequisite unless
introduced`（`actor present ≠ identity verified ≠ permission enforced`；in-process decision trace ≠ durable audit
evidence）。canonical 登记见 [POC Design §9.4](design/poc-design-v0.2.md#hitl-business-acceptance)（该时点
record 的 `§9.4` scoped closure 只定义 evidence boundary、未产生 evidence 的表述保留在原记录中，不回写）。

**更早：** **§9.4 applicable §6 prerequisite scope decision** —— Human 于 Issue #216 作出
**`HD-HITL-ACCEPT-R1 = APPROVED`**：对**最小 POC acceptance** 而言，`applicable §6 design gate = SATISFIED at the
scoped POC HITL boundary`（Review ＋ quantity Modify ＋ Approve ＋ Reject ＋ Procurement Request Draft ＋
stale ／ re-review ＋ `Human Approval ≠ Production Execution`）；full HITL state machine = **Deferred**、
execution-boundary implementation = **`OUTSIDE POC`**、persistence ／ durable history = **future §8 trigger if
introduced**、identity ／ permission enforcement = **future §7 trigger if introduced**。canonical 登记见
[POC Design §9.4](design/poc-design-v0.2.md#hitl-business-acceptance)（该时点记录 `§9.4 = DESIGN PENDING ／
JIT-BLOCKED` 与 `applicable §6 prerequisite satisfied ≠ §6 overall resolved` 的区分保留在原记录中，不回写）。

**更早：** **Draft runtime tranche** —— 已实现（Issue #214；`snapshot_loader/draft_runtime.py`；`open_draft` ／
`ProcurementRequestDraft`；current state 见
[§10.6 I](design/poc-design-v0.2.md#draft-runtime-code-start-gate)）并经 Independent Review ＋ Human merge
（PR #215，merge commit = `e55994f`）；Issue #214 已 CLOSED，CI SUCCESS。initial Draft quantity ＝
deterministic `RecommendedPurchaseQty` 并显式标记 `DRAFT`；decision 存在后 quantity ＝ **该 `ReviewInstance`
实际记录的** `HumanDecision.approved_value`（binding 要求 `review.decision is decision`，look-alike ／
其它 instance 的 decision 一律拒绝；含 explicit override）；`RecommendationNeedDate` 由 review grain
**派生只读**；supplier identity **absent**；reject terminal ／ stale non-actionable ／ new `AnalysisRun` ⇒
new instance ＋ new Draft ／ override 不继承；`is_actionable` 亦尊重 underlying `ReviewInstance` 的 terminal
decision；public construction（`ProcurementRequestDraft(review=...)` ／ `open_draft`）**只**形成 initial
Draft（`decision` 为 `init=False`），且在该 review 已记录 `HumanDecision` 时 **fail closed**（`DraftError`；
initial Draft 仅在 `review.decision is None` 时合法）；decision-bearing Draft **只能**由 validated
`with_decision(review.decision, run)` 路径从 decision 前已形成的 initial Draft 产生。
`§7` ／ `§8` = **NOT TRIGGERED**；`IMPLEMENTED ≠ VALIDATED ≠ business accepted ≠ POC SUCCESS`。

**更早：** **Draft runtime Code Start gate** —— 由上述 [§10.6](design/poc-design-v0.2.md#draft-runtime-code-start-gate) 登记关闭（Issue #212）。

**更早：** **§6 Procurement Request Draft scoped semantics = `DESIGN RESOLVED`** —— Human 于 Issue #210 作出
**D1 ～ D5** 决定，canonical 登记见 [POC Design §6.1](design/poc-design-v0.2.md#procurement-request-draft-boundary)：
Draft 初始使用 deterministic `RecommendedPurchaseQty`，Human decision 后为 `approved_value`（approve-as-is ＝
deterministic 值，explicit override ＝ Human override 值），reject ⇒ 不形成 approved Draft；
`RecommendationNeedDate` 只读原样、**supplier identity 不进入 Draft**；Draft = per-ReviewInstance ／
per-AnalysisRun 的 **ephemeral** artifact；structured business values 只来自 deterministic result ＋
applicable `HumanDecision`（when one exists）；Draft = **non-canonical ／ ephemeral ／ POC runtime artifact**。

**更早：** **quantity override runtime tranche** —— 已实现（Issue #208）并经 Independent Review ＋ Human merge
（PR #209，merge commit = `3dfc61f`）；Issue #208 已 CLOSED，CI SUCCESS。current state 见
[§10.5 G](design/poc-design-v0.2.md#quantity-override-code-start-gate)（`quantity override runtime =
IMPLEMENTED`，`IMPLEMENTED ≠ VALIDATED`）。

**更早：** **quantity override runtime implementation readiness ／ Code Start gate** —— 由上述 [§10.5](design/poc-design-v0.2.md#quantity-override-code-start-gate) 登记关闭（Issue #206）。

**更早：** **§6 HITL reduced runtime tranche** —— Human 已批准 Option A runtime architecture boundary 与该 reduced
coding tranche 的 **Code Start Gate = PASS**（[POC Design §10.3](design/poc-design-v0.2.md#minimal-hitl-tranche-gate)，
Issue #200）；该 tranche 的 runtime **已实现**（Issue #202；`snapshot_loader/hitl_review.py`；current state 与
Required Gates evidence 见 [§10.3 J](design/poc-design-v0.2.md#minimal-hitl-tranche-gate)），状态为
**`IMPLEMENTED`（reduced tranche）**：explanation ↔ AnalysisRun runtime binding 已实现（provider-facing
projection 仍无 AnalysisRun，无额外 egress）；quantity override ／ Modify 不在该 tranche 范围内；
`IMPLEMENTED ≠ VALIDATED`。

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

**Current technical evidence follow-up（Issue #232）：** [POC Design §9.7 D.3](design/poc-design-v0.2.md#accepted-revision-layer2-consolidation) 登记 accepted revision `00272580adab8cb8d5843a719d261e34047b877d`、Q3 scoped minimum claim、Linux symlink gap closure、refreshed HITL judgement 与 Human-accepted Layer-2 completeness。后续 docs revisions 仅为载体；Next Gate = real baseline / Layer 3、§17 dispositions、G final Human acceptance。final refresh IN PROGRESS / NOT COMPLETE；POC SUCCESS NOT CLAIMED。此前 snapshot / time-point records 不回写。
