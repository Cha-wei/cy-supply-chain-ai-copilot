# Adapter Boundary

**Document / Topic:** Adapter Boundary
**Parent Design:** [POC Design v0.2](../../poc-design-v0.2.md)
**Legacy Section:** §4.6（§4.6.1 ～ §4.6.22 编号保留）
**Design Status:** `DESIGN RESOLVED`（conceptual closure）
**Implementation Status:** `NOT IMPLEMENTED`（runtime / source-specific realization）
**Canonical Authority:** 本文件是 Adapter Boundary concern 的唯一 current canonical source；parent design 保留 navigation/status 入口。
**Migration Base:** `c6f74bf15579e2777ad488bc2755b32f90839639`

<!-- BEGIN MIGRATED LEGACY §4.6 BODY -->
### 4.6 Adapter Boundary

#### 4.6.1 Adapter Boundary Design Review（Review Finding）

**Review Authority / Scope**

```
Review Type    = 独立 Design Review（只产出 Review Finding）
Review Object  = Adapter Boundary（§4 最后一个 DESIGN PENDING 子领域）
Decision Power = NONE —— 本 Review 不作出任何 Human Decision
Write Scope    = 仅 docs/design/poc-design-v0.2.md
Status Change  = NONE（Adapter Boundary 保持 DESIGN PENDING）
```

本 Review **不选择** transport ／ connector ／ mapping 表达方式，
**不创建** Adapter ／ connector ／ parser ／ serializer ／ runtime code、JSON Schema、sample package，
**不新增** canonical entity ／ field ／ enum ／ Validation Reason ／ status，
**不选择** framework ／ database ／ API technology ／ deployment stack，
**不设计** RBAC ／ Secret Handling ／ 完整 Permission model，
**不重新打开**已 `DESIGN RESOLVED` 的 Snapshot / Import Contract、Data Validation 或 Master Data Mapping。

> **Inherited Constraint 标注约定：** 若某行为已由既有 canonical constraint **唯一确定**，
> 本 Review 标记为 **`Inherited Constraint`**，**不**伪装成新的 Human Decision；
> **`Inherited Constraint` 不得被实现为可选项。**
> 若仍有多个合理方案，则**只**呈现 trade-off 与 dependency。

---

#### 4.6.2 Existing Canonical Constraints（Inherited —— 不得重新打开）

| # | Constraint | Source |
| --- | --- | --- |
| `AC-1` | Integration Pattern = **Controlled Export / Snapshot**；`READ` **只能**通过 controlled exported snapshot；`WRITE` = **`DENIED`**；`Production Write-back = OUT OF SCOPE` | `§3.1` |
| `AC-2` | POC **不直接读取 Production DB**；business data **只能**经 `Simulated Enterprise Sources → Controlled Export → POC Data Landing Zone` 进入；**不得**绕过 Controlled Export 直连源系统，**不得**以「只读」为由扩大 source access | `§3.3` ／ `§3.4` |
| `AC-3` | `Controlled Snapshot unavailable` ／ `Data Landing Zone unavailable` ⇒ **fail closed**；**不得**切换 Production direct access、**不得**让 LLM 用旧数据伪装当前事实 | `§3.10` |
| `AC-4` | `LLM does not create business truth`；business truth 只能来自 deterministic 路径（`Data Source → Deterministic Data Tool → Structured Result → LLM`） | `§3.11` ／ `§5` |
| `AC-5` | **`Source Identifier ≠ Canonical Identity`**；只有经**可靠 mapping** 后 source evidence 才能作为 canonical business evidence 使用 | `§4.5.2` |
| `AC-6` | Mapping **必须** `deterministic` ／ `explicit` ／ `traceable` ／ `reproducible`；**不得**依赖 LLM guess ／ name similarity ／ fuzzy matching ／ human-name intuition ／ silent normalization | `§4.5.2` |
| `AC-7` | **禁止** auto-reconciliation：`missing → 0`、`invalid → clamp`、unknown status → `AVAILABLE`、unknown relationship → eligible、fuzzy mapping、自动选最新 ／ 最大 ／ 覆盖 conflicting record（除非既有 Business Rule 明确允许） | `§4.4.13` ／ `§4.4.73` |
| `AC-8` | **`No Silent Exclusion`**：invalid evidence **不得**为了让计算继续而被静默丢弃；`Scope coverage` 无法可靠判断时，**不得**把「无匹配记录」解释为明确 `zero` | `§4.4.9` ／ `§4.4.8` |
| `AC-9` | 必须区分 **`source evidence absent`** 与 **`source evidence exists but canonical mapping unavailable`**；后者是 identity ／ relationship resolution problem；**不得** `mapping missing → business value = 0` | `§4.5.17` |
| `AC-10` | `SEMANTIC_UNRESOLVED` **仅在**「capability 确实需要该 semantic」**且**「当前 approved Design 无法可靠解释」**同时成立**时使用；**没有全局 source vocabulary ／ 没有 global source-field precedence 本身不是 Validation Issue** | `§4.4.95` |
| `AC-11` | Mapping **必须**属于当前 Analysis Run 绑定的 **accepted Snapshot Package context**；**不得** `P1 business evidence ＋ P2 identity mapping` 静默组成同一 Analysis Run；跨 Package **必须**作为新 Design | `§4.5.15` |
| `AC-12` | Provenance 追溯链：`source identity context → canonical identity → mapping evidence → Snapshot Package`；**logical carrier contract = `DESIGN RESOLVED`**（`P-A` 位于 record `"_meta"`，`MB-A` 与之间层） | `§4.5.14` ／ `§4.3.25` ／ `§4.5.22` |
| `AC-13` | `Stable Source Evidence Locator` = **opaque JSON string**；**必须**保持原始 identity value，**禁止** trim ／ case conversion ／ Unicode normalization ／ numeric coercion ／ heuristic interpretation | `§4.2` ／ `C-2` ／ `C-10` ／ `§4.3.28 E` |
| `AC-14` | `Mapping ／ Resolution Basis` = **optional exact JSON string**，**仅**在发生 semantic mapping ／ resolution 时要求，colocated with the relevant association | `§4.3.28 E` |
| `AC-15` | Package = **Flat Directory Package**（package-root `manifest.json` ＋ 每个 included logical dataset 一个 package-root-level JSON artifact）；`Final Import Contract` 为 **`DESIGN RESOLVED`**：acceptance gate、`PN-1` strict literal path、version dispatch、unknown-content `UX-A reject`、raw-byte SHA-256、`Decision 10A` stable-view binding | `§4.3.23` ／ `§4.3.28` ／ `§4.3.29` |
| `AC-16` | 四层 validation model；`Package Structural Failure ≠ Capability Evidence Unavailable ≠ Business DATA_INCOMPLETE`；Validation Issue Taxonomy（8 categories ／ 12 reasons）为 `REGISTERED`，**不得**新增 root reason | `§4.4.2` ／ `§4.4.3` ／ `§4.4.80` ／ `§4.4.81` |
| `AC-17` | 每个 canonical requirement 都有 **logical evidence requirement**；Capability Matrix **不**定义 physical file requirement；physical carrier = **`SOURCE-SPECIFIC`**；`loss_rate` 的 owner ／ grain 与 `ApplicableMOQ` 来源等 canonical resolution contract 均已 `DESIGN RESOLVED`，但**真实 source field 未知 ≠ Design Pending** | `§4.4.7` ／ `§4.2.16` ／ `§4.1.12` |
| `AC-18` | `effective_arrival_date` 的 **`Option D`**（source-specific mapping → canonical）× **`exactly-one-or-unresolved`** × **`Global Source-Field Precedence = NOT ADOPTED`** × **`single candidate ≠ automatically canonical`** × **`promised_date ≠ expected_arrival_date` 本身不构成 DQ Issue** × **`updated_at ≠ effective_arrival_date`** —— 均为 Human-approved current design | `§4.5.21` |
| `AC-19` | `sourcing_status` **不建立全局 source enum**；`source vocabulary → canonical eligibility condition` 为 mapping contract；`Warehouse` **不是** canonical entity（source ／ mapping ／ scope context） | `§4.5.11` ／ `§4.5.12` |
| `AC-20` | Physical carrier **design** 已关闭（FCM ／ FIC = `DESIGN RESOLVED`）；**仍未实现**的是 runtime ／ source-specific ／ **Adapter realization** | `§4.3.16` ／ `§4.3.17` |
| `AC-21` | `RBAC` ／ `Data Scope` ／ `Tool Permission` ／ `Secret Handling` = **`DESIGN PENDING`**；**不得**将真实企业 credentials 放入 Git，**不得**将 secrets 写入 prompt ／ logs；`AI Effective Permission = User Permission ∩ Data Scope ∩ Tool Permission ∩ Workflow State ∩ POC Policy`。**current-state（`Decision 7` ／ Issue #86）：** Adapter Boundary **只**登记 **Adapter ↔ `Permission & Security` 的 interface expectation**（**Option ① —— declarative access-requirement interface**：Adapter 声明执行已批准职责所需的 **minimum authorized access requirements**，**不**拥有 authorization decision ／ credential lifecycle ／ Secret Handling；required authorized access 不可用 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ **fail closed**）；`RBAC` ／ `Data Scope` ／ `Tool Permission` ／ `Secret Handling` **仍为 `DESIGN PENDING`**，`§7` **未**关闭 | `§7` ／ `§4.6.10` `Decision 7` Human Decision Record（Issue #86） |
| `AC-22` | **current approved canonical policy 对 Adapter 及相关层有明确规定的事项**（**仅**列**已被批准文本明确规定**者；**不**引用任何 Review Finding，**亦不**把「可从批准文本推导」当作已批准 ownership）：<br>• **`§3` read boundary**：POC business data **只能**经 Controlled Export 进入 Data Landing Zone；**不得**直连 source system ／ 绕过 Controlled Export（`§3.1` ／ `§3.3` ／ `§3.4`）；unavailable ⇒ fail closed（`§3.10`）<br>• **source-specific semantic mapping responsibility ＋ mapping constraints**：具体 `source value ／ field → canonical value` 由 **source-specific mapping ／ Adapter** 提供，且 mapping **必须** deterministic ／ explicit ／ traceable ／ reproducible，**不得** fuzzy ／ similarity ／ LLM 选择；Adapter **不得**重新定义 canonical semantic（逐条对应各 Human-approved mapping records：`§4.5.21` `effective_arrival_date`、`§4.5.11` `sourcing_status`、`§4.5.2` 一般原则）<br>• **`Data Validation`** = Layer 2 ～ Layer 4 conceptual semantics ＋ validation layering（`§4.4.2` ／ `§4.4.3`）<br>• **`Final Import Contract`** = acceptance ／ rejection 判定与 package disposition（`§4.3.28 F` ／ `§4.3.29`）<br>• **`FCM`** = record ／ dataset carrier shape 与 approved literals（`§4.3.25` ／ `§4.3.28 E`）<br>• **Adapter Boundary 通用职责（`Decision 1(a)`，**Issue #72 Human-approved**）**：在 **Controlled Export ／ Data Landing Zone 之后** —— 读取 ／ 提取 exported artifacts ／ source records、`exported-artifact format ／ protocol handling`、`generic source-field identification`、`source-specific mapping execution ／ realization`（`§4.6.10` Decision 1 Human Decision Record）；**明确不含** source-system connectivity ／ Controlled Export 上游链路 ／ export-side protocol ／ credentials<br>• **producer ／ Package Assembly ownership（`Decision 2`，**Issue #74 Human-approved**）**：**每个 Adapter** 拥有其 **canonical dataset artifact production**，并负责将其自身掌握的 source-derived **record-level provenance ／ evidence locator ／ `mapping_basis`** 写入**已批准 carrier**（且**不**生成 package-level acceptance ／ disposition）；**独立 `Package Assembly`（conceptual responsibility）** 拥有 `snapshot_package_id` ／ Manifest 生成、package-level artifact references ／ package organization 以及**完整、原子** Snapshot Package 的组装，并将完整 package 提交 `Final Import Contract`；`Final Import Contract` **只**验证 ／ disposition，**不生产** artifacts ／ Manifest ／ package（`§4.6.10` Decision 2 Human Decision Record）<br>• **unresolved ／ unsupported mapping 策略 ＋ Failure ／ Quarantine Interface 授权（`Decision 3`，**Issue #76 Human-approved**）**：**条件组合，以 `UF-2` ／ fail-closed 为主** —— approved missing（mapping contract 明确允许 source absence → canonical `null` ／ missing）为**正常 missing**；unresolved ／ ambiguous ／ conflicting ／ unsupported 时 Adapter 对 **affected dataset artifact fail closed**，**不产出** canonical artifact，**禁止** silent skip ／ 强制压成 `null` ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization ／ 自行扩展 canonical semantic ／ enum ／ mapping contract；该 failure context 由**已授权单独设计**的 **non-canonical Adapter Failure ／ Quarantine Interface** 承载（**不得**进入 Snapshot Package、**不得**新增现有 canonical record ／ dataset ／ `"_meta"` 字段、**不得**改现有 FCM ／ FIC carrier 与 canonical schema ／ semantic；**物理形态 ／ schema 仍未定**，**尚未** operationally available）；Package Assembly **不得**补 mapping ／ placeholder ／ 把 unresolved 当成正常 `null`（`§4.6.10` Decision 3 Human Decision Record）<br>• **source-specific mapping rule representation boundary（`Decision 4`，**Issue #78 Human-approved**）**：**Option ① —— 只登记 contract requirements，representation carrier deferred** —— 任何 source-specific mapping ／ resolution rule **必须** explicit ／ deterministic ／ traceable ／ reproducible、明确 source ／ source scope 与 logical dataset ／ canonical target、具有可审计可复现的 rule ／ revision identity 且可追溯「某 canonical result 出自哪一 approved rule ／ revision」；**不得**依赖 hidden default ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization、**不得**重新定义或扩展 canonical semantic ／ enum ／ mapping contract、**不得**建立 Global Source-Field Precedence、**不得**越过已 `DESIGN RESOLVED` 的 canonical mapping contracts；missing ／ conflicting ／ 非确定性 rule ⇒ 服从 **`Decision 3`** fail-closed；**representation carrier（YAML ／ JSON ／ DB ／ code ／ rule engine ／ service 等）与强制 `Mapping Registry` component 均不规定**，留给 Architecture ／ Implementation（`§4.6.10` Decision 4 Human Decision Record）<br>• **`Mapping ／ Resolution Basis` semantic granularity（`Decision 5`，**Issue #82 Human-approved**）**：**Option ① —— minimal rule ／ revision reference** —— `mapping_basis` 以一个 **exact JSON string** 标识本次 semantic mapping ／ resolution 使用的 **approved mapping rule identity ＋ revision identity**（可回答「该 canonical result 出自哪一 approved rule 的哪一 revision」）；**职责分离**：`evidence` 承载 Stable Source Evidence Locator、`mapping_basis` 只标识 approved rule ＋ revision、approved mapping rule 承载 deterministic mapping ／ resolution logic，**可复现性由三者组合建立**；**不要求、也不允许** `mapping_basis` 承载 source evidence ／ rule logic ／ explanation ／ rationale ／ 自由文本 ／ 新 provenance schema ／ mini-schema；**具体 string syntax ／ encoding（`rule-id@revision` ／ path-like ／ URI-like ／ namespaced ／ hash 等）留属 Architecture ／ Implementation**；保持 exact-string **不 normalize ／ trim ／ case-fold ／ Unicode-normalize ／ numeric coercion** 边界（`§4.6.10` Decision 5 Human Decision Record）<br>• **multi-Adapter governance ／ canonical semantic drift detection（`Decision 6`，**Issue #84 Human-approved**）**：**Option ② —— explicit cross-Adapter consistency obligation** —— 多个 Adapter **可以**拥有不同 source-specific mapping ／ resolution rules，但**只要**指向**相同或重叠**的 canonical entity ／ field ／ semantic ／ relationship ／ applicability scope（或其他共同影响同一 canonical interpretation 的 mapping），其 approved mapping rules ／ revisions **必须**可被检查为：与 current approved canonical contract 一致、与各自声明的 source scope ／ logical dataset ／ canonical target 一致、**不存在**未解释的 semantic contradiction，且**不依赖** implicit Adapter priority ／ first-wins ／ latest-wins ／ source priority ／ LLM ／ heuristic arbitration ／ silent normalization；consistency check 的**两个 conceptual points** = ① rule registration ／ revision change（新 rule ／ 修改 rule ／ 新 revision ／ source scope ／ canonical target 扩展在可被视为 approved ／ usable **之前**）② overlapping canonical use（多 Adapter outputs 被共同用于同一 canonical context ／ Analysis Run **之前**）；**canonical-first（`MS-1`）** 保持 authoritative —— canonical semantic 由 canonical design 定义、Adapter 只做 source-specific mapping ／ realization、**不得**引入第二套 canonical identity ／ vocabulary、**不得**建立 Global Source-Field Precedence（`MS-2 precedence-first` 仍为 `NOT COMPATIBLE`）；unresolved drift **不得** first-wins ／ latest-wins ／ Adapter priority ／ source priority ／ LLM ／ heuristic ／ silent reconciliation，**不得**由 Package Assembly 自行解释或修复，**不得**把 unresolved drift 重新解释为正常 missing ／ `null`；pre-canonical unresolved drift 与 **`Decision 3`** fail-closed 对齐（affected dataset artifact **不产出** canonical artifact，**不**为「让 Data Validation 有东西可报」而先生成错误 canonical artifact），既有 unresolved ／ consistency taxonomy **只**在真实 canonical validation context 中适用；**检测 mechanism（CI ／ test ／ registry validation ／ runtime validator ／ service ／ workflow node ／ DB ／ API ／ manual review 等）与任何 Cross-Adapter Registry ／ Drift Detector component 均不规定**，属 **Architecture ／ Implementation**（`§10`）（`§4.6.10` Decision 6 Human Decision Record）<br>• **Adapter ↔ `Permission & Security` interface expectation（`Decision 7`，**Issue #86 Human-approved**）**：**Option ① —— declarative access-requirement interface** —— Adapter Boundary **只**声明执行其已批准职责所需的 **minimum authorized access requirements ／ security dependencies**，**不**决定 Permission & Security 如何实现授权。Adapter **必须**能够声明至少以下 conceptual requirements：**resource boundary**（仅限其职责所需的 **Data Landing Zone-side** exported artifacts ／ resources）；**operation ／ capability**（完成职责所需的最小 capability；**不得**扩展为 Production write）；**logical data scope**（所需 logical dataset ／ source scope ／ applicable exported-artifact scope）；**security dependency**（运行该 Adapter 需要一个满足上述要求的 **authorized access context**）；**secret dependency（when applicable）**（若未来实现机制确实需要 credential ／ secret，Adapter **只**声明该 dependency ／ requirement 存在，**不**声明 secret value，**不**选择其 provisioning ／ storage ／ retrieval 机制）—— 该声明的语义是「Adapter 需要什么条件才能合法执行」，**不是**「Adapter 有权自行授予或取得什么权限」；**不赋予 Adapter：** RBAC policy、user ／ role definition、Data Scope policy ／ approval、Tool Permission policy ／ approval、authorization decision、authentication mechanism、identity ／ principal model、credential issuance ／ provisioning ／ storage ／ retrieval ／ delivery、secret rotation ／ lifecycle ／ secret manager selection、policy evaluation、permission escalation、emergency ／ break-glass policy（上述仍由 `§7` 后续设计负责，**不**因本 Decision 标为 `DESIGN RESOLVED`）；required authorized access 未提供 ／ 不满足所需 resource ／ scope ／ capability ／ 已失效 ／ 无法被可靠确认 ⇒ Adapter **必须 fail closed ／ do not proceed**，**不得**自行扩大 Data Scope、**不得**自行提升 Tool Permission、**不得**改用更高权限身份、**不得**猜测或选择替代 credential、**不得**使用未批准 credential、**不得**绕过 Permission & Security policy、**不得**绕过 Data Landing Zone、**不得** fallback 到 source-system direct access ／ Production DB ／ API、**不得**把缺少授权伪装成正常 data missing；该 failure 是 **Permission ／ Security dependency failure**，**不得**被重新解释为 canonical mapping unresolved ／ canonical missing ／ `null` ／ business `DATA_INCOMPLETE` ／ Data Validation reason ／ Adapter mapping conflict ／ package disposition，其 reporting ／ audit ／ operational handling 留给 `§7` ／ `§8` ／ Architecture ／ Implementation；**不扩展** `Decision 3` 的 non-canonical Failure ／ Quarantine Interface 的 schema ／ responsibility；**secret boundary**：**不得**在 canonical design 写真实 username ／ password ／ token ／ API key ／ secret value，**不得**在 mapping rule 嵌入真实 credential ／ secret，**不得**在 `mapping_basis` ／ provenance ／ canonical record ／ `"_meta"` 承载 credential ／ secret，**不得**把 secret 写入 prompt ／ log ／ Git，**不选择** Vault ／ Secrets Manager ／ Kubernetes Secret ／ env var ／ OAuth ／ service account ／ API key 等具体 mechanism；该 requirement **严格限于 Data Landing Zone ／ Controlled Export 之后**，**不含** source-system ／ ERP ／ SRM ／ Production DB credentials、export-side protocol credentials、Controlled Export 上游身份、Production API write credential（若要 Adapter 直连 source system 须另走 Human-approved `§3` design change）；**interface expectation ≠ injection mechanism**：**不选择** security layer injection ／ pull ／ push credential delivery ／ broker ／ sidecar ／ environment injection ／ secret mount ／ token exchange ／ identity federation ／ service account ／ policy agent ／ auth middleware ／ API gateway 或任何具体 security runtime mechanism；existing **`AI Effective Permission` invariant 保持不变**（Adapter 的 declared requirement **不能**扩大 effective permission）（`§4.6.10` Decision 7 Human Decision Record）<br>• **Adapter Boundary closure policy（`Decision 8`，**Issue #88 Human-approved**）**：**Accept `A-1` ～ `A-14` ＋ authorize dedicated Closure Design Change ＋ conditional status advancement；no blanket runtime implementation authorization** —— `A-1` ～ `A-14` = **Human-approved mandatory minimum closure criteria**（`§4.6.9`）；`A-15` ／ `A-16` 保持 **POC DESIGN OBJECTIVE**（必须评估、non-blocking）；**Decision 8 本身不关闭** `Adapter Boundary`（该 Decision registration 时点仍 **`DESIGN PENDING`**）—— 必须先由 **Dedicated Adapter Boundary Closure Design Change PR** 以 current canonical design 为准对 `A-1` ～ `A-14` 逐项做 **PASS ／ FAIL** verification、对 `A-15` ／ `A-16` 做非阻塞评估、并执行 `A-13` selected-decision composition check（确认 `Decision 1` ～ `7` 的组合与 `§3` ／ `§4.3` ／ `§4.4` ／ `§4.5` 之间无未登记冲突）；**只有全部 mandatory criteria PASS** 才允许 `DESIGN PENDING → DESIGN RESOLVED`，任一 FAIL 则保持 `DESIGN PENDING`，**不得**用 Exception ／ waiver ／ reviewer opinion 强行关闭；该状态转换**不表示** IMPLEMENTED ／ TESTED ／ production-ready ／ real ERP ／ source field known ／ runtime Adapter 存在 ／ mapping registry 存在 ／ `mapping_basis` concrete string syntax 已选 ／ cross-Adapter drift detection mechanism 已实现 ／ `Permission & Security` overall 已完成 ／ Failure ／ Quarantine Interface runtime 已实现 ／ Architecture ／ ADR 已完成 ／ POC Design overall APPROVED ／ FROZEN；Failure ／ Quarantine 的 physical shape ／ schema ／ storage ／ API ／ runtime realization 与 `§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling **仍为未完成 ／ `DESIGN PENDING`**，但**不自动阻止** Adapter Boundary **conceptual closure**（`Decision 8` 8.5 ／ 8.6）；**no blanket implementation authorization**（8.8）：Adapter runtime code ／ connector ／ parser ／ serializer ／ mapping registry ／ mapping rule storage ／ Failure ／ Quarantine implementation ／ drift detector ／ runtime validator ／ auth middleware ／ credential ／ secret mechanism ／ database ／ API ／ framework ／ deployment ／ source-system integration **均未**由此授权；Architecture ／ Implementation deferrals（mapping rule representation carrier、`mapping_basis` concrete string syntax ／ encoding、cross-Adapter consistency detection mechanism、Package Assembly runtime shape、Failure ／ Quarantine physical realization、auth ／ credential ／ secret-delivery mechanism、framework ／ database ／ API ／ deployment、ADR）**保持**（`§4.6.10` Decision 8 Human Decision Record）<br><br>**授权来源区分（**不得混同**）：** 上述 **`§3` ／ `§4.3` ／ `§4.4` ／ `§4.5` 条目为历史 **`Inherited Constraint`**；**`Decision 1(a)` ／ `Decision 1(b)`（Issue #72）、`Decision 2`（Issue #74）、`Decision 3`（Issue #76）、`Decision 4`（Issue #78）、`Decision 5`（Issue #82）、`Decision 6`（Issue #84）、`Decision 7`（Issue #86）与 `Decision 8`（Issue #88）为本层 newly Human-approved registered policy** —— 二者同属 **current approved policy**，但**后者不得**被表述为 inherited constraint；`Decision 3` 的 fail-closed policy 与 interface 授权、`Decision 4` 的 contract requirements 与 carrier deferral、`Decision 5` 的 `mapping_basis` semantic 与 syntax deferral、`Decision 6` 的 cross-Adapter consistency obligation 与 canonical-first governance、`Decision 7` 的 declarative access-requirement interface expectation、`Decision 8` 的 closure criteria acceptance 与 closure gate authorization 均属 **registered**，**不是** inherited | `§3.1` ／ `§3.3` ／ `§3.4` ／ `§3.10` ／ `§4.3.25` ／ `§4.3.28` ／ `§4.3.29` ／ `§4.4.2` ／ `§4.4.3` ／ `§4.5.2` ／ `§4.5.11` ／ `§4.5.21` ／ `§4.6.10`（`Decision 1` ／ `Decision 2` ／ `Decision 3` ／ `Decision 4` ／ `Decision 5` ／ `Decision 6` ／ `Decision 7` ／ `Decision 8` HD Records） |
| `AC-23` | **Adapter Boundary 的 ownership 列表**只在其**已获批准的部分**才成立；未获批部分**不得**写成 inherited：<br>① `RIF-11` 属 PR #65 的 **review-only Review Finding**，**不构成**已批准 policy（`AB-01`）；<br>② **仅凭「可由批准文本推导」不得**把 Adapter 的通用职责写成 inherited（`AB-05`）；<br>③ **`Decision 1(a)` 已于 Issue #72 获 Human Approval**，因此 `4.6.5 A` 中的**读取 ／ 提取、format ／ protocol handling、generic source-field identification、source-specific mapping execution** 现为 **registered**（见 `AC-22`）；<br>④ **`Decision 2` 已于 Issue #74 获 Human Approval**，因此 **producer ownership 与 `Package identity` ／ `manifest` generation** **不再属于未获批项** ⇒ 已 **registered**（见 `AC-22`）。<br>⑤ **`Decision 3` 已于 Issue #76 获 Human Approval**，因此 **unresolved ／ unsupported mapping 策略**（条件组合，以 `UF-2` ／ fail-closed 为主）与 **Adapter Failure ／ Quarantine Interface 的授权** 已 **registered**；该 interface 为 **non-canonical**，**不得**进入 Snapshot Package、**不得**新增现有 carrier 字段、**不得**改变 canonical schema ／ semantic，其**物理形态 ／ schema 仍未定**（**尚未** operationally available）。<br>⑥ **`Decision 4` 已于 Issue #78 获 Human Approval**，因此 **source-specific mapping rule 的 contract requirements**（explicit ／ deterministic ／ traceable ／ reproducible；source scope ／ canonical target ／ rule ＋ revision identity；禁 hidden default ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization）与 **representation carrier deferral**（**不**规定 configuration ／ registry ／ code ／ DB ／ rule engine ／ service，**不创建**强制 `Mapping Registry` component）已 **registered**。<br>⑦ **`Decision 5` 已于 Issue #82 获 Human Approval**，因此 **`mapping_basis` 的语义粒度**已 **registered**（**Option ① minimal rule ／ revision reference** —— 只标识 approved mapping rule identity ＋ revision identity；`evidence` ／ `mapping_basis` ／ approved mapping rule 职责分离；不承载 evidence ／ rule logic ／ explanation ／ rationale ／ mini-schema）；**具体 string syntax ／ encoding 属 Architecture ／ Implementation**，**不属**本层待决。<br>⑧ **`Decision 6` 已于 Issue #84 获 Human Approval**，因此 **multi-Adapter governance ／ canonical semantic drift detection** 的边界已 **registered**（**Option ② —— explicit cross-Adapter consistency obligation** —— canonical-first（`MS-1`）保持 authoritative；多 Adapter 指向**相同或重叠**的 canonical entity ／ field ／ semantic ／ relationship ／ applicability scope 时，其 approved mapping rules ／ revisions **必须**满足显式一致性义务；consistency check 的两个 conceptual points = **rule registration ／ revision change** 与 **overlapping canonical use**；**禁止** Adapter priority ／ source priority ／ first-wins ／ latest-wins ／ LLM ／ heuristic ／ silent reconciliation，**不得**由 Package Assembly 自行解释或修复；unresolved drift 与 `Decision 3` fail-closed 对齐）；**具体 detection mechanism 属 Architecture ／ Implementation**，**不属**本层待决。<br>⑨ **`Decision 7` 已于 Issue #86 获 Human Approval**，因此 **Adapter ↔ `Permission & Security` 的 interface expectation** 已 **registered**（**Option ① —— declarative access-requirement interface** —— Adapter **只声明**执行已批准职责所需的 minimum authorized access requirements ／ security dependencies（resource boundary ／ operation ／ logical data scope ／ authorized access context ／ secret dependency），**不**拥有 RBAC ／ Data Scope ／ Tool Permission ／ authorization decision ／ credential lifecycle ／ Secret Handling；required authorized access 不可用 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ **fail closed ／ do not proceed**，禁 privilege expansion ／ 替代 credential 猜测 ／ policy bypass ／ source-system fallback；Permission ／ Security dependency failure **不得**伪装成 canonical missing ／ mapping unresolved ／ `DATA_INCOMPLETE` ／ Data Validation reason ／ package disposition，且**不扩展** `Decision 3` Failure ／ Quarantine Interface；**injection ／ broker ／ secret manager ／ auth runtime mechanism 属 Architecture ／ Implementation**，`§7` 各 remaining item 仍 `DESIGN PENDING`）。<br>⑩ **`Decision 8` 已于 Issue #88 获 Human Approval**，因此 **Adapter Boundary closure policy** 已 **registered**（**Accept `A-1` ～ `A-14` 为 mandatory minimum closure criteria ＋ 授权 Dedicated Adapter Boundary Closure Design Change PR ＋ 条件性状态转换；无 blanket runtime implementation authorization**）；`A-15` ／ `A-16` 保持 **non-blocking design objectives**；**本 Decision 不推进状态** —— `Adapter Boundary` 仍 `DESIGN PENDING`，closure 与 `DESIGN RESOLVED` 只能由该 Dedicated Closure PR 在全部 mandatory gate `PASS` 后登记。<br>**仍未决者：** 本层**已无**剩余 Human Decision（`Decision 1` ～ `Decision 8` 均已登记）；**该 Dedicated Closure Gate 已执行（Issue #90 Closure Validation）：** `A-1` ～ `A-14` **全部 PASS** ⇒ 已登记 `Adapter Boundary = DESIGN RESOLVED`（见 **`§4.6.21`**；任一 FAIL 本应保持 `DESIGN PENDING`，本次无 FAIL）。**仍未完成但非本层 closure blocker 者：** **已授权但尚未设计的 Failure ／ Quarantine Interface 形态**、`§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 的**具体设计**、以及 **mapping rule representation 与 `mapping_basis` string syntax 的 Architecture ／ Implementation 选型**（属 `§10` ／ 实现）；**仍为本层 finding ／ option 者**交 Human Decision | `§4.3.28`（Bundle 1 ～ 6 登记范围）＋ 本 Review `AB-01` ／ `AB-05` ＋ `§4.6.10`（`Decision 1` ／ `Decision 2` ／ `Decision 3` ／ `Decision 4` ／ `Decision 5` ／ `Decision 6` ／ `Decision 7` ／ `Decision 8` HD Records） |

**本 Review 未发现**上述约束之间存在冲突；`AC-18` ／ `AC-19` 是**已经唯一确定**的行为，
**不得**在本层被重新打开为自由选项。
**`AC-22` 只列已批准部分；任何超出 `AC-22` 的 ownership 主张必须按 `AC-23` 走 Human Decision。**

---

#### 4.6.3 Exact Review Scope

**In scope（仅以下问题）：**

1. Adapter owns ／ does not own 什么（含与 `Snapshot / Import Contract`、`Data Validation`、
   `Master Data Mapping`、`Field Carrier Mapping`、`Permission & Security` 的边界）
2. Adapter 的**输入**与**输出 conceptual contract**
3. source → canonical mapping 的 **deterministic ／ fail-safe** 要求
4. missing ／ ambiguous ／ unsupported source evidence 的**表达归属**（Adapter failure vs Data Validation）
5. `Stable Source Evidence Locator` 与 `Mapping ／ Resolution Basis` 的 **carrier obligation**（producer-neutral），
   以及**谁**是该 metadata 的 producer
6. 多 source ／ 多 Adapter 下的 **canonical semantic drift** 防护
7. 哪些问题**必须本层关闭**，哪些**明确留给** `Permission & Security` ／ `Architecture` ／ Implementation
8. Adapter Boundary 的 **minimum closure criteria** 候选

**Out of scope（属其他层或实现）：**

