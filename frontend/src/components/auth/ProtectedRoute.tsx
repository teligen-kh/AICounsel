'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Permission } from '@/types/auth';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: Permission[];
  fallback?: React.ReactNode;
}

export function ProtectedRoute({ 
  children, 
  requiredPermissions = [], 
  fallback 
}: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth();

  // 로딩 중일 때
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>로딩 중...</span>
        </div>
      </div>
    );
  }

  // 인증되지 않은 경우
  if (!isAuthenticated || !user) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-gray-900">접근 권한이 없습니다</h2>
          <p className="text-gray-600">로그인이 필요합니다.</p>
        </div>
      </div>
    );
  }

  // 권한 확인
  if (requiredPermissions.length > 0) {
    const hasPermission = requiredPermissions.every(permission =>
      user.permissions.includes(permission)
    );

    if (!hasPermission) {
      return fallback || (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">권한이 부족합니다</h2>
            <p className="text-gray-600">
              이 페이지에 접근할 권한이 없습니다.
            </p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
} 