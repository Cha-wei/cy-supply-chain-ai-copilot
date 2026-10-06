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
// Presentation-only record. Override is an approval with a truthful flag, not a canonical enum.
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
export type State = Readonly<{
  dialog: DialogName | null;
  evidenceViewed: boolean;
  explanationViewed: boolean;
  draftViewed: boolean;
  decision: PresentationDecision | null;
}>;
export const initialState: State = Object.freeze({
  dialog: null,
  evidenceViewed: false,
  explanationViewed: false,
  draftViewed: false,
  decision: null,
});
type Event =
  | { type: "OPEN"; dialog: DialogName }
  | { type: "CLOSE" }
  | { type: "APPROVE" }
  | { type: "OVERRIDE"; quantity: string; reason: string }
  | { type: "REJECT"; reason: string }
  | { type: "RESET" };
const source = {
  actor: "Human" as const,
  sourceRecommendation: scenario.recommended,
};
export function reducer(state: State, event: Event): State {
  switch (event.type) {
    case "RESET":
      return initialState;
    case "CLOSE":
      return { ...state, dialog: null };
    case "OPEN":
      if (event.dialog === "draft" && state.decision?.kind !== "approve")
        return state;
      if (
        ["review", "override", "reject"].includes(event.dialog) &&
        state.decision
      )
        return state;
      return {
        ...state,
        dialog: event.dialog,
        evidenceViewed: state.evidenceViewed || event.dialog === "evidence",
        explanationViewed:
          state.explanationViewed || event.dialog === "explanation",
        draftViewed: state.draftViewed || event.dialog === "draft",
      };
    case "APPROVE":
      if (state.dialog !== "review" || state.decision) return state;
      return {
        ...state,
        dialog: null,
        decision: Object.freeze({
          ...source,
          kind: "approve",
          approvedQuantity: scenario.recommended,
          override: false,
        }),
      };
    case "OVERRIDE":
      if (
        state.dialog !== "override" ||
        state.decision ||
        Object.keys(validateOverride(event.quantity, event.reason)).length
      )
        return state;
      return {
        ...state,
        dialog: null,
        decision: Object.freeze({
          ...source,
          kind: "approve",
          approvedQuantity: event.quantity,
          override: true,
          reason: event.reason,
        }),
      };
    case "REJECT":
      if (
        state.dialog !== "reject" ||
        state.decision ||
        reasonError(event.reason)
      )
        return state;
      return {
        ...state,
        dialog: null,
        decision: Object.freeze({
          ...source,
          kind: "reject",
          reason: event.reason,
        }),
      };
  }
}
export function demoStep(state: State) {
  if (state.decision?.kind === "reject") return "REJECTED";
  if (state.decision?.kind === "approve")
    return state.draftViewed
      ? "DRAFT_READY"
      : state.decision.override
        ? "OVERRIDDEN"
        : "APPROVED";
  if (state.dialog && ["review", "override", "reject"].includes(state.dialog))
    return "REVIEW_OPEN";
  if (state.explanationViewed) return "EXPLANATION_VIEWED";
  if (state.evidenceViewed) return "EVIDENCE_VIEWED";
  return "RECOMMENDATION_READY";
}