- 直连 Production DB ／ API 或任何 Production write
- 真实 ERP table ／ column ／ proprietary field 选择；framework ／ database ／ API technology ／ deployment stack
- Adapter ／ connector ／ parser ／ serializer ／ runtime code、JSON Schema、sample package
- RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling ／ 完整 Permission model
- canonical entity ／ field ／ enum、`BR-*`、Validation Taxonomy 的修改
- 重新打开 `Snapshot / Import Contract`、`Data Validation`、`Master Data Mapping`
- 真实 credentials、sample production integration、runtime artifact

---

#### 4.6.4 Critical Scenarios

`性质` 列：**`IC`** = behavioural outcome 已被 inherited；**`IC + open`** = outcome inherited、
**表述 ／ 报告细节**仍开放；**`open`** = 真正待 Human Decide。

**A. Input side**

| # | Scenario | 既有约束要求的行为 | 性质 |
| --- | --- | --- | --- |
| `AS-1` | Controlled Export ／ Snapshot 产物 unavailable，或 Data Landing Zone 不可用 | **fail closed**（`AC-3`）；**不得**改走 Production direct access，**不得**用旧数据伪装当前事实 | **`IC`** |
| `AS-2` | 被要求以「只读」为理由直接查询源系统 ／ 绕过 Controlled Export | **拒绝**（`AC-1` ／ `AC-2`）；source access **不得**扩大 | **`IC`** |
| `AS-3` | 同一 canonical logical dataset 的 source artifact 采用 **source-specific physical shape**，**且**某 producer 提交其 mapped result 作为 canonical artifact | **producer-neutral invariant**：该 canonical artifact **必须**在不改变 canonical semantic 的前提下与对应 logical dataset 一致（`AC-5` ／ `AC-6`）；**谁**是 producer ⇒ **open**（`P-2` ／ **Decision 2** ／ `ADEP-11`） | **`IC`**（invariant）＋ **`open`**（producer ownership） |
| `AS-4` | source artifact 中含**未获批准**的 source field ／ 未知 source 结构 ／ unsupported exported-artifact shape | **`Registered`（`Decision 3`，Issue #76 Human-approved —— **非** inherited）：** 属 **Adapter-side unsupported ／ failure condition** ⇒ Adapter 对 **affected dataset artifact fail closed**，**不产出** canonical artifact，**不**生成假的 canonical artifact，**不**由 Data Validation 反向猜测 source-side root cause；其 context 由**已授权单独设计**的 non-canonical Failure ／ Quarantine Interface 承载（**物理形态 ／ schema 仍未定**）。**inherited 部分仅为** general fail-closed 原则（`AC-7` ／ `AC-8` ／ `§3.10`），**Decision 3 本身不得**标为 inherited | **`Registered`**（`Decision 3`） |
| `AS-5` | 同一 source record 需要按 manifest 声明的 logical dataset 顺序引用 | Adapter **不得**依赖 filename ／ ordering ／ discovery heuristic 推断 role（`IC-3` 边界） | **`IC`** |

**B. Mapping side**

| # | Scenario | 既有约束要求的行为 | 性质 |
| --- | --- | --- | --- |
| `AS-6` | source identifier 需要解析成 canonical identity | **deterministic ＋ explicit ＋ traceable ＋ reproducible**；**不得** fuzzy ／ name similarity ／ LLM guess（`AC-5` ／ `AC-6`） | **`IC`** |
| `AS-7` | 多个 candidate source dates 存在且不同，且**无** approved source-specific mapping | **不得选择任何一个** ⇒ mapping unresolved ⇒ `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED`；capability 需要时 `DATA_INCOMPLETE`（`AC-18`） | **`IC`** |
| `AS-8` | 只有一个 candidate source date 有值 | **仍不得**自动视为 canonical（`single candidate ≠ automatically canonical`，`AC-18`） | **`IC`** |
| `AS-9` | 需要 source-field precedence（`promised_date` ／ `expected_arrival_date` ／ `ETA` 谁优先） | **Global Source-Field Precedence = `NOT ADOPTED`**；**不得**发明（`AC-18`） | **`IC`** |
| `AS-10` | Adapter 发现 canonical semantic 本身无法解释某 source value | `SEMANTIC_UNRESOLVED` 边界；Adapter **不得**自行改定义 canonical semantic（`AC-10` ／ `AC-18`） | **`IC`** |
| `AS-11` | Adapter 需要「补全」缺失值以让 downstream 计算继续 | **禁止** auto-reconciliation ／ `missing → 0` ／ sentinel 代替（`AC-7`） | **`IC`** |
| `AS-12` | Adapter 需要 trim ／ case-fold ／ Unicode-normalize ／ 数值强转以完成匹配 | **禁止** silent fix-up（`AC-6` ／ `AC-13`） | **`IC`** |
| `AS-13` | Adapter 需要建立**第二套 canonical identity 或 vocabulary** 以简化映射 | **不得**（`AC-5` ／ `AC-19`）；identity ／ vocabulary 归属本层之外 | **`IC`** |
| `AS-14` | Adapter 的 mapping 判定规则本身**如何表达**（configuration ／ mapping registry ／ code） | **已登记（`Decision 4`，Issue #78 —— **registered**，非 inherited）：** 本层**只**规定 mapping rule **必须满足的 contract requirements**（explicit ／ deterministic ／ traceable ／ reproducible；明确 source scope ／ logical dataset ／ canonical target；rule identity ／ revision identity 可审计可复现；禁 hidden default ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization；不改 canonical semantic ／ enum ／ mapping contract；不建立 Global Source-Field Precedence；不得越过已 `DESIGN RESOLVED` 的 canonical mapping contracts）；**representation carrier 明确 deferred 给 Architecture ／ Implementation**，**不创建**强制 `Mapping Registry` component；missing ／ conflicting ／ 非确定性 rule ⇒ 服从 `Decision 3` fail-closed | **`Registered`**（`Decision 4`） |

**C. Output side**

| # | Scenario | 既有约束要求的行为 | 性质 |
| --- | --- | --- | --- |
| `AS-15` | 某 producer 提交 canonical artifact set，供 Snapshot / Import Contract 接受 | **producer-neutral invariant（`P-1`）**：任何提交给 `Final Import Contract` 的 package 内容**必须可被**其验证（`IC-1` ／ `IC-3` ／ `IC-8` ／ `IC-22` ＋ `AC-15`），且**不得**自行宣告 `Accepted`。**current-state（`Decision 2` ／ Issue #74）：** 每个 Adapter 产出其职责范围内的 canonical dataset artifact（`P-2`）；只有经 **Package Assembly** 形成的**完整 package** 才可提交 `Final Import Contract`，partial artifacts **不得单独**被视为可接受 package | **`IC`**（invariant）＋ **`Registered`**（producer ownership，`P-2`） |
| `AS-16` | Artifact 的 digest 与 **producer 提交 ／ acceptance 所验证的 exact raw bytes** 不一致 | `IG-raw` = exact raw bytes ⇒ **fail closed**（package-level）；**任何** producer ／ 写入者 **不得**静默重算 ／ 覆盖（若 Adapter 为被选中的 producer 则同受此约束） | **`IC`** |
| `AS-17` | acceptance 过程中 artifact 被替换 ／ 重读得到不同视图 | `Decision 10A`：验证结果**必须**绑定实际被接受的同一 stable content view（`AC-15`） | **`IC`** |
| `AS-18` | 某 producer 在 canonical artifact 中写入 `"_meta"` provenance association 与 mapping basis | **carrier obligation（`Inherited Constraint`）**：shape 与 approved literals **已由 FCM ／ FIC 唯一确定**（`AC-12` ／ `AC-13` ／ `AC-14`），写入者**必须**遵守。**current-state（`Decision 2` ／ Issue #74）：** **每个 Adapter 负责写入其自身掌握的 source-derived record-level provenance ／ evidence locator ／ `mapping_basis`**，且**只能**使用已批准 carrier ／ literals（`P-2` ／ `ADEP-4` ／ `ADEP-11`） | **`IC`**（carrier obligation）＋ **`Registered`**（metadata producer） |
| `AS-19` | **提交给 downstream ／ `Final Import Contract` 的 candidate package** 缺少某 capability 所需的 logical evidence role | 属 **`EVIDENCE_AVAILABILITY`**（Layer 2）capability 后果，**不是** 任何 producer 自定的 package structural failure（`AC-16`）；**producer ownership 已由 `Decision 2` 登记**（Adapter 产出其 artifact ／ Package Assembly 组装完整 package，`P-2` ／ `ADEP-11`） | **`IC`**（semantic）＋ **`Registered`**（producer ownership） |
| `AS-20` | Adapter 想要**直接标记** `REJECTED` ／ `UNUSABLE` 或自行生成 Validation Issue | **不得** —— disposition 由 `Final Import Contract` 判定（`§4.3.29` `RD-B`）；Validation Issue 由 Data Validation 依 taxonomy 产生（`AC-16`） | **`IC`** |
| `AS-21` | 同一 source 的两次 mapping 在同一输入下给出不同结果 | 违反 `deterministic` ／ `reproducible`（`AC-6`） | **`IC`** |

**D. Multi-source / multi-Adapter**

| # | Scenario | 既有约束要求的行为 | 性质 |
| --- | --- | --- | --- |
| `AS-22` | Source A 与 Source B 对同一 canonical semantic 使用**不同 source-specific mapping** | **允许**（`AC-18` ／ `AC-19`），**前提**是 canonical semantic 由 canonical design 定义、mapping 显式且可追溯 | **`IC`** |
| `AS-23` | 两个 Adapter 对同一 canonical field 给出**不同 canonical value**（同一 grain） | **不得** first ／ latest ／ most-frequent wins；应为 unresolved ／ consistency issue（`§4.5.16` 边界 ＋ `AC-7`）。**current-state（`Decision 6` ／ Issue #84）：** 该一致性义务已登记为 **explicit cross-Adapter consistency obligation**（冲突处理见 `Decision 6` 6.4 ／ 6.5；pre-canonical 阶段与 `Decision 3` fail-closed 对齐） | **`IC`** ＋ **`Registered`**（`Decision 6` consistency obligation） |
| `AS-24` | Adapter 引入 local convention（默认值 ／ fallback ／ 「合理」推断）并成为事实上的全局语义 | **不得** —— 属 **silent semantic drift**（`AC-6` ／ `AC-7` ／ `AC-10`） | **`IC`** |
| `AS-25` | 多 Adapter 之间需要共享的 canonical 约定（identifier ／ vocabulary ／ priority）**表达与治理** | **已登记（`Decision 6`，Issue #84 —— **registered**，非 inherited）：** canonical-first（`MS-1`）保持 authoritative；**不得**引入第二套 canonical identity ／ vocabulary、**不得**建立 Global Source-Field Precedence ／ Adapter priority ／ source priority；多 Adapter 指向**相同或重叠** canonical entity ／ field ／ semantic ／ scope 时**必须**满足 **explicit cross-Adapter consistency obligation**（`Decision 6` 6.2 ／ 6.3）；**具体 detection mechanism 属 Architecture ／ Implementation** | **`Registered`**（`Decision 6`） |
| `AS-26` | 同一 source identity 在同一有效 mapping context 中指向多个 canonical identities | 视为 **unresolved identity ／ consistency issue**，限制 blast radius；**不得**自动选择（`AC-7`） | **`IC`** |

**E. Cross-layer / governance**

| # | Scenario | 既有约束要求的行为 | 性质 |
| --- | --- | --- | --- |
| `AS-27` | Adapter 需要 credentials ／ secrets 以读取 **Data Landing Zone 中的 exported artifacts** | Secret Handling = `DESIGN PENDING`（`AC-21`）；本层**不得**设计，只登记 dependency。**不涉及 source-system credentials**（`AC-1` ／ `AC-2` ／ `ADEP-9`）。**已登记（`Decision 7` ／ Issue #86 —— **registered**，非 inherited）：** Adapter **只**声明「该 Data Landing Zone-side read dependency 存在 authorized credential ／ secret requirement」这一 **conceptual dependency**，**不**声明 secret value、**不**选择 provisioning ／ storage ／ retrieval ／ rotation mechanism；真实 credential ／ secret **不得**进入 canonical design ／ mapping rule ／ `mapping_basis` ／ provenance ／ canonical record ／ `"_meta"` ／ prompt ／ log ／ Git | **`Registered`**（`Decision 7`）＋ **`open`**（`§7` Secret Handling 仍 `DESIGN PENDING`） |
| `AS-28` | Adapter 的 data scope ／ permission 边界（**仅限 Data Landing Zone 侧**） | `Data Scope` ／ `Tool Permission` = `DESIGN PENDING`（`AC-21`），**仍由 `§7` 后续设计负责**。**已登记（`Decision 7` ／ Issue #86 —— **registered**，非 inherited）：** Adapter **只声明**所需 **logical data scope**（logical dataset ／ source scope ／ applicable exported-artifact scope）与最小 **operation ／ capability**，并需要一个满足该要求的 **authorized access context**；Adapter **不**拥有 Data Scope ／ Tool Permission policy ／ approval 与 authorization decision；requirement 不可用 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ **fail closed**，**不得**自行扩大 Data Scope ／ 提升 Tool Permission ／ 绕过 policy | **`Registered`**（`Decision 7`）＋ **`open`**（`§7` Data Scope ／ Tool Permission 仍 `DESIGN PENDING`） |
| `AS-29` | Adapter 需要真实的 source table ／ column 名称 | **不得**在本层选择；真实 source field 未知 **≠** design pending（`AC-17`） | **`IC`** |
| `AS-30` | Adapter 的 runtime failure（exported artifact unreadable ／ malformed ／ 无法解析 source shape）如何上报 | 不得自行定义新 reason；Layer 1 部分属 `Final Import Contract`，Layer 2 ～ 4 部分属 Data Validation（`AC-16`）。**不**包含 source-system unreachable —— 该情形属 **Data Landing Zone ／ Controlled Export 上游**（`§3.10` fail closed ／ `ADEP-9`） | **`IC`** |

---

#### 4.6.5 Candidate Options / Trade-offs

> 以下仅为**候选模型**，**不代表**本 Review 的选择。
> **已被 inherited constraints 排除的模型**显式标注 `NOT COMPATIBLE`，**不**列为开放选项。

**A. Adapter Owns ／ Does Not Own（Q1）**

**A-1. 继承约束（`Inherited Constraint`）—— 历史已批准来源（`AC-22` 前 5 项）：**

| `Inherited Constraint` 明确规定 | 依据 |
| --- | --- |
| Adapter 受 `§3` read boundary 约束：只处理经 Controlled Export 进入 **Data Landing Zone** 的业务数据，**不得**直连 source system；unavailable ⇒ fail closed | `§3.1` ／ `§3.3` ／ `§3.4` ／ `§3.10` |
| **source-specific semantic mapping responsibility ＋ mapping constraints**：具体 `source value ／ field → canonical value` 由 source-specific mapping ／ Adapter 提供；mapping **必须** deterministic ／ explicit ／ traceable ／ reproducible（禁 fuzzy ／ similarity ／ LLM 选择）；Adapter **不得**重新定义 canonical semantic | `§4.5.2` ／ `§4.5.11` ／ `§4.5.21`（各 Human-approved mapping record 的实际范围） |
| `Stable Source Evidence Locator` 与 `Mapping ／ Resolution Basis` 的 **carrier obligation**（**任何**写入者的写入形态要求；carrier shape 与 literals 归 `FCM`） | `§4.3.28 E` ／ `§4.5.2`（traceable requirement） |
| **不得**：定义 canonical entity ／ field ／ enum 与 `BR-*` semantic；宣告 `Accepted` ／ package disposition；定义 record ／ artifact carrier shape 与 approved literals；生成 Layer 2 ～ Layer 4 validation outcome；设计 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling | `§4.4.2` ／ `§4.4.3` ／ `§4.3.25` ／ `§4.3.28` ／ `§4.3.29` ／ `§7` |

**A-2. 本层 newly Human-approved registered policy（**不是** historical inherited）：**

| 已登记政策（`REGISTERED`） | 依据 |
| --- | --- |
| **Adapter Boundary 通用职责（`Decision 1(a)`，Issue #72 Human-approved，`REGISTERED`）**：在 Controlled Export ／ Data Landing Zone **之后** —— 读取 ／ 提取 exported artifacts ／ source records；`exported-artifact format ／ protocol handling`；`generic source-field identification`；`source-specific mapping execution ／ realization`。**明确不含** source-system connectivity ／ Controlled Export 上游链路 ／ export-side protocol ／ credentials（若要纳入须另走 Human-approved `§3` design change） | `§4.6.10` `Decision 1` Human Decision Record（Issue #72） |
| **Adapter 可在内部定义 source-specific resolution rules（`Decision 1(b)`，Issue #72 Human-approved，`REGISTERED`）**：**必须** explicit ／ deterministic ／ traceable ／ reproducible；**不得** LLM guess ／ fuzzy ／ similarity ／ silent normalization；**不得**修改或重新定义 canonical semantic；**不得**建立 global source-field precedence；**不得**越过已 `DESIGN RESOLVED` 的 canonical mapping contracts | `§4.6.10` `Decision 1` Human Decision Record（Issue #72） |
| **Adapter 拥有其 canonical dataset artifact production（`Decision 2`，Issue #74 Human-approved，`REGISTERED`）**：每个 Adapter 负责其职责范围内的 `source-specific mapping ／ resolution`、产出对应的 **canonical dataset artifact**、将其掌握的 source-derived provenance ／ evidence locator ／ `mapping_basis` 写入**已批准 carrier**、保持 deterministic ／ explicit ／ traceable ／ reproducible；**不生成** package-level acceptance ／ disposition | `§4.6.10` `Decision 2` Human Decision Record（Issue #74） |
| **Package Assembly 拥有 package production（`Decision 2`，Issue #74 Human-approved，`REGISTERED`）**：独立的 **conceptual responsibility** 负责汇集一个或多个 Adapter 产出的 canonical artifacts、生成 ／ 绑定 `snapshot_package_id`、生成 Manifest、建立 package-level artifact references ／ package organization、形成满足既有 Snapshot / Import Contract 的**完整、原子** Snapshot Package、并将完整 package 提交给 `Final Import Contract`。**不选择**其运行形态（service ／ module ／ job ／ library ／ workflow node ／ framework ／ database ／ queue ／ API ／ deployment） | `§4.6.10` `Decision 2` Human Decision Record（Issue #74） |
| **`Final Import Contract` 只验证 ／ disposition，**不**生产 package（`Decision 2`，Issue #74 Human-approved，`REGISTERED`）**：不生产 canonical artifacts ／ Manifest ／ package；不改变既有 FIC ／ FCM contract | `§4.6.10` `Decision 2` Human Decision Record（Issue #74）＋ `§4.3.28` ／ `§4.3.29` |
| **unresolved ／ unsupported mapping 策略（`Decision 3`，Issue #76 Human-approved，`REGISTERED`）**：条件组合，**以 `UF-2` ／ fail-closed 为主**；approved missing（mapping contract 明确允许 source absence → canonical `null` ／ missing）为**正常 missing**；unresolved ／ ambiguous ／ conflicting ／ unsupported 时 Adapter **对 affected dataset artifact fail closed**，**不产出**伪 canonical artifact，**禁止** silent skip ／ 强制压成 `null` ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization ／ 自行扩展 canonical semantic ／ enum ／ mapping contract；Package Assembly **不得**补 mapping ／ 生成 placeholder ／ 把 unresolved 当成正常 `null` | `§4.6.10` `Decision 3` Human Decision Record（Issue #76） |
| **Adapter Failure ／ Quarantine Interface（`Decision 3` 授权，Issue #76，`AUTHORIZED FOR SEPARATE DESIGN`）**：**non-canonical** interface ／ responsibility，用于承载 source evidence reference ／ unresolved ／ unsupported ／ failure context ／ mapping attempt ／ rule context 与诊断信息。**边界（不可让步）：** **不得**进入 Snapshot Package、**不得**往现有 canonical record ／ dataset ／ `"_meta"` 偷加字段、**不得**修改现有 FCM ／ FIC carrier、**不得**改变 canonical schema ／ semantic；**物理形态 ／ schema ／ runtime implementation 尚未完成** ⇒ **不得**在任何 current-state 表述中声称其 **operationally available**（本 Decision 不决定其形态） | `§4.6.10` `Decision 3` Human Decision Record（Issue #76） |
| **source-specific mapping rule representation boundary（`Decision 4`，Issue #78 Human-approved，`REGISTERED`）**：**Option ① —— 只登记 contract requirements，representation carrier deferred**。任何 source-specific mapping ／ resolution rule **必须** explicit ／ deterministic ／ traceable ／ reproducible、明确 source ／ source scope 与 logical dataset ／ canonical target、具有可审计可复现的 rule ／ revision identity 且可追溯其产出的 canonical result；**禁止** hidden default ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization ／ 重定义或扩展 canonical semantic ／ enum ／ mapping contract ／ Global Source-Field Precedence ／ 越过已 `DESIGN RESOLVED` 的 canonical mapping contracts；missing ／ conflicting ／ 非确定性 rule ⇒ 服从 **`Decision 3`** fail-closed。**representation carrier（configuration ／ registry ／ code ／ DB ／ rule engine ／ service 等）与强制 `Mapping Registry` component 均不规定**，属 **Architecture ／ Implementation**（`§10`） | `§4.6.10` `Decision 4` Human Decision Record（Issue #78） |
| **`Mapping ／ Resolution Basis` semantic granularity（`Decision 5`，Issue #82 Human-approved，`REGISTERED`）**：**Option ① —— minimal rule ／ revision reference**。`mapping_basis` 以一个 **exact JSON string** 标识本次 semantic mapping ／ resolution 使用的 **approved mapping rule identity ＋ revision identity**（可回答「该 canonical result 出自哪一 approved rule 的哪一 revision」）；**职责分离** —— `evidence` = Stable Source Evidence Locator、`mapping_basis` = approved rule ＋ revision、approved mapping rule = deterministic mapping ／ resolution logic，**可复现性由三者组合建立**；**不要求、也不允许** `mapping_basis` 承载 source evidence ／ rule logic ／ explanation ／ rationale ／ 自由文本 ／ mini-schema ／ 新 provenance schema；**具体 string syntax ／ encoding（`rule-id@revision` ／ path-like ／ URI-like ／ namespaced ／ hash 等）属 Architecture ／ Implementation**；保持 exact-string **不 normalize ／ trim ／ case-fold ／ Unicode-normalize ／ numeric coercion**、**不新增** `"_meta"` member ／ literal ／ carrier | `§4.6.10` `Decision 5` Human Decision Record（Issue #82） |
| **multi-Adapter governance ／ canonical semantic drift detection（`Decision 6`，Issue #84 Human-approved，`REGISTERED`）**：**Option ② —— explicit cross-Adapter consistency obligation**。多个 Adapter **可以**拥有不同 source-specific mapping ／ resolution rules，但**只要**指向**相同或重叠**的 canonical entity ／ field ／ semantic ／ relationship ／ applicability scope（或其他共同影响同一 canonical interpretation 的 mapping），其 approved mapping rules ／ revisions **必须**可被检查为：与 current approved canonical contract 一致 ／ 与各自声明的 source scope ／ logical dataset ／ canonical target 一致 ／ **不存在**未解释的 semantic contradiction ／ **不依赖** implicit Adapter priority ／ first-wins ／ latest-wins ／ source priority ／ LLM ／ heuristic arbitration ／ silent normalization。**canonical-first（`MS-1`）** 保持 authoritative；**不得**引入第二套 canonical identity ／ vocabulary；**不得**建立 Global Source-Field Precedence（`MS-2` = `NOT COMPATIBLE`）。**两个 conceptual check points：** ① rule registration ／ revision change（新 rule ／ 修改 rule ／ 新 revision ／ source scope ／ canonical target 扩展在可被视为 approved ／ usable **之前**）；② overlapping canonical use（多 Adapter outputs 被共同用于同一 canonical context ／ Analysis Run **之前**）。unresolved drift ⇒ **不得** first-wins ／ latest-wins ／ priority ／ LLM ／ heuristic ／ silent reconciliation，**不得**由 Package Assembly 自行解释或修复；pre-canonical unresolved drift 与 **`Decision 3`** fail-closed 对齐。**检测 mechanism 与 Cross-Adapter Registry ／ Drift Detector component 均不规定**，属 **Architecture ／ Implementation**（`§10`） | `§4.6.10` `Decision 6` Human Decision Record（Issue #84） |
| **Adapter ↔ `Permission & Security` interface expectation（`Decision 7`，Issue #86 Human-approved，`REGISTERED`）**：**Option ① —— declarative access-requirement interface**。Adapter Boundary **只**声明执行已批准职责所需的 **minimum authorized access requirements ／ security dependencies** —— **resource boundary**（仅限其职责所需的 **Data Landing Zone-side** exported artifacts ／ resources）／ **operation ／ capability**（完成职责所需的最小 capability；**不得**扩展为 Production write）／ **logical data scope**（所需 logical dataset ／ source scope ／ applicable exported-artifact scope）／ **security dependency**（需要满足上述要求的 **authorized access context**）／ **secret dependency（when applicable）**（只声明 dependency 存在，**不**声明 secret value，**不**选择 provisioning ／ storage ／ retrieval）。**不赋予 Adapter：** RBAC policy、user ／ role、Data Scope policy ／ approval、Tool Permission policy ／ approval、authorization decision、authentication、identity ／ principal model、credential issuance ／ provisioning ／ storage ／ retrieval ／ delivery、secret rotation ／ lifecycle ／ manager 选择、policy evaluation、permission escalation、emergency ／ break-glass policy（仍由 `§7` 后续设计负责，**不**标为 `DESIGN RESOLVED`）。required authorized access 未提供 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ **fail closed ／ do not proceed**；**禁止**自行扩大 Data Scope ／ 提升 Tool Permission ／ 改用更高权限身份 ／ 猜测或使用未批准 credential ／ 绕过 policy ／ 绕过 Data Landing Zone ／ fallback 到 source-system direct access ／ Production DB ／ API ／ 把缺授权伪装成正常 data missing。Permission ／ Security dependency failure **不得**被重新解释为 canonical mapping unresolved ／ canonical missing ／ `null` ／ business `DATA_INCOMPLETE` ／ Data Validation reason ／ mapping conflict ／ package disposition；**不扩展** `Decision 3` Failure ／ Quarantine Interface 的 schema ／ responsibility。**Secret boundary：** 真实 credential ／ secret **不得**进入 canonical design ／ mapping rule ／ `mapping_basis` ／ provenance ／ canonical record ／ `"_meta"` ／ prompt ／ log ／ Git；**不选择** Vault ／ Secrets Manager ／ Kubernetes Secret ／ env var ／ OAuth ／ service account ／ API key 等 mechanism。**严格限于 Data Landing Zone ／ Controlled Export 之后**（**不含** source-system ／ ERP ／ SRM ／ Production DB credentials、export-side protocol credentials、Controlled Export 上游身份、Production API write credential）。**interface expectation ≠ injection mechanism**；existing **`AI Effective Permission` invariant 保持不变**。`§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling **仍为 `DESIGN PENDING`** | `§4.6.10` `Decision 7` Human Decision Record（Issue #86） |

**A-3. 本层开放 —— Finding ／ Human Decision（**仅真正 pending 项**；依 `AC-23`）：**

| # | 开放 ownership ／ responsibility 问题 | 落点 |
| --- | --- | --- |
| — | **（无）** —— `Decision 1` ～ `Decision 8` 已登记；本表当前**不含** open ownership ／ responsibility 问题 | **已由 Dedicated Adapter Boundary Closure Design Change PR（Issue #90）执行**：`A-1` ～ `A-14` **全部 PASS** ⇒ 已登记 `DESIGN RESOLVED`（见 **`§4.6.21`**） |

> **已由 `Decision 3` 登记（Issue #76）：** ⑥ **unresolved ／ unsupported mapping 策略** ——
> 条件组合，**以 `UF-2` ／ fail-closed 为主**；approved missing（`3.1`）与 unresolved（`3.2`）**必须区分**；
> unsupported source field ／ vocabulary ／ exported-artifact shape 属 **Adapter-side unsupported ／ failure condition**；
> Package Assembly **不得**补 mapping ／ placeholder ／ unresolved-as-null。
> 同时 **授权后续单独设计** non-canonical **Adapter Failure ／ Quarantine Interface**（**不**进入 Snapshot Package、
> **不**改现有 FCM ／ FIC carrier、**不**新增 canonical 字段、**不**预选实现技术）；其**形态 ／ schema 仍未定**。
> 该行**已从本开放表移出**，其内容见 **A-2** ／ `AC-22` ／ **`§4.6.10` `Decision 3` Human Decision Record**（`ADEP-12`）。
>
> **已由 `Decision 4` 登记（Issue #78）：** ⑦ **source-specific mapping rule representation boundary** ——
> **Option ①：只登记 contract requirements，representation carrier deferred**（explicit ／ deterministic ／
> traceable ／ reproducible；source scope ／ canonical target ／ rule ＋ revision identity 可审计可复现；
> 禁 hidden default ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization；不改 canonical semantic ／ enum ／
> mapping contract；不建立 Global Source-Field Precedence；不越过已 `DESIGN RESOLVED` 的 canonical mapping contracts）；
> missing ／ conflicting ／ 非确定性 rule ⇒ 服从 `Decision 3` fail-closed。
> **representation carrier（configuration ／ registry ／ code ／ DB ／ rule engine ／ service）与强制 `Mapping Registry`
> component 均不规定** ⇒ 属 **Architecture ／ Implementation**（`§10`），**不属本层 open table**。
> 该行**已从本开放表移出**，其内容见 **A-2** ／ `AC-22` ／ **`§4.6.10` `Decision 4` Human Decision Record**（`ADEP-2` ／ `ADEP-8`）。
>
> **已由 `Decision 5` 登记（Issue #82）：** ⑧ **`mapping_basis` 语义粒度** ——
> **Option ① minimal rule ／ revision reference**（approved mapping rule identity ＋ revision identity；
> `evidence` ／ `mapping_basis` ／ approved mapping rule 职责分离；可复现性由三者组合建立；
> 不承载 evidence ／ rule logic ／ explanation ／ rationale ／ mini-schema；不新增 `"_meta"` member ／ literal ／ carrier）。
> **`mapping_basis` 的具体 string syntax ／ encoding** ⇒ 属 **Architecture ／ Implementation**（`§10`），**不属本层 open table**。
> 该行**已从本开放表移出**，其内容见 **A-2** ／ `AC-22` ／ **`§4.6.10` `Decision 5` Human Decision Record**（`ADEP-4` ／ `PE-1` ／ `ARF-5` ／ `A-8`）。
>
> **已由 `Decision 6` 登记（Issue #84）：** ⑨ **multi-Adapter governance ／ canonical semantic drift detection** ——
> **Option ② explicit cross-Adapter consistency obligation**（canonical-first 保持；相同或重叠 canonical target ／
> scope 的多 Adapter approved rules ／ revisions **必须**可被检查为与 canonical contract 及各自声明的 scope 一致、
> **不存在**未解释 semantic contradiction；禁 Adapter priority ／ source priority ／ first-wins ／ latest-wins ／
> LLM ／ heuristic ／ silent reconciliation；unresolved drift 与 `Decision 3` fail-closed 对齐）。
> **具体 detection mechanism** ⇒ 属 **Architecture ／ Implementation**（`§10`），**不属本层 open table**。
> 该行**已从本开放表移出**，其内容见 **A-2** ／ `AC-22` ／ **`§4.6.10` `Decision 6` Human Decision Record**（`ADEP-5` ／ `ARF-6` ／ `A-9`）。
>
> **已由 `Decision 7` 登记（Issue #86）：** ⑩ **Adapter ↔ `Permission & Security` interface expectation** ——
> **Option ① declarative access-requirement interface**（Adapter 只声明 minimum authorized access requirements ／
> resource boundary ／ operation ／ logical data scope ／ authorized access context ／ secret dependency；
> 不拥有 RBAC ／ Data Scope ／ Tool Permission ／ authorization decision ／ credential lifecycle ／ Secret Handling；
> authorized access 不可用 ⇒ fail closed；Permission ／ Security failure 不得伪装为 canonical missing ／
> mapping unresolved ／ `DATA_INCOMPLETE` ／ Data Validation reason ／ package disposition）。
> **`§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 仍为 `DESIGN PENDING`**；具体 injection ／ broker ／
> secret manager ／ auth runtime mechanism ⇒ 属 **Architecture ／ Implementation**，**不属本层 open table**。
> 该行**已从本开放表移出**，其内容见 **A-2** ／ `AC-22` ／ **`§4.6.10` `Decision 7` Human Decision Record**（`ADEP-7` ／ `ARF-8` ／ `A-11`）。

> **已由 `Decision 1` 登记（Issue #72）：** ① `source extraction` 责任；
> ② `generic source-field identification ownership`；③ `exported-artifact format ／ protocol handling` ownership；
> ④ Adapter 与 `Master Data Mapping` 的 mapping decision 分工（`Decision 1(b)`）。
> 上述四项**不再是 open**，其内容见 **A-2** 与 `AC-22`。
>
> **已由 `Decision 2` 登记（Issue #74）：** ⑤ **producer ownership** ——
> Adapter 拥有**其** canonical dataset artifact production 与 record-level provenance 写入；
> **Package Assembly**（独立 conceptual responsibility）拥有 `snapshot_package_id` ／ Manifest ／
> package organization ／ 完整 package 组装；`Final Import Contract` **只**验证 ／ disposition。
> **该行已从本开放表移出**，其内容见 **A-2** 与 **`§4.6.10` `Decision 2` Human Decision Record**（`P-2` ／ `ADEP-11`）。

```
Adapter 不得重新定义 canonical semantic；也不得在未获 Human authorization 的情况下
自行承担 source-system connectivity 或 package-level 职责。

