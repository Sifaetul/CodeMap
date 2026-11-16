'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Compass, ArrowLeft, Plus } from 'lucide-react';

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const token = localStorage.getItem('token');
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name, description }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create project');
      
      router.push(`/projects/${data.id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col justify-between">
      {/* Navbar */}
      <header className="border-b border-slate-800 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Compass size={18} className="text-white" />
            </div>
            <Link href="/" className="font-semibold text-lg tracking-tight hover:opacity-90">
              Code<span className="text-cyan-400">Atlas</span>
            </Link>
          </div>
          <Link href="/projects" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 transition">
            <ArrowLeft size={16} /> Back to Projects
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-8 shadow-2xl shadow-black/40 w-full max-w-lg backdrop-blur-md">
          <h1 className="text-2xl font-bold text-white mb-2">Create New Project</h1>
          <p className="text-sm text-slate-400 mb-6">Initialize a new codebase workspace for architecture mapping and intelligence.</p>
          
          {error && (
            <div className="mb-4 p-3 bg-red-950/50 text-red-400 rounded-xl text-sm border border-red-800/60">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Project Name</label>
              <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition text-sm" 
                placeholder="e.g. CodeAtlas Core"
                required 
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Description (Optional)</label>
              <textarea 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition text-sm resize-none" 
                placeholder="A brief description of this codebase"
                rows={3}
              />
            </div>
            <div className="flex space-x-3 pt-2">
              <button 
                type="button" 
                onClick={() => router.push('/projects')}
                className="flex-1 py-3 bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded-xl font-medium text-sm transition"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                disabled={loading}
                className="flex-1 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 text-white rounded-xl font-medium text-sm transition shadow-lg shadow-cyan-500/20 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </form>
        </div>
      </main>

      <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500">
        CodeAtlas Architecture Platform
      </footer>
    </div>
  );
}
