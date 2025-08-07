'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Permission } from '@/types/auth';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Send, 
  Bot, 
  User, 
  Clock, 
  MessageSquare,
  Loader2,
  Settings,
  FileText,
  Download,
  ArrowLeft,
  Home
} from 'lucide-react';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isTyping?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(`session-${Date.now()}`);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: input,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // 타이핑 표시기 추가
    const typingMessage: Message = {
      id: `typing-${Date.now()}`,
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      isTyping: true
    };

    setMessages(prev => [...prev, typingMessage]);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          conversation_id: sessionId
        }),
      });

      const data = await response.json();
      
      // 타이핑 메시지 제거하고 실제 응답 추가
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isTyping);
        return [...filtered, {
          id: `assistant-${Date.now()}`,
          content: data.response,
          role: 'assistant',
          timestamp: new Date()
        }];
      });
    } catch (error) {
      console.error('Error sending message:', error);
      // 에러 메시지 표시
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isTyping);
        return [...filtered, {
          id: `error-${Date.now()}`,
          content: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.',
          role: 'assistant',
          timestamp: new Date()
        }];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const exportConversation = () => {
    const conversationText = messages
      .map(msg => `${msg.role === 'user' ? '사용자' : 'AI 상담사'}: ${msg.content}`)
      .join('\n\n');
    
    const blob = new Blob([conversationText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <ProtectedRoute requiredPermissions={[Permission.CHAT_ACCESS]}>
      <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-indigo-50 overflow-hidden">
        {/* 헤더 */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/')}
                className="p-2 h-8 w-8"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div className="p-2 bg-blue-100 rounded-lg">
                <MessageSquare className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">AI 상담사</h1>
                <p className="text-xs text-gray-600">
                  전문적인 상담 서비스를 제공합니다
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">
                온라인
              </Badge>
              <Button variant="outline" size="sm" onClick={exportConversation} className="text-xs">
                <Download className="h-3 w-3 mr-1" />
                내보내기
              </Button>
            </div>
          </div>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto px-4 py-3" ref={scrollAreaRef}>
            <div className="space-y-4 max-w-4xl mx-auto pb-4">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <div className="p-3 bg-blue-100 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                    <Bot className="h-6 w-6 text-blue-600" />
                  </div>
                  <h3 className="text-base font-medium text-gray-900 mb-2">
                    AI 상담사와 대화를 시작하세요
                  </h3>
                  <p className="text-gray-600 max-w-md mx-auto text-sm">
                    어떤 도움이 필요하신가요? 전문적인 상담 서비스를 제공해드리겠습니다.
                  </p>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex items-start space-x-2 max-w-[85%] ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <Avatar className={`h-6 w-6 ${message.role === 'user' ? 'bg-blue-500' : 'bg-gray-500'}`}>
                      <AvatarImage src="" />
                      <AvatarFallback className="text-white text-xs">
                        {message.role === 'user' ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <Card className={`${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white'} shadow-sm max-w-full`}>
                        <CardContent className="p-3">
                          {message.isTyping ? (
                            <div className="flex items-center space-x-2">
                              <Loader2 className="h-3 w-3 animate-spin" />
                              <span className="text-xs">응답을 생성하고 있습니다...</span>
                            </div>
                          ) : (
                            <div className="whitespace-pre-wrap text-sm leading-relaxed break-words">
                              {message.content}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                      
                      <div className={`flex items-center space-x-1 mt-1 text-xs text-gray-500 ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                        <Clock className="h-2 w-2" />
                        <span>{formatTime(message.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 입력 영역 */}
        <div className="bg-white border-t border-gray-200 px-4 py-3 flex-shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-2">
              <div className="flex-1 min-w-0">
                <Textarea
                  placeholder="메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={isLoading}
                  className="min-h-[40px] max-h-[120px] resize-none text-sm"
                  rows={1}
                />
              </div>
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                size="default"
                className="px-4 h-[40px] flex-shrink-0"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center space-x-3">
                <span>세션: {sessionId.slice(-6)}</span>
                <span>메시지: {messages.filter(m => !m.isTyping).length}개</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-600">AI 상담사 준비 완료</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
} 