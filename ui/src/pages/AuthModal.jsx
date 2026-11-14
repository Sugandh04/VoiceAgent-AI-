import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../components/Toast";
import { Radio, ShieldCheck, Sparkles } from "lucide-react";

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
        showToast("Welcome back to VoiceAgent AI!", "success");
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
        background: "rgba(5, 7, 12, 0.85)",
        backdropFilter: "blur(16px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        animation: "fadeIn 0.25s ease",
      }}
    >
      <div
        className="modal-content"
        style={{
          width: "100%",
          maxWidth: "440px",
          padding: "36px",
          background: "var(--bg-card)",
          boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.9)",
          border: "1px solid var(--border-hover)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "26px" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              background: "linear-gradient(135deg, var(--sarvam-orange) 0%, #ea580c 40%, var(--sarvam-indigo) 100%)",
              color: "#fff",
              borderRadius: "14px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 12px auto",
              boxShadow: "0 0 20px var(--sarvam-orange-glow)",
            }}
          >
            <Radio size={24} />
          </div>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "22px",
              fontWeight: 700,
              color: "var(--text-accent)",
              letterSpacing: "-0.5px",
              margin: "0 0 4px 0",
            }}
          >
            VoiceAgent AI
          </h2>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", margin: 0 }}>
            Sovereign B2B Voice Calling & Lead Automation
          </p>
        </div>

        {/* Tab Switcher */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "4px",
            background: "var(--bg-card-subtle)",
            padding: "4px",
            borderRadius: "10px",
            marginBottom: "24px",
            border: "1px solid var(--border)",
          }}
        >
          <button
            type="button"
            style={{
              padding: "9px",
              border: "none",
              background: isLogin ? "linear-gradient(135deg, var(--sarvam-orange), #ea580c)" : "transparent",
              color: isLogin ? "#ffffff" : "var(--text-muted)",
              fontFamily: "inherit",
              fontSize: "13px",
              fontWeight: 700,
              borderRadius: "8px",
              cursor: "pointer",
              transition: "var(--transition)",
            }}
            onClick={() => setIsLogin(true)}
          >
            Sign In
          </button>
          <button
            type="button"
            style={{
              padding: "9px",
              border: "none",
              background: !isLogin ? "linear-gradient(135deg, var(--sarvam-orange), #ea580c)" : "transparent",
              color: !isLogin ? "#ffffff" : "var(--text-muted)",
              fontFamily: "inherit",
              fontSize: "13px",
              fontWeight: 700,
              borderRadius: "8px",
              cursor: "pointer",
              transition: "var(--transition)",
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
            style={{ width: "100%", marginTop: "16px", padding: "12px", fontSize: "14px" }}
            disabled={loading}
          >
            {loading ? "Authenticating..." : isLogin ? "Sign In to Platform" : "Create Account"}
          </button>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "6px", marginTop: "18px", fontSize: "11.5px", color: "var(--text-light)" }}>
            <ShieldCheck size={14} color="#10b981" />
            <span>Encrypted via Native BCrypt & JWT Session</span>
          </div>
        </form>
      </div>
    </div>
  );
}
