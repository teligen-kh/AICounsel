'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { MessageSquare, BarChart2 } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI 상담 분석 시스템
          </h1>
          <p className="text-xl text-gray-600">
            AI와의 대화를 분석하고 인사이트를 얻어보세요
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Link href="/chat" className="block">
            <Card className="p-8 hover:shadow-lg transition-shadow duration-300 h-full">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-6">
                  <MessageSquare className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                  AI 상담
                </h2>
                <p className="text-gray-600">
                  AI 상담사와 대화를 나누고 상담 내용을 기록하세요.
                  실시간으로 대화를 분석하고 인사이트를 제공합니다.
                </p>
              </div>
            </Card>
          </Link>

          <Link href="/analysis" className="block">
            <Card className="p-8 hover:shadow-lg transition-shadow duration-300 h-full">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
                  <BarChart2 className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                  상담 분석
                </h2>
                <p className="text-gray-600">
                  기간별 상담 데이터를 분석하고 통계를 확인하세요.
                  대화 패턴과 키워드를 통해 인사이트를 얻을 수 있습니다.
                </p>
              </div>
            </Card>
          </Link>
        </div>

        <div className="mt-16 text-center">
          <p className="text-gray-500">
            © 2024 AI 상담 분석 시스템. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
