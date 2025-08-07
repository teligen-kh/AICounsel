'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

export function LoginForm() {
  const { login, isLoading, error, isAuthenticated } = useAuth();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [autoLogin, setAutoLogin] = useState(false);

  useEffect(() => {
    // 자동 로그인 여부를 localStorage에서 불러오기
    const savedAutoLogin = localStorage.getItem('autoLogin');
    const savedEmail = localStorage.getItem('savedEmail');
    const savedPassword = localStorage.getItem('savedPassword');
    
    console.log('자동 로그인 정보 확인:', { savedAutoLogin, savedEmail, savedPassword });
    
    if (savedAutoLogin === 'true' && savedEmail && savedPassword) {
      setAutoLogin(true);
      setFormData({
        email: savedEmail,
        password: savedPassword,
      });
      console.log('자동 로그인 정보 로드 완료');
    } else {
      console.log('저장된 자동 로그인 정보가 없습니다');
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 자동 로그인 상태를 먼저 저장
    if (autoLogin) {
      localStorage.setItem('autoLogin', 'true');
      // 이메일과 비밀번호 저장
      localStorage.setItem('savedEmail', formData.email);
      localStorage.setItem('savedPassword', formData.password);
    } else {
      localStorage.removeItem('autoLogin');
      // 자동 로그인 해제 시 저장된 정보도 삭제
      localStorage.removeItem('savedEmail');
      localStorage.removeItem('savedPassword');
    }
    
    await login(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleAutoLoginChange = (checked: boolean) => {
    setAutoLogin(checked);
    
    if (!checked) {
      // 자동 로그인 해제 시 저장된 정보 삭제
      localStorage.removeItem('autoLogin');
      localStorage.removeItem('savedEmail');
      localStorage.removeItem('savedPassword');
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-center">로그인</CardTitle>
        <CardDescription className="text-center">
          AI 상담 관리센터에 로그인하세요
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              이메일
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="이메일을 입력하세요"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>
          
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              비밀번호
            </label>
            <div className="relative">
              <Input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="비밀번호를 입력하세요"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <input
              id="autoLogin"
              name="autoLogin"
              type="checkbox"
              checked={autoLogin}
              onChange={(e) => handleAutoLoginChange(e.target.checked)}
              className="form-checkbox h-4 w-4 text-blue-600"
              disabled={isLoading}
            />
            <label htmlFor="autoLogin" className="text-sm text-gray-700 select-none">
              자동 로그인 (이메일과 비밀번호 저장)
            </label>
          </div>
          
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                로그인 중...
              </>
            ) : (
              '로그인'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
} 