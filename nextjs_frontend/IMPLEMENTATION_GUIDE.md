# AUB LMS Implementation Guide

This guide provides the complete implementation for the AUB Learning Management System frontend.

## 📁 Complete File Structure

```
nextjs_frontend/
├── app/
│   ├── layout.tsx                    # ✅ Root layout
│   ├── page.tsx                      # ✅ Landing page
│   ├── globals.css                   # ✅ Use globals.aub.css
│   │
│   ├── professor/
│   │   ├── layout.tsx               # Professor layout with sidebar
│   │   ├── page.tsx                 # Professor dashboard
│   │   ├── materials/
│   │   │   ├── page.tsx            # Upload & manage materials
│   │   │   └── [docId]/page.tsx    # View document chunks
│   │   ├── problem-sets/
│   │   │   ├── page.tsx            # List problem sets
│   │   │   ├── generate/page.tsx   # Generate new set
│   │   │   └── [setId]/
│   │   │       ├── page.tsx        # View problem set
│   │   │       └── submissions/page.tsx  # Grade submissions
│   │   └── analytics/page.tsx       # Analytics dashboard
│   │
│   └── student/
│       ├── layout.tsx               # Student layout
│       ├── page.tsx                 # Student dashboard
│       ├── workspace/page.tsx       # Main 3-column workspace
│       ├── problem-sets/
│       │   ├── page.tsx            # List problem sets
│       │   └── [setId]/
│       │       ├── page.tsx        # View problem set
│       │       └── submit/page.tsx # Submit solution
│       └── grades/page.tsx          # View all grades
│
├── components/
│   ├── ui/                          # Reusable UI components
│   ├── layout/                      # Layout components
│   ├── professor/                   # Professor components
│   └── student/                     # Student components
│
├── lib/
│   ├── api/                         # API client
│   ├── hooks/                       # Custom hooks
│   ├── types/                       # TypeScript types
│   └── utils/                       # Utilities
│
└── public/                          # Static assets
```

---

## 🎨 Design System

### Colors (Tailwind Config)

```typescript
// tailwind.config.ts
colors: {
  aub: {
    green: {
      dark: '#1a4d2e',
      DEFAULT: '#2d5f3f',
      light: '#4a7c59',
      pale: '#e8f5e9',
    },
    gold: {
      dark: '#a68a5c',
      DEFAULT: '#c5a572',
      light: '#d4b98a',
    },
    cream: '#faf8f3',
    beige: '#f5f1e8',
  },
}
```

### Component Classes

```css
/* Buttons */
.btn-primary → Green background, white text
.btn-secondary → White background, green border
.btn-gold → Gold background, white text

/* Cards */
.card → White background, shadow, rounded
.card-hover → Card with hover effect

/* Inputs */
.input → Standard input with green focus ring

/* Badges */
.badge-green → Green badge
.badge-gold → Gold badge
```

---

## 🏗️ Core Components

### 1. Root Layout (`app/layout.tsx`)

```typescript
import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AUB Learning Management System',
  description: 'AI-powered learning platform for American University of Beirut',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-aub-cream`}>
        {children}
      </body>
    </html>
  )
}
```

### 2. Landing Page (`app/page.tsx`)

```typescript
'use client';

