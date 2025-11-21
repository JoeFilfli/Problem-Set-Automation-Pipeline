'use client';

import Link from 'next/link';

/**
 * Landing Page - Role Selection
 * Simple portal selection for professors and students
 */
export default function Home() {
  return (
    <div className="min-h-screen gradient-aub">
      <div className="container-aub py-20">
        {/* Header */}
        <div className="text-center mb-16 animate-fade-in">
          <div className="mb-8">
            <h1 className="text-5xl font-bold text-white mb-4">
              American University of Beirut
            </h1>
            <h2 className="text-3xl text-white/90">
              Learning Management System
            </h2>
          </div>
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            AI-powered platform for course management, problem set generation,
            and intelligent grading
          </p>
        </div>

        {/* Role Selection Cards */}
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Professor Card */}
          <Link href="/professor">
            <div className="card-hover bg-white p-8 text-center transform hover:scale-105 transition-transform animate-slide-up">
              <div className="text-6xl mb-4">👨‍🏫</div>
              <h3 className="text-2xl font-bold text-aub-black mb-3">
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
            <div className="card-hover bg-white p-8 text-center transform hover:scale-105 transition-transform animate-slide-up" style={{ animationDelay: '0.1s' }}>
              <div className="text-6xl mb-4">🎓</div>
              <h3 className="text-2xl font-bold text-aub-black mb-3">
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
        <div className="mt-20 text-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <h3 className="text-2xl font-bold text-white mb-8">
            Powered by AI
          </h3>
          <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto">
            <div className="bg-white/10 backdrop-blur p-6 rounded-aub">
              <div className="text-3xl mb-2">📚</div>
              <p className="text-white font-medium">Smart Chunking</p>
            </div>
            <div className="bg-white/10 backdrop-blur p-6 rounded-aub">
              <div className="text-3xl mb-2">🤖</div>
              <p className="text-white font-medium">AI Problem Generation</p>
            </div>
            <div className="bg-white/10 backdrop-blur p-6 rounded-aub">
              <div className="text-3xl mb-2">✍️</div>
              <p className="text-white font-medium">Automated Grading</p>
            </div>
            <div className="bg-white/10 backdrop-blur p-6 rounded-aub">
              <div className="text-3xl mb-2">💬</div>
              <p className="text-white font-medium">RAG Chatbot</p>
            </div>
          </div>
        </div>

        {/* Quick Demo Link */}
        <div className="mt-12 text-center">
          <Link href="/rag-lab" className="text-white/80 hover:text-white transition-colors text-sm underline">
            Or try the RAG Lab Demo
          </Link>
        </div>
      </div>
    </div>
  );
}
