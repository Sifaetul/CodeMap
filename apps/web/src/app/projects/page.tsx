'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Compass, Plus, Trash2, FolderGit2, ArrowRight, Clock, Activity } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export default function ProjectsDashboard() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchProjects = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      } else {
        router.push('/login');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [router]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project? This will remove all associated repositories and analysis data.')) {
      return;
    }

    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        setProjects(projects.filter(p => p.id !== id));
      } else {
        alert('Failed to delete project');
      }
    } catch (err) {
      console.error(err);
      alert('Error deleting project');
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
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
          <button 
            onClick={() => router.push('/projects/new')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-lg font-medium text-sm transition shadow-lg shadow-cyan-500/20"
          >
            <Plus size={16} /> New Project
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-10 w-full space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Your Projects</h1>
          <p className="text-sm text-slate-400 mt-1">Select a codebase project to view its architecture graph or run analysis.</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-44 rounded-2xl bg-slate-900 border border-slate-800/80"></div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-2xl p-16 text-center border border-slate-800 bg-slate-900/40 backdrop-blur-sm">
            <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center mx-auto mb-4 text-slate-400">
              <FolderGit2 size={24} />
            </div>
            <h2 className="text-lg font-medium text-slate-200 mb-2">No projects found</h2>
            <p className="text-sm text-slate-400 max-w-sm mx-auto mb-6">Create your first project to import a GitHub repository or upload a ZIP archive for analysis.</p>
            <button 
              onClick={() => router.push('/projects/new')}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 text-white text-sm font-medium rounded-xl transition"
            >
              <Plus size={16} /> Create Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {projects.map(p => (
              <div 
                key={p.id} 
                onClick={() => router.push(`/projects/${p.id}`)}
                className="group relative p-6 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-lg shadow-black/20"
              >
                <div>
                  <div className="flex justify-between items-start gap-4 mb-3">
                    <h3 className="text-lg font-semibold text-slate-100 group-hover:text-cyan-300 transition truncate">
                      {p.name}
                    </h3>
                    <button 
                      onClick={(e) => handleDelete(e, p.id)}
                      className="opacity-0 group-hover:opacity-100 transition p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-950/40 rounded-lg"
                      title="Delete Project"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <p className="text-slate-400 text-xs line-clamp-2 leading-relaxed">
                    {p.description || 'No description provided.'}
                  </p>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 mt-6 pt-4 border-t border-slate-800/80">
                  <span className="flex items-center gap-1.5">
                    <Clock size={12} /> {new Date(p.created_at).toLocaleDateString()}
                  </span>
                  <span className="inline-flex items-center gap-1 text-cyan-400 font-medium group-hover:translate-x-0.5 transition-transform">
                    View <ArrowRight size={12} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
