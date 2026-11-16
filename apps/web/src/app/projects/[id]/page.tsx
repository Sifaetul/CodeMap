'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Compass, ArrowLeft, GitBranch, Upload, Layers, MessageSquare, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ProjectDetailsPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [project, setProject] = useState<any>(null);
  const [githubUrl, setGithubUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchProject = async () => {
      const token = localStorage.getItem('token');
      if (!token) return router.push('/login');
      
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) setProject(await res.json());
        else router.push('/projects');
      } catch (err) {
        console.error(err);
      }
    };
    fetchProject();
  }, [params.id, router]);

  const handleGithubImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}/repositories/github`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ url: githubUrl })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Import failed');

      router.push(`/projects/${params.id}/architecture`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (file: File) => {
    if (!file.name.endsWith('.zip')) {
      setError('Only ZIP files are supported');
      return;
    }

    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}/repositories/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      setUploadedFile(file.name);
      router.push(`/projects/${params.id}/architecture`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleZipUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  if (!project) {
    return (
      <div className="min-h-screen bg-[#090d16] flex items-center justify-center text-slate-400">
        Loading project details...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col justify-between">
      {/* Header */}
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
            <ArrowLeft size={16} /> All Projects
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-10 w-full space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">{project.name}</h1>
            <p className="text-sm text-slate-400 mt-1">{project.description || 'No description provided.'}</p>
          </div>
          <div className="flex gap-3">
            <Link 
              href={`/projects/${params.id}/architecture`} 
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 text-white rounded-xl text-sm font-medium transition shadow-lg shadow-cyan-500/20"
            >
              <Layers size={16} /> Architecture Map
            </Link>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-red-400 text-sm">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* Ingestion Cards */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 backdrop-blur-md">
          <h2 className="text-xl font-bold text-white mb-2">Ingest Codebase</h2>
          <p className="text-sm text-slate-400 mb-8">Import your source code via GitHub clone or ZIP upload to run polyglot AST analysis and graph generation.</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* GitHub Ingestion */}
            <form onSubmit={handleGithubImport} className="space-y-4 flex flex-col justify-between p-6 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div>
                <div className="flex items-center gap-2 text-slate-200 font-semibold mb-2">
                  <GitBranch size={18} className="text-cyan-400" /> Import from GitHub
                </div>
                <p className="text-xs text-slate-400 mb-4">Shallow clones the repository securely to generate call trees and identify architectural smells.</p>
                <input 
                  type="text" 
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/username/repository"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 text-sm"
                  required 
                  disabled={loading}
                />
              </div>
              <button 
                type="submit"
                disabled={loading} 
                className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm rounded-xl transition disabled:opacity-50 mt-2"
              >
                {loading ? 'Cloning & Analyzing...' : 'Import & Run Analysis'}
              </button>
            </form>

            {/* ZIP Upload Ingestion */}
            <div className="space-y-4 flex flex-col justify-between p-6 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <div>
                <div className="flex items-center gap-2 text-slate-200 font-semibold mb-2">
                  <Upload size={18} className="text-indigo-400" /> Upload ZIP Archive
                </div>
                <p className="text-xs text-slate-400 mb-4">Upload a compressed project folder directly. Sanitized with path-traversal guards.</p>
                
                {uploadedFile ? (
                  <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/50 text-center">
                    <CheckCircle2 size={24} className="text-emerald-400 mx-auto mb-1" />
                    <p className="text-xs font-semibold text-emerald-300">Uploaded Successfully</p>
                    <p className="text-[11px] text-emerald-400/80 truncate mt-0.5">{uploadedFile}</p>
                  </div>
                ) : (
                  <div 
                    className={`border-2 border-dashed rounded-xl p-6 text-center transition cursor-pointer flex flex-col items-center justify-center ${
                      isDragging ? 'border-cyan-400 bg-cyan-950/20' : 'border-slate-800 hover:border-slate-700 hover:bg-slate-900/50'
                    }`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <Upload size={24} className="text-slate-500 mb-2" />
                    <p className="text-xs font-medium text-slate-300">
                      {loading ? 'Extracting & Parsing...' : isDragging ? 'Drop ZIP archive here' : 'Click to select or drag & drop ZIP'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-1">Maximum 50MB</p>
                    
                    <input 
                      type="file" 
                      accept=".zip" 
                      ref={fileInputRef}
                      onChange={handleZipUpload}
                      className="hidden"
                      disabled={loading}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500">
        CodeAtlas Architecture Platform
      </footer>
    </div>
  );
}
