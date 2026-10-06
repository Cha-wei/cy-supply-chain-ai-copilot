import { scenario } from "./fixture";

// UI input validation only, following POC Design §10.4/§10.5 and
// snapshot_loader/exact_quantity.py. No recommendation computation or runtime call.
type Exact = { units: bigint; scale: number };
function parse(value: unknown): Exact | null {
  if (typeof value !== "string") return null;
  const match = /^[+-]?[0-9]+(?:\.[0-9]+)?$/.exec(value);
  if (!match || match[0] !== value) return null;
  const [whole, fraction = ""] = value.replace(/^[+-]/, "").split(".");
  return {
    units: BigInt(whole + fraction) * (value.startsWith("-") ? -1n : 1n),
    scale: fraction.length,
  };
}
function align(a: Exact, b: Exact) {
  const scale = Math.max(a.scale, b.scale);
  return {
    a: a.units * 10n ** BigInt(scale - a.scale),
    b: b.units * 10n ** BigInt(scale - b.scale),
    scale,
  };
}
export type InputErrors = { quantity?: string; reason?: string };
export function reasonError(reason: unknown): string | undefined {
  return typeof reason === "string" && reason.trim().length > 0
    ? undefined
    : "请填写原因，说明你的决定。";
}
export function validateOverride(
  quantity: unknown,
  reason: unknown,
): InputErrors {
  const errors: InputErrors = {};
  const value = parse(quantity);
  const moq = parse(scenario.moq);
  if (!value)
    errors.quantity =
      "请输入完整的十进制数量，不使用空格、千分位或科学计数法。";
  else if (value.units <= 0n) errors.quantity = "批准数量必须大于 0。";
  else if (!moq || moq.units < 0n)
    errors.quantity = "无法验证适用 MOQ，不能确认此决定。";
  else {
    const aligned = align(value, moq);
    if (aligned.a < aligned.b)
      errors.quantity = `批准数量不能低于适用 MOQ（${scenario.moq} 件）。`;
  }
  const reasonIssue = reasonError(reason);
  if (reasonIssue) errors.reason = reasonIssue;
  return errors;
}
// Exact display delta only; raw approved input is preserved separately without normalization.
export function decisionAdjustment(quantity: string): string {
  const value = parse(quantity),
    source = parse(scenario.recommended);
  if (!value || !source) return "";
  const { a, b, scale } = align(value, source);
  const delta = a - b;
  const digits = (delta < 0n ? -delta : delta)
    .toString()
    .padStart(scale + 1, "0");
  const body = scale
    ? `${digits.slice(0, -scale)}.${digits.slice(-scale)}`
    : digits;
  return `${delta > 0n ? "+" : delta < 0n ? "-" : ""}${body}`;
}
