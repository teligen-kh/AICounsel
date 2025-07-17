'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { User, Mail, Shield, Calendar } from 'lucide-react';

export default function ProfilePage() {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <p className="text-center text-gray-600">로그인이 필요합니다.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">프로필</h1>
          <p className="text-gray-600 mt-2">사용자 정보를 확인하고 관리하세요</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <User className="h-5 w-5" />
              <span>기본 정보</span>
            </CardTitle>
            <CardDescription>사용자의 기본 정보입니다</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center space-x-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src="" alt={user.username} />
                <AvatarFallback className="bg-blue-50 text-white text-lg">
                  {user.username.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{user.username}</h3>
                <p className="text-gray-600">{user.email}</p>
                <div className="flex items-center space-x-2 mt-2">
                  <Badge variant="secondary">{user.role}</Badge>
                  {user.company && (
                    <Badge variant="outline">{user.company}</Badge>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <Mail className="h-5 w-5 text-gray-500" />
                <div>
                  <p className="text-sm font-medium text-gray-900">이메일</p>
                  <p className="text-sm text-gray-600">{user.email}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <Shield className="h-5 w-5 text-gray-500" />
                <div>
                  <p className="text-sm font-medium text-gray-900">권한</p>
                  <p className="text-sm text-gray-60">{user.role}</p>
                </div>
              </div>

              {user.company && (
                <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <User className="h-5 w-5 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">회사</p>
                    <p className="text-sm text-gray-600">{user.company}</p>
                  </div>
                </div>
              )}

              {user.last_login_at && (
                <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <Calendar className="h-5 w-5 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      마지막 로그인:
                    </p>
                    <p className="text-sm text-gray-600">
                      {new Date(user.last_login_at).toLocaleDateString('ko-KR')}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {user.permissions && user.permissions.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">권한 목록</h4>
                <div className="flex flex-wrap gap-2">
                  {user.permissions.map((permission, index) => (
                    <Badge key={index} variant="outline">
                      {permission}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-center space-x-4">
          <Button variant="outline" onClick={() => window.history.back()}>
            뒤로 가기
          </Button>
          <Button>
            정보 수정
          </Button>
        </div>
      </div>
    </div>
  );
} 