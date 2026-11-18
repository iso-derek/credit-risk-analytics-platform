// One place that decides how every kind of value is shown to people.
export type Kind = "money" | "percent" | "integer" | "number" | "years" | "months" | "score" | "text" | "flag" | "ratio" | "repayment";

let currency = "USD";
export function setCurrency(code: string) {
  currency = code;
}

export function money(value: number | null | undefined, compact = false): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: compact ? "compact" : "standard",
    maximumFractionDigits: compact ? 1 : 0,
  }).format(value);
}

export function percent(value: number | null | undefined, digits = 1): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function points(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${Math.abs(value * 100).toFixed(1)} pts`;
}

export function integer(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

// UCI repayment status codes: -2 no balance, -1 paid in full, 0 minimum paid, n = n months late.
function repayment(value: unknown): string {
  const code = Number(value);
  if (Number.isNaN(code)) return String(value);
  if (code <= -2) return "No balance due";
  if (code === -1) return "Paid in full";
  if (code === 0) return "Paid minimum";
  return `${code} month${code === 1 ? "" : "s"} late`;
}

export function formatValue(value: unknown, kind: Kind | string): string {
  if (value == null || value === "") return "—";
  if (kind === "repayment") return repayment(value);
  if (typeof value !== "number") return String(value);
  switch (kind) {
    case "money":
      return money(value);
    case "percent":
      return percent(value);
    case "integer":
    case "score":
      return integer(value);
    case "years":
      return `${Number.isInteger(value) ? value : value.toFixed(1)} yrs`;
    case "months":
      return `${integer(value)} months`;
    case "flag":
      return value ? "Yes" : "No";
    case "ratio":
      return value.toFixed(3);
    default:
      return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
  }
}

export const BAND_COLORS: Record<string, string> = {
  A: "var(--band-a)",
  B: "var(--band-b)",
  C: "var(--band-c)",
  D: "var(--band-d)",
  E: "var(--band-e)",
};
