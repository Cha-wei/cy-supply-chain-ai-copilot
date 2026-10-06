# ADR-003 — Portfolio Demo Local Runtime Integration Architecture

**Status:** `ACCEPTED`（Human-approved；architecture/design only）
**Decision Authority:** Human
**Approval:** 2026-10-06，Human Decision — ADR-003 Decision Pack，`APPROVED WITH CLARIFICATIONS`（D1–D8 ＋ 10 项 binding clarifications）
**Base:** `main @ 78427dc67e9dcc1ca79342fd77e5b4ac9c6f2f48`
**UI reference:** accepted presentation head `5ecb73b05892e111b21db6e406ec879efd56dc08`，PR #241 → #242 → #243 → #244 → #245；不是 main 已合并或 runtime-connected 的声明。
**Implementation:** `NOT AUTHORIZED`；登记后必须停在 Human review，另行 Code Start。

## Context and decision authority

现有 Python deterministic、Q3、HITL、quantity override 与 Draft runtime 已存在；React Portfolio UI 的交互仍为 presentation-only。连接两者需要新增 localhost transport / cross-process boundary，不能继承 ADR-001 / ADR-002 的 in-process 授权。

Human 明确批准 D1–D8，并以十项 binding clarifications 约束 composition、AnalysisRun、stale 文案、session、解释顺序、§7、§8、validation、authority split 和 scope。本 ADR 登记该明确决定，不以 Agent 推荐代替批准。Human 同时明确：**“This approval is architecture/design authority only. It does NOT authorize runtime coding yet.”**

