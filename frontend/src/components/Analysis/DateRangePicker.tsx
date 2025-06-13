'use client';

import { useState } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface DateRangePickerProps {
  startDate: Date | null;
  endDate: Date | null;
  onDateChange: (range: { startDate: Date | null; endDate: Date | null }) => void;
}

export function DateRangePicker({ startDate, endDate, onDateChange }: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (date: Date | undefined) => {
    if (!date) return;

    if (!startDate || (startDate && endDate)) {
      onDateChange({ startDate: date, endDate: null });
    } else {
      if (date < startDate) {
        onDateChange({ startDate: date, endDate: startDate });
      } else {
        onDateChange({ startDate, endDate: date });
      }
      setIsOpen(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start text-left font-normal"
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {startDate ? (
                format(startDate, 'PPP', { locale: ko })
              ) : (
                <span>시작일 선택</span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={startDate}
              onSelect={handleSelect}
              locale={ko}
            />
          </PopoverContent>
        </Popover>

        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start text-left font-normal"
              disabled={!startDate}
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {endDate ? (
                format(endDate, 'PPP', { locale: ko })
              ) : (
                <span>종료일 선택</span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={endDate}
              onSelect={handleSelect}
              disabled={(date) => !startDate || date < startDate}
              locale={ko}
            />
          </PopoverContent>
        </Popover>
      </div>

      <div className="flex gap-2">
        <Button
          variant="outline"
          className="w-full"
          onClick={() => {
            const today = new Date();
            const start = new Date();
            start.setDate(today.getDate() - 7);
            onDateChange({ startDate: start, endDate: today });
          }}
        >
          최근 7일
        </Button>
        <Button
          variant="outline"
          className="w-full"
          onClick={() => {
            const today = new Date();
            const start = new Date();
            start.setMonth(today.getMonth() - 1);
            onDateChange({ startDate: start, endDate: today });
          }}
        >
          최근 30일
        </Button>
        <Button
          variant="outline"
          className="w-full"
          onClick={() => {
            const today = new Date();
            const start = new Date();
            start.setMonth(today.getMonth() - 3);
            onDateChange({ startDate: start, endDate: today });
          }}
        >
          최근 3개월
        </Button>
      </div>
    </div>
  );
} 