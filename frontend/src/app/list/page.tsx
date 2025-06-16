'use client';

import { useState } from 'react';
import { DateRangePicker } from '@/components/Analysis/DateRangePicker';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface Message {
  role: string;
  content: string;
  timestamp?: string;
}

interface Conversation {
  id: string;
  title: string;
  consultation_time: string;
  summary: string;
  status: string;
  message_count: number;
  messages: Message[];
}

export default function ListPage() {
  const [dateRange, setDateRange] = useState<{
    startDate: Date | null;
    endDate: Date | null;
  }>({
    startDate: null,
    endDate: null,
  });
  const [keyword, setKeyword] = useState('');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  const handleSearch = async () => {
    if (!dateRange.startDate || !dateRange.endDate) {
      alert('날짜 범위를 선택해주세요.');
      return;
    }
    
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/analysis/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          startDate: dateRange.startDate.toISOString(),
          endDate: dateRange.endDate.toISOString(),
          keyword: keyword.trim() || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '검색 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setConversations(data.conversations);
      setTotal(data.total);
    } catch (error) {
      console.error('Search error:', error);
      alert('검색 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">상담 리스트</h1>
      
      <div className="flex flex-col gap-4 mb-6">
        <DateRangePicker
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onDateChange={setDateRange}
        />
        
        <div className="flex gap-4">
          <Input
            placeholder="키워드 검색 (고객명, 상담 내용 등)"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="flex-1"
          />
          <Button
            onClick={handleSearch}
            disabled={isLoading || !dateRange.startDate || !dateRange.endDate}
          >
            {isLoading ? '검색 중...' : '검색'}
          </Button>
        </div>
      </div>

      {total > 0 && (
        <div className="mb-4">
          총 {total}개의 상담 내역이 있습니다.
        </div>
      )}

      {conversations.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-20">번호</TableHead>
                <TableHead>상담 시간</TableHead>
                <TableHead>제목</TableHead>
                <TableHead>요약</TableHead>
                <TableHead className="w-24">메시지 수</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {conversations.map((conv, index) => (
                <TableRow
                  key={conv.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => setSelectedConversation(conv)}
                >
                  <TableCell className="font-medium">{conversations.length - index}</TableCell>
                  <TableCell>
                    {format(new Date(conv.consultation_time), 'yyyy-MM-dd HH:mm:ss', { locale: ko })}
                  </TableCell>
                  <TableCell>{conv.title}</TableCell>
                  <TableCell className="max-w-md truncate">{conv.summary}</TableCell>
                  <TableCell>{conv.message_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        !isLoading && (
          <div className="text-center text-gray-500">
            검색 결과가 없습니다.
          </div>
        )
      )}

      <Dialog open={!!selectedConversation} onOpenChange={() => setSelectedConversation(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>상담 내용</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {selectedConversation?.messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white ml-4'
                      : 'bg-gray-100 text-gray-900 mr-4'
                  }`}
                >
                  <div className={`text-sm mb-1 ${
                    message.role === 'user'
                      ? 'text-blue-100'
                      : 'text-gray-500'
                  }`}>
                    {message.speaker} [{message.start_time} - {message.end_time}]
                  </div>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
} 