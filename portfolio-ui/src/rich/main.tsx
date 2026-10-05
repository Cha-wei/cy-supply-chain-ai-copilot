import { useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ChevronDown,
  FileText,
  Info,
  MessageCircle,
  ShieldCheck,
} from "lucide-react";
import { scenario as f } from "../fixture";
import { Button } from "../concepts/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "../concepts/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../concepts/ui/tabs";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../apple/ui/collapsible";
import { Switch } from "../apple/ui/switch";
import { Input } from "../apple/ui/input";
import { Textarea } from "../apple/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../apple/ui/tooltip";

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
function Preview({
  variant,
  title,
  description,
  trigger,
  children,
}: {
  variant: Variant;
  title: string;
  description: string;
  trigger: ReactNode;
  children: ReactNode;
}) {
  return (
    <Dialog>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="material system-dialog" data-variant={variant}>
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{description}</DialogDescription>
        {children}
      </DialogContent>
    </Dialog>
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
function Workspace({ variant }: { variant: Variant }) {
  return (
    <section className="design-stage material" data-variant={variant}>
      <div className="workspace">
        <header className="workspace-nav">
          <div className="brand">
            <span className="brand-mark">CY</span>
            <span>供应链 AI Copilot</span>
          </div>
          <nav aria-label="工作区导航">
            <a href="#evidence">建议与依据</a>
            <a href="#review">人工审核</a>
          </nav>
          <div className="nav-end">
            <span className="simulation">
              模拟演示 <span>SIMULATED</span>
            </span>
            <Preview
              variant={variant}
              title="展示边界"
              description="Presentation-only · 仅展示原型"
              trigger={
                <Action kind="icon" aria-label="查看展示边界">
                  <Info />
                </Action>
              }
            >
              <p>
                沿用项目既有模拟数据。本页面未连接计算或 AI 服务，不写入
                ERP，不创建采购订单，也不执行生产操作。
              </p>
            </Preview>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <h1>采购决策</h1>
              <p>让采购建议有据可循，由人做出决定</p>
            </div>
            <span className="status">
              <span />
              待人工审核 · 预览
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
                <Preview
                  variant={variant}
                  title="计算依据"
                  description="既有模拟数据中的只读业务事实，数量未重新计算。"
                  trigger={
                    <Action kind="ghost">
                      查看完整依据 <ArrowRight />
                    </Action>
                  }
                >
                  <Facts detailed />
                </Preview>
              </div>
              <div className="evidence-summary">
                需求是 <span className="quantity-inline">30 件</span>
                ，最低起订量是 <span className="quantity-inline">100 件</span>。
                <br />
                本次建议因此增加 <span className="quantity-inline">70 件</span>
                。
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
                  ，但最低起订量为{" "}
                  <span className="quantity-inline">100 件</span>
                  。因此，建议在基础需求上增加{" "}
                  <span className="quantity-inline">70 件</span>，采购{" "}
                  <span className="quantity-inline">100 件</span>。
                </p>
                <p className="prepared-note">预置解释 · 未调用 AI 服务</p>
                <Collapsible className="ai-disclosure">
                  <CollapsibleTrigger className="disclosure">
                    AI 在这里做什么 <ChevronDown />
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <p>
                      AI
                      只解释已有的计算结果，不计算或修改采购数量。是否采纳建议，最终由人工决定。
                    </p>
                  </CollapsibleContent>
                </Collapsible>
              </div>
              <div className="human-review" id="review">
                <div className="section-heading">
                  <h2>人工审核</h2>
                  <span className="role-label">待决定</span>
                </div>
                <p>建议供你参考，最终决策由人工完成。</p>
                <div className="review-actions">
                  <Preview
                    variant={variant}
                    title="人工审核预览"
                    description="视觉探索 · 不记录审核决定"
                    trigger={
                      <Action kind="primary">
                        预览人工审核 <ArrowRight />
                      </Action>
                    }
                  >
                    <p>
                      当前建议采购量为 100 件。最终数量和是否批准均由人工决定。
                    </p>
                    <Facts />
                    <p className="support">
                      本预览不记录批准，也不生成真实草稿。
                    </p>
                  </Preview>
                  <Preview
                    variant={variant}
                    title="采购申请草稿"
                    description="草稿状态预览 · 等待人工决定"
                    trigger={<Action>预览草稿</Action>}
                  >
                    <div className="draft-preview">
                      <FileText />
                      <h3>尚未形成采购申请草稿</h3>
                      <p>建议采购 100 件。批准数量尚未确定。</p>
                    </div>
                    <p>这不是采购订单，不会写入 ERP 或触发生产执行。</p>
                  </Preview>
                </div>
              </div>
              <div className="draft">
                <FileText />
                <div>
                  <h3>采购申请草稿</h3>
                  <p>尚未形成 · 等待人工决定</p>
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
                    仅状态预览，不是采购订单。
                  </TooltipContent>
                </Tooltip>
              </div>
              <p className="execution-note">人工批准 ≠ 生产执行</p>
            </section>
          </div>
        </main>
        <footer className="workspace-footer">
          <span>
            确定性计算 <ArrowRight /> AI 解释 <ArrowRight /> 人工决策
          </span>
          <span>仅展示原型 · 无 ERP 写入 / 采购订单 / 生产执行</span>
        </footer>
      </div>
    </section>
  );
}
function Specimen({ variant }: { variant: Variant }) {
  const [on, setOn] = useState(false);
  return (
    <Preview
      variant={variant}
      title="控件与状态"
      description="视觉样本 · 输入与切换仅在当前预览中保留，不保存业务数据。"
      trigger={<Action>控件与状态</Action>}
    >
      <div className="specimen">
        <Tabs defaultValue="control">
          <TabsList className="system-tabs" aria-label="样本显示">
            <TabsTrigger value="control">控件样本</TabsTrigger>
            <TabsTrigger value="material">材质样本</TabsTrigger>
          </TabsList>
          <TabsContent value="control">
            <p className="sample-caption">同一套控件，用于输入、选择与确认。</p>
          </TabsContent>
          <TabsContent value="material">
            <p className="sample-caption">
              暖白工作区、蓝灰决策面与柔和的临时浮层。
            </p>
          </TabsContent>
        </Tabs>
        <div className="sample-buttons">
          <Action kind="primary" onClick={() => setOn(!on)}>
            {on ? "已切换样本" : "主要操作样本"}
          </Action>
          <Action disabled>不可用样本</Action>
        </div>
        <label className="switch-row" htmlFor="sample-switch">
          开关样本
          <Switch
            id="sample-switch"
            className="system-switch"
            checked={on}
            onCheckedChange={setOn}
          />
        </label>
        <label htmlFor="sample-input">输入样本</label>
        <Input
          id="sample-input"
          className="system-input"
          placeholder="输入内容 · 不保存"
        />
        <label htmlFor="sample-textarea">备注样本</label>
        <Textarea
          id="sample-textarea"
          className="system-input"
          placeholder="记录想法 · 不保存"
        />
        <div className="material-scale">
          <span>基础表面</span>
          <span>次级表面</span>
          <span>浮层</span>
        </div>
        <p className="support">
          统一 150–220ms 过渡。支持键盘焦点与减少动态效果偏好。
        </p>
      </div>
    </Preview>
  );
}
function App() {
  const present = new URLSearchParams(location.search).has("present");
  return (
    <TooltipProvider>
      <div
        className="apple-page premium-page rich-page material"
        data-variant="C32"
      >
        {!present && (
          <div className="gallery">
            <span>
              C3.2 <span>Apple Premium Rich · 最终视觉审核</span>
            </span>
            <div>
              <Specimen variant="C32" />
              <a href="?present=1">
                仅看画面 <ArrowRight />
              </a>
            </div>
          </div>
        )}
        <Workspace variant="C32" />
        {!present && (
          <div className="concept-caption">
            <h2>克制的色彩，清晰的层次。</h2>
            <p>
              保留 C3 的信息架构与 Premium 气质。仅展示原型，等待 Human
              最终视觉审核。
            </p>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
