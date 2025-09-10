// src/App.jsx — Ultra Theme + Motion
import { useEffect, useMemo, useState, useRef } from "react";
import "./App.css";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from "recharts";
import { motion } from "framer-motion";

export default function App() {
  const API = import.meta.env.VITE_API_BASE_URL;

  // --- בסיס ---
  const [status, setStatus] = useState(null);
  const [events, setEvents] = useState([]); // [time, trap, ip, input]
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(false);

  // --- חיפוש/סינון/מיון ---
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedTrap, setSelectedTrap] = useState("all");
  const [sortDir, setSortDir] = useState("desc");

  // --- סימולטור ---
  const [simTrap, setSimTrap] = useState("");
  const [simInput, setSimInput] = useState("");
  const [simIP, setSimIP] = useState("");
  const [simLoading, setSimLoading] = useState(false);
  const [simMsg, setSimMsg] = useState("");

  // --- GeoIP ---
  const [geoFlag, setGeoFlag] = useState(false);
  const [geoRows, setGeoRows] = useState([]);

  // --- שלב 10: Pagination ---
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10); // 10/20/50

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query.trim().toLowerCase()), 320);
    return () => clearTimeout(t);
  }, [query]);

  // Health
  async function checkHealth() {
    try {
      const res = await fetch(`${API}/health`);
      const data = await res.json();
      setStatus(data?.status || "unknown");
    } catch {
      setStatus("❌ Error");
    }
  }

  // --- שלב 10: AbortController לדוח ---
  const reportAbortRef = useRef(null);

  // Report load (עם ביטול בקשות קודמות)
  async function loadReport() {
    if (reportAbortRef.current) {
      try { reportAbortRef.current.abort(); } catch {}
    }
    const controller = new AbortController();
    reportAbortRef.current = controller;

    try {
      setLoading(true);
      setError("");
      const res = await fetch(`${API}/report`, {
        headers: { Accept: "text/html" },
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`Report HTTP ${res.status}`);
      const htmlText = await res.text();

      const parser = new DOMParser();
      const doc = parser.parseFromString(htmlText, "text/html");
      const rows = [];
      const table = doc.querySelector("table");
      const trs = table ? table.querySelectorAll("tr") : [];
      trs.forEach((tr, i) => {
        // Only select <td> cells (skip header)
        const cells = Array.from(tr.querySelectorAll("td")).map(td => td.textContent.trim());
        if (!cells.length) return;
        rows.push(cells.slice(0, 4)); // [time, trap, ip, input]
      });
      setEvents(rows);
      setLastUpdated(new Date());
    } catch (e) {
      if (e?.name !== "AbortError") {
        setError("❌ לא ניתן לטעון את הדוח (ננסה שוב).");
        setEvents([]);
      }
    } finally {
      if (reportAbortRef.current === controller) {
        reportAbortRef.current = null;
      }
      setLoading(false);
    }
  }

  // Polling
  useEffect(() => {
    loadReport();
    const id = setInterval(loadReport, 10000);
    return () => clearInterval(id);
  }, []);

  // כשמשנים חיפוש/מסנן/מיון – חוזרים לעמוד 1
  useEffect(() => {
    setPage(1);
  }, [selectedTrap, debouncedQuery, sortDir]);

  // Options
  const trapOptions = useMemo(() => {
    const set = new Set(events.map(r => r[1]).filter(Boolean));
    return ["all", ...Array.from(set).sort()];
  }, [events]);

  // Sort
  function sortByTime(a, b) {
    const da = new Date(a[0]).getTime() || 0;
    const db = new Date(b[0]).getTime() || 0;
    return sortDir === "asc" ? da - db : db - da;
  }

  // Filters
  const filteredEvents = useMemo(() => {
    let data = [...events];
    if (selectedTrap !== "all") {
      data = data.filter(row => (row[1] || "").toLowerCase() === selectedTrap.toLowerCase());
    }
    if (debouncedQuery) {
      data = data.filter(row => {
        const hay = `${row[1] || ""} ${row[2] || ""} ${row[3] || ""}`.toLowerCase();
        return hay.includes(debouncedQuery);
      });
    }
    data.sort(sortByTime);
    return data;
  }, [events, selectedTrap, debouncedQuery, sortDir]);

  // --- שלב 10: נגזרות עימוד ---
  const totalItems = filteredEvents.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const pagedEvents = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredEvents.slice(start, start + pageSize);
  }, [filteredEvents, page, pageSize]);

  // Charts data
  const byTrap = useMemo(() => {
    const counts = {};
    for (const row of filteredEvents) {
      const trap = row[1] || "";
      counts[trap] = (counts[trap] || 0) + 1;
    }
    return Object.entries(counts).map(([trap, count]) => ({ trap, count }))
      .sort((a, b) => b.count - a.count);
  }, [filteredEvents]);

  const byTime = useMemo(() => {
    const buckets = {};
    for (const row of filteredEvents) {
      const ts = row[0];
      if (!ts) continue;
      const d = new Date(ts); if (isNaN(d)) continue;
      const label = d.getFullYear() + "-" +
        String(d.getMonth() + 1).padStart(2, "0") + "-" +
        String(d.getDate()).padStart(2, "0") + " " +
        String(d.getHours()).padStart(2, "0") + ":00";
      buckets[label] = (buckets[label] || 0) + 1;
    }
    return Object.entries(buckets).map(([time, count]) => ({ time, count }))
      .sort((a, b) => (a.time < b.time ? -1 : 1));
  }, [filteredEvents]);

  // מנקה שם trap מהאימוג'ים/רווחים/תווים לא-אלפביתיים
  function normalizeTrap(t = "") {
    return String(t)
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9_]/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  // Simulation (עם normalizeTrap + input כאובייקט)
  async function submitSimulation(e) {
    e.preventDefault();
    setSimMsg("");

    if (!simTrap && selectedTrap === "all") {
      setSimMsg("בחר trap type (או בחר ב־Filter שמעל)");
      return;
    }

    const chosen = simTrap || (selectedTrap !== "all" ? selectedTrap : "");
    const trapType = normalizeTrap(chosen);

    const body = {
      trap_type: trapType,
      input: simInput ? { raw: simInput } : {}, // שליחה בטוחה לשרת
    };
    if (simIP.trim()) body.ip = simIP.trim();

    try {
      setSimLoading(true);
      const res = await fetch(`${API}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
      setSimMsg("✅ Simulation sent successfully");
      loadReport(); // רענון מיידי
    } catch (err) {
      setSimMsg(`❌ ${err.message}`);
    } finally {
      setSimLoading(false);
    }
  }

  // GeoIP aggregation
  const ipAgg = useMemo(() => {
    const map = new Map();
    for (const [t, trap, ip] of filteredEvents) {
      if (!ip) continue;
      if (!map.has(ip)) map.set(ip, { ip, attempts: 0, lastSeen: t, location: "—", org: "—", coords: "—" });
      const obj = map.get(ip);
      obj.attempts += 1;
      if (new Date(t).getTime() > new Date(obj.lastSeen).getTime()) obj.lastSeen = t;
    }
    return Array.from(map.values());
  }, [filteredEvents]);

  // GeoIP resolve
  async function resolveGeoIP() {
    if (ipAgg.length === 0) return;
    const results = [];
    for (const row of ipAgg) {
      try {
        const url = `${API}/geoip?ip=${encodeURIComponent(row.ip)}`;
        const res = await fetch(url);
        const data = await res.json();
        if (res.ok) {
          const loc = [data.city, data.region, data.country].filter(Boolean).join(", ");
          const coords = (data.latitude && data.longitude) ? `${data.latitude}, ${data.longitude}` : "—";
          results.push({ ip: row.ip, location: loc || "—", org: data.org || "—", coords });
        }
      } catch { /* ignore single fails */ }
    }
    setGeoFlag(true);
    setGeoRows(results);
  }

  // KPIs
  const totalAttempts = filteredEvents.length;
  const uniqueIPs = new Set(filteredEvents.map(r => r[2]).filter(Boolean)).size;
  const uniqueTraps = new Set(filteredEvents.map(r => r[1]).filter(Boolean)).size;
  const lastSeenTs = filteredEvents[0]?.[0] || null;

  // עזר לשיוך צבע לתגית
  const trapClass = (t="") => {
    const k = (t || "").toLowerCase().replace(/\s+/g,'_');
    return ["ftp","ssh","http","ransomware","open_ports","admin_panel","iot_router"].includes(k) ? k : "";
  };

  return (
    <>
      {/* רקע דינמי */}
      <div className="bgs">
        <div className="blob b1" />
        <div className="blob b2" />
        <div className="blob b3" />
      </div>

      <div className="container">
        {/* Header */}
        <motion.div className="header"
          initial={{ opacity:0, y:-10 }} animate={{ opacity:1, y:0 }} transition={{ duration:.5 }}>
          <div className="brand">
            <div className="badge3d">🛡️</div>
            <div className="title">
              Honeypot Dashboard
              <small>Blue-Neon Glass · Live Analytics · GeoIP</small>
            </div>
          </div>
          <div className="actions">
            <button className="btn solid" onClick={checkHealth}>Check Backend Health</button>
            <button className="btn" onClick={loadReport}>Refresh Report</button>
          </div>
        </motion.div>

        {status && (
          <motion.div className="status" initial={{ opacity:0 }} animate={{ opacity:1 }}>
            Backend status: <span className="pill">{status}</span>
          </motion.div>
        )}

        {/* KPIs */}
        <motion.div className="kpis"
          initial={{ opacity:0, y:6 }} animate={{ opacity:1, y:0 }} transition={{ delay:.05, duration:.45 }}>
          <div className="kpi">
            <div className="kpi-label">Total Attempts</div>
            <div className="kpi-value">{totalAttempts}</div>
            <div className="kpi-sub">All events after filters</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Unique IPs</div>
            <div className="kpi-value">{uniqueIPs}</div>
            <div className="kpi-sub">Attack sources</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Trap Types</div>
            <div className="kpi-value">{uniqueTraps}</div>
            <div className="kpi-sub">Seen in current view</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Last Seen</div>
            <div className="kpi-value">{lastSeenTs ? new Date(lastSeenTs).toLocaleTimeString() : "—"}</div>
            <div className="kpi-sub">{lastSeenTs ? new Date(lastSeenTs).toLocaleDateString() : ""}</div>
          </div>
        </motion.div>

        {/* Controls */}
        <motion.div className="controls"
          initial={{ opacity:0, y:6 }} animate={{ opacity:1, y:0 }} transition={{ delay:.12, duration:.45 }}>
          <input className="input" placeholder="חיפוש (IP / Input / Trap Type)…"
                 value={query} onChange={e => setQuery(e.target.value)} />
          <select className="select" value={selectedTrap} onChange={e => setSelectedTrap(e.target.value)}>
            {trapOptions.map(opt => <option key={opt} value={opt}>{opt === "all" ? "All traps" : opt}</option>)}
          </select>
          <button className="btn" onClick={() => setSortDir(d => d === "asc" ? "desc" : "asc")}>
            Sort by Time: {sortDir.toUpperCase()}
          </button>
        </motion.div>

        {/* Charts */}
        <div className="grid">
          {/* Attempts by Trap Type */}
          <motion.div className="card"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18 }}>
            <h2>Attempts by Trap Type</h2>
            {byTrap.length === 0 ? (
              <div className="empty">אין נתונים לגרף.</div>
            ) : (
              <div className="chart-box">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={byTrap} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="trap" stroke="#94a3b8" />
                    <YAxis allowDecimals={false} stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(15,23,42,0.95)",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                        color: "#f8fafc",
                      }}
                      itemStyle={{ color: "#fefefe", fontWeight: 500 }}
                      labelStyle={{ color: "#38bdf8", fontWeight: 600 }}
                    />
                    <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="subtle">Grouped by trap type</div>
          </motion.div>

          {/* Attempts Over Time */}
          <motion.div className="card"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22 }}>
            <h2>Attempts Over Time</h2>
            {byTime.length === 0 ? (
              <div className="empty">אין נתונים לגרף.</div>
            ) : (
              <div className="chart-box">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={byTime} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="time" stroke="#94a3b8" />
                    <YAxis allowDecimals={false} stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(15,23,42,0.95)",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                        color: "#f8fafc",
                      }}
                      itemStyle={{ color: "#fefefe", fontWeight: 500 }}
                      labelStyle={{ color: "#38bdf8", fontWeight: 600 }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#60a5fa" strokeWidth={2} dot={{ fill: "#38bdf8" }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="subtle">Hourly buckets</div>
          </motion.div>
        </div>

        {/* GeoIP */}
        <motion.div className="card" style={{ marginTop:16 }}
          initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ delay:.26 }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", gap:12 }}>
            <h2>GeoIP Panel</h2>
            <button className="btn" onClick={resolveGeoIP}>Resolve GeoIP</button>
          </div>
          {ipAgg.length === 0 ? (
            <div className="empty">להצגה כרגע אין כתובות IP.</div>
          ) : (
            <>
              {geoFlag && <div className="pill" style={{ marginTop:8 }}>✅ GeoIP resolved</div>}
              <div className="table-wrap" style={{ marginTop:10 }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>IP</th>
                      <th>Attempts</th>
                      <th>Last Seen</th>
                      <th>Location</th>
                      <th>Org</th>
                      <th>Coordinates</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ipAgg.map(row => {
                      const match = geoRows.find(g => g.ip === row.ip);
                      return (
                        <tr key={row.ip}>
                          <td>{row.ip}</td>
                          <td>{row.attempts}</td>
                          <td>{row.lastSeen}</td>
                          <td>{match?.location || row.location}</td>
                          <td>{match?.org || row.org}</td>
                          <td>{match?.coords || row.coords}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="note">※ שימוש ב־ipapi.co. יתכנו הגבלות מהירות/DB.</div>
            </>
          )}
        </motion.div>

        {/* Simulator */}
        <motion.div className="card" style={{ marginTop:16 }}
          initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ delay:.30 }}>
          <h2>Simulator</h2>
          <form className="sim-form" onSubmit={submitSimulation}>
            <select className="select" value={simTrap} onChange={e => setSimTrap(e.target.value)} aria-label="trap type">
              <option value="">Trap type…</option>
              {trapOptions.filter(t => t !== "all").map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>
            <input className="input" placeholder='Input (e.g. {"cmd":"ls"} או טקסט חופשי)'
                  value={simInput} onChange={e => setSimInput(e.target.value)} aria-label="input" />
            <input className="input" placeholder="IP (optional)"
                  value={simIP} onChange={e => setSimIP(e.target.value)} aria-label="ip" />
            <button className="btn solid" type="submit" disabled={simLoading}>
              {simLoading ? "Sending…" : "Send"}
            </button>
          </form>
          {simMsg && <div className={`alert ${simMsg.startsWith("✅") ? "ok" : "err"}`}>{simMsg}</div>}
          <div className="note">טיפ: אם <b>Trap type</b> ריק, נשתמש ב־Filter שמעל.</div>
        </motion.div>

        {/* Events Table */}
        <motion.div className="card" style={{ marginTop:16 }}
          initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ delay:.34 }}>
          <h2>Events Report</h2>
          {loading && <div className="empty">טוען…</div>}
          {error && <div className="alert err">{error}</div>}
          {filteredEvents.length === 0 && !loading ? (
            <div className="empty">אין אירועים להצגה כרגע.</div>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Trap Type</th>
                    <th>IP</th>
                    <th>Input</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedEvents.map((row, i) => (
                    <tr key={`${page}-${i}`}>
                      <td>{row[0] || ""}</td>
                      <td>
                        <span className={`badge-trap ${trapClass(row[1])}`}>{row[1] || ""}</span>
                      </td>
                      <td>{row[2] || ""}</td>
                      <td>{row[3] || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* --- שלב 10: פקדי עימוד --- */}
              <div
                className="pager"
                style={{
                  display: "flex",
                  gap: 8,
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginTop: 10,
                }}
              >
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <button
                    className="btn"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  >
                    Prev
                  </button>
                  <button
                    className="btn"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  >
                    Next
                  </button>
                  <span style={{ opacity: 0.8 }}>Page {page} / {totalPages}</span>
                </div>

                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <span style={{ opacity: 0.8 }}>Rows:</span>
                  <select
                    className="select"
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setPage(1);
                    }}
                  >
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                  <span style={{ opacity: 0.6 }}>Total: {totalItems}</span>
                </div>
              </div>
            </div>
          )}
          <div className="footer">{lastUpdated ? `עודכן: ${lastUpdated.toLocaleTimeString()}` : "—"}</div>
        </motion.div>
      </div>
    </>
  );
}
