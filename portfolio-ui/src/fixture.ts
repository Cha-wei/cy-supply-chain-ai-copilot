// Presentation-layer fixture only. No Python runtime, AI provider or business calculation.
// Source: tests/test_hitl_review.py::_FIXTURE_FACT_TEXT at baseline 96b19ea.
export const scenario = Object.freeze({
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
