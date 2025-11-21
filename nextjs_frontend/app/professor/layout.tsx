'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';

/**
 * Professor Layout
 * Provides navigation and structure for all professor pages
 */
export default function ProfessorLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  // Navigation items
  const navItems = [
    { href: '/professor', label: 'Dashboard', icon: '📊' },
    { href: '/professor/materials', label: 'Materials', icon: '📚' },
    { href: '/professor/problem-sets', label: 'Problem Sets', icon: '📝' },
    { href: '/professor/analytics', label: 'Analytics', icon: '📈' },
  ];

  return (
    <div className="min-h-screen bg-aub-cream">
      {/* Top Navigation Bar */}
      <header className="bg-aub-red text-white shadow-aub-lg">
        <div className="container-aub">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Nav */}
            <div className="flex items-center space-x-8">
              <Link href="/professor" className="text-xl font-bold hover:text-white/80 transition-colors">
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

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <span className="text-sm hidden sm:inline">Prof. John Doe</span>
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

      {/* Footer */}
      <footer className="bg-aub-beige border-t border-gray-200 mt-16">
        <div className="container-aub py-6 text-center text-sm text-gray-600">
          <p>American University of Beirut Learning Management System</p>
          <p className="mt-1">AI-powered by OpenAI · Built with Next.js & FastAPI</p>
        </div>
      </footer>
    </div>
  );
}

