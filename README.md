# cy-supply-chain-ai-copilot

供应链 AI Copilot 项目（Yunnan CY Group Supply Chain AI Copilot）。

## 项目状态

Human-approved minimum POC SUCCESS acceptance / evidence policy 已登记（Issue #224）；
canonical authority 见 [POC Design §9.7](docs/design/poc-design-v0.2.md#minimum-poc-success-policy)。
Q3 coverage plan 已登记（Issue #226；[§9.7 D.1](docs/design/poc-design-v0.2.md#q3-coverage-plan)）；
Next Gate 为 approved cases execution readiness、后续获授权的 revision-bound refresh 与真实 Layer 3 evidence，
再提交 Human final acceptance；本次未执行，business-value evidence = NOT PRODUCED，POC SUCCESS = NOT CLAIMED。

**Project Foundation + 第一批 deterministic implementation tranche（`POC Design v0.2` §10.1 B）
的模块实现与 integration 串联。**

```
POC Design v0.2                 = DRAFT
Code Start Gate                 = PASS（POC Design §10.1 E，CSG-1 ～ CSG-8）
Architecture Option A           = HUMAN APPROVED / ADR-001 ACCEPTED
First deterministic tranche     = IMPLEMENTATION AUTHORIZED（仅 POC Design §10.1 B）
First deterministic tranche     = IMPLEMENTED + composed（§10.2 current-state record，Issue #172）
Unrestricted implementation     = NOT AUTHORIZED
§6 ～ §9 full closure            = NOT CLAIMED
POC success                     = NOT CLAIMED
```

`Snapshot loader → Validation → Canonical data objects → Deterministic business rules
→ Procurement recommendation result` 五个模块职责**均已实现**，并由
`run_first_tranche_pipeline` 按 canonical ordering 串联为一条 local / single-process /
in-memory 的 deterministic pipeline：

```
Snapshot loader / import        = IMPLEMENTED（Layer-1 package acceptance）
Validation                      = IMPLEMENTED（Layer-2 canonical evidence validation；
                                  Layer 3 capability readiness 由各 runtime seam 承担）
Canonical data objects          = IMPLEMENTED（Phase A construction + Phase B policy input seam）
Deterministic business rules    = IMPLEMENTED（BR-REQUIREMENT-001 / BR-INVENTORY-001 /
                                  BR-INBOUND-001 / BR-SUBSTITUTE-001 / BR-SHORTAGE-001 /
                                  BR-PROCUREMENT-001 / BR-SUPPLIER-RISK-001）
Recommendation result           = IMPLEMENTED（procurement recommendation + supplier risk evidence）
Integration / acceptance closure= IMPLEMENTED（Issue #172；thin composition，无业务语义）
P0 AI Explanation（Q3 slice）   = IMPLEMENTED（provider-neutral runtime core；§5.20，Issue #182）
Hosted provider adapter         = IMPLEMENTED（DeepSeek；§5.21，Issue #184；implementation
                                  configuration，credential 只从 process environment 读取，
                                  tests ／ CI 一律使用 stub transport，无真实 secret）
Manual live smoke（opt-in）     = IMPLEMENTED / PASS once（§5.22 ／ §5.23，Issue #186 ／ #188；
                                  tooling 已实现；real hosted smoke 于 main @ 31fab37 真实执行
                                  一次 = LIVE_SMOKE_PASS；单次观察（n = 1），非 AI Eval、
                                  非 provider ／ model quality validation）
Q3 full-composition observation = TOOLING IMPLEMENTED / OBSERVED ONCE（§9.3，Issue #194 ／ #196；
  （opt-in operator tooling）      manual opt-in；固定 SIMULATED fixture；由 explain_q3(...) 驱动的
                                  完整 composition；real full-composition hosted observation 于
                                  main @ a28da0b 真实执行一次 = observed once（n = 1）；
                                  per-observation，无 AI Eval verdict、无 aggregate quality 结论）
§6 minimal review/decision       = DESIGN RESOLVED（scoped；Issue #198；read-only review projection ＋
  boundary（design-only）          quantity override（M1）＋ Approve ／ Reject ＋ stale contract，
                                  in-process、无 persistence ／ RBAC ／ audit ／ ERP write-back；
                                  §6 overall 仍 DESIGN PENDING（Draft scoped semantics =
                                  DESIGN RESOLVED（§6.1）；Draft runtime = IMPLEMENTED（§10.6 I）；
                                  remaining overall gap = 完整 workflow ／ state machine、
                                  execution boundary 实现等）；
                                  不构成 business acceptance evidence）
Minimal HITL runtime tranche     = CODE START GATE PASS / IMPLEMENTATION AUTHORIZED / IMPLEMENTED
  （reduced；Issue #200 ／ #202）    （scoped；Issue #200 gate，Issue #202 implementation；Option A =
                                  既有 Python package 内 minimal in-process HITL runtime、消费既有
                                  runtime result surfaces、ephemeral non-canonical artifacts、无新依赖 ／
                                  无 persistence ／ 无 DB ／ 无 Web ／ API ／ 无 network ／ egress ／
                                  无 RBAC ／ identity ／ data-scope enforcement ／ 无 audit platform ／
                                  无 production execution ／ ERP write；scope = read-only Review
                                  projection → Approve deterministic RecommendedPurchaseQty as-is →
                                  Reject → AnalysisRun stale detection ／ re-review enforcement；
                                  runtime surface = snapshot_loader/hitl_review.py；
                                  explanation ↔ AnalysisRun runtime binding = IMPLEMENTED
                                  （ExplanationResult.analysis_run 由 explain_q3 在全部 outcome path
                                  绑定；provider-facing Q3 projection 仍不含 AnalysisRun，无额外 egress）；
                                  quantity override ／ Modify = OUT OF SCOPE（本 reduced tranche；
                                  HD-3 业务语义见下方 HD-3 行）；
                                  §7 ／ §8 JIT blocker 未被该严格 scope 触发；不新建 ADR（独立 Human
                                  Architecture disposition）；Unrestricted implementation 仍未授权；
                                  IMPLEMENTED ≠ VALIDATED；无 business acceptance ／ durable approval ／
                                  production-readiness claim）
HD-3 quantity override contract    = DESIGN RESOLVED（design-only；Issue #204；HD-3 Option A′）
  （quantity override semantics）     input = exact base-10 decimal string（复用既有 exact quantity
                                  semantics；不得 binary float ／ scientific notation ／ locale ／
                                  thousands ／ fixed scale ／ precision policy ／ round ／ quantize ／
                                  truncate）；override_quantity > 0（= 0 与 < 0 INVALID；「本次不采购」
                                  用既有 Reject）；approved_value >= ApplicableMOQ（不得绕过 MOQ，
                                  且不修改 ApplicableMOQ ／ deterministic RecommendedPurchaseQty ／
                                  MOQAdjustmentQty）；非法值 = decision-level fail closed；
                                  不得 round ／ quantize ／ clamp ／ normalize ／ auto-adjust-to-MOQ；
                                  方向不限、无 additional maximum cap；reason 必填；最终 decision =
                                  approve + override_flag = true + approved_value = Human override
                                  quantity + deterministic value preserved（不新增 modify kind ／
                                  enum ／ status）；HD-4 stale 不变；Architecture re-entry ／ New ADR ／
                                  §7 ／ §8 trigger = NOT REQUIRED ／ NOT TRIGGERED；
                                  runtime = IMPLEMENTED（§10.5 G，Issue #208）；DESIGN RESOLVED ≠ IMPLEMENTED）
Quantity override runtime tranche  = CODE START GATE PASS / IMPLEMENTATION AUTHORIZED / IMPLEMENTED
  （Code Start ＋ impl；Issue #206 ／   （scoped；Issue #206 gate，Issue #208 implementation；
   #208）                              DoR ／ Code Start assessment = Code Start Gate PASS
                                  （7 PASS ＋ 2 NOT TRIGGERED ＋ 1 NOT REQUIRED；0 blocking items）；
                                  runtime surface = ReviewInstance.approve_with_override
                                  （snapshot_loader/hitl_review.py）；override 输入 = exact finite
                                  base-10 decimal string（既有 parse_exact_quantity ／ ExactQuantity），
                                  要求 > 0 ＋ >= ApplicableMOQ ＋ reason 必填，exact Fraction
                                  approved_value，无 float ／ round ／ quantize ／ clamp ／ normalize ／
                                  auto-adjust-to-MOQ；非法值 = decision-level fail closed（无 decision、
                                  review 保持 OPEN、deterministic 不变、可重试）；decision 仍为 approve
                                  ＋ override_flag = true（不新增 modify kind ／ enum ／ status）；
                                  边界 = existing Python package + in-process + ephemeral + no new
                                  dependency / persistence / network / egress / identity-permission
                                  enforcement / ERP-production write；§7 ／ §8 ／ §10 =
                                  NOT TRIGGERED ／ NOT REQUIRED；Unrestricted implementation =
                                  NOT AUTHORIZED；IMPLEMENTED ≠ VALIDATED）
Procurement Request Draft         = DESIGN RESOLVED（scoped to Draft generation only；design-only；
  （§6.1；Issue #210，D1 ～ D5）      Issue #210）：初始 quantity = deterministic RecommendedPurchaseQty；
                                  Human decision 后 = approved_value（approve-as-is ＝ deterministic 值，
                                  explicit override ＝ Human override 值），reject ⇒ 不形成 approved Draft；
                                  deterministic 值永不改变且不写回；必须保持 DRAFT ＋
                                  RecommendedPurchaseQty ≠ ApprovedPurchaseQty ≠ PurchaseOrderQty，
                                  不得表述为 formal Purchase Request ／ Purchase Order ／ submitted
                                  record ／ production execution；RecommendationNeedDate 仅只读原样、
                                  supplier identity 不进入 Draft（Supplier Risk Evidence 仅 Review evidence；
                                  supplier ranking ／ selection 继续 OUT OF SCOPE）；Draft =
                                  per-ReviewInstance ／ per-AnalysisRun 的 ephemeral artifact
                                  （new AnalysisRun ⇒ old Draft stale ／ non-actionable；stale 不得 approve ／
                                  复活；rejected terminal；approved 绑定 HumanDecision；override 不跨 run
                                  继承）；structured business values 只来自 deterministic result ＋
                                  applicable HumanDecision（when one exists；initial Draft 可只基于
                                  deterministic result），LLM 永远仅 wording ／ presentation；Draft = non-canonical ／
                                  ephemeral ／ POC runtime artifact（不 persistence ⇒ 不触发 §8）；
                                  §7 ／ Architecture re-entry = NOT TRIGGERED ／ NOT REQUIRED；
                                  Draft runtime = IMPLEMENTED（§10.6 I，Issue #214）；IMPLEMENTED ≠ VALIDATED）
Draft runtime tranche             = CODE START GATE PASS / IMPLEMENTATION AUTHORIZED / IMPLEMENTED
  （Code Start ＋ impl；Issue #212 ／   （scoped；Issue #212 gate，Issue #214 implementation；
   #214）                              HD-DRAFT-R1 Runtime Architecture = Option A =
                                  existing Python package + deterministic／local Draft assembly +
                                  in-process + ephemeral + non-canonical Draft + 消费既有
                                  ReviewInstance／AnalysisRun／HumanDecision surfaces + no new
                                  dependency／persistence／Web／API／workflow engine／network／egress／
                                  hosted LLM／credential／RBAC-identity-data-scope-Tool-permission
                                  enforcement／audit platform／production execution／ERP write；
                                  ADR = NOT REQUIRED（local／low blast-radius／reversible／无新长期
                                  基础设施或技术承诺；不是 waiver、非 Human Decision 替代 ADR、
                                  不继承 ADR-001／002 scope）；HD-DRAFT-R2 scoped tranche =
                                  existing ReviewInstance／AnalysisRun → initial ephemeral Draft
                                  （quantity = deterministic RecommendedPurchaseQty）→ applicable
                                  HumanDecision exists ⇒ Draft truthfully reflects approved_value
                                  → Reject／stale／new AnalysisRun lifecycle；严格遵守 §6.1 D1～D5；
                                  hosted LLM wording = OUT OF SCOPE（未来引入须重新进入
                                  Architecture／egress gate，不得继承 ADR-002）；§7／§8 =
                                  NOT TRIGGERED；§9.4 当时未推进（其后由 Issue #218 登记为 scoped DESIGN RESOLVED）；runtime surface =
                                  DRAFT_MARKER ／ DraftError ／ ProcurementRequestDraft ／ open_draft
                                  （snapshot_loader/draft_runtime.py）；initial Draft quantity =
                                  deterministic RecommendedPurchaseQty；decision binding =
                                  只接受该 ReviewInstance 实际记录的 HumanDecision（review.decision is
                                  decision；look-alike ／ 其它 instance 的 decision 一律拒绝）⇒
                                  approved_value 原样进入 Draft；initial Draft ／ 已记录 decision 的 review
                                  ⇒ is_actionable = False；public construction（
                                  ProcurementRequestDraft(review=...) ／ open_draft）只形成 initial Draft
                                  （decision 为 init=False），且 review 已记录 HumanDecision 时 fail close
                                  （DraftError；initial Draft 仅在 review.decision is None 时合法）；
                                  decision-bearing Draft 只能由 with_decision 从 decision 前已形成的
                                  initial Draft 产生；reject ／ stale ／ new AnalysisRun
                                  lifecycle 按 §6.1 D1～D5；Draft runtime =
                                  IMPLEMENTED（§10.6 I，Issue #214）；IMPLEMENTED ≠ VALIDATED；
                                  Unrestricted implementation = NOT AUTHORIZED）
§9.4 acceptance prerequisite       = APPLICABLE §6 DESIGN GATE SATISFIED at the scoped POC HITL boundary
  scope（design-only；Issue #216 ／   （Review ＋ quantity Modify ＋ Approve ＋ Reject ＋ Procurement Request
  HD-HITL-ACCEPT-R1）                 Draft ＋ stale ／ re-review ＋ Human Approval ≠ Production Execution）；
                                    full HITL state machine = Deferred；execution boundary = OUTSIDE POC；
                                    persistence ／ durable history = future §8 trigger if introduced；
                                    identity ／ permission enforcement = future §7 trigger if introduced；
                                    applicable §6 prerequisite satisfied ≠ §6 overall resolved；
                                    prerequisite ambiguity closed ≠ §9.4 design resolved
                                    （该时点记录保持原样；§9.4 自身 current status 见下一行）
§9.4 scoped acceptance ／             = DESIGN RESOLVED（scoped；design-only；Issue #218 ／
  evidence boundary                   HD-HITL-ACCEPT-R2）：既有四类 upper-level evidence obligation
  （design-only；Issue #218）           （O-1 ～ O-4）保留，并展开为 SC-1 ～ SC-6 subordinate scenario ／
                                    evidence checks 与 A-1 ～ A-11 最小 acceptance scenario matrix
                                    （expected outcome 只取自 canonical authority，不以 current
                                    implementation 行为为 oracle）；claim discipline 区分 HITL
                                    behavioral acceptance ／ business acceptance（须由 Human-designated
                                    POC business reviewer 显式作出）／ business-value evidence（需真实
                                    baseline，当前只定义 category ／ prerequisite）／ POC SUCCESS
                                    （GSD-3.5，不在本 unit 判断）；§7 ／ §8 = NOT a prerequisite
                                    unless introduced（actor present ≠ identity verified ≠ permission
                                    enforced；in-process decision trace ≠ durable audit evidence；
                                    §7 ／ §8 未 closure）；rule ／ code-version freshness =
                                    NOT RESOLVED 不变；§6 overall ／ §7 overall ／ §8 ／ §9.3 不变；
                                    该 design closure **当时**只定义 evidence boundary（未产生 evidence；
                                    实际 evidence production 由 Issue #220 单独授权与登记，见下一行）；
                                    不引入 KPI ／ threshold ／ baseline ／ adoption result
§9.4 scoped HITL behavioral           = produced ／ observed（intentional acceptance execution；
  acceptance evidence                  Issue #220 ／ HD-HITL-ACCEPT-R3）：在实际执行 revision
  （validation-time-point；Issue #220） bd17a1d7b11e90c3c2fe29cb00746101d25606d1 上刻意执行既有
                                      `SIMULATED` deterministic tests
                                      （python -m unittest tests.test_hitl_review tests.test_hitl_draft -v）
                                      = Ran 100 tests … OK（0 failures ／ 0 errors ／ 0 skipped；
                                      test_hitl_review 67 ＋ test_hitl_draft 33）；A-1 ～ A-11 的
                                      evidence mapping（canonical authority ／ existing test identifier ／
                                      observed result ／ evidence class ／ proves ／ does not prove）与
                                      observed result 已 canonical 登记于 §9.4；A-10 仅为当前
                                      repository ／ runtime scope 的 negative ／ structural behavioral
                                      evidence（不得外推为 production security guarantee ／ real ERP
                                      write protection ／ enterprise permission enforcement）；
                                      未新增 test ／ script ／ runtime surface；未新增 canonical entity ／
                                      enum ／ business status；executed revision 仅作 execution
                                      provenance metadata（≠ commit-SHA freshness binding ≠
                                      rule-version binding ≠ cross-execution equivalence guarantee）；
                                      本记录不构成 business acceptance ／ real-customer acceptance ／
                                      business-value evidence ／ usage ／ adoption evidence ／
                                      production acceptance ／ POC SUCCESS；business acceptance 的
                                      judgement 见下一行
§9.4 scoped POC business              = 已由 Human-designated reviewer 作出并 canonical 登记
  acceptance judgement                 （docs-level time-point record；Issue #222 ／
  （Issue #222 ／ HD-HITL-ACCEPT-R4）   HD-HITL-ACCEPT-R4）：Human 指定 POC business reviewer = Cha
                                      （仅 project-governance assignment；≠ runtime identity ／
                                      account ／ RBAC ／ permission enforcement ／ durable role），
                                       授权其对 Issue #220 登记的 A-1 ～ A-11 scoped `SIMULATED`
                                       HITL behavioral evidence 作出一次显式 scoped judgement；
                                       reviewer 于 2026-10-03 16:39 UTC+08:00 作出该 judgement，
                                       其逐字原文与 project-level claim boundary 已分开登记于 §9.4
                                       （未改写、润色、缩写、补充或推断）；该 judgement 只接受
                                       scoped HITL 行为层面的 evidence，明确 ≠ real-customer
                                       acceptance ≠ business-value evidence ≠ usage ／ adoption
                                       evidence ≠ production acceptance ≠ POC SUCCESS；
                                       未新增 runtime artifact ／ schema ／ enum ／ business status ／
                                       persistence ／ durable approval history ／ audit trail；
                                       未复用 §6 HumanDecision；§7 ／ §8 未 closure；
                                       rule ／ code-version freshness = NOT RESOLVED 不变
```

**Layer-1 Package Structural Validation（已实现范围，有意保持最小）**：

- configured trusted package-input boundary（`§4.3.28` D.3 `IG-self-C`）；
- Manifest 可读性 + strict JSON parse（`IC-8`：拒绝 BOM / duplicate key / comment /
  trailing comma / `NaN` / `Infinity`）；
- required Manifest structure / package identity / `contract_version` 可判定；
- `contract_version` exact-match（`VC-1`，supported token `"v0.2"`）；
- Manifest / dataset-entry / canonical record property 的 unknown-content reject（`UX-A`）；
- logical dataset role 的 identity / cardinality、artifact reference 与严格 literal path
  语义（`IC-1` / `IC-3` / `IC-2` / `PN-1`）；
- declared artifact existence / readability（`IC-14`）；
- artifact raw-byte SHA-256 integrity（`IG-raw` / `IG-alg-1` / `IC-22`）；
- record carrier / canonical field / `"_meta"` shape（`IC-6` / `IC-7` / Bundle 5）；
- `record_count` consistency（`IC-4` / `IC-16`）；
- acceptance-time stable view binding（Decision 10A）与 trusted reuse re-verification
  （Decision 10B `MG-2`）；
- `FR-3` collect-all 与 `not evaluable due to prerequisite` 显式区分；
- package disposition：`ACCEPTED` / `REJECTED` / `UNUSABLE`。

**Integration 串联（`§10.2`，Issue #172）**：`snapshot_loader/first_tranche_pipeline.py`
的 `run_first_tranche_pipeline` / `run_first_tranche_pipeline_from_paths` 只调用各模块**已登记**
的 public entry point，唯一 caller-supplied 语义是已登记的 in-process logical handoff
（`PhaseAHandoff`，`§4.3.31` E ／ G I-1 ～ I-9）与 configured trusted boundary；不重实现任何 rule、
不重读 raw evidence、不新增 business status。上游 Analysis Run ／ exactly-one accepted package
binding 由各消费 seam 自行校验（`F3-RB1`）。

**P0 AI Explanation（Q3 slice，`§5.20`，Issue #182）**：`snapshot_loader/explanation_q3.py` +
`explanation_seam.py` 实现 `§5.3` **Q3** 的 **provider-neutral** runtime core —— 只读 non-canonical
projection（只选取已登记量，exact payload lossless）→ provider-agnostic 单次调用 seam（provider 只做
**选取**：来自 **read-only closed registry** 的 answer kind ＋ projected fact names；只在 projection
`COMPLETE` 时调用，且 `uncertainty` 必须为空）→ 由 runtime 依据 projection **组装** 只承载 `§5.5`
四段 meaning 的 response artifact，并带 deterministic fail-closed 路径（recommendation 不完整 ⇒
不调用 provider 并显式暴露既有缺失证据；provider 抛错 ／ 选取不可用 ⇒ explanation 明确 unavailable 且
deterministic result 不变）。因此数量改写、shortage ／ recommended 角色互换、projection 之外的原因 ／
数值 ／ status、「已批准 ／ 无需人工决策」以及把已确定事实重标为 uncertain 都不可表达（由 runtime
组装与 registered relation ／ required evidence 校验保证，不依赖 provider 自觉，也不涉及 AI Eval）。
该 core **不**选择 provider ／ model、**不**做 HTTP ／ network、**不**读取 environment credential、
**不**新增依赖；tests 只用 stub provider。

**Hosted provider adapter（DeepSeek，`§5.21`，Issue #184）**：`snapshot_loader/deepseek_provider.py`
是 **provider integration ／ composition boundary**：它是唯一读取 credential 的地方（仅从 **process
environment**，环境变量名属 implementation configuration），唯一 egress 是 existing Q3 projection，
DeepSeek 返回的只是 **selection**，最终仍由 existing `validate_provider_response(...)` 判定。失败
（credential 缺失 ／ transport ／ timeout ／ 401 ／ 403 ／ 429 ／ 5xx ／ malformed envelope ／ invalid
JSON）一律 fail closed，无 retry、不切换 provider ／ credential。实现仅用 **standard library**
（`urllib.request`），**无** SDK ／ 新增 dependency；HTTP transport 可注入，tests 与 CI **不**调用
真实 DeepSeek、**不**持有真实 secret。Q1 ／ Q2 ／ Q4 ／ Q5 ／ Q6 与 AI Eval closure 仍未实现。

**Q3 manual opt-in live smoke（`§5.22`，Issue #186）**：`scripts/deepseek_q3_live_smoke.py` 是
operator 显式运行的 **thin** entry point —— 它复用已 merge 的 adapter 与已 merge 的
`validate_provider_response(...)`，**不**复制 HTTP client ／ parser ／ validator，**不**新增 retry ／
fallback。唯一 business payload 是固定 **SIMULATED** Q3 projection（五个已登记量、fake plant ／
material、无 package ／ run ／ raw evidence）。import 该脚本**不**发起 network；credential 只由
merged composition boundary 从 **process environment** 解析，该脚本**不**读取 credential value、**不**提供
`--api-key` ／ 文件输入；report 只承载 status ／ count ／ identifier 与 registered vocabulary ——
provider ／ caller 动态字符串必须先通过 narrow validation（registered `answer_kind`、安全 commit identifier、
固定 shape 的 ISO-8601 timestamp），否则记 `None` 或在任何 egress 前以 `INVALID_METADATA` 拒绝且不回显；
每次运行另做“无 permitted vocabulary 之外字符串”的自检，检出即以 `UNSANITIZED_REPORT` 失败并只以 fixed
vocabulary 重建 report。结果词汇：`LIVE_SMOKE_PASS` ／ `LIVE_SMOKE_FAIL`（minimal category）／
`LIVE_SMOKE_NOT_RUN`。automatic tests 覆盖 entry-point logic 但一律使用 stub ／ patched transport；
这不是 AI Eval。

**Real hosted smoke（`§5.23`，Issue #188）**：Human 已在本地、基于 `main @ 31fab37`、以 **process
environment** 提供 credential，显式真实执行一次该 entry point，结果为 **`LIVE_SMOKE_PASS`**
（`request_count = 1`、HTTP 200、真实 `/responses` envelope 被 merged parser 接受、selection 被 merged
validator 接受、`answer_kind = MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE`、五个 Q3 量齐备、`uncertainty`
为空、human-decision contract 保持、synthetic input 未变、sanitized report 未观察到 credential 泄漏）。
即 `real hosted integration contract observed successfully once`；执行后该 credential 已由 Human 清除。
这是**单次观察（n = 1）**：不构成 AI Eval、provider ／ model quality validation、business acceptance、
production readiness 或 `POC validated` 证据（`§5.21` ／ `§5.22` 的 “live API 未验证” ／
`LIVE_SMOKE_NOT_RUN` 为各自时点的 historical records，保持原文；current state 见 `§5.23`）。

**明确未实现 / 当前未纳入已授权实现范围**（本列表**不**承担 scope classification：
`Out of Scope ≠ P1 ≠ Prohibited ≠ Deferred`，逐项分类以 `§1` `GSD-5` classification table 为准）：
Web / API / service、Agent Framework / Tool protocol、完整 HITL state machine、
HITL execution boundary 实现、RBAC / identity / secrets、persistent Audit / durable approval history、
database / persistent business state、real ERP / SRM Adapter / source connectivity、production write-back、P1，
以及 `§6` ～ `§9` 各项 just-in-time gate。（已实现项不在此列：`quantity override / Modify` ＝ IMPLEMENTED
（`§10.5` G）；`Draft generation` scoped semantics ＝ DESIGN RESOLVED（`§6.1`）＋ runtime ＝ IMPLEMENTED
（`§10.6` I）；`§6 overall` 仍 `DESIGN PENDING`。）

**状态纪律**：`DESIGN RESOLVED` ≠ `IMPLEMENTED` ≠ `TESTED`；`IMPLEMENTED` ≠ `VALIDATED`
≠ `POC SUCCESS`。全部验证仅覆盖 **SIMULATED** fixtures，不构成真实企业集成证据。

## 目录结构

```
.
├── README.md                     # 项目说明
├── AGENTS.md                     # AI 协作约定
├── CONTRIBUTING.md               # 工程协作规范
├── pyproject.toml                # Python package metadata（无第三方运行时依赖）
├── .github/workflows/ci.yml      # Foundation checks + deterministic SIMULATED tests（Python 3.11 / 3.12）+ thin CLI check
├── snapshot_loader/              # deterministic core（第一批 tranche）
│   ├── constants.py              # 已登记的 exact literals（不 runtime 推导）
│   ├── strict_json.py            # strict JSON parse（C-1 / C-9）
│   ├── path_scope.py             # strict literal path semantics（PN-1）
│   ├── trust.py                  # trusted boundary / stable view / trusted reuse
│   ├── loader.py                 # Layer-1 acceptance gate（§4.3.28 D4）
│   ├── layer2.py                 # Layer-2 canonical evidence validation
│   ├── canonical_objects.py      # Phase A canonical object construction（§4.3.31）
│   ├── requirement_calculation.py / inventory_calculation.py / inbound_calculation.py
│   ├── substitute_calculation.py / shortage_calculation.py
│   ├── procurement_policy_input.py / procurement_recommendation.py
│   ├── supplier_risk_input.py / supplier_risk_calculation.py
│   ├── result_binding.py         # F3-RB1 Analysis Run binding（跨 result provenance）
│   ├── exact_quantity.py         # exact numeric representation（§4.3.25 C-5）
│   ├── first_tranche_pipeline.py # first-tranche composition（§10.2；无业务语义）
│   ├── hitl_review.py            # §6 reduced HITL review / decision runtime（§10.3 C / J；
│   │                             #   in-process、ephemeral、无 override 路径）
│   ├── issues.py / report.py / cli.py
│   └── __init__.py               # public runtime surface
├── tests/                        # deterministic SIMULATED unittest suite
│   └── test_hitl_review.py       # §10.3 H 的 32 项 Required Test obligations
└── docs/
    ├── discovery/                # 需求调研与探索记录
    ├── architecture/             # ADR
    └── design/                   # canonical design specs
```

## 文档

- `docs/discovery/`：需求调研、领域知识整理与方案探索记录（`FROZEN` baseline）。
- `docs/architecture/adr-001-deterministic-core.md`：第一批 deterministic tranche 的
  minimum Architecture（Python 本地单进程 core library + thin CLI）。
- `docs/design/poc-design-v0.2.md`：POC Design 阶段 Canonical Source（`DRAFT`）。
- `docs/design/specs/data-integration/`：Snapshot / Import Contract、Canonical Data Model、
  Data Dictionary、Data Validation、Master Data Mapping、Adapter Boundary 的 standalone
  canonical specs。

## 运行与测试

只使用 Python 标准库，无第三方运行时依赖。deterministic core 与全部 tests 都不发起 network ／
database ／ LLM 调用：唯一可能发起 hosted 调用的是 `snapshot_loader/deepseek_provider.py` 的
DeepSeek adapter，且只在被显式注入并调用时；tests 与 CI 一律使用 stub transport，从不调用真实
provider，也不持有真实 secret。

```bash
# 单元测试（deterministic SIMULATED fixtures）—— 在 repository root 运行
python -m unittest discover -s tests -v

# 单个测试模块
python -m unittest tests.test_layer1_acceptance -v
```

**Q3 manual opt-in live smoke（可选，仅 operator 显式运行；自动执行路径一律不产生真实 egress）：**

```bash
# 固定 SIMULATED 数据，最多 1 次 hosted 请求；credential 只从 process environment 解析
python scripts/deepseek_q3_live_smoke.py          # 文本报告
python scripts/deepseek_q3_live_smoke.py --json   # 机器可读（sanitized）报告
```

- credential 未配置时输出 `LIVE_SMOKE_NOT_RUN` 且 **零 egress**（exit code 0）；PASS 为 exit code 0，
  FAIL 为 exit code 1；
- 该脚本**没有** `--api-key` ／ 文件输入：credential 不可通过 command line 传入；
- automatic tests **会覆盖** entry-point logic（含 CLI 路径），但一律使用 **stub ／ patched transport ＋
  fake environment**：**不**使用真实 hosted credential、**不**执行真实 DeepSeek network call；CI **不**执行
  real live smoke、**不**持有真实 secret。只有 operator 的显式 real run 才可能 egress；
- `--commit-sha` 只接受 `UNKNOWN` 或 hex Git SHA（short ／ full）；timestamp 只接受固定 shape 的 ISO-8601
  instant。不安全的值在任何请求前被拒绝（`INVALID_METADATA`）、不记录、不回显（该 smoke 的 metadata
  contract 自 `§5.22` 起未改变；**不**强制 exact full merged-main SHA）；
- 报告**不**包含 credential、`Authorization` header、raw provider body 或 exception message（`§7.1`
  S-8 ／ S-11，`§5.22`）。

**Q3 full-composition hosted observation（`§9.3`，Issue #194；可选，仅 operator 显式运行）：**

```bash
# 固定 SIMULATED fixture；最多 1 次 hosted 请求；由 merged explain_q3(...) 驱动完整 composition。
# 真实 hosted 执行必须由 operator 提供精确 40 位 commit identifier：
python scripts/q3_full_composition_observation.py --case q3-c1-moq-raised --json --commit-sha <merged-main-sha>
python scripts/q3_full_composition_observation.py --case q3-c2-moq-non-binding --json --commit-sha <merged-main-sha>
```

`--case` 必填，仅允许上述两个 fixed SIMULATED cases：C1 使用 MOQ 100，C2 使用 MOQ 20；
其余 fixture inputs 相同，五量由既有 deterministic pipeline 推导。实际 relation 在 credential resolution
之前核验，不匹配时 zero egress。`case_id` 仅为 sanitized operator/evidence metadata，不进入 provider payload，
不表示 acceptance；无任意数量或 fixture-path CLI。批准 coverage policy 见 POC Design §9.7 D.1。
本 tooling adaptation 与 offline/CI PASS 不满足 hosted Q3 coverage；final revision-bound refresh 仍为 NOT RUN。

- 与 live smoke 的区别：本 tooling 走 **deterministic pipeline → procurement recommendation → Q3 projection →
  hosted provider → parser → validator → 完整 `explain_q3(...)` composition**（`§9.3` 定义的 observation unit），
  而 `§5.23` 的 smoke 只直连 adapter ＋ validator；两者都**不**在 CI 执行；
- **commit binding（HD-C）**：真实 observation 的 durable record **必须**绑定 commit identifier ——
  `--commit-sha` 必须是**精确 40 位 hex**。省略参数、`UNKNOWN`、短 SHA 或任何非法值一律 **零 egress**、
  exit code `1`、仅产出 sanitized failure record，且**不**记录／**不**回显该输入。该 identifier 由 operator
  提供：tooling 只做 **shape enforcement**（**不**调用 git ／ subprocess），**不**验证 GitHub repository
  membership 或 current main identity；Human 执行真实 observation 时必须提供**实际执行的** merged-main SHA，
  该事实由后续 validation-record review 对 GitHub authority 核验 —— 代码本身**不**保证 supplied SHA 就是
  真实 merged-main；
- exit code `0` = 已产出 truthful sanitized record（无论该次是否形成 AI behavior observation）；
  exit code `1` = 无法产出 truthful record（commit 未按要求绑定 ／ fixture 未被接受 ／ 观察到多次请求 ／
  record 未通过 sanitization）；
- canonical criterion mapping 只按**可观察证据**判定：mechanism-shape deviation（多余键 ／ 未登记 evidence
  name ／ 未登记 `answer_kind`）**不**自动等同 business-semantics violation（记 `not determined` ／
  `not expressible under the selection contract`），mechanism 与 canonical 判定不一致时保留 **mismatch
  finding**；
- missing credential ／ non-`COMPLETE` projection ⇒ **零 egress**；报告不含 raw body ／ header ／ credential ／
  机器路径；**不**新增 PASS ／ FAIL 或任何 AI Eval verdict token；
- **real full-composition hosted observation = observed once（n = 1）**：Human 已在
  `main @ a28da0b55e5956d858463ed3a14b1e68673e5388` 上以 process environment credential 显式真实执行一次
  （tool exit code `0`；执行后 credential 已立即清除），sanitized record 见 `§9.3` 的 Issue #196 follow-up；
- **该记录只支持 per-observation 事实**：本 tooling 不产生 overall AI Eval verdict，也不支持 provider ／ model
  quality、accuracy、reliability、stability、benchmark、production readiness、business acceptance、
  `POC validated` 或 `POC success`；无论累计多少 observation，仅依据 per-observation contract 都**不得**推出
  quality 结论（aggregate claim 须经未来独立 design）。`AI Eval` overall 仍 `DESIGN PENDING`。

**CI 状态（必须准确表述）：**

```
.github/workflows/ci.yml = Foundation checks
                         + deterministic SIMULATED unit tests（含 first-tranche
                           integration / acceptance tests；Python 3.11 / 3.12）
                         + thin CLI entry-point verification
```

**CI 运行范围（必须准确表述）：**

- **运行**：标准库 `unittest` 套件 —— 包含 deterministic **SIMULATED first-tranche
  integration / acceptance tests**（`tests/test_first_tranche_pipeline.py` 等同套件内
  执行）—— 以及 Foundation checks 与 thin CLI entry-point 检查；
- **不运行**：real-system / external integration（真实 ERP / SRM / source connectivity、
  跨进程或服务级集成）、lint、AI Eval、**real live smoke**（`§5.22`：CI 不执行真实 hosted 调用，
  也不持有 hosted credential；entry-point logic 由 offline stub ／ patched-transport tests 覆盖）。

`§6` ～ `§9` 的 Required Gates 仍按各自 status boundary 处理。

当前验证证据：

- **local**：`1052 tests / 2 skipped / 0 failed`（本文上方命令，SIMULATED fixtures，本机
  Python 3.14）；
- **local（manual opt-in live smoke，无 credential 时）**：process environment 未配置 hosted credential
  ⇒ `LIVE_SMOKE_NOT_RUN`（`CREDENTIAL_NOT_CONFIGURED`，`requests = 0`），即**零 egress**、
  真实 hosted 调用**未执行**（可重复的 no-credential 行为，`§5.22`）；
- **live（Human-provided，`§5.23`）**：`main @ 31fab37` 上真实 hosted smoke = **`LIVE_SMOKE_PASS`**
  一次（`request_count = 1`、HTTP 200、envelope parser ／ selection parsing ／ validator 均 PASS、
  五个 Q3 量齐备、`uncertainty` 为空、无 credential 泄漏观察）；单次观察（n = 1），
  **不**执行于 CI，**不**构成 AI Eval 或 provider ／ model quality validation；
- **live（Human-provided，第一次 full-composition hosted observation，`§9.3` ／ Issue #196）**：
  `main @ a28da0b55e5956d858463ed3a14b1e68673e5388` 上真实执行一次
  `scripts/q3_full_composition_observation.py`（tool exit code `0`；credential 仅来自 process environment，
  执行后立即清除）= **observed once（n = 1）**：`request_count = 1`、HTTP 200、真实 hosted response 形成
  checkable structured selection（`MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE`，五个 registered facts 齐备，
  `uncertainty` 空，`human_decision_required` boolean true，无多余键）、经 merged parser ／ validator 被接受、
  由完整 `explain_q3(...)` composition 产出 `EXPLAINED`、deterministic recommendation 未变、无 mismatch
  finding、`credential leakage not observed in the sanitized tooling output`。该记录**只**支持该次
  per-observation 事实：**不**是 AI Eval verdict（无 PASS ／ FAIL），**不**构成 provider ／ model quality、
  accuracy、stability、production readiness 或 business acceptance 证据，也**不**支持任何 aggregate 结论；
- **remote**：`main` push CI 在 **Python 3.11 与 3.12** 上运行同一 deterministic SIMULATED
  套件并通过，另有 Foundation checks 与 thin CLI 端到端检查。

本文**不登记**动态的 PR head SHA 或 transient Actions run id —— 二者会随每次 push 变化；
具体 current run evidence 以对应 PR / Actions run 为准。

### Manifest carrier presence（Layer-1 requirement）

依 Human Decision，POC v0.2 Layer-1 **要求 presence**：

- `"package"` block 必须包含 `snapshot_package_id` / `contract_version` / `created_at` /
  `environment` / `evidence_classification` / `completeness_state`；
- 每个 included dataset entry 必须包含 `role` / `artifact` / `record_count` /
  `provenance_ref` / `integrity_evidence`。

```
presence required ≠ semantic value validation
```

Layer 1 只判断 carrier 是否存在、是否位于 approved group / entry、以及既有 structural
shape 是否可判定；**不**判断 carrier 的 value semantic。`CF-1` 保持：
`completeness_state` 的 **presence** 是 REQUIRED，但其 **value 不参与** Layer-1 gate。

`provenance_ref` **无** value 格式约束（canonical authority 未登记其 representation）。

### CLI 用法

```bash
python -m snapshot_loader \
  --trusted-root <trusted-input-boundary-dir> \
  --package      <trusted-input-boundary-dir>/<package-dir>

# 机器可读输出
python -m snapshot_loader --trusted-root <dir> --package <dir> --json

# 接受后立即执行 trusted reuse re-verification（MG-2）
python -m snapshot_loader --trusted-root <dir> --package <dir> --reverify
```

Exit code：`0` = `ACCEPTED`；`1` = 未接受（`REJECTED` / not-evaluable）；`2` = CLI usage error。

**注意：**

- `--trusted-root` 是 **configured** trusted package-input boundary；`--package` 必须是它的
  **直接子目录**（flat directory package）。缺失 / 不可验证的 trust input ⇒ `not evaluable`
  ⇒ fail closed。
- CLI **不**创建 Analysis Run，**不**写回输入，**不**持久化任何内容。
- 未 `Accepted` 的 package **不得**作为正常 Analysis Run 的输入（`IC-18`）。

### SIMULATED fixture package 形状

```jsonc
// manifest.json
{
  "package": {
    "snapshot_package_id": "SIMULATED-PKG-0001",
    "contract_version": "v0.2",
    "created_at": "2026-01-05T08:30:00Z",
    "environment": "SIMULATED",
    "evidence_classification": "SIMULATED",
    "completeness_state": "COMPLETE"
  },
  "datasets": [
    {
      "role": "Production Requirement",
      "artifact": "requirement.json",
      "record_count": 1,
      "provenance_ref": "simulated://requirement",
      "integrity_evidence": "<64-char lowercase hex sha256 of the exact artifact raw bytes>"
    }
  ]
}
```

```jsonc
// requirement.json —— bare record array；canonical field identifier 直接作 property name
[
  {
    "plant_id": "P1",
    "material_code": "M1",
    "required_date": "2026-02-01",
    "ProductionQty": "10",
    "BOMComponentQty": "2"
  }
]
```

已知 canonical record property 是 **explicit / closed / version-bound / Human-approved**
的 exact literal 集合（`snapshot-import-contract.md` §4.3.30 B）。它**不是** runtime 从
Data Dictionary 自动推导的白名单。

## 说明

- 所有 fixture 与示例均为 **SIMULATED**，不代表真实 CY 企业生产数据。
- `_meta` 是唯一受控的 record-level carrier metadata namespace；approved member 仅
  `provenance_associations` / `observation` / `evidence` / `mapping_basis`。
- Layer 1 只判断 structural acceptance；field requiredness / logical type / range /
  business applicability / semantic resolution / capability readiness 属 Layer 2 ～ Layer 4。
