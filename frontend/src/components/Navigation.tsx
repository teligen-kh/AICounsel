import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center justify-between p-4 border-b">
      <div className="flex items-center space-x-4">
        <Link href="/" className="text-xl font-bold">
          AI 상담 분석
        </Link>
      </div>
      <div className="flex items-center space-x-4">
        <Link
          href="/"
          className={cn(
            "px-3 py-2 rounded-md text-sm font-medium",
            pathname === "/"
              ? "bg-gray-100 text-gray-900"
              : "text-gray-500 hover:text-gray-900"
          )}
        >
          홈
        </Link>
        <Link
          href="/chat"
          className={cn(
            "px-3 py-2 rounded-md text-sm font-medium",
            pathname === "/chat"
              ? "bg-gray-100 text-gray-900"
              : "text-gray-500 hover:text-gray-900"
          )}
        >
          AI 상담
        </Link>
        <Link
          href="/analysis"
          className={cn(
            "px-3 py-2 rounded-md text-sm font-medium",
            pathname === "/analysis"
              ? "bg-gray-100 text-gray-900"
              : "text-gray-500 hover:text-gray-900"
          )}
        >
          상담 분석
        </Link>
        <Link
          href="/list"
          className={cn(
            "px-3 py-2 rounded-md text-sm font-medium",
            pathname === "/list"
              ? "bg-gray-100 text-gray-900"
              : "text-gray-500 hover:text-gray-900"
          )}
        >
          상담 리스트
        </Link>
      </div>
    </nav>
  );
} 