已登记（Decision 1）：Data Landing Zone 之后的读取 ／ 提取、format ／ protocol handling、
                      generic source-field identification、source-specific mapping execution
已登记（Decision 2）：谁直接产出 canonical artifact ／ package ／ manifest ／ provenance metadata
已登记（Decision 3）：unresolved ／ unsupported fail-closed 策略 ＋ non-canonical Failure ／ Quarantine
                      Interface 的**单独设计授权**（physical shape ／ schema ／ runtime 仍 pending；
                      **不得**进入 Snapshot Package；**尚未** operationally available）
已登记（Decision 7）：Adapter ／ Permission & Security interface expectation（**Option ① 声明式**；
                      `§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 仍 pending）
已关闭（Decision 8 ／ Issue #90 Closure Validation = PASS）：Adapter Boundary closure gate
                      ⇒ Adapter Boundary = DESIGN RESOLVED（conceptual；implementation 未授权）
```

**B. Adapter Input ／ Output Conceptual Contract（Q2）**

| 候选 | 含义 |
| --- | --- |
| `AI-1` —— **只接受 Controlled Export 产物**（Data Landing Zone 中的 exported artifacts ／ records；**不**包含与 source system 的任何连接） | input = 已导出快照；**不得**任何直连（`AC-1` ／ `AC-2`） |
| `AI-2` —— 允许直接连接 source system（只读） | **`NOT COMPATIBLE`** —— 违反 `AC-1` ／ `AC-2` |
| `AO-1` —— 产出 **canonical artifact set**（符合 FCM ／ Layout 的 carrier shape）＋ **mapping evidence**（`P-*` ／ `MB-*` 内容），由 `Final Import Contract` 验证 | output 是**输入给 import contract**的候选 package 内容，**不是** `Accepted` 结论 —— 见下方 invariant ／ producer 拆分 |
| `AO-2` —— Adapter 自行宣告 package acceptance ／ disposition | **`NOT COMPATIBLE`** —— 与已批准 policy（acceptance 判定归 `Final Import Contract`）及 `AS-20` 冲突（**不依赖** `RIF-11`） |

> **必须区分两个不同命题（不得合并表述）：**
>
> | # | 命题 | 性质 |
> | --- | --- | --- |
> | **P-1** | **FIC-valid output invariant**：任何**进入** `Final Import Contract` 的 package ／ artifacts **必须**符合 canonical carrier ／ contract（`AC-15`），否则由 `Final Import Contract` 判定为 structural failure；Adapter **不得**宣告 `Accepted` | **`Inherited Constraint`**（`§4.3.25` ／ `§4.3.28` ／ `§4.3.29`） |
> | **P-2** | **producer ownership**：**谁直接产出** canonical artifacts ／ package ／ manifest —— 已由 **`Decision 2`（Issue #74）登记为 Option ②**：每个 Adapter 产出其 canonical dataset artifact（含其 source-derived provenance ／ locator ／ `mapping_basis`），独立 **Package Assembly** 形成完整 package；`Final Import Contract` **只**验证 ／ disposition | **`Registered`（`Decision 2` ／ `ADEP-11`）** |
>
> `AO-1` **只**表达 **P-1**（output **必须**是 FIC-valid），**不**表达 **P-2**。
> 其他 producer 形态（例如 intermediate＋assembly）**同样**受 `P-1` 约束，
> **不得**被理解为与 `P-1` 冲突。

**`Inherited Constraint`：** `AI-1` ＋ **`P-1`（FIC-valid output invariant）**。
**已登记（`Decision 2` ／ Issue #74）：** **`P-2`（producer ownership）** —— Adapter 产出其 canonical dataset
artifact（含 source-derived provenance ／ locator ／ `mapping_basis`），**Package Assembly** 负责汇集、
生成 `snapshot_package_id` ／ Manifest 与 package organization，形成**完整、原子** Snapshot Package；
多 Adapter 的 partial artifacts **不得单独**视为可接受 package，**禁止 dataset-level partial acceptance**。
Package Assembly 为 **conceptual responsibility**，其运行形态与 technology **不在**本 Decision 范围内。
见 **`§4.6.10` `Decision 2` Human Decision Record** ／ `ADEP-11`。

**C. Deterministic ／ Fail-safe Requirements（Q3 ／ Q4）**

**`Inherited Constraint`（`AC-5` ～ `AC-10` ／ `AC-18`）：**

```
同一 source input ＋ 同一 approved mapping contract ⇒ 同一 canonical output（determinism）
no fuzzy ／ no similarity ／ no LLM choose ／ no silent normalization
exactly-one-or-unresolved（对需要参与 deterministic business rule 的 semantic）
missing ／ unresolved ／ invalid 必须区分，不得压平
```

**已登记（`Decision 3`，Issue #76 Human-approved）：** unresolved ／ ambiguous ／ conflicting ／ unsupported 一律 **fail closed**（`UF-2` 语义）：
Adapter 对 **affected dataset artifact 不产出** canonical artifact；**approved missing**（`3.1`）与 unresolved（`3.2`）**必须区分**。
**未选为主要策略：** `UF-1`（仅在既有 approved carrier 可表达的范围内成立）；**`UF-3` = `NOT COMPATIBLE`。**

| 候选 | 含义 | `Decision 3` 之后的定位 |
| --- | --- | --- |
| `UF-1` | Adapter **显式产出 unresolved marker**，downstream 由 Data Validation 依既有 reason 表达后果 | **未选为主要策略** —— 仅在**已批准 carrier 可表达**的范围内成立（见下方判定） |
| `UF-2` | Adapter **halt** 该 source ／ 该 dataset 的产出（**fail closed**），不产出伪 canonical artifact | **`SELECTED`（主要策略）** —— 其 context 由 `Decision 3` **授权单独设计**的 non-canonical **Adapter Failure ／ Quarantine Interface** 承载（`ADEP-12`）；**interface 形态 ／ schema 仍未定** |
| `UF-3` | Adapter **只**产出已可靠解析的 records，其余**静默省略** | **`NOT COMPATIBLE`（`AC-8`）** |

**`UF-1` 的相容性判定（`Decision 3` 之下 —— **仍不得**标为无条件可用）：**

- **可以**用已批准 carrier 表达的部分：对「**mapping 已批准、source value 不存在**」的字段，
  在 canonical record 中写 **`null`**（`C-2` 的 explicit missing ／ unavailable）——
  **无需**任何新 property ／ literal ／ artifact；
- **不可以**用已批准 carrier 表达的部分：**「存在 source evidence，但无 approved mapping ／
  无法可靠解析 semantic」**这一 **root condition 本身**。理由：
  ① `"_meta"` 的 known-member set 已固定，**新增 member 会被 reject**（`§4.3.28 E`）；
  ② 一般的 canonical field 写入 `null` 会与「approved mapping 下的 explicit missing」**压平**，
  而 current design 明确要求二者**不得**压平（`AC-9` ／ `AC-10` ／ `§4.5.21` A ／ B ／ C）；
  ③ 因此若要求**确定性区分** root condition，**必须**有该 mapping 是否已批准的**负向证据**位置，
  而现有已批准 carrier **没有**该位置。
- **结论（`Decision 3` 之后）：** `UF-1` **不能**仅凭已批准 carrier 完成 root-condition 区分，且**未**被选为主要策略。
  ① 若接受「Adapter 侧只表达 unresolved、root condition 由 Data Validation 依
  **mapping declaration**（属 mapping contract ／ implementation）判定」，则 `UF-1`
  **可**在不新增 carrier 的前提下成立 —— 但 `Decision 3` **未**采用该解读为默认路径；
  ② 若要求 unresolved 事实**必须**在 package 内被承载，则 `UF-1`
  **依赖单独 Human-authorized carrier ／ interface design change**（`ADEP-12`）。
- **`quarantine`：** `Decision 3` 已授权**单独设计** non-canonical **Adapter Failure ／ Quarantine Interface**；
  其**具体形态 / schema / storage / API 仍未定**，且**不得**进入 Snapshot Package ／ **不得**新增现有 carrier 字段。

```
Decision 3 已登记 = 「以 UF-2 ／ fail-closed 为主」＋「授权单独设计 non-canonical Failure ／ Quarantine Interface」
仍未定           = interface 的物理形态 / schema / storage / API（Design 4 ～ 8 之外，属后续单独设计）
UF-1 可声称范围   = 仍限于「不新增 carrier 的 Adapter-side unresolved 表达」
UF-3             = NOT COMPATIBLE（AC-8）
```

**本 Review 因此不把 `UF-1` 标为 inherited 或无条件 compatible。**

**D. Missing ／ Ambiguous ／ Unsupported 的表达归属（Q4）**

**`Inherited Constraint`（`AC-9` ／ `AC-10` ／ `AC-16` ＋ `§4.5.21` A ／ B ／ C）：**

| Root condition | 归属 | Validation reason（既有，不新增） |
| --- | --- | --- |
| approved mapping 存在，但 mapped source value **absent** | Data Validation（Layer 2 ／ 3） | `FIELD_VALUE` ／ `MISSING` |
| source evidence **存在**，但**无 approved mapping** ／ 无法可靠解析 | Data Validation（Layer 2 ／ 3） | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` |
| approved mapping 已确定，但值**无法解析为合法类型** | Data Validation（Layer 2 ／ 3） | `FIELD_VALUE` ／ `INVALID_TYPE` |
| source artifact 结构 ／ carrier 层问题（例如 required artifact absent ／ unreadable ／ digest 不符） | **`Final Import Contract`**（Layer 1） | `PACKAGE_STRUCTURE` ／ `STRUCTURAL_INCONSISTENCY` |

**开放的归属问题：** 「不支持 ／ 未批准的 source field 出现」时，
Adapter 的 fail-safe 行为与**上报形态** —— 见 Decision 3（**不等同于**新增 Validation Reason）。

**E. Evidence Locator ／ Mapping Basis Responsibility（Q5）**

- `PE-1` —— **producer-neutral**：**写入** canonical artifact 的 producer **必须**把 `locator` ／ `basis`
  字符串内容写入**已固定的** carrier（shape 依 FCM ／ FIC），**并保持**其原始值；
  **`mapping_basis` 语义已由 `Decision 5`（Issue #82）登记为 Option ① minimal rule ／ revision reference**
- `PE-2` —— canonical value 由某 producer 产出，provenance 由**下游**补
  **`NOT COMPATIBLE`** —— `P-A` ／ `MB-A` 为 **record-level carrier**（`AC-12`），
  下游无 source-level 知识，**无法**补出 locator 与 basis

**`Inherited Constraint`（producer-neutral 的 carrier obligation）：**
**任何** producer 写入 canonical artifact 时，**必须**依 `§4.3.28 E` 的 `"evidence"` ／ `"mapping_basis"`
carrier 形态写入 locator ／ basis，并满足 `§4.5.2` 的 traceable requirement
（`§4.3.28 E` ／ `§4.5.2`；**不**依赖 `RIF-11`）。
**已登记（`Decision 2` ／ Issue #74）：** ① **谁**是该 metadata 的 producer ——
**每个 Adapter 负责写入其自身掌握的 source-derived record-level provenance ／ evidence locator ／
`mapping_basis`**，且**只能**使用已批准 carrier ／ literals（`P-2` ／ `ADEP-4` ／ `ADEP-11`）。
**仍未决：** ② **basis 字符串的语义粒度**（见 Decision 5）。

**F. Multi-source ／ Multi-Adapter Canonical Semantic Stability（Q6）**

- `MS-1` —— **canonical-first**：canonical semantic 由 canonical design 定义；
  每个 source **只**登记自己的 explicit source-specific mapping；**不**建立跨 source precedence
- `MS-2` —— **precedence-first**：建立跨 source ／ 跨字段优先级来消解差异
  **`NOT COMPATIBLE`** —— 违反 `AC-18`（`Global Source-Field Precedence = NOT ADOPTED`）
- `MS-3` —— allowed-but-not-interpret ／ preserve raw source value 供人工判读
  （**仅**在既有 carrier 已有位置时可考虑；**不得**新增 carrier）

**已登记（`Decision 6` ／ Issue #84 —— **registered**，非 inherited）：** 多 Adapter 共享 canonical 约定的**治理** = **canonical-first（`MS-1`）＋ explicit cross-Adapter consistency obligation（`Decision 6` Option ②）** —— 多 Adapter 指向**相同或重叠** canonical entity ／ field ／ semantic ／ relationship ／ applicability scope 时，其 approved mapping rules ／ revisions **必须**可被检查为与 current approved canonical contract 及各自声明的 source scope ／ logical dataset ／ canonical target 一致，且**不存在**未解释的 semantic contradiction；**禁止** Adapter priority ／ source priority ／ Global Source-Field Precedence ／ first-wins ／ latest-wins ／ LLM ／ heuristic ／ silent reconciliation。
**仍未决（属 Architecture ／ Implementation）：** drift 的**具体 detection mechanism**（CI ／ test ／ registry validation ／ runtime validator ／ service ／ workflow node ／ DB ／ API ／ manual review 等）与两个 conceptual check points 的实现形态（`Decision 6` 6.3 ／ 6.7）。

**G. Boundary Ownership with Other Layers（Q7）**

**`Inherited Constraint`：** 见 `AC-22`（已批准部分）与 `§3`；

- `Permission & Security` 拥有 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling（**`DESIGN PENDING`**）
- `Architecture` 拥有 framework ／ technology ／ deployment 选择（**尚无 ADR**）
- Implementation 拥有 runtime code ／ scheduling ／ retry
- **source-system connectivity（连接 source system ／ export-side protocol ／ export-side credentials） =
  POC Adapter boundary 之外**（`§3.1` ／ `§3.3`；`AC-1` ／ `AC-2`）—— 若未来要把其纳入 Adapter，
  **必须**另走 Human-approved `§3` design change，**不得**在本层推定

**已登记（`Decision 7` ／ Issue #86 —— **registered**，非 inherited）：** Adapter 与 `Permission & Security` 之间的**接口期待** = **Option ① —— declarative access-requirement interface**：Adapter **只声明**其在 **Data Landing Zone 侧读取 exported artifacts** 所需的 **minimum authorized access requirements ／ security dependencies**（resource boundary ／ operation ／ logical data scope ／ authorized access context ／ secret dependency），**不**决定 authorization ／ RBAC ／ Data Scope ／ Tool Permission ／ credential lifecycle ／ Secret Handling 的实现，**也不选择** injection ／ broker ／ secret manager ／ auth runtime mechanism（属 `§7` ／ Architecture ／ Implementation）。
**仍未决（属 `§7`）：** RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 仍为 `DESIGN PENDING`（`AC-21`）。**该接口不涉及 source-system connectivity。**

---

#### 4.6.6 Option Comparison

`—` = 不适用。判定针对**既有 canonical 约束兼容性**与 **POC implementation cost**，
**不代表**本 Review 的选择。

| Model | 与既有约束兼容 | POC cost | 备注 |
| --- | --- | --- | --- |
| `AI-1`（只接受 Controlled Export 产物） | **`Inherited Constraint`（`AC-1` ／ `AC-2`）** | 最低 | 唯一合法 input 通道 |
| `AI-2`（直连 source system） | **`NOT COMPATIBLE`** | — | 违反 hard boundary；非开放选项 |
| `AO-1`（output **必须** FIC-valid）**—— 仅 `P-1` invariant** | **`Inherited Constraint`** | 中 | output **必须**可被 FIC 验证；Adapter 不宣告 acceptance。**producer ownership（`P-2`）已由 `Decision 2`（Issue #74）登记** |
| `AO-2`（Adapter 自行宣告 acceptance） | **`NOT COMPATIBLE`** | — | 与已批准 policy（acceptance 判定归 `Final Import Contract`）／ `AS-20` 冲突 |
| `UF-1`（显式 unresolved marker） | **条件性** —— **仅**在「不新增 carrier，root-condition 区分依赖 mapping declaration」的解读下成立（`AC-9` ／ `AC-10`） | 低 | **不**标为 inherited；若要求在 package 内承载 unresolved 事实 ⇒ 依赖单独 Human-authorized carrier ／ interface design change（`ADEP-12`） |
| `UF-2`（halt dataset 并等待修复） | **条件性** —— 需承载「该 unresolved source ／ 该 attempt 未通过」，已批准 carrier **无**对应位置 ⇒ **依赖单独 Human-authorized design change** | 中 | 更强 fail-safe；「何时可重跑」亦需登记 |
| `UF-3`（静默省略 unresolved records） | **`NOT COMPATIBLE`（`AC-8`）** | — | silent exclusion 被明确禁止 |
| `PE-1`（**producer-neutral**：写入者必须把 locator ／ basis 写入已固定 carrier 并保持原始值） | **`Inherited Constraint`（carrier obligation；`§4.3.28 E` ／ `§4.5.2`）** | 中 | carrier shape 已由 FCM 固定；**metadata producer 已由 `Decision 2`（Issue #74）登记为「每个 Adapter 写入其自身掌握的 source-derived provenance」**（`P-2` ／ `ADEP-4` ／ `ADEP-11`） |
| `PE-2`（下游补 provenance） | **`NOT COMPATIBLE`** | — | 下游无 source-level 信息 |
| `MS-1`（canonical-first ＋ source-specific mapping） | **`Inherited Constraint`（`AC-18` ／ `AC-19`）** | 低 ／ 中 | 与 Human-approved Option B ／ Option D 一致 |
| `MS-2`（precedence-first） | **`NOT COMPATIBLE`（`AC-18`）** | — | global precedence 已 `NOT ADOPTED` |
| `MS-3`（preserve raw 供人工判读） | 兼容（**仅**限既有 carrier 位置） | 中 | **不得**新增 carrier ／ literal |
| Adapter-side mapping 表达（Decision 1） | 均兼容 | 低 ／ 中 | 属实现与 architecture 边界 |
| `Package identity` ／ `manifest` generation 归属（Decision 2） | **开放** —— 已批准 policy **未**指派 | 低 ／ 中 | `ADEP-11`；**不**得写成 inherited does-not-own |
| Adapter 与 Permission & Security 接口（Decision 7） | **已登记（`Decision 7`，Issue #86）：** **Option ① —— declarative access-requirement interface**（仅限 Data Landing Zone 侧） | 低 ／ 中 | Adapter **只声明** minimum authorized access requirements；**不**拥有 authorization ／ credential lifecycle ／ Secret Handling；authorized access 不可用 ⇒ fail closed；具体 mechanism 依赖 `§7` 后续设计；**不**含 source-system connectivity |

---

#### 4.6.7 Cross-Decision Dependencies

| # | Dependency | 说明 |
| --- | --- | --- |
| `ADEP-1` | **任何提交给 `Final Import Contract` 的 package 内容（producer-neutral）↔ acceptance** | **producer-neutral invariant**：**任何**提交给 `Final Import Contract` 的 package 内容**必须**满足 `IC-1` ／ `IC-3` ／ `IC-8` ／ `IC-22` 与 `AC-15`；digest 为 `IG-raw`（exact raw bytes）⇒ **被选中的 producer 不得**在 acceptance 之后改写字节。**current-state（`Decision 2` ／ Issue #74）：** 只有经 **Package Assembly** 形成的**完整 package** 才可提交 `Final Import Contract`；多个 Adapter 的 partial artifacts **不得单独**提交 ／ 视为可接受 package（**禁止 dataset-level partial acceptance**；`IC-13`） |
| `ADEP-2` | **mapping decision ↔ `Master Data Mapping` ownership** | canonical identity ／ relationship resolution contract 已 `DESIGN RESOLVED`；Adapter **只**提供 source-specific 实现，**不**改 contract。**责任交接点已由 `Decision 1(b)`（Issue #72）登记**：Adapter **允许**在内部定义 source-specific resolution rules，但须 explicit ／ deterministic ／ traceable ／ reproducible，且**不得**越过已 `DESIGN RESOLVED` 的 canonical mapping contracts ／ 建立 global precedence。**current-state（`Decision 4` ／ Issue #78）：** 该等 rule 的 **contract requirements** 与 **representation carrier deferral** 已登记（`Decision 4` Option ①）；**representation carrier 属 Architecture ／ Implementation**，**不**在本层决定（`ADEP-8`） |
| `ADEP-3` | **unresolved mapping ↔（分层）Data Validation taxonomy** | **分层 handoff（`Decision 3` ／ Issue #76 —— 不得混淆）：**<br>**(1) Decision 3 fail-closed path：** unresolved ／ ambiguous ／ conflicting 时 Adapter 对 **affected dataset artifact 不产出** canonical artifact（`UF-2`）⇒ **该路径上不得伪造 canonical Validation Issue ／ Reason**；source-side root cause 由 **non-canonical** Failure ／ Quarantine Interface 承载；**不得** silent skip ／ 强制压成 `null` ／ fuzzy ／ LLM guess；approved missing（`3.1`）与 unresolved（`3.2`）**必须区分**。<br>**(2) 既有 Data Validation taxonomy：** **只**在**真实 canonical validation context**（canonical artifact 实际存在且可由**已批准 carrier** 表达）中继续适用，并以既有 reason（`SEMANTIC_UNRESOLVED` ／ `MISSING` ／ `INVALID_TYPE`）表达；**不因 Decision 3 新增** reason，**亦不**要求 Data Validation 对**不存在**的 canonical artifact 反向生成 ／ 猜测 reason；**不重开 `§4.4`** |
| `ADEP-4` | **evidence locator ／ basis 的 carrier obligation（producer-neutral）↔ FCM ／ FIC carrier** | carrier 位置与 literals 已固定（`"_meta"` ／ `provenance_associations` ／ `observation` ／ `evidence` ／ `mapping_basis`）：**任何**写入者**必须**依该 shape 写入，**不**得自定义 shape。**谁**负责生成该 metadata 内容（producer ownership）⇒ **已由 `Decision 2`（Issue #74）登记**：**每个 Adapter 写入其自身掌握的 source-derived record-level provenance ／ locator ／ `mapping_basis`**，且只能使用已批准 carrier ／ literals（`P-2` ／ `ADEP-11`）。**`mapping_basis` 的语义粒度已由 `Decision 5`（Issue #82）登记**：**Option ① minimal rule ／ revision reference** —— 只标识 **approved mapping rule identity ＋ revision identity**，不承载 evidence ／ rule logic ／ explanation ／ mini-schema；**具体 string syntax ／ encoding 留属 Architecture ／ Implementation** |
| `ADEP-5` | **multi-source canonical stability ↔ `Global Source-Field Precedence = NOT ADOPTED`** | 跨 source precedence **不得**被 Adapter 重新引入（`AC-18`）；drift 防护须以显式 mapping 与 unresolved 表达实现。**current-state（`Decision 6` ／ Issue #84）：** 多 Adapter governance 与 canonical semantic drift 防护的**边界**已登记为 **explicit cross-Adapter consistency obligation**（Option ②）—— canonical-first 保持；相同或重叠 canonical target ／ scope 的多 Adapter mapping **必须**满足显式一致性义务；**禁止** Adapter priority ／ source priority ／ Global Source-Field Precedence ／ first-wins ／ latest-wins ／ LLM ／ heuristic ／ silent reconciliation；unresolved drift 与 `Decision 3` fail-closed 对齐；**具体 detection mechanism 属 Architecture ／ Implementation** |
| `ADEP-6` | **Adapter failure 表达 ↔ Layer 1 ／ Layer 2 归属（分层）** | **Layer 1：** artifact 结构问题（required artifact absent ／ unreadable ／ digest 不符等）归 `Final Import Contract`（`AC-16` ／ `AC-22`）。**Layer 2 ～ 4：** semantic ／ field 问题归 Data Validation，**但只在真实 canonical validation context 中适用**。**non-canonical path（`Decision 3` ／ Issue #76）：** 当 Adapter 对 affected dataset artifact **fail closed、不产出** canonical artifact 时，该 failure context 走 **non-canonical** Failure ／ Quarantine Interface ⇒ **不得**伪造 Validation Issue ／ Reason（`ADEP-3` ／ `ADEP-12`）。Adapter **不**自行产生 package disposition 或新 reason |
| `ADEP-7` | **Adapter ↔ `Permission & Security`（`§7` = `DESIGN PENDING`）** | **历史：** **Data Landing Zone 侧**的读取范围 ／ secret 边界未定 ⇒ 本层**不得**设计，只能登记依赖与接口期待。**current-state（`Decision 7` ／ Issue #86）：** 该**接口期待**已登记为 **Option ① —— declarative access-requirement interface**（Adapter **只声明** minimum authorized access requirements ／ security dependencies；**不**拥有 authorization decision ／ credential lifecycle ／ Secret Handling；authorized access 不可用 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ **fail closed**）；`§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling **仍为 `DESIGN PENDING`**，其设计属 `§7`；**不**涉及 source-system credentials 或 export-side protocol（`ADEP-9`） |
| `ADEP-8` | **Adapter ↔ Architecture Decisions（尚无 ADR）** | framework ／ technology ／ deployment 选择属 `§10`；本层**不得**预选 |
| `ADEP-9` | **Adapter ↔ `Data Landing Zone` 之前链路** | Controlled Export 与 **source-system connectivity**（连接源系统、export-side protocol ／ credentials）由 source system 侧完成（`§3.1` ／ `§3.3`）；Adapter **不**设计 export 侧实现，**不**扩大 source access。若未来要把 source-system connectivity 纳入 Adapter，**必须**另走 **Human-approved `§3` design change**。**current-state（`Decision 7` ／ Issue #86）：** Adapter 的 access requirement **严格限于 Data Landing Zone ／ Controlled Export 之后**，**不含** source-system ／ ERP ／ SRM ／ Production DB credentials 与 export-side protocol credentials；Decision 7 **未**授权任何 source-system access 扩展 |
| `ADEP-10` | **Adapter ↔ real source field 未知** | 真实 ERP field 未知 **≠** design pending（`AC-17`）；Adapter 的存在**不**要求现在选定真实 field |
| `ADEP-11` | **`Decision 2` ↔ package ／ manifest producer ownership** | **历史（Decision 1 时点）：** 已批准 policy **未**指派 `Package identity` ／ `manifest` generation 的职责 ⇒ 当时为 **open**。**current-state（Issue #74）：** 已由 **`Decision 2`（Option ②）登记** —— 每个 Adapter 产出其 canonical dataset artifact（含其 source-derived provenance ／ locator ／ `mapping_basis`）；独立 **Package Assembly** 汇集 artifacts 并生成 ／ 绑定 `snapshot_package_id`、生成 Manifest、建立 package organization、形成**完整、原子** package 后提交 `Final Import Contract`；`Final Import Contract` **不**生产 package。**Package Assembly 为 conceptual responsibility**，其运行形态与 technology **不在**本 Decision 范围 |
| `ADEP-12` | **`Decision 3`（`UF-2` ／ fail-closed）↔ 已批准 carrier contract ＋ Failure ／ Quarantine Interface** | **历史（Decision 1 ／ 2 时点）：** `UF-1` ／ `UF-2` ／ quarantine 若需新 interface ／ artifact ／ operational state ⇒ 已批准 carrier（`§4.3.25` ／ `§4.3.28 E`，unknown `"_meta"` member ⇒ reject）**无**对应位置 ⇒ 依赖单独 Human-authorized design change。**current-state（Issue #76）：** `Decision 3` 已登记「条件组合，以 **`UF-2` ／ fail-closed** 为主」，并**已授权**后续**单独设计**一个 **non-canonical Adapter Failure ／ Quarantine Interface**（承载 source evidence reference ／ unresolved ／ unsupported ／ failure context ／ mapping attempt ／ rule context 与诊断信息）。**该 interface：** **不得**进入 Snapshot Package、**不得**往现有 canonical record ／ dataset ／ `"_meta"` 偷加字段、**不得**修改现有 FCM ／ FIC carrier、**不得**改变 canonical schema ／ semantic；其**物理形态 ／ schema ／ storage ／ API 仍未定**（本 Decision 不决定） |
| `ADEP-13` | **`source extraction` ／ generic field-identification ／ exported-artifact format ／ protocol handling ownership ↔ 已批准 policy 的覆盖范围** | **历史（AB-05 时点）：** `§3` 批准的是 **read boundary**；`§4.5` 系列批准的是 **source-specific mapping responsibility ＋ mapping constraints**；**二者均未**批准上述**通用 ownership** ⇒ 当时该等职责为 open。**current-state：** 已由 **`Decision 1(a)`（Issue #72 Human-approved）** 明确指派给 **Adapter Boundary**（在 Controlled Export ／ Data Landing Zone **之后**），并**不含** source-system connectivity ／ export-side protocol ／ credentials ⇒ 该 ownership **已登记**（见 `AC-22` ／ `4.6.5 A`）；**producer ownership 亦已登记**（`Decision 2`，见 `ADEP-11`） |

---

#### 4.6.8 Review Findings

**`ARF-1`（Q1 Ownership）**
**历史 `Inherited Constraint`（`AC-22` 前 5 项）：** ① `§3` read boundary（只处理 Data Landing Zone
业务数据、**不**直连 source system、unavailable ⇒ fail closed）；② **source-specific semantic mapping
responsibility ＋ mapping constraints**（按 `§4.5.2` ／ `§4.5.11` ／ `§4.5.21` 各自实际范围）；
③ evidence locator ／ basis 的 **carrier obligation**（`§4.3.28 E`）；④ 各层**明确**的 does-not-own 与
`FCM` ／ `Data Validation` ／ `FIC` 职责。
**本层 newly Human-approved registered policy（**不是** historical inherited）：**
⑤ **`Decision 1(a)`（Issue #72）** —— Data Landing Zone **之后**的读取 ／ 提取、
`exported-artifact format ／ protocol handling`、`generic source-field identification`、
`source-specific mapping execution ／ realization` 归 Adapter（**不含** source-system connectivity）；
⑥ **`Decision 2`（Issue #74）** —— **producer ／ Package Assembly ownership**：Adapter 拥有其
canonical dataset artifact production 与 record-level provenance ／ locator ／ `mapping_basis` 写入；
独立 **Package Assembly**（conceptual responsibility）拥有 `snapshot_package_id` ／ Manifest ／
package organization ／ 完整 package 组装；`Final Import Contract` **只**验证 ／ disposition。
`AC-23` 同时确认 **ownership 列表只在已批准部分成立**。
**已由 `Decision 1` 登记：** `source extraction` 责任、generic source-field identification ownership、
`exported-artifact format ／ protocol handling` ownership、Adapter 与 `Master Data Mapping` 的 mapping decision 分工
（`Decision 1(b)`）—— 见 `4.6.5 A` 的 **A-2** registered 表与 **`§4.6.10` `Decision 1` Human Decision Record**。
**已由 `Decision 2` 登记（Issue #74）：** `Package identity` ／ `manifest` generation 与
**producer ownership** —— 每个 Adapter 产出其 canonical dataset artifact 并写入其 source-derived
provenance ／ locator ／ `mapping_basis`；独立 **Package Assembly**（conceptual responsibility）
负责 `snapshot_package_id` ／ Manifest ／ package organization ／ 完整 package 组装；
`Final Import Contract` **只**验证 ／ disposition（`ADEP-11` ／ **`§4.6.10` `Decision 2` HD Record**）。
**已由 `Decision 7` 登记（Issue #86）：** Adapter ↔ `Permission & Security` 的 **interface expectation** —— Adapter **只声明**执行已批准职责所需的 minimum authorized access requirements ／ security dependencies（Data Landing Zone-side），**不**拥有 authorization decision ／ credential lifecycle ／ Secret Handling；authorized access 不可用 ⇒ **fail closed**（`ADEP-7` ／ **`§4.6.10` `Decision 7` HD Record**）。
**仍未决（**不得**写成 inherited，**亦不得**写成已登记）：** **Failure ／ Quarantine Interface 的 physical shape ／ schema ／ runtime realization**（已授权单独设计，**尚未** operationally available；`ADEP-12`）；`§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 的**具体设计**（**`DESIGN PENDING`**）。
**另：** `source-system connectivity`（连接 source system ／ export-side credentials ／ protocol）
**不属** POC Adapter boundary（`AB-02` ／ `ADEP-9`）；若要纳入须另走 Human-approved `§3` design change。

**`ARF-2`（Q2 Input ／ Output Contract）**
**`Inherited Constraint`：** input **只能**是 Data Landing Zone 中的 Controlled Export 产物（`AI-1`）；
output **必须** FIC-valid（**`P-1` invariant**）。
**已登记（`Decision 2` ／ Issue #74）：** **producer ownership（`P-2`）** —— 每个 Adapter 产出其
canonical dataset artifact（含其 source-derived provenance ／ locator ／ `mapping_basis`）；
独立 **Package Assembly** 汇集 artifacts、生成 `snapshot_package_id` ／ Manifest 与 package organization，
形成**完整、原子** Snapshot Package 后提交 `Final Import Contract`；partial artifacts **不得单独**
视为可接受 package（**禁止 dataset-level partial acceptance**）。
**本 Review 不写**任何 connector 或 runtime 流程，**不**假设 Adapter 与 source system 的连接，
**亦不**选择 Package Assembly 的运行形态。

**`ARF-3`（Q3 Determinism ／ Fail-safe）**
**`Inherited Constraint`：** `AC-5` ～ `AC-10` 已唯一确定
deterministic ／ explicit ／ traceable ／ reproducible 与禁止 auto-reconciliation ／ silent fix-up。
**已登记（`Decision 3` ／ Issue #76）：** unresolved ／ ambiguous ／ conflicting 时**以 `UF-2` ／ fail-closed 为主**
—— Adapter 对 **affected dataset artifact** 必须 fail closed，**不得**产出伪 canonical artifact；
**不得** silent skip record ／ 强制压成 canonical `null` ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization ／
自行扩展 canonical semantic ／ enum ／ mapping contract。
**仍未定：** Failure ／ Quarantine Interface 的**物理形态 ／ schema**（已授权**单独设计**，`ADEP-12`）。

**`ARF-4`（Q4 Missing ／ Ambiguous 归属）**
**`Inherited Constraint`：** 四种 root condition 的**validation 归属**已由 `§4.5.21` ／ `AC-9` ／
`AC-10` ／ `AC-16` 唯一确定（见 4.6.5 D 表）。
**已登记（`Decision 3` ／ Issue #76 —— **registered**，非 inherited）：** ① **approved missing**
（mapping contract 明确允许 source absence 映射为 canonical `null` ／ missing，且 evidence 确属该语义）
为**正常 missing**，Adapter 可按**既有** contract 产出 missing ／ `null`；
② **unsupported source field ／ vocabulary ／ exported-artifact shape ／ 无法识别的 source input**
属 **Adapter-side unsupported ／ failure condition** ⇒ Adapter 对 affected dataset artifact **fail closed**，
**不产出** canonical artifact，**不**生成假的 canonical artifact，且**不**由 Data Validation 反向猜测 source-side root cause；
③ Adapter **不**自行产生 Layer 1 类 package disposition 或新 Validation Reason。
**分层 handoff（`ADEP-3` ／ `ADEP-6` 已同步）：** fail-closed path 上**不得伪造** canonical Validation Issue ／ Reason；
既有 taxonomy **只**在**真实 canonical validation context** 中适用。
**仍未定：** Failure ／ Quarantine Interface 的**物理形态 ／ schema**（已授权单独设计，**尚未** operationally available）。

**`ARF-5`（Q5 Evidence Locator ／ Mapping Basis）**
**`Inherited Constraint`（**producer-neutral** carrier obligation）：** **任何**写入 canonical artifact 的
producer **必须**把 `locator` ／ `basis` 内容写入**已固定**的 carrier（`ADEP-4`；
依据 `§4.3.28 E` 的 `"evidence"` ／ `"mapping_basis"` 与 `§4.5.2` 的 traceable requirement）。
carrier shape 与 literals 已由 FCM ／ FIC 固定，**本层不得**新增。
`AC-13` 要求 locator 保持原始 identity value：**禁止** trim ／ case ／ Unicode ／ numeric coercion。
**已登记（`Decision 2` ／ Issue #74）：** ① **谁**是该 metadata 的 producer ——
**每个 Adapter 负责写入其自身掌握的 source-derived record-level provenance ／ evidence locator ／
`mapping_basis`**，且**只能**使用已批准 carrier ／ literals。
**已登记（`Decision 5` ／ Issue #82）：** ② `mapping_basis` 的**语义粒度** —— **Option ① minimal rule ／
revision reference**：该 exact JSON string 只标识本次 mapping ／ resolution 使用的
**approved mapping rule identity ＋ revision identity**（可回答「该 canonical result 出自哪一 approved rule 的哪一 revision」），
**不**承载 source evidence ／ rule logic ／ explanation ／ rationale ／ mini-schema；
`evidence` ／ `mapping_basis` ／ approved mapping rule **三者职责分离**，可复现性由三者组合建立；
**具体 string syntax ／ encoding 仍属 Architecture ／ Implementation**。
**仍未决：** 仅 **`Decision 8`** 所辖事项（`Decision 7` 的 interface expectation **已登记**；
`§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 的**具体设计**仍为 `DESIGN PENDING`，
但该 `DESIGN PENDING` **不等于** `Decision 7` 未决）。

