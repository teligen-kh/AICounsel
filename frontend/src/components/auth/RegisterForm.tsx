'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

export function RegisterForm() {
  const { register, isLoading, error } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [validationError, setValidationError] = useState('');
  const [emailStatus, setEmailStatus] = useState<{ available: boolean; message: string } | null>(null);
  const [usernameStatus, setUsernameStatus] = useState<{ available: boolean; message: string } | null>(null);
  const [isCheckingEmail, setIsCheckingEmail] = useState(false);
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    // 비밀번호 확인
    if (formData.password !== formData.confirmPassword) {
      setValidationError('비밀번호가 일치하지 않습니다.');
      return;
    }

    // 비밀번호 길이 확인
    if (formData.password.length < 6) {
      setValidationError('비밀번호는 최소 6자 이상이어야 합니다.');
      return;
    }

    await register(formData);
  };

  const checkEmailAvailability = async (email: string) => {
    if (!email || email.length < 3) {
      setEmailStatus(null);
      return;
    }
    
    setIsCheckingEmail(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/auth/check-email?email=${encodeURIComponent(email)}`);
      const data = await response.json();
      setEmailStatus(data);
    } catch (error) {
      console.error('이메일 확인 오류:', error);
    } finally {
      setIsCheckingEmail(false);
    }
  };

  const checkUsernameAvailability = async (username: string) => {
    if (!username || username.length < 2) {
      setUsernameStatus(null);
      return;
    }
    
    setIsCheckingUsername(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/auth/check-username?username=${encodeURIComponent(username)}`);
      const data = await response.json();
      setUsernameStatus(data);
    } catch (error) {
      console.error('사용자명 확인 오류:', error);
    } finally {
      setIsCheckingUsername(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    // 실시간 중복 확인
    if (name === 'email') {
      setTimeout(() => checkEmailAvailability(value), 500);
    } else if (name === 'username') {
      setTimeout(() => checkUsernameAvailability(value), 500);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-center">회원가입</CardTitle>
        <CardDescription className="text-center">
          AI 상담 관리센터에 가입하세요
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {(error || validationError) && (
            <Alert variant="destructive">
              <AlertDescription>{error || validationError}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium">
              사용자명
            </label>
            <Input
              id="username"
              name="username"
              type="text"
              placeholder="사용자명을 입력하세요"
              value={formData.username}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
            {isCheckingUsername && (
              <p className="text-sm text-blue-600">확인 중...</p>
            )}
            {usernameStatus && (
              <p className={`text-sm ${usernameStatus.available ? 'text-green-600' : 'text-red-600'}`}>
                {usernameStatus.message}
              </p>
            )}
          </div>
          
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
            {isCheckingEmail && (
              <p className="text-sm text-blue-600">확인 중...</p>
            )}
            {emailStatus && (
              <p className={`text-sm ${emailStatus.available ? 'text-green-600' : 'text-red-600'}`}>
                {emailStatus.message}
              </p>
            )}
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
                placeholder="비밀번호를 입력하세요 (최소 6자)"
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
          
          <div className="space-y-2">
            <label htmlFor="confirmPassword" className="text-sm font-medium">
              비밀번호 확인
            </label>
            <div className="relative">
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="비밀번호를 다시 입력하세요"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                disabled={isLoading}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
          
          <Button
            type="submit"
            className="w-full"
            disabled={
              isLoading || 
              !emailStatus?.available || 
              !usernameStatus?.available ||
              isCheckingEmail ||
              isCheckingUsername
            }
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                가입 중...
              </>
            ) : (
              '회원가입'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
} 