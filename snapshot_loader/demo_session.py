"""Ephemeral transport orchestration, not a second business implementation."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
from uuid import uuid4
import json
import re

from .demo_composition import analyze, PLANT_ID, MATERIAL_CODE
from .deepseek_provider import UnavailableProvider
from .explanation_q3 import explain_q3
from .hitl_review import open_review, ReviewError
from .draft_runtime import open_draft

ACTOR = "SIMULATED-PORTFOLIO-REVIEWER"
MAX_INTENTS = 1024  # fail closed when full; never evict then execute an old id anew
FIELDS = {
    "initialize": set(), "new_analysis": set(), "explain": set(), "open_review": set(),
    "approve": set(), "override": {"quantity", "reason"}, "reject": {"reason"},
}


class DemoError(Exception):
    def __init__(self, code, status=409):
        self.code, self.status = code, status
        super().__init__(code)


def exact(value: Fraction | None):
    if value is None:
        return None
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def display(value: Fraction | None):
    """Lossless display only; never a rounding or business precision policy."""
    if value is None:
        return ""
    if value.denominator == 1:
        return str(value.numerator)
    # A rational remains a rational on screen. No repeating-decimal approximation.
    return f"{value.numerator}/{value.denominator}"


class DemoSession:
    def __init__(self, *, provider=None):
        # Production entry never resolves environment credentials. Injection is a Python test seam.
        self.provider = provider if provider is not None else UnavailableProvider()
        self.lock = RLock()
        self.temp = TemporaryDirectory(prefix="cy-simulated-input-")
        self.session = uuid4().hex
        self.run_ref = None
        self.review_ref = None
        self.review_count = 0  # ephemeral presentation metadata, not a canonical identifier
        self.result = self.review = self.draft = self.explanation = None
        self.intents = {}
        self.closed = False

    def close(self):
        with self.lock:
            self.closed = True
            self.result = self.review = self.draft = self.explanation = None
            self.intents.clear()
            self.temp.cleanup()

    @property
    def run(self):
        return self.result.procurement_recommendation.analysis_run

    def execute(self, request):
        if not isinstance(request, dict):
            raise DemoError("invalid_request", 400)
        op = request.get("op")
        if not isinstance(op, str) or op not in FIELDS:
            raise DemoError("invalid_request", 400)
        common = {"op", "intent", "session"} if op == "initialize" else {"op", "intent", "session", "run", "review"}
        if set(request) != common | FIELDS[op]:
            raise DemoError("invalid_request", 400)
        if any(not isinstance(request[k], str) for k in FIELDS[op]):
            raise DemoError("invalid_request", 400)
        intent = request["intent"]
        if not isinstance(intent, str) or not re.fullmatch(r"[a-zA-Z0-9-]{8,80}", intent):
            raise DemoError("invalid_request", 400)
        fingerprint = json.dumps(request, sort_keys=True, ensure_ascii=True)
        with self.lock:
            if self.closed:
                raise DemoError("session_lost")
            if request["session"] != self.session:
                raise DemoError("session_lost")
            if intent in self.intents:
                prior, error = self.intents[intent]
                if prior != fingerprint:
                    raise DemoError("intent_conflict")
                if error:
                    raise DemoError(error)
                # Return CURRENT authoritative state, never resurrect a cached old Draft.
                return self.snapshot()
            if len(self.intents) >= MAX_INTENTS:
                raise DemoError("session_capacity")
            if op != "initialize" and (
                self.result is None or request["run"] != self.run_ref or request["review"] != self.review_ref
            ):
                raise DemoError("binding_conflict")
            # Reserve even failed commands. No uncertain partial mutation can be executed twice.
            self.intents[intent] = (fingerprint, "operation_failed")
            try:
                self._apply(op, request)
            except DemoError as error:
                self.intents[intent] = (fingerprint, error.code)
                raise
            except ReviewError:
                self.intents[intent] = (fingerprint, "decision_invalid")
                raise DemoError("decision_invalid", 422) from None
            except Exception:
                raise DemoError("operation_failed", 503) from None
            self.intents[intent] = (fingerprint, None)
            return self.snapshot()

    def _apply(self, op, request):
        if op in {"initialize", "new_analysis"}:
            if op == "initialize" and self.result is not None:
                return
            new_ref = uuid4().hex
            result = analyze(Path(self.temp.name), "SIMULATED-" + new_ref)
            self.result, self.run_ref = result, new_ref
            self.explanation = None
            if self.review:
                self.review.is_stale(self.run)
                self.draft.is_stale(self.run)
            return
        if op == "explain":
            if self.review and not self.review.is_stale(self.run):
                raise DemoError("review_evidence_fixed")
            result = explain_q3(self.result.procurement_recommendation, self.provider,
                                plant_id=PLANT_ID, material_code=MATERIAL_CODE)
            if result.analysis_run != self.run:
                raise DemoError("binding_conflict")
            self.explanation = result
            return
        if op == "open_review":
            if self.review and not self.review.is_stale(self.run):
                return  # another tab already opened this immutable Review
            self.review = open_review(self.result.procurement_recommendation,
                                      plant_id=PLANT_ID, material_code=MATERIAL_CODE,
                                      actor_reference=ACTOR, supplier_risk=self.result.supplier_risk,
                                      explanation=self.explanation)
            self.draft = open_draft(self.review)
            self.review_ref = uuid4().hex
            self.review_count += 1
            return
        if self.review is None or self.review.is_stale(self.run):
            raise DemoError("review_unavailable")
        if self.review.decision is not None:
            raise DemoError("decision_conflict")
        args = dict(current_analysis_run=self.run, actor_reference=ACTOR)
        if op == "reject":
            decision = self.review.reject(**args, reason=request["reason"])
        else:
            args.update(plant_id=self.review.grain[0], material_code=self.review.grain[1],
                        recommendation_need_date=self.review.grain[2])
            if op == "approve":
                decision = self.review.approve_as_recommended(**args)
            else:
                decision = self.review.approve_with_override(**args, override_quantity=request["quantity"],
                                                            reason=request["reason"])
        self.draft = self.draft.with_decision(decision, self.run)

    def snapshot(self):
        with self.lock:
            if self.closed:
                raise DemoError("session_lost")
            if self.result is None:
                return {"initialized": False, "session": self.session}
            recommendation = self.result.procurement_recommendation.for_family(PLANT_ID, MATERIAL_CODE)
            raw = recommendation.to_dict()
            values = (recommendation.shortage_qty, recommendation.base_purchase_need,
                      recommendation.moq_adjustment_qty, recommendation.recommended_purchase_qty)
            names = ("shortage", "base", "adjustment", "recommended")
            facts = {name: display(value) for name, value in zip(names, values)}
            quantities = {name: exact(value) for name, value in zip(names, values)}
            facts.update(moq=raw["ApplicableMOQ"], material_code=recommendation.material_code,
                         plant_id=recommendation.plant_id)
            stale = bool(self.review and self.review.is_stale(self.run))
            decision = self.review.decision if self.review else None
            decision_view = None if decision is None else {
                "kind": decision.decision_kind, "override": decision.override_flag,
                "approvedQuantity": display(decision.approved_value), "approvedExact": exact(decision.approved_value),
                "sourceRecommendation": display(decision.deterministic_recommended_value),
                "reason": decision.human_reason,
            }
            approved = bool(self.draft and self.draft.has_approved_draft(self.run))
            explanation = self.explanation
            response = getattr(explanation, "response", None)
            # Current-analysis explanation is independent of the retained old Review's staleness.
            has_explanation = bool(explanation and explanation.analysis_run == self.run and response)
            return {
                "initialized": True, "session": self.session, "run": self.run_ref,
                "binding": {"analysis_run_id": self.run.analysis_run_id, "analysis_date": self.run.analysis_date,
                            "snapshot_package_identity": self.run.snapshot_package_identity,
                            "accepted_content_view_digest": self.run.accepted_content_view_digest},
                "facts": facts, "quantities": quantities,
                "review": {"id": self.review_ref, "stale": stale, "decision": decision_view},
                "reReview": self.review_count > 1,
                "canDraft": approved, "canDecide": bool(self.review and self.draft.is_actionable(self.run)),
                "draft": None if not self.draft else {"state": self.draft.draft_state(self.run),
                         "quantity": exact(self.draft.quantity), "quantityText": display(self.draft.quantity)},
                "hasExplanation": has_explanation,
                "explanation": response.answer if has_explanation else None,
                "explanationOutcome": explanation.outcome if explanation else "NOT_REQUESTED",
                "pendingCount": 1 if stale or decision is None else 0,
            }
