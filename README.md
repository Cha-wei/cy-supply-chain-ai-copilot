# cy-supply-chain-ai-copilot

供应链 AI Copilot 项目（Yunnan CY Group Supply Chain AI Copilot）。

## 项目状态

**Project Foundation + 第一批 deterministic implementation tranche 的第 1 个模块。**

```
POC Design v0.2                 = DRAFT
Code Start Gate                 = PASS（POC Design §10.1 E，CSG-1 ～ CSG-8）
Architecture Option A           = HUMAN APPROVED / ADR-001 ACCEPTED
First deterministic tranche     = IMPLEMENTATION AUTHORIZED（仅 POC Design §10.1 B）
Unrestricted implementation     = NOT AUTHORIZED
POC success                     = NOT CLAIMED
```

`Snapshot loader → Validation → Canonical data objects → Deterministic business rules
→ Procurement recommendation result` 五个模块中，**只有 Snapshot loader / import** 已实现：

```
Snapshot loader / import  = IMPLEMENTED（Layer-1 package acceptance only）
Validation                = NOT STARTED
Canonical data objects    = NOT STARTED
Deterministic rules       = NOT STARTED
Recommendation result     = NOT STARTED
```

**已实现范围（有意保持最小）** —— POC v0.2 **Layer-1 Package Structural Validation**：

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

**明确未实现（Out of Scope）**：`§4.4` Layer 2 ～ Layer 4 validation、canonical business
object construction、`§2` business rules、procurement recommendation、Web / API、
database / persistent business state、real ERP / source connectivity、LLM / Agent / Tool
protocol、HITL、RBAC / secrets、persistent Audit、production write-back、P1。

**状态纪律**：`DESIGN RESOLVED` ≠ `IMPLEMENTED` ≠ `TESTED`；`IMPLEMENTED` ≠ `VALIDATED`
≠ `POC SUCCESS`。本模块的验证仅覆盖 **SIMULATED** fixtures，不构成真实企业集成证据。

## 目录结构

```
.
├── README.md                     # 项目说明
├── AGENTS.md                     # AI 协作约定
├── CONTRIBUTING.md               # 工程协作规范
├── pyproject.toml                # Python package metadata（无第三方运行时依赖）
├── .github/workflows/ci.yml      # Foundation checks + Layer-1 loader tests
├── snapshot_loader/              # Controlled Snapshot loader（本 tranche 唯一实现）
│   ├── constants.py              # 已登记的 exact literals（不 runtime 推导）
│   ├── strict_json.py            # strict JSON parse（C-1 / C-9）
│   ├── path_scope.py             # strict literal path semantics（PN-1）
│   ├── trust.py                  # trusted boundary / stable view / trusted reuse
│   ├── loader.py                 # Layer-1 acceptance gate（§4.3.28 D4）
│   ├── issues.py                 # 继承的 Validation Taxonomy dimensions
│   ├── report.py                 # disposition / issue 报告模型
│   └── cli.py                    # thin CLI（outer entry point）
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
