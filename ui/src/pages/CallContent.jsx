import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Plus,
  CheckCircle,
  Radio,
  Trash2,
  Edit,
  ShieldCheck,
  RefreshCw,
  Gift,
  PartyPopper,
  Flame,
  Zap,
  Sliders,
} from "lucide-react";
import { api } from "../services/api";
import { useToast } from "../components/Toast";

const PRESETS = [
  {
    title: "🎉 New Year Special Offer",
    content_type: "NEW_YEAR",
    greeting_override:
      "Happy New Year! This is Sarah from VoiceAgent AI. Wishing you and your business immense success in the new year! Am I speaking with the business owner?",
    prompt_text:
      "NEW YEAR SPECIAL CONTEXT:\n- Greet the prospect warmly wishing them a prosperous New Year.\n- Mention our New Year special: 'We are offering free onboarding and 500 complimentary voice minutes to start the new year strong.'\n- Emphasize how automated AI calls will help them beat competitors and scale sales in the new year.\n- Book a 5-minute phone demo for this week to claim the New Year voucher.",
  },
  {
    title: "🎄 Christmas Holiday Demo Promo",
    content_type: "CHRISTMAS",
    greeting_override:
      "Merry Christmas and season's greetings! This is Sarah from VoiceAgent AI. Hope you're having a wonderful holiday season! Am I speaking with the business head?",
    prompt_text:
      "CHRISTMAS HOLIDAY CONTEXT:\n- Start with cheerful Christmas greetings.\n- Value angle: 'Holiday season means high incoming customer inquiries. Our AI agent ensures you never miss a customer even when your staff is on holiday break.'\n- Propose a quick 5-minute phone demo to set up their automated answering before year-end.\n- Keep the tone celebratory, polite, and encouraging.",
  },
  {
    title: "🪔 Diwali Business Growth Offer",
    content_type: "DIWALI",
    greeting_override:
      "Shubh Deepavali! This is Sarah calling from VoiceAgent AI. Wishing your business prosperity and light this festive season! May I speak with the owner?",
    prompt_text:
      "DIWALI FESTIVE CAMPAIGN:\n- Wish Shubh Deepavali with high warmth.\n- Highlight: Festive order rush requires 24/7 immediate call response.\n- Offer our festive 20% discount on annual voice minutes.\n- Goal: Confirm a 5-minute phone demo for tomorrow or day after.",
  },
  {
    title: "🚀 Product Launch Special",
    content_type: "PRODUCT_LAUNCH",
    greeting_override:
      "Hello! This is Sarah from VoiceAgent AI. We just launched our Voice 3.0 ultra-low latency engine with Hindi support! Am I speaking with the founder?",
    prompt_text:
      "PRODUCT 3.0 LAUNCH CONTEXT:\n- Announce the new VoiceAgent AI 3.0 engine with sub-120ms latency and native Hinglish support.\n- Highlight that human callers cannot tell it is an AI agent.\n- Offer an exclusive early-adopter beta slot with priority setup.\n- Book a 5-minute live phone demo on their mobile number.",
  },
];

