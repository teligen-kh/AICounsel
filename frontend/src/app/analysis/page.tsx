'use client';

import { useState } from 'react';
import { DateRangePicker } from '@/components/Analysis/DateRangePicker';
import { AnalysisResults } from '@/components/Analysis/AnalysisResults';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const API_BASE_URL = 'http://localhost:8000';

export default function AnalysisPage() {
  const [dateRange, setDateRange] = useState<{
    startDate: Date | null;
    endDate: Date | null;
  }>({
    startDate: null,
    endDate: null,
  });
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!dateRange.startDate || !dateRange.endDate) {
      alert('날짜 범위를 선택해주세요.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          startDate: dateRange.startDate.toISOString(),
          endDate: dateRange.endDate.toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('분석 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setAnalysisResults(data);
    } catch (error) {
      console.error('Analysis error:', error);
      alert('분석 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">상담 분석</h1>

      <Card className="p-6 mb-6">
        <div className="flex flex-col gap-4">
          <DateRangePicker
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            onDateChange={setDateRange}
          />
          
          <Button
            onClick={handleAnalyze}
            disabled={isLoading || !dateRange.startDate || !dateRange.endDate}
            className="w-full"
          >
            {isLoading ? '분석 중...' : '분석 시작'}
          </Button>
        </div>
      </Card>

      {analysisResults && (
        <AnalysisResults results={analysisResults} />
      )}
    </div>
  );
} 