import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Download, Search } from "lucide-react";
import { apiUrl, useApi } from "../api";
import { useDataset } from "../context";
import { BAND_COLORS, integer, money, percent } from "../format";
import { BandBadge, Card, ErrorState, PageHead, Segmented, Skeleton } from "../components/ui";

interface ApplicantRow {
  application_id: string;
  credit_score_band: string;
  probability_default: number;
  ead: number;
  expected_loss: number;
  loan_purpose?: string;
  employment_status?: string;
  annual_income?: number;
  age?: number;
  AGE?: number;
}
type Sort = "risk" | "loss" | "exposure" | "id";
const PAGE = 25;

export default function Applicants() {
  const { dataset, meta } = useDataset();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [band, setBand] = useState("");
  const [sort, setSort] = useState<Sort>("risk");
  const [limit, setLimit] = useState(PAGE);

  useEffect(() => {
    const timer = setTimeout(() => setQuery(search), 250);
    return () => clearTimeout(timer);
  }, [search]);
  useEffect(() => setLimit(PAGE), [query, band, sort, dataset]);

  const { data, error, loading } = useApi<{ total: number; rows: ApplicantRow[] }>(
    apiUrl("applicants", dataset, { search: query, band, sort, limit }),
  );
  const bandName = (code: string) => meta?.bands.find((item) => item.band === code)?.name ?? code;

  return (
    <>
      <PageHead title="Applicants">
        Every applicant in the test group, ranked by risk. Open anyone to see what drives their score.
      </PageHead>
      <Card>
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
          <label className="row" style={{ flex: "1 1 260px", gap: 8 }}>
            <Search size={18} className="muted" aria-hidden />
            <input
              className="input"
              style={{ flex: 1 }}
              placeholder={meta?.synthetic ? "Search by ID, purpose or employment" : "Search by ID"}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search applicants"
            />
          </label>
          <select className="input" value={sort} onChange={(event) => setSort(event.target.value as Sort)} aria-label="Sort applicants">
            <option value="risk">Highest risk first</option>
            <option value="loss">Largest expected loss</option>
            <option value="exposure">Largest loan</option>
            <option value="id">Application number</option>
          </select>
        </div>
        <Segmented
          label="Risk band"
          value={band}
          onChange={setBand}
          options={[{ key: "", label: "All" }, ...(meta?.bands ?? []).map((item) => ({ key: item.letter, label: item.name }))]}
        />

        <div className="list" style={{ marginTop: 16 }}>
          <div className="list-row list-head">
            <span>Applicant</span>
            <span className="hide-sm">Chance of default</span>
            <span className="hide-sm right">Loan</span>
            <span className="right">Expected loss</span>
            <span />
          </div>
          {error ? <ErrorState message={error} /> : !data ? <Skeleton height={400} /> : data.rows.length === 0 ? (
            <p className="muted" style={{ padding: 16 }}>No applicants match.</p>
          ) : (
            data.rows.map((row) => {
              const letter = row.credit_score_band.slice(0, 1);
              const details = [row.loan_purpose, row.employment_status, row.age ?? row.AGE ? `age ${row.age ?? row.AGE}` : undefined]
                .filter(Boolean).join(" · ");
              return (
                <Link key={row.application_id} to={`/applicants/${encodeURIComponent(row.application_id)}`} className="list-row">
                  <span>
                    <div className="cell-main">{row.application_id}</div>
                    <div className="cell-sub">{details || bandName(row.credit_score_band)}</div>
                  </span>
                  <span className="hide-sm">
                    <div className="row" style={{ gap: 10 }}>
                      <BandBadge letter={letter} name={bandName(row.credit_score_band)} />
                      <strong className="num">{percent(row.probability_default)}</strong>
                    </div>
                    <div className="meter" style={{ marginTop: 6, maxWidth: 220 }}>
                      <span style={{ width: `${row.probability_default * 100}%`, background: BAND_COLORS[letter] }} />
                    </div>
                  </span>
                  <span className="hide-sm right num">{money(row.ead)}</span>
                  <span className="right num">
                    <strong>{money(row.expected_loss)}</strong>
                  </span>
                  <ChevronRight size={18} className="muted" aria-hidden />
                </Link>
              );
            })
          )}
        </div>
        {data && (
          <div className="row" style={{ justifyContent: "space-between", marginTop: 16 }}>
            <span className="small muted">
              Showing {integer(Math.min(limit, data.total))} of {integer(data.total)}
            </span>
            <div className="row">
              <a className="button" href={apiUrl("downloads/applicants", dataset)}>
                <Download size={16} aria-hidden /> Download CSV
              </a>
              {limit < data.total && (
                <button className="button button-primary" type="button" disabled={loading} onClick={() => setLimit(limit + PAGE)}>
                  Show more
                </button>
              )}
            </div>
          </div>
        )}
      </Card>
    </>
  );
}
