'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';

/**
 * Student Layout
 * Provides navigation for student pages
 */
export default function StudentLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { href: '/student', label: 'Dashboard', icon: '🏠' },
    { href: '/student/workspace', label: 'Workspace', icon: '📚' },
    { href: '/student/problem-sets', label: 'Problem Sets', icon: '📝' },
    { href: '/student/beat-ai', label: 'Beat the AI', icon: '🤖' },
    { href: '/student/grades', label: 'Grades', icon: '📊' },
  ];

  return (
    <div className="min-h-screen bg-aub-cream">
      {/* Top Navigation */}
      <header className="bg-aub-red text-white shadow-aub-lg">
        <div className="container-aub">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <Link href="/student" className="text-xl font-bold hover:text-white/80 transition-colors">
                AUB LMS
              </Link>
              <nav className="hidden md:flex space-x-1">
                {navItems.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`px-4 py-2 rounded-aub transition-colors ${
                        isActive
                          ? 'bg-white/20 text-white'
                          : 'text-white/80 hover:bg-white/10 hover:text-white'
                      }`}
                    >
                      <span className="mr-2">{item.icon}</span>
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm hidden sm:inline">Jane Smith</span>
              <Link href="/" className="btn-secondary text-sm bg-white/10 border-white/30 text-white hover:bg-white/20">
                Logout
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container-aub py-8">
        {children}
      </main>
    </div>
  );
}