**`ARF-6`（Q6 Multi-source Stability）**
**`Inherited Constraint`：`MS-1`**；`MS-2` = `NOT COMPATIBLE`（`AC-18`）。
**已登记（`Decision 6` ／ Issue #84 —— **registered**，非 inherited）：** 多 Adapter 共享 canonical 约定的**登记与治理** = **canonical-first ＋ explicit cross-Adapter consistency obligation**（Option ②）：多 Adapter 指向**相同或重叠** canonical entity ／ field ／ semantic ／ relationship ／ applicability scope 时，其 approved rules ／ revisions **必须**可被检查为与 current approved canonical contract 及各自声明的 source scope ／ canonical target 一致，且**不存在**未解释的 semantic contradiction；**禁止** Adapter priority ／ source priority ／ first-wins ／ latest-wins ／ LLM ／ heuristic ／ silent reconciliation，**不得**由 Package Assembly 自行解释或修复；unresolved drift 与 `Decision 3` fail-closed 对齐；**不得**新增 carrier ／ Validation Reason ／ Category ／ status enum。
**仍未决（属 Architecture ／ Implementation）：** drift 的**具体检测 mechanism** 与两个 conceptual check points 的实现形态（`Decision 6` 6.3 ／ 6.7）。

**`ARF-7`（Q7 What Must Close Here vs Elsewhere）**
**必须在本层关闭：** ownership 边界（`ARF-1`）、input ／ output conceptual contract（`ARF-2`）、
determinism ／ fail-safe 要求（`ARF-3`）、unresolved 归属与 Adapter-side contract（`ARF-4`）、
locator ／ basis 的 carrier obligation（`ARF-5`）、multi-source 原则（`ARF-6`）、与 `Permission & Security`
及 Architecture 的接口期待（`ARF-8`）。
**已由 `Decision 7`（Issue #86）登记：** 与 `Permission & Security` 的**接口期待**（Adapter 声明式 minimum authorized access requirements；authorized access 不可用 ⇒ fail closed）—— 见 `ARF-8` ／ `A-11`。
**已由 `Decision 8`（Issue #88）登记：** 本层 **minimum closure criteria** = **`A-1` ～ `A-14`**（Human-approved **mandatory**）；`A-15` ／ `A-16` 为 **non-blocking** design objectives；逐项 verification 与**条件性**状态转换由后续 **Dedicated Adapter Boundary Closure Design Change PR** 执行 —— **`Decision 8` 本身不推进状态**。**该 Closure Validation 已于 Issue #90 执行：`A-1` ～ `A-14` = `PASS` ⇒ `Adapter Boundary` = `DESIGN RESOLVED`**（见 **`§4.6.21`**）。
**明确留给其他层：** RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 的**具体设计**（`§7`，仍 **`DESIGN PENDING`**）、
framework ／ technology ／ deployment（`§10`）、runtime 实现、真实 source field 选择。
**明确留在 POC 之外：** **source-system connectivity ／ export-side protocol ／ export-side credentials**
（`§3.1` ／ `§3.3`；若要纳入 Adapter 需另走 Human-approved `§3` design change）。

**`ARF-8`（Cross-layer Interface Expectation）**
**已登记（`Decision 7` ／ Issue #86 —— **registered**，非 inherited）：** Adapter 与 `Permission & Security` 之间的**接口期待** = **Option ① —— declarative access-requirement interface**：Adapter **只声明**其在 **Data Landing Zone 侧读取 exported artifacts** 所需的 minimum authorized access requirements ／ security dependencies（resource boundary ／ operation ／ logical data scope ／ authorized access context ／ secret dependency），**不**决定授权实现、**不**自行放宽权限；authorized access 不可用 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ **fail closed ／ do not proceed**。`§7` 为 `DESIGN PENDING` ⇒ **本层不得**设计 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 或 secret mechanism（`AC-21` ／ `ADEP-7`）；**interface expectation ≠ injection mechanism**。该接口**不**涉及 source-system credentials。**`Decision 8`（Issue #88）：** `§7` 的 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 仍 `DESIGN PENDING`，但本层 security interface expectation 已由 `Decision 7` 登记 ⇒ 该 remaining `§7` 设计**不自动阻止** Adapter Boundary **conceptual closure**（`§4.6.10` `Decision 8` 8.6）。

**`ARF-9`（Fail-safe Summary）**

**继承的 fail-safe invariant（`Inherited Constraint`）：** 在任何无法可靠完成映射的情形下，
Adapter **必须** fail safe：

```
不猜测
不 silent skip
不 silent normalization
不 fallback 到未批准来源
absent 与 unresolved 不得压平
```

不得把「没有 source data」与「有 data 但无法映射」压平为同一结果（`AC-9`）。

**`Decision 3` registered outcome（Issue #76 —— **registered**，**不是** inherited）：**
unresolved ／ ambiguous ／ conflicting ／ unsupported 的 **fail-closed path**：

```
affected dataset artifact 不产出 canonical artifact
不得伪造 canonical Validation Issue ／ Reason
source-side context 进入 non-canonical Failure ／ Quarantine Interface
```

**既有 Data Validation taxonomy 仅在真实 canonical validation context 中适用**（`ADEP-3` ／ `ADEP-6`）；
**approved missing** 继续按既有 canonical contract 处理。

**旧 current-state 更正：** 本 Review 早期曾写「*如何* 在 package 内承载 unresolved 事实尚未决定」。
**current-state：** Failure ／ Quarantine Interface **明确不进入 Snapshot Package**（不得往现有 canonical
record ／ dataset ／ `"_meta"` 偷加字段，不得改现有 FCM ／ FIC carrier），其**单独设计已获 Human 授权**；
**仍未完成**的是该 interface 的 **physical shape ／ schema ／ runtime implementation** ⇒ **尚未** operationally available。

---

#### 4.6.9 Minimum Closure Criteria（Human-approved —— `Decision 8` ／ Issue #88）

> **current-state（Issue #88）：** `A-1` ～ `A-14` 已由 **`Decision 8`** Human Approval 接受为 **MANDATORY MINIMUM CLOSURE CRITERIA**；`A-15` ／ `A-16` 保持 **POC DESIGN OBJECTIVE（non-blocking）**。
> **Closure Verification 已完成（Issue #90）：** `A-1` ～ `A-14` = **`PASS`**（0 FAIL）；`Adapter Boundary` 现为 **`DESIGN RESOLVED`**（见 **`§4.6.21`**）。逐项 **PASS ／ FAIL** verification 已由
> **Dedicated Adapter Boundary Closure Design Change PR**（**Issue #90**）执行完毕 —— `A-1` ～ `A-14` **全部 PASS**，故已登记
> `DESIGN PENDING → DESIGN RESOLVED`（任一 FAIL 本应保持 `DESIGN PENDING`；本次无 FAIL）。
> 见 **`§4.6.10` `Decision 8` Human Decision Record**。

| # | Criterion | 类别 |
| --- | --- | --- |
| `A-1` | Adapter **owns ／ does not own** 边界已登记，且**只**把 current approved policy **明确规定**的事项写成 approved；**并区分授权来源**（historical `Inherited Constraint` vs 本层 newly Human-approved registered policy）。**历史 inherited：** `§3` read boundary ／ `§4.5` mapping responsibility ＋ constraints ／ locator ／ basis carrier obligation ／ 各层 does-not-own 与 `FCM` ／ `Data Validation` ／ `FIC` 职责。**已登记（`Decision 1(a)`，Issue #72）：** Data Landing Zone **之后**的读取 ／ 提取、`exported-artifact format ／ protocol handling`、`generic source-field identification`、`source-specific mapping execution ／ realization` ⇒ Adapter **owns**；**明确不含** `source-system connectivity` ／ Controlled Export 上游 ／ export-side protocol ／ credentials。**已登记（`Decision 2`，Issue #74）：** `Package identity` ／ `manifest` generation 与 **producer ownership** ⇒ 每个 Adapter 产出其 canonical dataset artifact（含其 source-derived provenance ／ locator ／ `mapping_basis`）；独立 **Package Assembly** 负责 `snapshot_package_id` ／ Manifest ／ package organization ／ 完整 package 组装（`ADEP-11`）。**已登记（`Decision 3`，Issue #76）：** unresolved ／ unsupported 的 **fail-closed 策略**、**responsibility 归属**（source-side context 归 non-canonical Failure ／ Quarantine Interface）与 **interface 的单独设计授权** ⇒ **registered**（`ADEP-12`）。**已登记（`Decision 4`，Issue #78）：** source-specific mapping rule 的 contract requirements 与 **representation carrier deferral** ⇒ **registered**（`ADEP-2` ／ `ADEP-8`）。**已登记（`Decision 7`，Issue #86）：** Adapter ↔ `Permission & Security` **interface expectation**（**Option ① declarative access-requirement interface**；Adapter **只声明** minimum authorized access requirements ／ security dependencies，**不**拥有 authorization decision ／ credential lifecycle ／ Secret Handling；authorized access 不可用 ⇒ **fail closed**）⇒ **registered**（`ADEP-7`）。**仍未完成但由 `Decision 8`（Issue #88）明确为 non-blocking（不阻止 Adapter conceptual closure）：** ① **Failure ／ Quarantine Interface 的 physical shape ／ schema ／ runtime realization**（已授权单独设计，**尚未** operationally available）；② `§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 的**具体设计**（**`DESIGN PENDING`**）；二者**不**构成本层 mandatory closure 的 blocker，**亦不得**被写成已完成。**Decision 3 的 strategy ／ responsibility ／ authorization 本身不得**被重新列为 unresolved Human Decision；**未**以任何 Review Finding 或推导作为 approved authority | MANDATORY CLOSURE CRITERION |
| `A-2` | Adapter **input conceptual contract** 已登记（只接受 Data Landing Zone 中的 Controlled Export 产物；**不**含 source-system connectivity；无直连 ／ 无 source access 扩大） | MANDATORY CLOSURE CRITERION |
| `A-3` | Adapter **output conceptual contract** 已登记（canonical artifact set ＋ mapping evidence；**不**宣告 acceptance ／ disposition）；**producer ownership 已由 `Decision 2`（Issue #74）登记**：Adapter 产出其 canonical dataset artifact 并写入其 source-derived provenance ／ locator ／ `mapping_basis`；`snapshot_package_id` ／ `manifest` ／ package organization 归 **Package Assembly**（独立 conceptual responsibility）；只有**完整 package** 可提交 `Final Import Contract`，partial artifacts **不得单独**视为可接受 package（**禁止 dataset-level partial acceptance**） | MANDATORY CLOSURE CRITERION |
| `A-4` | **Determinism 要求**已登记（deterministic ／ explicit ／ traceable ／ reproducible；禁 fuzzy ／ similarity ／ LLM choose ／ silent normalization），且**不依赖** implementation 选择；**并含 `Decision 1(b)`（Issue #72）**：Adapter **允许**在内部定义 source-specific resolution rules，但**必须**满足同一 determinism 要求，且**不得**修改 ／ 重新定义 canonical semantic、**不得**建立 global source-field precedence、**不得**越过已 `DESIGN RESOLVED` 的 canonical mapping contracts。**已由 `Decision 4`（Issue #78）登记完整的 rule-level contract requirements**：明确 source ／ source scope 与 logical dataset ／ canonical target、可审计可复现的 rule ／ revision identity 与「canonical result ← approved rule ／ revision」可追溯性、**禁 hidden default**；**representation carrier 明确 deferred** 给 Architecture ／ Implementation（**不创建**强制 `Mapping Registry` component）；missing ／ conflicting ／ 非确定性 rule ⇒ 服从 `Decision 3` fail-closed | MANDATORY CLOSURE CRITERION |
| `A-5` | **Fail-safe 要求**已登记：unresolved ／ unsupported ／ not-evaluable 时**不得**猜测 ／ 静默省略 ／ fallback 到未批准来源；且区分 `absent` 与 `unresolved`。**已由 `Decision 3`（Issue #76）登记**：unresolved ／ ambiguous ／ conflicting 时**以 `UF-2` ／ fail-closed 为主**，Adapter 对 affected dataset artifact **不产出** canonical artifact | MANDATORY CLOSURE CRITERION |
| `A-6` | **unresolved mapping 的 Adapter-side contract** 已登记（`UF-2` 为**主要策略**、条件组合；`UF-1` 未选为主要路径、`UF-3` = `NOT COMPATIBLE`）；**分层 handoff 已登记（`Decision 3` ／ Issue #76）：** **fail-closed path** 上 Adapter 对 affected dataset artifact **不产出** canonical artifact ⇒ **不得伪造** canonical Validation Issue ／ Reason，source-side context 由 **non-canonical** Failure ／ Quarantine Interface 承载；**既有 Data Validation taxonomy 只**在**真实 canonical validation context** 中适用，**不新增** reason。**承载方式：** `Decision 3` 已**授权单独设计**该 interface（**不**进入 Snapshot Package、**不**改现有 FCM ／ FIC carrier、**不**新增 canonical 字段），其**形态 ／ schema 仍未定** | MANDATORY CLOSURE CRITERION |
| `A-7` | **unsupported ／ 未批准 source field ／ vocabulary ／ exported-artifact shape** 的 fail-safe 行为与上报边界已登记（属 **Adapter-side unsupported ／ failure condition** ⇒ fail closed、**不**生成假 canonical artifact、**不**由 Data Validation 反向猜测 source-side root cause），且明确 Adapter **不**自行产生 package disposition 或新 Validation Reason | MANDATORY CLOSURE CRITERION |
| `A-8` | `Stable Source Evidence Locator` 与 `Mapping ／ Resolution Basis` 的 **producer-neutral carrier obligation** 已登记（**任何**写入 canonical artifact 的 producer **必须**依 FCM ／ FIC 已固定 carrier 写入并保持原始值，**不新增** carrier），且保持 `AC-13` 的「保持原始 identity value」要求；**谁**是该 metadata 的 producer（producer ownership）**已由 `Decision 2`（Issue #74）登记**：**每个 Adapter 负责写入其自身掌握的 source-derived record-level provenance ／ evidence locator ／ `mapping_basis`**，且**只能**使用已批准 carrier ／ literals（`P-2` ／ `ADEP-4` ／ `ADEP-11`）；**`mapping_basis` 的语义粒度已由 `Decision 5`（Issue #82）登记**：**Option ① minimal rule ／ revision reference** —— 只标识 **approved mapping rule identity ＋ revision identity**（可回答「该 canonical result 出自哪一 approved rule 的哪一 revision」）；**`evidence` ／ `mapping_basis` ／ approved mapping rule 三者职责分离**，可复现性由三者组合建立；**不**承载 evidence ／ rule logic ／ explanation ／ rationale ／ mini-schema；**具体 string syntax ／ encoding 属 Architecture ／ Implementation**；**不新增** `"_meta"` member ／ literal ／ carrier | MANDATORY CLOSURE CRITERION |
| `A-9` | **多 source ／ 多 Adapter semantic stability** 要求已登记（canonical-first；**不**建立跨 source precedence；冲突表达为 unresolved ／ consistency issue）；**已由 `Decision 6`（Issue #84）登记**：**Option ② —— explicit cross-Adapter consistency obligation**（多 Adapter 指向**相同或重叠** canonical entity ／ field ／ semantic ／ relationship ／ applicability scope 时，其 approved mapping rules ／ revisions **必须**可被检查为与 current approved canonical contract 及各自声明的 source scope ／ logical dataset ／ canonical target 一致、**不存在**未解释的 semantic contradiction、**不依赖** implicit Adapter priority ／ first-wins ／ latest-wins ／ source priority ／ LLM ／ heuristic ／ silent normalization）；**两个 conceptual check points** = rule registration ／ revision change **之前** 与 overlapping canonical use **之前**；unresolved drift **不得** first-wins ／ latest-wins ／ priority ／ LLM ／ heuristic ／ silent reconcile，**不得**由 Package Assembly 自行解释或修复 ⇒ 与 `Decision 3` fail-closed 对齐（**不**新增 Validation Reason ／ Category ／ status enum）；**具体 detection mechanism 属 Architecture ／ Implementation** | MANDATORY CLOSURE CRITERION |
| `A-10` | **跨层边界**已登记：`Permission & Security`（scope ／ tool permission ／ secret）／ Architecture（technology）／ Implementation（runtime）各自归属明确，且本层**未**越过。**已由 `Decision 7`（Issue #86）登记本层侧接口期待**（Adapter **只声明** minimum authorized access requirements；**不**设计 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling；authorized access 不可用 ⇒ fail closed）；`§7` 各 remaining item 仍 **`DESIGN PENDING`** | MANDATORY CLOSURE CRITERION |
| `A-11` | **Adapter 与 `Permission & Security` 的接口期待**已登记（Adapter 需要什么、由谁提供），且**未**设计 RBAC ／ secret 机制。**已由 `Decision 7`（Issue #86）登记：** **Option ① —— declarative access-requirement interface** —— Adapter **只声明**执行已批准职责所需的 **minimum authorized access requirements ／ security dependencies**（resource boundary ／ operation ／ logical data scope ／ authorized access context ／ secret dependency）；**「由谁提供」的实现机制不在本层登记**（授权机制 ／ injection ／ credential lifecycle ／ Secret Handling 属 `§7` ／ Architecture ／ Implementation，仍 **`DESIGN PENDING`**）；authorized access 不可用 ／ 失效 ／ 无法可靠确认 ⇒ **fail closed** | MANDATORY CLOSURE CRITERION |
| `A-12` | Adapter **failure 上报边界**已登记：Layer 1 归 `Final Import Contract`、Layer 2 ～ 4 归 Data Validation；**不新增** category ／ reason | MANDATORY CLOSURE CRITERION |
| `A-13` | **selected-decision composition check**：已选组合与 `§3` hard boundary、`§4.3` FIC、`§4.4` Data Validation、`§4.5` Master Data Mapping 之间**无未登记的跨选择冲突**。**`Decision 8`（Issue #88）要求 Dedicated Closure PR 显式执行该 composition check**（`Decision 1` ～ `7` 的组合 ↔ `§3` ／ `§4.3` ／ `§4.4` ／ `§4.5`） | MANDATORY CLOSURE CRITERION |
| `A-14` | **真实 source field 未知**状态已登记且**不构成** blocker（`DESIGN RESOLVED ≠ real ERP field known ≠ Adapter implemented ≠ tested`）。**`Decision 8`（Issue #88）确认该状态继续 non-blocking**：closure 只能基于 conceptual ／ canonical contract completeness，**不得**把 implementation-time source discovery 变成 design closure prerequisite | MANDATORY CLOSURE CRITERION |
| `A-15` | Human Inspectability（Adapter 的 mapping ／ unresolved 结果可被人工检视与追溯）。**`Decision 8`：** 必须在 Dedicated Closure PR 中显式评估并给出简洁结论 ／ evidence；保持 **POC DESIGN OBJECTIVE**，**不得**升级为 hard closure gate | POC DESIGN OBJECTIVE |
| `A-16` | Implementation Simplicity（Adapter contract 结构最小化）。**`Decision 8`：** 必须在 Dedicated Closure PR 中显式评估并给出简洁结论 ／ evidence；保持 **POC DESIGN OBJECTIVE**，**不得**升级为 hard closure gate | POC DESIGN OBJECTIVE |

`A-15` ／ `A-16` **必须评估**，但**不作为**独立 hard closure blocker；
**不得**把主观判断变成不可验证的 closure Gate。

**`Decision 8`（Issue #88）登记：** `A-1` ～ `A-14` = **Human-approved mandatory minimum closure criteria**；
`A-15` ／ `A-16` 必须在 Dedicated Closure PR 中**显式评估**并给出简洁结论 ／ evidence，
但**不得**升级为 hard closure gate、**不得**阻止 closure —— **除非**评估暴露出已触发
`A-1` ～ `A-14` 中某项 mandatory criterion 的**客观失败**。

**Closure Verification（Issue #90 Dedicated Closure Validation）：** `A-1` ～ `A-14` = **`PASS`**（0 FAIL）；
`A-15` ／ `A-16` = **NON-BLOCKING（已评估）** ⇒ `Adapter Boundary` = **`DESIGN RESOLVED`**（per-criterion evidence ＋ `A-13` composition check 见 **`§4.6.21`**）。

---

#### 4.6.10 Human Decision Required

**Decision 1 —— Adapter 的通用职责 ownership 与 mapping decision 分工如何表达**

> 本 Decision 覆盖 **AB-05** 指出的三项**尚无直接批准依据**的 Adapter 通用职责
> （`source extraction` 责任 ／ generic source-field identification ownership ／
> `exported-artifact format ／ protocol handling` ownership），以及 Adapter 与
> `Master Data Mapping` 的 mapping decision 分工。**已批准**的仅是 `§3` read boundary 与
> `§4.5` 系列 source-specific mapping responsibility ＋ mapping constraints（`AC-22`）。

- **Question：**
  **(a) 通用职责归属：** `source extraction` 责任、**generic source-field identification ownership**、
  **`exported-artifact format ／ protocol handling` ownership** 分别归谁 —— 归 Adapter Boundary、
  归其他层（例如 package assembly ／ Import Contract 侧），还是**不指派**（仅由各层自证符合 contract）？
  **(b) mapping 责任交接点：** Adapter 侧 source-specific mapping 与已 `DESIGN RESOLVED` 的
  canonical mapping contract（`§4.5`）之间的**责任交接点**如何登记 —— Adapter **只**实现已登记的
  resolution contract，**还是**允许 Adapter 在其内部定义 source-specific resolution 规则
  （仍须 explicit ／ deterministic ／ traceable）？
- **Options：**
  **(a)** ① 明确指派给 Adapter Boundary（并登记其与 assembly ／ FIC 的接口）；② 指派给其他层并登记 Adapter 的配合义务；③ 不指派 ownership，只登记各层**必须符合的 contract**（read boundary ＋ FIC-valid invariant ＋ mapping constraints）。
  **(b)** ① 严格分离（Adapter 只提供 source evidence，resolution 由 mapping contract 定义）；② 允许 source-specific resolution 规则，但**必须**显式登记且不改 canonical semantic；③ 两者混合并逐层声明。
- **Trade-offs：** **(a)** ① 最清晰但与已批准文本距离最远、需新增授权；② 边界清楚但可能弱化 Adapter 责任；③ 最小改动、最贴合已批准事实，但留白较多、后续实现需自证。**(b)** ① 最可审计但登记成本高；② 贴近真实 source 差异但有 drift 风险；③ 灵活但需额外登记纪律。
- **Dependencies：** `AC-22` ／ `AC-23` ／ `AC-5` ／ `AC-6` ／ `AC-18` ／ `ADEP-2` ／ **`ADEP-13`**；
  **Human Decision Record 见本 Decision 条目之后**（Issue #72）。
- **What changes：** `A-1` ／ `A-4` 的可判定性；`§4.5` 契约与 Adapter 文档的责任划分表述；
  **哪些通用职责**进入 `4.6.5 A` 的 registered 列 —— **已由 `Decision 1(a)` 登记**（`REGISTERED`），
  **producer ownership 亦已由 `Decision 2` 登记**（Issue #74）。
- **注意：** **不得**仅凭 `§3` read boundary 或 `§4.5` mapping duty **推导**通用 ownership（`AB-05`）；
  所有选项**均不得**修改 canonical identity ／ relationship resolution contract，
  **亦不得**引入 source-system connectivity。

**Decision 1 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #72 Human Decision**。本记录**只**登记已批准的 Decision 1(a) ／ 1(b)，
并执行最小必要 synchronization —— **不**选择 Decision 2 ～ 8、**不**推进 `Adapter Boundary` 状态。

```
Decision Scope     = §4.6.10 Decision 1（(a) 通用职责归属 ／ (b) mapping 责任交接点）
Decision Authority = Human（Issue #72）
Write Scope        = docs/design/poc-design-v0.2.md
```

**Decision 1(a) —— 通用职责归属 = Option ①（APPROVED）**

在 **Controlled Export ／ Data Landing Zone 之后**，以下职责明确归 **Adapter Boundary**：

```
从 Data Landing Zone 读取 ／ 提取 exported artifacts ／ source records
exported-artifact format ／ protocol handling
generic source-field identification
source-specific mapping execution ／ realization
```

**明确边界（保持 —— 不得扩大）：**

```
不包含 Production ERP ／ source-system connectivity
不包含 Controlled Export 上游链路
不包含 export-side protocol ／ credentials
若未来要把 source-system connectivity 纳入 Adapter ⇒ 必须另走 Human-approved §3 design change
```

**Decision 1(b) —— mapping responsibility handoff = Option ②（APPROVED）**

Adapter **允许在其内部定义 source-specific resolution rules**，但**必须**满足：

```
explicit
deterministic
traceable
reproducible
不依赖 LLM guess ／ fuzzy ／ similarity ／ silent normalization
不得修改或重新定义 canonical semantic
不得建立 global source-field precedence
不得越过已 DESIGN RESOLVED 的 canonical mapping contracts
```

**边界（不受本 Decision 影响）：**

- `§3` hard boundary（Controlled Export ／ read boundary ／ no Production write）**未修改**；
- `§4.5` 系列 canonical mapping contracts 与 `BR-*` semantic **未修改**；
- **producer ownership**（artifact ／ package ／ manifest ／ provenance metadata 的 producer）**仍由 Decision 2 决定**；
- **Decision 2 ～ 8 保持未决**。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 1(a) ／ 1(b)        = RECORDED
Decision 2 ～ 8                    = 未决
producer ownership（Decision 2）   = OPEN
POC Design v0.2                   = DRAFT
```

**Decision 2 —— Adapter output 的组织与提交方式（含 `Package identity` ／ `manifest` generation 归属）**
- **Question：** Adapter 产出 canonical artifact set 时，**manifest ／ package identity** 由谁生成 —— ① 由 Adapter 生成、② 由独立 package assembly 步骤生成，还是 ③ 其他形态？多 Adapter 是否可各自产出部分 artifact、output 的提交形态（一次完整 package ／ 分片）如何？
- **Options：** ① 单一 Adapter 生成完整 package（含 manifest）；② 多个 Adapter 各自产出 artifact，由一个 package assembly 步骤生成 manifest；③ 其他有依据的形态。
- **Trade-offs：** ① 最简、single-writer 语义清晰；② 更贴近多 source 现实，但引入 assembly 步骤与 partial 风险；③ 需额外论证。
- **Dependencies：** `AC-15` ／ `AC-23` ／ `ADEP-1` ／ `ADEP-11` ／ `IC-13`（package-level atomic）。
- **What changes：** `A-3` 的登记内容；Adapter 与他方（或独立 assembly 步骤）的接口。
- **注意：** 本项**是 open ownership 问题**（`AC-23`）—— 已批准 policy **未**指派该职责，
  因此 §4.6.5 A 的 ownership 表**不得**把 `Package identity` ／ `manifest generation`
  列为 inherited `does not own`；各 option **均不得**引入 dataset-level partial acceptance，
  **不得**新增 carrier ／ literal。

**Decision 2 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #74 Human Decision**。本记录**只**登记已批准的 Decision 2，并执行最小必要 synchronization ——
**不**选择 Decision 3 ～ 8、**不**推进 `Adapter Boundary` 状态、**不**选择任何实现技术。

```
Decision Scope     = §4.6.10 Decision 2（Adapter output organization ／ producer ownership）
Decision Authority = Human（Issue #74）
Selected Option    = Option ② —— Multi-Adapter artifacts ＋ independent Package Assembly
Write Scope        = docs/design/poc-design-v0.2.md
```

**A. Adapter responsibility（APPROVED）**

每个 Adapter 负责其职责范围内的：

```
source-specific mapping ／ resolution
产出对应的 canonical dataset artifact
将其掌握的 source-derived provenance ／ evidence locator ／ mapping_basis 写入已批准 carrier
保持 deterministic ／ explicit ／ traceable ／ reproducible
不生成 package-level acceptance ／ disposition
```

**B. Package Assembly responsibility（APPROVED —— conceptual responsibility）**

独立的 **Package Assembly conceptual responsibility** 负责：

```
汇集一个或多个 Adapter 产出的 canonical artifacts
生成 ／ 绑定 snapshot_package_id
生成 Manifest
建立 package-level artifact references ／ package organization
形成满足既有 Snapshot / Import Contract 的完整、原子 Snapshot Package
将完整 package 提交给 Final Import Contract
```

**C. Final Import Contract responsibility（保持 —— 不新增职责）**

```
Final Import Contract 只负责验证与 acceptance ／ rejection ／ unusable 等既有 disposition semantics
Final Import Contract 不负责生产 canonical artifacts ／ Manifest ／ package
不改变既有 FIC ／ FCM contract
```

**D. Mandatory Boundary（APPROVED —— 不可让步）**

```
多个 Adapter 可以各自产出部分 canonical artifacts
这些 partial artifacts 不得单独被视为可接受 package
禁止 dataset-level partial acceptance
只有经过 Package Assembly 形成的完整 package 才可提交 Final Import Contract
```

**E. Package Assembly 的形态（本 Decision 不选择）**

Package Assembly 是 **conceptual responsibility ／ boundary**；本 Decision **不选择**其运行形态：

```
不决定它是独立 service ／ module ／ job ／ library ／ workflow node 或其他技术实现
不选择 framework ／ database ／ queue ／ API ／ deployment
```

**F. 边界（不受本 Decision 影响）**

- `§3` hard boundary（Controlled Export ／ read boundary ／ no Production write）**未修改**；
- `§4.3` FCM ／ FIC 与 Snapshot / Import Contract 已 `DESIGN RESOLVED` 的 contract **未重开**；
- 不新增 carrier ／ literal ／ Validation Reason ／ Validation Category ／ status enum；
- **Decision 3 ～ 8 保持未决**。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 2                  = RECORDED（Option ②）
Decision 3 ～ 8                    = 未决
P-2（producer ownership）          = RESOLVED BY DECISION 2
POC Design v0.2                   = DRAFT
```

**Decision 3 —— unresolved ／ unsupported mapping 的 Adapter-side contract 与其承载方式**

