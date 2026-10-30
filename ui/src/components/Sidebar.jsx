import React from "react";
import { LayoutDashboard, Users, CalendarCheck, Megaphone, PhoneCall, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Sidebar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "contacts", label: "Leads & Contacts", icon: Users },
    { id: "bookings", label: "Booked Demos", icon: CalendarCheck },
    { id: "campaigns", label: "Outbound Campaigns", icon: Megaphone },
    { id: "calls", label: "Call Logs & History", icon: PhoneCall },
  ];

  const userInitial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : "U";

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-badge">🎙️</div>
        <span>VoiceAgent AI</span>
      </div>

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
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-user">
        <div className="user-profile">
          <div className="user-avatar">{userInitial}</div>
          <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-main)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {user?.full_name || user?.email || "User"}
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Administrator</span>
          </div>
        </div>
        <button
          onClick={logout}
          title="Sign Out"
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            color: "var(--text-light)",
            padding: "6px",
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--rose-500)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-light)")}
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
}
