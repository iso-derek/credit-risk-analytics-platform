import { useState } from "react";
import { CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Scatter, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import { Check, Download } from "lucide-react";
import { apiUrl, useApi, type Field } from "../api";
import { useDataset } from "../context";
import { formatValue, integer, percent } from "../format";
import { Card, ErrorState, PageHead, Skeleton } from "../components/ui";

interface Metric { key: string; label: string; kind: string; better: "higher" | "lower"; help: string }
interface ModelRow extends Record<string, unknown> { name: string; algorithm: string; variant: string; selected: boolean; best_ranking: boolean }
interface ModelsData {
  selected: string;
  best_ranking: string;
  metrics: Metric[];
  models: ModelRow[];
  reliability: { bin: string; predicted: number; observed: number; applicants: number }[];
  selection_test: { probability_choice: string; ranking_choice: string; brier_difference: number; lower_95: number; upper_95: number };
}
interface DriftData {
  score: { psi: number; shift_signal: string; mean_pd_change: number };
  features: (Field & { psi: number; signal: string; type: string })[];
}
const SIGNAL_TONE: Record<string, string> = {
  "Lower shift signal": "var(--good)",
  "Moderate shift signal": "var(--band-c)",
  "Higher shift signal": "var(--bad)",
};

export default function ModelQuality() {
  const { dataset } = useDataset();
  const models = useApi<ModelsData>(apiUrl("models", dataset));
  const drift = useApi<DriftData>(apiUrl("drift", dataset));
  const [showImportance, setShowImportance] = useState(false);
  const importance = useApi<{ rows: (Field & { importance: number })[] }>(showImportance ? apiUrl("models/importance", dataset) : null);

  if (models.error) return <ErrorState message={models.error} />;
  if (!models.data) return <Skeleton height={420} />;
  const data = models.data;
  const selected = data.models.find((model) => model.selected)!;
  const best = (metric: Metric) => {
    const values = data.models.map((model) => Number(model[metric.key]));
    return metric.better === "higher" ? Math.max(...values) : Math.min(...values);
  };

  return (
    <>
      <PageHead title="Model quality">
        {data.models.length} candidate models were trained. The one in use was chosen on a separate validation group before any of
        these test results were looked at.
      </PageHead>

      <div className="grid cols-4">
        <div className="card" style={{ background: "var(--brand)", color: "var(--brand-ink)", borderColor: "var(--brand)" }}>
          <div className="stat-label" style={{ color: "inherit", opacity: 0.85 }}>Model in use</div>
          <div className="stat-value" style={{ fontSize: 22 }}>{selected.algorithm}</div>
          <div className="small" style={{ opacity: 0.85 }}>{selected.variant} probabilities · lowest validation log loss</div>
        </div>
        {data.metrics.filter((metric) => ["roc_auc", "brier", "log_loss"].includes(metric.key)).map((metric) => (
          <div className="card" key={metric.key} title={metric.help}>
            <div className="stat-label">{metric.label}</div>
            <div className="stat-value">{formatValue(Number(selected[metric.key]), metric.kind)}</div>
            <div className="stat-note">{metric.better === "higher" ? "Higher is better" : "Lower is better"}</div>
          </div>
        ))}
      </div>

      <div className="grid cols-2 section">
        <Card title="Can the percentages be trusted?" sub="Predicted chance of default vs. how often people in that group really defaulted">
          <div style={{ height: 300 }}>
            <ResponsiveContainer>
              <ComposedChart data={data.reliability} margin={{ top: 8, right: 16, bottom: 16, left: 0 }}>
                <CartesianGrid />
                <XAxis type="number" dataKey="predicted" domain={[0, 1]} tickFormatter={(value) => percent(value, 0)}
                  label={{ value: "Predicted", position: "insideBottom", offset: -8 }} />
                <YAxis type="number" dataKey="observed" domain={[0, 1]} tickFormatter={(value) => percent(value, 0)}
                  label={{ value: "Actual", angle: -90, position: "insideLeft" }} />
                <ZAxis type="number" dataKey="applicants" range={[40, 400]} />
                <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--faint)" strokeDasharray="4 4" />
                <Line dataKey="observed" stroke="var(--brand)" dot={false} strokeWidth={2} isAnimationActive={false} />
                <Scatter dataKey="observed" fill="var(--brand)" />
                <Tooltip content={({ active, payload }) => {
                  const point = payload?.[0]?.payload as ModelsData["reliability"][number] | undefined;
                  return active && point ? (
                    <div className="tooltip">
                      <strong>{integer(point.applicants)} applicants</strong>
                      <div>Predicted {percent(point.predicted)} · actual {percent(point.observed)}</div>
                    </div>
                  ) : null;
                }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="small muted">Points on the dashed line mean the model's percentages match reality. Bigger dots hold more applicants.</p>
        </Card>

        <Card title="All candidate models" sub="Scored on the same unseen test applicants">
          <div className="scroll-x">
            <table className="table">
              <thead>
                <tr>
                  <th>Model</th>
                  {data.metrics.map((metric) => <th key={metric.key} className="right" title={metric.help}>{metric.label.replace(/ \(.*\)/, "")}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.models.map((model) => (
                  <tr key={model.name} style={model.selected ? { background: "var(--brand-soft)" } : undefined}>
                    <td>
                      <div style={{ fontWeight: 700 }}>{model.algorithm}</div>
                      <div className="small muted">{model.variant}{model.selected ? " · in use" : ""}</div>
                    </td>
                    {data.metrics.map((metric) => {
                      const value = Number(model[metric.key]);
                      return (
                        <td key={metric.key} className="right">
                          {formatValue(value, metric.kind)}
                          {value === best(metric) && <Check size={14} style={{ marginLeft: 4, color: "var(--good)" }} aria-label="best" />}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small muted">
            {data.selection_test.probability_choice === data.selection_test.ranking_choice
              ? "The same model wins on both probability accuracy and ranking."
              : `Choosing for probability accuracy instead of ranking changes the Brier score by ${data.selection_test.brier_difference.toFixed(4)} (95% range ${data.selection_test.lower_95.toFixed(4)} to ${data.selection_test.upper_95.toFixed(4)}).`}
          </p>
        </Card>
      </div>

      <div className="grid cols-2 section">
        <Card title="Has the data shifted?" sub="How much each input differs between training and test applicants"
          action={<a className="button" href={apiUrl("downloads/drift", dataset)}><Download size={16} aria-hidden /> CSV</a>}>
          {drift.error ? <ErrorState message={drift.error} /> : !drift.data ? <Skeleton height={260} /> : (
            <>
              <p style={{ marginTop: 0 }}>
                Overall score shift: <strong style={{ color: SIGNAL_TONE[drift.data.score.shift_signal] }}>
                  {drift.data.score.shift_signal.replace(" shift signal", "").toLowerCase()}</strong>{" "}
                <span className="muted small">(PSI {drift.data.score.psi.toFixed(3)})</span>
              </p>
              <div className="stack" style={{ gap: 10 }}>
                {drift.data.features.slice(0, 8).map((feature) => (
                  <div key={feature.key}>
                    <div className="row" style={{ justifyContent: "space-between" }}>
                      <span>{feature.label}</span>
                      <span className="small num muted">{feature.psi.toFixed(3)}</span>
                    </div>
                    <div className="meter" style={{ marginTop: 4 }}>
                      <span style={{ width: `${Math.min(feature.psi / 0.25, 1) * 100}%`, background: SIGNAL_TONE[feature.signal] }} />
                    </div>
                  </div>
                ))}
              </div>
              <p className="small muted">Below 0.10 is a small shift, 0.10–0.25 moderate, above 0.25 large. A same-period check, not live monitoring.</p>
            </>
          )}
        </Card>

        <Card title="Which inputs matter most?" sub="How much ranking accuracy drops when each input is scrambled">
          {!showImportance ? (
            <button className="button button-primary" type="button" onClick={() => setShowImportance(true)}>Calculate importance</button>
          ) : importance.error ? <ErrorState message={importance.error} /> : !importance.data ? <Skeleton height={260} /> : (
            <div className="stack" style={{ gap: 10 }}>
              {importance.data.rows.slice(0, 10).map((row) => {
                const top = Math.max(...importance.data!.rows.map((item) => item.importance), 1e-9);
                return (
                  <div key={row.key}>
                    <div className="row" style={{ justifyContent: "space-between" }}>
                      <span>{row.label}</span>
                      <span className="small num muted">{row.importance.toFixed(3)}</span>
                    </div>
                    <div className="meter" style={{ marginTop: 4 }}>
                      <span style={{ width: `${Math.max(row.importance / top, 0) * 100}%`, background: "var(--brand)" }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>
      <div className="row section">
        <a className="button" href={apiUrl("downloads/research", dataset)}><Download size={16} aria-hidden /> Download full research bundle</a>
      </div>
    </>
  );
}