> **current-state（Issue #76）：** 本条目为 **Decision source（时点记录）**；其结果已登记于下方
> **`Decision 3 —— Human Decision Record`**（`REGISTERED`）。**该 Decision 不再是 open item。**
- **Question：** 采用 `UF-1`（显式产出 unresolved marker，由 Data Validation 表达后果）、`UF-2`（halt 该 source ／ dataset 的输出并等待人工修复），还是按情形组合？另需裁定：① **unsupported ／ 未批准 source field** 出现时，Adapter 是 skip ／ quarantine ／ 或 stop？② unresolved 事实**如何被承载** —— 若要求在 package 内承载（或 quarantine 需要新 artifact ／ state），**是否**授权单独 carrier ／ interface design change？
- **Options：** `UF-1` ／ `UF-2` ／ 明确条件的组合；(skip ／ quarantine ／ stop) 之一或组合；承载方式 = 既有 approved carrier（root-condition 区分依赖 mapping declaration）／ 单独 Human-authorized carrier ／ interface design change。
- **Trade-offs：** `UF-1` 信息最完整、与既有 taxonomy 对齐，但把不确定性带入下游，且**在既有 carrier 下不能**确定性区分 `absent` 与 `unresolved`；`UF-2` fail-safe 最强、边界最清晰，但需承载「该 attempt 未通过」的事实（已批准 carrier **无**位置 ⇒ 需新 interface ／ state）并定义「何时可重跑」；组合更贴近现实但需登记判定条件。
- **Dependencies：** `AC-7` ／ `AC-8` ／ `AC-9` ／ `AC-10` ／ `AC-16` ／ `ADEP-3` ／ **`ADEP-12`**（carrier 可行性）。
- **What changes：** `A-5` ／ `A-6` ／ `A-7` 的登记内容；Adapter failure 与 Data Validation 的实际交接形态；**是否**需要新增 Human-authorized carrier ／ interface design change。
- **注意：** **`UF-3`（静默省略）与 `AC-8` 不兼容，不作为选项**；**不得**新增 Validation Reason 或 Package disposition；
  **`UF-1` ／ `UF-2` 不得**被当作无条件可用。
  **current-state（Issue #76 —— 状态区分）：** Failure ／ Quarantine Interface 的**单独设计已获 Human 授权**
  （见下方 `Decision 3` HD Record `3.4`），**但**其**物理形态 ／ schema ／ runtime implementation 尚未完成** ⇒
  在完成前**不得**声称该 interface **operationally available**；`UF-2` 的 **fail-closed 行为本身已登记**，
  而**承载其 context 的 interface 仍待单独设计**（`ADEP-12` ／ `A-6`）。

**Decision 3 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #76 Human Decision**。本记录**只**登记已批准的 Decision 3，并执行最小必要 synchronization ——
**不**选择 Decision 4 ～ 8、**不**推进 `Adapter Boundary` 状态、**不**设计 Failure ／ Quarantine Interface 的具体形态。

```
Decision Scope     = §4.6.10 Decision 3（unresolved ／ unsupported mapping strategy）
Decision Authority = Human（Issue #76）
Selected Model     = 条件组合，以 UF-2 ／ fail-closed 为主
Write Scope        = docs/design/poc-design-v0.2.md
```

**3.1 Approved missing case（正常 missing —— **不是** unresolved）**

**当且仅当**：

```
approved mapping contract 已明确允许某 source absence 映射为 canonical null ／ missing
且 source evidence 的确属于该 approved missing 语义
```

Adapter **才**可按**既有** canonical contract 产出对应 missing ／ `null`。
这属于 **正常 missing**，**不是** unresolved。

**3.2 Unresolved ／ ambiguous ／ conflicting source evidence（`UF-2` ／ fail-closed）**

当出现下列任一情形：

```
source evidence 存在，但没有 approved mapping
mapping ambiguous
存在 conflicting source evidence
当前 source-specific resolution rule 无法唯一、确定地得到 canonical result
```

则：

```
Adapter 对 affected dataset artifact 必须 fail closed
不得产出该 dataset 的伪 canonical artifact
```

**明确禁止：**

```
silent skip record
将 unresolved 强制压成 canonical null
通过 fuzzy ／ similarity ／ LLM guess 推断
silent normalization
自行扩展 canonical semantic ／ enum ／ mapping contract
```

**3.3 Unsupported source ／ exported-artifact condition（Adapter-side failure）**

当出现：

```
unsupported source field ／ vocabulary
unsupported exported-artifact shape ／ format
无法按已登记 Adapter contract 解析或识别的 source input
```

则：

```
视为 Adapter-side unsupported ／ failure condition
Adapter 对 affected dataset artifact fail closed
不生成假的 canonical artifact
不由 Data Validation 反向猜测 source-side root cause
```

**3.4 Adapter Failure ／ Quarantine Interface —— Human 授权后续单独设计**

Human **授权后续单独设计**一个 **Adapter Failure ／ Quarantine Interface**，用于承载：

```
source evidence reference
unresolved ／ unsupported ／ failure context
mapping attempt ／ rule context
诊断与后续人工修复所需的信息
```

**同时固定以下边界（不可让步）：**

```
它是 non-canonical interface ／ responsibility
不得进入 Snapshot Package
不得往现有 canonical record ／ dataset ／ "_meta" carrier 偷加字段
不得修改现有 FCM ／ FIC carrier
不得改变 canonical schema ／ canonical semantic
本 Decision 不决定其物理实现：
  不决定 file ／ table ／ DB ／ queue ／ API ／ event ／ service ／ module
  不选择 framework ／ database ／ storage ／ deployment
  不定义最终 runtime schema
```

**3.5 Package Assembly ／ downstream boundary**

```
Package Assembly 只能组装成功产出的 canonical artifacts
不得替 Adapter 猜 mapping
不得生成 placeholder canonical artifact 来掩盖 Adapter failure
不得把 unresolved ／ unsupported condition 当成正常 canonical null
是否能够形成完整 package，继续服从已 DESIGN RESOLVED 的 Snapshot / Import Contract ／ FIC
本 Decision 不引入 dataset-level partial acceptance
```

**3.6 边界（不受本 Decision 影响）**

- `§3` hard boundary、`§4.3` FCM ／ FIC、`§4.4` Data Validation、`§4.5` Master Data Mapping
  已 `DESIGN RESOLVED` 的 contract **未重开**；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal、**未**新增 Validation Reason ／
  Validation Category ／ canonical status enum；
- **Decision 4 ～ 8 保持未决**。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 3                  = RECORDED（条件组合，以 UF-2 ／ fail-closed 为主）
Failure ／ Quarantine Interface    = AUTHORIZED FOR SEPARATE DESIGN（形态 ／ schema ／ runtime 未完成；**尚未** operationally available）
Decision 4 ～ 8                    = 未决
POC Design v0.2                   = DRAFT
```

**Decision 4 —— source-specific mapping 规则的**表达方式**（实现边界）**
- **Question：** source-specific mapping 规则的**表达载体**（configuration ／ mapping registry ／ code）是否必须在本层登记为 contract 要求，还是留给 Architecture ／ Implementation？
- **Options：** ① 本层只要求「必须显式 ／ 确定性 ／ 可追溯」，载体留给 Architecture；② 本层登记一个 conceptual mapping-registry 形态（**不**绑定技术）；③ 其他。
- **Trade-offs：** ① 边界最干净、不预选技术；② 提高可审计性与一致性，但接近实现选择；③ 见论证。
- **Dependencies：** `AC-6` ／ `ADEP-8`（`§10` 尚无 ADR）。
- **What changes：** `A-4` 的登记粒度；是否需要在 Adapter 之外新增 registry 概念。
- **注意：** **不得**选择 framework ／ database ／ API technology；**不得**创建 runtime artifact。

**Decision 4 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #78 Human Decision**。本记录**只**登记已批准的 Decision 4，并执行最小必要 synchronization ——
**不**选择 Decision 5 ～ 8、**不**推进 `Adapter Boundary` 状态、**不**选择 mapping rule 的具体技术载体。

```
Decision Scope     = §4.6.10 Decision 4（source-specific mapping rule representation boundary）
Decision Authority = Human（Issue #78）
Selected Option    = Option ① —— Contract requirements only；representation carrier deferred
Write Scope        = docs/design/poc-design-v0.2.md
```

**4.1 Mandatory contract requirements（APPROVED）**

任何 source-specific mapping ／ resolution rule **必须**：

```
explicit
deterministic
traceable
reproducible
明确其适用的 source ／ source scope
明确其适用的 logical dataset ／ canonical target
具有足以支持审计与复现的 rule identity ／ revision identity
能够追溯「某 canonical result 是依据哪一个 approved rule ／ rule revision 得出的」
```

**明确禁止：**

```
不依赖 hidden default
不使用 fuzzy ／ similarity ／ LLM guess
不进行 silent normalization
不重新定义或扩展 canonical semantic ／ enum ／ mapping contract
不建立 Global Source-Field Precedence
不越过已经 DESIGN RESOLVED 的 canonical mapping contracts
```

**4.2 Missing ／ conflict behavior（APPROVED —— 服从 `Decision 3`）**

当出现：

```
mapping rule 不存在
mapping rules 相互冲突
rule 无法唯一、确定地得到 canonical result
rule 不满足上述 contract requirements
```

则**不得** fallback 到隐式逻辑或猜测，**必须**服从已登记 **`Decision 3`**：

```
affected dataset artifact fail closed
不产出伪 canonical artifact
failure context 按已授权但尚未 operationally available 的
  non-canonical Adapter Failure ／ Quarantine Interface 边界处理
```

**4.3 Representation carrier deferred（APPROVED）**

本 Decision **不规定** mapping rules 必须使用：

```
YAML ／ JSON ／ TOML ／ spreadsheet configuration
mapping registry
database table
Python ／ Java ／ other code
rule engine
service ／ API
framework-specific representation
任何其他具体 storage ／ runtime mechanism
```

上述选择**留给后续 Architecture ／ Implementation**；**无论采用何种方式**，都**必须**满足本 Decision 的 contract requirements。

**4.4 No mandatory Mapping Registry component（APPROVED）**

本 Decision **不创建、也不要求**一个强制的 **`Mapping Registry` architectural component**。
后续 Architecture **可以**选择 registry，**也可以**选择 configuration ／ code ／ other representation；
**只要**满足已批准 contract 即可。

**4.5 `Decision 5` boundary（保持）**

本 Decision **只**要求 mapping rule ／ revision **可被明确识别并审计**。它**不决定**：

```
canonical mapping_basis 字符串的语义粒度
mapping_basis 如何编码 rule id ／ revision ／ explanation
provenance carrier 的新字段或新 literal
```

上述仍属 **`Decision 5`** 或既有 carrier contract，**不得**在本 Decision 中决定。

**4.6 边界（不受本 Decision 影响）**

- `§3` hard boundary、`§4.3` FCM ／ FIC、`§4.4` Data Validation、`§4.5` Master Data Mapping
  已 `DESIGN RESOLVED` 的 contract **未重开**；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal、**未**新增 Validation Reason ／
  Validation Category ／ canonical status enum；
- `Decision 3` 的 Failure ／ Quarantine Interface 具体 design **未修改**；
- **`Decision 5` ～ `8` 保持未决**。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 4                  = RECORDED（Option ①）
mapping rule representation       = ARCHITECTURE ／ IMPLEMENTATION CONCERN（contract requirements 已登记）
Mandatory Mapping Registry        = NOT REQUIRED（本 Decision 不创建）
Decision 5 ～ 8                    = 未决
POC Design v0.2                   = DRAFT
```

**Decision 5 —— `Mapping ／ Resolution Basis` 字符串的语义粒度**

> **current-state（Issue #82）：** 本条目为 **Decision source（时点记录）**；其结果已登记于下方
> **`Decision 5 —— Human Decision Record`**（`REGISTERED`）。**该 Decision 不再是 open item。**
- **Question：** `mapping_basis`（`AC-14`）应登记到何种粒度 —— 只标识「使用哪条 approved mapping」，还是需要包含足以重现 resolution 的判定依据？在**不新增** carrier ／ literal 的前提下如何表达？
- **Options：** ① 最小（标识 mapping 标识符 ／ 规则引用）；② 更完整（含判定依据摘要），仍为单一 exact JSON string；③ 其他。
- **Trade-offs：** ① 成本最低、不引入新语义；② 可审计性更强，但字符串语义需明确边界；③ 见论证。
- **Dependencies：** `AC-13` ／ `AC-14` ／ `AC-18` ／ `ADEP-4`。
- **What changes：** `A-8` 的登记内容；provenance 的可审计程度。
- **注意：** **不得**新增 `"_meta"` member ／ literal ／ carrier；locator 与 basis **不得**被规范化或改写。

**Decision 5 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #82 Human Decision**。本记录**只**登记已批准的 Decision 5，并执行最小必要 synchronization ——
**不**选择 Decision 6 ～ 8、**不**推进 `Adapter Boundary` 状态、**不**定义 `mapping_basis` 的具体 string syntax ／ encoding。

```
Decision Scope     = §4.6.10 Decision 5（Mapping ／ Resolution Basis semantic granularity）
Decision Authority = Human（Issue #82）
Selected Option    = Option ① —— minimal rule ／ revision reference
Write Scope        = docs/design/poc-design-v0.2.md
```

**5.1 Required semantics（APPROVED）**

`mapping_basis` 的职责是：以一个 **exact JSON string**，明确、稳定、可审计地标识本次 semantic
mapping ／ resolution 所使用的 **approved mapping rule identity ＋ revision identity**。
它**必须**至少能够回答：

```
这个 canonical result 是依据哪一个 approved mapping rule 的哪一个 revision 得出的？
```

当 semantic mapping ／ resolution 实际发生、且既有 carrier contract 要求写入 `mapping_basis` 时，
该 exact JSON string **必须**：

```
标识对应的 approved mapping rule identity
标识对应的 rule revision identity
稳定地支持 audit ／ trace ／ reproduce
与 Decision 4 的 rule identity ／ revision identity requirement 对齐
不依赖 hidden default
不允许 fuzzy ／ inferred ／ heuristic basis
不得把一个未批准的 rule 伪装成 approved basis
```

**5.2 Responsibility separation（APPROVED）**

```
evidence        —— 承载 Stable Source Evidence Locator；回答「本次 mapping 基于哪些 source evidence」
mapping_basis   —— 只标识 approved mapping rule ＋ revision；回答「本次 mapping 使用了哪条 approved rule ／ revision」
approved mapping rule —— 承载真正的 deterministic mapping ／ resolution logic；
                        回答「规则本身如何把 source evidence 映射成 canonical result」
```

**可复现性由三者组合共同建立：**

```
Stable Source Evidence Locator
+ mapping_basis（approved rule identity + revision identity）
+ approved mapping rule
= auditable ／ reproducible mapping context
```

**5.3 Explicitly NOT carried by `mapping_basis`（APPROVED）**

本 Decision **不要求、也不允许**把以下职责扩展到 `mapping_basis`：

```
不作为 source evidence carrier
不复制 mapping rule logic
不写 decision explanation ／ rationale
不要求「判定依据摘要」
不作为自由文本说明
不承载新的 provenance schema
不通过一个 JSON string 偷渡 mini-schema ／ nested semantics
不新增 canonical field ／ member ／ literal ／ carrier
```

**5.4 String encoding ／ syntax deferred（APPROVED）**

本 Decision **不定义** `mapping_basis` exact JSON string 的具体编码格式，例如：

```
rule-id@revision
path-like identity
URI-like identity
namespaced identifier
hash ／ digest
structured string convention
任何其他具体 syntax
```

上述具体 representation **留给后续 Architecture ／ Implementation**，但**必须**满足本 Decision 的 semantic requirements。

**5.5 Preservation ／ normalization boundary（保持）**

```
mapping_basis 是 exact JSON string
不得 silent normalize ／ trim ／ case-fold ／ Unicode-normalize ／ numeric coercion
locator 与 basis 不得被下游擅自改写
不新增 "_meta" member
不新增 literal ／ carrier
```

**5.6 Interaction with `Decision 4`（保持）**

`Decision 4` 已规定：mapping rule **必须**有 rule identity ／ revision identity；rule **必须**
explicit ／ deterministic ／ traceable ／ reproducible；representation carrier 留给 Architecture ／ Implementation。
`Decision 5` **只**进一步规定：canonical `mapping_basis` 应引用该 **approved rule identity ＋ revision identity**。
`Decision 5` **不重新决定** mapping rule 自身用 YAML ／ code ／ DB ／ registry ／ rule engine 等何种载体。

**5.7 边界（不受本 Decision 影响）**

- 既有 `evidence` carrier semantics、FCM ／ FIC ／ Snapshot & Import Contract、
  Master Data Mapping canonical semantic、`Decision 3` Failure ／ Quarantine Interface、
  `Decision 4` representation-carrier decision 均**未修改**；
- **未**新增 `"_meta"` member ／ field ／ literal ／ carrier、**未**新增 provenance schema；
- **`Decision 6` ～ `8` 保持未决**。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 5                  = RECORDED（Option ① minimal rule ／ revision reference）
mapping_basis string syntax       = ARCHITECTURE ／ IMPLEMENTATION CONCERN（semantic requirements 已登记）
Decision 6 ～ 8                    = 未决
POC Design v0.2                   = DRAFT
```

**Decision 6 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #84 Human Decision**。本记录**只**登记已批准的 Decision 6，并执行最小必要 synchronization ——
**不**选择 Decision 7 ～ 8、**不**推进 `Adapter Boundary` 状态、**不**创建任何 drift detection ／ registry ／ validator 组件、
**不**新增 Validation Reason ／ Validation Category ／ canonical status enum、**不**新增 canonical carrier ／ literal ／ schema。

```
Decision Scope     = §4.6.10 Decision 6（multi-Adapter governance ／ canonical semantic drift detection）
Decision Authority = Human（Issue #84）
Selected Option    = Option ② —— explicit cross-Adapter consistency obligation
Write Scope        = docs/design/poc-design-v0.2.md
```

**6.1 Canonical-first remains authoritative（APPROVED）**

既有 **`MS-1`** 继续保持：

```
canonical semantic 由 canonical design 定义
每个 Adapter 只做 source-specific mapping ／ realization
不同 source 可以拥有不同 source vocabulary ／ physical representation ／ mapping rule
不得因为 Adapter 不同而改变 canonical semantic
不得引入第二套 canonical identity ／ vocabulary
不得建立 Global Source-Field Precedence
```

**`MS-2 precedence-first` 继续为 `NOT COMPATIBLE`。**

**6.2 Explicit cross-Adapter consistency obligation（APPROVED）**

当两个或多个 Adapter 的职责范围涉及：

```
相同 canonical entity
相同 canonical field ／ semantic
相同 canonical relationship
相同或重叠 applicability scope
其他会共同影响同一 canonical interpretation 的 mapping
```

则这些 Adapter 的 approved mapping rules ／ revisions **必须**能够被检查为：

```
与 current approved canonical contract 一致
与各自声明的 source scope ／ logical dataset ／ canonical target 一致
不存在未解释的 semantic contradiction
不依赖隐式 Adapter priority
不依赖 first wins ／ latest wins
不依赖 source priority
不依赖 LLM ／ heuristic arbitration
不通过 silent normalization 消解冲突
```

该 obligation 的目标是**主动防止 canonical semantic drift**，**不是**建立 Adapter 优先级或 source precedence。

**6.3 Required consistency-check points（APPROVED）**

本 Decision **只**登记 conceptual obligation，**不**定义实现技术。至少在以下两个 conceptual points 上
**必须**满足 cross-Adapter consistency：

**Point A —— rule registration ／ revision change：** 当某 Adapter 新增 approved mapping rule ／ 修改 mapping rule ／
产生新的 rule revision ／ 扩展 source scope ／ canonical target applicability 时，在该变更**可被视为
approved ／ usable 之前**，**必须**确认它不会与 current canonical contract 或相关 Adapter 的已批准
assumptions ／ mappings 产生未解释冲突。

**Point B —— overlapping canonical use：** 当多个 Adapter 的 outputs ／ mappings 将被共同用于同一 canonical
context、同一 Analysis Run 或其他存在 overlapping canonical interpretation 的场景**之前**，**必须**不存在
unresolved cross-Adapter semantic conflict。

**本 Decision 不规定**该 consistency check 由何种 mechanism 实现：

```
CI
unit test ／ integration test
registry validation ／ config validation
runtime validator ／ service ／ workflow node
database ／ API
manual review tool
其他任何具体 mechanism
```

具体 mechanism 留给 **Architecture ／ Implementation**（`§10`）。

**6.4 Conflict behavior（APPROVED）**

若 cross-Adapter consistency check 发现 semantic contradiction ／ overlapping scope 下 mapping assumptions
不一致 ／ 两个 approved-looking rules 不能同时成立 ／ 同一 canonical target 出现无法唯一解释的 competing
interpretation ／ drift 无法由 existing approved canonical contract 唯一解决，则：

```
不得 first wins
不得 latest wins
不得 Adapter priority
不得 source priority
不得 Global Source-Field Precedence
不得 LLM ／ fuzzy ／ heuristic decide
不得 silent reconciliation
不得 Package Assembly 自行解释或修复 semantic conflict
```

**必须**按 existing unresolved ／ consistency boundary 处理。

**6.5 Alignment with `Decision 3`（APPROVED）**

当 drift ／ conflict 在 canonical artifact 生成**之前**被发现，且受影响的 mapping 无法
deterministic ／ uniquely resolve 时：

```
affected dataset artifact fail closed
不产出伪 canonical artifact
不为「让 Data Validation 有东西可报」而先生成错误 canonical artifact
source-side ／ mapping-side context 继续走已授权但尚未 operationally available 的
non-canonical Adapter Failure ／ Quarantine Interface
```

**只有在真实 canonical validation context 已存在、且 existing taxonomy 确实适用时**，才使用 existing
unresolved ／ consistency taxonomy。本 Decision **不新增**：

```
ADAPTER_DRIFT
CROSS_ADAPTER_CONFLICT
任何新的 Validation Reason ／ Validation Category ／ status enum
```

**6.6 Package Assembly boundary（保持）**

Package Assembly 继续保持 `Decision 2` ／ `Decision 3` 已批准边界：

```
只组装成功产出的 canonical artifacts
不负责 semantic arbitration
不决定哪个 Adapter 更可信
不建立 Adapter ／ source precedence
不补 mapping
不 reconcile conflicting canonical semantics
不生成 placeholder canonical artifact
不把 unresolved drift reinterpret 为正常 missing ／ null
```

Package completeness ／ acceptance 仍由既有 Snapshot ／ Import ／ FIC contract 决定。

**6.7 Governance scope vs implementation mechanism（APPROVED）**

本 Decision 登记的是 **cross-Adapter consistency obligation**、canonical-first governance、
unresolved drift fail-safe behavior 与 required conceptual check points。

本 Decision **不创建**：

```
Cross-Adapter Registry service
Drift Detection service
new Mapping Registry component
consistency database
event bus ／ API ／ queue ／ scheduler
CI framework ／ runtime validator
dashboard
workflow engine
任何其他实现组件
```

上述均留给 **Architecture ／ Implementation**。

**6.8 No new canonical semantics（APPROVED）**

Decision 6 **不得**：

```
新增 canonical identifier 形式
新增 canonical vocabulary
新增 canonical field ／ entity ／ relationship
新增 Adapter-specific canonical semantics
用 cross-Adapter governance 重新定义 §4.5 已 DESIGN RESOLVED 的 mapping contracts
```

若发现 canonical contract 本身无法解释真实 source 差异，应登记为**新的 design gap ／ Human Decision**，
而**不得**由 Adapter 层自行「统一」。

**6.9 边界（不受本 Decision 影响）**

- `§3` hard boundary、`§4.3` FCM ／ FIC ／ Snapshot & Import Contract、`§4.4` Data Validation、
  `§4.5` Master Data Mapping 已 `DESIGN RESOLVED` 的 contract **未重开**；
- `Decision 3` 的 fail-closed 策略与其 Failure ／ Quarantine Interface **授权**未被修改；
- `Decision 4` 的 rule contract requirements 与 representation-carrier deferral、`Decision 5` 的
  `mapping_basis` 语义粒度与 syntax deferral **未被修改**；
- **未**新增 Validation Reason ／ Validation Category ／ status enum；**未**新增 canonical carrier ／
  `"_meta"` member ／ literal ／ provenance field ／ schema；
- **`Decision 7` ～ `8` 保持未决**。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 6                  = RECORDED（Option ② explicit cross-Adapter consistency obligation）
drift detection mechanism         = ARCHITECTURE ／ IMPLEMENTATION CONCERN（obligation 已登记）
Decision 7 ～ 8                    = 未决
POC Design v0.2                   = DRAFT
```

**Decision 6 —— 多 Adapter 共享 canonical 约定的治理与 drift 检测形态**

> **current-state（Issue #84）：** 本条目为 **Decision source（时点记录）**；其结果已登记于上方
> **`Decision 6 —— Human Decision Record`**（`REGISTERED`）。**该 Decision 不再是 open item。**
- **Question：** 多 source ／ 多 Adapter 场景下，共享的 canonical 约定（identifier 形式、vocabulary、适用范围）如何登记与治理？canonical semantic drift 的**检测形态**是什么（**不**新增 carrier ／ reason）？
- **Options：** ① 只依赖既有 canonical contract ＋ unresolved 表达（最小）；② 增加 explicit cross-Adapter consistency obligation（仍在既有 taxonomy 内表达）；③ 其他有证据支持的形态。
- **Trade-offs：** ① 最小、与 `MS-1` 一致；② 更主动，但需定义检测时点与责任；③ 见论证。
- **Dependencies：** `AC-18` ／ `AC-19` ／ `§4.5.16` ／ `ADEP-5`。
- **What changes：** `A-9` 的登记内容；是否需要在 Adapter 层新增一致性义务。
- **注意：** **不得**重新引入 global source-field precedence；**不得**新增 Validation Reason。

**Decision 7 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #86 Human Decision**。本记录**只**登记已批准的 Decision 7，并执行最小必要 synchronization ——
**不**选择 Decision 8、**不**推进 `Adapter Boundary` 状态、**不**设计 `§7` 的 RBAC ／ Data Scope ／
Tool Permission ／ Secret Handling、**不**创建 credential ／ secret、**不**选择 authentication ／
authorization ／ secret-delivery 技术、**不**改变 `§7` 各 remaining item 的 `DESIGN PENDING` 状态。

```
Decision Scope     = §4.6.10 Decision 7（Adapter ↔ Permission & Security interface expectation）
Decision Authority = Human（Issue #86）
Selected Option    = Option ① —— declarative access-requirement interface
Write Scope        = docs/design/poc-design-v0.2.md
```

**7.1 Adapter responsibility —— declare minimum access requirements（APPROVED）**

对于 Adapter 在 **Controlled Export ／ Data Landing Zone 之后**执行已批准职责所需的访问，Adapter **必须**能够
声明至少以下 conceptual requirements：

```
resource boundary       —— 仅限其职责所需的 Data Landing Zone-side exported artifacts ／ resources
operation ／ capability —— 仅声明完成职责所需的最小 capability；不得扩展为 Production write
logical data scope      —— 所需 logical dataset ／ source scope ／ applicable exported-artifact scope
security dependency     —— 运行该 Adapter 需要一个满足上述要求的 authorized access context
secret dependency       —— when applicable：若未来实现机制确实需要 credential ／ secret，
                           Adapter 只声明「存在该 dependency ／ requirement」，不声明 secret value，
                           不选择其 provisioning ／ storage ／ retrieval 机制
```

该声明的语义是：**「Adapter 需要什么条件才能合法执行」**，
而**不是**「Adapter 有权自行授予或取得什么权限」。

**7.2 Permission & Security ownership remains outside Adapter（APPROVED）**

本 Decision **不把**以下职责赋予 Adapter：

```
RBAC policy
user ／ role definition
Data Scope policy ／ approval
Tool Permission policy ／ approval
authorization decision
authentication mechanism
identity ／ principal model
credential issuance ／ provisioning
credential storage
credential retrieval ／ delivery mechanism
secret rotation
secret lifecycle
secret manager selection
policy evaluation
permission escalation
emergency ／ break-glass policy
```

上述仍由 **`§7` Permission & Security 后续设计**负责；本 Decision **不**将其标记为 `DESIGN RESOLVED`。

**7.3 Authorized access unavailable ⇒ fail closed（APPROVED）**

如果 Adapter 已声明的 required authorized access context **未提供** ／ **不满足**所需 resource ／ scope ／
capability ／ **已失效** ／ 或**无法被可靠确认**，则 Adapter **不得**：

```
自行扩大 Data Scope
自行提升 Tool Permission
改用更高权限身份
猜测或选择替代 credential
使用未批准 credential
绕过 Permission & Security policy
绕过 Data Landing Zone
fallback 到 source-system direct access
fallback 到 Production DB ／ API
将缺少授权伪装成正常 data missing
```

必须：**对该受保护访问 fail closed ／ do not proceed。**
本 Decision 只登记这一 behavioral boundary，**不定义**最终 error code ／ audit event ／ retry ／
user-facing message ／ incident state。

**7.4 Failure classification boundary（APPROVED）**

「required authorized access unavailable」是 **Permission ／ Security dependency failure**，
**不得**被本层重新解释为：

```
canonical mapping unresolved
canonical missing ／ null
business DATA_INCOMPLETE
Data Validation reason
Adapter mapping conflict
package disposition
```

本 Decision **不新增** Validation Reason ／ Validation Category ／ canonical status enum ／
package disposition ／ security failure enum。其未来具体 reporting ／ audit ／ operational handling 留给
**`§7` Permission & Security**、**`§8` Audit & Observability** 与 **Architecture ／ Implementation**。
同时保持既有 `Decision 3` boundary：**只有** source ／ mapping-side unresolved ／ unsupported 才走其已授权的
non-canonical Failure ／ Quarantine Interface；**Decision 7 不把 Permission ／ Security failure 自动塞入该
interface，也不扩展其 schema ／ responsibility。**

**7.5 Secret boundary（APPROVED）**

Adapter **可以**声明 conceptual：「该 Data Landing Zone-side read dependency 需要 authorized
credential ／ secret context。」但本 Decision 明确**禁止**：

```
在 canonical design 中写真实 username ／ password ／ token ／ API key ／ secret value
在 mapping rule 中嵌入真实 credential ／ secret
在 mapping_basis ／ provenance ／ canonical record ／ "_meta" 中承载 credential ／ secret
把 secret 写入 prompt ／ log ／ Git
选择 Vault ／ Secrets Manager ／ Kubernetes Secret ／ env var ／ OAuth ／ service account ／ API key 等具体 mechanism
```

上述均留给 **`§7` ／ Architecture ／ Implementation**。

**7.6 Data Landing Zone-only boundary（保持）**

Decision 7 的 Adapter-side access requirement **严格限于 Data Landing Zone ／ Controlled Export 之后**，
**不包括**：

```
source-system credentials
ERP ／ SRM ／ Production DB credentials
export-side protocol credentials
Controlled Export 上游身份
Production API write credential
```

若未来要让 Adapter 直连 source system，**必须**另走 **Human-approved `§3` design change**；
Decision 7 **不**授权该扩展。

**7.7 Interface expectation ≠ injection mechanism（APPROVED）**

本 Decision **不选择**：

```
security layer injection
pull ／ push credential delivery
broker
sidecar
environment injection
secret mount
token exchange
identity federation
service account
policy agent
auth middleware
API gateway
任何 concrete security runtime mechanism
```

即：Decision 7 **只**关闭 Adapter Boundary 的「**需要声明什么** ／ **不得自行做什么**」的**接口期待**，
**不**关闭 `§7` 的实现与 policy design。

**7.8 Effective permission invariant preserved（保持）**

```
AI Effective Permission
= User Permission
∩ Data Scope
∩ Tool Permission
∩ Workflow State
∩ POC Policy
```

Decision 7 **不**改写该公式，**也不**定义各 factor 的计算方式。Adapter 的 declared requirement
**不能**扩大 effective permission；最终 authorized capability 仍**必须**受 Permission & Security policy 约束。

**7.9 No status inflation（保持）**

```
Adapter ↔ Permission & Security interface expectation = REGISTERED（本 Decision）
RBAC                = DESIGN PENDING ← 不因本 Decision 改变
Data Scope          = DESIGN PENDING ← 不因本 Decision 改变
Tool Permission     = DESIGN PENDING ← 不因本 Decision 改变
Secret Handling     = DESIGN PENDING ← 不因本 Decision 改变
§7 Permission & Security overall = 不得因本 Decision 宣称 DESIGN RESOLVED
Adapter Boundary    = DESIGN PENDING ← 直到 Decision 8 closure gate
```

**7.10 边界（不受本 Decision 影响）**

- `§3` hard boundary、`§4.3` FCM ／ FIC ／ Snapshot & Import Contract、`§4.4` Data Validation、
  `§4.5` Master Data Mapping 已 `DESIGN RESOLVED` 的 contract **未重开**；
- `Decision 3` Failure ／ Quarantine Interface 的 **schema ／ responsibility 未修改**；
  Permission ／ Security failure **不**被塞入该 interface；
- `Decision 1` ～ `Decision 6` 已批准内容**未被修改**；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ field；**未**新增 Validation Reason ／
  Validation Category ／ status enum ／ package disposition；
- **未**创建 credential ／ secret；**未**改写 `§7` 状态；
- **`Decision 8` 保持未决**。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 7                  = RECORDED（Option ① declarative access-requirement interface）
§7 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling = DESIGN PENDING（未改变）
security runtime mechanism        = ARCHITECTURE ／ IMPLEMENTATION CONCERN
Decision 8                        = 未决
POC Design v0.2                   = DRAFT
```

**Decision 7 —— Adapter 与 `Permission & Security` 的接口期待**

> **current-state（Issue #86）：** 本条目为 **Decision source（时点记录）**；其结果已登记于上方
> **`Decision 7 —— Human Decision Record`**（`REGISTERED`）。**该 Decision 不再是 open item。**
- **Question：** Adapter 需要 data scope ／ credentials 时，接口形态是 ① Adapter **声明**所需 scope ／ secret 需求（由 `§7` 后续设计提供），还是 ② 由 security 层**注入**并限制？本层登记到什么程度？
- **Options：** ① 声明式接口期待（本层登记「需要什么」，不设计机制）；② 注入式（本层登记「由谁提供」）；③ 其他。
- **Trade-offs：** ① 与 `§7` `DESIGN PENDING` 状态最兼容、不越界；② 更明确但可能预先约束 `§7` 设计；③ 见论证。
- **Dependencies：** `AC-21` ／ `ADEP-7`；`§7` 为 `DESIGN PENDING`。
- **What changes：** `A-10` ／ `A-11` 的登记内容。
- **注意：** **不得**设计 RBAC ／ Secret Handling；**不得**创建 credentials 或 secrets。

**Decision 8 —— Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #88 Human Decision**。本记录**只**登记已批准的 Decision 8（closure policy），并执行最小必要
current-state synchronization —— **不**在本 registration PR 推进 `Adapter Boundary` 状态、**不**执行 closure、
**不**伪造 `A-1` ～ `A-14` 的 PASS 结果、**不**授权 blanket runtime implementation、
**不**关闭 `§7` ／ Failure ／ Quarantine ／ Architecture deferrals。

```
Decision Scope     = §4.6.10 Decision 8（minimum closure criteria acceptance ／ dedicated closure gate authorization）
Decision Authority = Human（Issue #88）
Selected Option    = Accept A-1 ～ A-14 ＋ authorize dedicated Adapter Boundary Closure Design Change ＋
                     conditional status advancement；no blanket runtime implementation authorization
