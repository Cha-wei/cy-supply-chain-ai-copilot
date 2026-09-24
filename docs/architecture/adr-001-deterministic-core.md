# ADR-001 — First Deterministic Tranche Minimum Architecture

**Status:** `ACCEPTED`（Human-approved；Issue #116）
**Decision Authority:** Human
**Scope:** 第一批 deterministic implementation tranche only
**Base:** `main @ 44da0a2a866f2e205d3b13a35c544f5c1243f2f3`

## Context and approval evidence

[Issue #116](https://github.com/Cha-wei/cy-supply-chain-ai-copilot/issues/116) 批准 IRM-1 two-stage gate，但要求真实 Architecture choice 先取得 Human Approval。
在该 Task 的 Architecture options review 后，Human 明确回复：**“Human Decision：批准 Issue #116 的 Architecture Option A。”** 本 ADR 将该批准登记为 repository authority；不是 Agent 自行选型，也不以 IRM-1 的批准替代 Architecture approval。

## Options → Trade-offs → Recommendation

| Option | Trade-offs | Disposition |
| --- | --- | --- |
| 0 — Keep current / do nothing | 无新增技术承诺，但无 minimum Architecture authority，不能通过 Code Start Gate | NOT SELECTED |
| A — Python 本地单进程 core library ＋ thin CLI | 可局部验证确定性规则，不需要服务／数据库；后续交互与部署需另行适配 | RECOMMENDED → HUMAN APPROVED |
| B — TypeScript / Node.js 本地 core library ＋ thin CLI | 可采用静态类型组织模块，但需另行落实 exact numeric representation，不能用普通浮点数替代 canonical semantics | NOT SELECTED |
| C — Web service ＋ database | 提前具备服务与持久化形态，但增加第一批不需要的接口、存储和治理设计 | NOT SELECTED |

## Approved decision

- **Python 本地单进程 core library**；**thin CLI** 为外层运行入口，core 不依赖 CLI。
- 输入为既有 **Controlled JSON Snapshot**，沿用 [Snapshot / Import Contract](../design/specs/data-integration/snapshot-import-contract.md) §4.3.22 ～ §4.3.29；不新增输入 carrier 或 ERP physical-field 假设。
- 第一批采用 **in-memory processing**；不引入 database 或 persistent business state。
- 保留 package identity、provenance、immutability、exactly-one-package linkage；内存处理不豁免任何 acceptance / integrity / reuse 规则。
- 数值实现必须保持 **canonical exact semantics**，可使用 Python `Decimal`；不得新增 rounding / precision business policy。§4.3.25 C-5 的 decimal string、禁止 binary floating-point、禁止 serializer round / quantize / truncate 等规则继续有效。不得把 Decimal 默认 context 当作业务精度；实现必须证明所用运算保持批准的 exact semantics，不能因库默认值而静默舍入。若某业务运算必须依赖尚未批准的精度／舍入选择，暂停受影响工作并升级，不能自行补全。
- **优先标准库**，但 `stdlib only` 不是永久架构规则；新增依赖仍遵循 CONTRIBUTING 的依赖与升级规则。
- 第一批不实现 Web、LLM / Agent framework、HITL、RBAC、persistent Audit、real ERP Adapter 或 production write-back。

## Dependency and interaction boundary

thin CLI 调用 application orchestration；orchestration 组合 snapshot loading、validation、canonical objects、deterministic rules 与 recommendation result。文件读取在外层，核心业务计算只消费明确输入并返回结果，不反向调用 CLI、LLM、数据库或外部系统。

首批结果为程序内 recommendation result，供 CLI 展示或测试检查；不是 Human approval、ERP request 或 purchase order。不在本 ADR 定义 public HTTP API、Tool protocol、持久结果 schema 或最终 UI。

本地运行不把任意路径自动认定为 trusted input。loader 必须服从 §4.3.28 C／D／D4 的 configured trusted package-input boundary、stable content view、strict path、raw-byte integrity 与 trusted reuse 约束；缺失／不可验证的 trust input 按既有 fail-closed 语义处理。通过 controlled SIMULATED fixtures 验证该参数化输入边界，不宣称 sender authenticity 或真实企业集成已经验证。

内存中保留 accepted input 的不可变视图与 provenance，analysis context 关联 exactly one accepted package；不得回写输入文件，不混合新旧 package，不用同 ID 表示不同内容。后续 trusted reuse 仍按 §4.3.28 C.3 重新验证 required integrity；本 ADR 不声称跨进程 durable registry、持久审计或生产级防篡改已经建立。

## Consequences and revisit points

- 此决定足以约束首批 code shape、入口、依赖方向及 persistence boundary，不选择完整生产架构。
- Python 选择仅限本 tranche；**不是 whole-project Python lock-in**。
- 引入 Web、持久业务状态、LLM / Agent、真实 ERP 或新的长期 Architecture choice 前，先补相应设计／Human Approval／ADR；不以本 ADR 推导授权。
- §6 ～ §9 的 just-in-time gates 见 [POC Design §10.1](../design/poc-design-v0.2.md#implementation-ready-minimum)。本 ADR 不关闭这些章节，也不把 §10 整体标记 resolved。
- **Option A approved ≠ production architecture approved ≠ §6 ～ §10 resolved ≠ POC SUCCESS**。
- Code Start Gate、scoped implementation authorization 与验收边界由 POC Design §10.1 canonical 管理；本 ADR 本身不代替 Gate PASS。
