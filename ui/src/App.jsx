import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./components/Toast";
import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";
import AuthModal from "./pages/AuthModal";
import Dashboard from "./pages/Dashboard";
import Contacts from "./pages/Contacts";
import Bookings from "./pages/Bookings";
import Campaigns from "./pages/Campaigns";
import CallLogs from "./pages/CallLogs";

function MainApp() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const { isAuthenticated, showAuthModal, loading } = useAuth();

  const titles = {
    dashboard: "Dashboard Overview",
    contacts: "Leads & Contacts Management",
    bookings: "Scheduled 5-Min Phone Demos",
    campaigns: "Outbound Calling Campaigns",
    calls: "Call Logs & Transcripts",
  };

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          height: "100vh",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg-main)",
          color: "var(--text-muted)",
          fontSize: "14px",
          fontWeight: 600,
        }}
      >
        Loading VoiceAgent AI Platform...
      </div>
    );
  }

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="main-wrapper">
        <Navbar
          title={titles[activeTab] || "VoiceAgent AI"}
          onCallTriggered={() => {
            if (activeTab === "dashboard" || activeTab === "calls") {
              setActiveTab("calls");
            }
          }}
        />

        <div className="content-viewport">
          {activeTab === "dashboard" && <Dashboard setActiveTab={setActiveTab} />}
          {activeTab === "contacts" && <Contacts />}
          {activeTab === "bookings" && <Bookings />}
          {activeTab === "campaigns" && <Campaigns />}
          {activeTab === "calls" && <CallLogs />}
        </div>
      </main>

      {/* Auth Modal Overlay when not authenticated */}
      {(!isAuthenticated || showAuthModal) && <AuthModal />}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <MainApp />
      </ToastProvider>
    </AuthProvider>
  );
}
