# cy-supply-chain-ai-copilot

供应链 AI Copilot 项目（Yunnan CY Group Supply Chain AI Copilot）。

## 项目状态

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

**明确未实现（Out of Scope）**：Web / API / service、LLM / Agent / Tool protocol、HITL、
RBAC / secrets、persistent Audit、database / persistent business state、real ERP / SRM
Adapter / source connectivity、production write-back、P1，以及 `§6` ～ `§9` 各项
just-in-time gate。

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
│   ├── issues.py / report.py / cli.py
│   └── __init__.py               # public runtime surface
├── tests/                        # deterministic SIMULATED unittest suite
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

只使用 Python 标准库，无第三方运行时依赖，无 network / database / LLM。

```bash
# 单元测试（deterministic SIMULATED fixtures）—— 在 repository root 运行
python -m unittest discover -s tests -v

# 单个测试模块
python -m unittest tests.test_layer1_acceptance -v
```

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
  跨进程或服务级集成）、lint、AI Eval。

`§6` ～ `§9` 的 Required Gates 仍按各自 status boundary 处理。

当前验证证据：

- **local**：`964 tests / 2 skipped / 0 failed`（本文上方命令，SIMULATED fixtures，本机
  Python 3.14）；
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