Write Scope        = docs/design/poc-design-v0.2.md
```

**8.1 Mandatory closure criteria（APPROVED）**

正式接受：

```
A-1 ～ A-14 = MANDATORY MINIMUM CLOSURE CRITERIA
```

Dedicated Closure PR **必须**逐项验证：

```
A-1  ownership ／ does-not-own boundary
A-2  input conceptual contract
A-3  output conceptual contract ／ Package Assembly boundary
A-4  determinism ／ rule-level contract
A-5  fail-safe
A-6  unresolved Adapter-side contract ／ handoff
A-7  unsupported source behavior ／ reporting boundary
A-8  evidence locator ／ mapping_basis carrier ＋ producer ＋ semantic boundary
A-9  multi-source ／ multi-Adapter semantic stability
A-10 cross-layer boundary
A-11 Adapter ↔ Permission & Security interface expectation
A-12 failure reporting boundary
A-13 selected-decision composition check
A-14 real source field unknown is not a design-closure blocker
```

**8.2 Design objectives remain non-blocking（APPROVED）**

`A-15 Human Inspectability` 与 `A-16 Implementation Simplicity`：

```
必须在 Closure PR 中显式评估
必须给出简洁结论 ／ evidence
仍属 POC DESIGN OBJECTIVE
不得因主观评价升级为 hard closure gate
不得阻止 closure —— 除非评估暴露出已触发 A-1 ～ A-14 中某项 mandatory criterion 的客观失败
```

**8.3 Dedicated Closure PR required（APPROVED）**

Decision 8 **不直接关闭** `Adapter Boundary`。必须先执行一个独立的
**Adapter Boundary Closure Design Change PR**，其职责**仅**是：

```
1 以 current canonical design 为准，对 A-1 ～ A-14 逐项做 PASS ／ FAIL verification
2 对 A-15 ／ A-16 做非阻塞评估
3 执行 A-13 selected-decision composition check，确认 Decision 1 ～ 7 的组合与
  §3 hard boundary ／ §4.3 Snapshot ／ Import Contract ／ FCM ／ FIC ／
  §4.4 Data Validation ／ §4.5 Master Data Mapping 之间不存在未登记冲突
4 仅在全部 mandatory criteria PASS 时进行状态转换与必要 canonical synchronization
5 若任一 mandatory criterion FAIL ⇒ Adapter Boundary 保持 DESIGN PENDING；
  不得用 Exception ／ waiver ／ reviewer opinion 强行关闭；
  失败项必须作为新的明确 design gap ／ follow-up task 处理
```

**8.4 Conditional status advancement（APPROVED）**

只有 Dedicated Closure PR 验证：

```
A-1 ... A-14 = PASS
```

才允许：

```
Adapter Boundary
DESIGN PENDING
→ DESIGN RESOLVED
```

该状态转换表示：Adapter 的 **conceptual responsibility ／ behavioral ／ cross-layer boundary** 已达到当前
POC design closure 标准。它**不表示**：

```
IMPLEMENTED
TESTED
production-ready
real ERP ／ source field known
runtime Adapter exists
mapping registry exists
mapping_basis concrete string syntax 已选
cross-Adapter drift detection mechanism 已实现
Permission & Security overall 已完成
Failure ／ Quarantine Interface runtime 已实现
Architecture ／ ADR 已完成
POC Design overall APPROVED ／ FROZEN
```

**8.5 Failure ／ Quarantine Interface remains separate（保持）**

`Decision 3` 已关闭的是：unresolved ／ unsupported strategy、fail-closed responsibility、
non-canonical Failure ／ Quarantine Interface 的 **separate-design authorization**。
该 interface 的 physical shape ／ schema ／ storage ／ API ／ runtime realization
**仍未设计 ／ 未 operationally available**。上述**不自动阻止** Adapter Boundary **conceptual closure**
（只要 `A-1` ～ `A-14` 对 Adapter-side responsibility ／ handoff boundary 已满足）。
Decision 8 **不授权**其 physical design ／ implementation。

**8.6 `§7` remains independently `DESIGN PENDING`（保持）**

```
RBAC              = DESIGN PENDING ← 不因 Decision 8 改变
Data Scope        = DESIGN PENDING ← 不因 Decision 8 改变
Tool Permission   = DESIGN PENDING ← 不因 Decision 8 改变
Secret Handling   = DESIGN PENDING ← 不因 Decision 8 改变
§7 Permission & Security overall = 不得标记为 DESIGN RESOLVED
```

这些 remaining `§7` items **不自动阻止** Adapter Boundary conceptual closure，
因为 Adapter 本层的 security interface expectation 已由 `Decision 7` 登记。

**8.7 Real source field unknown remains non-blocking（保持）**

保持 `A-14`：real ERP table ／ column ／ proprietary field unknown、source-specific physical field name
unknown、runtime credential unknown **不等于** Adapter Boundary design 未完成。Closure **只能**基于
**conceptual ／ canonical contract completeness**，**不得**把 implementation-time source discovery
强行变成 design closure prerequisite。

**8.8 No blanket implementation authorization（APPROVED）**

本 Decision **不授权任意 runtime implementation PR**。特别**不**因 Decision 8 自动授权：

```
Adapter runtime code
connector ／ parser ／ serializer
mapping registry ／ mapping rule storage
Failure ／ Quarantine implementation
drift detector ／ runtime validator
auth middleware ／ credential ／ secret mechanism
database ／ API ／ framework ／ deployment
source-system integration
```

后续 implementation **必须**：① 先完成 Adapter Boundary closure；② 按当时 current
Architecture ／ `§7` ／ `§8` ／ `§9` ／ implementation governance；
③ 在独立、明确授权的 task ／ PR 中进行。

**8.9 Architecture deferrals preserved（保持）**

Decision 8 **不**关闭以下 Architecture ／ Implementation deferrals：

```
mapping rule representation carrier
mapping_basis concrete string syntax ／ encoding
cross-Adapter consistency detection mechanism
Package Assembly runtime shape
Failure ／ Quarantine physical realization
auth ／ credential ／ secret-delivery mechanism
framework ／ database ／ API ／ deployment
ADR
```

`No ADR created yet` 状态**不因 Decision 8 改变**。

**8.10 Registration-time status（保持）**

```
Decision 1 ～ 8                = REGISTERED
Adapter Boundary               = DESIGN PENDING ← 本 registration PR 不推进
POC Design v0.2                = DRAFT
Next gate                      = Dedicated Adapter Boundary Closure Design Change PR
DESIGN RESOLVED                = 只能由该 Closure PR 在全部 mandatory gate PASS 后登记
```

**8.11 边界（不受本 Decision 影响）**

- `§3` hard boundary、`§4.3` FCM ／ FIC ／ Snapshot & Import Contract、`§4.4` Data Validation、
  `§4.5` Master Data Mapping 已 `DESIGN RESOLVED` 的 contract **未重开**；
- `Decision 1` ～ `Decision 7` 已批准内容**未被修改**；
- **未**伪造任何 `A-1` ～ `A-14` 的 PASS 结果；**未**执行 closure；**未**推进状态；
- **未**把 `A-15` ／ `A-16` 升级为 hard blocker；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ field、Validation Reason ／ Category ／
  status enum ／ package disposition；
- **未**创建 runtime code ／ registry ／ detector ／ validator ／ ADR；**未**选择 architecture ／ framework ／
  database ／ API ／ deployment；
- **未**创建 credential ／ secret；**未**修改 `§7` 状态。

**执行状态（本 Registration 时点）**

```
Adapter Boundary                  = DESIGN PENDING ← 本 Decision 不推进状态
Human Decision 8                  = RECORDED（Accept A-1 ～ A-14 ＋ dedicated Closure PR ＋ conditional advancement）
Closure criteria                  = A-1 ～ A-14 MANDATORY（Human-approved）；A-15 ／ A-16 non-blocking
Closure verification              = PENDING（Dedicated Adapter Boundary Closure Design Change PR）
§7 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling = DESIGN PENDING（未改变）
blanket implementation authorization = NOT GRANTED
Decision 1 ～ 8                    = REGISTERED
POC Design v0.2                   = DRAFT
```

**Decision 8 —— Minimum closure criteria 接受与 follow-up 授权**

> **current-state（Issue #88）：** 本条目为 **Decision source（时点记录）**；其结果已登记于上方
> **`Decision 8 —— Human Decision Record`**（`REGISTERED`）。**该 Decision 不再是 open item。**
- **Question：** 是否接受 **`A-1` ～ `A-14`** 作为 Adapter Boundary minimum closure criteria（`A-15` ／ `A-16` 为 design objectives）？是否授权后续独立 Adapter Boundary Design Change ／ Implementation PR，并在满足 closure criteria 时允许 `DESIGN PENDING → DESIGN RESOLVED`？
- **Options：** 接受 ／ 调整 ／ 拒绝；授权 ／ 不授权。
- **Trade-offs：** 授权推进 closure；不授权保持 `DESIGN PENDING`。
- **Dependencies：** Decision 1 ～ 7。
- **What changes：** 本层是否可进入 closure。

**本 Review 不作出上述任何决定。** 后续必须由 **Human Decision** 裁定；
**不得**由 Agent 自行选择 final adapter model ／ mapping 表达方式 ／ unresolved 策略。

> **current-state（Issue #72 ／ #74 ／ #76 ／ #78 ／ #82 ／ #84 ／ #86 ／ #88）：** **`Decision 1`（#72）／ `Decision 2`（#74）／ `Decision 3`（#76）／ `Decision 4`（#78）／ `Decision 5`（#82）／ `Decision 6`（#84）／ `Decision 7`（#86）／ `Decision 8`（#88）已登记** ——
> 见上方各自的 **Human Decision Record**（`Registration Status：REGISTERED`）与
> **`§4.6.13`** ／ **`§4.6.14`** ／ **`§4.6.15`** ／ **`§4.6.16`** ／ **`§4.6.17`** ／ **`§4.6.18`** ／ **`§4.6.19`** ／ **`§4.6.20`** 的 Registration Synchronization。
> **本层已无剩余 undecided Human Decision**；**`Decision 8` 已登记 closure policy**，但 `Adapter Boundary` **未**因此关闭；**producer ownership**（artifact ／ package ／ manifest ／
> provenance metadata 的 producer）**已由 `Decision 2` 决定**（Option ②）；
> **unresolved ／ unsupported 策略**已由 `Decision 3` 决定（条件组合，以 `UF-2` ／ fail-closed 为主），
> 并**授权单独设计** non-canonical **Adapter Failure ／ Quarantine Interface**（形态 ／ schema ／ runtime 未完成，**尚未** operationally available）；
> **mapping rule representation** 已由 `Decision 4` 决定（**Option ①：只登记 contract requirements，carrier deferred** 给 Architecture ／ Implementation）；
> **`mapping_basis` 语义粒度**已由 `Decision 5` 决定（**Option ①：minimal rule ／ revision reference**；string syntax ／ encoding 属 Architecture ／ Implementation）；
> **multi-Adapter governance 与 canonical semantic drift 边界**已由 `Decision 6` 决定（**Option ②：explicit cross-Adapter consistency obligation**；canonical-first 保持；detection mechanism 属 Architecture ／ Implementation）；
> **Adapter ↔ `Permission & Security` interface expectation** 已由 `Decision 7` 决定（**Option ①：declarative access-requirement interface**；Adapter 只声明 minimum authorized access requirements；authorized access 不可用 ⇒ fail closed；`§7` RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 仍 `DESIGN PENDING`）；
> **minimum closure criteria 与 closure gate** 已由 `Decision 8` 决定（**Accept `A-1` ～ `A-14` 为 mandatory minimum closure criteria ＋ 授权 Dedicated Closure Design Change PR ＋ 条件性状态转换；no blanket runtime implementation authorization**）。
> **`Decision 8` registration 时点** `Adapter Boundary` **仍为 `DESIGN PENDING`**（**该 registration PR 未推进状态**）；其后由 **Dedicated Closure Validation（Issue #90）= `PASS`** 登记为 **`DESIGN RESOLVED`**（见 **`§4.6.21`**）。`POC Design v0.2` 仍 `DRAFT`。
> **下一步 gate：** Adapter Boundary **implementation ／ Architecture ／ `§7` ／ `§8` 等后续独立授权** —— 均**未**由本 closure 授权（见 **`§4.6.21`** E 节 ／ `Decision 8` 8.8）。

---

#### 4.6.11 Explicit Non-Decisions

本 Review **不创建**：

```
Adapter ／ connector ／ extractor runtime code
parser ／ serializer ／ runtime validator
JSON Schema ／ sample package ／ mock dataset
framework ／ database ／ API technology ／ deployment stack
RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 设计
credentials ／ secrets ／ real source connection
real ERP table ／ column ／ proprietary field 选择
canonical entity ／ field ／ enum ／ status
new Validation Reason ／ new Validation Category
新的 Package disposition ／ status enum
新的 carrier ／ sidecar ／ `"_meta"` literal
Production write ／ write-back ／ Production API call
ADR ／ Architecture Decision
```

**未**修改 `AGENTS.md` ／ `CONTRIBUTING.md` ／ Discovery `FROZEN` docs；
**未**修改 `docs/project-index.md`；
**未**重新打开 `Snapshot / Import Contract` ／ `Data Validation` ／ `Master Data Mapping`
任何已登记 policy 或历史记录。

---

#### 4.6.12 Review Revision Log（Coordinator Review 修正 —— review-only）

> 本节记录 **PR #71 Coordinator Review `AB-01` ～ `AB-07`** 的修正，
> 用于说明本 Review 的 inherited-authority 依据、边界收窄与 carrier 可行性判定。
> **仍不选择任何方案**、**不**登记 policy、**不**改变任何 status、**不**创建 runtime artifact。

| 修正项 | 主题 | 本次变更 |
| --- | --- | --- |
| `AB-01` | 不得把 PR #65 `RIF-11` Review Finding 当作 inherited authority | `AC-22` 重写为**仅列可由 current approved policy 直接推出的** ownership，并**逐条**标注来源（`§3.1` ／ `§3.3` ／ `§3.4` ／ `§4.3.25` ／ `§4.3.28` ／ `§4.3.29` ／ `§4.4` ／ `§4.5.2`）；新增 **`AC-23`** 明确「完整 ownership 列表尚未获批」，`RIF-11` **不构成**已批准 policy；**超出**该范围的 ownership（`connector` ／ `source protocol` ／ `Package identity` ／ `manifest` / unresolved carrier ／ security 接口）**全部降级**为本层 finding ／ option 并绑定 Decision；`ARF-1` ／ `ARF-2` ／ `PE-1` 依据同步更正 |
| `AB-02` | Adapter 必须严格保持在 `§3` Controlled Export 之后 | 「Adapter owns `source-specific connector` ／ `protocol`」改为 **exported-artifact format ／ protocol handling**；ownership 表新增一行明确 **`source-system connectivity` 属 POC Adapter boundary 之外**；`AS-27` 收窄为读取 **Data Landing Zone 中的 exported artifacts** 的 credentials ／ secrets；`AS-28` 收窄为 **Data Landing Zone 侧** scope；`AS-30` 的 `source unreachable` 移出（改述为 exported artifact unreadable ／ malformed）；`ADEP-7` ／ `ADEP-9` ／ `4.6.5 G` ／ `ARF-7` ／ `ARF-8` 同步；并明确若要把 source-system connectivity 纳入 Adapter，**必须另走 Human-approved `§3` design change** |
| `AB-03` | `UF-1` 未证明可由已批准 carrier 表达 | `UF-1` 改为 **条件性**：可用部分为「mapping 已批准但 value 缺失 ⇒ `null`（`C-2`）」，**不可**用部分为「存在 source evidence 但无 approved mapping」的 root condition —— 因 `"_meta"` known-member set 固定（新 member ⇒ reject）且 canonical field 写 `null` 会与 explicit missing **压平**（违反 `AC-9` ／ `AC-10`）；因此若要求在 package 内承载 unresolved 事实 ⇒ **依赖单独 Human-authorized carrier ／ interface design change**；`UF-2` 同样标注该依赖；`quarantine` 需新 artifact ／ state 时同处理；新增 **`ADEP-12`**；`A-6` 增加承载方式要求；`Decision 3` 增加承载方式选项；`4.6.6` 相容性列同步 |
| `AB-04` | manifest ／ package generation ownership 自相矛盾 | ownership 表的 `Package identity ／ manifest generation` 从 **inherited does-not-own** 移出，改列为本层 **open**（`AC-23`）；新增 **`ADEP-11`**；`Decision 2` 扩展为「谁生成 manifest ／ package identity」并注明**各 option 均不得**被判为与 inherited does-not-own 冲突；`4.6.5 B` ／ `4.6.6` ／ `A-3` 同步 |
| `AB-05` | `AC-22` 仍把**未获批准**的 Adapter ownership 写成「已批准部分」 | **`AC-22` 再次收窄为 current approved policy 明确规定者**：① `§3` read boundary；② **source-specific semantic mapping responsibility ＋ mapping constraints**（按 `§4.5.2` ／ `§4.5.11` ／ `§4.5.21` **各自实际范围**）；③ evidence locator ／ basis 取值与保留；④ 各层明确 does-not-own 与 `FCM` ／ `Data Validation` ／ `FIC` 职责。**`source extraction` 责任**、**generic source-field identification ownership**、**`exported-artifact format ／ protocol handling` ownership** **移出** inherited，改为本层 **open finding ／ Human Decision**（`4.6.5 A` 开放表 ／ **`ADEP-13`** ／ **Decision 1**）；`AC-23` 补充「**仅凭可由批准文本推导**不得写成 inherited」；`ARF-1` ／ `A-1` 同步；**新增 `P-1` ／ `P-2` 拆分**：`AO-1` **只**表达 **FIC-valid output invariant**（`P-1`，inherited），**producer ownership**（`P-2`：Adapter 直接产出完整 artifact set vs intermediate＋assembly）明确留在 **Decision 2**；`4.6.5 B` ／ `4.6.6` ／ `ARF-2` 同步 |
| `AB-06` | 旧场景 ／ dependency 仍把 open producer ownership 写回 Adapter 的 inherited responsibility | **统一改为 producer-neutral invariant**：`AS-3`（改述为「若某 producer 提交 mapped result，则必须与 logical dataset 一致」，producer ⇒ `P-2` ／ Decision 2）、`AS-15`（任何提交给 FIC 的 package **必须** FIC-valid；**若 Adapter 是被选中的 producer 则同样受约束**）、`AS-18`（carrier obligation inherited；**谁写入 metadata ⇒ open**）、`PE-1` ／ `ARF-5`（改为「**任何**写入者必须依已固定 carrier 写入并保持原始值」）、`ADEP-1`（producer-neutral：任何提交给 FIC 的 package 内容必须满足 contract；若 Adapter 为 producer 则同受约束）、`ADEP-4`（carrier obligation inherited；metadata producer ⇒ open）、`A-8`（producer-neutral carrier obligation；producer 归属留给 Decision 1 ／ 2）。**保留** Human-approved 的 **source-specific semantic mapping responsibility**（`AC-22` ②）；**「谁把 mapped result ／ provenance metadata 写成最终 canonical artifact ／ package」继续留给 Decision 2**。**未**新增 Decision、**未**改 option、**未**推进状态 |
| `AB-07` | producer-neutral cleanup 残余（**consistency-only**） | ① **`AS-16`** 由「Artifact 的 digest 与 **Adapter 产出时**的字节不一致」改为「与 **producer 提交 ／ acceptance 所验证的 exact raw bytes** 不一致」，invariant 仍为 `IG-raw` ⇒ **fail closed**；② **`AS-19`** 由「**Adapter 未产出**某 required logical evidence role」改为「**提交给 downstream ／ `Final Import Contract` 的 candidate package** 缺少 capability 所需的 logical evidence role」，Layer 2 **`EVIDENCE_AVAILABILITY`** 语义保持，**producer ownership 仍 open**（`P-2` ／ Decision 2）；③ PR body 的 inherited 结论同步为 producer-neutral carrier obligation。**未**改 Decision ／ option ／ closure criteria 集合、**未**新增 canonical policy、**未**推进状态 |

---

#### 4.6.13 Decision 1 Registration Synchronization（Issue #72 —— current-state）

> 本节记录 **Issue #72 登记 `Decision 1`** 后所执行的**最小必要一致性同步**。
> 本节**只**登记已批准的 `Decision 1(a)` ／ `1(b)`，并使其与 current-state canonical wording 一致 ——
> **未**选择 `Decision 2` ～ `8`、**未**推进 `Adapter Boundary` 状态、**未**新增 carrier ／ literal ／ reason ／ enum。

**A. Human Decision registered**

`Decision 1`（`(a)` 通用职责归属 ／ `(b)` mapping 责任交接点）已以
**Human Decision Record** 形式登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 1(a) = Option ①  ADAPTER_BOUNDARY（Controlled Export ／ Data Landing Zone 之后）
Decision 1(b) = Option ②  Adapter MAY define source-specific resolution rules（受约束）
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-22` | 增列 **Adapter Boundary 通用职责（`Decision 1(a)`）** 为已批准事项，并注明**不含** source-system connectivity ／ 上游链路 ／ export-side protocol ／ credentials |
| 2 | `§4.6.2` `AC-23` | 改为「ownership 只在**已批准部分**成立」：`Decision 1(a)` 的四项职责现为 **registered**；`Package identity` ／ `manifest` / producer ownership ／ unresolved carrier ／ security 接口**仍 open** |
| 3 | `§4.6.5 A` | inherited 表新增 **`Decision 1(a)`** 行与 **`Decision 1(b)`** 行；开放表由 7 项收敛为 **3 项**（producer ownership ／ unresolved carrier ／ security 接口），并注明 `Decision 1` 已关闭的 4 项 |
| 4 | `§4.6.7` `ADEP-2` | 责任交接点改为**已登记**（`Decision 1(b)`），保留「不改 canonical mapping contract ／ 不建 global precedence」约束 |
| 5 | `§4.6.7` `ADEP-13` | 保留 **AB-05 时点**历史结论，新增 **current-state**：ownership 已由 `Decision 1(a)` 指派给 Adapter（`REGISTERED`）；**producer ownership 仍 open**（`Decision 2`） |
| 6 | `§4.6.8` `ARF-1` | inherited 项新增 `Decision 1(a)`；开放项收敛为 producer ownership ／ unresolved carrier ／ security 接口 |
| 7 | `§4.6.9` `A-1` | 明确 `Decision 1(a)` 已登记的 `owns` 项与仍 open 项 |
| 8 | `§4.6.9` `A-4` | 增列 `Decision 1(b)` 的约束（允许 internal source-specific resolution rules，但须服从 determinism 与 canonical contracts） |
| 9 | `§4.6.10` `Decision 1` | 保留原 Question ／ Options 作为 Decision source，其后新增 **Human Decision Record**；`Decision 2` ～ `8` **保持未决** |
| 10 | `§4.6.4` `AS-18` ／ `§4.6.5 E` `PE-1` ／ `§4.6.8` `ARF-5` ／ `§4.6.7` `ADEP-4` ／ `§4.6.9` `A-8` ／ `§4.6.6` | **producer ownership 引用统一收敛为 `Decision 2` only**（`P-2` ／ `ADEP-11`）；**保留** producer-neutral carrier obligation 表述。理由：`Decision 1` 关闭的是 extraction ／ format-protocol ／ generic field identification ／ source-specific mapping handoff，**未**决定最终 canonical artifact ／ package ／ provenance metadata writer —— 见下方 **E** |

**C. 明确保留（未被本 Decision 决定）**

```
Decision 2 ～ 8                     = 未决
producer ownership（artifact ／ package ／ manifest ／ provenance metadata producer） = OPEN（Decision 2 only）
Adapter Boundary                   = DESIGN PENDING ← 未推进
POC Design v0.2                    = DRAFT
```

**D. Scope / Non-Decision 核验**

- **未**新增 carrier ／ literal ／ Validation Reason ／ Validation Category ／ status enum；
- **未**修改 `§3` hard boundary 与 `§4.1` ～ `§4.5` 已批准 policy；
- **未**设计 RBAC ／ Secret Handling ／ Architecture ／ framework ／ database ／ API ／ deployment；
- **未**选择真实 ERP table ／ column ／ proprietary field；
- **未**创建 Adapter ／ connector ／ parser ／ serializer ／ runtime code；
- **未**修改 Discovery `FROZEN` docs 或 governance docs；
- `Decision 1(a)` **不**扩大 `§3` source access（source-system connectivity 仍在 POC boundary 之外）。

**E. Current-state Consolidation（`AD1-REG-01`）**

> **历史保留：** `§4.6.12` 的 **`AB-06`** Review Revision Log 中「Decision 1 ／ 2」的**时点表述**
> **保留不改**（属历史 Review 记录）。

`Decision 1` 已关闭的职责为 extraction ／ `exported-artifact format ／ protocol handling` ／
`generic source-field identification` ／ source-specific mapping handoff；
它**未**决定「**谁**把 mapped result ／ provenance metadata 写成最终 canonical artifact ／ package」。

因此 current-state 中所有 producer ownership 引用**统一收敛为 `Decision 2` only**：

```
producer ownership（artifact ／ package ／ manifest ／ provenance metadata writer）
  ⇒ Decision 2 only（P-2 ／ ADEP-11）
producer-neutral carrier obligation（carrier shape ／ literals ／ 原始值保持）
  ⇒ inherited（任何写入者均受约束）
```

**已同步位置：** `AS-18` ／ `PE-1`（`4.6.5 E` 与 `4.6.6` 两处）／ `ARF-5` ／ `ADEP-4` ／ `A-8`。
**未同步（历史）：** `§4.6.12` `AB-06` 行
（另 `4.6.6` 的 `Adapter-side mapping 表达（Decision 1）` 行为**通用 ownership** 选项比较，**不涉** producer ownership，故保留）。

**本次修正的 review-only 边界（自我核验）：**

```
未选择任何 Human option（adapter model ／ mapping 表达 ／ unresolved 策略 ／ manifest 归属）
未登记任何 policy；未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未新增 Validation Reason ／ Category ／ status enum ／ carrier ／ literal
未修改 §3 ／ §4.1 ～ §4.5 任何已登记 policy 与历史记录
未创建 runtime code ／ schema ／ sample package
```

---

#### 4.6.14 Decision 2 Registration Synchronization（Issue #74 —— current-state）

> 本节记录 **Issue #74 登记 `Decision 2`** 后所执行的**最小必要一致性同步**。
> 本节**只**登记已批准的 `Decision 2`（Option ②），并使其与 current-state canonical wording 一致 ——
> **未**选择 `Decision 3` ～ `8`、**未**推进 `Adapter Boundary` 状态、**未**新增 carrier ／ literal ／
> reason ／ enum、**未**选择任何实现技术。

**A. Human Decision registered**

`Decision 2`（Adapter output organization ／ producer ownership）已以 **Human Decision Record** 形式
登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 2 = Option ②  Multi-Adapter artifacts ＋ independent Package Assembly
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-22` ／ `AC-23` | 保持既有已批准事项；`Package identity` ／ `manifest` ／ **producer ownership** 由 `Decision 2` 登记（原 `AC-23` 开放项之一） |
| 2 | `§4.6.4` `AS-15` | 增列 current-state：Adapter 产出其 canonical dataset artifact；只有经 **Package Assembly** 形成的**完整 package** 才可提交 `Final Import Contract`；partial artifacts 不得单独视为可接受 package |
| 3 | `§4.6.4` `AS-18` | 增列 current-state：**每个 Adapter 负责写入其自身掌握的 source-derived record-level provenance ／ locator ／ `mapping_basis`**，且只能使用已批准 carrier ／ literals |
| 4 | `§4.6.4` `AS-19` | `producer ownership` 由 open 改为 **registered**（`Decision 2`） |
| 5 | `§4.6.5 A` | inherited 表新增 3 行：**Adapter artifact production**、**Package Assembly package production**、**FIC 只验证 ／ 不生产**；开放表第 1 项（producer ownership）改为已登记 |
| 6 | `§4.6.5 B` ／ `§4.6.5 E` | **`P-2`** 由 `本层 open` 改为 **`Registered`（`Decision 2`）**；`PE-1` 开放项之一改为已登记（仅剩 `mapping_basis` 粒度 → `Decision 5`） |
| 7 | `§4.6.6` | `AO-1` 备注改为「producer ownership 已由 `Decision 2` 登记」；`PE-1` 备注改为「metadata producer 已由 `Decision 2` 登记」 |
| 8 | `§4.6.7` `ADEP-1` | 增列 current-state：只有**完整 package** 可提交 FIC；partial artifacts 不得单独提交（**禁止 dataset-level partial acceptance**） |
| 9 | `§4.6.7` `ADEP-4` | metadata producer 由 open 改为 **已登记**（每个 Adapter 写入其自身掌握的 source-derived provenance） |
| 10 | `§4.6.7` `ADEP-11` | 保留 **Decision 1 时点**历史结论，新增 **current-state**：`Decision 2`（Option ②）已登记 Adapter ／ Package Assembly ／ FIC 的职责划分 |
| 11 | `§4.6.7` `ADEP-13` | 「producer ownership 仍 open」改为**已登记**（`Decision 2`） |
| 12 | `§4.6.8` `ARF-1` | 新增「已由 `Decision 2` 关闭的开放项」；未决项收敛为 unresolved carrier ／ security 接口 |
| 13 | `§4.6.8` `ARF-2` ／ `ARF-5` | `P-2` 改为已登记；`ARF-5` 仅保留 `mapping_basis` 粒度未决 |
| 14 | `§4.6.9` `A-1` ／ `A-3` ／ `A-8` | `A-1` 的 open 项收敛；`A-3` 登记 Adapter ／ Package Assembly ／ FIC 的产出口径；`A-8` metadata producer 改为已登记 |

**C. 明确保留（未被本 Decision 决定）**

```
Decision 3 ～ 8                     = 未决
unresolved marker carrier（Decision 3） = OPEN
mapping_basis 语义粒度（Decision 5）  = OPEN
multi-Adapter governance（Decision 6） = OPEN
Adapter ／ Permission & Security 接口（Decision 7） = OPEN
package closure（Decision 8）         = OPEN
Adapter Boundary                   = DESIGN PENDING ← 未推进
POC Design v0.2                    = DRAFT
```

**D. Scope / Non-Decision 核验**

- **未**选择或登记 `Decision 3` ～ `8`；
- **未**设计 unresolved carrier ／ quarantine ／ failure reporting shape、mapping rule implementation carrier、
  `mapping_basis` 语义粒度、multi-Adapter governance ／ drift detection、Permission & Security interface
  或 Adapter Boundary closure；
- **未**修改 `§3` hard boundary 与 `§4.1` ～ `§4.5` 已批准 policy；**未**重开 FCM ／ FIC ／ Snapshot & Import Contract；
- **未**新增 carrier ／ literal ／ Validation Reason ／ Validation Category ／ status enum；
- **未**创建 Adapter ／ Package Assembly ／ parser ／ serializer ／ runtime code；
- **未**选择真实 ERP table ／ column ／ proprietary field；**未**选择 architecture ／ technology ／ deployment；
- **未**修改 Discovery `FROZEN` docs 或 governance docs；
- **Package Assembly 保持 conceptual responsibility**，其运行形态（service ／ module ／ job ／ library ／
  workflow node）与 technology **均未被选择**。

**本次修正的 review-only 边界（自我核验）：**

```
未选择任何 Decision 3 ～ 8
未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未新增 carrier ／ literal ／ Validation Reason ／ Category ／ status enum
未修改 §3 ／ §4.1 ～ §4.5 任何已登记 policy 与历史记录
未创建 runtime code ／ schema ／ sample package
```

**E. Authoritative Boundary Synchronization（`AD2-REG-01` —— current-state）**

> **历史保留：** 本节 A ～ D、`§4.6.12` Review Revision Log 与 **`§4.6.13` Decision 1 Registration
> Synchronization** 中的**时点表述保留未改**（含 Decision 1 时点的 `producer ownership = OPEN`）。

`Decision 2` 登记后，**上游 authoritative boundary** 亦同步为 current-state：

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-22` | **正式登记 `Decision 2` 已批准的 producer ／ Package Assembly ownership**（Adapter artifact production ＋ record-level provenance 写入；Package Assembly 拥有 `snapshot_package_id` ／ Manifest ／ package organization ／ 完整 package 组装；FIC 只验证 ／ disposition），并**删除**「`Package identity` ／ `manifest` 与 producer ownership 仍为 open」尾注 |
| 2 | `§4.6.2` `AC-23` | 新增第 ④ 项：**`Decision 2` 已于 Issue #74 获 Human Approval** ⇒ **producer ownership ／ `Package identity` ／ `manifest` generation 不再属于未获批项**；**仍未决者仅剩** unresolved marker 的 carrier ／ interface（`Decision 3`）与 security 接口（`Decision 7`） |
| 3 | `§4.6.2` `AC-22` 尾注 | 新增**授权来源区分**：`§3` ／ `§4.3` ／ `§4.4` ／ `§4.5` 为 **historical `Inherited Constraint`**；`Decision 1(a)` ／ `1(b)`（Issue #72）与 `Decision 2`（Issue #74）为 **本层 newly Human-approved registered policy**，**不得**表述为 inherited |
| 4 | `§4.6.5 A` | 结构改为 **A-1 `Inherited Constraint`（历史）** ／ **A-2 本层 newly Human-approved registered policy** ／ **A-3 本层开放**；**producer ownership 行已从开放表移出**，开放表**只**保留真正 pending 项（unresolved carrier ／ security 接口） |
| 5 | `§4.6.8` `ARF-1` | 分列 **历史 inherited** 与 **本层 registered policy**（含 `Decision 2`）；未决项收敛为 unresolved carrier ／ security 接口 |
| 6 | `§4.6.9` `A-1` | 明确区分 inherited ／ newly Human-approved registered；`Decision 2` 已登记的 `owns` 项与仍 open 项分列 |
| 7 | `§4.6.10` `Decision 1` 的 `What changes` | 「producer ownership 仍 open」改为「**亦已由 `Decision 2` 登记**（Issue #74）」 —— 该行属 Decision source 的 current-state 描述，**非** time-point record |

