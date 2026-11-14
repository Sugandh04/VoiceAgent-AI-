import React, { useState, useEffect, useRef } from "react";
import {
  PhoneCall,
  PhoneOff,
  ExternalLink,
  Sparkles,
  Radio,
  X,
  Mic,
  Cpu,
  ShieldCheck,
  Zap,
  Sun,
  Moon,
  Globe,
} from "lucide-react";
import { api } from "../services/api";
import { useToast } from "./Toast";
import { useTheme } from "../context/ThemeContext";
import VoiceOrb3D from "./VoiceOrb3D";

export default function Navbar({ title, onCallTriggered, onViewLanding }) {
  const { theme, toggleTheme } = useTheme();
  const { showToast } = useToast();
  const [showStudioModal, setShowStudioModal] = useState(false);
  const [testMode, setTestMode] = useState("webrtc"); // "webrtc" or "pstn"
  const [phoneNumber, setPhoneNumber] = useState("+91");
  const [isCalling, setIsCalling] = useState(false);
  const [callSession, setCallSession] = useState(null);
  const [callDuration, setCallDuration] = useState(0);

  const timerRef = useRef(null);

  useEffect(() => {
    if (isCalling) {
      setCallDuration(0);
      timerRef.current = setInterval(() => {
        setCallDuration((d) => d + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isCalling]);

  const formatDuration = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const handleStartCall = async (e) => {
    e.preventDefault();
    try {
      setIsCalling(true);
      const destination = testMode === "webrtc" ? "Browser WebRTC User" : phoneNumber;

      const res = await api.triggerOutboundCall(
        destination,
        testMode === "webrtc" ? "Interactive WebRTC Studio Test" : "PSTN Mobile Carrier Test"
      );

      setCallSession(res);
      showToast(
        testMode === "webrtc"
          ? "Live WebRTC audio channel connected with Sarah!"
          : `Outbound PSTN call dispatched to ${phoneNumber}`,
        "success"
      );
      if (onCallTriggered) onCallTriggered();
    } catch (err) {
      setIsCalling(false);
      showToast(`Call initiation failed: ${err.message}`, "error");
    }
  };

  const handleEndCall = () => {
    setIsCalling(false);
    showToast(`Test call ended (${formatDuration(callDuration)}).`, "info");
    setCallSession(null);
  };

  return (
    <>
      <header className="topbar">
        {/* Left Section: Title & Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "19px",
              fontWeight: 700,
              letterSpacing: "-0.3px",
              color: "#ffffff",
            }}
          >
            {title}
          </h1>
          <div className="topbar-status">
            <span className="live-dot"></span>
            <span>Sarah Voice Agent Active</span>
          </div>
        </div>

        {/* Right Section: Telemetry & Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {/* Audio latency pill */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "5px 12px",
              borderRadius: "var(--radius-full)",
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border)",
              fontSize: "11px",
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
            }}
          >
            <Zap size={12} color="var(--sarvam-orange)" />
            <span>Sub-120ms Latency</span>
          </div>

          {/* Theme Toggle (Dark / Light) */}
          <button
            className="btn btn-outline btn-sm theme-toggle-btn"
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            style={{
              padding: "6px 12px",
              borderRadius: "var(--radius-full)",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              cursor: "pointer",
            }}
          >
            {theme === "dark" ? (
              <>
                <Sun size={13} color="#f59e0b" />
                <span style={{ fontSize: "11.5px", fontWeight: 700 }}>Light</span>
              </>
            ) : (
              <>
                <Moon size={13} color="#6366f1" />
                <span style={{ fontSize: "11.5px", fontWeight: 700 }}>Dark</span>
              </>
            )}
          </button>

          {/* Voice AI Studio Test Button */}
          <button className="btn btn-primary btn-sm" onClick={() => setShowStudioModal(true)}>
            <div className="soundwave-box" style={{ height: "12px", marginRight: "2px" }}>
              <div className="soundwave-bar" style={{ background: "#ffffff" }}></div>
              <div className="soundwave-bar" style={{ background: "#ffffff" }}></div>
              <div className="soundwave-bar" style={{ background: "#ffffff" }}></div>
            </div>
            <span>Live Agent Studio</span>
          </button>

          {/* Home / Landing Page button */}
          {onViewLanding && (
            <button
              className="btn btn-outline btn-sm"
              onClick={onViewLanding}
              title="View Public Home Page"
              style={{ display: "flex", alignItems: "center", gap: "5px" }}
            >
              <Globe size={13} color="var(--sarvam-indigo)" />
              <span>Home</span>
            </button>
          )}

          {/* Swagger link */}
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="btn btn-outline btn-sm"
            style={{ textDecoration: "none" }}
          >
            <ExternalLink size={13} />
            <span>API Docs</span>
          </a>
        </div>
      </header>

      {/* ── INTERACTIVE VOICE AI STUDIO TEST MODAL ── */}
      {showStudioModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "560px" }}>
            <div className="modal-header">
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "10px",
                    background: "linear-gradient(135deg, var(--sarvam-orange), var(--sarvam-indigo))",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#ffffff",
                    boxShadow: "0 0 16px var(--sarvam-orange-glow)",
                  }}
                >
                  <Radio size={18} />
                </div>
                <div>
                  <h3 className="modal-title" style={{ fontSize: "17px", margin: 0 }}>
                    Voice AI Studio Test
                  </h3>
                  <div style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Test Sarah's speech pipeline in real time
                  </div>
                </div>
              </div>
              <button
                className="modal-close"
                onClick={() => {
                  if (isCalling) handleEndCall();
                  setShowStudioModal(false);
                }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Calling Active View */}
            {isCalling ? (
              <div style={{ textAlign: "center", padding: "8px 0" }}>
                {/* 3D Neural Voice Orb */}
                <div style={{ display: "flex", justifyContent: "center", marginBottom: "12px" }}>
                  <VoiceOrb3D size={160} isActive={true} isSpeaking={isCalling} />
                </div>

                <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                  <span className="live-dot"></span>
                  <span style={{ fontSize: "12px", fontWeight: 700, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    {testMode === "webrtc" ? "Live WebRTC Audio Channel Active" : "Carrier Dial Connected"}
                  </span>
                </div>

                <h4 style={{ fontSize: "20px", fontWeight: 800, color: "#ffffff", margin: "0 0 4px 0" }}>
                  Sarah (VoiceAgent AI)
                </h4>
                <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "0 0 16px 0" }}>
                  {testMode === "webrtc" ? "Connected via Browser Microphone & Opus" : `Calling ${phoneNumber}`}
                </p>

                {/* Duration Counter */}
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "32px",
                    fontWeight: 700,
                    color: "var(--sarvam-orange)",
                    letterSpacing: "1px",
                    marginBottom: "20px",
                  }}
                >
                  {formatDuration(callDuration)}
                </div>

                {/* Pipeline Diagnostic Telemetry */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "8px",
                    background: "rgba(0,0,0,0.3)",
                    padding: "12px",
                    borderRadius: "10px",
                    border: "1px solid var(--border)",
                    marginBottom: "20px",
                    fontSize: "11px",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-muted)",
                    textAlign: "left",
                  }}
                >
                  <div>VAD: <span style={{ color: "#ffffff" }}>Silero (150ms)</span></div>
                  <div>TTS: <span style={{ color: "#ffffff" }}>Deepgram Aura (118ms)</span></div>
                  <div>LLM: <span style={{ color: "#ffffff" }}>Sarvam 105B / 4o-mini</span></div>
                  <div>Guard: <span style={{ color: "#34d399" }}>PromptGuard Active</span></div>
                </div>

                <button
                  className="btn btn-danger"
                  style={{ width: "100%", padding: "12px", fontSize: "13.5px" }}
                  onClick={handleEndCall}
                >
                  <PhoneOff size={16} />
                  <span>End Voice Session</span>
                </button>
              </div>
            ) : (
              /* Pre-call setup view */
              <form onSubmit={handleStartCall}>
                {/* Mode Selector Tabs */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "8px",
                    background: "rgba(0, 0, 0, 0.35)",
                    padding: "4px",
                    borderRadius: "10px",
                    border: "1px solid var(--border)",
                    marginBottom: "20px",
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setTestMode("webrtc")}
                    style={{
                      padding: "10px",
                      borderRadius: "8px",
                      border: "none",
                      background: testMode === "webrtc" ? "linear-gradient(135deg, var(--sarvam-orange), #ea580c)" : "transparent",
                      color: testMode === "webrtc" ? "#ffffff" : "var(--text-muted)",
                      fontWeight: 700,
                      fontSize: "12.5px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "6px",
                      transition: "var(--transition)",
                    }}
                  >
                    <Mic size={15} />
                    <span>Browser WebRTC (Free)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setTestMode("pstn")}
                    style={{
                      padding: "10px",
                      borderRadius: "8px",
                      border: "none",
                      background: testMode === "pstn" ? "linear-gradient(135deg, var(--sarvam-indigo), #4338ca)" : "transparent",
                      color: testMode === "pstn" ? "#ffffff" : "var(--text-muted)",
                      fontWeight: 700,
                      fontSize: "12.5px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "6px",
                      transition: "var(--transition)",
                    }}
                  >
                    <PhoneCall size={15} />
                    <span>Mobile Phone (PSTN)</span>
                  </button>
                </div>

                {testMode === "webrtc" ? (
                  <div
                    style={{
                      padding: "16px",
                      borderRadius: "12px",
                      background: "rgba(255, 107, 53, 0.05)",
                      border: "1px solid rgba(255, 107, 53, 0.2)",
                      marginBottom: "20px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                      <Sparkles size={16} color="var(--sarvam-orange)" />
                      <strong style={{ fontSize: "13px", color: "var(--text-accent)" }}>
                        Direct High-Fidelity Audio Test
                      </strong>
                    </div>
                    <p style={{ fontSize: "12.5px", color: "var(--text-muted)", margin: 0, lineHeight: "1.5" }}>
                      Connects directly through LiveKit WebRTC (UDP/Opus 48kHz). Talk naturally with Sarah using your computer microphone. Sub-120ms human response time.
                    </p>
                  </div>
                ) : (
                  <div style={{ marginBottom: "20px" }}>
                    <label className="form-label">Destination Indian Mobile Number</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="+919876543210"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      required
                    />
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                      Triggers real outbound GSM call via Exotel / LiveKit SIP Trunk.
                    </span>
                  </div>
                )}

                {/* Features Highlights */}
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-light)", marginBottom: "20px", padding: "0 4px" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <ShieldCheck size={13} color="#10b981" /> PromptGuard Protected
                  </span>
                  <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <Cpu size={13} color="var(--sarvam-orange)" /> Live VAD Interruption
                  </span>
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: "100%", padding: "12px", fontSize: "13.5px" }}
                >
                  <PhoneCall size={16} />
                  <span>Start Live Voice Test</span>
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
