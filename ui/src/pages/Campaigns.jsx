import React, { useState, useEffect } from "react";
import { Megaphone, Play, Pause, Plus, RefreshCw, X, Download, FileSpreadsheet } from "lucide-react";
import { api } from "../services/api";
import { useToast } from "../components/Toast";

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: "", concurrency: 5, file: null });
  const [uploading, setUploading] = useState(false);

  const { showToast } = useToast();

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const data = await api.getCampaigns();
      setCampaigns(data);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (id) => {
    try {
      await api.startCampaign(id);
      showToast("Campaign started! Background dialer active.", "success");
      fetchCampaigns();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const handlePause = async (id) => {
    try {
      await api.pauseCampaign(id);
      showToast("Campaign paused", "info");
      fetchCampaigns();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!form.file) {
      showToast("Please select a CSV file", "error");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("name", form.name);
    formData.append("concurrency", form.concurrency);
    formData.append("file", form.file);

    try {
      await api.uploadCampaign(formData);
      showToast("Campaign created from CSV!", "success");
      setShowModal(false);
      setForm({ name: "", concurrency: 5, file: null });
      fetchCampaigns();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setUploading(false);
    }
  };

  const downloadSampleCSV = () => {
    const csvContent = "name,phone,company,city\n" +
      "Amit Sharma,+919876543210,Apex Technologies,Mumbai\n" +
      "Pooja Verma,+919812345678,Verma Retail Mart,Delhi\n" +
      "Rahul Gupta,+919922334455,Gupta Logistics,Bengaluru\n" +
      "Sunita Patel,+919833221100,Patel Pharma,Ahmedabad\n" +
      "Vikram Singh,+919877001122,Singh Auto Components,Pune\n";
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "sample_leads.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <div className="saas-card">
        <div className="saas-card-header">
          <div className="saas-card-title">
            <Megaphone size={18} color="var(--primary)" />
            <span>Automated Outbound Calling Campaigns</span>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button className="btn btn-outline btn-sm" onClick={downloadSampleCSV}>
              <Download size={13} />
              <span>Sample CSV</span>
            </button>
            <button className="btn btn-outline btn-sm" onClick={fetchCampaigns}>
              <RefreshCw size={13} />
              <span>Refresh</span>
            </button>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              <Plus size={14} />
              <span>New Campaign (CSV)</span>
            </button>
          </div>
        </div>

        <div className="table-wrap">
          <table className="saas-table">
            <thead>
              <tr>
                <th>Campaign Name</th>
                <th>Status</th>
                <th>Total Leads</th>
                <th>Dialing Progress</th>
                <th>Demos Booked</th>
                <th>Concurrency</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    Loading campaigns...
                  </td>
                </tr>
              ) : !campaigns.length ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    No campaigns created yet. Click "+ New Campaign (CSV)" to upload a lead batch!
                  </td>
                </tr>
              ) : (
                campaigns.map((c) => {
                  const isRunning = c.status === "RUNNING";
                  const percent = c.total_leads > 0 ? Math.round((c.called_leads / c.total_leads) * 100) : 0;

                  return (
                    <tr key={c.id}>
                      <td>
                        <strong>{c.name}</strong>
                      </td>
                      <td>
                        <span className={`badge ${isRunning ? "badge-interested" : "badge-not-interested"}`}>
                          {c.status}
                        </span>
                      </td>
                      <td>{c.total_leads}</td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <div
                            style={{
                              width: "80px",
                              height: "6px",
                              background: "var(--border)",
                              borderRadius: "4px",
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${percent}%`,
                                height: "100%",
                                background: "var(--primary)",
                              }}
                            ></div>
                          </div>
                          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                            {c.called_leads}/{c.total_leads}
                          </span>
                        </div>
                      </td>
                      <td>
                        <strong style={{ color: "var(--emerald-500)" }}>{c.booked_demos}</strong>
                      </td>
                      <td>{c.concurrency} parallel calls</td>
                      <td>
                        {isRunning ? (
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => handlePause(c.id)}
                            style={{ color: "var(--amber-500)" }}
                          >
                            <Pause size={13} />
                            <span>Pause</span>
                          </button>
                        ) : (
                          <button className="btn btn-primary btn-sm" onClick={() => handleStart(c.id)}>
                            <Play size={13} />
                            <span>Start Dialing</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Campaign Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "540px" }}>
            <div className="modal-header">
              <h3 className="modal-title">Create Outbound Calling Campaign</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleUpload}>
              <div className="form-group">
                <label className="form-label">Campaign Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Delhi NCR Real Estate Batch"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Parallel Dialing Concurrency</label>
                <input
                  type="number"
                  className="form-input"
                  value={form.concurrency}
                  min={1}
                  max={20}
                  onChange={(e) => setForm({ ...form, concurrency: parseInt(e.target.value) || 5 })}
                  required
                />
                <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                  Number of leads to dial simultaneously in parallel (1 - 20)
                </span>
              </div>

              {/* Sample Format Preview Box */}
              <div
                style={{
                  background: "var(--bg-card-subtle)",
                  border: "1px dashed var(--border)",
                  borderRadius: "8px",
                  padding: "12px",
                  marginBottom: "16px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", fontWeight: "600" }}>
                    <FileSpreadsheet size={14} color="var(--primary)" />
                    <span>Expected CSV Columns</span>
                  </div>
                  <button
                    type="button"
                    onClick={downloadSampleCSV}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--primary)",
                      fontSize: "12px",
                      fontWeight: "600",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    <Download size={12} />
                    <span>Download Sample</span>
                  </button>
                </div>
                <code
                  style={{
                    display: "block",
                    fontSize: "11px",
                    padding: "8px",
                    background: "var(--bg-main)",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    color: "var(--text-main)",
                    lineHeight: "1.5",
                  }}
                >
                  name,phone,company,city<br />
                  Amit Sharma,+919876543210,Apex Tech,Mumbai<br />
                  Pooja Verma,+919812345678,Verma Mart,Delhi
                </code>
              </div>

              <div className="form-group">
                <label className="form-label">Select Leads CSV File</label>
                <input
                  type="file"
                  className="form-input"
                  accept=".csv"
                  onChange={(e) => setForm({ ...form, file: e.target.files[0] })}
                  required
                />
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={uploading}>
                  {uploading ? "Uploading..." : "Upload & Create Campaign"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
