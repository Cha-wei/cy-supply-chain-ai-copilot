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
import { Tabs, TabsList, TabsTrigger } from "../concepts/ui/tabs";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./ui/collapsible";
import { Switch } from "./ui/switch";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import "@fontsource-variable/noto-sans-sc";
import "@fontsource-variable/manrope";
import "./styles.css";
const variants = {
  C1: ["Apple Clean", "明净", "明亮中性底色、近乎隐形的分隔与精确留白。"],
  C2: ["Apple Layered", "层叠", "半透明导航、柔和材质与有分寸的空间深度。"],
  C3: ["Apple Premium", "雅致", "深色导航、温润连续表面与更从容的排版节奏。"],
} as const;
type Variant = keyof typeof variants;
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
              <p>MOQ 高于当前缺口 · 只读模拟场景</p>
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
              <div className="recommendation">
                <div>
                  <h2>当前采购建议</h2>
                  <p className="support">
                    <ShieldCheck />
                    确定性计算结果
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
              <div className="section-heading">
                <h2>计算依据</h2>
                <Preview
                  variant={variant}
                  title="计算依据"
                  description="既有模拟数据中的只读业务事实，数量未重新计算。"
                  trigger={
                    <Action kind="ghost">
                      查看详情 <ArrowRight />
                    </Action>
                  }
                >
                  <Facts detailed />
                </Preview>
              </div>
              <Facts />
              <Collapsible className="source">
                <CollapsibleTrigger className="disclosure">
                  查看数据来源说明 <ChevronDown />
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
                <h3>缺口 30，为什么建议采购 100？</h3>
                <p>
                  基础采购需求为 30 件。由于最低起订量为 100 件，MOQ 调整增加 70
                  件，最终建议采购 100 件。
                </p>
                <p className="prepared-note">预置解释 · 未调用 AI 服务</p>
                <Preview
                  variant={variant}
                  title="AI 解释的职责"
                  description="预置解释文案 · 未调用 AI 服务"
                  trigger={
                    <Action kind="ghost">
                      了解解释边界 <ArrowRight />
                    </Action>
                  }
                >
                  <p>
                    当前缺口与基础采购需求均为 30 件。适用 MOQ 为 100 件，因此
                    MOQ 调整为 70 件，建议采购量为 100 件。
                  </p>
                  <p>AI 只负责解释既有结果，最终决策权属于人工。</p>
                </Preview>
              </div>
              <div className="human-review" id="review">
                <div className="section-heading">
                  <h2>人工审核</h2>
                  <span className="role-label">待决定</span>
                </div>
                <p>最终决策由人工完成。阅读依据与解释后，再形成采购决定。</p>
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
                  <p>
                    尚未形成 <span>· DRAFT 预览</span>
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
          统一 180–220ms 过渡。支持键盘焦点与减少动态效果偏好。
        </p>
      </div>
    </Preview>
  );
}
function App() {
  const query = new URLSearchParams(location.search);
  const key = query.get("variant");
  const [variant, setVariant] = useState<Variant>(
    key && key in variants ? (key as Variant) : "C1",
  );
  return (
    <TooltipProvider>
      <div className="apple-page material" data-variant={variant}>
        {!query.has("present") && (
          <div className="gallery">
            <span>
              Concept C <span>整体视觉系统</span>
            </span>
            <Tabs
              value={variant}
              onValueChange={(v) => {
                setVariant(v as Variant);
                history.replaceState(null, "", `?variant=${v}`);
              }}
            >
              <TabsList className="system-tabs">
                {Object.entries(variants).map(([id, v]) => (
                  <TabsTrigger value={id} key={id}>
                    {id} {v[1]}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
            <div>
              <Specimen variant={variant} />
              <a href={`?variant=${variant}&present=1`}>
                仅看画面 <ArrowRight />
              </a>
            </div>
          </div>
        )}
        <Workspace variant={variant} />
        {!query.has("present") && (
          <div className="concept-caption">
            <h2>
              {variant} — {variants[variant][0]}
            </h2>
            <p>{variants[variant][2]} 三个方向共享同一信息架构与业务事实。</p>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
