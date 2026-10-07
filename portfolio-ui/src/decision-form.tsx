import { useRef, useState } from "react";
import { Button } from "./ui/button";
import { useFacts, useRuntime } from "./runtime";
import {
  type InputErrors,
} from "./decision-input";

export function DecisionForm({
  kind,
  onCancel,
  onConfirm,
}: {
  kind: "override" | "reject";
  onCancel: () => void;
  onConfirm: (quantity: string, reason: string) => Promise<InputErrors | undefined>;
}) {
  const scenario = useFacts();
  const { busy } = useRuntime();
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");
  const [errors, setErrors] = useState<InputErrors>({});
  const quantityField = useRef<HTMLInputElement>(null);
  const reasonField = useRef<HTMLTextAreaElement>(null);
  const override = kind === "override";
  async function confirm() {
    const next = await onConfirm(quantity, reason);
    if (next) {
      setErrors(next);
      (next.quantity ? quantityField.current : reasonField.current)?.focus();
    }
  }
  return (
    <form
      className="decision-form"
      noValidate
      onSubmit={(e) => e.preventDefault()}
    >
      <dl className="facts decision-source">
        <div>
          <dt>系统建议</dt>
          <dd>
            {scenario.recommended}
            <span>件</span>
          </dd>
        </div>
      </dl>
      {override && (
        <div className="decision-field">
          <label htmlFor="approved-quantity">
            批准数量 <span aria-hidden="true">*</span>
          </label>
          <div className="quantity-field">
            <input
              ref={quantityField}
              id="approved-quantity"
              type="text"
              inputMode="decimal"
              required
              autoComplete="off"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              aria-invalid={!!errors.quantity}
              aria-describedby={`quantity-help${errors.quantity ? " quantity-error" : ""}`}
            />
            <span>件</span>
          </div>
          <p id="quantity-help" className="field-help">
            适用 MOQ 为 {scenario.moq} 件。原建议不变，输入不会自动取整。
          </p>
          {errors.quantity && (
            <p id="quantity-error" className="field-error" role="alert">
              {errors.quantity}
            </p>
          )}
        </div>
      )}
      <div className="decision-field">
        <label htmlFor="decision-reason">
          {override ? "调整原因" : "拒绝原因"} <span aria-hidden="true">*</span>
        </label>
        <textarea
          ref={reasonField}
          id="decision-reason"
          rows={3}
          required
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          aria-invalid={!!errors.reason}
          aria-describedby={errors.reason ? "reason-error" : undefined}
        />
        {errors.reason && (
          <p id="reason-error" className="field-error" role="alert">
            {errors.reason}
          </p>
        )}
      </div>
      <p className="support">
        {override
          ? "确认后，草稿采用你批准的数量。"
          : "拒绝后不形成已批准草稿。"}
        Python 记录当前模拟会话；刷新保留，服务重启后丢失。
      </p>
      <p className="support">
        人工批准 ≠ 生产执行 · 不写入 ERP · 不创建采购订单
      </p>
      <div className="review-actions">
        <Button
          type="button"
          className="system-button secondary"
          onClick={onCancel}
        >
          取消
        </Button>
        <Button
          type="button"
          className={`system-button ${override ? "primary" : "destructive"}`}
          disabled={busy}
          onClick={() => void confirm()}
        >
          {override ? "确认修改并批准" : "确认拒绝"}
        </Button>
      </div>
    </form>
  );
}
