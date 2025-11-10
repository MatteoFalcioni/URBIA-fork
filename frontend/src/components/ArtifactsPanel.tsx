/**
 * ArtifactsPanel: Right sidebar for displaying artifacts (reports, reviews, etc.)
 */

import { X, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChatStore } from '@/store/chatStore';

export function ArtifactsPanel() {
  const togglePanel = useChatStore((state) => state.toggleArtifactsPanel);
  const currentReport = useChatStore((state) => state.currentReport);
  const currentReportTitle = useChatStore((state) => state.currentReportTitle);

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-slate-700 flex-shrink-0">
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-gray-600 dark:text-slate-400" />
          <h2 className="text-lg font-semibold">Artifacts</h2>
        </div>
        <button
          onClick={togglePanel}
          className="p-1.5 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Close artifacts panel"
        >
          <X size={18} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {currentReport ? (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {currentReportTitle && (
              <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-slate-100 border-b border-gray-200 dark:border-slate-700 pb-2">
                {currentReportTitle}
              </h1>
            )}
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {currentReport}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 dark:text-slate-400">
            <FileText size={48} className="mb-4 opacity-30" />
            <p className="text-sm">No artifacts yet</p>
            <p className="text-xs mt-1">Reports and analysis will appear here</p>
          </div>
        )}
      </div>
    </>
  );
}

