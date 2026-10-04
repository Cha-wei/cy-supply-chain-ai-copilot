import { useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronRight,
  FileText,
  Layers2,
  ShieldCheck,
  X,
} from "lucide-react";
import { scenario as f } from "../fixture";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./ui/tabs";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "./ui/dialog";
import "@fontsource-variable/noto-sans-sc";
import "@fontsource-variable/manrope";
import "./styles.css";

const concepts = {
  A: {
    name: "决策画布",
    en: "Apple Decision Canvas",
    summary: "让差异成为主角。以留白和比例，讲清 30 到 100。",
  },
  B: {
    name: "空间供应链",
    en: "Spatial Supply Chain",
    summary: "让关系浮出平面。从供需缺口，走向有依据的采购建议。",
  },
  C: {
    name: "决策工作台",
    en: "Executive Decision Workspace",
    summary: "让依据与判断并置。左侧理解结果，右侧形成决定。",
  },
};
type Concept = keyof typeof concepts;
const factLabels = [
  "当前缺口",
  "基础采购需求",
  "最低起订量 MOQ",
  "MOQ 调整",
  "建议采购量",
];
function Evidence({ className = "" }: { className?: string }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          className={"text-action h-11 px-0 " + className}
        >
          查看计算依据 <ArrowUpRight size={16} />
        </Button>
      </DialogTrigger>
      <DialogContent className="concept-dialog rounded-2xl border-0 p-8">
        <DialogTitle>每一个数量，都有依据。</DialogTitle>
        <DialogDescription>
          只读模拟数据；未执行实时计算或数据校验。
        </DialogDescription>
        <dl className="dialog-facts">
          {f.facts.map(([name, value], i) => (
            <div key={name}>
              <dt>
                {factLabels[i]}
                <code>{name}</code>
              </dt>
              <dd>
                {value}
                <small>件</small>
              </dd>
            </div>
          ))}
        </dl>
        <p className="text-sm text-muted-foreground">
          确定性系统计算，AI 只负责解释。当前展示不构成运行时证据。
        </p>
      </DialogContent>
    </Dialog>
  );
}
function Explain() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost" className="text-action h-11 px-0">
          查看 AI 解释 <ArrowUpRight size={16} />
        </Button>
      </DialogTrigger>
      <DialogContent className="concept-dialog rounded-2xl border-0 p-8">
        <DialogTitle>为什么缺口只有 30，却建议采购 100？</DialogTitle>
        <DialogDescription>
          以下为预制解释文案，没有调用 AI 服务。
        </DialogDescription>
        <p className="text-base leading-8">
          当前缺口与基础采购需求均为 <b>30 件</b>。适用最低起订量为{" "}
          <b>100 件</b>，因此确定性计算增加 <b>70 件</b> MOQ 调整，形成{" "}
          <b>100 件</b>采购建议。
        </p>
        <div className="dialog-rule">30 + 70 = 100</div>
        <p className="text-sm leading-7 text-muted-foreground">
          AI 不参与采购数量计算。是否采纳建议，由人工决定。
        </p>
      </DialogContent>
    </Dialog>
  );
}
function ReviewPreview() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button className="review-button h-11 rounded-full px-6">
          预览人工审核 <ArrowRight size={16} />
        </Button>
      </DialogTrigger>
      <DialogContent className="concept-dialog rounded-2xl border-0 p-8">
        <DialogTitle>最终决策，由你完成。</DialogTitle>
        <DialogDescription>
          仅展示审核构图，不记录批准，也不生成真实草稿。
        </DialogDescription>
        <div className="dialog-rule">建议采购 {f.recommended} 件</div>
        <p className="text-base leading-8">
          请根据建议与计算依据作出判断。本画面仅预览审核状态，不提供批准操作；人工批准也不代表执行采购。
        </p>
        <div className="draft-inline">
          <FileText size={20} />
          <div>
            <b>采购申请草稿 · 状态预览</b>
            <p>待人工决定 · DRAFT / 临时</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
