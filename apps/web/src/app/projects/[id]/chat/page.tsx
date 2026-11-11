'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function ChatPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [messages, setMessages] = useState<{role: string, content: string, sources?: string[]}[]>([
    { role: 'assistant', content: 'Hello! I am grounded on this repository. Ask me anything about the architecture or code.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if(!input.trim()) return;
    
    const userMessage = input;
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setLoading(true);

    const token = localStorage.getItem('token');
    if (!token) return router.push('/login');

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}/chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: userMessage })
      });
      
      const data = await res.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.response,
        sources: data.sources 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to the AI server.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa] p-8 flex justify-center font-sans text-gray-800">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-200 w-full max-w-3xl flex flex-col h-[80vh]">
        <header className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-medium text-gray-900">AI Assistant</h1>
          <button onClick={() => router.push(`/projects/${params.id}`)} className="text-sm text-gray-500 hover:text-gray-900">
            ← Back to Project
          </button>
        </header>

        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
          {messages.map((m, i) => (
            <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`p-4 rounded-2xl max-w-[85%] ${m.role === 'user' ? 'bg-gray-900 text-white rounded-br-sm' : 'bg-gray-100 text-gray-800 rounded-bl-sm'}`}>
                <div className="whitespace-pre-wrap">{m.content}</div>
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
                    <span className="font-semibold">Sources:</span> {m.sources.join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex items-start">
              <div className="p-4 rounded-2xl bg-gray-100 text-gray-500 rounded-bl-sm animate-pulse">
                Thinking...
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSend} className="flex space-x-2 pt-2 border-t border-gray-100">
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400 bg-gray-50"
            placeholder="Ask about the codebase..."
          />
          <button 
            disabled={loading || !input.trim()} 
            className="px-6 py-3 bg-yellow-400 text-gray-900 font-medium rounded-xl hover:bg-yellow-500 transition disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