export default function CallContent() {
  const [contents, setContents] = useState([]);
  const [activeContent, setActiveContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    title: "",
    content_type: "CUSTOM",
    greeting_override: "",
    prompt_text: "",
  });

  const { showToast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [list, active] = await Promise.all([
        api.getCallContents(),
        api.getActiveCallContent(),
      ]);
      setContents(list || []);
      setActiveContent(active || null);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = (preset = null) => {
    setEditingItem(null);
    if (preset) {
      setFormData({
        title: preset.title,
        content_type: preset.content_type,
        greeting_override: preset.greeting_override,
        prompt_text: preset.prompt_text,
      });
    } else {
      setFormData({
        title: "",
        content_type: "CUSTOM",
        greeting_override: "",
        prompt_text: "",
      });
    }
    setShowModal(true);
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setFormData({
      title: item.title,
      content_type: item.content_type,
      greeting_override: item.greeting_override || "",
      prompt_text: item.prompt_text,
    });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.prompt_text.trim()) {
      showToast("Please provide both a title and prompt text.", "error");
      return;
    }
    try {
      setSubmitting(true);
      if (editingItem) {
        await api.updateCallContent(editingItem.id, formData);
        showToast("Script updated successfully!", "success");
      } else {
        await api.createCallContent(formData);
        showToast("New script created and validated by PromptGuard!", "success");
      }
      setShowModal(false);
      await loadData();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleActivate = async (id) => {
    try {
      await api.activateCallContent(id);
      showToast("Script activated! Sarah will now use this prompt for all calls.", "success");
      await loadData();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const handleDeactivateAll = async () => {
    try {
      await api.deactivateAllCallContent();
      showToast("Reverted to default Sarah sales pitch.", "info");
      await loadData();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this script?")) return;
    try {
      await api.deleteCallContent(id);
      showToast("Script deleted.", "success");
      await loadData();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  return (
    <div>
      {/* ── ACTIVE PERSONA BANNER ── */}
      <div
        className="saas-card"
        style={{
          marginBottom: "24px",
          background: activeContent
            ? "linear-gradient(135deg, rgba(255, 107, 53, 0.1) 0%, rgba(79, 70, 229, 0.1) 100%)"
            : "var(--bg-card)",
          border: activeContent
            ? "1px solid rgba(255, 107, 53, 0.4)"
            : "1px solid var(--border)",
          boxShadow: activeContent ? "0 10px 30px -10px var(--sarvam-orange-glow)" : "var(--shadow-sm)",
        }}
      >
        <div style={{ padding: "24px 28px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 12px",
                  borderRadius: "var(--radius-full)",
                  fontSize: "11.5px",
                  fontWeight: 700,
                  background: activeContent ? "var(--emerald-bg)" : "rgba(255, 255, 255, 0.05)",
                  color: activeContent ? "#34d399" : "var(--text-muted)",
                  border: `1px solid ${activeContent ? "#10b98140" : "var(--border)"}`,
                }}
              >
                <Radio size={12} className={activeContent ? "pulse" : ""} />
                {activeContent ? "CUSTOM PROMPT ACTIVE IN LIVE CALLS" : "DEFAULT SALES PERSONA"}
              </span>
              <span style={{ fontSize: "11.5px", color: "var(--text-muted)", display: "inline-flex", alignItems: "center", gap: "5px" }}>
                <ShieldCheck size={14} color="#10b981" />
                PromptGuard Layer Active
              </span>
            </div>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "20px", fontWeight: 700, margin: 0, color: "#ffffff" }}>
              {activeContent ? activeContent.title : "Standard B2B Sales Pitch (Sarah)"}
            </h2>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px", marginBottom: 0, maxWidth: "700px" }}>
              {activeContent
                ? `Greeting override: "${activeContent.greeting_override || 'Standard greeting'}"`
                : "Sarah is using the baseline B2B owner qualification and 5-min phone demo booking flow."}
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px" }}>
            {activeContent && (
              <button className="btn btn-outline btn-sm" onClick={handleDeactivateAll}>
                Revert to Default Pitch
              </button>
            )}
            <button className="btn btn-primary btn-sm" onClick={() => openCreateModal()}>
              <Plus size={14} />
              <span>Create Custom Script</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── QUICK-APPLY PRESETS ── */}
      <div style={{ marginBottom: "28px" }}>
        <h3
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "15px",
            fontWeight: 700,
            color: "#ffffff",
            marginBottom: "14px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <Sparkles size={16} color="var(--sarvam-orange)" />
          <span>Seasonal & Campaign Presets (1-Click Load)</span>
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px" }}>
          {PRESETS.map((p, idx) => (
            <div
              key={idx}
              className="saas-card"
              style={{
                cursor: "pointer",
                transition: "var(--transition)",
                padding: "18px",
                marginBottom: 0,
                background: "rgba(18, 24, 36, 0.7)",
              }}
              onClick={() => openCreateModal(p)}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--sarvam-orange)";
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "var(--shadow-glow)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "var(--shadow-xs)";
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "10.5px", fontWeight: 700, padding: "2px 8px", borderRadius: "var(--radius-full)", background: "rgba(255, 107, 53, 0.12)", color: "var(--sarvam-orange)", border: "1px solid rgba(255, 107, 53, 0.3)" }}>
                  {p.content_type}
                </span>
                <Plus size={14} color="var(--sarvam-orange)" />
              </div>
              <h4 style={{ fontFamily: "var(--font-display)", fontSize: "14px", fontWeight: 700, margin: "0 0 6px 0", color: "#ffffff" }}>
                {p.title}
              </h4>
              <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: 0, lineClamp: 2, WebkitLineClamp: 2, display: "-webkit-box", WebkitBoxOrient: "vertical", overflow: "hidden", lineHeight: "1.4" }}>
                {p.greeting_override}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ── SAVED SCRIPTS TABLE ── */}
      <div className="saas-card">
        <div className="saas-card-header">
          <div className="saas-card-title">
            <Sliders size={18} color="var(--sarvam-orange)" />
            <span>Saved Call Scripts ({contents.length})</span>
          </div>
          <button className="btn btn-outline btn-sm" onClick={loadData}>
            <RefreshCw size={13} />
            <span>Refresh</span>
          </button>
        </div>

        <div className="table-wrap">
          <table className="saas-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Title & Type</th>
                <th>Greeting Spoken First</th>
                <th>Prompt Instructions</th>
                <th>Created</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    Loading call scripts...
                  </td>
                </tr>
              ) : !contents.length ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    No custom scripts yet. Click "Create Custom Script" or load a Seasonal Preset above!
                  </td>
                </tr>
              ) : (
                contents.map((c) => (
                  <tr key={c.id}>
                    <td>
                      {c.is_active ? (
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "5px",
                            padding: "3px 9px",
                            borderRadius: "var(--radius-full)",
                            fontSize: "11px",
                            fontWeight: 700,
                            background: "var(--emerald-bg)",
                            color: "#34d399",
                            border: "1px solid rgba(16, 185, 129, 0.3)",
                          }}
                        >
                          <CheckCircle size={12} />
                          Active
                        </span>
                      ) : (
                        <span style={{ fontSize: "11px", color: "var(--text-light)" }}>Inactive</span>
                      )}
                    </td>
                    <td>
                      <strong style={{ color: "#ffffff" }}>{c.title}</strong>
                      <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginTop: "2px", fontFamily: "var(--font-mono)" }}>
                        Tag: {c.content_type}
                      </div>
                    </td>
                    <td style={{ maxWidth: "220px", fontSize: "12px", color: "var(--text-muted)" }}>
                      {c.greeting_override ? (
                        <span title={c.greeting_override}>
                          "{c.greeting_override.length > 55 ? c.greeting_override.substring(0, 55) + "..." : c.greeting_override}"
                        </span>
                      ) : (
                        <em style={{ color: "var(--text-light)" }}>Default greeting</em>
                      )}
                    </td>
                    <td style={{ maxWidth: "300px", fontSize: "12px", color: "var(--text-muted)" }}>
                      <span title={c.prompt_text}>
                        {c.prompt_text.length > 75 ? c.prompt_text.substring(0, 75) + "..." : c.prompt_text}
                      </span>
                    </td>
                    <td style={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: "6px" }}>
                        {!c.is_active && (
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => handleActivate(c.id)}
                            title="Set as active prompt for calls"
                          >
                            Activate
                          </button>
                        )}
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => openEditModal(c)}
                          title="Edit"
                        >
                          <Edit size={13} />
                        </button>
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => handleDelete(c.id)}
                          title="Delete"
                          style={{ color: "var(--rose-500)" }}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── MODAL: CREATE / EDIT SCRIPT ── */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "600px" }}>
            <div className="modal-header">
              <h3 className="modal-title">
                {editingItem ? "Edit Call Script" : "Create New Call Script"}
              </h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "12px" }}>
                <div>
                  <label className="form-label">Script Title *</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="e.g. New Year 2027 Special Demo"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  />
                </div>
                <div>
                  <label className="form-label">Category</label>
                  <select
                    className="form-select"
                    value={formData.content_type}
                    onChange={(e) => setFormData({ ...formData, content_type: e.target.value })}
                  >
                    <option value="NEW_YEAR">NEW_YEAR</option>
                    <option value="CHRISTMAS">CHRISTMAS</option>
                    <option value="DIWALI">DIWALI</option>
                    <option value="PRODUCT_LAUNCH">PRODUCT_LAUNCH</option>
                    <option value="SEASONAL">SEASONAL</option>
                    <option value="CUSTOM">CUSTOM</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="form-label">Greeting Message Override (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="The first sentence Sarah says when the call connects"
                  value={formData.greeting_override}
                  onChange={(e) => setFormData({ ...formData, greeting_override: e.target.value })}
                />
                <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                  Leave blank to use Sarah's default warm greeting.
                </span>
              </div>

              <div>
                <label className="form-label">Prompt Instructions / Pitch Details *</label>
                <textarea
                  rows={6}
                  required
                  className="form-textarea"
                  placeholder="Instructions for Sarah on what to say, special offers, festive greetings, and objections handling..."
                  value={formData.prompt_text}
                  onChange={(e) => setFormData({ ...formData, prompt_text: e.target.value })}
                />
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "6px" }}>
                  <span style={{ fontSize: "11px", color: "#34d399", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    <ShieldCheck size={13} color="#10b981" />
                    Validated in real time by PromptGuard security
                  </span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    {formData.prompt_text.length} / 1000 characters
                  </span>
                </div>
              </div>

              <div className="modal-footer" style={{ marginTop: "8px" }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Validating & Saving..." : editingItem ? "Update Script" : "Save Script"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
