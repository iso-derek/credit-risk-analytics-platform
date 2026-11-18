import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { apiUrl, useApi, type Field } from "../api";
import { useDataset } from "../context";
import { formatValue, money, points } from "../format";
import { BandBadge, Card, ErrorState, Notice, PageHead, RiskGauge, Skeleton } from "../components/ui";

interface Driver extends Field {
  value: unknown;
  reference: unknown;
  pd_change: number;
}
interface ApplicantData {
  application_id: string;
  probability_default: number;
  letter: string;
  name: string;
  range: string;
  exposure: number;
  expected_loss: number;
  defaulted: boolean;
  summary: string | null;
  profile: (Field & { value: unknown })[];
  drivers: Driver[];
}

export default function ApplicantDetail() {
  const { id = "" } = useParams();
  const { dataset, meta } = useDataset();
  const { data, error } = useApi<ApplicantData>(apiUrl(`applicants/${encodeURIComponent(id)}`, dataset));

  const back = (
    <Link to="/applicants" className="button" style={{ marginBottom: 16 }}>
      <ArrowLeft size={16} aria-hidden /> All applicants
    </Link>
  );
  if (error) return <>{back}<ErrorState message={error} /></>;
  if (!data || !meta) return <>{back}<Skeleton height={420} /></>;

  const biggest = Math.max(0.01, ...data.drivers.map((driver) => Math.abs(driver.pd_change)));
  return (
    <>
      {back}
      <PageHead title={`Applicant ${data.application_id}`}>
        {data.summary ?? "Scores come from the selected model using this applicant's repayment history and balances."}
      </PageHead>

      <div className="grid cols-3">
        <Card title="Risk score">
          <RiskGauge value={data.probability_default} letter={data.letter} />
          <div className="row" style={{ justifyContent: "center", marginTop: 8 }}>
            <BandBadge letter={data.letter} name={`${data.name} risk · ${data.range}`} />
          </div>
          <dl className="kv" style={{ marginTop: 20 }}>
            <dt>Amount at risk</dt><dd>{money(data.exposure)}</dd>
            <dt>Expected loss</dt><dd>{money(data.expected_loss)}</dd>
            <dt>What actually happened</dt><dd>{data.defaulted ? "Defaulted" : "Did not default"}</dd>
          </dl>
        </Card>

        <Card
          title="What moves this score"
          sub="Change in default chance if this one detail were typical (the training average) instead"
          className="span-2"
        >
          {data.drivers.length === 0 ? <p className="muted">No single detail changes the score noticeably.</p> : (
            <div>
              {data.drivers.map((driver) => {
                const raises = driver.pd_change > 0;
                const width = (Math.abs(driver.pd_change) / biggest) * 50;
                return (
                  <div className="driver" key={driver.key}>
                    <div>
                      <div style={{ fontWeight: 700 }}>{driver.label}</div>
                      <div className="small muted">
                        {formatValue(driver.value, driver.kind)} here · typical {formatValue(driver.reference, driver.kind)}
                      </div>
                    </div>
                    <div className="driver-bar" aria-hidden>
                      <span style={{
                        width: `${width}%`,
                        left: raises ? "50%" : `${50 - width}%`,
                        background: raises ? "var(--bad)" : "var(--good)",
                      }} />
                    </div>
                    <div className={`num right ${raises ? "delta-up" : "delta-down"}`} style={{ fontWeight: 700 }}>
                      {points(driver.pd_change)}
                    </div>
                  </div>
                );
              })}
              <p className="small muted" style={{ marginTop: 12 }}>
                <span className="delta-up">Red</span> details push risk up; <span className="delta-down">green</span> pull it down.
                This shows how the model reacts, not what caused the outcome.
              </p>
            </div>
          )}
        </Card>
      </div>

      <Card title="Applicant details" className="section">
        <dl className="kv" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 0 }}>
          {data.profile.map((field) => (
            <div key={field.key} className="row" style={{ justifyContent: "space-between", padding: "10px 8px", borderBottom: "1px solid var(--line)" }}>
              <dt title={field.help}>{field.label}</dt>
              <dd>{formatValue(field.value, field.kind)}</dd>
            </div>
          ))}
        </dl>
      </Card>
      {!meta.synthetic && (
        <div className="section">
          <Notice>
            {meta.dataset === "german"
              ? "Real 1970s loan applications from southern Germany (UCI Statlog German Credit, CC BY 4.0). Amounts are in Deutsche Mark. Sex, age and foreign-worker status are not used by the model."
              : "Real 2005 credit-card clients in Taiwan (UCI, CC BY 4.0). Amounts are in New Taiwan dollars. Sex, education, marital status and age are not used by the model."}
          </Notice>
        </div>
      )}
    </>
  );
}