---

#### 4.6.15 Decision 3 Registration Synchronization（Issue #76 —— current-state）

> 本节记录 **Issue #76 登记 `Decision 3`** 后所执行的**最小必要一致性同步**。
> 本节**只**登记已批准的 `Decision 3`（条件组合，以 `UF-2` ／ fail-closed 为主），并使其与
> current-state canonical wording 一致 —— **未**选择 `Decision 4` ～ `8`、**未**推进 `Adapter Boundary` 状态、
> **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ Validation Reason ／ Category ／ status enum、
> **未**设计 Failure ／ Quarantine Interface 的具体形态。

**A. Human Decision registered**

`Decision 3`（unresolved ／ unsupported mapping strategy）已以 **Human Decision Record** 形式
登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 3 = 条件组合，以 UF-2 ／ fail-closed 为主
3.1 approved missing（正常 missing，非 unresolved）
3.2 unresolved ／ ambiguous ／ conflicting ⇒ affected dataset artifact fail closed
3.3 unsupported source ／ exported artifact ⇒ Adapter-side unsupported ／ failure condition ⇒ fail closed
3.4 Adapter Failure ／ Quarantine Interface = AUTHORIZED FOR SEPARATE DESIGN（non-canonical；形态 ／ schema ／ runtime 未完成）
3.5 Package Assembly 不得补 mapping ／ placeholder ／ unresolved-as-null
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.5 C` `UF-1` ／ `UF-2` ／ `UF-3` | `UF-2` 标为 **`SELECTED`（主要策略）**；`UF-1` 标为**未选为主要策略**（仅限既有 approved carrier 可表达范围）；`UF-3` 维持 **`NOT COMPATIBLE`**（`AC-8`） |
| 2 | `§4.6.5 C` 结论段 | 增列 `Decision 3` 之后的定位：fail-closed 为主；Failure ／ Quarantine Interface 形态／schema 仍未定 |
| 3 | `§4.6.4` `AS-4` | 由 `open` 改为 **`IC + Registered`**：unsupported source field ／ vocabulary ／ exported-artifact shape ⇒ Adapter-side failure ⇒ affected dataset artifact fail closed；context 由授权单独设计的 interface 承载 |
| 4 | `§4.6.7` `ADEP-3` | 增列 current-state：fail-closed 策略、禁止 silent skip ／ 强制 `null` ／ fuzzy ／ LLM guess；approved missing 与 unresolved 必须区分 |
| 5 | `§4.6.7` `ADEP-12` | 保留 **Decision 1 ／ 2 时点**历史结论，新增 **current-state**：`UF-2` ／ fail-closed 已登记，Failure ／ Quarantine Interface 已**授权单独设计**（non-canonical、不进入 package、不改 FCM ／ FIC carrier、形态未定） |
| 6 | `§4.6.8` `ARF-3` | 由「开放」改为**已登记**：fail-closed 为主 ＋ 禁止清单；未定项收敛为 interface 物理形态 |
| 7 | `§4.6.8` `ARF-4` | 由「开放」改为**已登记**：approved missing ／ unsupported 归属 ／ Adapter 不产生 disposition 均已登记 |
| 8 | `§4.6.9` `A-5` ／ `A-6` ／ `A-7` | 增列 `Decision 3` 的登记内容（fail-closed 主要策略、interface 授权与边界、unsupported 归属） |
| 9 | `§4.6.2` `AC-23` | 新增第 ⑤ 项：`Decision 3` 已获 Human Approval ⇒ unresolved ／ unsupported 策略与 interface 授权为 **registered**；未决项收敛（仅剩 `Decision 7` 接口 ／ `Decision 4`～`6`／`8` 所辖事项 ／ interface 形态） |
| 10 | `§4.6.5 A-2` | 新增 **unresolved ／ unsupported mapping 策略** 与 **Adapter Failure ／ Quarantine Interface（`AUTHORIZED FOR SEPARATE DESIGN`）** 两行 registered 记录 |
| 11 | `§4.6.5 A-3` | 开放表由 2 项收敛为 **1 项**（仅剩 Adapter ／ `Permission & Security` 接口）；并注明 `Decision 3` 已登记项 |

**C. 明确保留（未被本 Decision 决定）**

```
Decision 4 ～ 8                     = 未决
Failure ／ Quarantine Interface 形态 ／ schema ／ storage ／ API = 未定（已授权单独设计）
Adapter ／ Permission & Security 接口（Decision 7） = OPEN
Adapter Boundary                   = DESIGN PENDING ← 未推进
POC Design v0.2                    = DRAFT
```

**D. Scope / Non-Decision 核验**

- **未**选择或登记 `Decision 4` ～ `8`；
- **未**定义 Failure ／ Quarantine Interface 的最终 carrier ／ schema ／ storage ／ API；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal、**未**新增 Validation Reason ／
  Validation Category ／ canonical status enum；
- **未**修改已 `DESIGN RESOLVED` 的 FCM ／ FIC ／ Snapshot & Import Contract 与 `§4.1` ～ `§4.5` policy；
- **未**创建 Adapter ／ quarantine runtime ／ parser ／ serializer ／ code；
- **未**选择 architecture ／ technology ／ deployment；
- **未**修改 Discovery `FROZEN` docs 或 governance docs；
- **未**推进 `Adapter Boundary` 至 `DESIGN RESOLVED`。

**本次修正的 review-only 边界（自我核验）：**

```
未选择任何 Decision 4 ～ 8
未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未新增 canonical carrier ／ literal ／ Validation Reason ／ Category ／ status enum
未修改 §3 ／ §4.1 ～ §4.5 任何已登记 policy 与历史记录
未创建 runtime code ／ schema ／ sample package
```

**E. Current-state Consistency Corrections（`AD3-REG-01` ～ `AD3-REG-03`）**

> **历史保留：** 本节 A ～ D 与 `§4.6.12` ／ `§4.6.13` ／ `§4.6.14` 的**时点表述保留未改**。

| # | 位置 | 修正 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-22` | **纳入 `Decision 3`** 的 current approved policy（条件组合、以 `UF-2` ／ fail-closed 为主；approved missing 与 unresolved 区分；unsupported ⇒ Adapter-side failure；Failure ／ Quarantine Interface 授权与不可让步边界；Package Assembly 不得补 mapping ／ placeholder ／ unresolved-as-null）；**授权来源区分扩展至 `Decision 3`**，并明确其 **fail-closed policy 与 interface 授权属 `registered`，非 inherited**；reference list 加入 `Decision 3` HD Record |
| 2 | `§4.6.4` `AS-4` | authority label 由 `IC + Registered` 改为 **`Registered`**；并显式拆分：**inherited 部分仅为** general fail-closed 原则（`AC-7` ／ `AC-8` ／ `§3.10`），**Decision 3 本身不得**标为 inherited |
| 3 | `§4.6.7` `ADEP-3` | 改为**分层 handoff**：**(1) fail-closed path** —— affected dataset artifact **不产出** canonical artifact ⇒ **不得伪造** canonical Validation Issue ／ Reason，source-side root cause 由 **non-canonical** interface 承载；**(2) 既有 taxonomy** —— **只**在**真实 canonical validation context** 中适用，**不新增** reason，**不**要求对不存在的 artifact 反向生成 ／ 猜测 reason，**不重开 `§4.4`** |
| 4 | `§4.6.7` `ADEP-6` | 最小同步：区分 **Layer 1（`Final Import Contract`）** ／ **Layer 2 ～ 4（仅在真实 canonical validation context）** ／ **non-canonical fail-closed path（不得伪造 Issue ／ Reason）** |
| 5 | `§4.6.8` `ARF-4` | 最小同步：标注 `Decision 3` 为 **registered（非 inherited）**；加入分层 handoff 说明；interface **已授权但尚未 operationally available** |
| 6 | `§4.6.9` `A-6` | 由「映射到既有 validation reason」改为**分层 handoff 表述**（fail-closed path 不得伪造 reason；既有 taxonomy 只在真实 canonical validation context 适用） |
| 7 | `§4.6.10` `Decision 3` 前的 current-state 注意 | 由「承载方式**未获授权前**不得声称可用」改为：**单独设计已获授权**，但**物理形态 ／ schema ／ runtime implementation 尚未完成** ⇒ 完成前**不得**声称 **operationally available**；`UF-3 = NOT COMPATIBLE` 保留 |
| 8 | `§4.6.5 A-2` ／ `§4.6.10` Decision 3 execution 状态块 | 同步为「授权已有、schema ／ runtime 未完成、尚未 operationally available」 |

---

#### 4.6.16 Decision 4 Registration Synchronization（Issue #78 —— current-state）

> 本节记录 **Issue #78 登记 `Decision 4`** 后所执行的**最小必要一致性同步**。
> 本节**只**登记已批准的 `Decision 4`（**Option ①：只登记 contract requirements，representation carrier deferred**），
> 并使其与 current-state canonical wording 一致 —— **未**选择 `Decision 5` ～ `8`、**未**推进 `Adapter Boundary` 状态、
> **未**规定 mapping rule 的具体技术载体、**未**创建强制 `Mapping Registry` component、
> **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ Validation Reason ／ Category ／ status enum。

**A. Human Decision registered**

`Decision 4`（source-specific mapping rule representation boundary）已以 **Human Decision Record** 形式
登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 4 = Option ① —— Contract requirements only；representation carrier deferred
4.1 Mandatory contract requirements（explicit ／ deterministic ／ traceable ／ reproducible ＋ scope ／ target ／ identity ／ 禁清单）
4.2 Missing ／ conflict behavior ⇒ 服从 Decision 3 fail-closed
4.3 Representation carrier deferred 给 Architecture ／ Implementation
4.4 No mandatory Mapping Registry component
4.5 Decision 5 boundary（mapping_basis 语义粒度仍属 Decision 5）
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-22` | 新增 **source-specific mapping rule representation boundary（`Decision 4`，Issue #78 Human-approved）** 条目（Option ① ＋ 完整 contract requirements ＋ 禁止清单 ＋ 服从 `Decision 3` ＋ carrier deferral ＋ 不创建强制 `Mapping Registry`）；**授权来源区分扩展至 `Decision 4`**；reference list 加入 `Decision 4` HD Record |
| 2 | `§4.6.2` `AC-23` | 新增第 ⑥ 项：`Decision 4` 已于 Issue #78 获 Human Approval ⇒ contract requirements 与 carrier deferral 为 **registered**；未决项更新（`Decision 5`～`6`／`8` 所辖事项；representation 选型归 `§10` ／ 实现，非本层待决） |
| 3 | `§4.6.4` `AS-14` | 由 `open` 改为 **`Registered`**：contract requirements 已登记、representation carrier deferred（不回标 inherited） |
| 4 | `§4.6.5 A-2` | 新增 **mapping rule representation boundary（`Decision 4`）** registered 行 |
| 5 | `§4.6.5 A-3` | 注明 `Decision 4` 已登记项；**representation carrier 明确属 Architecture ／ Implementation**，**不**留在本层 open table |
| 6 | `§4.6.7` `ADEP-2` | 增列 current-state：mapping rule 的 contract requirements 与 carrier deferral 已由 `Decision 4` 登记；representation carrier 归 `ADEP-8`（Architecture） |
| 7 | `§4.6.9` `A-4` | 增列 `Decision 4` 的完整 rule-level contract requirements（含 source ／ target 明确性、rule ＋ revision identity 可审计、**禁 hidden default**）；representation carrier deferred；rule 缺失 ／ 冲突 ／ 非确定性 ⇒ 服从 `Decision 3` |
| 8 | `§4.6.10` current-state note | 更新为 `Decision 1`／`2`／`3`／`4` 已登记；`Decision 5～8` 保持未决 |

**C. 明确保留（未被本 Decision 决定）**

```
Decision 5 ～ 8                     = 未决
mapping_basis 语义粒度（Decision 5）  = OPEN
multi-Adapter governance（Decision 6） = OPEN
Adapter ／ Permission & Security 接口（Decision 7） = OPEN
package closure（Decision 8）         = OPEN
mapping rule representation carrier   = ARCHITECTURE ／ IMPLEMENTATION（§10；本层不规定）
Failure ／ Quarantine Interface 形态 ／ schema ／ runtime = 未定（已授权单独设计）
Adapter Boundary                   = DESIGN PENDING ← 未推进
POC Design v0.2                    = DRAFT
```

**D. Scope / Non-Decision 核验**

- **未**选择或登记 `Decision 5` ～ `8`；
- **未**规定或设计具体 `Mapping Registry`；**未**选择 YAML ／ JSON ／ DB ／ code ／ rule engine ／ framework；
- **未**定义 registry schema ／ table ／ API ／ service；
- **未**决定 `mapping_basis` 语义粒度或字符串格式（属 `Decision 5`）；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal、**未**新增 Validation Reason ／
  Validation Category ／ canonical status enum；
- **未**修改已 `DESIGN RESOLVED` 的 FCM ／ FIC ／ Snapshot & Import Contract ／ Master Data Mapping semantic；
- **未**修改 `Decision 3` 的 Failure ／ Quarantine Interface 具体 design；
- **未**创建 Adapter ／ mapping registry ／ parser ／ runtime code；**未**选择 architecture ／ technology ／ deployment；
- **未**修改 Discovery `FROZEN` docs 或 governance docs；
- **未**推进 `Adapter Boundary` 至 `DESIGN RESOLVED`。

**本次修正的 review-only 边界（自我核验）：**

```
未选择任何 Decision 5 ～ 8
未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未新增 canonical carrier ／ literal ／ Validation Reason ／ Category ／ status enum
未修改 §3 ／ §4.1 ～ §4.5 任何已登记 policy 与历史记录
未创建 runtime code ／ schema ／ sample package
```

---

#### 4.6.17 Decision 5 Registration Synchronization（Issue #82 —— current-state）

> 本节记录 **Issue #82 登记 `Decision 5`** 后所执行的**最小必要一致性同步**。
> 本节**只**登记已批准的 `Decision 5`（**Option ①：minimal rule ／ revision reference**），
> 并使其与 current-state canonical wording 一致 —— **未**选择 `Decision 6` ～ `8`、**未**推进 `Adapter Boundary` 状态、
> **未**定义 `mapping_basis` 的具体 string syntax ／ namespace ／ URI ／ path ／ delimiter ／ hash、
> **未**新增 `"_meta"` member ／ field ／ literal ／ carrier ／ provenance schema、
> **未**修改既有 `evidence` carrier semantics 与 FCM ／ FIC ／ Snapshot & Import Contract。

**A. Human Decision registered**

`Decision 5`（`Mapping ／ Resolution Basis` semantic granularity）已以 **Human Decision Record** 形式
登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 5 = Option ① —— minimal rule ／ revision reference
5.1 mapping_basis = approved mapping rule identity + revision identity（exact JSON string）
5.2 evidence ／ mapping_basis ／ approved mapping rule 三者职责分离；可复现性由三者组合建立
5.3 不承载 source evidence ／ rule logic ／ explanation ／ rationale ／ free text ／ mini-schema
5.4 string syntax ／ encoding deferred 给 Architecture ／ Implementation
5.5 exact-string 不 normalize ／ trim ／ case-fold ／ Unicode-normalize ／ numeric coercion；不新增 "_meta" member ／ literal ／ carrier
5.6 与 Decision 4 的 rule ／ revision identity requirement 对齐；不重新决定 rule 载体
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-22` | 新增 **`Mapping ／ Resolution Basis` semantic granularity（`Decision 5`，Issue #82 Human-approved）** 条目（Option ① ＋ 职责分离 ＋ 三者组合可复现性 ＋ 不承载清单 ＋ syntax deferral ＋ exact-string 边界）；**授权来源区分扩展至 `Decision 5`**；reference list 加入 `Decision 5` HD Record |
| 2 | `§4.6.2` `AC-23` | 新增第 ⑦ 项：`Decision 5` 已获 Human Approval ⇒ `mapping_basis` 语义粒度 **registered**；string syntax ／ encoding 归 Architecture ／ Implementation；未决项更新为 `Decision 6` ／ `8` 所辖事项 |
| 3 | `§4.6.5 E` `PE-1` | 注明 `mapping_basis` 语义已由 `Decision 5` 登记（Option ①），carrier obligation 与原始值保持要求不变 |
| 4 | `§4.6.5 A-2` | 新增 **`Mapping ／ Resolution Basis` semantic granularity（`Decision 5`）** registered 行 |
| 5 | `§4.6.5 A-3` | 注明 `Decision 5` 已登记项；**string syntax ／ encoding 属 Architecture ／ Implementation**，**不**留在本层 open table |
| 6 | `§4.6.7` `ADEP-4` | 增列 current-state：`mapping_basis` 语义粒度已由 `Decision 5` 登记；syntax 留属实现 |
| 7 | `§4.6.8` `ARF-5` | 「仍未决：② `mapping_basis` 语义粒度（Decision 5）」改为 **已登记（Decision 5）**，并保留职责分离与 exact-string 边界 |
| 8 | `§4.6.9` `A-8` | 增列 `Decision 5` 的登记内容（Option ①、三者职责分离、不承载清单、syntax 属实现、不新增 carrier ／ literal） |
| 9 | `§4.6.10` Decision 5 source 条目 | 新增 current-state 注记：该条目为 **Decision source（时点记录）**，结果已登记于下方 HD Record ⇒ **不再是 open item** |
| 10 | `§4.6.10` current-state note | 更新为 `Decision 1`～`5` 已登记；`Decision 6～8` 保持未决；Current Status 顺延为 **`4.6.18`** |

**C. 明确保留（未被本 Decision 决定）**

```
Decision 6 ～ 8                     = 未决
multi-Adapter governance（Decision 6） = OPEN
Adapter ／ Permission & Security 接口（Decision 7） = OPEN
package closure（Decision 8）         = OPEN
mapping_basis string syntax ／ encoding = ARCHITECTURE ／ IMPLEMENTATION（§10；本层不规定）
Failure ／ Quarantine Interface 形态 ／ schema ／ runtime = 未定（已授权单独设计）
Adapter Boundary                   = DESIGN PENDING ← 未推进
POC Design v0.2                    = DRAFT
```

**D. Scope / Non-Decision 核验**

- **未**选择或登记 `Decision 6` ～ `8`；
- **未**定义 `mapping_basis` 的具体 string syntax ／ namespace ／ URI ／ path ／ delimiter ／ hash；
- **未**把 explanation ／ rationale ／ rule logic ／ evidence summary 塞进 `mapping_basis`；
- **未**新增 `"_meta"` member ／ field ／ literal ／ carrier；**未**新增 provenance schema；
- **未**修改既有 `evidence` carrier semantics、FCM ／ FIC ／ Snapshot & Import Contract、
  Master Data Mapping canonical semantic、`Decision 3` Failure ／ Quarantine Interface、`Decision 4` representation-carrier decision；
- **未**新增 Validation Reason ／ Validation Category ／ canonical status enum；
- **未**创建 runtime code ／ serializer ／ parser；**未**选择 architecture ／ framework ／ database ／ technology ／ deployment；
- **未**修改 Discovery `FROZEN` docs 或 governance docs；
- **未**推进 `Adapter Boundary` 至 `DESIGN RESOLVED`。

**本次修正的 review-only 边界（自我核验）：**

```
未选择任何 Decision 6 ～ 8
未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未新增 canonical carrier ／ literal ／ Validation Reason ／ Category ／ status enum
未修改 §3 ／ §4.1 ～ §4.5 任何已登记 policy 与历史记录
未创建 runtime code ／ schema ／ sample package
```

---

#### 4.6.18 Decision 6 Registration Synchronization（Issue #84 —— current-state）

> 本节记录 **Issue #84 登记 `Decision 6`** 后所执行的**最小必要一致性同步**。
> 本节**只**登记已批准的 `Decision 6`（**Option ②：explicit cross-Adapter consistency obligation**），
> 并使其与 current-state canonical wording 一致 —— **未**选择 `Decision 7` ～ `8`、**未**推进 `Adapter Boundary` 状态、
> **未**创建 Cross-Adapter Registry ／ Drift Detection ／ Validator service ／ consistency database ／ event bus ／ API ／
> queue ／ scheduler ／ CI framework ／ dashboard ／ workflow engine、**未**新增 Validation Reason ／ Validation Category ／
> canonical status enum、**未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ schema、
> **未**修改 `§4.5` canonical semantic 与 FCM ／ FIC ／ Snapshot & Import Contract。

**A. Human Decision registered**

`Decision 6`（multi-Adapter governance ／ canonical semantic drift detection）已以 **Human Decision Record** 形式
登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 6 = Option ② —— explicit cross-Adapter consistency obligation
6.1 canonical-first（MS-1）保持 authoritative；MS-2 precedence-first 仍为 NOT COMPATIBLE；不建立 Global Source-Field Precedence
6.2 相同／重叠 canonical entity ／ field ／ semantic ／ relationship ／ scope 的多 Adapter mapping 必须满足 explicit consistency obligation
6.3 conceptual check points：① rule registration ／ revision change；② overlapping canonical use（mechanism deferred 给 Architecture ／ Implementation）
6.4 conflict behavior：禁 Adapter priority ／ source priority ／ first-wins ／ latest-wins ／ LLM ／ heuristic ／ silent reconciliation
6.5 pre-canonical unresolved drift 与 Decision 3 fail-closed 对齐；existing taxonomy 仅在真实 canonical validation context 适用
6.6 Package Assembly 不承担 semantic arbitration ／ reconciliation
6.7 governance scope（obligation）vs implementation mechanism（Architecture ／ Implementation）
6.8 不新增 canonical identifier ／ vocabulary ／ field ／ entity ／ relationship ／ Adapter-specific canonical semantics
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-22` | 新增 **multi-Adapter governance ／ canonical semantic drift detection（`Decision 6`，Issue #84 Human-approved）** 条目（Option ② ＋ canonical-first ＋ consistency obligation ＋ 两个 conceptual check points ＋ 冲突禁止清单 ＋ `Decision 3` 对齐 ＋ mechanism deferral）；**授权来源区分扩展至 `Decision 6`**；reference list 加入 `Decision 6` HD Record |
| 2 | `§4.6.2` `AC-23` | 新增第 ⑧ 项：`Decision 6` 已获 Human Approval ⇒ multi-Adapter governance ／ drift detection 边界 **registered**；detection mechanism 归 Architecture ／ Implementation；未决项收敛为 `Decision 7` 接口 ／ `Decision 8` closure ／ interface 形态；reference list 加入 `Decision 6` HD Record |
| 3 | `§4.6.4` `AS-23` ／ `AS-25` | `AS-23` 增列 current-state：cross-Adapter consistency 义务已登记（冲突处理见 `Decision 6` 6.4 ／ 6.5）；`AS-25` 由 **`open` + prerequisite** 改为 **`Registered`（`Decision 6`）** |
| 4 | `§4.6.5 F` | `MS-1` ／ `MS-2` ／ `MS-3` 之后的 current-state：治理已由 `Decision 6` 登记；**drift detection mechanism 与两个 check points 的实现形态**仍属 Architecture ／ Implementation |
| 5 | `§4.6.5 A-2` | 新增 **multi-Adapter governance ／ canonical semantic drift detection（`Decision 6`）** registered 行 |
| 6 | `§4.6.5 A-3` | 注明 `Decision 6` 已登记项；**detection mechanism 属 Architecture ／ Implementation**，**不**留在本层 open table |
| 7 | `§4.6.7` `ADEP-5` | 增列 current-state：cross-Adapter consistency obligation 已由 `Decision 6` 登记；precedence 仍 `NOT ADOPTED`；机制留属实现 |
| 8 | `§4.6.8` `ARF-6` | 「开放：登记与治理 ／ 检测形态」改为 **已登记（`Decision 6`）**，并保留 mechanism deferral |
| 9 | `§4.6.8` `ARF-5` | 未决项表述收敛：由「`Decision 6` ～ `8` 所辖事项」改为「`Decision 7` ～ `8` 所辖事项」 |
| 10 | `§4.6.9` `A-9` | 增列 `Decision 6` 的登记内容（Option ②、consistency obligation、两个 check points、冲突禁止清单、`Decision 3` 对齐、mechanism 属实现） |
| 11 | `§4.6.10` Decision 6 source 条目 | 新增 current-state 注记：该条目为 **Decision source（时点记录）**，结果已登记于上方 HD Record ⇒ **不再是 open item** |
| 12 | `§4.6.10` current-state note | 更新为 `Decision 1`～`6` 已登记；`Decision 7～8` 保持未决；Current Status 顺延为 **`4.6.19`** |

**C. 明确保留（未被本 Decision 决定）**

```
Decision 7 ～ 8                     = 未决
Adapter ／ Permission & Security 接口（Decision 7） = OPEN
package closure（Decision 8）         = OPEN
drift detection mechanism（CI ／ test ／ registry validation ／ runtime validator ／
  service ／ workflow node ／ DB ／ API ／ manual review）= ARCHITECTURE ／ IMPLEMENTATION（§10；本层不规定）
Cross-Adapter Registry ／ Drift Detector component = NOT CREATED（本 Decision 不创建）
Failure ／ Quarantine Interface 形态 ／ schema ／ runtime = 未定（已授权单独设计）
Adapter Boundary                   = DESIGN PENDING ← 未推进
POC Design v0.2                    = DRAFT
```

**D. Scope / Non-Decision 核验**

- **未**选择或登记 `Decision 7` ～ `8`；
- **未**创建 Cross-Adapter Registry ／ Drift Detection ／ Validator service ／ consistency database ／
  event bus ／ API ／ queue ／ scheduler ／ CI framework ／ dashboard ／ workflow engine；
- **未**定义 concrete drift detection technology ／ CI ／ test framework ／ runtime mechanism；
- **未**新增 Validation Reason ／ Validation Category ／ canonical status enum
  （`ADAPTER_DRIFT` ／ `CROSS_ADAPTER_CONFLICT` 或任何新 reason ／ category ／ status **均不新增**）；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ provenance field ／ schema；
- **未**创建 cross-source precedence ／ Adapter priority ／ source priority；
- **未**修改 FCM ／ FIC ／ Snapshot & Import Contract、`§4.5` Master Data Mapping canonical semantic、
  `Decision 3` ／ `Decision 4` ／ `Decision 5` 已批准内容；
- **未**设计 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 与 Failure ／ Quarantine Interface
  physical schema ／ runtime；
- **未**创建 runtime code ／ tests ／ schema ／ service；**未**选择 architecture ／ framework ／ database ／ deployment；
- **未**修改 Discovery `FROZEN` docs 或 governance docs；
- **未**推进 `Adapter Boundary` 至 `DESIGN RESOLVED`；**未**执行 Adapter Boundary closure（`Decision 8`）。

**本次登记的 review-only 边界（自我核验）：**

```
未选择任何 Decision 7 ～ 8
未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未新增 canonical carrier ／ literal ／ Validation Reason ／ Category ／ status enum
未修改 §3 ／ §4.1 ～ §4.5 任何已登记 policy 与历史记录
未创建 runtime code ／ registry ／ detector ／ validator ／ schema ／ service
```

---

#### 4.6.19 Decision 7 Registration Synchronization（Issue #86 —— current-state）

> 本节记录 **Issue #86 登记 `Decision 7`** 后所执行的**最小必要一致性同步**。
> 本节**只**登记已批准的 `Decision 7`（**Option ①：declarative access-requirement interface**），
> 并使其与 current-state canonical wording 一致 —— **未**选择 `Decision 8`、**未**推进 `Adapter Boundary` 状态、
> **未**设计 `§7` 的 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling、**未**创建 credential ／ secret、
> **未**选择 authentication ／ authorization ／ secret-delivery 技术、**未**改变 `§7` 各 remaining item 的
> `DESIGN PENDING` 状态、**未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ field、
> **未**新增 Validation Reason ／ Category ／ status enum ／ package disposition、
> **未**修改 FCM ／ FIC ／ Snapshot & Import Contract 与 `§4.5` canonical semantic。

**A. Human Decision registered**

`Decision 7`（Adapter ↔ `Permission & Security` interface expectation）已以 **Human Decision Record** 形式
登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 7 = Option ① —— declarative access-requirement interface
7.1 Adapter 只声明 minimum authorized access requirements（resource boundary ／ operation ／ logical data scope ／ authorized access context ／ secret dependency）
7.2 RBAC ／ Data Scope ／ Tool Permission ／ authorization decision ／ credential lifecycle ／ Secret Handling 不归 Adapter
7.3 required authorized access 不可用 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ fail closed ／ do not proceed
7.4 Permission ／ Security dependency failure ≠ canonical missing ／ mapping unresolved ／ DATA_INCOMPLETE ／ Data Validation reason ／ package disposition；不扩展 Decision 3 interface
7.5 secret boundary：不写真实 credential ／ secret；不放入 Git ／ prompt ／ log ／ carrier ／ provenance；不选择 secret manager 等 mechanism
7.6 严格限于 Data Landing Zone ／ Controlled Export 之后；不含 source-system ／ export-side ／ Production credentials
7.7 interface expectation ≠ injection mechanism（injection ／ broker ／ sidecar ／ token exchange ／ policy agent 等不选）
7.8 AI Effective Permission invariant 保持；declared requirement 不扩大 effective permission
7.9 不 inflate 状态：§7 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 仍 DESIGN PENDING；Adapter Boundary 仍 DESIGN PENDING
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.2` `AC-21` | 增列 current-state：Adapter Boundary **只**登记 interface expectation（Option ①）；`RBAC` ／ `Data Scope` ／ `Tool Permission` ／ `Secret Handling` **仍 `DESIGN PENDING`**，`§7` **未**关闭 |
| 2 | `§4.6.2` `AC-22` | 新增 **Adapter ↔ `Permission & Security` interface expectation（`Decision 7`，Issue #86 Human-approved）** 条目（Option ① ＋ 声明内容 ＋ ownership 排除清单 ＋ fail-closed ／ 禁止清单 ＋ failure classification ＋ secret boundary ＋ Data Landing Zone-only ＋ injection mechanism deferral ＋ effective-permission invariant）；**授权来源区分扩展至 `Decision 7`**；reference list 加入 `Decision 7` HD Record |
| 3 | `§4.6.2` `AC-23` | 新增第 ⑨ 项：`Decision 7` 已获 Human Approval ⇒ security interface expectation **registered**；未决项收敛为 `Decision 8` closure ／ Failure ／ Quarantine 形态 ／ Architecture ／ Implementation 选型；reference list 加入 `Decision 7` HD Record |
| 4 | `§4.6.4` `AS-27` ／ `AS-28` | 由 **`open` + prerequisite** 改为 **`Registered`（`Decision 7`）＋ `open`（`§7` 相应项仍 `DESIGN PENDING`）**，并登记 secret dependency 与 logical data scope 的声明边界 |
| 5 | `§4.6.5 A` code block | 「仍 open（Decision 7）」改为「**已登记（Decision 7）**：Adapter ／ `Permission & Security` interface expectation（Option ① 声明式）」；补记「仍 open（Decision 8）」 |
| 6 | `§4.6.5 A-2` | 新增 **Adapter ↔ `Permission & Security` interface expectation（`Decision 7`）** registered 行 |
| 7 | `§4.6.5 A-3` | 开放表最后一项移出（表内标注**无** open ownership 项）；新增 `Decision 7` 已登记注记；未决仅余 `Decision 8` closure gate |
| 8 | `§4.6.5 F` ／ `§4.6.5 G` | G 的「开放：接口形态」改为 **已登记（`Decision 7`）**；并注明 `§7` 各 remaining item 仍 `DESIGN PENDING` |
| 9 | `§4.6.6` Option Comparison | Adapter ／ `Permission & Security` 接口行标注 **已登记（`Decision 7`）** 与 mechanism deferral |
| 10 | `§4.6.7` `ADEP-7` ／ `ADEP-9` | `ADEP-7` 增列 current-state（interface expectation 已登记；`§7` 仍 pending）；`ADEP-9` 增列「access requirement 严格限于 Data Landing Zone 之后」 |
| 11 | `§4.6.8` `ARF-1` ／ `ARF-7` ／ `ARF-8` | 未决列表中的 security 接口改为 **已登记（`Decision 7`）**；`ARF-8` 由「只登记 dependency 与可选形态」改为 **Option ① 已登记** |
| 12 | `§4.6.9` `A-1` ／ `A-10` ／ `A-11` | `A-1` 的 open ② 改为 **registered（`Decision 7`）**（open 缩至 Failure ／ Quarantine 形态与 `§7` 具体设计）；`A-10` ／ `A-11` 增列 `Decision 7` 登记内容与「由谁提供」的实现机制不在本层登记 |
| 13 | `§4.6.10` Decision 7 source 条目 | 新增 current-state 注记：该条目为 **Decision source（时点记录）**，结果已登记于上方 HD Record ⇒ **不再是 open item** |
| 14 | `§4.6.10` current-state note | 更新为 `Decision 1`～`7` 已登记；`Decision 8` 保持未决；Current Status 顺延为 **`4.6.20`** |

