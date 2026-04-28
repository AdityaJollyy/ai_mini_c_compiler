import { useState, useEffect, useRef } from 'react';

function OutputPanel({ compileResult, onFixWithAI, code }) {
  const [fixError, setFixError] = useState(null);
  const [isFixing, setIsFixing] = useState(false); // Local loading state for AI fix
  const [originalCode, setOriginalCode] = useState(null); // Store code before AI fix
  const [showOriginal, setShowOriginal] = useState(false); // Toggle for original code view
  const [aiFixApplied, setAiFixApplied] = useState(false); // Track if AI fix was applied
  const prevCompileResultRef = useRef(null); // Track previous compile result

  // Clear AI fix states when a new compilation happens (compileResult changes)
  useEffect(() => {
    // Only clear if this is a new compilation (compileResult changed and is not null)
    if (compileResult !== null && compileResult !== prevCompileResultRef.current) {
      // Clear AI fix related states when user re-compiles
      setOriginalCode(null);
      setShowOriginal(false);
      setAiFixApplied(false);
      setFixError(null);
    }
    prevCompileResultRef.current = compileResult;
  }, [compileResult]);

  const formatErrorsForAI = () => {
    if (!compileResult || !compileResult.errors) return '';
    return compileResult.errors
      .map(err => `Line ${err.line}: ${err.type} Error - ${err.message}`)
      .join('\n');
  };

  const handleFix = async () => {
    setFixError(null);
    setIsFixing(true); // Start loading
    setOriginalCode(code); // Save original code before fix
    const errorsText = formatErrorsForAI();
    
    try {
      const response = await fetch('http://localhost:8000/fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, errors: errorsText }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMessage = data.detail || 'Failed to fix code';
        setFixError(errorMessage);
        setOriginalCode(null); // Clear on error
        return;
      }

      onFixWithAI(data.fixed_code);
      setShowOriginal(true); // Auto-show original code comparison
      setAiFixApplied(true); // Mark that AI fix was applied
    } catch (error) {
      setFixError(error.message || 'Network error');
      setOriginalCode(null); // Clear on error
    } finally {
      setIsFixing(false); // Stop loading regardless of success/failure
    }
  };

  const hasErrors = compileResult && !compileResult.success && compileResult.errors?.length > 0;
  const isSuccess = compileResult && compileResult.success;

  return (
    <div className="flex flex-col h-full bg-gray-900 border-l border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div>
          <h2 className="text-lg font-semibold text-white">Output</h2>
          <p className="text-sm text-gray-400">Compilation results</p>
        </div>
        {hasErrors && (
          <button
            onClick={handleFix}
            disabled={isFixing}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isFixing ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                Fixing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Fix with AI
              </>
            )}
          </button>
        )}
      </div>

      {/* Output Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!compileResult && (
          <div className="text-gray-500 text-center mt-8">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>Click "Compile" to check your code</p>
          </div>
        )}

        {isSuccess && (
          <div className="space-y-4">
            {/* Success Message */}
            <div className="bg-green-900/30 border border-green-600 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 className="text-lg font-semibold text-green-400">Compilation Successful</h3>
                  <p className="text-sm text-green-300/80">No errors found in your Mini-C code.</p>
                </div>
              </div>
            </div>

            {/* Program Output */}
            <div className="bg-gray-800 border border-gray-600 rounded-lg overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2 bg-gray-700 border-b border-gray-600">
                <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-sm font-medium text-gray-300">Program Output</span>
              </div>
              <div className="p-4 font-mono text-sm">
                {compileResult.output ? (
                  <pre className="text-green-300 whitespace-pre-wrap">{compileResult.output}</pre>
                ) : (
                  <span className="text-gray-500 italic">No output (program has no printf statements)</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Fix Error */}
        {fixError && (
          <div className="mb-4 bg-red-900/30 border border-red-600 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 className="text-sm font-semibold text-red-400">AI Fix Failed</h4>
                <p className="text-sm text-red-300/80 mt-1">{fixError}</p>
              </div>
            </div>
          </div>
        )}

        {/* AI Fix Applied - Show original code for comparison */}
        {/* Only show when AI fix was just applied and user hasn't re-compiled yet */}
        {aiFixApplied && originalCode && !fixError && (
          <div className="mb-4 space-y-3">
            {/* Success banner */}
            <div className="bg-purple-900/30 border border-purple-600 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div>
                  <h3 className="text-lg font-semibold text-purple-400">AI Fix Applied</h3>
                  <p className="text-sm text-purple-300/80">Look for <code className="bg-purple-800/50 px-1 rounded">// FIXED:</code> comments in the editor</p>
                </div>
              </div>
            </div>

            {/* Collapsible original code section */}
            <div className="bg-gray-800 border border-gray-600 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className="w-full flex items-center justify-between px-4 py-2 bg-gray-700 hover:bg-gray-650 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  <span className="text-sm font-medium text-gray-300">Original Code (Before Fix)</span>
                </div>
                <svg 
                  className={`w-4 h-4 text-gray-400 transition-transform ${showOriginal ? 'rotate-180' : ''}`} 
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showOriginal && (
                <div className="p-4 border-t border-gray-600">
                  <pre className="text-sm text-gray-400 font-mono whitespace-pre-wrap overflow-x-auto">{originalCode}</pre>
                </div>
              )}
            </div>

            {/* Clear comparison button */}
            <button
              onClick={() => { setOriginalCode(null); setShowOriginal(false); setAiFixApplied(false); }}
              className="text-xs text-gray-500 hover:text-gray-400 transition-colors"
            >
              Dismiss comparison
            </button>
          </div>
        )}

        {hasErrors && (
          <div className="space-y-3">
            <div className="bg-red-900/30 border border-red-600 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-lg font-semibold text-red-400">
                  {compileResult.errors.length} Error{compileResult.errors.length > 1 ? 's' : ''} Found
                </h3>
              </div>
            </div>

            {compileResult.errors.map((error, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border-l-4 ${
                  error.type === 'Syntax'
                    ? 'bg-orange-900/20 border-orange-500'
                    : error.type === 'Semantic'
                    ? 'bg-yellow-900/20 border-yellow-500'
                    : error.type === 'Lexical'
                    ? 'bg-purple-900/20 border-purple-500'
                    : error.type === 'Runtime'
                    ? 'bg-pink-900/20 border-pink-500'
                    : 'bg-red-900/20 border-red-500'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className={`text-xs font-medium px-2 py-1 rounded ${
                    error.type === 'Syntax'
                      ? 'bg-orange-600 text-white'
                      : error.type === 'Semantic'
                      ? 'bg-yellow-600 text-white'
                      : error.type === 'Lexical'
                      ? 'bg-purple-600 text-white'
                      : error.type === 'Runtime'
                      ? 'bg-pink-600 text-white'
                      : 'bg-red-600 text-white'
                  }`}>
                    {error.type}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm text-gray-300">
                      {error.line > 0 && <span className="text-gray-500">Line {error.line}: </span>}
                      {error.message}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400">
                Click <span className="text-purple-400 font-medium">"Fix with AI"</span> to automatically correct these errors.
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Note: Requires GEMINI_API_KEY to be configured.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Language Info */}
      <div className="p-4 border-t border-gray-700 bg-gray-800/50">
        <h4 className="text-xs font-semibold text-gray-400 mb-2">Supported Mini-C Features:</h4>
        <div className="flex flex-wrap gap-2">
          {['int', 'if', 'printf("%d")', '+', '-', '*', '/', '<', '>', '==', '!='].map((feature) => (
            <span key={feature} className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded">
              {feature}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default OutputPanel;