本 ADR 是独立限定的 interaction adaptation 决定，不改写 ADR-001 / ADR-002 的历史 Approved Decision，不改变 FROZEN business baseline。架构契约以本文为准；scoped gate 状态以 [POC Design §10.7](../design/poc-design-v0.2.md#portfolio-local-runtime-integration-gate) 为准。

## Options and disposition

| Option | Trade-off | Decision |
| --- | --- | --- |
| A — React → minimal localhost Python boundary → existing runtime | 保留 UI 与 Python 对象身份，编排层最少；新增 transport、session 和 security boundary | **HUMAN APPROVED** |
| B — Node/Vite → Python subprocess | 增加 IPC、进程生命周期、重复编排与 secret 传播风险 | NOT SELECTED |
| C — Desktop wrapper | 增加打包、平台与 bridge 依赖；无当前 desktop capability 需求 | NOT SELECTED；不选具体产品 |
| D — Pre-generated artifacts / offline presentation | 适合静态展示，不能替代实时 HITL / stale / Draft evidence | **DEFERRED from first slice；no silent fallback** |
| E — Python-rendered UI | 丢弃已接受前端，且不当然消除 transport boundary | NOT SELECTED |

## Approved architecture and authority split

`React → minimal localhost Python integration boundary → existing Python runtime`

- Frontend = presentation ＋ explicit Human intent only。
- Python integration boundary = thin local transport ＋ orchestration ＋ session ownership。
- Existing Python runtime = business truth ＋ runtime-state authority。
- Built React assets 可由 Python boundary 同源提供；Vite 仅是开发工具，不新增 Node business orchestration。
- 优先小依赖面；不冻结 stdlib server / framework、端口、endpoint、HTTP verb 或 JSON schema。ADR-001 的优先标准库不是永久 stdlib-only 规则。
- 保留 SIMULATED Portfolio Demo 定位；不批准 production architecture、ERP / PO / production write、database、durable workflow、RBAC 或 agent framework。

### D1 — Fixed SIMULATED composition

采用 Python 侧显式组装，而非 browser-supplied PhaseAHandoff 或新 serialized handoff carrier。

未来 implementation unit 可以引入 narrow Python demo-composition module。它只组装固定已批准 SIMULATED scenario，复用已登记 fixture 的语义、值、evidence relationships 及 existing loader / handoff / pipeline paths。

**Runtime/demo code 不得依赖 `tests/*`，不得把 observation script 当成 runtime architecture。** `scripts/q3_full_composition_observation.py` 的固定场景组装仅提供既有场景与证据关系参考；不能直接把其 observation lifecycle 当作服务生命周期。

必须经过现有 trusted package boundary、loader acceptance、同一个 accepted package 的证据关联与 pipeline validation；不引入新 canonical input carrier、不补 convenience defaults、不加业务规则、不暴露任意路径或 handoff 输入。浏览器不拥有业务输入 authority。

连接 UI 的 `material_code` 必须来自 Python runtime result；不得为了匹配旧 presentation fixture 重写身份。display_name 仅是 presentation label，不参与 identity、provenance 或计算。

### D2 — AnalysisRun authority and truthful stale control

| Component | Authority |
| --- | --- |
| analysis_run_id | Python composition 为每次明确新执行分配新身份，不复用旧 run identity |
| analysis_date | Python composition 显式提供；固定首个 scenario 为 `2026-10-01` |
| snapshot_package_identity | accepted package processing |
| accepted_content_view_digest | accepted content processing 的实际 digest |

初始 Demo-session initialization **显式创建第一个 AnalysisRun**。之后仅 explicit new-analysis operation 创建新 run。Browser refresh、打开 Workspace / Detail / Review、请求 Draft 均不创建新 run。不得用 browser time、wall-clock today()、package convenience defaults 或 implicit derivation 替代 authority。

新 run 必须由实际 pipeline 形成结果；失败不得伪装成成功的新 current result。相同 fixed accepted input 可具有相同 package identity / digest，仍以新 analysis_run_id 区分新执行。此时 UI 使用 **“模拟新分析运行”** 或等价真实文案；只有实际产生不同 accepted input/content view 及真实 binding 变化时，才能使用“模拟输入数据更新”。首个 slice 不因此授权新增场景。

Stale 沿用 §6 HD-4 四项 AnalysisRun binding；old review 永久 stale，新 current run 的 recommendation / supplier-risk / explanation 重新绑定，override 不继承。Re-review 使用已产生的 current run 创建新 Review，不因打开 Review 再产生 run，不复活 old review，不新增同-run 终态决定重开捷径。Rule/code-version freshness **NOT RESOLVED**。

### D3 — Single ephemeral Demo session

业务对象仅存在于**一个 Python server process 的内存**；Browser ↔ Python 仍是 cross-process architecture。多标签共享一个 Demo session，不是多用户或认证体系。

- Refresh 读取 Python authoritative state，不重算、不清空决定。
- 第二标签读取同一 session；边界对状态变更作串行一致性控制。
- 请求必须对应当前 session / run / review；stale、丢失或不匹配引用 fail closed，不把旧意图改投新 Review。
- 同一 Review 只允许一个终态决定；Approve / Override / Reject 重复、重放不能再次产生决定或复活实例。
- 超时结果不明先读取状态，不自动重发决定。
- Service restart 终止旧 session；浏览器不得恢复 HumanDecision / Draft，须明确 session loss 后重新初始化。
- 无数据库、cross-session recovery、durable approval history 或 audit claim。

### D4 — Explanation / Review / Draft ordering

`Analysis → optional Q3 completes or explicitly unavailable → open Review with fixed evidence → create internal initial Draft → Human decision → bind actual recorded HumanDecision to Draft`

不请求或 AI unavailable 均不阻塞 deterministic Human Review。Q3 可选，provider call 不能成为审核前提。Review 打开后不追加、替换或悄悄注入晚到 explanation；异步结果先核对 run binding，old explanation 不跨 run 复用。

内部 initial Draft 按既有 `open_draft(review)` 在决定前建立；之后只绑定同一 Review 实际记录的 HumanDecision，不反序创建、不从 browser JSON 重构等价对象。Approved Draft、Reject 无 approved Draft、stale 和 exact override semantics 均由 existing runtime 决定。

### D5 — Scoped localhost transport / secret contract

§7.1 credential semantics **保持不变**；这里只追加 localhost transport contract：

- Loopback only；限定允许的 Host / Origin / request context，不开放任意跨源访问。Loopback 不等于认证。
- 校验请求类型、允许字段、大小及 session/run/review 绑定；malformed、unexpected、stale requests fail closed。
- Python composition/provider boundary 从 process environment 获取 credential；不改变已有 memory-only、missing credential no-egress 与 sanitized failure 契约。
- Browser responses 不包含 credential、provider Authorization header、environment secret、provider raw response/error material；只输出批准的展示投影与 sanitized errors。
- 日志不包含 secret、原始 provider material 或完整敏感 request；不新增 audit/logging infrastructure。
- 不提供任意文件读取、通用代理或 browser-controlled provider configuration。
- 不引入 subprocess secret propagation；若未来需要，按 §7.1 S10 另行 review/approval。
- 无 production authentication / OAuth / RBAC / multi-user security / cloud deployment claim。

### D6 — §8 scoped applicability disposition

**Conflict:** §9.4 cross-process trigger 比 §10.1 D / §10.6 F 以 persistence/audit 为中心的表述更宽。
**Impact:** 不能仅以 memory-only 判定 NOT TRIGGERED，也不应为了 gate 引入数据库。
**Human-approved resolution:** 新 cross-process shape 使 **§8 applicability review = TRIGGERED**；该 scoped slice **persistence / durable audit implementation = NOT REQUIRED**，因为对象仅 Python memory、无 cross-session recovery、durable approval history 或 audit claim。

此 disposition 不是删除 trigger 或关闭 §8：**§8 overall = NOT CLOSED；rule/code-version freshness = NOT RESOLVED**。未来 persistence / recovery / audit claim 必须重新进入 gate。

### D7 — Validation obligations (future implementation)

Required：transport/integration regression；binding/session/replay regression；exact quantity transport fidelity；使用 existing projection/validator 的 Q3 evidence-fidelity regression；secret exposure/fail-closed regression。检查既有 deterministic、HITL、override、Reject、Draft、stale 行为未被 boundary 重定义。

Quantity transport 不得损失精度、经过 binary float 或增加 rounding/normalization policy；wire encoding 留给 implementation contract，业务语义仍由 Python 执行。Q3 regression 可使用既有 stub/sentinel，不在 CI 使用真实 credential/provider。

不自动要求 overall AI Eval closure、新 AI quality framework 或 hosted live campaign。**任何通过新路径的 hosted observation 都需要另行 explicit Human authorization**。本 registration 不执行 validation、不声称新链路 verified，§9.3 overall 状态不变。

### D8 — Minimal conceptual bridge surface

| Conceptual operation | Truth owner |
| --- | --- |
| Initialize / explicit new fixed analysis | boundary 组装显式上下文；loader/pipeline 产生 accepted facts 和结果 |
| Read recommendation / evidence | existing Python results；boundary 仅作受限展示投影 |
| Optional Q3 explanation | existing Q3 projection / provider / validator |
| Open Review / re-review | existing HITL；boundary 持有实例并执行 D2/D4 顺序 |
| Approve-as-recommended / approve-with-override / Reject | existing HITL / exact quantity runtime |
| Read Draft | existing Draft runtime；boundary 不重建 Draft 语义 |

不把 runtime `to_dict` inspection payload 自动冻结为 public wire schema。前端 fixture business outputs、AnalysisRun simulation、stale truth、HumanDecision construction、exact quantity business validation、Draft construction、prepared AI explanation 均退出 connected-mode authority；TypeScript 只渲染结果、收集输入、发送意图、维护局部 presentation state。Offline presentation fallback **DEFERRED**，不得在故障时静默切换。

## Consequences, reversibility and revisit

新增可独立撤销的 transport/composition 层，保留现有 core dependency direction；不把浏览器逻辑移植成第二套业务实现。服务停止即失去 session，不承诺恢复。原 presentation artifact 可独立保留，但首轮不实现 fallback mode。

新增输入场景/carrier、rule semantics、durable state、auth/RBAC、非 loopback deployment、多服务/多用户、长期基础设施、secret 传播、Q3 egress/projection 扩张或 production writes 均需重新判断适用 architecture/design gates；不得凭本 ADR 自动扩展。

## Next gate

**Architecture/design approval only. Runtime coding NOT AUTHORIZED.** 先审查本 ADR 与 scoped canonical gate registration；Human review 后另行确定 Code Start / implementation authorization。不得把 ACCEPTED ADR、scoped design resolved 或已有 runtime tests 当作新 integration implemented / tested / accepted。