**C. 明确保留（未被本 Decision 决定）**

```
Decision 8                         = 未决（Adapter Boundary closure gate）
§7 RBAC                            = DESIGN PENDING ← 未改变
§7 Data Scope                      = DESIGN PENDING ← 未改变
§7 Tool Permission                 = DESIGN PENDING ← 未改变
§7 Secret Handling                 = DESIGN PENDING ← 未改变
§7 Permission & Security overall   = 不得宣称 DESIGN RESOLVED
security runtime mechanism（injection ／ broker ／ sidecar ／ secret mount ／ token exchange ／
  identity federation ／ service account ／ policy agent ／ auth middleware ／ API gateway）
                                   = ARCHITECTURE ／ IMPLEMENTATION（本层不选择）
credential issuance ／ storage ／ retrieval ／ rotation ／ lifecycle = §7 ／ Architecture ／ Implementation
Failure ／ Quarantine Interface 形态 ／ schema ／ runtime = 未定（已授权单独设计；Decision 7 不扩展）
Adapter Boundary                   = DESIGN PENDING ← 未推进
POC Design v0.2                    = DRAFT
```

**D. Scope / Non-Decision 核验**

- **未**选择或登记 `Decision 8`；**未**执行 Adapter Boundary closure；**未**推进至 `DESIGN RESOLVED`；
- **未**设计 RBAC role model ／ permission matrix、Data Scope policy、Tool Permission policy、
  authentication ／ authorization mechanism、identity ／ principal schema；
- **未**创建 credential ／ secret，**未**定义 credential value ／ name ／ path，
  **未**选择 Vault ／ Secrets Manager ／ Kubernetes Secret ／ env ／ OAuth ／ service account ／ API key，
  **未**设计 secret provisioning ／ storage ／ rotation ／ retrieval；
- **未**将 `§7` overall ／ RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 标记为 resolved；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ field；**未**新增 Validation Reason ／
  Validation Category ／ status enum ／ package disposition；**未**新增 security failure enum；
- **未**修改 `Decision 3` Failure ／ Quarantine Interface 的 schema ／ responsibility；
- **未**修改 FCM ／ FIC ／ Snapshot & Import Contract、`§4.5` Master Data Mapping canonical semantic、
  `Decision 1` ～ `Decision 6` 已批准内容；
- **未**创建 runtime code ／ auth middleware ／ policy engine ／ service ／ API ／ schema；
  **未**选择 architecture ／ framework ／ database ／ deployment；
- **未**修改 Discovery `FROZEN` docs 或 governance docs。

**本次登记的 review-only 边界（自我核验）：**

```
未选择 Decision 8
未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未改变 §7 各 remaining item 的 DESIGN PENDING 状态
未新增 canonical carrier ／ literal ／ Validation Reason ／ Category ／ status enum ／ package disposition
未创建 credential ／ secret，未写入任何真实 secret
未修改 §3 ／ §4.1 ～ §4.5 任何已登记 policy 与历史记录
未创建 runtime code ／ auth middleware ／ policy engine ／ schema ／ service
```

---

#### 4.6.20 Decision 8 Registration Synchronization（Issue #88 —— current-state）

> 本节记录 **Issue #88 登记 `Decision 8`** 后所执行的**最小必要 current-state consistency synchronization**。
> 本节**只**登记已批准的 Decision 8（closure policy），并使其与 current-state canonical wording 一致 ——
> **未**在本 PR 推进 `Adapter Boundary` 状态、**未**执行 closure、**未**伪造 `A-1` ～ `A-14` 的 PASS 结果、
> **未**把 `A-15` ／ `A-16` 升级为 hard blocker、**未**授权 blanket runtime implementation、
> **未**关闭 `§7` ／ Failure ／ Quarantine ／ Architecture deferrals、
> **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ field 与 Validation Reason ／ Category ／
> status enum、**未**修改 `Decision 1` ～ `Decision 7` 已批准内容与 FCM ／ FIC ／ `§4.5` canonical semantic。

**A. Human Decision registered**

`Decision 8`（minimum closure criteria acceptance ／ dedicated closure gate authorization）已以
**Human Decision Record** 形式登记于 **`§4.6.10`**（`Registration Status：REGISTERED`）。

```
Decision 8 = Accept A-1 ～ A-14 ＋ authorize dedicated Adapter Boundary Closure Design Change
             ＋ conditional status advancement；no blanket runtime implementation authorization
8.1  A-1 ～ A-14 = MANDATORY MINIMUM CLOSURE CRITERIA（逐项 PASS ／ FAIL verification 由 Closure PR 执行）
8.2  A-15 ／ A-16 = POC DESIGN OBJECTIVE（必须评估、non-blocking、不得升级为 hard gate）
8.3  Dedicated Closure PR required（不在本 Decision 内关闭 Adapter Boundary）
8.4  Conditional status advancement（A-1 ～ A-14 全 PASS ⇒ 才允许 DESIGN PENDING → DESIGN RESOLVED）
8.5  Failure ／ Quarantine physical shape ／ schema ／ runtime 仍开放；不自动阻止 conceptual closure
8.6  §7 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling 仍 DESIGN PENDING；不自动阻止 conceptual closure
8.7  real source field unknown 继续 non-blocking
8.8  no blanket implementation authorization（后续 implementation 须独立、明确授权）
8.9  Architecture ／ Implementation deferrals 保持；ADR 仍未创建
8.10 registration-time：Decision 1 ～ 8 = REGISTERED；Adapter Boundary = DESIGN PENDING；POC Design v0.2 = DRAFT
```

**B. Minimum synchronization applied**

| # | 位置 | 同步内容 |
| --- | --- | --- |
| 1 | `§4.6.9` 标题 ／ 状态 | 由「**candidate —— 待 Human 批准**」改为 **Human-approved minimum closure criteria**；新增 current-state 与 closure gate wording（`A-1` ～ `A-14` mandatory；`A-15` ／ `A-16` non-blocking；`Adapter Boundary` 仍 `DESIGN PENDING`；PASS ／ FAIL verification 归 Dedicated Closure PR） |
| 2 | `§4.6.9` `A-1` | 「仍 open（绑定 Decision）」改为「**仍未完成但由 `Decision 8` 明确为 non-blocking**」（Failure ／ Quarantine 形态、`§7` 具体设计**不**构成 mandatory closure blocker，**亦不得**写成已完成） |
| 3 | `§4.6.9` `A-13` ／ `A-14` | `A-13` 增列 **Closure PR 必须显式执行 composition check**；`A-14` 增列 **`Decision 8` 确认 real source field unknown 继续 non-blocking** |
| 4 | `§4.6.9` `A-15` ／ `A-16` | 保持 **POC DESIGN OBJECTIVE**；增列「必须在 Closure PR 显式评估、给出简洁结论 ／ evidence、**不得**升级为 hard closure gate」 |
| 5 | `§4.6.9` 尾注 | 新增 `Decision 8` 登记说明（mandatory vs non-blocking；唯一例外 = 评估暴露 `A-1` ～ `A-14` 客观失败） |
| 6 | `§4.6.5 A-3` | 开放表说明更新为 `Decision 1` ～ `Decision 8` 已登记；落点改为 **Dedicated Adapter Boundary Closure Design Change PR** |
| 7 | `§4.6.8` `ARF-7` | 增列 `Decision 8` 登记：minimum closure criteria = `A-1` ～ `A-14`；逐项 verification 与条件性状态转换归 Dedicated Closure PR（**本 Decision 不推进状态**） |
| 8 | `§4.6.8` `ARF-8` | 增列 `Decision 8` 8.6：remaining `§7` 设计**不自动阻止** Adapter Boundary conceptual closure |
| 9 | `§4.6.2` `AC-22` | 新增 **Adapter Boundary closure policy（`Decision 8`，Issue #88 Human-approved）** 条目（mandatory criteria ＋ non-blocking objectives ＋ dedicated Closure PR ＋ conditional advancement ＋ 「不表示什么」清单 ＋ `§7` ／ Failure ／ Quarantine 非阻断 ＋ no blanket implementation authorization ＋ deferrals 保持）；**授权来源区分扩展至 `Decision 8`**；reference list 加入 `Decision 8` HD Record |
| 10 | `§4.6.2` `AC-23` | 新增第 ⑩ 项：`Decision 8` 已获 Human Approval ⇒ closure policy **registered**；未决项更新为「本层已无剩余 Human Decision；下一步 gate = Dedicated Closure PR」；reference list 加入 `Decision 8` HD Record |
| 11 | `§4.6.10` Decision 8 source 条目 | 新增 current-state 注记：该条目为 **Decision source（时点记录）** ⇒ **不再是 open item** |
| 12 | `§4.6.10` current-state note ／ next gate wording | 更新为 `Decision 1` ～ `8` 已登记、本层无剩余 undecided Human Decision；明确 **本 registration PR 不推进状态**；**下一步 gate = Dedicated Adapter Boundary Closure Design Change PR**；Current Status 顺延为 **`4.6.21`** |

**C. 明确保留（未被本 Decision 决定 / 关闭）**

```
Decision 1 ～ 8                    = REGISTERED
Adapter Boundary                   = DESIGN PENDING ← 本 PR 未推进
POC Design v0.2                    = DRAFT
Closure verification（A-1 ～ A-14） = PENDING ← Dedicated Adapter Boundary Closure Design Change PR
DESIGN RESOLVED                    = 未登记（不得由本 PR 登记）
§7 RBAC / Data Scope / Tool Permission / Secret Handling = DESIGN PENDING ← 未改变
§7 Permission & Security overall   = 不得标记为 DESIGN RESOLVED
Failure / Quarantine physical shape / schema / storage / API / runtime = 未设计 / 未 operationally available
mapping rule representation carrier / mapping_basis concrete string syntax / drift detection mechanism /
  Package Assembly runtime shape / auth / credential / secret-delivery mechanism /
  framework / database / API / deployment / ADR = ARCHITECTURE / IMPLEMENTATION DEFERRALS（保持）
blanket runtime implementation authorization = NOT GRANTED
```

**D. Scope / Non-Decision 核验**

- **未**在本 PR 把 `Adapter Boundary` 改为 `DESIGN RESOLVED`；**未**执行 Adapter Boundary closure；
- **未**伪造 `A-1` ～ `A-14` 的 PASS 结果；**未**预写 Closure PR 的 verification 结论；
- **未**把 `A-15` ／ `A-16` 升级为 hard blocker；
- **未**授权或创建 runtime implementation（Adapter runtime code ／ connector ／ parser ／ serializer ／
  mapping registry ／ mapping rule storage ／ Failure ／ Quarantine implementation ／ drift detector ／
  runtime validator ／ auth middleware ／ credential ／ secret mechanism ／ database ／ API ／ framework ／
  deployment ／ source-system integration 均**未**授权或创建）；
- **未**设计 Failure ／ Quarantine Interface physical shape ／ schema ／ runtime；
- **未**设计 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling；**未**修改 `§7` remaining statuses；
- **未**选择 architecture ／ framework ／ database ／ API ／ deployment；**未**创建 ADR；
- **未**定义 mapping rule concrete carrier 或 `mapping_basis` concrete syntax；**未**选择 drift detection mechanism；
- **未**创建 credential ／ secret；
- **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ field、Validation Reason ／ Category ／
  status enum ／ package disposition；
- **未**修改 FCM ／ FIC ／ Snapshot & Import Contract、Master Data Mapping canonical semantic、
  `Decision 1` ～ `Decision 7` 已批准内容；
- **未**修改 Discovery `FROZEN` docs 或 governance docs。

**本次登记的 review-only 边界（自我核验）：**

```
未推进 Adapter Boundary 状态（仍 DESIGN PENDING）
未登记 DESIGN RESOLVED
未伪造 A-1 ～ A-14 PASS 结果
未将 A-15 / A-16 升级为 hard blocker
未授权 blanket implementation
未改变 §7 各 remaining item 的 DESIGN PENDING 状态
未新增 canonical carrier / literal / Validation Reason / Category / status enum
未创建 runtime code / registry / detector / validator / ADR / service / credential / secret
未修改 §3 / §4.1 ～ §4.5 任何已登记 policy 与历史记录
```

---

#### 4.6.21 Adapter Boundary Closure Validation（Decision 8 closure gate —— Issue #90）

> 本节依据 **Human-approved `Decision 8`（Issue #88）** 授权的 closure gate 执行 **Dedicated Adapter Boundary
> Closure Validation**。本节**不是**新的 Human Decision —— **不**创建新 policy、**不**重开
> `Decision 1` ～ `Decision 8`、**不**选择任何新 Option。
> Verification 基准 = **current canonical design**（`docs/design/poc-design-v0.2.md` 的现行 canonical 文本）。
> **未**新增 canonical carrier ／ `"_meta"` member ／ literal ／ field、Validation Reason ／ Category ／
> status enum ／ package disposition；**未**创建 runtime ／ 架构 ／ credential ／ secret artifact。

**A. Closure Gate Result**

```
Closure Gate          = Dedicated Adapter Boundary Closure Design Change（Decision 8 授权 ／ Issue #90）
Mandatory criteria    = A-1 ～ A-14（Human-approved minimum closure criteria）
Closure Gate Result   = PASS —— A-1 ～ A-14 全部 PASS；FAIL 数 = 0
A-15 ／ A-16          = NON-BLOCKING assessment 完成（无 mandatory-criterion failure 被暴露）
Adapter Boundary      = DESIGN PENDING → DESIGN RESOLVED（由本 Closure Validation 登记）
POC Design v0.2       = DRAFT（未改变）
§7 Permission & Security overall = DESIGN PENDING（未改变）
Failure ／ Quarantine physical shape ／ schema ／ storage ／ API ／ runtime = 未设计 ／ 未 operationally available（未改变）
Architecture ／ ADR   = 未决定 ／ 尚无正式 ADR（未改变）
blanket runtime implementation authorization = NOT GRANTED（未改变）
```

**B. Per-criterion verification（`A-1` ～ `A-14`）**

| # | Criterion（`§4.6.9`） | Result | Canonical evidence（现行文本） |
| --- | --- | --- | --- |
| `A-1` | ownership ／ does-not-own boundary | **PASS** | `§4.6.2` `AC-22`（`Decision 1(a)` ／ `Decision 1(b)` ／ `Decision 2` ／ `Decision 3` ／ `Decision 4` ／ `Decision 5` ／ `Decision 6` ／ `Decision 7` 各条目：owns 读取 ／ 提取、format ／ protocol handling、generic source-field identification、source-specific mapping execution、canonical dataset artifact production、自身 source-derived provenance ／ locator ／ `mapping_basis`；Package Assembly owns `snapshot_package_id` ／ Manifest ／ package-level references ／ organization ／ 完整原子 package；`Final Import Contract` owns 验证 ／ acceptance ／ disposition）＋ `AC-23` ①～⑩（逐 Decision registered 追踪）＋ `§4.6.5 A-1` ／ `A-2` ／ `A-3` ＋ `§4.6.8` `ARF-1` ＋ `ADEP-11` ／ `ADEP-12` ／ `ADEP-13`。**does-not-own：** source-system connectivity ／ Controlled Export 上游 ／ export-side protocol ／ credentials（`AC-22` ／ `ADEP-9`）、package acceptance ／ disposition（`AC-22` ／ `AO-2`）、RBAC ／ Data Scope ／ Tool Permission policy ／ authorization decision ／ credential lifecycle ／ Secret Handling（`Decision 7` 7.2 ／ `AC-21`）。**授权来源可区分：** `AC-22` 明确区分 historical `Inherited Constraint` 与 newly Human-approved registered policy |
| `A-2` | input conceptual contract | **PASS** | `AC-1` ／ `AC-2`（Controlled Export ／ Snapshot 唯一通道；不得直连、不得扩大 source access）／ `AC-3`（unavailable ⇒ fail closed）；`§4.6.5 B` `AI-1` 为 `Inherited Constraint`、`AI-2` = `NOT COMPATIBLE`；`ARF-2`；`ADEP-9`；`AS-1` ／ `AS-2`；`Decision 7` 7.6 禁 source-system fallback |
| `A-3` | output conceptual contract ／ Package Assembly boundary | **PASS** | `AC-15`（FIC `DESIGN RESOLVED`）；`§4.6.5 B` `AO-1` ＋ `P-1`（FIC-valid output invariant）＋ `P-2`（`Decision 2` producer ownership）；`ARF-2`；`ADEP-1` ／ `ADEP-11`；`AS-15` ／ `AS-19` ／ `AS-20`；`§4.6.9` `A-3` 明示 partial artifacts 不得单独视为可接受 package（**禁止 dataset-level partial acceptance**），`Final Import Contract` 只验证 ／ disposition |
| `A-4` | determinism ／ rule-level contract | **PASS** | `AC-5` ／ `AC-6`；`§4.6.5 C`；`Decision 1(b)` HD Record；**`Decision 4` HD Record（Option ①：explicit ／ deterministic ／ traceable ／ reproducible；source ／ source scope 与 logical dataset ／ canonical target；rule identity ＋ revision identity 可审计可复现；canonical result ← approved rule ／ revision；禁 hidden default ／ fuzzy ／ similarity ／ LLM guess ／ silent normalization；不得重定义 canonical semantic ／ enum ／ mapping contract；不得建立 Global Source-Field Precedence）**；`ADEP-2`；`AS-14`；representation carrier 明确 deferred |
| `A-5` | fail-safe behavior | **PASS** | `AC-7` ／ `AC-8` ／ `AC-9` ／ `AC-10`；`§4.6.5 C`；`Decision 3` HD Record（unresolved ／ ambiguous ／ conflicting ／ unsupported ⇒ `UF-2` ／ fail-closed；不产出伪 canonical artifact；approved missing 与 unresolved 必须区分）；`ARF-9`；`AS-11` ／ `AS-12` |
| `A-6` | unresolved Adapter-side contract ／ handoff | **PASS** | `Decision 3` HD Record（strategy ／ responsibility registered；affected dataset artifact 不产出；context 归 **non-canonical** Adapter Failure ／ Quarantine Interface；不进入 Snapshot Package、不改现有 FCM ／ FIC carrier ／ canonical schema）；`ADEP-3` ／ `ADEP-6` ／ `ADEP-12`；`ARF-4`；**`Decision 8` 8.5：其 physical shape ／ schema ／ runtime 未完成不自动阻止 conceptual closure**（本 Closure 据此判定 **non-blocking**，且**未**声称其已完成） |
| `A-7` | unsupported-source behavior ／ reporting boundary | **PASS** | `ARF-4` ②（unsupported source field ／ vocabulary ／ exported-artifact shape ／ 无法识别 input 属 Adapter-side unsupported ／ failure condition ⇒ fail closed、不生成假 canonical artifact）；`AS-4`；`ADEP-6`；Adapter 不自行产生 package disposition 或新 Validation Reason |
| `A-8` | evidence locator ／ `mapping_basis` boundary | **PASS** | `AC-12` ／ `AC-13`（locator = opaque exact string，保持原始 identity value；禁 trim ／ case conversion ／ Unicode normalization ／ numeric coercion）／ `AC-14`；`§4.6.5 E` `PE-1`（producer-neutral carrier obligation）＋ `PE-2` = `NOT COMPATIBLE`；`Decision 2` HD Record（Adapter 写入自身 source-derived record-level provenance）；`Decision 5` HD Record（`mapping_basis` 只标识 approved rule identity ＋ revision identity；`evidence` ／ `mapping_basis` ／ approved mapping rule 三者职责分离；不承载 evidence ／ rule logic ／ explanation ／ rationale ／ mini-schema；concrete syntax 属 Architecture ／ Implementation）；`ADEP-4`；`AS-18` |
| `A-9` | multi-source ／ multi-Adapter semantic stability | **PASS** | `AC-18`（`Global Source-Field Precedence = NOT ADOPTED`）／ `AC-19`；`§4.6.5 F` `MS-1`（canonical-first）／ `MS-2` = `NOT COMPATIBLE` ／ `MS-3`；**`Decision 6` HD Record`6.1`～`6.9`**（explicit cross-Adapter consistency obligation；两个 conceptual check points = rule registration ／ revision change 与 overlapping canonical use；禁 Adapter priority ／ source priority ／ first-wins ／ latest-wins ／ LLM ／ heuristic ／ silent reconciliation；Package Assembly 不承担 semantic arbitration；unresolved drift 与 `Decision 3` fail-closed 对齐；detection mechanism 属 Architecture ／ Implementation）；`ADEP-5`；`ARF-6` |
| `A-10` | cross-layer boundary | **PASS** | `§4.6.5 G`（`Permission & Security` ／ Architecture ／ Implementation 各自归属；source-system connectivity 属 POC 之外）；`ARF-7` ／ `ARF-8`；`ADEP-7` ／ `ADEP-8` ／ `ADEP-9`；`§7` status table 未改变。**本 Closure Validation 明确不声称：** `§7` overall resolved、Failure ／ Quarantine runtime 已设计、Architecture 已选择、Implementation 已完成（见 E 节） |
| `A-11` | Adapter ↔ `Permission & Security` interface expectation | **PASS** | **`Decision 7` HD Record`7.1`～`7.10`**（Option ① declarative access-requirement interface：Adapter 只声明 minimum Data Landing Zone-side resource boundary ／ operation ／ logical data scope ／ authorized access context ／ secret dependency；不自授权、不猜测替代 credential、不绕过 policy、不 fallback 到 source system；required authorized access 不可用 ／ 不满足 ／ 失效 ／ 无法可靠确认 ⇒ fail closed ／ do not proceed；Permission ／ Security dependency failure 不得重解释为 canonical missing ／ mapping unresolved ／ `DATA_INCOMPLETE` ／ Data Validation reason ／ package disposition）；`AC-21` ／ `AC-22`（`Decision 7` 条目）；`ARF-8`；`ADEP-7`；`AS-27` ／ `AS-28`；`§7` 细节设计仍独立 `DESIGN PENDING` |
| `A-12` | failure reporting boundary | **PASS** | `AC-16`（四层 validation model；Validation Issue Taxonomy 8 categories ／ 12 reasons 为 `REGISTERED`，**不得**新增 root reason）；`§4.6.5 D`（root condition 归属表）；`ADEP-3` ／ `ADEP-6`（Layer 1 归 `Final Import Contract`；Layer 2 ～ 4 归 Data Validation；pre-canonical fail-closed path 不得伪造 canonical Validation Issue ／ Reason）；`AS-30`；`ARF-4` ③。本 Closure **未**新增任何 Validation Category ／ Reason ／ status enum |
| `A-13` | selected-decision composition check | **PASS** | 见 **C 节**（对照 `§3` ／ `§4.3` ／ `§4.4` ／ `§4.5` 的显式四向核验；未发现需要新 Human Decision 的未登记冲突） |
| `A-14` | real source field unknown = non-blocking | **PASS** | `AC-17`（真实 source field 未知 **≠** Design Pending；physical carrier = `SOURCE-SPECIFIC`）；`ADEP-10`；`AS-29`；`§4.6.9` `A-14`（`DESIGN RESOLVED ≠ real ERP field known ≠ Adapter implemented ≠ tested`）；`Decision 8` 8.7。Closure **未**要求真实 ERP table ／ column、真实 credential 或 runtime source discovery |

**C. `A-13` selected-decision composition check（显式四向核验）**

被核验的组合 = **`Decision 1` ～ `Decision 7` 的已选组合 ＋ `Decision 8` 的 closure policy**。

**C.1 对 `§3` System Boundary：**

```
无 source-system direct connectivity        —— AC-1 ／ AC-2 ／ ADEP-9 ／ Decision 7 7.6
无绕过 Controlled Export                    —— AC-1 ／ AC-2 ／ AS-2 ／ Decision 7 7.3（禁绕过 Data Landing Zone）
无 Production write                         —— AC-1（WRITE = DENIED）／ AO-2 = NOT COMPATIBLE ／ AS-20
POC approval ≠ Production execution         —— §3 hard boundary ＋ Decision 8 8.4（DESIGN RESOLVED 不表示 production-ready）
fail-closed 行为未被削弱                     —— AC-3 ／ §3.10 ／ Decision 3 ／ Decision 7 7.3
```

结论：**无未登记冲突（PASS）**。

**C.2 对 `§4.3` Snapshot ／ Import Contract ／ FCM ／ FIC：**

```
仅使用 approved carriers ／ literals        —— AC-12 ／ AC-13 ／ AC-14 ＋ ADEP-4；Decision 5 ／ 6 ／ 7 ／ 8 均不新增 carrier
Package Assembly 遵守 atomic complete package —— Decision 2 HD Record ＋ ADEP-1 ／ ADEP-11 ／ IC-13
无 partial acceptance                       —— ADEP-1 ／ ADEP-11 ／ §4.6.9 A-3（禁止 dataset-level partial acceptance）
无新增 "_meta" member                       —— §4.3.28 E（unknown member ⇒ reject）＋ Decision 3 ／ 5 ／ 7 ／ 8 明示不新增
无 Adapter-owned acceptance ／ disposition   —— AO-2 = NOT COMPATIBLE ／ AS-20 ／ P-1 ／ ADEP-1
无 unresolved ／ failure artifact 被静默塞入 canonical package —— Decision 3 fail-closed ＋ Failure ／ Quarantine 为 non-canonical 且不进入 Snapshot Package（ADEP-12）
```

结论：**无未登记冲突（PASS）**。

**C.3 对 `§4.4` Data Validation：**

```
无新增 Validation Reason ／ Category        —— AC-16（8 categories ／ 12 reasons REGISTERED；不得新增 root reason）；Decision 3 ／ 6 ／ 7 ／ 8 均声明不新增
无 source-side root-cause 反向猜测          —— ARF-4 ② ／ ADEP-6
pre-canonical fail-closed path 不伪造 issue —— ADEP-3 (1) ／ ADEP-6 ／ ARF-4
taxonomy 仅在真实 canonical validation context 适用 —— ADEP-3 (2) ／ ADEP-6 ／ A-6 ／ §4.6.5 D
与 §4.4 既有语义相容                       —— §4.4 的 validation 判定以 canonical artifact ／ capability context 实际存在为前提（例如 §4.4.15 的 root-condition 表）；Decision 3 的 fail-closed path 不产出该 artifact，故二者为已登记的**分层 handoff**，非冲突
```

结论：**无未登记冲突（PASS）**。

**C.4 对 `§4.5` Master Data Mapping：**

```
Adapter rules implement 而不 redefine canonical semantic —— AC-5 ／ AC-6 ／ §4.5.2 ＋ Decision 4 HD Record ／ AC-22
无 global source precedence                 —— AC-18（NOT ADOPTED）／ §4.5.21 Option D ／ Decision 1(b) ／ Decision 4 ／ Decision 6
无 silent normalization                     —— AC-6 ／ AC-13 ／ AS-12
既有 mapping contracts 保持 authoritative    —— §4.5.2 ／ §4.5.11 ／ §4.5.21 ＋ ADEP-2
source-specific rules ／ multi-Adapter consistency 与 §4.5 相容 —— Decision 4 只登记 rule contract requirements；Decision 6 明确不重定义 §4.5 已 DESIGN RESOLVED 的 mapping contracts
```

结论：**无未登记冲突（PASS）**。

**四向核验总结果：`A-13` = `PASS`** —— 未发现无法由既有已批准 canonical text 解决的冲突；
**本 Task 未创建任何新 Human Decision、未引入 Exception ／ waiver。**

**D. `A-15` ／ `A-16` non-blocking objective assessment**

| Objective | 评估 | Evidence（现行文本） | 结论 |
| --- | --- | --- | --- |
| `A-15` Human Inspectability | **PASS** | 每个 mapping 均有可审计的 **rule identity ＋ revision identity** 与「canonical result ← approved rule ／ revision」可追溯性（`Decision 4`）；`Stable Source Evidence Locator` 保持原始 identity value（`AC-12` ／ `AC-13`）；`mapping_basis` 只标识 approved rule ＋ revision，且与 `evidence` ／ rule 职责分离（`Decision 5`）；unresolved ／ unsupported 有显式 fail-closed 边界与不得压平要求（`AC-9` ／ `AC-10` ／ `Decision 3`）；**禁** hidden default ／ fuzzy ／ similarity ／ LLM guess（`Decision 4` ／ `AS-14`） | **NON-BLOCKING**；conceptual 层面已可人工检视与追溯。runtime inspectability tooling 属 Architecture ／ Implementation，**不**阻断 conceptual closure |
| `A-16` Implementation Simplicity | **PASS** | **不**要求强制 `Mapping Registry` component（`Decision 4` Option ①）；**不**规定 mapping rule storage ／ carrier 技术（`Decision 4`）；**不**要求 drift-detection service（`Decision 6` 6.7）；**不**选择 auth ／ injection ／ secret-manager mechanism（`Decision 7` 7.7）；**未**新增 carrier ／ `"_meta"` member ／ literal ／ schema ／ status enum（`Decision 3` ／ `5` ／ `6` ／ `7` ／ `8`） | **NON-BLOCKING**；conceptual contract 保持最小，closure **未**引入新组件或新复杂度 |

两项评估均**未**暴露任何 `A-1` ～ `A-14` 的客观失败，故**不**转为 blocking（`Decision 8` 8.2）。

**E. 本 Closure 的含义 ／ 不含义**

**含义：** Adapter 的 **conceptual responsibility ／ behavioral ／ cross-layer boundary** 已达到当前
**POC design closure 标准**（`Decision 8` 8.4）。

**明确不表示（`Decision 8` 8.4 清单，逐项保持）：**

```
IMPLEMENTED
TESTED
production-ready
real ERP ／ source field known
runtime Adapter exists
mapping registry exists
mapping_basis concrete string syntax 已选
cross-Adapter drift detection mechanism 已实现
Permission & Security overall 已完成
Failure ／ Quarantine Interface runtime 已实现
Architecture ／ ADR 已完成
POC Design overall APPROVED ／ FROZEN
```

**本 Closure 未改变的事项：**

```
§7 RBAC ／ Data Scope ／ Tool Permission ／ Secret Handling = DESIGN PENDING（未改变）
Failure ／ Quarantine Interface physical shape ／ schema ／ storage ／ API ／ runtime = 未设计 ／ 未 operationally available（未改变）
mapping rule representation carrier ／ mapping_basis concrete syntax ／ drift detection mechanism ／
  Package Assembly runtime shape ／ auth ／ credential ／ secret-delivery mechanism ／
  framework ／ database ／ API ／ deployment ／ ADR = ARCHITECTURE ／ IMPLEMENTATION DEFERRALS（保持）
blanket runtime implementation authorization = NOT GRANTED（未改变）
POC Design v0.2 = DRAFT（未改变）
```

**F. 执行状态（本 Closure 时点）**

```
Decision 1 ～ 8                    = REGISTERED
A-1 ～ A-14                        = PASS（per-criterion evidence 见 B 节）
A-13 composition check             = PASS（§3 ／ §4.3 ／ §4.4 ／ §4.5 四向核验；见 C 节）
A-15 ／ A-16                      = PASS（NON-BLOCKING；见 D 节）
Adapter Boundary                   = DESIGN RESOLVED ← 由本 Closure Validation 登记（conceptual closure）
POC Design v0.2                    = DRAFT
§7 Permission & Security overall   = DESIGN PENDING（未改变）
Next gate                          = Adapter Boundary implementation ／ Architecture ／ §7 ／ §8 等**独立授权**（未由本 closure 授权）
```

**Historical-record preservation（本 Closure 的写入边界）：**

- `Decision 1` ～ `Decision 8` 的 **registration-time execution-state 记录**（各 HD Record 的「执行状态（本 Registration 时点）」块、
  `§4.6.13` ～ `§4.6.20` Registration Synchronization、`§4.6.12` Review Revision Log）**保留未改**；
- `§4.6.1` Design Review Authority block（`Review Object = Adapter Boundary（§4 最后一个 DESIGN PENDING 子领域）`）为**Review 时点**记录，**保留未改**；
- 本 Closure **只**更新 live current-state 状态标记、新增本节、并同步 `docs/project-index.md`（navigation ／ status only）；
- **未**对历史 `Adapter Boundary = DESIGN PENDING` 做全局替换。

---

#### 4.6.22 Current Status（Closure 时点 —— Issue #90）

```
Snapshot / Import Contract overall = DESIGN RESOLVED
  Package Envelope ／ Atomicity Boundary ／ Immutability Boundary ／ Analysis Run Linkage = DESIGN RESOLVED
  Serialization Format             = DESIGN RESOLVED
  Physical Dataset Layout          = DESIGN RESOLVED
  Field Carrier Mapping            = DESIGN RESOLVED
  Final Import Contract            = DESIGN RESOLVED
Adapter Boundary                   = DESIGN RESOLVED  ← Issue #90 Closure Validation = PASS
                                     （conceptual closure；implementation ／ Architecture ／ §7 ／ §8 未授权）
POC Design v0.2                    = DRAFT

Package Structural Failure
  ≠ Capability Evidence Unavailable
  ≠ Business DATA_INCOMPLETE
```

**以下三句为 `§4.6.1` Adapter Boundary Design Review 时点的事实（保留）；其后的状态推进由
Issue #90 Closure Validation 登记（见 `§4.6.21`）。**

**本 Review 不选择任何 Option。**
**本 Review 未创建任何 runtime artifact。**
**本 Review 未推进任何状态。**

---

<!-- END MIGRATED LEGACY §4.6 BODY -->
