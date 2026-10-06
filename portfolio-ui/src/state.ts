import { scenario } from "./fixture";

export type DialogName =
  "evidence" | "explanation" | "review" | "draft" | "boundary";
// Presentation orchestration only: no canonical runtime record, identity or calculation.
export type PresentationDecision = Readonly<{
  kind: "approve";
  actor: "Human";
  approvedQuantity: string;
  sourceRecommendation: string;
  override: false;
}>;
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
  | { type: "RESET" };
export function reducer(state: State, event: Event): State {
  switch (event.type) {
    case "RESET":
      return initialState;
    case "CLOSE":
      return { ...state, dialog: null };
    case "OPEN":
      if (event.dialog === "draft" && !state.decision) return state;
      if (event.dialog === "review" && state.decision) return state;
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
          kind: "approve",
          actor: "Human",
          approvedQuantity: scenario.recommended,
          sourceRecommendation: scenario.recommended,
          override: false,
        }),
      };
  }
}
export function demoStep(state: State) {
  if (state.decision) return state.draftViewed ? "DRAFT_READY" : "APPROVED";
  if (state.dialog === "review") return "REVIEW_OPEN";
  if (state.explanationViewed) return "EXPLANATION_VIEWED";
  if (state.evidenceViewed) return "EVIDENCE_VIEWED";
  return "RECOMMENDATION_READY";
}
