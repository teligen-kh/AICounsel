'use client';

import React, { useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">AI 상담 관리센터</h1>
          <p className="text-gray-600">
            {isLogin ? '계정에 로그인하세요' : '새 계정을 만드세요'}
          </p>
        </div>

        {isLogin ? <LoginForm /> : <RegisterForm />}

        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <p className="text-sm text-gray-600">
                {isLogin ? '계정이 없으신가요?' : '이미 계정이 있으신가요?'}
              </p>
              <Button
                variant="outline"
                onClick={() => setIsLogin(!isLogin)}
                className="w-full"
              >
                {isLogin ? '회원가입' : '로그인'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 