'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      
      localStorage.setItem('token', data.access_token);
      router.push('/projects');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f8f9fa] to-[#fff4cc] flex items-center justify-center p-4">
      <div className="bg-white/80 backdrop-blur-md rounded-3xl p-8 shadow-sm border border-white/50 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-block text-xl font-semibold tracking-tight text-gray-900 border border-gray-300 rounded-full px-4 py-1 mb-4">
            CodeAtlas
          </div>
          <h1 className="text-3xl font-light text-gray-900">Welcome Back</h1>
          <p className="text-gray-500 mt-2 text-sm">Sign in to your account</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-xl text-sm text-center border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-2xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400 bg-white/50" 
              placeholder="you@example.com"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-2xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400 bg-white/50" 
              placeholder="••••••••"
              required 
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-3 bg-gray-900 text-white rounded-2xl font-medium hover:bg-gray-800 transition disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          Don't have an account? <a href="/register" className="text-gray-900 font-medium hover:underline">Register</a>
        </p>
      </div>
    </div>
  );
}
