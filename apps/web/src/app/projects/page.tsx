'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

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
    e.stopPropagation(); // Prevent card click
    
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
        // Remove from UI immediately
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
    <div className="min-h-screen bg-[#f8f9fa] p-8 font-sans text-gray-800">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-light text-gray-900">Your Projects</h1>
          <button 
            onClick={() => router.push('/projects/new')}
            className="px-6 py-2 bg-yellow-400 text-gray-900 rounded-full font-medium shadow-sm hover:bg-yellow-500 transition"
          >
            + New Project
          </button>
        </header>

        {loading ? (
          <div className="text-gray-500">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border border-gray-200 shadow-sm">
            <h2 className="text-xl font-medium text-gray-700 mb-2">No projects yet</h2>
            <p className="text-gray-500 mb-6">Get started by creating your first CodeAtlas project.</p>
            <button 
              onClick={() => router.push('/projects/new')}
              className="px-6 py-2 bg-gray-900 text-white rounded-full font-medium hover:bg-gray-800 transition"
            >
              Create Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {projects.map(p => (
              <div 
                key={p.id} 
                onClick={() => router.push(`/projects/${p.id}`)}
                className="bg-white rounded-3xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition cursor-pointer relative group"
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-medium pr-8">{p.name}</h3>
                  <button 
                    onClick={(e) => handleDelete(e, p.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full absolute top-4 right-4"
                    title="Delete Project"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
                
                <p className="text-gray-500 text-sm mb-4 line-clamp-2">{p.description || 'No description provided.'}</p>
                <div className="flex justify-between items-center text-xs text-gray-400 mt-auto pt-4 border-t border-gray-100">
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded">Active</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