import Link from 'next/link';
import Image from 'next/image';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-aub-green-dark via-aub-green to-aub-green-light">
      <div className="container-aub py-20">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="mb-8">
            {/* AUB Logo */}
            <h1 className="text-5xl font-bold text-white mb-4">
              American University of Beirut
            </h1>
            <h2 className="text-3xl text-aub-gold-light">
              Learning Management System
            </h2>
          </div>
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            AI-powered platform for course management, problem set generation, 
            and intelligent grading
          </p>
        </div>

        {/* Role Selection */}
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Professor Card */}
          <Link href="/professor">
            <div className="card-hover bg-white p-8 text-center transform hover:scale-105 transition-transform">
              <div className="text-6xl mb-4">👨‍🏫</div>
              <h3 className="text-2xl font-bold text-aub-green-dark mb-3">
                Professor Portal
              </h3>
              <p className="text-gray-600 mb-4">
                Upload materials, generate problem sets, grade submissions, 
                and view analytics
              </p>
              <div className="btn-primary inline-block">
                Enter as Professor
              </div>
            </div>
          </Link>

          {/* Student Card */}
          <Link href="/student">
            <div className="card-hover bg-white p-8 text-center transform hover:scale-105 transition-transform">
              <div className="text-6xl mb-4">🎓</div>
              <h3 className="text-2xl font-bold text-aub-green-dark mb-3">
                Student Portal
              </h3>
              <p className="text-gray-600 mb-4">
                Access materials, chat with AI tutor, complete problem sets, 
                and view grades
              </p>
              <div className="btn-primary inline-block">
                Enter as Student
              </div>
            </div>
          </Link>
        </div>

        {/* Features */}
        <div className="mt-20 text-center">
          <h3 className="text-2xl font-bold text-white mb-8">
            Powered by AI
          </h3>
          <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto">
            <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
              <div className="text-3xl mb-2">📚</div>
              <p className="text-white font-medium">Smart Chunking</p>
            </div>
            <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
              <div className="text-3xl mb-2">🤖</div>
              <p className="text-white font-medium">AI Problem Generation</p>
            </div>
            <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
              <div className="text-3xl mb-2">✍️</div>
              <p className="text-white font-medium">Automated Grading</p>
            </div>
            <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
              <div className="text-3xl mb-2">💬</div>
              <p className="text-white font-medium">RAG Chatbot</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 👨‍🏫 Professor Interface

### Professor Layout (`app/professor/layout.tsx`)

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';

