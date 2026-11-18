import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiUrl, useApi, type Band } from "../api";
import { useDataset } from "../context";
import { BAND_COLORS, integer, money, percent } from "../format";
import { BandBadge, Card, ErrorState, Notice, PageHead, Segmented, Skeleton, Stat } from "../components/ui";

interface BandRow extends Band {
  applicants: number;
  share: number;
  mean_pd: number | null;
  observed_default_rate: number | null;
  exposure: number;
  expected_loss: number;
}
interface OverviewData {
  kpis: { applicants: number; mean_pd: number; observed_default_rate: number; exposure: number; expected_loss: number };
  histogram: ({ from: number; to: number } & Record<string, number>)[];
  bands: BandRow[];
  segment_options: { key: string; label: string }[];
}
interface SegmentRow {
  segment: string;
  applicants: number;
  total_exposure: number;
  mean_predicted_pd: number;
  expected_loss: number;
  expected_loss_share: number;
  exposure_share: number;
}
interface SegmentData {
  label: string;
  rows: SegmentRow[];
  concentration: { largest_expected_loss_share: number };
}

export default function Overview() {
  const { dataset, meta } = useDataset();
  const { data, error } = useApi<OverviewData>(apiUrl("overview", dataset));
  const [segment, setSegment] = useState("loan_purpose");
  const segmentKey = data?.segment_options.some((option) => option.key === segment) ? segment : data?.segment_options[0]?.key;
  const segments = useApi<SegmentData>(segmentKey ? apiUrl("segments", dataset, { by: segmentKey }) : null);

  if (error) return <ErrorState message={error} />;
  if (!data || !meta) return <Skeleton height={420} />;
  const { kpis } = data;
  const histogram = data.histogram.map((row) => ({ ...row, name: `${Math.round(row.from * 100)}–${Math.round(row.to * 100)}%` }));
  const topSegment = segments.data?.rows[0];

  return (
    <>
      <PageHead title="Portfolio at a glance">
        How likely each applicant is to default, and how much money that could cost — measured on {integer(kpis.applicants)} applicants
        the model never saw while learning.
      </PageHead>
      {meta.synthetic && (
        <div style={{ marginBottom: 16 }}>
          <Notice tone="warn">This is simulated demo data. It shows how the analysis works, not real lending results.</Notice>
        </div>
      )}

      <div className="grid cols-4">
        <Stat label="Applicants scored" value={integer(kpis.applicants)} note="Held back from training" />
        <Stat label="Average chance of default" value={percent(kpis.mean_pd)} note="Predicted by the model" />
        <Stat label="Actually defaulted" value={percent(kpis.observed_default_rate)} note="What really happened" />
        <Stat label="Expected loss" value={money(kpis.expected_loss, true)} note={`If ${percent(meta.lgd, 0)} of each defaulted loan is lost`} />
      </div>

      <div className="grid cols-3 section">
        <Card title="How risk is spread" sub="Applicants by predicted chance of default, coloured by risk band" className="span-2">
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={histogram} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="name" interval={3} tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip
                  cursor={{ fill: "var(--surface-2)" }}
                  content={({ active, payload, label }) =>
                    active && payload?.length ? (
                      <div className="tooltip">
                        <strong>{label} chance of default</strong>
                        <div>{integer(payload.reduce((sum, item) => sum + Number(item.value ?? 0), 0))} applicants</div>
                      </div>
                    ) : null
                  }
                />
                {data.bands.map((band) => (
                  <Bar key={band.letter} dataKey={band.letter} stackId="risk" fill={BAND_COLORS[band.letter]} name={band.name} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Risk bands" sub="Predicted vs. what actually happened">
          <div className="stack" style={{ gap: 14 }}>
            {data.bands.map((band) => (
              <div key={band.letter}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <BandBadge letter={band.letter} name={`${band.name} · ${band.range}`} />
                  <span className="small num">{integer(band.applicants)}</span>
                </div>
                <div className="meter" style={{ marginTop: 8 }}>
                  <span style={{ width: `${band.share * 100}%`, background: BAND_COLORS[band.letter] }} />
                </div>
                <div className="small muted num" style={{ marginTop: 4 }}>
                  {band.applicants ? <>Predicted {percent(band.mean_pd)} · actual {percent(band.observed_default_rate)}</> : "No applicants"}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card
        title="Where the expected loss sits"
        sub={topSegment ? <>{topSegment.segment} carries the largest share: {percent(topSegment.expected_loss_share)} of expected loss.</> : " "}
        className="section"
        action={
          segmentKey && (
            <Segmented label="Group by" value={segmentKey} onChange={setSegment}
              options={data.segment_options.map((option) => ({ key: option.key, label: option.label }))} />
          )
        }
      >
        {segments.error ? <ErrorState message={segments.error} /> : !segments.data ? <Skeleton height={240} /> : (
          <div className="grid cols-2">
            <div style={{ height: Math.max(220, segments.data.rows.length * 40) }}>
              <ResponsiveContainer>
                <BarChart data={segments.data.rows} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 8 }}>
                  <CartesianGrid horizontal={false} />
                  <XAxis type="number" tickFormatter={(value) => percent(value, 0)} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="segment" width={130} tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ fill: "var(--surface-2)" }}
                    content={({ active, payload }) => {
                      const row = payload?.[0]?.payload as SegmentRow | undefined;
                      return active && row ? (
                        <div className="tooltip">
                          <strong>{row.segment}</strong>
                          <div>{percent(row.expected_loss_share)} of expected loss</div>
                          <div>{money(row.expected_loss)} across {integer(row.applicants)} applicants</div>
                        </div>
                      ) : null;
                    }}
                  />
                  <Bar dataKey="expected_loss_share" radius={[0, 6, 6, 0]}>
                    {segments.data.rows.map((row, index) => (
                      <Cell key={row.segment} fill="var(--brand)" fillOpacity={1 - index * 0.08} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="scroll-x">
              <table className="table">
                <thead>
                  <tr>
                    <th>{segments.data.label}</th>
                    <th className="right">Applicants</th>
                    <th className="right">Avg. risk</th>
                    <th className="right">Expected loss</th>
                  </tr>
                </thead>
                <tbody>
                  {segments.data.rows.map((row) => (
                    <tr key={row.segment}>
                      <td>{row.segment}</td>
                      <td className="right">{integer(row.applicants)}</td>
                      <td className="right">{percent(row.mean_predicted_pd)}</td>
                      <td className="right">{money(row.expected_loss)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>
      <p className="small muted section">
        {meta.exposure_assumption}. Loss assumes {percent(meta.lgd, 0)} of a defaulted amount is not recovered — an assumption, not an observed recovery rate.
      </p>
    </>
  );
}
