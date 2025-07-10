export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  permissions: Permission[];
  createdAt: Date;
  lastLoginAt?: Date;
}

export enum UserRole {
  ADMIN = 'admin',
  COUNSELOR = 'counselor',
  USER = 'user',
  GUEST = 'guest'
}

export enum Permission {
  // 채팅 관련
  CHAT_ACCESS = 'chat_access',
  CHAT_HISTORY = 'chat_history',
  
  // 분석 관련
  ANALYSIS_ACCESS = 'analysis_access',
  ANALYSIS_EXPORT = 'analysis_export',
  
  // 관리 관련
  USER_MANAGEMENT = 'user_management',
  SYSTEM_SETTINGS = 'system_settings',
  
  // 상담 관련
  COUNSELING_ACCESS = 'counseling_access',
  COUNSELING_MANAGE = 'counseling_manage'
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
} 