'use client';

import Link from 'next/link';

/**
 * Student Dashboard
 * Overview page with quick actions
 */
export default function StudentDashboard() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Section */}
      <div className="card bg-aub-red text-white p-8">
        <h1 className="text-3xl font-bold mb-2 text-white">Welcome back, Jane!</h1>
        <p className="text-white/90">
          Ready to learn? Access your materials, chat with the AI tutor, and complete problem sets.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="card hover:shadow-aub-lg transition-shadow">
          <div className="text-3xl mb-2">📚</div>
          <div className="text-2xl font-bold text-aub-red">12</div>
          <div className="text-sm text-gray-600">Available Materials</div>
        </div>

        <div className="card hover:shadow-aub-lg transition-shadow">
          <div className="text-3xl mb-2">📝</div>
          <div className="text-2xl font-bold text-aub-red">8</div>
          <div className="text-sm text-gray-600">Problem Sets</div>
        </div>

        <div className="card hover:shadow-aub-lg transition-shadow">
          <div className="text-3xl mb-2">✅</div>
          <div className="text-2xl font-bold text-aub-red">85%</div>
          <div className="text-sm text-gray-600">Average Grade</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-aub-black mb-4">Quick Actions</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <Link href="/student/workspace">
            <div className="card-hover">
              <h3 className="text-lg font-semibold text-aub-black mb-2">
                📚 Study Workspace
              </h3>
              <p className="text-sm text-gray-600">
                Access materials and chat with the AI tutor
              </p>
            </div>
          </Link>

          <Link href="/student/problem-sets">
            <div className="card-hover">
              <h3 className="text-lg font-semibold text-aub-black mb-2">
                📝 View Problem Sets
              </h3>
              <p className="text-sm text-gray-600">
                Complete practice problems and submit solutions
              </p>
            </div>
          </Link>

          <Link href="/student/grades">
            <div className="card-hover">
              <h3 className="text-lg font-semibold text-aub-black mb-2">
                📊 Check Grades
              </h3>
              <p className="text-sm text-gray-600">
                View your submissions and feedback
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-bold text-aub-black mb-4">
          Recent Activity
        </h2>
        <div className="space-y-3">
          {[
            { action: 'Completed problem set', item: 'Thermodynamics Set 3', time: '2 hours ago', icon: '✅' },
            { action: 'Started studying', item: 'Chapter 7 - Fluid Mechanics', time: '5 hours ago', icon: '📖' },
            { action: 'Submitted solution', item: 'Problem Set 2', time: '1 day ago', icon: '📤' },
          ].map((activity, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{activity.icon}</span>
                <div>
                  <div className="font-medium text-gray-900">{activity.action}</div>
                  <div className="text-sm text-gray-600">{activity.item}</div>
                </div>
              </div>
              <div className="text-sm text-gray-500">{activity.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

