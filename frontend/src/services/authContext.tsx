import React, { createContext, useContext, useState } from 'react';
import { UserProfile, UserRole } from '../types/index.js';
import { apiClient } from './apiClient.js';

export interface AuditSessionEvent {
  id: string;
  timestamp: string;
  action: string;
  field: string;
  targetId: string;
  actor: string;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  switchDemoRole: (role: UserRole) => Promise<void>;
  auditEvents: AuditSessionEvent[];
  logAuditEvent: (action: string, field: string, targetId: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{
  children: React.ReactNode;
  initialRole?: UserRole | null;
}> = ({ children, initialRole = 'credit_team' }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    if (!initialRole) return null;
    return {
      username: initialRole === 'credit_team' ? 'officer_sfl' : 'judge_auditor',
      role: initialRole,
      full_name:
        initialRole === 'credit_team'
          ? 'SFL Credit Risk Manager'
          : 'Hackathon Judge / Auditor Demo View',
      is_active: true,
    };
  });

  const [token, setToken] = useState<string | null>(() => {
    if (!initialRole) return null;
    const initialToken =
      initialRole === 'credit_team'
        ? 'mock-sfl-credit-jwt-token'
        : 'mock-sfl-judge-jwt-token';
    apiClient.setAccessToken(initialToken);
    return initialToken;
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [auditEvents, setAuditEvents] = useState<AuditSessionEvent[]>([]);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await apiClient.login(username, password);
      setToken(res.access_token);
      setUser({
        username: res.user_id,
        role: res.role,
        full_name: res.full_name,
        is_active: true,
      });
      logAuditEvent('USER_LOGIN', 'SESSION_AUTH', username);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    apiClient.setAccessToken(null);
    setToken(null);
    setUser(null);
  };

  const switchDemoRole = async (targetRole: UserRole) => {
    if (targetRole === 'credit_team') {
      await login('officer_sfl', 'SFLCreditRisk@2026!');
    } else {
      await login('judge_auditor', 'ViewerJudge@2026!');
    }
  };

  const logAuditEvent = (action: string, field: string, targetId: string) => {
    const event: AuditSessionEvent = {
      id: `SES-AUD-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString(),
      action,
      field,
      targetId,
      actor: user ? `${user.username} (${user.role})` : 'anonymous',
    };
    setAuditEvents((prev) => [event, ...prev]);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role || null,
        isAuthenticated: Boolean(token && user),
        isLoading,
        login,
        logout,
        switchDemoRole,
        auditEvents,
        logAuditEvent,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
