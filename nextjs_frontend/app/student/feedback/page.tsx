'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { submitFeedback } from '@/lib/api/feedback';
import type { CourseFeedbackCreate } from '@/lib/types';

/**
 * Course Feedback Survey Page (Student View)
 * Students provide ratings and feedback about the course
 */
export default function CourseFeedbackPage() {
  const router = useRouter();

  // Form state
  const [formData, setFormData] = useState<CourseFeedbackCreate>({
    overall_rating: 3,
    content_quality: 3,
    difficulty_level: 3,
    pacing: 3,
    materials_quality: 3,
    instructor_effectiveness: 3,
    what_worked_well: '',
    what_needs_improvement: '',
    suggestions: '',
    favorite_topics: [],
    challenging_topics: [],
  });

  // Topic inputs
  const [favoriteTopicInput, setFavoriteTopicInput] = useState('');
  const [challengingTopicInput, setChallengingTopicInput] = useState('');

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle rating change
  const handleRatingChange = (field: string, value: number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle text change
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Add topic handlers
  const handleAddFavoriteTopic = () => {
    const topic = favoriteTopicInput.trim();
    if (topic && !formData.favorite_topics?.includes(topic)) {
      setFormData(prev => ({
        ...prev,
        favorite_topics: [...(prev.favorite_topics || []), topic]
      }));
      setFavoriteTopicInput('');
    }
  };

  const handleAddChallengingTopic = () => {
    const topic = challengingTopicInput.trim();
    if (topic && !formData.challenging_topics?.includes(topic)) {
      setFormData(prev => ({
        ...prev,
        challenging_topics: [...(prev.challenging_topics || []), topic]
      }));
      setChallengingTopicInput('');
    }
  };

  const handleRemoveFavoriteTopic = (topic: string) => {
    setFormData(prev => ({
      ...prev,
      favorite_topics: (prev.favorite_topics || []).filter(t => t !== topic)
    }));
  };

  const handleRemoveChallengingTopic = (topic: string) => {
    setFormData(prev => ({
      ...prev,
      challenging_topics: (prev.challenging_topics || []).filter(t => t !== topic)
    }));
  };

  // Submit feedback
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setSubmitting(true);
      setError(null);

      await submitFeedback(formData);
      setSuccess(true);

      // Redirect after short delay
      setTimeout(() => {
        router.push('/student');
      }, 2000);
    } catch (err: any) {
      console.error('Error submitting feedback:', err);
      setError(err.message || 'Failed to submit feedback');
      setSubmitting(false);
    }
  };

  // Render star rating
  const StarRating = ({ value, onChange, label, description }: {
    value: number;
    onChange: (value: number) => void;
    label: string;
    description: string;
  }) => (
    <div className="space-y-2">
      <div>
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        {[1, 2, 3, 4, 5].map(star => (
          <button
            key={star}
            type="button"
            onClick={() => onChange(star)}
            className={`text-3xl transition-all ${
              star <= value
                ? 'text-yellow-400 hover:text-yellow-500'
                : 'text-gray-300 hover:text-gray-400'
            }`}
          >
            ★
          </button>
        ))}
        <span className="ml-2 text-sm font-medium text-gray-700">{value}/5</span>
      </div>
    </div>
  );

  if (success) {
    return (
      <div className="max-w-2xl mx-auto space-y-8 animate-fade-in">
        <div className="card bg-green-50 border-green-200 text-center py-12">
          <div className="text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-green-900 mb-2">
            Thank You for Your Feedback!
          </h2>
          <p className="text-green-700">
            Your input helps improve the course for everyone.
          </p>
          <p className="text-sm text-green-600 mt-4">
            Redirecting to dashboard...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-aub-black">Course Feedback Survey</h1>
        <p className="text-gray-600 mt-2">
          Help us improve! Your honest feedback makes the course better for everyone.
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-aub p-4 text-red-800">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Rating Scales */}
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-6">Rate Your Experience</h2>
          <div className="space-y-6">
            <StarRating
              value={formData.overall_rating}
              onChange={(v) => handleRatingChange('overall_rating', v)}
              label="Overall Course Rating"
              description="How would you rate the course overall?"
            />
            <hr className="border-gray-200" />
            <StarRating
              value={formData.content_quality}
              onChange={(v) => handleRatingChange('content_quality', v)}
              label="Content Quality"
              description="Are the topics relevant and well-explained?"
            />
            <StarRating
              value={formData.difficulty_level}
              onChange={(v) => handleRatingChange('difficulty_level', v)}
              label="Difficulty Level"
              description="1 = Too Easy, 3 = Just Right, 5 = Too Hard"
            />
            <StarRating
              value={formData.pacing}
              onChange={(v) => handleRatingChange('pacing', v)}
              label="Course Pacing"
              description="1 = Too Slow, 3 = Just Right, 5 = Too Fast"
            />
            <StarRating
              value={formData.materials_quality}
              onChange={(v) => handleRatingChange('materials_quality', v)}
              label="Materials Quality"
              description="Textbooks, slides, resources, etc."
            />
            <StarRating
              value={formData.instructor_effectiveness}
              onChange={(v) => handleRatingChange('instructor_effectiveness', v)}
              label="Instructor Effectiveness"
              description="Teaching clarity, availability, and support"
            />
          </div>
        </div>

        {/* Topics */}
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">Topics</h2>

          {/* Favorite Topics */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Favorite Topics
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Which topics did you enjoy the most?
            </p>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={favoriteTopicInput}
                onChange={(e) => setFavoriteTopicInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddFavoriteTopic())}
                className="input-primary flex-1"
                placeholder="e.g., Linear Programming"
              />
              <button
                type="button"
                onClick={handleAddFavoriteTopic}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.favorite_topics?.map((topic, i) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm flex items-center gap-2"
                >
                  {topic}
                  <button
                    type="button"
                    onClick={() => handleRemoveFavoriteTopic(topic)}
                    className="text-green-600 hover:text-green-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Challenging Topics */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Challenging Topics
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Which topics did you find most difficult?
            </p>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={challengingTopicInput}
                onChange={(e) => setChallengingTopicInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddChallengingTopic())}
                className="input-primary flex-1"
                placeholder="e.g., Network Flows"
              />
              <button
                type="button"
                onClick={handleAddChallengingTopic}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.challenging_topics?.map((topic, i) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm flex items-center gap-2"
                >
                  {topic}
                  <button
                    type="button"
                    onClick={() => handleRemoveChallengingTopic(topic)}
                    className="text-red-600 hover:text-red-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Open-Ended Feedback */}
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">Tell Us More</h2>

          <div className="space-y-6">
            <div>
              <label htmlFor="what_worked_well" className="block text-sm font-medium text-gray-700 mb-2">
                What worked well?
              </label>
              <textarea
                id="what_worked_well"
                name="what_worked_well"
                value={formData.what_worked_well}
                onChange={handleTextChange}
                rows={4}
                className="input-primary w-full"
                placeholder="What aspects of the course did you find most helpful or enjoyable?"
              />
            </div>

            <div>
              <label htmlFor="what_needs_improvement" className="block text-sm font-medium text-gray-700 mb-2">
                What needs improvement?
              </label>
              <textarea
                id="what_needs_improvement"
                name="what_needs_improvement"
                value={formData.what_needs_improvement}
                onChange={handleTextChange}
                rows={4}
                className="input-primary w-full"
                placeholder="What aspects could be better? Be specific!"
              />
            </div>

            <div>
              <label htmlFor="suggestions" className="block text-sm font-medium text-gray-700 mb-2">
                Suggestions for Next Semester
              </label>
              <textarea
                id="suggestions"
                name="suggestions"
                value={formData.suggestions}
                onChange={handleTextChange}
                rows={4}
                className="input-primary w-full"
                placeholder="Any ideas for how to make this course even better?"
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={() => router.back()}
            className="btn-secondary"
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={submitting}
          >
            {submitting ? (
              <>
                <span className="spinner mr-2"></span>
                Submitting...
              </>
            ) : (
              '📝 Submit Feedback'
            )}
          </button>
        </div>
      </form>

      {/* Privacy Note */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">🔒 Privacy Note</h3>
        <p className="text-sm text-blue-800">
          Your feedback is valuable for improving the course. 
          All responses are reviewed by the instructor to enhance the learning experience.
          Thank you for taking the time to help us improve!
        </p>
      </div>
    </div>
  );
}

