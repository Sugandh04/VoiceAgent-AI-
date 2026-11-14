import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);

  useEffect(() => {
    checkUser();

    const handleAuthRequired = () => {
      setUser(null);
      setShowAuthModal(true);
    };

    window.addEventListener("auth:required", handleAuthRequired);
    return () => window.removeEventListener("auth:required", handleAuthRequired);
  }, []);

  const checkUser = async () => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      setShowAuthModal(false);
      return;
    }

    try {
      const data = await api.getMe();
      setUser(data);
      setShowAuthModal(false);
    } catch (err) {
      api.setToken(null);
      setUser(null);
      setShowAuthModal(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const res = await api.login({ email, password });
    api.setToken(res.access_token);
    setUser(res.user);
    setShowAuthModal(false);
    return res.user;
  };

  const register = async (full_name, email, password) => {
    const res = await api.register({ full_name, email, password });
    api.setToken(res.access_token);
    setUser(res.user);
    setShowAuthModal(false);
    return res.user;
  };

  const logout = () => {
    api.setToken(null);
    setUser(null);
    setShowAuthModal(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        showAuthModal,
        setShowAuthModal,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
