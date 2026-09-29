"""DeepSeek hosted provider adapter for the P0 AI Explanation Q3 seam.

Registered authority:

* ``ADR-002`` (``ACCEPTED``) -- P0 AI Explanation minimum runtime: in-process, a single
  provider-agnostic call, provider-neutral seam, deterministic fail-closed path, and
  ``LLM does not create business truth``.  The provider ／ model are **replaceable
  implementation configuration**; this adapter is that configuration for the first hosted
  provider and introduces no canonical semantic and no new ADR.
* ``POC Design v0.2`` §5.20 (Q3 runtime implementation record) ／ §5.3 (Q3) ／ §5.5 -- §5.7.
* ``POC Design v0.2`` §7.1 (Secret Handling minimum contract, Issue #180): this module is the
  **provider integration ／ composition boundary** of ``S-3`` -- it is the only place that
  reads the provider credential, it reads it from the **process environment**, and the raw
  credential never becomes a business-side parameter of the explanation seam (``S-4``).

Boundary summary:

* the business payload sent to the provider is **exactly** the existing Q3 projection -- no
  recommendation object, no pipeline result, no snapshot package, no raw artifact, no
  credential (``§7.1`` ``S-1`` ／ ``S-2``, ``ADR-002`` egress boundary);
* the provider's answer is treated as a **selection** only; the existing
  :func:`snapshot_loader.explanation_seam.validate_provider_response` remains the final trust
  boundary and is never bypassed or re-implemented here;
* the HTTP transport is an injectable seam, so tests never touch the network, and CI never
  holds a real secret;
* one request produces one response: no tool calling, no web search, no MCP, no agent, no
  multi-turn or persistent conversation state.  The request asks for ``reasoning.effort =
  "none"`` because a closed selection needs no thinking budget; that is implementation
  configuration, not a canonical semantic.

Standard library only (``urllib.request``); no SDK and no new dependency.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from .explanation_seam import ANSWER_KIND_LITERALS, RESPONSE_KEYS
from .explanation_q3 import Q3_FACT_FIELDS

#: Implementation configuration (not canonical semantics): provider, model, endpoint.
DEEPSEEK_PROVIDER: str = "deepseek"
DEEPSEEK_MODEL: str = "deepseek-flash"
DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
DEEPSEEK_RESPONSES_PATH: str = "/responses"

#: The environment variable the composition boundary reads (implementation configuration).
DEEPSEEK_API_KEY_ENV: str = "DEEPSEEK_API_KEY"

#: Request defaults.
DEFAULT_TIMEOUT_SECONDS: float = 30.0
MAX_RESPONSE_BYTES: int = 1_000_000
SELECTION_SCHEMA_NAME: str = "q3_selection"

#: The provider-control instruction.  It carries **no** business fact: it only asks for a
#: schema-shaped selection over the supplied projection and forbids prose or new values.
INSTRUCTIONS: str = (
    "你在为一个已确定的采购建议做 selection，而不是生成新事实。"
    "只根据提供的 Q3 explanation projection JSON 选择：answer_kind 只能取自允许集合；"
    "evidence 只能列出 projection 中已存在的量名；uncertainty 必须为空数组；"
    "human_decision_required 必须为 true。"
    "不得生成新的业务事实、不得计算新的数值、不得输出任何解释性文字（prose），"
    "只返回符合给定 JSON Schema 的 JSON 对象。"
)


class ProviderUnavailable(RuntimeError):
    """The hosted provider could not supply a usable selection.

    The message is deliberately credential-free and detail-free: it never contains the
    credential, the request headers, the request URL with parameters or the provider's error
    body (``§7.1`` ``S-8``).  The explanation runtime maps this to
    ``OUTCOME_PROVIDER_UNAVAILABLE`` and surfaces only ``AI explanation unavailable``.
    """


@dataclass(frozen=True, slots=True)
class HttpRequest:
    """One HTTP request handed to a transport (frozen, so a stub can retain it safely).

    ``headers`` and ``body`` are excluded from ``repr`` deliberately: the request carries the
    credential in its ``Authorization`` header (``§7.1`` ``S-8``), so a diagnostic that prints
    the object must never be able to expose it.  The attributes remain fully accessible for
    the transport that has to send the request.
    """

    method: str
    url: str
    headers: tuple[tuple[str, str], ...] = field(repr=False)
    body: bytes = field(repr=False)
    timeout: float


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """One HTTP response: a status and a bounded body (HTTP errors are responses, not raises).

    ``body`` is excluded from ``repr`` for the same reason: a provider error body may echo
    request context, so diagnosis output must not surface it by accident.
    """

    status: int
    body: bytes = field(repr=False)


class HttpTransport(Protocol):
    """The injectable HTTP seam; the default implementation is standard-library only."""

    def send(self, request: HttpRequest) -> HttpResponse:  # pragma: no cover - protocol
        ...


class StdlibHttpTransport:
    """Minimal ``urllib.request`` transport: no SDK, no retry, no logging."""

    def send(self, request: HttpRequest) -> HttpResponse:
        http_request = urllib.request.Request(
            request.url,
            data=request.body,
            headers=dict(request.headers),
            method=request.method,
        )
        try:
            with urllib.request.urlopen(http_request, timeout=request.timeout) as response:
                return HttpResponse(
                    status=int(getattr(response, "status", 200)),
                    body=response.read(MAX_RESPONSE_BYTES),
                )
        except urllib.error.HTTPError as error:
            # An HTTP error status is still a provider answer: return it so the adapter can
            # fail closed on the status without echoing the provider's error body.
            try:
                body = error.read(MAX_RESPONSE_BYTES)
            except Exception:  # noqa: BLE001 - a body we cannot read is simply absent
                body = b""
            finally:
                error.close()
            return HttpResponse(status=int(error.code), body=body)
        except (urllib.error.URLError, OSError, ValueError):
            # Transport-level failure (DNS, TLS, timeout, refused connection): fail closed.
            raise ProviderUnavailable("the hosted provider could not be reached") from None


def selection_json_schema() -> dict[str, object]:
    """The JSON Schema for the provider's structured output.

    It mirrors the **existing** selection vocabulary -- it does not define a new contract:
    ``answer_kind`` is restricted to :data:`~snapshot_loader.explanation_seam.ANSWER_KIND_LITERALS`,
    ``evidence`` must list exactly the registered Q3 fact names, ``uncertainty`` must be empty
    and ``human_decision_required`` must be ``true``.  Only the fields the provider documents
    for a ``json_schema`` format are sent (``type`` ／ ``name`` ／ ``schema``); the schema is a
    provider hint and the authoritative validation stays with
    :func:`~snapshot_loader.explanation_seam.validate_provider_response`.
    """

    return {
        "type": "json_schema",
        "name": SELECTION_SCHEMA_NAME,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "answer_kind": {
                    "type": "string",
                    "enum": list(ANSWER_KIND_LITERALS),
                },
                "evidence": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(Q3_FACT_FIELDS)},
                    "minItems": len(Q3_FACT_FIELDS),
                    "maxItems": len(Q3_FACT_FIELDS),
                },
                "uncertainty": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 0,
                },
                "human_decision_required": {"type": "boolean", "enum": [True]},
            },
            "required": list(RESPONSE_KEYS),
        },
    }


def _extract_output_text(envelope: Mapping[str, object]) -> str | None:
    """The structured output text of the documented Responses shape, or ``None``.

    Only ``output[] -> message -> content[] -> output_text`` is parsed.  Items of any other
    type (for example a ``reasoning`` item preceding the message) contribute nothing, and
    there is deliberately **no** convenience-field fallback, so an undocumented envelope fails
    closed instead of being guessed at.
    """

    output = envelope.get("output")
    if not isinstance(output, Sequence) or isinstance(output, (str, bytes)):
        return None
    for item in output:
        if not isinstance(item, Mapping) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, Sequence) or isinstance(content, (str, bytes)):
            continue
        for part in content:
            if (
                isinstance(part, Mapping)
                and part.get("type") == "output_text"
                and isinstance(part.get("text"), str)
            ):
                return str(part["text"])
    return None


class DeepSeekProvider:
    """The DeepSeek adapter: one hosted request, one schema-shaped selection.

    The credential is passed in explicitly by the composition boundary (:func:`provider_from_environment`);
    the adapter itself never reads the environment, never logs and never includes the
    credential in the business payload.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEEPSEEK_MODEL,
        base_url: str = DEEPSEEK_BASE_URL,
        endpoint: str = DEEPSEEK_RESPONSES_PATH,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: HttpTransport | None = None,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("DeepSeekProvider requires a non-empty credential")
        self._api_key = api_key.strip()
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._endpoint = endpoint
        self._timeout = timeout
        self._transport: HttpTransport = transport or StdlibHttpTransport()

    # --- introspection (never exposes the credential) -------------------------------

    @property
    def model(self) -> str:
        return self._model

    @property
    def url(self) -> str:
        return f"{self._base_url}{self._endpoint}"

    def __repr__(self) -> str:  # pragma: no cover - trivial, asserted by test
        return (
            f"DeepSeekProvider(model={self._model!r}, url={self.url!r}, "
            f"transport={type(self._transport).__name__})"
        )

    # --- request boundary -----------------------------------------------------------

    def request_payload(self, projection: Mapping[str, object]) -> dict[str, object]:
        """The request body: provider-control fields plus the projection as the only data.

        Exposed so a caller (or a test) can audit exactly what would leave the process.
        """

        return {
            "model": self._model,
            "instructions": INSTRUCTIONS,
            "reasoning": {"effort": "none"},
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(projection, ensure_ascii=False, sort_keys=True),
                        }
                    ],
                }
            ],
            "text": {"format": selection_json_schema()},
        }

    def request_for(self, projection: Mapping[str, object]) -> HttpRequest:
        """The exact HTTP request the adapter would send (headers included)."""

        body = json.dumps(
            self.request_payload(projection), ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
        return HttpRequest(
            method="POST",
            url=self.url,
            headers=(
                ("Content-Type", "application/json"),
                ("Accept", "application/json"),
                ("Authorization", f"Bearer {self._api_key}"),
            ),
            body=body,
            timeout=self._timeout,
        )

    # --- the provider-agnostic seam --------------------------------------------------

    def explain(self, projection: Mapping[str, object]) -> object:
        """Send one request and return the provider's **selection** (never prose).

        Every failure -- transport, status, envelope shape, JSON syntax -- raises
        :class:`ProviderUnavailable`, so the explanation runtime fails closed without
        surfacing any provider detail.  No retry, no provider switching, no fallback answer.
        """

        response = self._transport.send(self.request_for(projection))
        if response.status in (401, 403):
            raise ProviderUnavailable(
                f"the hosted provider rejected the credential (status {response.status})"
            )
        if response.status == 429:
            raise ProviderUnavailable(
                "the hosted provider rate-limited the request (status 429)"
            )
        if response.status >= 500:
            raise ProviderUnavailable(
                f"the hosted provider failed (status {response.status})"
            )
        if response.status != 200:
            raise ProviderUnavailable(
                f"the hosted provider returned an unexpected status ({response.status})"
            )
        return self._selection_from_body(response.body)

    def _selection_from_body(self, body: bytes) -> dict[str, object]:
        try:
            envelope = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderUnavailable(
                "the hosted provider returned an unreadable response envelope"
            ) from None
        if not isinstance(envelope, Mapping):
            raise ProviderUnavailable(
                "the hosted provider returned a response envelope that is not an object"
            )
        if isinstance(envelope.get("error"), Mapping):
            raise ProviderUnavailable("the hosted provider reported an error")
        if envelope.get("status") != "completed":
            # The status is a hard gate: anything other than a completed response (including a
            # missing status) fails closed rather than being parsed optimistically.
            raise ProviderUnavailable(
                "the hosted provider did not report a completed response"
            )
        text = _extract_output_text(envelope)
        if text is None:
            raise ProviderUnavailable(
                "the hosted provider returned no structured output"
            )
        try:
            selection = json.loads(text)
        except json.JSONDecodeError:
            raise ProviderUnavailable(
                "the hosted provider returned output that is not valid JSON"
            ) from None
        if not isinstance(selection, Mapping):
            raise ProviderUnavailable(
                "the hosted provider returned output that is not a selection object"
            )
        return dict(selection)


@dataclass(frozen=True, slots=True)
class UnavailableProvider:
    """A provider that fails closed **before any egress** (the missing-credential policy).

    Returned by :func:`provider_from_environment` when the credential is absent: the
    explanation runtime then reports ``OUTCOME_PROVIDER_UNAVAILABLE`` with no HTTP attempt at
    all.  The message names neither the credential value nor the environment variable
    (``§7.1`` ``S-6`` ／ ``S-8``).
    """

    reason: str = "the hosted provider credential is not configured"

    def explain(self, projection: Mapping[str, object]) -> object:
        raise ProviderUnavailable(self.reason)


def provider_from_environment(
    *,
    environ: Mapping[str, str] | None = None,
    transport: HttpTransport | None = None,
    model: str = DEEPSEEK_MODEL,
    base_url: str = DEEPSEEK_BASE_URL,
    endpoint: str = DEEPSEEK_RESPONSES_PATH,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> DeepSeekProvider | UnavailableProvider:
    """Composition boundary: resolve the credential and build the provider (``§7.1`` ``S-2``).

    The credential is read **only** here, **only** from the process environment, at call time;
    it is never written anywhere, never logged and never returned.  When it is absent the
    policy is to fail closed with :class:`UnavailableProvider`, i.e. no hosted egress at all.
    """

    source: Mapping[str, str] = os.environ if environ is None else environ
    value = source.get(DEEPSEEK_API_KEY_ENV, "")
    if not isinstance(value, str) or not value.strip():
        return UnavailableProvider()
    return DeepSeekProvider(
        api_key=value,
        model=model,
        base_url=base_url,
        endpoint=endpoint,
        timeout=timeout,
        transport=transport,
    )


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "DEEPSEEK_API_KEY_ENV",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_PROVIDER",
    "DEEPSEEK_RESPONSES_PATH",
    "DeepSeekProvider",
    "HttpRequest",
    "HttpResponse",
    "HttpTransport",
    "INSTRUCTIONS",
    "MAX_RESPONSE_BYTES",
    "ProviderUnavailable",
    "SELECTION_SCHEMA_NAME",
    "StdlibHttpTransport",
    "UnavailableProvider",
    "provider_from_environment",
    "selection_json_schema",
]
