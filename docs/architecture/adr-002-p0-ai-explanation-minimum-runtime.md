# ADR-002 — P0 AI Explanation Minimum Runtime Architecture

**Status:** `ACCEPTED`（Human-approved；Issue #178）
**Decision Authority:** Human
**Scope:** `P0 AI Explanation` 的最小 runtime architecture only
**Base:** `main @ 390496b51488f9d29fb3d0ceabac50cce23d55ec`

**与既有决定的关系：** 本 ADR **不修改** `ADR-001` 的 Approved Decision。`ADR-001` 明确第一批
deterministic tranche 不实现 LLM ／ Agent framework；本 ADR 是其之后的**独立、范围更窄**的决定，
只覆盖 P0 AI Explanation 的最小 runtime。`§6` HITL、`§7` Permission & Security 的具体设计、
`§8` Audit & Observability、Procurement Request Draft generation 与 P1 **均不在**本 ADR 范围内。

## Context and approval evidence

`§5 AI / Tool Boundary`（`VB-28`）的 responsibility ／ behavioral boundary 已 `DESIGN RESOLVED` 且
Human-approved，但 `Implementation Status = NOT STARTED`（`§5` header ／ `§5.18`）：
framework selected、tools implemented、orchestration implemented、prompts implemented、LLM selected
**均未**发生。

first deterministic tranche 已 `IMPLEMENTED + composed + SIMULATED integration / acceptance tested`；
`§5.3` 六类 P0 问题（Q1 ～ Q6）所需的 structured facts 与 evidence **已全部由现有 deterministic
results 提供**。`§9` 的 `deterministic unit tests` 与 `integration tests` 层已 `DESIGN RESOLVED`，
`AI Eval` 仍 `DESIGN PENDING` ／ `JIT-BLOCKED`。

`§9.3` 登记的 trigger boundary 要求：在**任何** AI Eval closure ／ AI Explanation implementation
之前，必须完成**适用于该 implementation 的** Architecture Decision ＋ Human Approval。

在该 trigger 下完成的 architecture readiness ／ options analysis 结论为
`READY FOR ARCHITECTURE DECISION`，并识别出唯一实质性前置选择为 **egress ／ secret 边界**。
随后 Human 明确批准：

> **「批准 Option A — Minimal direct LLM explanation adapter ＋ A2 — Hosted LLM execution permitted。」**

本 ADR 将该批准登记为 repository authority；不是 Agent 自行选型，也不是先实施后以 ADR 事后合理化
（CONTRIBUTING `§10`）。

## Problem

- POC 的 P0 scope 含 AI Explanation（`FZ-1`「可解释」；`§5.3` 六类 P0 问题），但**当前没有任何 AI
  runtime**：仓库无 LLM 代码、无 network、`dependencies = []`。
- deterministic core 已产出解释所需的全部事实与 provenance，因此缺口**不是**业务语义，而是**缺少一个
  最小的、受控的、可逆的 runtime** 把已登记结果交给 LLM 解释。
- 若不先固定边界，实现容易自发引入 Agent Framework、Tool Protocol、Web ／ API、persistence 或
  RAG ／ Vector DB —— 这些在 `§5.19` 与 `§10` Explicit Non-Decisions 中**均未决定**。
- hosted LLM 引入 **data egress** 与 **API credential**，触及 `§10.1` D 的 `§7`
  **secret-bearing integration** blocker point。

## Constraints

继承的硬约束（本 ADR 不重新定义）：

- `§5.1` `LLM does not create business truth`；`§5.2` 受控链路（禁止 `LLM → free-form SQL →
  Production DB`）；
- `§5.5` response **meaning**（Answer ／ Evidence ／ Uncertainty・Missing Data ／ Human Decision
  Required），明确**不是** API ／ JSON ／ UI schema；
- `§5.6` evidence fidelity；`§5.7` no unsupported fact；`§5.8` partial answer；`§5.9` tool failure
  boundary；
- `§5.10` `AI Effective Permission` 不得被自然语言请求扩大；
- `§5.12` 不得由 LLM 决定的字段清单；`§5.13` Agent orchestration = **conceptual responsibility
  only**（**不得选择 Agent Framework**）；`§5.14` Controlled Tool = **capability boundary only**
  （不定义 tool names ／ API schema）；
- `§5.15` Draft 边界；
- `§3` read ／ write boundary（business data 只能经 Controlled Export 进入；`WRITE = DENIED`；
  不得直连 source system、不得以「只读」为由扩大 source access）；
- `ADR-001`（Python 本地单进程 core library、thin CLI 为外层入口、in-memory；首批不实现 Web ／
  LLM ／ Agent ／ HITL ／ RBAC ／ persistent Audit ／ real ERP ／ write-back）；
- `§10.1` C deterministic acceptance obligations 与 `§10.1` D JIT blockers；`§9.3` trigger boundary；
- 仓库当前 `dependencies = []`：引入任何依赖须按 CONTRIBUTING 的依赖与升级规则单独决定。

