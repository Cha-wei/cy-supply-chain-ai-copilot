// Presentation-layer fixture only. No Python runtime, AI provider or business calculation.
// Source: tests/test_hitl_review.py::_FIXTURE_FACT_TEXT at baseline 96b19ea.
export const scenario = Object.freeze({
  explanation:
    "当前缺口和基础采购需求均为 30 件，最低起订量为 100 件。既有确定性结果记录 MOQ 调整为 70 件，建议采购 100 件。AI 只解释这些已登记事实，不计算采购数量。",
  shortage: "30",
  base: "30",
  moq: "100",
  adjustment: "70",
  recommended: "100",
  facts: [
    ["ShortageQty", "30"],
    ["BasePurchaseNeed", "30"],
    ["ApplicableMOQ", "100"],
    ["MOQAdjustmentQty", "70"],
    ["RecommendedPurchaseQty", "100"],
  ] as readonly (readonly [string, string])[],
});
