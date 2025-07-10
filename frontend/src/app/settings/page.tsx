'use client';

import React, { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Permission } from '@/types/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { 
  Settings, 
  User, 
  Shield, 
  MessageSquare, 
  BarChart3, 
  Save,
  Loader2 
} from 'lucide-react';

interface SystemSettings {
  // AI 모델 설정
  modelName: string;
  temperature: number;
  maxTokens: number;
  
  // 채팅 설정
  autoScroll: boolean;
  messageHistoryLimit: number;
  typingIndicator: boolean;
  
  // 분석 설정
  analysisEnabled: boolean;
  autoAnalysis: boolean;
  exportFormat: 'csv' | 'json' | 'excel';
  
  // 보안 설정
  sessionTimeout: number;
  requireReauth: boolean;
  logActivity: boolean;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings>({
    modelName: 'phi-3.5-mini',
    temperature: 0.7,
    maxTokens: 1000,
    autoScroll: true,
    messageHistoryLimit: 100,
    typingIndicator: true,
    analysisEnabled: true,
    autoAnalysis: false,
    exportFormat: 'csv',
    sessionTimeout: 30,
    requireReauth: false,
    logActivity: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/settings', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('설정을 불러오는데 실패했습니다:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(settings),
      });
      
      if (response.ok) {
        // 성공 메시지 표시
        console.log('설정이 저장되었습니다.');
      }
    } catch (error) {
      console.error('설정 저장에 실패했습니다:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSettingChange = (key: keyof SystemSettings, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>설정을 불러오는 중...</span>
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute requiredPermissions={[Permission.SYSTEM_SETTINGS]}>
      <div className="container mx-auto py-8 px-4">
        <div className="space-y-6">
          {/* 헤더 */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">시스템 설정</h1>
              <p className="text-gray-600 mt-2">
                AI 상담 시스템의 다양한 설정을 관리하세요
              </p>
            </div>
            <Button onClick={saveSettings} disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  저장 중...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  설정 저장
                </>
              )}
            </Button>
          </div>

          <Tabs defaultValue="ai" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="ai" className="flex items-center space-x-2">
                <MessageSquare className="h-4 w-4" />
                <span>AI 설정</span>
              </TabsTrigger>
              <TabsTrigger value="chat" className="flex items-center space-x-2">
                <User className="h-4 w-4" />
                <span>채팅 설정</span>
              </TabsTrigger>
              <TabsTrigger value="analysis" className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4" />
                <span>분석 설정</span>
              </TabsTrigger>
              <TabsTrigger value="security" className="flex items-center space-x-2">
                <Shield className="h-4 w-4" />
                <span>보안 설정</span>
              </TabsTrigger>
            </TabsList>

            {/* AI 설정 */}
            <TabsContent value="ai" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>AI 모델 설정</CardTitle>
                  <CardDescription>
                    AI 상담사가 사용할 모델과 응답 설정을 구성하세요
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="modelName">모델 선택</Label>
                      <Select
                        value={settings.modelName}
                        onValueChange={(value) => handleSettingChange('modelName', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="모델을 선택하세요" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="phi-3.5-mini">Phi-3.5 Mini</SelectItem>
                          <SelectItem value="phi-3.5-medium">Phi-3.5 Medium</SelectItem>
                          <SelectItem value="llama-3.1-8b">LLaMA 3.1 8B</SelectItem>
                          <SelectItem value="polyglot-ko-12.8b">Polyglot-Ko 12.8B</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="temperature">창의성 (Temperature)</Label>
                      <div className="flex items-center space-x-2">
                        <Input
                          type="range"
                          min="0"
                          max="2"
                          step="0.1"
                          value={settings.temperature}
                          onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
                          className="flex-1"
                        />
                        <span className="text-sm text-gray-600 w-12">
                          {settings.temperature}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="maxTokens">최대 토큰 수</Label>
                      <Input
                        type="number"
                        value={settings.maxTokens}
                        onChange={(e) => handleSettingChange('maxTokens', parseInt(e.target.value))}
                        min="100"
                        max="4000"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 채팅 설정 */}
            <TabsContent value="chat" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>채팅 인터페이스 설정</CardTitle>
                  <CardDescription>
                    채팅 화면의 사용자 경험을 개인화하세요
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>자동 스크롤</Label>
                      <p className="text-sm text-gray-600">
                        새 메시지가 올 때 자동으로 스크롤합니다
                      </p>
                    </div>
                    <Switch
                      checked={settings.autoScroll}
                      onCheckedChange={(checked) => handleSettingChange('autoScroll', checked)}
                    />
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>타이핑 표시기</Label>
                      <p className="text-sm text-gray-600">
                        AI가 응답을 생성할 때 타이핑 표시기를 보여줍니다
                      </p>
                    </div>
                    <Switch
                      checked={settings.typingIndicator}
                      onCheckedChange={(checked) => handleSettingChange('typingIndicator', checked)}
                    />
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label htmlFor="messageHistoryLimit">메시지 기록 제한</Label>
                    <Input
                      type="number"
                      value={settings.messageHistoryLimit}
                      onChange={(e) => handleSettingChange('messageHistoryLimit', parseInt(e.target.value))}
                      min="10"
                      max="1000"
                    />
                    <p className="text-sm text-gray-600">
                      한 번에 표시할 최대 메시지 수입니다
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 분석 설정 */}
            <TabsContent value="analysis" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>분석 및 내보내기 설정</CardTitle>
                  <CardDescription>
                    대화 분석 기능과 데이터 내보내기 옵션을 설정하세요
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>분석 기능 활성화</Label>
                      <p className="text-sm text-gray-600">
                        대화 분석 기능을 사용할 수 있습니다
                      </p>
                    </div>
                    <Switch
                      checked={settings.analysisEnabled}
                      onCheckedChange={(checked) => handleSettingChange('analysisEnabled', checked)}
                    />
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>자동 분석</Label>
                      <p className="text-sm text-gray-600">
                        대화 종료 시 자동으로 분석을 실행합니다
                      </p>
                    </div>
                    <Switch
                      checked={settings.autoAnalysis}
                      onCheckedChange={(checked) => handleSettingChange('autoAnalysis', checked)}
                    />
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label htmlFor="exportFormat">내보내기 형식</Label>
                    <Select
                      value={settings.exportFormat}
                      onValueChange={(value: 'csv' | 'json' | 'excel') => 
                        handleSettingChange('exportFormat', value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="형식을 선택하세요" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="csv">CSV</SelectItem>
                        <SelectItem value="json">JSON</SelectItem>
                        <SelectItem value="excel">Excel</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 보안 설정 */}
            <TabsContent value="security" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>보안 및 세션 설정</CardTitle>
                  <CardDescription>
                    계정 보안과 세션 관리를 설정하세요
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="sessionTimeout">세션 타임아웃 (분)</Label>
                    <Input
                      type="number"
                      value={settings.sessionTimeout}
                      onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                      min="5"
                      max="480"
                    />
                    <p className="text-sm text-gray-600">
                      자동 로그아웃까지의 시간입니다
                    </p>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>중요 작업 시 재인증</Label>
                      <p className="text-sm text-gray-600">
                        설정 변경 시 비밀번호를 다시 입력해야 합니다
                      </p>
                    </div>
                    <Switch
                      checked={settings.requireReauth}
                      onCheckedChange={(checked) => handleSettingChange('requireReauth', checked)}
                    />
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>활동 로그 기록</Label>
                      <p className="text-sm text-gray-600">
                        사용자 활동을 로그에 기록합니다
                      </p>
                    </div>
                    <Switch
                      checked={settings.logActivity}
                      onCheckedChange={(checked) => handleSettingChange('logActivity', checked)}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </ProtectedRoute>
  );
} 