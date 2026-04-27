import { useState } from 'react';
import ChatPanel from './components/ChatPanel';
import CodeEditor, { DEFAULT_CODE } from './components/CodeEditor';
import OutputPanel from './components/OutputPanel';

function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [compileResult, setCompileResult] = useState(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Handle code generation from AI
  const handleCodeGenerated = (generatedCode) => {
    setCode(generatedCode);
    setCompileResult(null); // Reset compilation result
  };

  // Handle code changes in editor
  const handleCodeChange = (newCode) => {
    setCode(newCode);
  };

  // Handle compilation
  const handleCompile = async () => {
    setIsCompiling(true);
    try {
      const response = await fetch('http://localhost:8000/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        throw new Error('Compilation request failed');
      }

      const result = await response.json();
      setCompileResult(result);
    } catch (error) {
      setCompileResult({
        success: false,
        errors: [{ line: 0, type: 'Internal', message: error.message }],
      });
    } finally {
      setIsCompiling(false);
    }
  };

  // Handle AI fix - now receives fixed code directly from OutputPanel
  const handleFixWithAI = (fixedCode) => {
    setCode(fixedCode);
    setCompileResult(null); // Reset to allow re-compilation
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">C</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Mini-C Compiler</h1>
              <p className="text-xs text-gray-400">with AI Code Generation & Fix Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-500">
              Powered by Gemini AI
            </span>
          </div>
        </div>
      </header>

      {/* Main Content - Three Panel Layout */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chat */}
        <div className="w-80 flex-shrink-0">
          <ChatPanel 
            onCodeGenerated={handleCodeGenerated} 
            isLoading={isGenerating}
          />
        </div>

        {/* Center Panel - Code Editor */}
        <div className="flex-1 min-w-0">
          <CodeEditor
            code={code}
            onCodeChange={handleCodeChange}
            onCompile={handleCompile}
            isCompiling={isCompiling}
          />
        </div>

        {/* Right Panel - Output */}
        <div className="w-96 flex-shrink-0">
          <OutputPanel
            compileResult={compileResult}
            onFixWithAI={handleFixWithAI}
            isFixing={isFixing}
            code={code}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 px-6 py-2">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Mini-C Compiler v1.0</span>
          <span>Supports: int, if, printf("%d"), arithmetic, comparisons</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
