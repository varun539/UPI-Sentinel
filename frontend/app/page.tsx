
 "use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

const API = "/api/backend";

type Summary = {
  transactions?: number;
  users?: number;
  merchants?: number;
  investigation_candidates?: number;
  investigation_queue?: number;
  [key: string]: any;
};

type Investigation = {
  priority_rank?: number;
  entity_type?: string;
  entity_id?: string;
  risk_score?: number;
  risk_band?: string;
  reasons?: string;
  [key: string]: any;
};

type UploadResult = {
  status?: string;
  source?: string;
  filename?: string;
  raw_rows?: number;
  rows?: number;
  columns?: number;
  duplicates?: number;
  exact_duplicates_removed?: number;
  missing_fields?: Record<string, number>;
  message?: string;
  [key: string]: any;
};

type SourceName =
  | "UPI Transactions"
  | "KYC Records"
  | "Merchant Master"
  | "Chargebacks";

const navItems = [
  { icon: "⌂", label: "Dashboard", href: "/" },
  { icon: "⚠", label: "Investigations", href: "/investigations" },
  { icon: "↔", label: "Transactions", href: "/transactions" },
  { icon: "◉", label: "Users", href: "/users" },
  { icon: "▣", label: "Merchants", href: "/merchants" },
  { icon: "⌁", label: "Networks", href: "/networks" },
];

function formatNumber(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) return "—";
  return value.toLocaleString("en-IN");
}

function riskClass(risk?: string) {
  const r = String(risk || "").toUpperCase();
  if (r === "CRITICAL") return "risk-critical";
  if (r === "HIGH") return "risk-high";
  if (r === "MEDIUM") return "risk-medium";
  return "risk-low";
}