## Options → Trade-offs → Recommendation

| Option | Trade-offs | Disposition |
| --- | --- | --- |
| **0 — Keep current ／ no AI runtime** | 零风险、零依赖、零技术承诺；但 P0 explanation 持续未实现 | `NOT SELECTED`（作为基准评估） |
| **A — Minimal direct LLM explanation adapter**（`existing deterministic result → read-only non-canonical projection → provider-agnostic LLM seam → single LLM call → user-facing explanation`） | 最小且直击 P0；LLM 严格位于 deterministic truth 下游；in-process，无框架 ／ 协议 ／ 服务；projection 与 guardrail 可确定性测试 | **HUMAN APPROVED** |
| **A2 — Hosted LLM execution permitted**（hosted provider 作为 POC runtime option） | 无需本地推理 runtime；但引入 data egress ＋ API credential，触发 `§7` secret-bearing integration blocker | **HUMAN APPROVED（与 A 一并）** |
| **B — Lightweight orchestration without Agent framework**（显式 service ／ dispatcher ＋ capability routing） | 结构更清晰；但当前只有 6 个固定 P0 问题族，属过早抽象，且容易膨胀为事实上的 agent framework | `DEFERRED` |
| **C — Agent framework ／ graph**（如 LangGraph） | 具备未来多步 ／ multi-tool 编排能力；但为当前只读单步场景引入框架锁定，且框架语义易与 `§5.12` ／ `§5.13` 边界冲突 | `REJECTED`（当前） |
| **D — Tool-protocol-based architecture**（MCP-style tool surface） | 可复用、多客户端；但重新引入 ADR-001 有意避免的服务 ／ 协议形态，并把 `§7` Tool Permission 与 `§8` tool invocation 强行前移 | `DEFERRED`（未来 integration concern） |
| **E — Deterministic explanation renderer** | 完全确定性、可精确断言、无 egress；但**未实现** `§5.1` 赋予 LLM 的 explanation 职责与 intent understanding，单独使用低于 `VB-28` 的 P0 意图 | 不作为完整解释器选项；**本 ADR 不要求**建立完整 renderer（见 Failure boundary） |

**Recommendation：** Option A ＋ A2（已由 Human 批准）。

## Approved decision

P0 AI Explanation 的最小 runtime：

```text
existing deterministic result
        ↓
read-only non-canonical explanation projection
        ↓
provider-agnostic LLM seam
        ↓
single hosted LLM call
        ↓
user-facing explanation
```

架构约束（登记如下，后续实现不得放宽）：

- **in-process**；**single LLM call**；**provider-agnostic seam**；**不固定具体 provider ／ model**；
- **no Agent Framework**；**no LangGraph**；**no Tool Protocol ／ MCP**；**no Web ／ API**；
  **no database ／ persistence**；**no RAG ／ Vector DB**；**no HITL**；**no Draft generation**；
  **no supplier ranking ／ selection**；
- **不修改** deterministic business rules；
- **LLM 不产生 business truth**。

## Data boundary（projection）

LLM **只允许**消费：

```text
同一次 Analysis Run 的 read-only non-canonical explanation projection
```

projection：

- **只能**选择 ／ 序列化已登记 deterministic result 与 evidence；
- **不得**新计算业务值；
- **不得** invent classification ／ status；
- **不得**填补 missing data；
- **不得**无授权聚合；
- **不得**改变 provenance；
- **不得**直接发送整个 Snapshot Package；
- **不得**无差别发送整个 `FirstTranchePipelineResult`；
- **不得**发送 raw source artifact。

> `§5.3` 已登记的**可解释字段清单**构成 projection 的允许集；`§5.12` 的字段仍然**只能**由
> deterministic 侧产生。projection 是 **non-canonical runtime shape**：不新增 canonical
> field ／ entity ／ grain ／ status，也不改变任何已登记语义。

## Egress boundary（hosted LLM，A2）

- Human **明确允许** hosted LLM 作为 POC runtime option；
- **provider ／ model 为 replaceable implementation configuration**；
- **是否更换 provider 不得改变 canonical semantics**；
- hosted execution 引入 **data egress ＋ API credential**；
- egress 内容**仅限**上述 projection；不得发送整个 package ／ 整个 pipeline result ／ raw artifact；
- 真实 credential ／ secret **不得**进入 Git、canonical design、canonical record、`mapping_basis`、
  provenance 或 prompt 文本；
- 因此 **AI Explanation implementation 仍未授权开始**：必须先独立关闭最小
  `§7 Secret Handling` JIT gate（见下）。

## Provider-agnostic boundary

- seam 只暴露**一次** provider-agnostic 解释调用；provider-specific 概念（模型名、SDK 类型、
  endpoint、vendor 特有参数）**不得**进入业务侧 API、canonical semantics 或输出契约；
