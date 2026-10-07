import { useRef } from "react";
import {
  demoStep,
  type DialogName,
  isStale,
  draftAvailable,
  explanationAvailable,
} from "./state";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ChevronDown,
  FileText,
  Info,
  MessageCircle,
  ShieldCheck,
} from "lucide-react";
import { RuntimeProvider, useRuntime, useFacts } from "./runtime";
import { EntryPage } from "./entry";
import { AppShell } from "./shell";
import { DecisionForm } from "./decision-form";
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
  const { busy } = useRuntime();
  return (
    <Button
      {...props}
      disabled={busy || props.disabled}
      className={`system-button ${kind} ${props.className || ""}`}
    >
      {children}
    </Button>
  );
}
function Facts({ detailed = false }: { detailed?: boolean }) {
  const f = useFacts();
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
  const { state, dispatch } = useRuntime();
  const f = useFacts();
  const returnFocus = useRef<HTMLElement | null>(null);
  const reviewButton = useRef<HTMLButtonElement>(null);
  const draftButton = useRef<HTMLButtonElement>(null);
  const resetButton = useRef<HTMLButtonElement>(null);
  const rereviewButton = useRef<HTMLButtonElement>(null);
  function open(dialog: DialogName, target: HTMLElement) {
    returnFocus.current = target;
    dispatch({ type: "OPEN", dialog });
  }
  const decision = state.review.decision;
  const stale = isStale(state);
  const canDraft = draftAvailable(state);
  const hasExplanation = explanationAvailable(state);
  const approved = decision?.kind === "approve";
  const decided = decision !== null;
  const decisionLabel =
    decision?.kind === "reject"
      ? "已拒绝"
      : approved && decision.override
        ? "已修改并批准"
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
    explanation: "Q3 runtime 解释 · 本轮不调用 hosted AI",
    review: "按建议批准 · Python 内存中的 SIMULATED 人工决定",
    override: "由你决定批准数量，系统建议保持不变。",
    reject: "由你明确拒绝本条建议，系统建议保持不变。",
    draft: "DRAFT · 临时展示草稿，不是正式采购申请或采购订单",
    boundary: "SIMULATED · 本地 Python runtime",
  };
  return (
    <AppShell
      detail
      demoState={demoStep(state)}
      onBoundary={(target) => open("boundary", target)}
    >
      <main data-review-id={state.review.id} data-review-stale={stale}>
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
            {stale
              ? "审核已失效 · 演示"
              : decided
                ? `${approved && decision.override ? decisionLabel : `人工${decisionLabel}`} · 演示`
                : "待人工审核 · 演示"}
          </span>
        </div>
        {(stale || state.reReview) && (
          <p className="freshness-note">
            {stale
              ? "已执行新的分析运行。"
              : "已创建新的演示审核，上一轮决定与草稿不继承。"}
            相同固定输入已通过 Python 重新计算；数量相同不代表跨分析上下文等价。
          </p>
        )}
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
                aria-label={`当前缺口 ${f.shortage} 加 MOQ 调整 ${f.adjustment} 等于建议采购 ${f.recommended}`}
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
              需求是 <span className="quantity-inline">{f.shortage} 件</span>
              ，最低起订量是 <span className="quantity-inline">{f.moq} 件</span>。
              <br />
              本次建议因此增加 <span className="quantity-inline">{f.adjustment} 件</span>。
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
                  模拟场景。Python 已执行受控导入、校验与确定性计算，页面仅展示结果。
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
              {hasExplanation ? (
                <>
                  <div className="section-heading">
                    <h2>
                      <MessageCircle />
                      AI 解释
                    </h2>
                    <span className="role-label">仅解释</span>
                  </div>
                  <h3>为什么建议采购 {f.recommended} 件？</h3>
                  <p>{f.explanation}</p>
                  <p className="prepared-note">Q3 runtime 返回的已验证解释 · 非审批权威</p>
                  <div className="ai-disclosure">
                    <Action
                      kind="ghost"
                      onClick={(e) => open("explanation", e.currentTarget)}
                    >
                      查看 AI 解释 <ArrowRight />
                    </Action>
                  </div>
                </>
              ) : (
                <div className="explanation-unavailable">
                  <h2>
                    <MessageCircle />
                    AI 解释不可用
                  </h2>
                  <p>
                    当前未提供可用的 Q3 解释。旧解释不会跨分析运行复用。
                  </p>
                  <p className="prepared-note">
                    未调用 hosted AI。人工仍可依据确定性事实完成审核。
                  </p>
                  {(!state.review.id || stale) && <Action kind="ghost" onClick={() => dispatch({ type: "EXPLAIN" })}>请求 AI 解释</Action>}
                </div>
              )}
            </div>
            <div className="human-review" id="review">
              <div className="section-heading">
                <h2>
                  {stale ? "当前审核已失效" : decided ? "人工决定" : "人工审核"}
                </h2>
                <span className="role-label">
                  {stale ? "需重新审核" : decided ? decisionLabel : "待决定"}
                </span>
              </div>
              <p role="status" aria-live="polite">
                {stale
                  ? "已执行新的分析运行，需要基于当前结果重新审核。"
                  : decision?.kind === "reject"
                    ? "人工已拒绝建议，不形成已批准草稿。"
                    : approved
                      ? decision.override
                        ? `人工已修改并批准 ${decision.approvedQuantity} 件，原建议保持不变。`
                        : `人工已按建议批准 ${decision.approvedQuantity} 件，原建议保持不变。`
                      : "建议供你参考，最终决策由人工完成。"}
              </p>
              {decision && (
                <>
                  {stale && (
                    <div className="stale-decision-note">
                      <h3>上一轮人工决定</h3>
                      <p>已失效，仅供参考；不适用于新的分析上下文。</p>
                    </div>
                  )}
                  <dl
                    className={`decision-summary ${stale ? "stale-summary" : ""}`}
                    aria-label={
                      stale
                        ? "上一轮人工决定，已失效，仅供参考"
                        : "人工决定摘要"
                    }
                  >
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
                    {decision.reason && (
                      <div className="decision-reason">
                        <dt>原因</dt>
                        <dd>{decision.reason}</dd>
                      </div>
                    )}
                  </dl>
                </>
              )}
              <div className="review-actions decision-actions">
                {stale ? (
                  <Action
                    ref={rereviewButton}
                    kind="primary"
                    onClick={async () => {
                      await dispatch({ type: "REREVIEW" });
                      requestAnimationFrame(() =>
                        reviewButton.current?.focus(),
                      );
                    }}
                  >
                    重新审核 <ArrowRight />
                  </Action>
                ) : !decided ? (
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
                    {canDraft && (
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
                      模拟新分析运行
                    </Action>
                  </>
                )}
              </div>
            </div>
            <div className={`draft ${canDraft ? "draft-ready" : ""}`}>
              <FileText />
              <div>
                <h3>采购申请草稿</h3>
                <p>
                  {stale
                    ? approved
                      ? "STALE / NON-ACTIONABLE · 需重新审核"
                      : "需重新审核 · 尚未形成已批准草稿"
                    : approved
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
                  {stale
                    ? "旧草稿不可继续操作，旧批准不适用于新审核。"
                    : "Python 内存草稿，不是采购订单；服务重启后丢失。"}
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
            else
              (
                rereviewButton.current ??
                draftButton.current ??
                resetButton.current
              )?.focus();
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
                Python 确定性系统计算事实；浏览器不执行供应链规则。
              </p>
            </>
          )}
          {state.dialog === "explanation" && hasExplanation && (
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
                目前尚无人工决定。确认将由 Python 记录到当前模拟会话；刷新不会清除，服务重启后丢失。
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
                  onClick={() =>
                    dispatch({ type: "APPROVE", reviewId: state.review.id })
                  }
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
                    ? {
                        type: "OVERRIDE",
                        reviewId: state.review.id,
                        quantity,
                        reason,
                      }
                    : { type: "REJECT", reviewId: state.review.id, reason },
                )
              }
            />
          )}
          {state.dialog === "draft" &&
            canDraft &&
            state.review.decision?.kind === "approve" && (
              <>
                <dl className="facts draft-facts">
                  <div>
                    <dt>状态</dt>
                    <dd>DRAFT</dd>
                  </div>
                  <div>
                    <dt>人工批准数量</dt>
                    <dd>
                      {state.draft?.quantityText}
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
                  生产执行。本草稿仅存在于 Python 会话内存，不提交、不持久保存，服务重启后丢失。
                </p>
              </>
            )}
          {state.dialog === "boundary" && (
            <>
              <p>
                固定 SIMULATED 场景已连接本地 Python 计算、审核与草稿 runtime。
                人工决定仅存在于 Python 内存；多标签共享会话，未验证身份或权限。
                不写入 ERP，不创建采购订单，不执行生产操作。
              </p>
              <div className="demo-controls">
                <h3>演示控制</h3>
                <p>
                  对相同固定输入执行新的 Python 分析运行，不声称输入数据改变。旧审核与草稿失效，需重新审核；不调用 hosted AI。
                </p>
                <Action
                  disabled={stale}
                  onClick={() => {
                    returnFocus.current = null;
                    dispatch({
                      type: "SIMULATE_RUN",
                    });
                  }}
                >
                  模拟新分析运行
                </Action>
                <p className="prepared-note">
                  仅比较
                  analysis_run_id、snapshot_package_identity、accepted_content_view_digest、analysis_date。rule
                  / code-version freshness 仍未解决。
                </p>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
function App() {
  const f = useFacts();
  const recommendationPath = `/procurement/${encodeURIComponent(f.material_code)}`;
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
document.title = "采购决策 · CY 供应链 AI Copilot";
createRoot(document.getElementById("root")!).render(<RuntimeProvider><App /></RuntimeProvider>);
