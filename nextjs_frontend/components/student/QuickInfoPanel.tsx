'use client';

interface QuickInfoPanelProps {
  selectedMaterial: string | null;
}

/**
 * Quick Info Panel Component
 * Shows tips and helpful information
 */
export default function QuickInfoPanel({ selectedMaterial }: QuickInfoPanelProps) {
  return (
    <div className="panel h-full flex flex-col custom-scrollbar">
      {/* Header */}
      <div className="panel-header">
        <h3 className="font-semibold text-aub-black">Tips &amp; Help</h3>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* How to Use */}
        <div className="bg-aub-beige p-3 rounded-aub">
          <h4 className="text-sm font-semibold text-aub-black mb-2">How to Use</h4>
          <ul className="text-xs text-gray-700 space-y-1">
            <li>- Select a material from the list</li>
            <li>- Ask questions in natural language</li>
            <li>- Get answers with source citations</li>
          </ul>
        </div>

        {/* Example Questions */}
        <div className="bg-white border border-gray-200 p-3 rounded-aub">
          <h4 className="text-sm font-semibold text-aub-black mb-2">Example Questions</h4>
          <div className="space-y-2">
            <button className="w-full text-left text-xs bg-aub-beige hover:bg-aub-red-pale p-2 rounded transition-colors">
              &quot;Explain the main concept in simple terms&quot;
            </button>
            <button className="w-full text-left text-xs bg-aub-beige hover:bg-aub-red-pale p-2 rounded transition-colors">
              &quot;What are the key formulas?&quot;
            </button>
            <button className="w-full text-left text-xs bg-aub-beige hover:bg-aub-red-pale p-2 rounded transition-colors">
              &quot;Give me an example problem&quot;
            </button>
            <button className="w-full text-left text-xs bg-aub-beige hover:bg-aub-red-pale p-2 rounded transition-colors">
              &quot;How does this relate to the previous chapter?&quot;
            </button>
          </div>
        </div>

        {/* Current Material Info */}
        {selectedMaterial && (
          <div className="bg-aub-red-pale p-3 rounded-aub">
            <h4 className="text-sm font-semibold text-aub-black mb-1">Current Material</h4>
            <p className="text-xs text-gray-700 break-words">{selectedMaterial}</p>
          </div>
        )}

        {/* Study Tips */}
        <div className="bg-white border border-gray-200 p-3 rounded-aub">
          <h4 className="text-sm font-semibold text-aub-black mb-2">Study Tips</h4>
          <ul className="text-xs text-gray-700 space-y-1">
            <li>- Break down complex topics</li>
            <li>- Ask for clarification</li>
            <li>- Request practice problems</li>
            <li>- Review key concepts regularly</li>
          </ul>
        </div>

        {/* Features */}
        <div className="bg-white border border-gray-200 p-3 rounded-aub">
          <h4 className="text-sm font-semibold text-aub-black mb-2">Features</h4>
          <ul className="text-xs text-gray-700 space-y-1">
            <li>- Context-aware answers</li>
            <li>- Source citations included</li>
            <li>- Math notation support</li>
            <li>- Personalized learning</li>
          </ul>
        </div>

        {/* Need Help? */}
        <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-aub">
          <h4 className="text-sm font-semibold text-yellow-800 mb-1">Need Help?</h4>
          <p className="text-xs text-yellow-700">
            Contact your TA or visit the help desk if you encounter any issues.
          </p>
        </div>
      </div>
    </div>
  );
}
