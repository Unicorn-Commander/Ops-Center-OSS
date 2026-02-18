import React, { useRef, useEffect } from 'react';

/**
 * Terminal-style output component for displaying skill execution results.
 * Renders pre-formatted text in a dark terminal look.
 */
export default function CommandOutput({ output, title, isStreaming }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [output]);

  if (!output) return null;

  return (
    <div className="rounded-lg overflow-hidden border border-gray-700 my-2">
      {title && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-gray-800 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
              <span className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
            </div>
            <span className="text-xs text-gray-400 font-mono">{title}</span>
          </div>
          {isStreaming && (
            <span className="text-xs text-green-400 animate-pulse">streaming...</span>
          )}
        </div>
      )}
      <div
        ref={containerRef}
        className="bg-[#0d1117] p-3 max-h-80 overflow-auto"
      >
        <pre className="text-sm font-mono text-gray-200 whitespace-pre-wrap break-words leading-relaxed">
          {output}
        </pre>
      </div>
    </div>
  );
}