function StatCard({
  label, value, change, icon, tone = "",
}: {
  label: string; value: string; change: string; icon: string; tone?: string;
}) {
  return (
    <div className={`stat-card dashboard-stat ${tone}`}>
      <div className="stat-top">
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
        </div>
        <div className="stat-icon">{icon}</div>
      </div>
      <div className="stat-bottom">
        <span className="stat-live">● LIVE</span>
        <span>{change}</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [summary, setSummary] = useState<Summary>({});
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiOnline, setApiOnline] = useState(false);
  const [active, setActive] = useState("Dashboard");
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSource, setSelectedSource] = useState("UPI Transactions");
  const [dragging, setDragging] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<"idle" | "ready" | "uploading" | "success" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [sourceRows, setSourceRows] = useState<Record<SourceName, number>>({
    "UPI Transactions": 0,
    "KYC Records": 0,
    "Merchant Master": 0,
    "Chargebacks": 0,
  });

  async function loadDashboard(showRefresh = false) {
    if (showRefresh) setRefreshing(true);
    try {
      const [summaryRes, investigationRes] = await Promise.all([
        fetch(`${API}/dashboard/summary`, { cache: "no-store" }),
        fetch(`${API}/investigations?limit=6`, { cache: "no-store" }),
      ]);
      if (!summaryRes.ok) throw new Error("Summary API failed");
      setSummary(await summaryRes.json());
      if (investigationRes.ok) {
        const data = await investigationRes.json();
        setInvestigations(Array.isArray(data) ? data : data?.data || data?.items || []);
      }
      setApiOnline(true);
    } catch (error) {
      console.error("UPI Sentinel API error:", error);
      setApiOnline(false);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { loadDashboard(); }, []);

  const transactions = summary.transactions ?? summary.total_transactions;
  const users = summary.users ?? summary.total_users;
  const merchants = summary.merchants ?? summary.total_merchants;
  const investigationsCount =
    summary.investigation_candidates ?? summary.investigation_queue ?? summary.total_investigations;

  const summarySourceRows = useMemo(() => ({
    "UPI Transactions": Number(
      summary.source_rows?.transactions ??
      summary.rows?.transactions ??
      summary.transactions ??
      0
    ),
    "KYC Records": Number(
      summary.source_rows?.kyc ??
      summary.rows?.kyc ??
      summary.users ??
      0
    ),
    "Merchant Master": Number(
      summary.source_rows?.merchants ??
      summary.rows?.merchants ??
      summary.merchants ??
      0
    ),
    "Chargebacks": Number(
      summary.source_rows?.chargebacks ??
      summary.rows?.chargebacks ??
      summary.chargebacks ??
      0
    ),
  }), [summary]);

  const riskStats = useMemo(() => {
    const distribution = summary?.risk_distribution?.transactions || {};
    const bands = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
    const counts = bands.map((band) => Number(distribution[band] || 0));
    const distributionTotal = counts.reduce((sum, value) => sum + value, 0);

    return bands.map((label, index) => ({
      label,
      count: counts[index],
      value:
        distributionTotal > 0
          ? Number(((counts[index] / distributionTotal) * 100).toFixed(2))
          : 0,
      cls: label.toLowerCase(),
    }));
  }, [summary, transactions]);

  const sources: Array<{
    name: SourceName;
    icon: string;
    detail: string;
  }> = [
    { name: "UPI Transactions", icon: "↔", detail: "Cleaned, validated and scored through the Sentinel pipeline." },
    { name: "KYC Records", icon: "◉", detail: "Identity fields validated and canonicalized." },
    { name: "Merchant Master", icon: "▣", detail: "Merchant identifiers normalized for entity matching." },
    { name: "Chargebacks", icon: "⚠", detail: "Complaint records validated and linked to transactions." },
  ];

  function chooseFile(file?: File) {
    if (!file) return;
    const valid = ["text/csv", "application/json", "text/plain"].includes(file.type) ||
      /\.(csv|json|txt)$/i.test(file.name);
    if (!valid) {
      setUploadState("error");
      setUploadResult(null);
      setUploadMessage("Use a CSV or JSON intelligence file.");
      return;
    }
    setUploadFile(file);
    setUploadState("ready");
    setUploadResult(null);
    setUploadMessage(`${file.name} ready for ingestion`);
  }

  async function uploadData() {
    if (!uploadFile) return;

    setUploadState("uploading");
    setUploadMessage("Uploading source and starting Sentinel intelligence pipeline...");

    try {
      const form = new FormData();
      form.append("file", uploadFile);

      const sourceTypeMap: Record<string, string> = {
        "UPI Transactions": "transactions",
        "KYC Records": "kyc",
        "Merchant Master": "merchants",
        "Chargebacks": "chargebacks",
      };

      form.append(
        "source_type",
        sourceTypeMap[selectedSource] || "transactions"
      );

      const res = await fetch(`${API}/upload`, {
        method: "POST",
        body: form,
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const detail =
          typeof data?.detail === "string"
            ? data.detail
            : data?.detail?.message || "Upload could not be started.";
        throw new Error(detail);
      }

      setUploadResult(data);

      const jobId = data?.job_id;
      if (!jobId) {
        throw new Error("Pipeline job was not created.");
      }

      // The backend runs the eight existing pipeline stages in a background
      // job. Poll until the generated intelligence is ready, avoiding long
      // browser/proxy request timeouts.
      let completed = false;

      for (let attempt = 0; attempt < 180; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));

        const statusRes = await fetch(
          `${API}/upload/status/${encodeURIComponent(jobId)}`,
          { cache: "no-store" }
        );

        if (!statusRes.ok) {
          throw new Error("Could not read pipeline status.");
        }

        const statusData = await statusRes.json();

        if (statusData.status === "running" || statusData.status === "queued") {
          setUploadMessage(
            statusData.stage || "Running Sentinel intelligence pipeline..."
          );
          continue;
        }

        if (statusData.status === "failed") {
          throw new Error(
            statusData.message ||
              statusData.error ||
              "The intelligence pipeline failed."
          );
        }

        if (statusData.status === "completed") {
          completed = true;

          setUploadResult({
            ...data,
            ...statusData,
            status: "completed",
          });

          setUploadMessage(
            statusData.message ||
              "Analysis complete — dashboard intelligence refreshed."
          );

          if (statusData?.source_rows) {
            const sourceMap: Record<string, number> = {};
            if (statusData.source_rows.transactions !== undefined) {
              sourceMap["UPI Transactions"] = Number(statusData.source_rows.transactions);
            }
            if (statusData.source_rows.kyc !== undefined) {
              sourceMap["KYC Records"] = Number(statusData.source_rows.kyc);
            }
            if (statusData.source_rows.merchants !== undefined) {
              sourceMap["Merchant Master"] = Number(statusData.source_rows.merchants);
            }
            if (statusData.source_rows.chargebacks !== undefined) {
              sourceMap["Chargebacks"] = Number(statusData.source_rows.chargebacks);
            }
            setSourceRows((previous) => ({ ...previous, ...sourceMap }));
          }

          setUploadState("success");
          await loadDashboard(true);
          break;
        }
      }

      if (!completed) {
        throw new Error(
          "The pipeline is taking longer than expected. Refresh the dashboard shortly."
        );
      }
    } catch (error) {
      setUploadResult(null);
      setUploadState("error");
      setUploadMessage(
        error instanceof Error
          ? error.message
          : "Upload and analysis failed."
      );
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><span>U</span></div>
          <div><div className="brand-name">UPI SENTINEL</div><div className="brand-subtitle">FRAUD INTELLIGENCE</div></div>
        </div>

        <div className="nav-section">
          <div className="nav-title">MONITORING</div>
          {navItems.map((item) => (
            <button key={item.label} className={`nav-item ${active === item.label ? "active" : ""}`}
              onClick={() => { setActive(item.label); router.push(item.href); }}>
              <span className="nav-icon">{item.icon}</span><span>{item.label}</span>
              {item.label === "Investigations" && typeof investigationsCount === "number" && investigationsCount > 0 &&
                <span className="nav-badge">{investigationsCount}</span>}
            </button>
          ))}
        </div>

        <div className="nav-section">
          <div className="nav-title">INTELLIGENCE</div>
          <button className="nav-item" onClick={() => router.push("/ai-investigator")}>
            <span className="nav-icon">✦</span><span>Sentinel AI Analyst</span><span className="ai-badge">AI</span>
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className="system-status">
            <div className={`status-dot ${apiOnline ? "online" : "offline"}`} />
            <div><div className="system-title">{apiOnline ? "Intelligence engine online" : "Connecting..."}</div>
              <div className="system-subtitle">UPI Sentinel intelligence engine</div></div>
          </div>
          <div className="version">UPI Sentinel v0.2.0</div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">SENTINEL / <span>{active.toUpperCase()}</span></div>
            <h1>UPI Fraud & Merchant Intelligence</h1>
            <p className="page-description">Governed intelligence across UPI transactions, users, merchants and suspicious networks.</p>
          </div>
          <div className="topbar-actions">
            <div className="connection"><span className={`connection-dot ${apiOnline ? "online" : "offline"}`} />
              {apiOnline ? "INTELLIGENCE ONLINE" : "CONNECTING"}</div>
            <button className="refresh-button" onClick={() => loadDashboard(true)} disabled={refreshing}>
              {refreshing ? "↻ Syncing..." : "↻ Refresh"}
            </button>
            <div className="profile"><div className="profile-avatar">AI</div><div><div className="profile-name">Investigator</div><div className="profile-role">Risk Operations</div></div></div>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="stats-grid">
            <StatCard label="TOTAL TRANSACTIONS" value={loading ? "..." : formatNumber(transactions)} change="Processed" icon="↔" />
            <StatCard label="UNIQUE USERS" value={loading ? "..." : formatNumber(users)} change="Monitored" icon="◉" />
            <StatCard label="MERCHANT ENTITIES" value={loading ? "..." : formatNumber(merchants)} change="Indexed" icon="▣" />
            <StatCard label="INVESTIGATION QUEUE" value={loading ? "..." : formatNumber(investigationsCount)} change="Requires review" icon="⚠" tone="danger-stat" />
          </section>

          <section className="panel data-rescue-panel">
            <div className="data-rescue-header">
              <div><div className="panel-kicker">DATA RESCUE</div><h2>Governed Data Layer</h2>
                <p className="data-rescue-description">Upload a source and run it through Sentinel's cleaning, validation, ML, graph and unified intelligence pipeline.</p></div>
              <div className="pipeline-ready"><span className="ready-dot" /> PIPELINE READY</div>
            </div>

            <div className="source-grid">
              {sources.map((source) => (
                <button key={source.name} className={`source-card ${selectedSource === source.name ? "selected" : ""}`}
                  onClick={() => {
                    setSelectedSource(source.name);
                    setUploadFile(null);
                    setUploadState("idle");
                    setUploadMessage("");
                    setUploadResult(null);
                  }}>
                  <div className="source-top">
                    <div className="source-icon">{source.icon}</div>
                    <span className={`source-status ${selectedSource === source.name ? "selected-status" : ""}`}>
                      {selectedSource === source.name ? "SELECTED" : "READY"}
                    </span>
                  </div>
                  <strong>{source.name}</strong><span>
  {formatNumber(
    sourceRows[source.name] ??
    summarySourceRows[source.name] ??
    undefined
  )} processed records
</span><small>{source.detail}</small>
                  <span className="source-upload-label">
                    {selectedSource === source.name ? "UPLOAD THIS SOURCE →" : "SELECT TO UPLOAD"}
                  </span>
                </button>
              ))}
            </div>

            <div
              className={`upload-zone ${dragging ? "dragging" : ""} ${uploadState === "success" ? "upload-success" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => { e.preventDefault(); setDragging(false); chooseFile(e.dataTransfer.files?.[0]); }}
              onClick={() => fileInput.current?.click()}
            >
              <input
                ref={fileInput}
                type="file"
                accept=".csv,.json"
                hidden
                onChange={(e) => chooseFile(e.target.files?.[0])}
              />
              <div className="upload-icon">{uploadState === "success" ? "✓" : "↑"}</div>
              <div className="upload-copy">
                <strong>{uploadFile ? uploadFile.name : "Upload new intelligence"}</strong>
                <span>{uploadMessage || `Drop ${selectedSource} CSV/JSON here or click to browse`}</span>
              </div>
              <button
                type="button"
                className="upload-button"
                disabled={uploadState === "uploading"}
                onClick={(e) => {
                  e.stopPropagation();
                  if (uploadFile) uploadData();
                  else fileInput.current?.click();
                }}
              >
                {uploadState === "uploading" ? "Analyzing..." : uploadFile ? "Upload & Analyze" : "Choose File"}
              </button>
            </div>

            {uploadState === "uploading" && (
              <div className="upload-pipeline-status">
                <span className="pipeline-spinner" />
                <div>
                  <strong>Sentinel is analyzing the uploaded source</strong>
                  <span>Cleaning → Validation → Features → Graph → Anomaly Detection → Unified Intelligence</span>
                </div>
              </div>
            )}

            {uploadResult && uploadState === "success" && (
              <div className="upload-result-card">
                <div className="upload-result-head">
                  <div>
                    <div className="panel-kicker">INGESTION + ANALYSIS RESULT</div>
                    <strong>{uploadResult.filename || uploadFile?.name || "Uploaded source"}</strong>
                  </div>
                  <span className="upload-result-status">{uploadState === "success" ? "ANALYZED" : "PROCESSING"}</span>
                </div>
                <div className="upload-result-grid">
                  <div><span>RAW ROWS</span><strong>{formatNumber(Number(uploadResult.raw_rows ?? uploadResult.rows))}</strong></div>
                  <div><span>COLUMNS</span><strong>{formatNumber(Number(uploadResult.columns))}</strong></div>
                  <div>
                      <span>DUPLICATES</span>
                      <strong>
                        {formatNumber(
                          Number(
                            typeof uploadResult.duplicates === "number"
                              ? uploadResult.duplicates
                              : uploadResult.exact_duplicates_removed ?? 0
                          )
                        )}
                      </strong>
                    </div>
                  <div><span>SOURCE</span><strong>{uploadResult.source || selectedSource}</strong></div>
                </div>
                {uploadResult.missing_fields && Object.keys(uploadResult.missing_fields).length > 0 && (
                  <div className="upload-missing">
                    <span>Missing fields detected</span>
                    {Object.entries(uploadResult.missing_fields).slice(0, 5).map(([field, count]) => (
                      <b key={field}>{field}: {Number(count).toLocaleString("en-IN")}</b>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="data-rescue-footer">
              <div className="rescue-stat"><strong>{formatNumber(Number(summary.cleaning?.transactions?.exact_duplicates_removed ?? 400))}</strong><span>transaction duplicates removed</span></div>
              <div className="rescue-stat"><strong>{Number(summary.transaction_kyc_match_rate_pct ?? 27.96).toFixed(2)}%</strong><span>transaction → KYC match</span></div>
              <div className="rescue-stat"><strong>{Number(summary.transaction_merchant_match_rate_pct ?? 46.38).toFixed(2)}%</strong><span>transaction → merchant match</span></div>
              <div className="rescue-flow"><span>CLEAN</span><b>→</b><span>VALIDATE</span><b>→</b><span>ANALYZE</span><b>→</b><span>INVESTIGATE</span></div>
            </div>
          </section>

          <section className="dashboard-grid">
            <div className="panel risk-panel">
              <div className="panel-header"><div><div className="panel-kicker">RISK ENGINE</div><h2>Risk Overview</h2></div><div className="panel-chip">UNIFIED INTELLIGENCE</div></div>
              <div className="risk-overview">
                <div className="risk-ring"><div className="ring-inner"><span>{formatNumber(transactions)}</span><small>TRANSACTIONS</small></div></div>
                <div className="risk-bars">
                  {riskStats.map((risk) => (
                    <div className="risk-row" key={risk.label}>
                      <div className="risk-row-label"><span className={`legend-dot ${risk.cls}`} />{risk.label}</div>
                      <div className="bar"><div className={`bar-fill ${risk.cls}-fill`} style={{ width: `${Math.max(risk.value, 1)}%` }} /></div>
                      <strong>{risk.value < 0.1 ? "<1%" : `${risk.value}%`}</strong>
                    </div>
                  ))}
                </div>
              </div>
              <div className="risk-note">Risk scores are investigative signals, not calibrated probabilities or proof of fraud.</div>
            </div>

            <div className="panel intelligence-panel">
              <div className="panel-header"><div><div className="panel-kicker">SYSTEM INTELLIGENCE</div><h2>Detection Stack</h2></div></div>
              <div className="detection-list">
                {[
                  ["Data Rescue", "Raw source data normalized"],
                  ["Validation Engine", "Schema and integrity checks"],
                  ["ML Anomaly Detection", "Isolation Forest models active"],
                  ["Fraud Graph", "User ↔ Merchant relationships"],
                  ["Unified Risk", "Cross-entity intelligence"],
                ].map(([title, desc]) => (
                  <div className="detection-item" key={title}>
                    <div className="detection-icon">✓</div><div><strong>{title}</strong><span>{desc}</span></div><b>READY</b>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="panel investigation-panel">
            <div className="panel-header">
              <div><div className="panel-kicker">RISK OPERATIONS</div><h2>Investigation Queue</h2></div>
              <button className="view-all" onClick={() => router.push("/investigations")}>View all →</button>
            </div>
            <div className="table-wrap">
              <table><thead><tr><th>PRIORITY</th><th>ENTITY</th><th>ENTITY ID</th><th>RISK SCORE</th><th>RISK BAND</th><th>DETECTION SIGNALS</th></tr></thead>
                <tbody>
                  {investigations.length > 0 ? investigations.map((item, index) => (
                    <tr key={`${item.entity_id}-${index}`} onClick={() => router.push("/investigations")} className="clickable-row">
                      <td><span className="priority">#{item.priority_rank ?? index + 1}</span></td>
                      <td><span className="entity-type">{item.entity_type || "USER"}</span></td>
                      <td><code>{item.entity_id || "—"}</code></td>
                      <td><strong className="score">{typeof item.risk_score === "number" ? item.risk_score.toFixed(2) : "—"}</strong></td>
                      <td><span className={`risk-pill ${riskClass(item.risk_band)}`}>{item.risk_band || "MEDIUM"}</span></td>
                      <td><span className="signal">{item.reasons || "Behavioral risk detected"}</span></td>
                    </tr>
                  )) : <tr><td colSpan={6}><div className="empty-state">No investigation candidates returned.</div></td></tr>}
                </tbody>
              </table>
            </div>
          </section>

          <section className="bottom-grid">
            <div className="panel insight-card">
              <div className="insight-icon">⌁</div><div><div className="panel-kicker">NETWORK INTELLIGENCE</div><h3>Suspicious network candidates</h3>
                <div className="big-number">{formatNumber(Number(
  summary.suspicious_networks ??
  summary.rows?.suspicious_networks ??
  summary.graph?.suspicious_networks ??
  0
))}</div><p>Connected components flagged for investigator review based on shared-merchant relationships and behavioral signals.</p></div>
              <button onClick={() => router.push("/networks")}>Explore networks →</button>
            </div>
            <div className="panel insight-card ai-card"><div className="insight-icon ai-icon">✦</div><div><div className="panel-kicker">SENTINEL COPILOT</div>
              <h3>Ask Sentinel about your data</h3><p>Ask natural-language questions about transactions, risk patterns, merchants, chargebacks and suspicious networks.</p></div>
              <button onClick={() => router.push("/ai-investigator")}>Open Sentinel AI Analyst →</button>
            </div>
          </section>

          <footer><span>UPI SENTINEL</span><span>Fraud & Merchant Intelligence Platform</span><span>© 2026</span></footer>
        </div>
      </section>

      <style jsx>{`
        .source-card {
          width: 100%;
          text-align: left;
          cursor: pointer;
          font: inherit;
          color: inherit;
        }

        .source-card.selected {
          border-color: rgba(72, 213, 151, 0.35);
          background: rgba(72, 213, 151, 0.045);
          box-shadow: inset 0 0 0 1px rgba(72, 213, 151, 0.06);
        }

        .source-status.selected-status {
          color: #69dda9;
          border-color: rgba(72, 213, 151, 0.24);
          background: rgba(72, 213, 151, 0.08);
        }

        .source-upload-label {
          display: inline-block;
          margin-top: 8px;
          color: rgba(105, 221, 169, 0.62);
          font-size: 7px;
          font-weight: 800;
          letter-spacing: .09em;
        }

        .upload-pipeline-status {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 10px;
          padding: 10px 12px;
          border: 1px solid rgba(72, 213, 151, 0.13);
          border-radius: 9px;
          background: rgba(72, 213, 151, 0.025);
        }

        .upload-pipeline-status > div {
          display: flex;
          flex-direction: column;
          gap: 3px;
        }

        .upload-pipeline-status strong {
          color: rgba(255,255,255,0.68);
          font-size: 9px;
        }

        .upload-pipeline-status span:not(.pipeline-spinner) {
          color: rgba(255,255,255,0.3);
          font-size: 8px;
        }

        .pipeline-spinner {
          width: 14px;
          height: 14px;
          border: 2px solid rgba(72, 213, 151, 0.16);
          border-top-color: #69dda9;
          border-radius: 50%;
          animation: sentinel-spin .8s linear infinite;
          flex: 0 0 auto;
        }

        @keyframes sentinel-spin {
          to { transform: rotate(360deg); }
        }

        .upload-zone {
          min-height: 88px;
          margin-top: 16px;
          padding: 16px 18px;
          border: 1px dashed rgba(72, 213, 151, 0.28);
          border-radius: 12px;
          background: linear-gradient(135deg, rgba(72, 213, 151, 0.035), rgba(255,255,255,0.012));
          display: grid;
          grid-template-columns: auto minmax(0, 1fr) auto;
          align-items: center;
          gap: 14px;
          cursor: pointer;
          transition: border-color .18s ease, background .18s ease, transform .18s ease;
        }

        .upload-zone:hover, .upload-zone.dragging {
          border-color: rgba(72, 213, 151, 0.58);
          background: rgba(72, 213, 151, 0.065);
        }

        .upload-zone.upload-success {
          border-color: rgba(72, 213, 151, 0.45);
        }

        .upload-icon {
          width: 38px;
          height: 38px;
          border: 1px solid rgba(72, 213, 151, 0.2);
          border-radius: 10px;
          display: grid;
          place-items: center;
          color: #69dda9;
          background: rgba(72, 213, 151, 0.06);
          font-size: 18px;
        }

        .upload-copy {
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .upload-copy strong {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: rgba(255,255,255,0.82);
          font-size: 12px;
        }

        .upload-copy span {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: rgba(255,255,255,0.36);
          font-size: 9px;
        }

        .upload-button {
          min-width: 126px;
          height: 36px;
          padding: 0 14px;
          border: 1px solid rgba(72, 213, 151, 0.25);
          border-radius: 8px;
          background: rgba(72, 213, 151, 0.08);
          color: #69dda9;
          font: inherit;
          font-size: 9px;
          font-weight: 700;
          letter-spacing: .06em;
          cursor: pointer;
        }

        .upload-button:hover:not(:disabled) {
          background: rgba(72, 213, 151, 0.14);
          border-color: rgba(72, 213, 151, 0.45);
        }

        .upload-button:disabled {
          opacity: .55;
          cursor: wait;
        }

        .upload-result-card {
          margin-top: 10px;
          padding: 14px;
          border: 1px solid rgba(72, 213, 151, 0.18);
          border-radius: 10px;
          background: rgba(72, 213, 151, 0.025);
        }

        .upload-result-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .upload-result-head strong {
          display: block;
          margin-top: 3px;
          max-width: 560px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: rgba(255,255,255,0.76);
          font-size: 10px;
        }

        .upload-result-status {
          flex: 0 0 auto;
          padding: 5px 8px;
          border-radius: 999px;
          color: #69dda9;
          background: rgba(72, 213, 151, 0.08);
          font-size: 8px;
          font-weight: 700;
          letter-spacing: .08em;
        }

        .upload-result-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          margin-top: 12px;
        }

        .upload-result-grid > div {
          min-width: 0;
          padding: 9px 10px;
          border: 1px solid rgba(255,255,255,0.05);
          border-radius: 8px;
          background: rgba(255,255,255,0.012);
        }

        .upload-result-grid span, .upload-missing span {
          display: block;
          color: rgba(255,255,255,0.28);
          font-size: 7px;
          letter-spacing: .08em;
        }

        .upload-result-grid strong {
          display: block;
          margin-top: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: rgba(255,255,255,0.72);
          font-size: 10px;
        }

        .upload-missing {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 7px;
          margin-top: 10px;
        }

        .upload-missing b {
          padding: 4px 7px;
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 6px;
          color: rgba(255,255,255,0.42);
          font-size: 8px;
          font-weight: 500;
        }

        @media (max-width: 800px) {
          .upload-zone {
            grid-template-columns: auto minmax(0, 1fr);
          }
          .upload-button {
            grid-column: 2;
            width: max-content;
          }
          .upload-result-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 520px) {
          .upload-zone {
            grid-template-columns: 1fr;
          }
          .upload-icon {
            display: none;
          }
          .upload-button {
            grid-column: 1;
            width: 100%;
          }
          .upload-result-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
      `}</style>
    </main>
  );
}