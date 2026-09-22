"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

import { useRouter } from "next/navigation";

export type Role = "CITIZEN" | "VERIFIER" | "ANALYST" | "ADMIN";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  hasRole: (role: Role) => boolean;
  hasAnyRole: (roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let mounted = true;
    
    const initializeAuth = async () => {
      await Promise.resolve();
      if (!mounted) return;

      const storedToken = localStorage.getItem("mausam_token");
      const storedUser = localStorage.getItem("mausam_user");

      if (storedToken && storedUser) {
        try {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
        } catch (e) {
          console.error("Failed to parse stored user", e);
          localStorage.removeItem("mausam_token");
          localStorage.removeItem("mausam_user");
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
    return () => {
      mounted = false;
    };
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem("mausam_token", newToken);
    localStorage.setItem("mausam_user", JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("mausam_token");
    localStorage.removeItem("mausam_user");
    router.push("/login");
  };

  const hasRole = (role: Role) => {
    return user?.role === role;
  };

  const hasAnyRole = (roles: Role[]) => {
    if (!user) return false;
    return roles.includes(user.role);
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    token,
    login,
    logout,
    hasRole,
    hasAnyRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