- 更换 provider ／ model 属 implementation configuration 变更，**不得**要求修改 `§2` ／ `§4` ／ `§5`
  的任何已登记语义，也**不得**改变 deterministic results；
- 本 ADR **不选择**具体 provider ／ model，也不规定其配置形态。

## Response boundary

- 输出只承担 `§5.5` 已登记的 response meaning：**Answer ／ Evidence ／ Uncertainty・Missing Data ／
  Human Decision Required**；
- 它是 **non-canonical runtime artifact**，**不新增** business status ／ schema；
- **不得**把 Recommendation 写成 Approved Decision，**不得**出现 approval ／ ranking ／ selection 语义。

## Failure boundary

必须存在 **deterministic fail-closed path**：

- **evidence 不足**（含 `DATA_INCOMPLETE` ／ unresolved）⇒ 明确说明**无法可靠形成结论**，并指出缺失证据；
- **LLM ／ provider unavailable** ⇒ 明确说明 **AI explanation unavailable**；
- **不得**使用旧聊天、模型记忆或 guessed value 替代当前 deterministic facts；
- fail-closed 行为必须**不依赖** LLM 才能成立。

> **本 ADR 不要求**、也不授权建立**完整** deterministic explanation renderer；未来若需要，属独立设计。

## Implementation blocker — `§7 Secret Handling` JIT gate

```text
hosted LLM execution = secret-bearing integration
  ⇒ §10.1 D 的 §7 blocker point 被触发
  ⇒ 必须先独立关闭最小 §7 Secret Handling JIT gate
  ⇒ 在此之前 AI Explanation implementation 未获授权
```

- 本 ADR **不顺带设计**完整 RBAC ／ Data Scope ／ Tool Permission ／ authentication；
- `§7` 的 `RBAC` ／ `Data Scope` ／ `Tool Permission` ／ `Secret Handling` **仍为 `DESIGN PENDING`**
  （`Read ／ Write Boundary` 保持 `DESIGN RESOLVED`）；
- 本 ADR 的存在**不**使 `§7` 或 `§5` 变为 `IMPLEMENTED` ／ `TESTED`。

## First implementation slice direction（future, not authorized here）

未来 implementation 获得授权后，优先从

```text
Q3 — Why is the recommended purchase quantity X?
```

（`§5.3` Q3）开始最小 vertical slice：它所需的全部事实已在现有 `ProcurementRecommendation` 结果中
登记，且最能检验 evidence fidelity（`ShortageQty` ／ `BasePurchaseNeed` ／ `ApplicableMOQ` ／
`MOQAdjustmentQty` ／ `RecommendedPurchaseQty` **不得**被改写）。

**本 ADR 不实现 Q3**，也不创建任何 LLM client、prompt、依赖或 eval dataset。

## Non-claims

- **不**声称 `AI Eval` ready ／ `DESIGN RESOLVED`（`§9.3` 仍 `DESIGN PENDING` ／ `JIT-BLOCKED`）；
- **不**声称 `POC VALIDATED` ／ `POC success`；
- **不**声称 `§5` implemented ／ tested；
- **不**声称 `§7` ／ `§8` closure，也**不**声称任何 permission enforcement 或 audit 已建立；
- **不**声称真实用户验证；全部现有 evidence 仍为 **`SIMULATED`**；
- **不**修改 `FROZEN` Discovery baseline；`FROZEN` `H4 = TBD` 保持不变；
- **不**修改 `ADR-001` 的 Approved Decision；
- **不**修改 `§6` ／ `§8`，**不**设计 HITL state machine。

## Consequences and revisit points

- 本决定只约束 P0 AI Explanation 的最小 runtime shape、数据边界、egress 边界与 fail-closed 行为；
  **不**选择完整生产技术栈，**不**覆盖 `§6` ～ `§8`。
- `ADR-001` 的 Python ／ in-memory ／ thin CLI 约束继续有效；本 ADR 不引入 persistence 或 service 形态。
- **实现仍未授权**：实际 coding 之前必须先关闭 `§7 Secret Handling` JIT gate 并获得相应 Human Approval。

### Revisit Conditions

1. 出现**真正多步 ／ multi-tool orchestration 需求**时，重新评估 Option B（lightweight dispatcher）
   与 Option C（Agent framework）。
2. 需要**跨进程或多客户端 tool surface** 时，重新评估 Option D（Tool Protocol ／ MCP）。
3. 需要 **persistence ／ audit** 时，重新进入 `§8` ／ 新的 Architecture Decision（本 ADR **不**为解释
   结果持久化授权）。
4. **hosted provider 的 egress ／ secret contract 未关闭前不得 implementation**（`§7 Secret Handling`
   JIT gate）。
5. 若 P0 问题族显著增长（超出 `§5.3` 六类）或要求未登记的派生量，先评估是否需要新的 canonical 语义，
   而不是让 projection 自行扩张。
