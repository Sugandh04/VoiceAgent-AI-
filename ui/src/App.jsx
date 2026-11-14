import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./components/Toast";
import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";
import AuthModal from "./pages/AuthModal";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import CallContent from "./pages/CallContent";
import Contacts from "./pages/Contacts";
import Bookings from "./pages/Bookings";
import Campaigns from "./pages/Campaigns";
import CallLogs from "./pages/CallLogs";

function MainApp() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [userRequestedView, setUserRequestedView] = useState(null); // 'landing' or 'console'
  const { isAuthenticated, showAuthModal, setShowAuthModal, loading } = useAuth();

  // Determine active view: if not authenticated, default to landing; if authenticated, default to console
  const activeView = userRequestedView || (isAuthenticated ? "console" : "landing");

  const titles = {
    dashboard: "Dashboard Overview",
    content: "Call Scripts & AI Persona Content",
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

  if (activeView === "landing") {
    return (
      <>
        <LandingPage
          onLaunchConsole={() => {
            if (isAuthenticated) {
              setUserRequestedView("console");
            } else {
              setShowAuthModal(true);
            }
          }}
        />
        {showAuthModal && <AuthModal />}
      </>
    );
  }

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onViewLanding={() => setUserRequestedView("landing")}
      />

      {/* Main Content Area */}
      <main className="main-wrapper">
        <Navbar
          title={titles[activeTab] || "VoiceAgent AI"}
          onViewLanding={() => setUserRequestedView("landing")}
          onCallTriggered={() => {
            if (activeTab === "dashboard" || activeTab === "calls") {
              setActiveTab("calls");
            }
          }}
        />

        <div className="content-viewport">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
            >
              {activeTab === "dashboard" && <Dashboard setActiveTab={setActiveTab} />}
              {activeTab === "content" && <CallContent />}
              {activeTab === "contacts" && <Contacts />}
              {activeTab === "bookings" && <Bookings />}
              {activeTab === "campaigns" && <Campaigns />}
              {activeTab === "calls" && <CallLogs />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* Auth Modal Overlay when requested */}
      {showAuthModal && <AuthModal />}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <MainApp />
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