export default function ProfessorLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { href: '/professor', label: 'Dashboard', icon: '📊' },
    { href: '/professor/materials', label: 'Materials', icon: '📚' },
    { href: '/professor/problem-sets', label: 'Problem Sets', icon: '📝' },
    { href: '/professor/analytics', label: 'Analytics', icon: '📈' },
  ];

  return (
    <div className="min-h-screen bg-aub-cream">
      {/* Top Navigation */}
      <header className="bg-aub-green-dark text-white shadow-lg">
        <div className="container-aub">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <Link href="/professor" className="text-xl font-bold">
                AUB LMS
              </Link>
              <nav className="hidden md:flex space-x-1">
                {navItems.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`px-4 py-2 rounded-lg transition-colors ${
                        isActive
                          ? 'bg-aub-gold text-white'
                          : 'text-white/80 hover:bg-aub-green hover:text-white'
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
              <span className="text-sm">Prof. John Doe</span>
              <Link href="/" className="btn-secondary text-sm">
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
```

### Professor Dashboard (`app/professor/page.tsx`)

```typescript
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getSystemStats, getAllDocuments } from '@/lib/api/materials';

export default function ProfessorDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [systemStats, documents] = await Promise.all([
          getSystemStats(),
          getAllDocuments(),
        ]);
        setStats({ ...systemStats, documents });
      } catch (error) {
        console.error('Failed to load stats:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="card gradient-aub text-white p-8">
        <h1 className="text-3xl font-bold mb-2">Welcome back, Professor!</h1>
        <p className="text-white/90">
          Manage your courses, generate problem sets, and track student performance
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid md:grid-cols-4 gap-6">
        <div className="card">
          <div className="text-3xl mb-2">📚</div>
          <div className="text-2xl font-bold text-aub-green-dark">
            {stats?.total_documents || 0}
          </div>
          <div className="text-sm text-gray-600">Course Materials</div>
        </div>
        <div className="card">
          <div className="text-3xl mb-2">📝</div>
          <div className="text-2xl font-bold text-aub-green-dark">12</div>
          <div className="text-sm text-gray-600">Problem Sets</div>
        </div>
        <div className="card">
          <div className="text-3xl mb-2">👥</div>
          <div className="text-2xl font-bold text-aub-green-dark">45</div>
          <div className="text-sm text-gray-600">Students</div>
        </div>
        <div className="card">
          <div className="text-3xl mb-2">✅</div>
          <div className="text-2xl font-bold text-aub-green-dark">128</div>
          <div className="text-sm text-gray-600">Graded Submissions</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6">
        <Link href="/professor/materials">
          <div className="card-hover">
            <h3 className="text-lg font-semibold text-aub-green-dark mb-2">
              📤 Upload Material
            </h3>
            <p className="text-sm text-gray-600">
              Add new course PDFs and visualize chunking
            </p>
          </div>
        </Link>
        <Link href="/professor/problem-sets/generate">
          <div className="card-hover">
            <h3 className="text-lg font-semibold text-aub-green-dark mb-2">
              ✨ Generate Problem Set
            </h3>
            <p className="text-sm text-gray-600">
              Create AI-powered problem sets from materials
            </p>
          </div>
        </Link>
        <Link href="/professor/analytics">
          <div className="card-hover">
            <h3 className="text-lg font-semibold text-aub-green-dark mb-2">
              📊 View Analytics
            </h3>
            <p className="text-sm text-gray-600">
              Track performance and identify trends
            </p>
          </div>
        </Link>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-bold text-aub-green-dark mb-4">
          Recent Activity
        </h2>
        <div className="space-y-3">
          {[
            { action: 'Generated problem set', item: 'Chapter 5 Problems', time: '2 hours ago' },
            { action: 'Graded submissions', item: 'Problem Set 3', time: '5 hours ago' },
            { action: 'Uploaded material', item: 'Chapter 6 Notes', time: '1 day ago' },
          ].map((activity, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
              <div>
                <div className="font-medium text-gray-900">{activity.action}</div>
                <div className="text-sm text-gray-600">{activity.item}</div>
              </div>
              <div className="text-sm text-gray-500">{activity.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## 🎓 Student Interface

### Student Workspace (`app/student/workspace/page.tsx`)

This is the main 3-column interface:

```typescript
'use client';

import { useState, useEffect } from 'react';
import MaterialsPanel from '@/components/student/MaterialsPanel';
import ChatInterface from '@/components/student/ChatInterface';
import ProblemSetPanel from '@/components/student/ProblemSetPanel';

export default function StudentWorkspace() {
  const [selectedMaterial, setSelectedMaterial] = useState<string | null>(null);

  return (
    <div className="h-[calc(100vh-4rem)] flex gap-4">
      {/* Left Panel: Materials */}
      <div className="w-80 flex-shrink-0">
        <MaterialsPanel
          selectedMaterial={selectedMaterial}
          onSelectMaterial={setSelectedMaterial}
        />
      </div>

      {/* Center Panel: Chat */}
      <div className="flex-1 min-w-0">
        <ChatInterface selectedMaterial={selectedMaterial} />
      </div>

      {/* Right Panel: Problem Sets */}
      <div className="w-96 flex-shrink-0">
        <ProblemSetPanel />
      </div>
    </div>
  );
}
```

---

## 🧩 Key Components

### Material Uploader (`components/professor/MaterialUploader.tsx`)

```typescript
'use client';

import { useState } from 'react';
import { uploadMaterialWithProgress } from '@/lib/api/materials';
import type { UploadProgress } from '@/lib/types';

export default function MaterialUploader({ onUploadComplete }: any) {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState<UploadProgress | null>(null);

  const handleUpload = async () => {
    if (!file) return;

    setProgress({
      file,
      progress: 0,
      status: 'uploading',
    });

    try {
      const result = await uploadMaterialWithProgress(
        file,
        undefined,
        false,
        (prog) => {
          setProgress((prev) => prev ? { ...prev, progress: prog } : null);
        }
      );

      setProgress((prev) => prev ? { ...prev, status: 'complete' } : null);
      onUploadComplete?.(result);
    } catch (error) {
      setProgress((prev) => prev ? {
        ...prev,
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed',
      } : null);
    }
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Upload Course Material</h3>
      
      {/* File Input */}
      <div className="mb-4">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="input"
        />
      </div>

      {/* Progress */}
      {progress && (
        <div className="mb-4">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {progress.status === 'uploading' && `Uploading... ${Math.round(progress.progress)}%`}
            {progress.status === 'processing' && 'Processing and chunking...'}
            {progress.status === 'complete' && '✅ Upload complete!'}
            {progress.status === 'error' && `❌ ${progress.error}`}
          </p>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!file || progress?.status === 'uploading'}
        className="btn-primary w-full"
      >
        {progress?.status === 'uploading' ? 'Uploading...' : 'Upload PDF'}
      </button>
    </div>
  );
}
```

### Chat Interface (`components/student/ChatInterface.tsx`)

```typescript
'use client';

import { useState } from 'react';
import { ragQuery } from '@/lib/api/rag';
import type { ChatMessage } from '@/lib/types';

export default function ChatInterface({ selectedMaterial }: { selectedMaterial: string | null }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || !selectedMaterial) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await ragQuery({
        query: input,
        doc_id: selectedMaterial,
        top_k: 4,
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        chunks: response.retrieved_chunks,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel h-full flex flex-col">
      <div className="panel-header">
        <h3 className="font-semibold text-aub-green-dark">
          AI Tutor {selectedMaterial && `- ${selectedMaterial}`}
        </h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-container">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            Select a material and ask a question to get started
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-aub-green text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="spinner"></div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question..."
            disabled={!selectedMaterial || loading}
            className="input flex-1"
          />
          <button
            onClick={handleSend}
            disabled={!selectedMaterial || loading || !input.trim()}
            className="btn-primary"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 📊 Analytics Dashboard

Use Chart.js or Recharts for visualizations:

```typescript
import { Line, Bar, Pie } from 'react-chartjs-2';

// Grade distribution chart
// Performance trends over time
// Common error patterns
// Student progress tracking
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd nextjs_frontend
npm install
```

### 2. Configure Environment

```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Run Development Server

```bash
npm run dev
```

### 4. Build for Production

```bash
npm run build
npm start
```

---

## 📝 Implementation Checklist

### Phase 1: Core Setup
- [ ] Configure Tailwind with AUB colors
- [ ] Create root layout and landing page
- [ ] Set up API client
- [ ] Define TypeScript types

### Phase 2: Professor Interface
- [ ] Professor layout and navigation
- [ ] Material upload with progress
- [ ] Chunk visualization
- [ ] Problem set generator
- [ ] Grading interface
- [ ] Analytics dashboard

### Phase 3: Student Interface
- [ ] Student layout and navigation
- [ ] 3-column workspace
- [ ] Materials panel
- [ ] Chat interface with RAG
- [ ] Problem set viewer
- [ ] Submission uploader
- [ ] Grades viewer

### Phase 4: Polish
- [ ] Responsive design
- [ ] Loading states
- [ ] Error handling
- [ ] Accessibility
- [ ] Performance optimization

---

## 🎯 Key Features

### Professor
✅ Upload PDFs with progress tracking
✅ Visualize semantic chunks
✅ Generate AI problem sets
✅ View and grade submissions
✅ Analytics and insights

### Student
✅ Browse course materials
✅ Chat with AI tutor (RAG)
✅ View problem sets
✅ Submit solutions
✅ View grades and feedback

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs)
- [SWR for Data Fetching](https://swr.vercel.app)
- [React Hook Form](https://react-hook-form.com)
- [Chart.js](https://www.chartjs.org)

---

This implementation provides a solid foundation for the AUB LMS. Customize and extend as needed!

