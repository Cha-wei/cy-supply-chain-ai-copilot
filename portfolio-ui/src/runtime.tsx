import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { DialogName, Snapshot, State } from "./state";
import type { InputErrors } from "./decision-input";
import { displayName } from "./fixture";

type Event = { type: "OPEN"; dialog: DialogName } | { type: "CLOSE" | "REREVIEW" | "RESET" | "SIMULATE_RUN" | "EXPLAIN" } | { type: "APPROVE"; reviewId: string | null } | { type: "OVERRIDE"; reviewId: string | null; quantity: string; reason: string } | { type: "REJECT"; reviewId: string | null; reason: string };
type Runtime = { state: State; busy: boolean; error: string; dispatch: (event: Event) => Promise<InputErrors | undefined> };
const Context = createContext<Runtime | null>(null);
export const useRuntime = () => {
  const value = useContext(Context);
  if (!value) throw new Error("Runtime view unavailable");
  return value;
};
export function useFacts() {
  const { state } = useRuntime();
  const f = state.facts;
  return { ...f, display_name: displayName, explanation: state.explanation,
    facts: [["ShortageQty", f.shortage], ["BasePurchaseNeed", f.base], ["ApplicableMOQ", f.moq], ["MOQAdjustmentQty", f.adjustment], ["RecommendedPurchaseQty", f.recommended]],
  };
}
class RequestError extends Error { constructor(public code: string) { super(code); } }
async function exchange(method: "GET" | "POST", body?: object): Promise<Snapshot | { initialized: false; session: string }> {
  const response = await fetch(method === "GET" ? "/demo/state" : "/demo/intent", {
    method, headers: method === "POST" ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined, cache: "no-store", signal: AbortSignal.timeout(15000),
  });
  const value = await response.json();
  if (!response.ok) throw new RequestError(value.error || "unavailable");
  if (typeof value.initialized !== "boolean" || typeof value.session !== "string") throw new RequestError("unavailable");
  return value;
}
export function RuntimeProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const current = useRef<Snapshot | null>(null);
  const [dialog, setDialog] = useState<DialogName | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const working = useRef(false);
  const lost = useRef(false);
  const revision = useRef(0);
  function accept(value: Snapshot | { initialized: false; session: string }) {
    if (current.current && value.session !== current.current.session) {
      lost.current = true; setSnapshot(null); setDialog(null);
      throw new RequestError("session_lost");
    }
    if (!value.initialized) throw new RequestError("session_lost");
    const previous = current.current;
    if (previous && (previous.run !== value.run || previous.review.id !== value.review.id || JSON.stringify(previous.review.decision) !== JSON.stringify(value.review.decision))) setDialog(null);
    current.current = value; setSnapshot(value);
  }
  async function read() {
    const ticket = ++revision.current;
    const value = await exchange("GET");
    if (ticket === revision.current) accept(value);
  }
  async function initialize() {
    if (working.current) return;
    working.current = true; setBusy(true); setError("");
    try {
      const existing = await exchange("GET");
      if (lost.current) { current.current = null; lost.current = false; }
      accept(existing.initialized ? existing : await exchange("POST", { op: "initialize", intent: crypto.randomUUID(), session: existing.session }));
    } catch { setError("本地运行时不可用或会话已结束。请确认服务后重新连接。"); }
    finally { working.current = false; setBusy(false); }
  }
  useEffect(() => {
    void initialize();
    const refresh = () => { if (!working.current && !lost.current && current.current) void read().catch(() => setError("连接不可用或会话已结束；未切换为模拟数据。")); };
    window.addEventListener("focus", refresh);
    const timer = window.setInterval(refresh, 2000);
    return () => { window.removeEventListener("focus", refresh); window.clearInterval(timer); };
  }, []);
  async function command(op: string, args: object = {}) {
    ++revision.current; // retire any earlier poll response before mutating
    const now = current.current;
    if (!now) throw new RequestError("session_lost");
    accept(await exchange("POST", { op, intent: crypto.randomUUID(), session: now.session, run: now.run, review: now.review.id, ...args }));
  }
  async function dispatch(event: Event): Promise<InputErrors | undefined> {
    if (event.type === "CLOSE") { setDialog(null); return; }
    if (working.current) return;
    working.current = true; setBusy(true); setError("");
    try {
      if (event.type === "OPEN") {
        if (["review", "override", "reject"].includes(event.dialog)) await command("open_review");
        else if (event.dialog === "draft") await read();
        setDialog(event.dialog);
      } else if (event.type === "REREVIEW") { await command("open_review"); setDialog(null); }
      else if (event.type === "EXPLAIN") { await command("explain"); }
      else if (event.type === "SIMULATE_RUN" || event.type === "RESET") { await command("new_analysis"); setDialog(null); }
      else if ("reviewId" in event) {
        if (event.reviewId !== current.current?.review.id) throw new RequestError("binding_conflict");
        await command(event.type === "APPROVE" ? "approve" : event.type === "OVERRIDE" ? "override" : "reject",
          event.type === "OVERRIDE" ? { quantity: event.quantity, reason: event.reason } : event.type === "REJECT" ? { reason: event.reason } : {});
        setDialog(null);
      }
    } catch (failure) {
      const code = failure instanceof RequestError ? failure.code : "unknown_result";
      // Never repeat an uncertain mutation. Re-read Python state before another explicit intent.
      await read().catch(() => { setSnapshot(null); });
      if (code === "decision_invalid") return event.type === "OVERRIDE"
        ? { quantity: "Python 未批准此输入：请检查完整十进制数量、MOQ 和原因。", reason: "请填写有效原因。" }
        : { reason: "Python 未批准此输入：请填写有效原因。" };
      setError(code === "session_lost" ? "服务已重启，会话已结束。请重新连接。" : "操作未确认或当前审核已变化。已尝试读取最新状态，请核对后再决定。");
    } finally { working.current = false; setBusy(false); }
  }
  if (!snapshot) return <div className="demo-page material" data-variant="C32"><main className="workspace"><h1>采购决策工作台</h1><p role="status">{error || "正在连接本地运行时…"}</p><p>SIMULATED · 无 ERP / PO / 生产执行</p>{error && <button className="system-button primary" disabled={busy} onClick={() => void initialize()}>重新连接</button>}</main></div>;
  return <Context.Provider value={{ state: { ...snapshot, dialog }, busy, error, dispatch }}>
    {error && <p role="alert" className="runtime-message">{error}</p>}{children}
  </Context.Provider>;
}
