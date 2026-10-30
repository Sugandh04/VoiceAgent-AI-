import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../components/Toast";

export default function AuthModal() {
  const [isLogin, setIsLogin] = useState(true);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();
  const { showToast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        showToast("Welcome back!", "success");
      } else {
        await register(fullName, email, password);
        showToast("Account created successfully!", "success");
      }
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.6)",
        backdropFilter: "blur(8px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        animation: "fadeIn 0.3s ease",
      }}
    >
      <div
        style={{
          background: "#ffffff",
          width: "100%",
          maxWidth: "440px",
          borderRadius: "16px",
          padding: "36px",
          boxShadow: "0 25px 50px -12px rgba(15, 23, 42, 0.25)",
          border: "1px solid #e2e8f0",
          animation: "slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "10px",
              fontSize: "22px",
              fontWeight: 800,
              color: "var(--primary)",
              marginBottom: "6px",
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                background: "linear-gradient(135deg, var(--primary), #818cf8)",
                color: "#fff",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "20px",
              }}
            >
              🎙️
            </div>
            <span>VoiceAgent AI</span>
          </div>
          <p style={{ color: "var(--text-muted)", fontSize: "13.5px" }}>
            Real-time Voice Calling & Demo Booking Platform
          </p>
        </div>

        {/* Tab Switcher */}
        <div
          style={{
            display: "flex",
            background: "var(--bg-main)",
            padding: "4px",
            borderRadius: "10px",
            marginBottom: "24px",
          }}
        >
          <button
            type="button"
            style={{
              flex: 1,
              padding: "9px",
              border: "none",
              background: isLogin ? "#ffffff" : "transparent",
              color: isLogin ? "var(--primary)" : "var(--text-muted)",
              fontFamily: "inherit",
              fontSize: "13.5px",
              fontWeight: 700,
              borderRadius: "8px",
              cursor: "pointer",
              boxShadow: isLogin ? "0 1px 3px rgba(0, 0, 0, 0.08)" : "none",
              transition: "all 0.2s ease",
            }}
            onClick={() => setIsLogin(true)}
          >
            Sign In
          </button>
          <button
            type="button"
            style={{
              flex: 1,
              padding: "9px",
              border: "none",
              background: !isLogin ? "#ffffff" : "transparent",
              color: !isLogin ? "var(--primary)" : "var(--text-muted)",
              fontFamily: "inherit",
              fontSize: "13.5px",
              fontWeight: 700,
              borderRadius: "8px",
              cursor: "pointer",
              boxShadow: !isLogin ? "0 1px 3px rgba(0, 0, 0, 0.08)" : "none",
              transition: "all 0.2s ease",
            }}
            onClick={() => setIsLogin(false)}
          >
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="Aarav Sharma"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Work Email</label>
            <input
              type="email"
              className="form-input"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "12px", padding: "11px" }}
            disabled={loading}
          >
            {loading ? "Processing..." : isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
