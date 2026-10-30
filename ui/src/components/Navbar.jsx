import React from "react";
import { PhoneForwarded, ExternalLink } from "lucide-react";
import { api } from "../services/api";
import { useToast } from "./Toast";

export default function Navbar({ title, onCallTriggered }) {
  const { showToast } = useToast();

  const handleQuickDial = async () => {
    const phone = window.prompt("Enter Indian mobile phone number to dial (e.g. +919876543210):");
    if (!phone) return;

    try {
      const res = await api.triggerOutboundCall(phone, "Manual Test Call from SaaS Navbar");
      showToast(`Outbound call initiated! SID: ${res.callSid}`, "success");
      if (onCallTriggered) onCallTriggered();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  return (
    <header className="topbar">
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <h1 style={{ fontSize: "20px", fontWeight: 800, letterSpacing: "-0.5px" }}>{title}</h1>
        <div className="topbar-status">
          <span className="live-dot"></span>
          <span>Sarah Voice Agent Live</span>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <button className="btn btn-outline btn-sm" onClick={handleQuickDial}>
          <PhoneForwarded size={14} />
          <span>Quick Dial Test</span>
        </button>
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="btn btn-outline btn-sm"
          style={{ textDecoration: "none" }}
        >
          <ExternalLink size={14} />
          <span>Swagger API</span>
        </a>
      </div>
    </header>
  );
}
