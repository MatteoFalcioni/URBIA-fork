/**
 * ContextIndicator: circular progress indicator showing token usage.
 * Displays as a ring that fills as context grows, with "Summarizing..." when active.
 */

import { Loader2 } from 'lucide-react';

interface ContextIndicatorProps {
  tokensUsed: number;
  maxTokens: number;
  isSummarizing: boolean;
}

export function ContextIndicator({ tokensUsed, maxTokens, isSummarizing }: ContextIndicatorProps) {
  // Cap tokens at 90% threshold (summarization triggers at 90%)
  const effectiveMax = maxTokens * 0.9;
  const displayTokens = Math.min(tokensUsed, effectiveMax);
  
  // Calculate percentage (0-90 max, relative to maxTokens)
  const percentage = (displayTokens / maxTokens) * 100;
  
  // SVG circle parameters - smaller and bolder
  const radius = 10;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // SVG viewBox needs to account for stroke width to prevent clipping
  const strokeWidth = 2;
  const padding = strokeWidth / 2; // Half stroke width for padding
  const viewBoxSize = (radius + padding) * 2;
  const center = radius + padding;

  return (
    <div className="relative w-5 h-5" style={{ overflow: 'visible' }}>
      {/* Circular progress ring - smaller */}
      <svg 
        className="w-5 h-5 transform -rotate-90" 
        viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
        style={{ shapeRendering: 'geometricPrecision', overflow: 'visible' }}
      >
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          fill="none"
          style={{ shapeRendering: 'geometricPrecision' }}
        />
        {/* Progress circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke="var(--user-message-bg)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-500"
          strokeLinecap="round"
          style={{ shapeRendering: 'geometricPrecision' }}
        />
      </svg>
      {/* Center spinner when summarizing */}
      {isSummarizing && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 size={6} className="animate-spin" style={{ color: 'var(--user-message-bg)' }} />
        </div>
      )}
    </div>
  );
}
