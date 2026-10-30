import React, { useState, useEffect } from "react";
import { PhoneCall, FileText, RefreshCw, X } from "lucide-react";
import { api } from "../services/api";
import { useToast } from "../components/Toast";

export default function CallLogs() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTranscript, setActiveTranscript] = useState(null);

  const { showToast } = useToast();

  useEffect(() => {
    fetchCalls();
  }, []);

  const fetchCalls = async () => {
    try {
      setLoading(true);
      const data = await api.getCalls();
      setCalls(data);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="saas-card">
        <div className="saas-card-header">
          <div className="saas-card-title">
            <PhoneCall size={18} color="var(--primary)" />
            <span>Voice Call Logs & Turn-by-Turn Transcripts</span>
          </div>
          <button className="btn btn-outline btn-sm" onClick={fetchCalls}>
            <RefreshCw size={13} />
            <span>Refresh</span>
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
                <th>Transcript</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    Loading call history...
                  </td>
                </tr>
              ) : !calls.length ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    No call logs recorded yet.
                  </td>
                </tr>
              ) : (
                calls.map((c) => (
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
                    <td>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => setActiveTranscript(c)}
                      >
                        <FileText size={13} />
                        <span>Transcript ({(c.turns || []).length})</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transcript Modal */}
      {activeTranscript && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "600px" }}>
            <div className="modal-header">
              <h3 className="modal-title">Turn-by-Turn Call Transcript</h3>
              <button className="modal-close" onClick={() => setActiveTranscript(null)}>
                <X size={18} />
              </button>
            </div>
            <div style={{ maxHeight: "420px", overflowY: "auto", paddingRight: "6px" }}>
              {!(activeTranscript.turns || []).length ? (
                <p style={{ textAlign: "center", color: "var(--text-muted)", padding: "30px" }}>
                  No audio turns recorded for this session.
                </p>
              ) : (
                activeTranscript.turns.map((t, idx) => (
                  <div
                    key={idx}
                    style={{
                      marginBottom: "12px",
                      padding: "12px 16px",
                      borderRadius: "10px",
                      background: t.speaker === "USER" ? "#f1f5f9" : "#eef2ff",
                      border: `1px solid ${t.speaker === "USER" ? "#e2e8f0" : "#e0e7ff"}`,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: "4px",
                      }}
                    >
                      <strong
                        style={{
                          fontSize: "11px",
                          textTransform: "uppercase",
                          letterSpacing: "0.5px",
                          color: t.speaker === "USER" ? "var(--text-main)" : "var(--primary)",
                        }}
                      >
                        {t.speaker === "USER" ? "Caller / Customer" : "Sarah (AI Sales Agent)"}:
                      </strong>
                      <span style={{ fontSize: "10px", color: "var(--text-light)" }}>
                        {t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : ""}
                      </span>
                    </div>
                    <p style={{ fontSize: "13.5px", color: "var(--text-main)", lineHeight: "1.5" }}>{t.text}</p>
                  </div>
                ))
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setActiveTranscript(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
