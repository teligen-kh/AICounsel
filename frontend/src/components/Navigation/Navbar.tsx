'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import { 
  MessageSquare, 
  BarChart2, 
  Home, 
  List, 
  Settings,
  User,
  LogOut,
  LogIn
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';

export function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();

  const navItems = [
    {
      name: '홈',
      href: '/',
      icon: Home,
      requiresAuth: false,
    },
    {
      name: 'AI 상담',
      href: '/chat',
      icon: MessageSquare,
      requiresAuth: true,
    },
    {
      name: '상담 분석',
      href: '/analysis',
      icon: BarChart2,
      requiresAuth: true,
    },
    {
      name: '상담 리스트',
      href: '/list',
      icon: List,
      requiresAuth: true,
    },
    {
      name: '설정',
      href: '/settings',
      icon: Settings,
      requiresAuth: true,
    },
  ];

  const filteredNavItems = navItems.filter(item => 
    !item.requiresAuth || isAuthenticated
  );

  const handleLogout = () => {
    logout();
  };

  return (
    <nav className="border-b bg-white shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-gray-900 flex items-center space-x-2">
              <div className="p-1 bg-blue-100 rounded">
                <MessageSquare className="h-5 w-5 text-blue-600" />
              </div>
              <span>AI 상담 관리센터</span>
            </Link>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* 네비게이션 링크 */}
            {filteredNavItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}

            {/* 사용자 메뉴 */}
            {isAuthenticated && user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="" alt={user.username} />
                      <AvatarFallback className="bg-blue-500 text-white text-sm">
                        {user.username.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{user.username}</p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user.email}
                      </p>
                      <Badge variant="secondary" className="w-fit mt-1">
                        {user.role}
                      </Badge>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/profile" className="flex items-center">
                      <User className="mr-2 h-4 w-4" />
                      <span>프로필</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/settings" className="flex items-center">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>설정</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>로그아웃</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center space-x-2">
                <Button variant="ghost" asChild>
                  <Link href="/auth" className="flex items-center">
                    <LogIn className="mr-2 h-4 w-4" />
                    로그인
                  </Link>
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
} 