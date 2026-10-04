import { StrictMode, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCheck,
  ChevronDown,
  FileText,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { scenario as f } from "./fixture";
import "./style.css";

function App() {
  const [explained, setExplained] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [decision, setDecision] = useState<"open" | "approved" | "rejected">(
    "open",
  );
  const dialog = useRef<HTMLDialogElement>(null);
  const draft = useRef<HTMLElement>(null);
  function reset() {
    setExplained(false);
    setUnavailable(false);
    setDecision("open");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function approve() {
    setDecision("approved");
    dialog.current?.close();
    setTimeout(
      () =>
        draft.current?.scrollIntoView({ behavior: "smooth", block: "center" }),
      80,
    );
  }
  return (
    <>
      <header>
        <a className="brand" href="#">
          <span className="monogram">
            cy<span>·</span>
          </span>
          <span>
            Supply Chain <strong>AI Copilot</strong>
          </span>
        </a>
        <span className="environment">
          <i /> SIMULATED Portfolio POC
        </span>
        <button className="reset" onClick={reset}>
          <RotateCcw size={14} /> Reset demo
        </button>
      </header>
      <main>
        <div className="intro">
          <div>
            <p className="eyebrow">PROCUREMENT DECISION WORKSPACE</p>
            <h1>Clarity before commitment.</h1>
            <p className="subtitle">
              A shortage is a signal. A purchase is a human decision.
            </p>
          </div>
          <div className="authority">
            <span>
              Calculation <b>Deterministic</b>
            </span>
            <span>
              Explanation <b>AI</b>
            </span>
            <span>
              Decision <b>Human</b>
            </span>
          </div>
        </div>
        <nav aria-label="Demo progress">
          <ol>
            {["Scenario", "Recommendation", "Explain", "Review", "Draft"].map(
              (name, i) => (
                <li
                  key={name}
                  className={
                    i < 2 ||
                    (i === 2 && explained) ||
                    (i === 3 && decision !== "open") ||
                    (i === 4 && decision === "approved")
                      ? "complete"
                      : ""
                  }
                >
                  <a href={"#" + name.toLowerCase()}>
                    <span className="step">{i + 1}</span>
                    {name}
                  </a>
                  {i < 4 && <span className="connector" />}
                </li>
              ),
            )}
          </ol>
          <span className="prototype">
            Presentation prototype · not runtime evidence
          </span>
        </nav>
        <section id="scenario" className="scenario">
          <div className="scenario-icon">
            <ShieldCheck size={21} />
          </div>
          <div>
            <p className="eyebrow">01 / CONTROLLED SCENARIO</p>
            <h2>When the minimum order exceeds the shortage</h2>
          </div>
          <div className="scenario-status">
            <span>
              <Check size={13} /> Snapshot accepted
            </span>
            <span>
              <Check size={13} /> Validation accepted
            </span>
            <small>Fixture states · read only</small>
          </div>
        </section>
        <div className="workspace">
          <div className="left-column">
            <section id="recommendation" className="panel recommendation">
              <div className="section-top">
                <p className="eyebrow">02 / DETERMINISTIC RECOMMENDATION</p>
                <span className="quiet-tag">
                  <ShieldCheck size={13} /> Rule-based result
                </span>
              </div>
              <h2>
                Buy to the policy.
                <br />
                <span>Understand the difference.</span>
              </h2>
              <div className="metrics">
                <div>
                  <span className="metric-label">Shortage quantity</span>
                  <strong>{f.shortage}</strong>
                  <small>units needed</small>
                </div>
                <span className="metric-divider" />
                <div>
                  <span className="metric-label">Applicable MOQ</span>
                  <strong>{f.moq}</strong>
                  <small>minimum order quantity</small>
                </div>
              </div>
              <div className="recommended">
                <div>
                  <span className="metric-label">
                    Recommended purchase quantity
                  </span>
                  <strong>
                    {f.recommended}
                    <small>units</small>
                  </strong>
                </div>
                <div className="composition">
                  <span>
                    Base purchase need <b>{f.base}</b>
                  </span>
                  <span>
                    MOQ adjustment <b>+{f.adjustment}</b>
                  </span>
                  <div className="bar">
                    <i />
                    <i />
                  </div>
                  <small>30 needed + 70 to meet MOQ</small>
                </div>
              </div>
              <p className="calculation-note">
                <ShieldCheck size={14} /> Calculated by deterministic rules. AI
                does not set this quantity.
              </p>
              <details>
                <summary>
                  View calculation evidence <ChevronDown size={15} />
                </summary>
                <div className="evidence">
                  <p>
                    SIMULATED fixture · accepted input → deterministic
                    calculation → resolved procurement policy.
                  </p>
                  {f.facts.map(([key, value]) => (
                    <div key={key}>
                      <code>{key}</code>
                      <b>{value}</b>
                    </div>
                  ))}
                  <p>
                    Analysis Run: presentation context only; no live runtime
                    run. Source: repository MOQ-raised test scenario. AI did not
                    modify the result.
                  </p>
                </div>
              </details>
            </section>
            <section id="explain" className="panel explanation">
              <div className="section-top">
                <p className="eyebrow">03 / AI EXPLANATION</p>
                <span className="quiet-tag">
                  <Sparkles size={13} /> Explanation only
                </span>
              </div>
              <h2>“Why 100, if we only need 30?”</h2>
              <p className="muted">
                One business question. Grounded in five deterministic facts.
              </p>
              <div aria-live="polite">
                {!explained ? (
                  <button
                    className="explain-button"
                    onClick={() => setExplained(true)}
                  >
                    Explore the explanation <ArrowRight size={16} />
                  </button>
                ) : unavailable ? (
                  <div className="answer">
                    <h3>AI explanation unavailable</h3>
                    <p>
                      The recommendation remains available at <b>100 units</b>.
                      Business facts are unchanged. Human review can continue
                      using calculation evidence.
                    </p>
                  </div>
                ) : (
                  <div className="answer">
                    <p>
                      The shortage and base purchase need are both{" "}
                      <b>30 units</b>. The applicable minimum order quantity is{" "}
                      <b>100 units</b>, so the deterministic recommendation
                      includes an MOQ adjustment of <b>70 units</b>.
                    </p>
                    <p>
                      The recommended purchase quantity is therefore{" "}
                      <b>100 units</b>. A human must decide whether to approve
                      it.
                    </p>
                    <small>
                      Prepared presentation wording · no live AI request
                    </small>
                    <div className="fact-links">
                      {f.facts.map(([key, value]) => (
                        <span key={key}>
                          {key} <b>{value}</b>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <label className="availability">
                <input
                  type="checkbox"
                  checked={unavailable}
                  onChange={(e) => {
                    setUnavailable(e.target.checked);
                    setExplained(true);
                  }}
                />{" "}
                Preview AI unavailable state
              </label>
            </section>
          </div>
          <aside>
            <section id="review" className="panel review">
              <p className="eyebrow">04 / HUMAN REVIEW</p>
              <div className="review-title">
                <h2>Your decision.</h2>
                <span className="current">
                  <i />{" "}
                  {decision === "open"
                    ? "Current fixture"
                    : decision === "approved"
                      ? "Approved"
                      : "Rejected"}
                </span>
              </div>
              <p className="muted">
                Review the evidence before creating a draft.
              </p>
              <dl>
                <div>
                  <dt>Recommended quantity</dt>
                  <dd>{f.recommended} units</dd>
                </div>
                <div>
                  <dt>Applicable MOQ</dt>
                  <dd>{f.moq} units</dd>
                </div>
                <div>
                  <dt>Explanation</dt>
                  <dd>
                    {explained
                      ? unavailable
                        ? "Unavailable"
                        : "Prepared fixture"
                      : "Not viewed"}
                  </dd>
                </div>
                <div>
                  <dt>Decision authority</dt>
                  <dd>Human</dd>
                </div>
              </dl>
              <div className="supplier">
                <ShieldCheck size={17} />
                <div>
                  <h3>Supplier risk evidence</h3>
                  <p>
                    Not included in this presentation fixture. No supplier
                    ranking or selection is implied.
                  </p>
                </div>
              </div>
              {decision === "open" ? (
                <>
                  <button
                    className="primary"
                    onClick={() => dialog.current?.showModal()}
                  >
                    Approve as recommended <ArrowRight size={16} />
                  </button>
                  <button
                    className="reject"
                    onClick={() => setDecision("rejected")}
                  >
                    Reject recommendation
                  </button>
                  <p className="action-note">
                    Demo action only · no durable approval
                  </p>
                </>
              ) : (
                <div className="decision-result" role="status">
                  {decision === "approved" ? (
                    <CheckCheck size={22} />
                  ) : (
                    <X size={22} />
                  )}
                  <h3>
                    {decision === "approved"
                      ? "Approved as recommended"
                      : "Recommendation rejected"}
                  </h3>
                  <p>
                    {decision === "approved"
                      ? "100 units reflected in the ephemeral draft."
                      : "No approved draft created. Reset the demo to begin a new presentation."}
                  </p>
                </div>
              )}
            </section>
            <section
              id="draft"
              ref={draft}
              className={
                "panel draft " + (decision === "approved" ? "draft-ready" : "")
              }
            >
              <div className="section-top">
                <p className="eyebrow">05 / PROCUREMENT REQUEST</p>
                <FileText size={19} />
              </div>
              <h2>
                {decision === "approved"
                  ? "A draft. A deliberate next step."
                  : "A draft starts with you."}
              </h2>
              {decision === "approved" ? (
                <>
                  <span className="draft-label">DRAFT · EPHEMERAL</span>
                  <div className="draft-quantity">
                    <span>Approved quantity</span>
                    <strong>
                      100 <small>units</small>
                    </strong>
                  </div>
                  <p className="muted">
                    Human choice: approve as recommended.
                    <br />
                    Original recommendation: 100 units.
                  </p>
                </>
              ) : (
                <p className="muted">
                  {decision === "rejected"
                    ? "Rejected recommendations do not create an approved draft."
                    : "Approve the recommendation to preview the decision in a Procurement Request Draft."}
                </p>
              )}
              <div className="execution">
                <span>
                  ERP write <b>NO</b>
                </span>
                <span>
                  Purchase Order <b>NO</b>
                </span>
                <span>
                  Production execution <b>NO</b>
                </span>
              </div>
              <p className="boundary">Human approval ≠ production execution</p>
            </section>
          </aside>
        </div>
        <footer>
          <div>
            <span className="monogram">
              cy<span>·</span>
            </span>
            <p>Deterministic systems calculate. AI explains. Humans decide.</p>
          </div>
          <p>
            SIMULATED · Real customer validation not performed · Business value
            not proven
            <br />
            Production readiness not claimed · POC SUCCESS not claimed
          </p>
          <a
            href="https://github.com/Cha-wei/cy-supply-chain-ai-copilot"
            target="_blank"
            rel="noreferrer"
          >
            Explore the project <ArrowUpRight size={13} />
          </a>
        </footer>
      </main>
      <dialog
        ref={dialog}
        aria-labelledby="approval-title"
        onClick={(e) => {
          if (e.target === e.currentTarget) dialog.current?.close();
        }}
      >
        <form method="dialog">
          <button className="close" aria-label="Close confirmation">
            <X size={20} />
          </button>
        </form>
        <p className="eyebrow">HUMAN DECISION · PRESENTATION ONLY</p>
        <h2 id="approval-title">Approve 100 units?</h2>
        <p>
          This previews approval of the deterministic recommendation as-is. The
          resulting Procurement Request Draft is ephemeral and is not a Purchase
          Order.
        </p>
        <div className="confirm-value">
          <span>Approved quantity</span>
          <strong>100 units</strong>
        </div>
        <p className="muted">
          No ERP write. No production execution.
          <br />
          Resetting or refreshing clears this demo decision.
        </p>
        <button className="primary" onClick={approve}>
          Confirm demo approval <Check size={16} />
        </button>
      </dialog>
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
