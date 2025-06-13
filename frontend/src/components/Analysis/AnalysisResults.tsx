'use client';

import { Card } from '@/components/ui/card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface AnalysisResultsProps {
  results: {
    basic_stats: {
      total_conversations: number;
      total_messages: number;
      role_stats: {
        user: number;
        assistant: number;
      };
      avg_conversation_length: number;
    };
    patterns: {
      user_first: number;
      assistant_first: number;
      avg_turn_length: number;
      max_turn_length: number;
    };
    keywords: {
      [key: string]: number;
    };
  } | null;
}

export function AnalysisResults({ results }: AnalysisResultsProps) {
  if (!results) {
    return null;
  }

  const roleData = [
    { name: '사용자', value: results.basic_stats.role_stats.user },
    { name: '어시스턴트', value: results.basic_stats.role_stats.assistant },
  ];

  const patternData = [
    { name: '사용자 첫 발화', value: results.patterns.user_first },
    { name: '어시스턴트 첫 발화', value: results.patterns.assistant_first },
  ];

  const keywordData = Object.entries(results.keywords)
    .map(([word, count]) => ({ name: word, value: count }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">기본 통계</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">총 대화 수</p>
            <p className="text-2xl font-bold">{results.basic_stats.total_conversations}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">총 메시지 수</p>
            <p className="text-2xl font-bold">{results.basic_stats.total_messages}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">평균 대화 길이</p>
            <p className="text-2xl font-bold">{results.basic_stats.avg_conversation_length.toFixed(1)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">평균 턴 길이</p>
            <p className="text-2xl font-bold">{results.patterns.avg_turn_length.toFixed(1)}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">역할별 메시지 수</h2>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={roleData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">첫 발화자 통계</h2>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={patternData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">자주 사용된 키워드</h2>
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={keywordData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={150} />
              <Tooltip />
              <Bar dataKey="value" fill="#ffc658" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
} 