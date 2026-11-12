import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiUrl, useApi } from "../api";
import { useDataset } from "../context";
import { integer, percent } from "../format";
import { Card, ErrorState, Notice, PageHead, Segmented, Skeleton, Slider } from "../components/ui";

interface GroupRow {
  group: string;
  applicants: number;
  defaults: number;
  status: string;
  mean_predicted_pd: number | null;
  observed_default_rate: number | null;
  observed_rate_ci_low: number | null;
  observed_rate_ci_high: number | null;
  flag_rate: number | null;
  true_positive_rate: number | null;
  false_positive_rate: number | null;
}
interface FairnessData {
  options: { key: string; label: string }[];
  group: string;
  second: string | null;
  rows: GroupRow[];
}

export default function Fairness() {
  const { dataset } = useDataset();
  const [group, setGroup] = useState("");
  const [second, setSecond] = useState("");
  const [threshold, setThreshold] = useState(0.2);
  const [minSize, setMinSize] = useState(30);
  const [settings, setSettings] = useState({ threshold, minSize });
  useEffect(() => {
    const timer = setTimeout(() => setSettings({ threshold, minSize }), 200);
    return () => clearTimeout(timer);
  }, [threshold, minSize]);
  useEffect(() => { setGroup(""); setSecond(""); }, [dataset]);

  const { data, error } = useApi<FairnessData>(apiUrl("fairness", dataset, {
    group, second, threshold: settings.threshold, min_size: settings.minSize,
  }));
  const activeGroup = group || data?.group || "";
  const reported = data?.rows.filter((row) => row.status === "Reported") ?? [];
  const suppressed = data?.rows.filter((row) => row.status !== "Reported") ?? [];

  return (
    <>
      <PageHead title="Fairness check">
        Does the model's risk estimate hold up equally well across different groups of people? Compare predicted and actual default
        rates, and how often each group would be flagged.
      </PageHead>
      <Notice tone="warn">
        A diagnostic, not a legal fairness assessment. Group fields are not model inputs for the public dataset, but leaving them out
        does not by itself make a model fair.
      </Notice>

      {error ? <div className="section"><ErrorState message={error} /></div> : !data ? <div className="section"><Skeleton height={400} /></div> : data.options.length === 0 ? (
        <p className="muted section">This dataset has no supported group fields.</p>
      ) : (
        <>
          <Card className="section">
            <div className="grid cols-2">
              <div className="stack">
                <div>
                  <div className="stat-label" style={{ marginBottom: 6 }}>Compare groups by</div>
                  <Segmented label="Group" value={activeGroup} onChange={(key) => { setGroup(key); if (key === second) setSecond(""); }}
                    options={data.options} />
                </div>
                <div>
                  <div className="stat-label" style={{ marginBottom: 6 }}>Split further by (optional)</div>
                  <Segmented label="Second group" value={second} onChange={setSecond}
                    options={[{ key: "", label: "None" }, ...data.options.filter((option) => option.key !== activeGroup)]} />
                </div>
              </div>
              <div className="stack">
                <Slider label="Flag for review above" value={threshold} min={0.05} max={0.8} step={0.05}
                  display={percent(threshold, 0)} onChange={setThreshold} help="Applicants above this chance of default would be flagged." />
                <Slider label="Smallest group to report" value={minSize} min={10} max={100} step={5}
                  display={`${minSize} people`} onChange={setMinSize} help="Smaller groups are hidden because their results are unreliable." />
              </div>
            </div>
          </Card>

          <div className="grid cols-2 section">
            <Card title="Predicted vs. actual default rate" sub="Big gaps mean the model is miscalibrated for that group">
              {reported.length === 0 ? <p className="muted">No group is large enough to report.</p> : (
                <div style={{ height: Math.max(260, reported.length * 46) }}>
                  <ResponsiveContainer>
                    <BarChart data={reported} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 8 }}>
                      <CartesianGrid horizontal={false} />
                      <XAxis type="number" domain={[0, 1]} tickFormatter={(value) => percent(value, 0)} tickLine={false} axisLine={false} />
                      <YAxis type="category" dataKey="group" width={150} tickLine={false} axisLine={false} />
                      <Tooltip cursor={{ fill: "var(--surface-2)" }} formatter={(value) => percent(Number(value))} />
                      <Legend />
                      <Bar dataKey="mean_predicted_pd" name="Predicted" fill="var(--brand)" radius={[0, 4, 4, 0]} />
                      <Bar dataKey="observed_default_rate" name="Actual" fill="var(--band-c)" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>

            <Card title="Who gets flagged" sub={`Share of each group above ${percent(settings.threshold, 0)} risk`}>
              <div className="scroll-x">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Group</th>
                      <th className="right">People</th>
                      <th className="right">Flagged</th>
                      <th className="right" title="Of those who defaulted, share that were flagged">Defaulters caught</th>
                      <th className="right" title="Of those who repaid, share wrongly flagged">Wrongly flagged</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reported.map((row) => (
                      <tr key={row.group}>
                        <td>{row.group}</td>
                        <td className="right">{integer(row.applicants)}</td>
                        <td className="right">{percent(row.flag_rate)}</td>
                        <td className="right">{percent(row.true_positive_rate)}</td>
                        <td className="right">{percent(row.false_positive_rate)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {suppressed.length > 0 && (
                <p className="small muted">
                  Not shown ({suppressed.length}): {suppressed.map((row) => `${row.group} (${integer(row.applicants)})`).join(", ")} — too small or
                  only one outcome observed.
                </p>
              )}
            </Card>
          </div>
        </>
      )}
    </>
  );
}
