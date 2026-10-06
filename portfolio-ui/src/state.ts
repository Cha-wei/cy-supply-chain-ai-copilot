import { scenario } from "./fixture";
import { reasonError, validateOverride } from "./decision-input";

export type DialogName =
  | "evidence"
  | "explanation"
  | "review"
  | "override"
  | "reject"
  | "draft"
  | "boundary";
type Source = Readonly<{ actor: "Human"; sourceRecommendation: string }>;
export type PresentationDecision = Source &
  (
    | Readonly<{ kind: "approve"; approvedQuantity: string; override: false }>
    | Readonly<{
        kind: "approve";
        approvedQuantity: string;
        override: true;
        reason: string;
      }>
    | Readonly<{ kind: "reject"; reason: string }>
  );
// Demo sentinels only: not real AnalysisRun generation, detection or runtime metadata.
export const bindingComponents = [
  "analysis_run_id",
  "snapshot_package_identity",
  "accepted_content_view_digest",
  "analysis_date",
] as const;
export type DemoBinding = Readonly<
  Record<(typeof bindingComponents)[number], string>
>;
export const preparedBinding: DemoBinding = Object.freeze({
  analysis_run_id: "SIMULATED-RUN-1",
  snapshot_package_identity: "SIMULATED-PACKAGE",
  accepted_content_view_digest: "SIMULATED-CONTENT-1",
  analysis_date: "SIMULATED-DATE",
});
export function sameBinding(a: DemoBinding, b: DemoBinding) {
  return bindingComponents.every((key) => a[key] === b[key]);
}
export type PresentationReview = Readonly<{
  id: number;
  binding: DemoBinding;
  stale: boolean;
  decision: PresentationDecision | null;
  draftViewed: boolean;
}>;
function createReview(id: number, binding: DemoBinding): PresentationReview {
  return Object.freeze({
    id,
    binding: Object.freeze({ ...binding }),
    stale: false,
    decision: null,
    draftViewed: false,
  });
}
export type State = Readonly<{
  dialog: DialogName | null;
  evidenceViewed: boolean;
  explanationViewed: boolean;
  review: PresentationReview;
  // Only the immediately replaced snapshot; no history UI, persistence or audit log.
  previousReview: PresentationReview | null;
  currentBinding: DemoBinding;
  explanationRetired: boolean;
  simulationSequence: number;
}>;
export const initialState: State = Object.freeze({
  dialog: null,
  evidenceViewed: false,
  explanationViewed: false,
  review: createReview(1, preparedBinding),
  previousReview: null,
  currentBinding: preparedBinding,
  explanationRetired: false,
  simulationSequence: 1,
});
export type Event =
  | { type: "OPEN"; dialog: DialogName }
  | { type: "CLOSE" }
  | { type: "APPROVE"; reviewId: number }
  | { type: "OVERRIDE"; reviewId: number; quantity: string; reason: string }
  | { type: "REJECT"; reviewId: number; reason: string }
  | { type: "SIMULATE_RUN"; binding: DemoBinding }
  | { type: "REREVIEW" }
  | { type: "RESET" };
export function nextDemoBinding(state: State): DemoBinding {
  return Object.freeze({
    ...state.currentBinding,
    analysis_run_id: `SIMULATED-RUN-${state.simulationSequence + 1}`,
    accepted_content_view_digest: `SIMULATED-CONTENT-${state.simulationSequence + 1}`,
  });
}
export function isStale(state: State) {
  return (
    state.review.stale ||
    !sameBinding(state.review.binding, state.currentBinding)
  );
}
export function explanationAvailable(state: State) {
  return (
    !isStale(state) &&
    !state.explanationRetired &&
    sameBinding(preparedBinding, state.currentBinding)
  );
}
export function draftAvailable(state: State) {
  return !isStale(state) && state.review.decision?.kind === "approve";
}
const source = {
  actor: "Human" as const,
  sourceRecommendation: scenario.recommended,
};
function record(state: State, decision: PresentationDecision): State {
  return {
    ...state,
    dialog: null,
    review: Object.freeze({
      ...state.review,
      decision: Object.freeze(decision),
    }),
  };
}
export function reducer(state: State, event: Event): State {
  const review = state.review;
  if ("reviewId" in event && (event.reviewId !== review.id || isStale(state)))
    return state;
  switch (event.type) {
    // Reset restarts the whole disposable demo; it never mutates the old review object.
    case "RESET":
      return initialState;
    case "CLOSE":
      return { ...state, dialog: null };
    case "SIMULATE_RUN": {
      const binding = Object.freeze({ ...event.binding });
      const stale = review.stale || !sameBinding(review.binding, binding);
      return {
        ...state,
        currentBinding: binding,
        simulationSequence: state.simulationSequence + 1,
        dialog: null,
        explanationRetired: state.explanationRetired || stale,
        review:
          stale && !review.stale
            ? Object.freeze({ ...review, stale: true })
            : review,
      };
    }
    case "REREVIEW":
      if (!isStale(state)) return state;
      return {
        ...state,
        dialog: null,
        evidenceViewed: false,
        explanationViewed: false,
        previousReview: review,
        review: createReview(review.id + 1, state.currentBinding),
      };
    case "OPEN":
      if (event.dialog === "draft" && !draftAvailable(state)) return state;
      if (event.dialog === "explanation" && !explanationAvailable(state))
        return state;
      if (
        ["review", "override", "reject"].includes(event.dialog) &&
        (review.decision || isStale(state))
      )
        return state;
      return {
        ...state,
        dialog: event.dialog,
        evidenceViewed: state.evidenceViewed || event.dialog === "evidence",
        explanationViewed:
          state.explanationViewed || event.dialog === "explanation",
        review:
          event.dialog === "draft"
            ? Object.freeze({ ...review, draftViewed: true })
            : review,
      };
    case "APPROVE":
      if (state.dialog !== "review" || review.decision) return state;
      return record(state, {
        ...source,
        kind: "approve",
        approvedQuantity: scenario.recommended,
        override: false,
      });
    case "OVERRIDE":
      if (
        state.dialog !== "override" ||
        review.decision ||
        Object.keys(validateOverride(event.quantity, event.reason)).length
      )
        return state;
      return record(state, {
        ...source,
        kind: "approve",
        approvedQuantity: event.quantity,
        override: true,
        reason: event.reason,
      });
    case "REJECT":
      if (
        state.dialog !== "reject" ||
        review.decision ||
        reasonError(event.reason)
      )
        return state;
      return record(state, { ...source, kind: "reject", reason: event.reason });
  }
}
export function demoStep(state: State) {
  if (isStale(state)) return "STALE";
  const { decision, draftViewed } = state.review;
  if (decision?.kind === "reject") return "REJECTED";
  if (decision?.kind === "approve")
    return draftViewed
      ? "DRAFT_READY"
      : decision.override
        ? "OVERRIDDEN"
        : "APPROVED";
  if (state.dialog && ["review", "override", "reject"].includes(state.dialog))
    return "REVIEW_OPEN";
  if (state.explanationViewed) return "EXPLANATION_VIEWED";
  if (state.evidenceViewed) return "EVIDENCE_VIEWED";
  return "RECOMMENDATION_READY";
}
