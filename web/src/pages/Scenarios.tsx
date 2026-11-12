import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download } from "lucide-react";
import { apiUrl, useApi, type Band } from "../api";
import { useDataset } from "../context";
import { integer, money, percent } from "../format";
import { Card, ErrorState, PageHead, Segmented, Skeleton, Slider, Stat } from "../components/ui";

interface ScenarioData {
  baseline: { expected_loss: number; mean_pd: number; exposure: number };
  scenario: { expected_loss: number; mean_pd: number; exposure: number };
  change: number;
  bands: (Band & { baseline: number; scenario: number })[];
}
interface Settings { odds: number; lgd: number; exposure: number }

const PRESETS: { key: string; label: string; settings: Settings }[] = [
  { key: "today", label: "As modelled", settings: { odds: 1, lgd: 0.45, exposure: 1 } },
  { key: "mild", label: "Mild downturn", settings: { odds: 1.5, lgd: 0.5, exposure: 1 } },
  { key: "severe", label: "Severe recession", settings: { odds: 3, lgd: 0.6, exposure: 1.1 } },
  { key: "boom", label: "Strong economy", settings: { odds: 0.75, lgd: 0.4, exposure: 1 } },
];

export default function Scenarios() {
  const { dataset } = useDataset();
  const [settings, setSettings] = useState<Settings>(PRESETS[0].settings);
  const [debounced, setDebounced] = useState(settings);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(settings), 120);
    return () => clearTimeout(timer);
  }, [settings]);
  const { data, error } = useApi<ScenarioData>(apiUrl("scenario", dataset, { ...debounced }));
  const preset = PRESETS.find((item) => JSON.stringify(item.settings) === JSON.stringify(settings))?.key ?? "";
  const update = (key: keyof Settings) => (value: number) => setSettings((previous) => ({ ...previous, [key]: value }));

  return (
    <>
      <PageHead title="What-if scenarios">
        Stress the portfolio: make defaults more likely, recover less from each one, or lend more. Results update as you move the sliders.
      </PageHead>
      <div className="grid cols-3">
        <Card title="Assumptions" action={null}>
          <div className="stack">
            <Segmented label="Preset" value={preset} onChange={(key) => {
              const chosen = PRESETS.find((item) => item.key === key);
              if (chosen) setSettings(chosen.settings);
            }} options={PRESETS.map(({ key, label }) => ({ key, label }))} />
            <Slider label="Default likelihood" value={settings.odds} min={0.25} max={4} step={0.25}
              display={`×${settings.odds.toFixed(2)}`} onChange={update("odds")}
              help="Multiplies each applicant's odds of default. ×2 roughly doubles risk for low-risk applicants." />
            <Slider label="Lost when someone defaults" value={settings.lgd} min={0} max={1} step={0.05}
              display={percent(settings.lgd, 0)} onChange={update("lgd")}
              help="Share of a defaulted loan that is never recovered." />
            <Slider label="Loan sizes" value={settings.exposure} min={0} max={2} step={0.1}
              display={`${settings.exposure >= 1 ? "+" : "−"}${Math.abs((settings.exposure - 1) * 100).toFixed(0)}%`}
              onChange={update("exposure")} help="Scales every outstanding loan amount." />
          </div>
        </Card>

        <div className="span-2 stack">
          {error ? <ErrorState message={error} /> : !data ? <Skeleton height={380} /> : (
            <>
              <div className="grid cols-3">
                <Stat label="Expected loss" value={money(data.scenario.expected_loss, true)}
                  note={`Modelled today: ${money(data.baseline.expected_loss, true)}`} />
                <Stat label="Change" tone={data.change > 0 ? "up" : data.change < 0 ? "down" : undefined}
                  value={`${data.change >= 0 ? "+" : "−"}${money(Math.abs(data.change), true)}`}
                  note={`${data.change >= 0 ? "+" : "−"}${percent(Math.abs(data.change) / data.baseline.expected_loss, 0)} vs. today`} />
                <Stat label="Average chance of default" value={percent(data.scenario.mean_pd)}
                  note={`Today: ${percent(data.baseline.mean_pd)}`} />
              </div>
              <Card title="How applicants move between risk bands" sub="Number of applicants in each band, today vs. this scenario">
                <div style={{ height: 260 }}>
                  <ResponsiveContainer>
                    <BarChart data={data.bands.map((band) => ({ ...band, label: band.name }))} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                      <Tooltip cursor={{ fill: "var(--surface-2)" }} formatter={(value) => [integer(Number(value)), undefined]} />
                      <Legend />
                      <Bar dataKey="baseline" name="Today" fill="var(--faint)" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="scenario" name="Scenario" fill="var(--brand)" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="small muted">Sensitivity analysis under stated assumptions — not a forecast of a real recession.</span>
                <a className="button" href={apiUrl("downloads/scenario", dataset, { ...debounced })}>
                  <Download size={16} aria-hidden /> Download scenario
                </a>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
