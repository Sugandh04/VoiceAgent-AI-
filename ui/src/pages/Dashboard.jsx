import React, { useEffect, useState } from "react";
import { Users, CalendarCheck, PhoneCall, PhoneOff, TrendingUp, Sparkles, ArrowRight } from "lucide-react";
import { api } from "../services/api";

export default function Dashboard({ setActiveTab }) {
  const [stats, setStats] = useState({
    total_leads: 0,
    demos_booked: 0,
    total_calls: 0,
    calls_connected: 0,
    calls_not_picked: 0,
    conversion_rate: 0,
  });
  const [recentCalls, setRecentCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [s, c] = await Promise.all([api.getStats(), api.getCalls()]);
      setStats(s);
      setRecentCalls(c.slice(0, 6));
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  const kpis = [
    {
      label: "Total Leads",
      value: stats.total_leads,
      badge: "In Database",
      icon: Users,
      bg: "#e0e7ff",
      color: "#4338ca",
    },
    {
      label: "5-Min Demos Booked",
      value: stats.demos_booked,
      badge: "Phone Callbacks",
      icon: CalendarCheck,
      bg: "#d1fae5",
      color: "#047857",
    },
    {
      label: "Calls Connected",
      value: stats.calls_connected,
      badge: "Answered",
      icon: PhoneCall,
      bg: "#cffafe",
      color: "#0e7490",
    },
    {
      label: "Calls Not Picked / Busy",
      value: stats.calls_not_picked,
      badge: "AMD Filtered",
      icon: PhoneOff,
      bg: "#fef3c7",
      color: "#b45309",
    },
    {
      label: "Conversion Rate",
      value: `${stats.conversion_rate}%`,
      badge: "Demo / Lead",
      icon: TrendingUp,
      bg: "#e0e7ff",
      color: "#4f46e5",
    },
  ];

  return (
    <div>
      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpis.map((k, idx) => {
          const Icon = k.icon;
          return (
            <div key={idx} className="kpi-card">
              <div>
                <span className="kpi-label">{k.label}</span>
                <div className="kpi-value">{loading ? "..." : k.value}</div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "9999px",
                    background: k.bg,
                    color: k.color,
                  }}
                >
                  {k.badge}
                </span>
              </div>
              <div className="kpi-icon" style={{ background: k.bg, color: k.color }}>
                <Icon size={22} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Action Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, #4f46e5, #6366f1)",
          borderRadius: "16px",
          padding: "24px 28px",
          color: "#ffffff",
          marginBottom: "32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
          boxShadow: "0 10px 25px -5px rgba(79, 70, 229, 0.25)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <Sparkles size={18} color="#fde047" />
            <h3 style={{ fontSize: "17px", fontWeight: 800 }}>Sarah AI Voice Calling Engine Active</h3>
          </div>
          <p style={{ fontSize: "13.5px", opacity: 0.9 }}>
            Sarah connects to callers via WebRTC & Exotel PSTN, pitches 5-minute phone demos, and records all bookings into SQLite.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            className="btn"
            style={{ background: "#ffffff", color: "var(--primary)", border: "none" }}
            onClick={() => setActiveTab("contacts")}
          >
            <span>Manage Leads</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Recent Voice Calls Table */}
      <div className="saas-card">
        <div className="saas-card-header">
          <div className="saas-card-title">
            <PhoneCall size={18} color="var(--primary)" />
            <span>Recent Voice Call Sessions</span>
          </div>
          <button className="btn btn-outline btn-sm" onClick={() => setActiveTab("calls")}>
            View All Calls
          </button>
        </div>

        <div className="table-wrap">
          <table className="saas-table">
            <thead>
              <tr>
                <th>Call Session SID</th>
                <th>Participant / Phone</th>
                <th>Call Status</th>
                <th>Duration</th>
                <th>Date & Time</th>
              </tr>
            </thead>
            <tbody>
              {!recentCalls.length ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: "center", padding: "36px", color: "var(--text-muted)" }}>
                    No call sessions recorded yet. Start a session from LiveKit Console or click "Quick Dial Test"!
                  </td>
                </tr>
              ) : (
                recentCalls.map((c) => (
                  <tr key={c.id || c.call_sid}>
                    <td>
                      <strong>{c.call_sid}</strong>
                    </td>
                    <td>{c.from_number || "Browser WebRTC"}</td>
                    <td>
                      <span className={`badge ${c.status === "COMPLETED" ? "badge-demo" : "badge-no-answer"}`}>
                        {c.status}
                      </span>
                    </td>
                    <td>{c.duration_seconds || 0}s</td>
                    <td>{new Date(c.start_time).toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
