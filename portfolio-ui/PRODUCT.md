# Product — Portfolio Demo UI exploration

<!-- impeccable:product-schema 1 -->

此文件仅为本次 UI 设计工具的上下文，不是业务 canonical source；事实权威继续为仓库既有设计与 frozen baseline。

## Platform
web

## Users
用户已明确：用于求职 Portfolio、面试 PPT、屏幕分享与录屏；读者为审阅作品的面试者。真实客户验证未执行。

## Product Purpose
通过中文优先的视觉体验，展示确定性采购建议、AI 解释与人工决策的边界；本轮仅三个高保真概念，等待 Human selection。

## Positioning
同一 SIMULATED MOQ-raised 场景：缺口30、基础采购需求30、MOQ100、MOQ调整70、建议采购100。30 + 70 = 100 是 visual mechanism；AI不参与数量计算。

## Operating Context
1280×800、1440桌面；3–5分钟作品展示。当前v0.1为technical prototype，其视觉被用户否决，不是新视觉authority。

## Capabilities and Constraints
保留 React / TypeScript / Vite、fixture、主流程与Playwright。v0.2仅视觉预览，无完整业务交互。不得改变规则、ERP、PO、生产执行、供应商选择或接runtime。不实现override/stale。

## Brand Commitments
中文一级产品信息；Apple-inspired、premium、calm、precise、spatial、minimal、information-first。用户指定三个方向：A Decision Canvas、B Spatial Supply Chain、C Executive Decision Workspace。不得用默认cards/sidebar/dashboard。Tailwind与shadcn interaction primitives必须使用；Impeccable critique与audit必须执行。

## Evidence on Hand
src/fixture.ts 沿用；tests/test_hitl_review.py::_FIXTURE_FACT_TEXT 为来源。真实业务验证、价值、production readiness、POC SUCCESS均未宣称。

## Product Principles
确定性系统计算，AI解释，人工决策。UI follows the project。UI prototype ≠ runtime evidence。Human approval ≠ production execution。