function Header() {
  return (
    <header className="product-header">
      <a
        href="concepts.html?concept=A"
        className="brand"
        aria-label="供应链 AI Copilot"
      >
        <span className="brandmark">
          CY<span>·</span>
        </span>
        <span>
          供应链 <b>AI Copilot</b>
        </span>
      </a>
      <span className="header-context">采购决策 / 模拟场景</span>
      <span className="simulation">
        <span className="status-dot" />
        SIMULATED <span className="hidden sm:inline">· 仅展示原型</span>
      </span>
    </header>
  );
}
function Footer() {
  return (
    <footer className="product-footer">
      <span>
        系统计算<span className="footer-divider">/</span>AI 解释
        <span className="footer-divider">/</span>人工决策
      </span>
      <span>不写入 ERP · 不创建采购订单 · 不执行生产</span>
      <span>仅供展示 · 非运行时证据</span>
    </footer>
  );
}
function Draft({ dark = false }: { dark?: boolean }) {
  return (
    <div className={"draft-inline " + (dark ? "draft-dark" : "")}>
      <FileText size={20} strokeWidth={1.5} />
      <div>
        <b>
          采购申请草稿 <span>状态预览</span>
        </b>
        <p>待人工决定 · DRAFT / 临时</p>
      </div>
      <span className="draft-end">非采购订单</span>
    </div>
  );
}
function Authority() {
  return (
    <span className="authority-line">
      <ShieldCheck size={16} />
      确定性计算 <span>·</span> AI 不参与数量计算
    </span>
  );
}
function A() {
  return (
    <article className="artboard concept-a">
      <Header />
      <main className="a-main">
        <div className="a-heading">
          <div>
            <h1>从缺口，到有依据的采购。</h1>
            <p>缺口与建议之间的 70 件，来自最低起订量。</p>
          </div>
          <span className="scenario-note">
            <Check size={15} />
            模拟快照已接受
            <br />
            <span>只读模拟数据 · 校验通过状态预览</span>
          </span>
        </div>
        <section
          className="a-equation"
          aria-label="当前缺口30加MOQ调整70等于建议采购100"
        >
          <div className="equation-item">
            <span>当前缺口</span>
            <strong>
              {f.shortage}
              <small>件</small>
            </strong>
            <p>基础采购需求 {f.base} 件</p>
          </div>
          <span className="operator">+</span>
          <div className="equation-item adjustment">
            <span>MOQ 调整</span>
            <strong>
              {f.adjustment}
              <small>件</small>
            </strong>
            <p>满足最低起订量</p>
          </div>
          <span className="operator">=</span>
          <div className="equation-item total">
            <span>建议采购量</span>
            <strong>
              {f.recommended}
              <small>件</small>
            </strong>
            <p>最低起订量 MOQ {f.moq} 件</p>
          </div>
        </section>
        <div className="a-rationale">
          <Authority />
          <Evidence />
        </div>
        <div className="a-bottom">
          <section className="a-explain">
            <div className="section-heading">
              <h2>理解这份建议</h2>
              <span>AI 仅解释</span>
            </div>
            <h3>
              为什么缺口只有 30，
              <br />
              却建议采购 100？
            </h3>
            <p>数量由规则计算。AI 让依据更易理解。</p>
            <Explain />
          </section>
          <section className="a-review">
            <div className="section-heading">
              <h2>最终决策，由你完成。</h2>
              <span>人工审核</span>
            </div>
            <div className="review-row">
              <p>
                建议采购 <b>100 件</b>。<br />
                是否采纳，仍需人工判断。
              </p>
              <ReviewPreview />
            </div>
            <Draft />
          </section>
        </div>
      </main>
      <Footer />
    </article>
  );
}
function B() {
  return (
    <article className="artboard concept-b">
      <Header />
      <main className="b-main">
        <div className="b-heading">
          <div>
            <h1>看清数量背后的关系。</h1>
            <p>从供需缺口，经过采购策略，形成可解释的建议。</p>
          </div>
          <Authority />
        </div>
        <section
          className="spatial-stage"
          aria-label="供需、缺口、采购策略与采购建议的关系"
        >
          <div className="spatial-origin">
            <div className="origin-input">
              <Layers2 size={18} />
              <div>
                <b>需求 / 供应</b>
                <p>受控模拟场景 · 只读</p>
              </div>
            </div>
            <div className="origin-stem" />
            <div className="shortage-node">
              <span>当前缺口</span>
              <strong>
                {f.shortage}
                <small>件</small>
              </strong>
              <p>基础采购需求 {f.base} 件</p>
            </div>
          </div>
          <div className="path-bridge">
            <span>采购策略</span>
            <div />
            <ArrowRight size={20} />
          </div>
          <div className="policy-node">
            <span>最低起订量</span>
            <strong>{f.moq}</strong>
            <span>MOQ · 件</span>
            <div className="policy-adjust">
              补足 <b>+{f.adjustment} 件</b>
            </div>
          </div>
          <div className="path-bridge second">
            <span>经 MOQ 调整</span>
            <div />
            <ArrowRight size={20} />
          </div>
          <div className="result-plane">
            <span className="result-label">当前采购建议</span>
            <strong>
              {f.recommended}
              <small>件</small>
            </strong>
            <div className="plane-equation">
              30 <span>+</span> 70 <span>=</span> 100
            </div>
            <p>由确定性规则形成</p>
            <Evidence />
          </div>
        </section>
        <div className="b-lower">
          <section className="b-explain">
            <h2>30 → 100，AI 帮你读懂。</h2>
            <p>
              70 件调整来自 MOQ，而非 AI 的判断。
              <br />
              AI 只负责解释，最终决策权属于人工。
            </p>
            <Explain />
          </section>
          <section className="b-review">
            <div className="review-row">
              <div>
                <h2>建议已清晰，决定留给你。</h2>
                <p>人工审核 · 本轮仅展示</p>
              </div>
              <ReviewPreview />
            </div>
            <Draft dark />
          </section>
        </div>
      </main>
      <Footer />
    </article>
  );
}
function C() {
  return (
    <article className="artboard concept-c">
      <Header />
      <main className="c-main">
        <div className="c-heading">
          <div>
            <h1>采购建议，等待你的判断。</h1>
            <p>MOQ 高于缺口 · 模拟采购场景</p>
          </div>
          <span className="c-state">
            <span className="status-dot" />
            待人工审核 · 状态预览
          </span>
        </div>
        <div className="executive-grid">
          <section className="c-evidence">
            <div className="c-result">
              <div>
                <h2>当前采购建议</h2>
                <Authority />
              </div>
              <strong>
                {f.recommended}
                <small>件</small>
              </strong>
            </div>
            <div className="c-equation">
              <span>
                当前缺口 <b>30</b>
              </span>
              <span>+</span>
              <span>
                MOQ 调整 <b>70</b>
              </span>
              <span>=</span>
              <span>
                建议 <b>100</b>
              </span>
            </div>
            <div className="c-table-heading">
              <h2>计算依据</h2>
              <span>确定性事实 · 只读</span>
            </div>
            <dl className="c-facts">
              {f.facts.slice(0, 4).map(([key, value], i) => (
                <div key={key}>
                  <dt>{factLabels[i]}</dt>
                  <dd>
                    {i === 3 ? "+" : ""}
                    {value}
                    <small>件</small>
                  </dd>
                </div>
              ))}
            </dl>
            <Evidence />
            <p className="c-source">
              <Check size={15} />
              模拟快照 · 只读数据 · 校验通过状态预览
            </p>
          </section>
          <aside className="c-decision">
            <section>
              <div className="section-heading">
                <h2>AI 解释</h2>
                <span>仅解释 · 预制文案</span>
              </div>
              <h3>为什么缺口 30，建议却是 100？</h3>
              <p className="c-answer">
                缺口已低于最低起订量，新增的 70 件来自 MOQ 调整。
                <b>AI 不参与采购数量计算。</b>
              </p>
              <Explain />
            </section>
            <section className="c-human">
              <div className="section-heading">
                <h2>人工审核</h2>
                <span>待决定</span>
              </div>
              <p>
                最终决策权属于人工。
                <br />
                审核建议与依据，再决定是否采纳。
              </p>
              <ReviewPreview />
            </section>
            <Draft />
            <p className="c-boundary">人工批准 ≠ 生产执行</p>
          </aside>
        </div>
      </main>
      <Footer />
    </article>
  );
}
function App() {
  const initial = new URLSearchParams(location.search).get(
    "concept",
  ) as Concept;
  const [concept, setConcept] = useState<Concept>(
    initial in concepts ? initial : "A",
  );
  return (
    <Tabs
      value={concept}
      onValueChange={(v) => {
        setConcept(v as Concept);
        history.replaceState(null, "", `?concept=${v}`);
      }}
      className="concept-gallery"
    >
      <div className="gallery-bar">
        <div>
          <b>
            视觉探索 <span>v0.2</span>
          </b>
          <span className="gallery-status">待人工选型 · 非完整产品</span>
        </div>
        <TabsList className="concept-switcher" aria-label="选择视觉方向">
          {Object.entries(concepts).map(([key, item]) => (
            <TabsTrigger key={key} value={key}>
              {key}
              <span>{item.name}</span>
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      <TabsContent value="A">
        <A />
      </TabsContent>
      <TabsContent value="B">
        <B />
      </TabsContent>
      <TabsContent value="C">
        <C />
      </TabsContent>
      <div className="concept-caption">
        <b>
          Concept {concept} / {concepts[concept].en}
        </b>
        <p>{concepts[concept].summary}</p>
        <span>
          真实客户验证未执行 · 业务价值未证明 · 不宣称生产就绪或 POC SUCCESS
        </span>
      </div>
    </Tabs>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
