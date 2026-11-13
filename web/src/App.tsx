import { NavLink, Outlet, Route, Routes } from "react-router-dom";
import { Activity, Gauge, LayoutDashboard, Scale, SlidersHorizontal, Users } from "lucide-react";
import { useDataset } from "./context";
import { Segmented, Skeleton, ErrorState } from "./components/ui";
import Overview from "./pages/Overview";
import Applicants from "./pages/Applicants";
import ApplicantDetail from "./pages/ApplicantDetail";
import Scenarios from "./pages/Scenarios";
import ModelQuality from "./pages/ModelQuality";
import Fairness from "./pages/Fairness";

const LINKS = [
  { to: "/", label: "Portfolio", short: "Portfolio", icon: LayoutDashboard },
  { to: "/applicants", label: "Applicants", short: "People", icon: Users },
  { to: "/scenarios", label: "What-if scenarios", short: "What-if", icon: SlidersHorizontal },
  { to: "/model", label: "Model quality", short: "Model", icon: Gauge },
  { to: "/fairness", label: "Fairness check", short: "Fairness", icon: Scale },
];

function Shell() {
  const { dataset, setDataset, meta, metaError } = useDataset();
  return (
    <div className="shell">
      <nav className="nav" aria-label="Main">
        <div className="brand">
          <div className="brand-mark"><Activity size={18} aria-hidden /></div>
          <div>
            <div className="brand-name">Credit Risk Studio</div>
            <div className="brand-sub">Default risk &amp; expected loss</div>
          </div>
        </div>
        {LINKS.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"}>
            <Icon size={18} aria-hidden /> {label}
          </NavLink>
        ))}
        <div className="nav-foot">
          {meta ? <>Scored by {meta.model.replace(" / ", " (").toLowerCase()}) on {meta.test_applicants.toLocaleString()} unseen applicants.</> : "Loading model…"}
        </div>
      </nav>
      <div className="main">
        <div className="topbar">
          <div className="row">
            {meta?.synthetic && <span className="badge pill-warn">Simulated data</span>}
            {meta && !meta.synthetic && (
              <a className="badge pill-brand" href={meta.source_url ?? undefined} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
                Real data · {meta.name}
              </a>
            )}
          </div>
          <Segmented
            label="Dataset"
            value={dataset}
            onChange={setDataset}
            options={[{ key: "uci", label: "Taiwan cards" }, { key: "german", label: "German loans" }, { key: "synthetic", label: "Demo" }]}
          />
        </div>
        <main className="page">
          {metaError ? <ErrorState message={metaError} /> : meta ? <Outlet /> : <Skeleton height={320} />}
        </main>
      </div>
      <nav className="mobile-tabs" aria-label="Main">
        {LINKS.map(({ to, short, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"}>
            <Icon size={20} aria-hidden />
            {short}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Overview />} />
        <Route path="applicants" element={<Applicants />} />
        <Route path="applicants/:id" element={<ApplicantDetail />} />
        <Route path="scenarios" element={<Scenarios />} />
        <Route path="model" element={<ModelQuality />} />
        <Route path="fairness" element={<Fairness />} />
      </Route>
    </Routes>
  );
}
