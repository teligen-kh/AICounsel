'use client';

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { User, LoginCredentials, RegisterData, AuthState, AuthContextType, UserRole, Permission } from '@/types/auth';

// 초기 상태
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// 액션 타입
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: User }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'REGISTER_START' }
  | { type: 'REGISTER_SUCCESS'; payload: User }
  | { type: 'REGISTER_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; payload: boolean };

// 리듀서
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
    case 'REGISTER_START':
      return { ...state, isLoading: true, error: null };
    
    case 'LOGIN_SUCCESS':
    case 'REGISTER_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    
    case 'LOGIN_FAILURE':
    case 'REGISTER_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    default:
      return state;
  }
}

// Context 생성
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider 컴포넌트
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // 로그인 함수
  const login = async (credentials: LoginCredentials) => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '로그인에 실패했습니다.');
      }

      // 토큰을 로컬 스토리지에 저장
      localStorage.setItem('token', data.access_token);
      
      // 사용자 정보 저장
      localStorage.setItem('user', JSON.stringify(data.user_info));
      
      // 자동 로그인이 체크되어 있으면 이메일과 비밀번호 저장
      const autoLogin = localStorage.getItem('autoLogin');
      if (autoLogin === 'true') {
        localStorage.setItem('savedEmail', credentials.email);
        localStorage.setItem('savedPassword', credentials.password);
      } else {
        // 자동 로그인이 해제되어 있으면 저장된 정보 삭제
        localStorage.removeItem('savedEmail');
        localStorage.removeItem('savedPassword');
      }
      
      dispatch({ type: 'LOGIN_SUCCESS', payload: data.user_info });
    } catch (error) {
      dispatch({ 
        type: 'LOGIN_FAILURE', 
        payload: error instanceof Error ? error.message : '로그인에 실패했습니다.' 
      });
    }
  };

  // 회원가입 함수
  const register = async (data: RegisterData) => {
    dispatch({ type: 'REGISTER_START' });
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: data.username,
          email: data.email,
          password: data.password,
        }),
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(responseData.detail || '회원가입에 실패했습니다.');
      }

      // 회원가입 성공 시 자동 로그인
      await login({ email: data.email, password: data.password });
    } catch (error) {
      dispatch({ 
        type: 'REGISTER_FAILURE', 
        payload: error instanceof Error ? error.message : '회원가입에 실패했습니다.' 
      });
    }
  };

  // 로그아웃 함수
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    dispatch({ type: 'LOGOUT' });
  };

  // 인증 상태 확인
  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');

    if (!token || !userStr) {
      dispatch({ type: 'SET_LOADING', payload: false });
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const user = await response.json();
        dispatch({ type: 'LOGIN_SUCCESS', payload: user });
      } else {
        // 토큰이 유효하지 않으면 로그아웃
        logout();
      }
    } catch (error) {
      logout();
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // 컴포넌트 마운트 시 인증 상태 확인
  useEffect(() => {
    checkAuth();
  }, []);

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 