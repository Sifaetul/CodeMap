import Link from "next/link";
import { Compass, Sparkles, Layers, ShieldCheck, ArrowRight, GitFork } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col justify-between selection:bg-cyan-500 selection:text-black">
      {/* Navbar */}
      <header className="border-b border-slate-800/80 bg-[#090d16]/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Compass size={18} className="text-white" />
            </div>
            <span className="font-semibold text-lg tracking-tight">Code<span className="text-cyan-400">Atlas</span></span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="px-4 py-2 text-sm text-slate-300 hover:text-white transition">
              Sign In
            </Link>
            <Link href="/register" className="px-4 py-2 text-sm bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-lg font-medium transition shadow-lg shadow-cyan-500/20">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-20 flex flex-col items-center justify-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/40 border border-cyan-800/60 text-cyan-300 text-xs font-medium mb-8">
          <Sparkles size={14} /> AI-Powered Codebase Archaeology & Architecture Intelligence
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6">
          The <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">Google Maps</span> for Your Codebase
        </h1>

        <p className="text-lg md:text-xl text-slate-400 max-w-2xl font-light mb-10 leading-relaxed">
          Instantly reverse-engineer software architectures into interactive dependency graphs, detect architectural smells, and chat with your entire codebase with LLM-backed RAG.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium rounded-xl shadow-xl shadow-cyan-500/20 transition transform hover:-translate-y-0.5"
          >
            Explore Dashboard <ArrowRight size={18} />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center justify-center px-8 py-3.5 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 font-medium rounded-xl transition hover:bg-slate-800/60"
          >
            Existing Projects
          </Link>
        </div>

        {/* Feature Badges */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left w-full mt-4">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm hover:border-slate-700 transition">
            <div className="p-2.5 w-fit rounded-lg bg-cyan-500/10 text-cyan-400 mb-4">
              <Layers size={20} />
            </div>
            <h3 className="font-semibold text-slate-100 mb-2">Polyglot AST Extraction</h3>
            <p className="text-sm text-slate-400">Scans Python, TypeScript, and JavaScript codebases to build complete class, method, and module call graphs.</p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm hover:border-slate-700 transition">
            <div className="p-2.5 w-fit rounded-lg bg-indigo-500/10 text-indigo-400 mb-4">
              <ShieldCheck size={20} />
            </div>
            <h3 className="font-semibold text-slate-100 mb-2">Deep Graph Metrics</h3>
            <p className="text-sm text-slate-400">Identifies circular dependencies (Tarjan SCC), PageRank centrality bottlenecks, and dead/orphan code automatically.</p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm hover:border-slate-700 transition">
            <div className="p-2.5 w-fit rounded-lg bg-blue-500/10 text-blue-400 mb-4">
              <GitFork size={20} />
            </div>
            <h3 className="font-semibold text-slate-100 mb-2">Interactive Architecture AI</h3>
            <p className="text-sm text-slate-400">Select any node on the visual canvas and chat with real-time RAG context streamed directly into your browser.</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-8 text-center text-xs text-slate-500">
        CodeAtlas Architecture Platform • Engineered for modern software development
      </footer>
    </div>
  );
}
