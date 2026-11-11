'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

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
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) setProject(await res.json());
      else router.push('/projects');
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

      alert('Repository imported and analyzed successfully! Redirecting to Architecture Map...');
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
      alert('ZIP Repository uploaded and analyzed successfully! Redirecting to Architecture Map...');
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

  if (!project) return <div className="p-8">Loading...</div>;

  return (
    <div className="min-h-screen bg-[#f8f9fa] p-8 font-sans text-gray-800">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="flex justify-between items-center">
          <div>
            <Link href="/projects" className="text-sm text-gray-400 hover:text-gray-700 mb-2 inline-block">← Back to Projects</Link>
            <h1 className="text-3xl font-medium text-gray-900">{project.name}</h1>
            <p className="text-gray-500 mt-2">{project.description || 'No description'}</p>
          </div>
          <div className="flex space-x-4">
            <Link href={`/projects/${params.id}/architecture`} className="px-6 py-2 bg-white border border-gray-200 text-gray-900 rounded-full font-medium hover:bg-gray-50 transition">
              Architecture Map
            </Link>
            <Link href={`/projects/${params.id}/chat`} className="px-6 py-2 bg-gray-900 text-white rounded-full font-medium hover:bg-gray-800 transition shadow-sm">
              AI Chat
            </Link>
          </div>
        </header>

        <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-200">
          <h2 className="text-xl font-medium mb-6">Ingest Repository</h2>
          {error && <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-xl text-sm">{error}</div>}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <form onSubmit={handleGithubImport} className="space-y-4">
              <h3 className="font-medium text-gray-700">Import from GitHub</h3>
              <input 
                type="text" 
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                required 
                disabled={loading}
              />
              <button disabled={loading} className="w-full py-3 bg-yellow-400 text-gray-900 font-medium rounded-xl hover:bg-yellow-500 transition disabled:opacity-50">
                {loading ? 'Processing...' : 'Import & Analyze'}
              </button>
            </form>

            <div className="space-y-4">
              <h3 className="font-medium text-gray-700">Upload ZIP Archive</h3>
              
              {uploadedFile ? (
                <div className="border-2 border-green-300 bg-green-50 rounded-xl p-8 text-center flex flex-col items-center justify-center">
                  <span className="text-3xl mb-2">✅</span>
                  <p className="font-medium text-green-800">File Uploaded</p>
                  <p className="text-sm text-green-600 mt-1">{uploadedFile}</p>
                  <button 
                    onClick={() => setUploadedFile(null)}
                    className="mt-4 text-sm text-green-700 underline hover:text-green-900"
                  >
                    Upload another file
                  </button>
                </div>
              ) : (
                <div 
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer flex flex-col items-center justify-center relative overflow-hidden ${
                    isDragging ? 'border-yellow-400 bg-yellow-50' : 'border-gray-300 text-gray-500 hover:bg-gray-50 hover:border-gray-400'
                  }`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <span className="text-3xl mb-2">{isDragging ? '📥' : '📁'}</span>
                  <p className="font-medium text-gray-700">
                    {loading ? 'Uploading...' : isDragging ? 'Drop ZIP file here' : 'Click or Drag & Drop ZIP'}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">Extracts and analyzes code automatically</p>
                  
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
    </div>
  );
}
