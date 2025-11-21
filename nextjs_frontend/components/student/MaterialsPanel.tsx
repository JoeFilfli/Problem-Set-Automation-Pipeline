'use client';

import { useState, useEffect } from 'react';
import { getMaterials } from '@/lib/api';

interface MaterialsPanelProps {
  selectedMaterial: string | null;
  onSelectMaterial: (material: string) => void;
}

/**
 * Materials Panel Component
 * Shows list of available course materials
 */
export default function MaterialsPanel({
  selectedMaterial,
  onSelectMaterial,
}: MaterialsPanelProps) {
  const [materials, setMaterials] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load materials on mount
  useEffect(() => {
    async function loadMaterials() {
      try {
        setLoading(true);
        setError(null);
        const data = await getMaterials();
        setMaterials(data);
        
        // Auto-select first material if available
        if (data.length > 0 && !selectedMaterial) {
          onSelectMaterial(data[0]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load materials');
      } finally {
        setLoading(false);
      }
    }
    loadMaterials();
  }, []);

  return (
    <div className="panel h-full flex flex-col custom-scrollbar">
      {/* Header */}
      <div className="panel-header">
        <h3 className="font-semibold text-aub-black">📚 Course Materials</h3>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <div className="spinner"></div>
          </div>
        )}

        {error && (
          <div className="p-4">
            <div className="alert-error text-xs">
              <p>{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && materials.length === 0 && (
          <div className="p-4 text-center text-gray-500 text-sm">
            <p>No materials available</p>
          </div>
        )}

        {!loading && !error && materials.length > 0 && (
          <div className="p-2">
            {materials.map((material) => (
              <button
                key={material}
                onClick={() => onSelectMaterial(material)}
                className={`w-full text-left px-3 py-2.5 rounded-aub mb-1 transition-colors ${
                  selectedMaterial === material
                    ? 'bg-aub-red text-white'
                    : 'hover:bg-aub-beige text-gray-700'
                }`}
              >
                <div className="text-sm font-medium truncate">{material}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer Hint */}
      {materials.length > 0 && (
        <div className="p-3 border-t border-gray-200 bg-aub-beige/50">
          <p className="text-xs text-gray-600">
            💡 Select a material to start chatting
          </p>
        </div>
      )}
    </div>
  );
}

