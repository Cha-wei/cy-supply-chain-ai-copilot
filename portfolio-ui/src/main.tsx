import { useReducer, useRef } from "react";
import { initialState, reducer, demoStep, type DialogName } from "./state";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ChevronDown,
  FileText,
  Info,
  MessageCircle,
  ShieldCheck,
} from "lucide-react";
import { scenario as f, recommendationPath } from "./fixture";
import { EntryPage } from "./entry";
import { AppShell } from "./shell";
import { DecisionForm } from "./decision-form";
import { decisionAdjustment } from "./decision-input";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./ui/collapsible";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";

import "@fontsource-variable/noto-sans-sc";
import "./styles.css";
type Variant = "C32";
const labels = [
  "当前缺口",
  "基础采购需求",
  "最低起订量 MOQ",
  "MOQ 调整",
  "建议采购量",
];
function Action({
  children,
  kind = "secondary",
  ...props
}: React.ComponentProps<typeof Button> & { kind?: string }) {
  return (
    <Button
      {...props}
      className={`system-button ${kind} ${props.className || ""}`}
    >
      {children}
    </Button>
  );
}
function Facts({ detailed = false }: { detailed?: boolean }) {
  return (
    <dl className="facts">
      {f.facts.map(([key, value], i) => (
        <div key={key}>
          <dt>
            {labels[i]}
            {detailed && <code>{key}</code>}
          </dt>
          <dd>
            {value}
            <span>件</span>
          </dd>
        </div>
      ))}
    </dl>
  );
}
function RecommendationDetail({ variant }: { variant: Variant }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const returnFocus = useRef<HTMLElement | null>(null);
  const reviewButton = useRef<HTMLButtonElement>(null);
  const draftButton = useRef<HTMLButtonElement>(null);
  const resetButton = useRef<HTMLButtonElement>(null);
  function open(dialog: DialogName, target: HTMLElement) {
    returnFocus.current = target;
    dispatch({ type: "OPEN", dialog });
  }
  const decision = state.decision;
  const approved = decision?.kind === "approve";
  const decided = decision !== null;
  const decisionLabel =
    decision?.kind === "reject"
      ? "已拒绝"
      : approved && decision.override
        ? "已调整"
        : "已批准";
  const titles = {
    evidence: "计算依据",
    explanation: "AI 解释",
    review: "人工审核",
    override: "修改采购数量",
    reject: "拒绝建议",
    draft: "采购申请草稿",
    boundary: "展示边界",
  };
  const descriptions = {
    evidence: "既有模拟数据中的只读事实，页面不重新计算采购数量。",
    explanation: "预置演示解释 · 未发起实时 AI 请求 · 不作为 runtime 证据",
    review: "按建议批准 · 仅当前页面内的演示决定",
    override: "由你决定批准数量，系统建议保持不变。",
    reject: "由你明确拒绝本条建议，系统建议保持不变。",
    draft: "DRAFT · 临时展示草稿，不是正式采购申请或采购订单",
    boundary: "SIMULATED · presentation-only",
  };
  return (
    <AppShell
      detail
      demoState={demoStep(state)}
      onBoundary={(target) => open("boundary", target)}
    >
      <main>
        <div className="page-heading">
          <div>
            <h1>采购决策</h1>
            <p className="material-context">
              <span>{f.display_name}</span>
              <span className="material-identity">
                物料编码：{f.material_code}
              </span>
              <span className="display-label-note">模拟展示名称</span>
            </p>
          </div>
          <span className="status">
            <span />
            {decided ? `人工${decisionLabel} · 演示` : "待人工审核 · 演示"}
          </span>
        </div>
        <div className="work-columns">
          <section
            className="evidence-region"
            id="evidence"
            aria-label="采购建议与计算依据"
          >
            <div className="recommendation-surface">
              <div className="recommendation">
                <div>
                  <h2>采购建议</h2>
                  <p className="support">
                    <ShieldCheck />
                    <span>根据当前供需</span>
                    <span>与采购策略计算</span>
                  </p>
                </div>
                <div className="quantity">
                  {f.recommended}
                  <span>件</span>
                </div>
              </div>
              <div
                className="equation"
                aria-label="当前缺口 30 加 MOQ 调整 70 等于建议采购 100"
              >
                <div>
                  <strong>{f.shortage}</strong>
                  <span>当前缺口</span>
                </div>
                <span className="operator">+</span>
                <div>
                  <strong>{f.adjustment}</strong>
                  <span>MOQ 调整</span>
                </div>
                <span className="operator">=</span>
                <div>
                  <strong>{f.recommended}</strong>
                  <span>建议采购</span>
                </div>
              </div>
            </div>
            <div className="section-heading">
              <h2>计算依据</h2>
              <Action
                kind="ghost"
                onClick={(e) => open("evidence", e.currentTarget)}
              >
                查看完整依据 <ArrowRight />
              </Action>
            </div>
            <div className="evidence-summary">
              需求是 <span className="quantity-inline">30 件</span>
              ，最低起订量是 <span className="quantity-inline">100 件</span>。
              <br />
              本次建议因此增加 <span className="quantity-inline">70 件</span>。
            </div>
            <div className="evidence-groups">
              <div className="evidence-group">
                <h3>需求</h3>
                <dl>
                  <div>
                    <dt>当前缺口</dt>
                    <dd>
                      {f.shortage}
                      <span>件</span>
                    </dd>
                  </div>
                  <div>
                    <dt>基础采购需求</dt>
                    <dd>
                      {f.base}
                      <span>件</span>
                    </dd>
                  </div>
                </dl>
              </div>
              <div className="evidence-group">
                <h3>采购策略</h3>
                <dl>
                  <div>
                    <dt>
                      最低起订量 <span className="inline-english">MOQ</span>
                    </dt>
                    <dd>
                      {f.moq}
                      <span>件</span>
                    </dd>
                  </div>
                  <div>
                    <dt>MOQ 调整</dt>
                    <dd>
                      +{f.adjustment}
                      <span>件</span>
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
            <Collapsible className="source">
              <CollapsibleTrigger className="disclosure">
                关于这些数据 <ChevronDown />
              </CollapsibleTrigger>
              <CollapsibleContent>
                <p>
                  沿用项目既有 MOQ
                  模拟场景。这些数值来自既有模拟数据；页面未执行数据导入、校验或采购计算。
                </p>
              </CollapsibleContent>
            </Collapsible>
            <p className="calculation-note">
              <ShieldCheck />
              AI 不参与采购数量计算
            </p>
          </section>
          <section className="decision-region" aria-label="解释与人工决策">
            <div className="explanation">
              <div className="section-heading">
                <h2>
                  <MessageCircle />
                  AI 解释
                </h2>
                <span className="role-label">仅解释</span>
              </div>
              <h3>为什么建议采购 100 件？</h3>
              <p>
                目前需要补足 <span className="quantity-inline">30 件</span>
                ，但最低起订量为 <span className="quantity-inline">100 件</span>
                。因此，建议在基础需求上增加{" "}
                <span className="quantity-inline">70 件</span>，采购{" "}
                <span className="quantity-inline">100 件</span>。
              </p>
              <p className="prepared-note">
                预置演示解释 · 无实时 AI 请求 · 非 runtime 证据
              </p>
              <div className="ai-disclosure">
                <Action
                  kind="ghost"
                  onClick={(e) => open("explanation", e.currentTarget)}
                >
                  查看 AI 解释 <ArrowRight />
                </Action>
              </div>
            </div>
            <div className="human-review" id="review">
              <div className="section-heading">
                <h2>{decided ? "人工决定" : "人工审核"}</h2>
                <span className="role-label">
                  {decided ? decisionLabel : "待决定"}
                </span>
              </div>
              <p role="status" aria-live="polite">
                {decision?.kind === "reject"
                  ? "人工已拒绝建议，不形成已批准草稿。"
                  : approved
                    ? decision.override
                      ? `人工已修改并批准 ${decision.approvedQuantity} 件，原建议保持不变。`
                      : `人工已按建议批准 ${decision.approvedQuantity} 件，原建议保持不变。`
                    : "建议供你参考，最终决策由人工完成。"}
              </p>
              {decision && (
                <dl className="decision-summary">
                  <div>
                    <dt>系统建议</dt>
                    <dd>
                      {decision.sourceRecommendation}
                      <span>件</span>
                    </dd>
                  </div>
                  {approved && (
                    <div>
                      <dt>人工批准</dt>
                      <dd>
                        {decision.approvedQuantity}
                        <span>件</span>
                      </dd>
                    </div>
                  )}
                  {approved && decision.override && (
                    <div>
                      <dt>调整</dt>
                      <dd>
                        {decisionAdjustment(decision.approvedQuantity)}
                        <span>件</span>
                      </dd>
                    </div>
                  )}
                  <div>
                    <dt>决定方式</dt>
                    <dd>
                      {decision.kind === "reject"
                        ? "拒绝"
                        : decision.override
                          ? "修改数量"
                          : "按建议批准"}
                    </dd>
                  </div>
                  {"reason" in decision && (
                    <div className="decision-reason">
                      <dt>原因</dt>
                      <dd>{decision.reason}</dd>
                    </div>
                  )}
                </dl>
              )}
              <div className="review-actions decision-actions">
                {!decided ? (
                  <>
                    <Action
                      ref={reviewButton}
                      kind="primary"
                      onClick={(e) => open("review", e.currentTarget)}
                    >
                      按建议批准 <ArrowRight />
                    </Action>
                    <div className="decision-alternatives">
                      <Action
                        onClick={(e) => open("override", e.currentTarget)}
                      >
                        修改采购数量
                      </Action>
                      <Action
                        kind="ghost"
                        onClick={(e) => open("reject", e.currentTarget)}
                      >
                        拒绝建议
                      </Action>
                    </div>
                  </>
                ) : (
                  <>
                    {approved && (
                      <Action
                        ref={draftButton}
                        kind="primary"
                        onClick={(e) => open("draft", e.currentTarget)}
                      >
                        查看采购申请草稿 <ArrowRight />
                      </Action>
                    )}
                    <Action
                      ref={resetButton}
                      onClick={() => {
                        dispatch({ type: "RESET" });
                        requestAnimationFrame(() =>
                          reviewButton.current?.focus(),
                        );
                      }}
                    >
                      重新演示
                    </Action>
                  </>
                )}
              </div>
            </div>
            <div className={`draft ${approved ? "draft-ready" : ""}`}>
              <FileText />
              <div>
                <h3>采购申请草稿</h3>
                <p>
                  {approved
                    ? "DRAFT · 人工批准后可预览"
                    : decided
                      ? "未形成 · 建议已拒绝"
                      : "尚未形成 · 等待人工决定"}
                </p>
              </div>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Action kind="icon" aria-label="草稿状态说明">
                    <Info />
                  </Action>
                </TooltipTrigger>
                <TooltipContent
                  className="material system-tooltip"
                  data-variant={variant}
                >
                  临时展示状态，不是采购订单；刷新或重置后清除。
                </TooltipContent>
              </Tooltip>
            </div>
            <p className="execution-note">人工批准 ≠ 生产执行</p>
          </section>
        </div>
      </main>
      <Dialog
        open={state.dialog !== null}
        onOpenChange={(value) => {
          if (!value) dispatch({ type: "CLOSE" });
        }}
      >
        <DialogContent
          className="material system-dialog"
          data-variant={variant}
          onCloseAutoFocus={(e) => {
            e.preventDefault();
            if (returnFocus.current?.isConnected) returnFocus.current.focus();
            else (draftButton.current ?? resetButton.current)?.focus();
          }}
        >
          <DialogTitle>{state.dialog ? titles[state.dialog] : ""}</DialogTitle>
          <DialogDescription>
            {state.dialog ? descriptions[state.dialog] : ""}
          </DialogDescription>
          {state.dialog === "evidence" && (
            <>
              <Facts detailed />
              <p className="support">
                确定性系统计算事实；本页面只展示既有 fixture，不执行供应链规则。
              </p>
            </>
          )}
          {state.dialog === "explanation" && (
            <>
              <p>{f.explanation}</p>
              <Facts />
              <p>
                AI
                仅解释已有的确定性事实，不计算或修改采购数量。最终决策由人工完成。
              </p>
            </>
          )}
          {state.dialog === "review" && (
            <>
              <p>
                确认按建议批准 <strong>{f.recommended} 件</strong>
                ？此操作由你作出，AI 不具有审批权。
              </p>
              <Facts />
              <p className="support">
                目前尚无人工决定，草稿尚未形成。确认只记录本次页面演示状态，刷新或重置后清除。
              </p>
              <p className="support">
                人工批准 ≠ 生产执行 · 不写入 ERP · 不创建采购订单
              </p>
              <div className="review-actions">
                <Action onClick={() => dispatch({ type: "CLOSE" })}>
                  返回查看
                </Action>
                <Action
                  kind="primary"
                  onClick={() => dispatch({ type: "APPROVE" })}
                >
                  按建议批准 {f.recommended} 件
                </Action>
              </div>
            </>
          )}
          {(state.dialog === "override" || state.dialog === "reject") && (
            <DecisionForm
              key={state.dialog}
              kind={state.dialog}
              onCancel={() => dispatch({ type: "CLOSE" })}
              onConfirm={(quantity, reason) =>
                dispatch(
                  state.dialog === "override"
                    ? { type: "OVERRIDE", quantity, reason }
                    : { type: "REJECT", reason },
                )
              }
            />
          )}
          {state.dialog === "draft" && state.decision?.kind === "approve" && (
            <>
              <dl className="facts draft-facts">
                <div>
                  <dt>状态</dt>
                  <dd>DRAFT</dd>
                </div>
                <div>
                  <dt>人工批准数量</dt>
                  <dd>
                    {state.decision.approvedQuantity}
                    <span>件</span>
                  </dd>
                </div>
                <div>
                  <dt>来源建议数量</dt>
                  <dd>
                    {f.recommended}
                    <span>件</span>
                  </dd>
                </div>
                <div>
                  <dt>决定来源</dt>
                  <dd>人工（Human）</dd>
                </div>
                <div>
                  <dt>ERP 写入</dt>
                  <dd>否 · NO</dd>
                </div>
                <div>
                  <dt>采购订单（PO）</dt>
                  <dd>未创建 · NO</dd>
                </div>
                <div>
                  <dt>生产执行</dt>
                  <dd>否 · NO</dd>
                </div>
              </dl>
              <p>
                人工批准 ≠
                生产执行。本草稿仅存在于当前页面内存，不提交、不持久保存，刷新或重置后清除。
              </p>
            </>
          )}
          {state.dialog === "boundary" && (
            <p>
              沿用项目既有模拟数据。本页面未连接计算、AI 或审批
              runtime。人工决定仅为当前浏览器中的临时演示状态；未验证身份或权限。不写入
              ERP，不创建采购订单，不执行生产操作。
            </p>
          )}
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
function App() {
  return (
    <TooltipProvider>
      <div className="demo-page material" data-variant="C32">
        {location.pathname === "/" ? (
          <EntryPage />
        ) : location.pathname === recommendationPath ? (
          <RecommendationDetail variant="C32" />
        ) : (
          <AppShell>
            <main>
              <h1>未找到采购建议</h1>
              <p>当前演示仅包含一条固定模拟建议。</p>
              <a className="system-button secondary" href="/">
                返回采购决策工作台
              </a>
            </main>
          </AppShell>
        )}
      </div>
    </TooltipProvider>
  );
}
document.title =
  location.pathname === "/"
    ? "采购决策工作台 · CY 供应链 AI Copilot"
    : location.pathname === recommendationPath
      ? `${f.display_name} · 采购建议详情 · CY`
      : "未找到采购建议 · CY";
createRoot(document.getElementById("root")!).render(<App />);
