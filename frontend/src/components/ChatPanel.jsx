import { useState } from 'react';

const SAMPLE_PROMPTS = [
  "Create a program that declares two integers x and y, sets them to 10 and 20, and prints their sum",
  "Write code that checks if a number is greater than 50 and prints it",
  "Create a program that multiplies two numbers and prints the product",
  "Write Mini-C code that calculates the average of three numbers",
];

function ChatPanel({ onCodeGenerated, isLoading }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [generating, setGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || generating) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    
    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setGenerating(true);

    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userMessage }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Extract error message from response
        const errorMessage = data.detail || 'Failed to generate code';
        throw new Error(errorMessage);
      }
      
      // Add AI response to chat
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Generated code has been added to the editor.',
        isError: false
      }]);
      
      // Send generated code to parent
      onCodeGenerated(data.code);
    } catch (error) {
      // Add error message to chat
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: error.message,
        isError: true
      }]);
    } finally {
      setGenerating(false);
    }
  };

  const handleSamplePrompt = (prompt) => {
    setInputValue(prompt);
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 border-r border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">AI Code Generator</h2>
        <p className="text-sm text-gray-400 mt-1">Describe what code you want to generate</p>
      </div>

      {/* Sample Prompts */}
      <div className="p-3 border-b border-gray-700">
        <p className="text-xs text-gray-500 mb-2">Sample prompts:</p>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_PROMPTS.map((prompt, index) => (
            <button
              key={index}
              onClick={() => handleSamplePrompt(prompt)}
              className="text-xs px-2 py-1 bg-gray-800 text-gray-300 rounded hover:bg-gray-700 transition-colors text-left"
              title={prompt}
            >
              {prompt.length > 30 ? prompt.substring(0, 30) + '...' : prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-gray-500 text-sm text-center mt-8">
            <p>Start by describing what Mini-C code you want to generate.</p>
            <p className="mt-2 text-xs text-gray-600">
              Note: Requires GEMINI_API_KEY to be set in backend/.env
            </p>
          </div>
        )}
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white ml-4'
                : msg.isError
                ? 'bg-red-900/50 text-red-200 mr-4 border border-red-700'
                : 'bg-gray-800 text-gray-200 mr-4'
            }`}
          >
            <p className={`text-xs mb-1 ${msg.isError ? 'text-red-400' : 'text-gray-400'}`}>
              {msg.role === 'user' ? 'You' : msg.isError ? 'Error' : 'AI'}
            </p>
            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}
        {generating && (
          <div className="bg-gray-800 text-gray-200 p-3 rounded-lg mr-4">
            <p className="text-xs text-gray-400 mb-1">AI</p>
            <div className="flex items-center gap-2">
              <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span className="text-sm">Generating code...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Describe the code you want..."
            className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
            disabled={generating || isLoading}
          />
          <button
            type="submit"
            disabled={generating || isLoading || !inputValue.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatPanel;