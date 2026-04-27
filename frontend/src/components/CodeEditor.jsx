import { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

const DEFAULT_CODE = `// Mini-C Code Editor
// Supported: int declarations, assignments, arithmetic, printf, if statements

int x = 10;
int y = 20;
int sum;

sum = x + y;

if (sum > 15) {
    printf("%d", sum);
}

printf("%d %d", x, y);
`;

function CodeEditor({ code, onCodeChange, onCompile, isCompiling }) {
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const decorationsRef = useRef([]); // Track current decorations

  const handleEditorChange = (value) => {
    onCodeChange(value || '');
  };

  // Handle editor mount - save references
  const handleEditorMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
  };

  // Highlight lines containing "// FIXED:" comments
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current || !code) return;

    const editor = editorRef.current;
    const monaco = monacoRef.current;
    const lines = code.split('\n');
    
    // Find lines with "// FIXED:" comments
    const fixedLineNumbers = [];
    lines.forEach((line, index) => {
      if (line.includes('// FIXED:')) {
        fixedLineNumbers.push(index + 1); // Monaco uses 1-based line numbers
      }
    });

    // Create decorations for highlighted lines
    const newDecorations = fixedLineNumbers.map(lineNumber => ({
      range: new monaco.Range(lineNumber, 1, lineNumber, 1),
      options: {
        isWholeLine: true,
        className: 'fixed-line-highlight', // CSS class for the line
        glyphMarginClassName: 'fixed-line-glyph', // Glyph margin indicator
        overviewRuler: {
          color: '#a855f7', // Purple color in overview ruler
          position: monaco.editor.OverviewRulerLane.Full
        }
      }
    }));

    // Apply decorations (this replaces old ones automatically)
    decorationsRef.current = editor.deltaDecorations(
      decorationsRef.current,
      newDecorations
    );
  }, [code]); // Re-run when code changes

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Custom styles for line highlighting */}
      <style>{`
        .fixed-line-highlight {
          background-color: rgba(168, 85, 247, 0.15) !important;
          border-left: 3px solid #a855f7 !important;
        }
        .fixed-line-glyph {
          background-color: #a855f7;
          width: 4px !important;
          margin-left: 3px;
          border-radius: 2px;
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-gray-800">
        <div>
          <h2 className="text-lg font-semibold text-white">Code Editor</h2>
          <p className="text-xs text-gray-400">Mini-C Language</p>
        </div>
        <button
          onClick={onCompile}
          disabled={isCompiling}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isCompiling ? (
            <>
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              Compiling...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Compile
            </>
          )}
        </button>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          defaultLanguage="c"
          theme="vs-dark"
          value={code || DEFAULT_CODE}
          onChange={handleEditorChange}
          onMount={handleEditorMount}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            insertSpaces: true,
            wordWrap: 'on',
            lineNumbers: 'on',
            renderLineHighlight: 'all',
            selectOnLineNumbers: true,
            roundedSelection: false,
            cursorStyle: 'line',
            glyphMargin: true, // Enable glyph margin for indicators
            scrollbar: {
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10,
            },
          }}
        />
      </div>
    </div>
  );
}

export default CodeEditor;
export { DEFAULT_CODE };