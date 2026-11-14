import React from "react";
import {
  LayoutDashboard,
  Users,
  CalendarCheck,
  Megaphone,
  PhoneCall,
  Sparkles,
  LogOut,
  Radio,
  Cpu,
  Sun,
  Moon,
  Globe,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Sidebar({ activeTab, setActiveTab, onViewLanding }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "content", label: "Call Scripts & Prompts", icon: Sparkles },
    { id: "contacts", label: "Leads & Contacts", icon: Users },
    { id: "bookings", label: "Booked Demos", icon: CalendarCheck },
    { id: "campaigns", label: "Outbound Campaigns", icon: Megaphone },
    { id: "calls", label: "Call Logs & History", icon: PhoneCall },
  ];

  const userInitial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : "U";

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-logo">
        <div className="logo-badge">
          <Radio size={20} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--text-accent)", fontWeight: 800 }}>VoiceAgent</span>
            <span
              style={{
                fontSize: "10px",
                fontWeight: 700,
                padding: "2px 6px",
                borderRadius: "4px",
                background: "linear-gradient(135deg, var(--sarvam-orange), var(--sarvam-indigo))",
                color: "#ffffff",
                letterSpacing: "0.5px",
              }}
            >
              AI
            </span>
          </div>
          <div style={{ fontSize: "10.5px", color: "var(--text-light)", fontWeight: 500, letterSpacing: "0.3px", marginTop: "1px" }}>
            Sovereign Voice Stack
          </div>
        </div>
      </div>

      {/* Nav Links */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-link ${isActive ? "active" : ""}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={17} color={isActive ? "var(--sarvam-orange)" : "currentColor"} />
              <span>{item.label}</span>
            </button>
          );
        })}

        {onViewLanding && (
          <button
            className="nav-link"
            onClick={onViewLanding}
            style={{ marginTop: "6px", borderTop: "1px solid var(--border)", paddingTop: "12px" }}
          >
            <Globe size={17} color="var(--sarvam-indigo)" />
            <span>Public Home Page</span>
          </button>
        )}
      </nav>

      {/* Live AI Telemetry Pill */}
      <div className="sidebar-telemetry">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#34d399", fontWeight: 700, fontSize: "11px" }}>
            <span className="live-dot" style={{ width: "6px", height: "6px" }}></span>
            <span>LiveKit WebRTC Active</span>
          </span>
          <div className="soundwave-box" style={{ height: "14px" }}>
            <div className="soundwave-bar"></div>
            <div className="soundwave-bar"></div>
            <div className="soundwave-bar"></div>
            <div className="soundwave-bar"></div>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "3px", color: "var(--text-muted)", fontSize: "10.5px", fontFamily: "var(--font-mono)" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Latency</span>
            <span style={{ color: "var(--text-accent)" }}>~118ms (Aura)</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>LLM Brain</span>
            <span style={{ color: "var(--text-accent)" }}>Sarvam / 4o-mini</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Region</span>
            <span style={{ color: "var(--text-accent)" }}>Mumbai PoP</span>
          </div>
        </div>
      </div>

      {/* User Footer */}
      <div className="sidebar-user">
        <div className="user-profile">
          <div className="user-avatar">{userInitial}</div>
          <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <span
              style={{
                fontSize: "13px",
                fontWeight: 700,
                color: "var(--text-accent)",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {user?.full_name || user?.email || "User"}
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Administrator</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {/* Quick theme toggle in sidebar */}
          <button
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid var(--border)",
              cursor: "pointer",
              color: "var(--text-muted)",
              padding: "7px",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "var(--transition)",
            }}
          >
            {theme === "dark" ? <Sun size={14} color="#f59e0b" /> : <Moon size={14} color="#6366f1" />}
          </button>

          <button
            onClick={logout}
            title="Sign Out"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid var(--border)",
              cursor: "pointer",
              color: "var(--text-muted)",
              padding: "7px",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              transition: "var(--transition)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--rose-500)";
              e.currentTarget.style.borderColor = "rgba(244, 63, 94, 0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--text-muted)";
              e.currentTarget.style.borderColor = "var(--border)";
            }}
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}
