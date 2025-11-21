'use client';

import { useState, useEffect } from 'react';
import MaterialsPanel from '@/components/student/MaterialsPanel';
import ChatInterface from '@/components/student/ChatInterface';
import QuickInfoPanel from '@/components/student/QuickInfoPanel';

/**
 * Student Workspace
 * 3-column layout: Materials | Chat | Quick Info
 */
export default function StudentWorkspace() {
  const [selectedMaterial, setSelectedMaterial] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner-lg"></div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-aub-black">Study Workspace</h1>
        <p className="text-gray-600 text-sm mt-1">
          Select a material and ask questions to your AI tutor
        </p>
      </div>

      {/* 3-Column Layout */}
      <div className="grid lg:grid-cols-12 gap-4 h-[calc(100vh-12rem)]">
        {/* Left: Materials List */}
        <div className="lg:col-span-3 overflow-hidden">
          <MaterialsPanel
            selectedMaterial={selectedMaterial}
            onSelectMaterial={setSelectedMaterial}
          />
        </div>

        {/* Center: Chat Interface */}
        <div className="lg:col-span-6 overflow-hidden">
          <ChatInterface selectedMaterial={selectedMaterial} />
        </div>

        {/* Right: Quick Info/Tips */}
        <div className="lg:col-span-3 overflow-hidden">
          <QuickInfoPanel selectedMaterial={selectedMaterial} />
        </div>
      </div>
    </div>
  );
}

