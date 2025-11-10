/**
 * AnalysisObjectivesDropdown: displays analysis objectives in a collapsible dropdown in the header
 */

import { useEffect, useState } from 'react';
import { ListChecks, ChevronDown, ChevronUp } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { getThreadState } from '@/utils/api';

export function AnalysisObjectivesDropdown() {
  const currentThreadId = useChatStore((state) => state.currentThreadId);
  const analysisObjectives = useChatStore((state) => state.analysisObjectives);
  const setAnalysisObjectives = useChatStore((state) => state.setAnalysisObjectives);
  const [isExpanded, setIsExpanded] = useState(false);

  // Load objectives once when thread changes
  useEffect(() => {
    if (!currentThreadId) {
      setAnalysisObjectives([]);
      return;
    }

    const loadObjectives = async () => {
      try {
        const state = await getThreadState(currentThreadId);
        setAnalysisObjectives(state.analysis_objectives || []);
      } catch (err: any) {
        // Only log non-404 errors (404 means thread was deleted)
        if (err?.response?.status !== 404) {
          console.error('Failed to load analysis objectives:', err);
        }
        setAnalysisObjectives([]);
      }
    };

    // Load once on thread change
    loadObjectives();
  }, [currentThreadId, setAnalysisObjectives]);

  // Don't show if no thread
  if (!currentThreadId) {
    return null;
  }

  return (
    <div className="relative">
      {/* Toggle button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 hover:bg-gray-100 dark:hover:bg-slate-700"
        style={{ 
          color: 'var(--text-primary)',
        }}
      >
        <ListChecks size={16} className="text-gray-600 dark:text-slate-400" />
        <span className="font-medium">Objectives</span>
        {analysisObjectives.length > 0 ? (
          <span className="text-xs opacity-60">({analysisObjectives.length})</span>
        ) : (
          <span className="text-xs opacity-40 italic">none set</span>
        )}
        {isExpanded ? (
          <ChevronUp size={14} className="opacity-60" />
        ) : (
          <ChevronDown size={14} className="opacity-60" />
        )}
      </button>

      {/* Dropdown content */}
      {isExpanded && (
        <div 
          className="absolute top-full right-0 mt-1 w-80 rounded-lg shadow-lg border z-50 max-h-60 overflow-y-auto"
          style={{ 
            backgroundColor: 'var(--bg-primary)',
            borderColor: 'var(--border)',
          }}
        >
          <div className="p-3">
            <div className="flex items-center gap-2 mb-2 pb-2 border-b" style={{ borderColor: 'var(--border)' }}>
              <ListChecks size={14} className="text-gray-600 dark:text-slate-400" />
              <span className="text-xs font-medium opacity-75">Analysis Objectives</span>
            </div>
            {analysisObjectives.length > 0 ? (
              <ul className="space-y-1.5">
                {analysisObjectives.map((objective, idx) => (
                  <li key={idx} className="flex gap-2 text-xs">
                    <span className="text-gray-600 dark:text-slate-400 flex-shrink-0">•</span>
                    <span style={{ color: 'var(--text-primary)' }}>{objective}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs opacity-60 italic text-center py-2">
                None set yet
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

