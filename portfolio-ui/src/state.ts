// Presentation state only. All business flags and decisions are Python projections.
export type DialogName = "evidence" | "explanation" | "review" | "override" | "reject" | "draft" | "boundary";
export type Exact = { numerator: string; denominator: string };
export type Decision = { kind: "approve" | "reject"; override: boolean; approvedQuantity: string; approvedExact: Exact | null; sourceRecommendation: string; reason: string | null };
export type Snapshot = {
  initialized: true; session: string; run: string;
  binding: Record<string, string>;
  facts: { material_code: string; plant_id: string; shortage: string; base: string; moq: string; adjustment: string; recommended: string };
  review: { id: string | null; stale: boolean; decision: Decision | null };
  reReview: boolean;
  canDraft: boolean; canDecide: boolean; hasExplanation: boolean; explanation: string | null;
  explanationOutcome: string; pendingCount: number;
  draft: { state: string; quantity: Exact | null; quantityText: string } | null;
};
export type State = Snapshot & { dialog: DialogName | null };
export const isStale = (state: State) => state.review.stale;
export const draftAvailable = (state: State) => state.canDraft;
export const explanationAvailable = (state: State) => state.hasExplanation;
export function demoStep(state: State) {
  if (state.review.stale) return "STALE";
  if (state.dialog === "draft") return "DRAFT_READY";
  if (state.review.decision?.kind === "reject") return "REJECTED";
  if (state.review.decision?.kind === "approve") return state.review.decision.override ? "OVERRIDDEN" : "APPROVED";
  return state.dialog === "review" ? "REVIEW_OPEN" : "RECOMMENDATION_READY";
}
