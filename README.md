# Supply Chain AI Copilot

**AI-assisted procurement decision support system for manufacturing supply chains.**

An independently designed and implemented **SIMULATED Supply Chain AI Copilot Portfolio POC**. It connects deterministic supply-chain calculation, AI explanation, and a Human-in-the-loop decision workflow: calculate the facts, explain the evidence, and let a person decide.

![Procurement workspace showing one SIMULATED recommendation from the local Python runtime](portfolio-ui/review/runtime-integration/workspace-desktop.png)

[Run the local demo](portfolio-ui/README.md#启动) · [Explore the demo](#demo-showcase) · [Local verification](#运行与测试) · [Architecture and evidence](#documentation)

**Business value = NOT PROVEN · POC SUCCESS = NOT CLAIMED · Production readiness = NOT CLAIMED.** This is a portfolio case study, with no real customer validation or deployment claim.

## Business Problem

Manufacturing procurement decisions bring together production demand, BOM structure, available inventory, incoming supplies, loss rates, substitute materials, and procurement policies such as minimum order quantities (MOQ).

A procurement reviewer needs to understand:

- Which materials will become shortages, and when?
- How much should be purchased?
- Why is this action recommended, and what evidence supports it?

The challenge is more than producing a number: the recommendation must be explainable and reviewable. These are the business questions behind the design; the connected demo illustrates one fixed simulated material scenario, not a live factory planning system.

## Solution Overview

**Deterministic Computation + AI Explanation + Human Decision**

```text
SIMULATED snapshot → Validation → Canonical data model
                                      ↓
                           Deterministic calculation
                                      ↓
                         Recommendation + evidence
                                      ↓
                       Optional validated Q3 explanation
                                      ↓
                                Human Review
                                      ↓
                         Approve / Override / Reject
                                      ↓
                         Decision-bound Draft if approved
```

**Deterministic core.** Python owns requirement calculation, shortage analysis, procurement recommendations, and validation. AI does not calculate business facts. Keeping rules and exact quantities in this core makes results testable and keeps calculation independent of AI availability.

**AI explanation layer.** The implemented Q3 slice explains procurement quantities using validated results and evidence. It cannot modify facts, decide purchase quantities, or execute actions. This is a bounded explanation capability, not autonomous tool selection or validation of every planned business question. The connected demo defaults to **AI explanation unavailable** and makes no hosted AI calls; deterministic review remains usable.

**Human decision workflow.** A reviewer can approve the recommendation, override the quantity with a reason, or reject it. Overrides retain the original recommendation and must satisfy the existing quantity/MOQ validation. The runtime creates an internal initial Draft when review opens; approval binds the actual Human decision to it. Rejection produces no approved Draft. A new `AnalysisRun` makes old reviews and Drafts stale, requiring fresh review without inheriting old decisions.

React displays results and submits explicit user intent through a minimal localhost boundary. Python owns business facts and decision state. Drafts stay in server memory; Human approval does not execute procurement.

## Demo Showcase

[Local launch instructions](portfolio-ui/README.md#启动) provide the build and startup steps. The demo uses fixed **SIMULATED** inputs and runs on localhost.

| Step | What to explore |
| --- | --- |
| **1. Workspace** | Identify the simulated shortage and open its procurement recommendation. |
| **2. Detail View** | Inspect the calculation evidence: a shortage of 30 and MOQ of 100 produce a recommendation of 100, with an MOQ adjustment of 70. |
| **3. AI Explanation** | See the explicit unavailable state. The Q3 explanation boundary is implemented separately; this demo does not present generated hosted AI evidence. |
| **4. Human Review** | Approve 100 as recommended, enter an override with a reason, or reject. Invalid inputs leave the review undecided and allow correction. |
| **5. Decision Lifecycle** | View the approved Draft, then choose “模拟新分析运行” to make the old review/Draft stale and start a fresh review. The same fixed inputs are recalculated; this is not an input-data update. |

**Detail view — understand the recommendation and its evidence**

![Connected detail view showing shortage 30, MOQ adjustment 70, recommendation 100, AI unavailable, and Human review actions](portfolio-ui/review/runtime-integration/detail-desktop.png)

**Human review — enter an explicit quantity override and reason**

![Connected Human review dialog for modifying the procurement quantity](portfolio-ui/review/runtime-integration/dialog-desktop.png)

These screenshots come from the connected local runtime. [Desktop, laptop, and mobile captures](portfolio-ui/review/runtime-integration/validation.md#screenshots) document the same limited demo surface.

## Technical Implementation

| Area | Implementation |
| --- | --- |
| **Backend — Python** | Snapshot loading, validation, canonical data objects, deterministic rules, and Human decision/Draft runtime. A thin standard-library localhost server connects the demo to the existing runtime. |
| **Frontend — React + TypeScript** | Procurement workspace, detail view, evidence display, review dialogs, and Draft lifecycle presentation. Business validation and state remain in Python. |
| **Validation** | Python automated tests cover deterministic rules and runtime boundaries. Playwright exercises the connected review flow and responsive views. CI verifies the Python suite; a separate path-filtered UI workflow builds and checks connected interactions. |

The [recorded connected-runtime validation](portfolio-ui/review/runtime-integration/validation.md) includes offline Q3 stub checks, session/stale/replay cases, exact quantity transport, and failure boundaries. Technical checks do not establish AI model quality or business results.

<a id="运行与测试"></a>

For local verification, run `python -m unittest discover -s tests -q` at the repository root. Frontend build and Playwright commands are in the [demo guide](portfolio-ui/README.md#验证). Hosted observations require separate explicit authorization and are not part of the default demo or CI.

## My Role

**Independent Project Owner**

- **Business/System Design:** supply-chain workflow analysis, AI boundary design, and Human-in-the-loop review design.
- **Engineering:** deterministic runtime, canonical model, React integration, and testing strategy.
- **Engineering Process:** Issue/PR workflow, review process, and CI validation.

**AI-assisted Development:** AI coding agents were used as implementation assistants. Architecture decisions, task decomposition, review, and final acceptance remained human-owned.

## Scope & Limitations

**Implemented:** shortage analysis, procurement recommendations, the scoped Q3 AI explanation boundary, Human review with quantity override, ephemeral Draft lifecycle, and local React/Python runtime integration.

**Not included:** real customer validation; ERP/WMS/MES integration; database persistence; authentication/RBAC; production execution or purchase-order creation; business KPI measurement. The demo shares one Python memory session across tabs, and service restart loses decisions and Drafts. Rule/code-version freshness and overall AI Eval remain unresolved.

**Evidence boundary:** [historical technical closure](docs/design/poc-design-v0.2.md#portfolio-technical-closure) applies to accepted revision `00272580adab8cb8d5843a719d261e34047b877d`. The connected demo is a separately accepted technical extension at `2b5fe6205ebd22c062fc5c6ff10a2908f3689e26`. [The current scope record](docs/design/poc-design-v0.2.md#historical-closure-connected-extension) does not claim full current-main Portfolio Technical Closure or equivalence between those revisions. Real-world validation remains deferred.

**Business value = NOT PROVEN. POC SUCCESS = NOT CLAIMED.** No production readiness or customer validation is claimed.

This project demonstrates enterprise AI application engineering practices, not production deployment readiness.

## Documentation

| Material | Read more |
| --- | --- |
| **Architecture / ADRs** | [Deterministic core — ADR-001](docs/architecture/adr-001-deterministic-core.md), [Q3 explanation — ADR-002](docs/architecture/adr-002-p0-ai-explanation-minimum-runtime.md), [Local runtime integration — ADR-003](docs/architecture/adr-003-portfolio-demo-local-runtime-integration.md) |
| **Design documents** | [POC design](docs/design/poc-design-v0.2.md), [Canonical data model](docs/design/specs/data-integration/canonical-data-model.md), [Frozen business baseline](docs/discovery/discovery-brief-v0.1.1.md) |
| **Evidence** | [Historical accepted technical evidence](docs/design/poc-design-v0.2.md#accepted-revision-layer2-consolidation), [Historical Q3 hosted observations](docs/design/poc-design-v0.2.md#q3-hosted-refresh-evidence), [Connected demo validation](portfolio-ui/review/runtime-integration/validation.md) |
| **Navigation / local demo** | [Project Index](docs/project-index.md), [Demo launch and verification](portfolio-ui/README.md) |

Canonical documents retain the detailed decisions, evidence limitations, and engineering history; this README is the portfolio presentation layer.
