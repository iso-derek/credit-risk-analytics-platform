import type { ReactNode } from "react";
import { AlertTriangle, Info } from "lucide-react";
import { BAND_COLORS, percent } from "../format";

export function PageHead({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="page-head">
      <h1>{title}</h1>
      {children && <p>{children}</p>}
    </header>
  );
}

export function Card({ title, sub, action, children, className = "" }: {
  title?: string; sub?: ReactNode; action?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <div className="card-head">
          <div>
            {title && <h2>{title}</h2>}
            {sub && <div className="card-sub">{sub}</div>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Stat({ label, value, note, tone }: { label: string; value: ReactNode; note?: ReactNode; tone?: "up" | "down" }) {
  return (
    <div className="card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${tone === "up" ? "delta-up" : tone === "down" ? "delta-down" : ""}`}>{value}</div>
      {note && <div className="stat-note">{note}</div>}
    </div>
  );
}

export function BandBadge({ letter, name }: { letter: string; name?: string }) {
  const color = BAND_COLORS[letter] ?? "var(--faint)";
  return (
    <span className="badge" style={{ background: `color-mix(in srgb, ${color} 16%, transparent)`, color }}>
      <span className="band-dot" style={{ background: color }} />
      {name ?? letter}
    </span>
  );
}

export function Segmented<T extends string>({ options, value, onChange, label }: {
  options: { key: T; label: string }[]; value: T; onChange: (value: T) => void; label: string;
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option.key} type="button" aria-pressed={option.key === value} onClick={() => onChange(option.key)}>
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "warn"; children: ReactNode }) {
  const Icon = tone === "warn" ? AlertTriangle : Info;
  return (
    <div className={`notice notice-${tone}`} role={tone === "warn" ? "alert" : undefined}>
      <Icon size={18} style={{ flexShrink: 0, marginTop: 2 }} aria-hidden />
      <div>{children}</div>
    </div>
  );
}

export function Skeleton({ height = 120 }: { height?: number }) {
  return <div className="skeleton" style={{ height }} aria-label="Loading" />;
}

export function ErrorState({ message }: { message: string }) {
  return <Notice tone="warn">{message}</Notice>;
}

export function Slider({ label, value, min, max, step, onChange, display, help }: {
  label: string; value: number; min: number; max: number; step: number;
  onChange: (value: number) => void; display: string; help?: string;
}) {
  return (
    <label className="slider">
      <span className="slider-top">
        <span className="stat-label">{label}</span>
        <span className="slider-value">{display}</span>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
      {help && <span className="small muted">{help}</span>}
    </label>
  );
}

/** Half-circle gauge for a default probability. */
export function RiskGauge({ value, letter }: { value: number; letter: string }) {
  const angle = Math.PI * (1 - Math.min(Math.max(value, 0), 1));
  const x = 100 + 80 * Math.cos(angle);
  const y = 100 - 80 * Math.sin(angle);
  const color = BAND_COLORS[letter] ?? "var(--brand)";
  const large = value > 0.5 ? 1 : 0;
  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 200 116" width="220" role="img" aria-label={`Default probability ${percent(value)}`}>
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="var(--surface-2)" strokeWidth="16" strokeLinecap="round" />
        {value > 0.001 && (
          <path d={`M20 100 A80 80 0 ${large} 1 ${x.toFixed(2)} ${y.toFixed(2)}`} fill="none" stroke={color} strokeWidth="16" strokeLinecap="round" />
        )}
        <text x="100" y="92" textAnchor="middle" fontSize="30" fontWeight="800" fill="var(--ink)">{percent(value)}</text>
        <text x="100" y="112" textAnchor="middle" fontSize="11" fill="var(--muted)">chance of default</text>
      </svg>
    </div>
  );
}
