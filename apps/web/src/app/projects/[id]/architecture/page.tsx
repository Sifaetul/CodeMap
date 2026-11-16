'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import ReactFlow, { Background, Controls, MiniMap, useNodesState, useEdgesState, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity, Code, GitMerge, FileText, ArrowLeft, Terminal, Cpu,
  Send, Sparkles, X, Copy, Check, ShieldAlert,
  SlidersHorizontal, RefreshCw, Layers, ShieldCheck, AlertTriangle
} from 'lucide-react';
import CustomNode from '@/components/CustomNode';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  dagreGraph.setGraph({ rankdir: direction, ranksep: 100, nodesep: 70 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 220, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 220 / 2,
        y: nodeWithPosition.y - 80 / 2,
      },
    };
  });

  return { nodes: newNodes, edges };
};

export default function ArchitecturePage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [rawNodes, setRawNodes] = useState<any[]>([]);
  const [rawEdges, setRawEdges] = useState<any[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [entityDetails, setEntityDetails] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'logic' | 'findings'>('overview');
  const [findings, setFindings] = useState<any[]>([]);
  const [copiedCode, setCopiedCode] = useState(false);
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR'>('TB');
  const [filterType, setFilterType] = useState<string>('all');
  
  // Chat state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<{role: 'user'|'ai', text: string}[]>([
    { role: 'ai', text: 'Hello! I am CodeAtlas Architecture Intelligence. Ask me anything about this codebase architecture, its call graph, or stability metrics.' }
  ]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Restore Chat History on Mount
  useEffect(() => {
    const fetchHistory = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}/chat/messages`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const history = await res.json();
          if (history.length > 0) {
            setChatMessages(history.map((m: any) => ({
              role: m.role === 'user' ? 'user' : 'ai',
              text: m.content
            })));
          }
        }
      } catch (err) {
        console.error('Failed to load chat history', err);
      }
    };
    fetchHistory();
  }, [params.id]);

  // Fetch Findings on Mount
  useEffect(() => {
    const fetchFindings = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/analysis/projects/${params.id}/findings`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          setFindings(await res.json());
        }
      } catch (err) {
        console.error('Failed to load findings', err);
      }
    };
    fetchFindings();
  }, [params.id]);

  const sendMessage = async () => {
    if (!currentMessage.trim()) return;
    const newMsg = currentMessage;
    setCurrentMessage('');
    setChatMessages(prev => [...prev, { role: 'user', text: newMsg }]);
    setIsTyping(true);
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ message: newMsg, context_entity_id: selectedNodeId })
      });
      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [...prev, { role: 'ai', text: data.reply }]);
      } else {
        setChatMessages(prev => [...prev, { role: 'ai', text: 'Sorry, unable to contact architecture AI backend.' }]);
      }
    } catch(e) {
      setChatMessages(prev => [...prev, { role: 'ai', text: 'Network connection error while contacting AI core.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

  const applyFilterAndLayout = useCallback((rawN: any[], rawE: any[], dir: 'TB' | 'LR', filter: string) => {
    let filteredNodes = rawN;
    if (filter !== 'all') {
      filteredNodes = rawN.filter(n => {
        const typeStr = (n.data?.type || '').toLowerCase();
        return typeStr === filter.toLowerCase();
      });
    }

    const visibleNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = rawE.filter(e => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target));

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(filteredNodes, filteredEdges, dir);
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [setNodes, setEdges]);

  useEffect(() => {
    const fetchGraph = async () => {
      const token = localStorage.getItem('token');
      if (!token) return router.push('/login');
      
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}/graph`, {
          headers: { 'Authorization': `Bearer ${token}` }, cache: 'no-store'
        });
        
        if (res.ok) {
          const data = await res.json();
          
          const styledNodes = data.nodes.map((n: any) => {
            const labelParts = (n.data?.label || '').split(':');
            const nodeType = labelParts.length > 1 ? labelParts[0].trim() : (n.type || 'entity');
            const nodeName = labelParts.length > 1 ? labelParts.slice(1).join(':').trim() : (n.data?.name || n.id);

            return {
              ...n,
              type: 'custom',
              data: {
                ...n.data,
                type: nodeType,
                name: nodeName
              }
            };
          });
          
          // Performance-optimized edges (no expensive multi-pass drop-shadows)
          const styledEdges = data.edges.map((e: any) => {
            const isCall = e.type === 'call';
            const isDep = e.type === 'dependency';
            return {
              ...e,
              type: 'smoothstep',
              animated: isCall || isDep,
              markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 14,
                height: 14,
                color: isCall ? '#06b6d4' : (isDep ? '#f59e0b' : '#64748b'),
              },
              style: isCall ? {
                strokeWidth: 2.5,
                stroke: '#06b6d4',
                opacity: 0.9,
              } : (isDep ? {
                strokeWidth: 2,
                stroke: '#f59e0b',
                strokeDasharray: '4,4',
                opacity: 0.85,
              } : {
                strokeWidth: 1.5,
                stroke: '#475569',
                strokeDasharray: '6,6',
                opacity: 0.6,
              }),
            };
          });

          setRawNodes(styledNodes);
          setRawEdges(styledEdges);
          applyFilterAndLayout(styledNodes, styledEdges, layoutDirection, filterType);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, [params.id, router, applyFilterAndLayout, layoutDirection, filterType]);

  const handleFilterChange = (newFilter: string) => {
    setFilterType(newFilter);
    applyFilterAndLayout(rawNodes, rawEdges, layoutDirection, newFilter);
  };

  const handleDirectionToggle = () => {
    const nextDir = layoutDirection === 'TB' ? 'LR' : 'TB';
    setLayoutDirection(nextDir);
    applyFilterAndLayout(rawNodes, rawEdges, nextDir, filterType);
  };

  const onNodeClick = useCallback(async (event: any, node: any) => {
    setSelectedNodeId(node.id);
    setEntityDetails(null);
    setActiveTab('overview');
    
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${params.id}/entities/${node.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setEntityDetails(await res.json());
      }
    } catch(e) {
      console.error(e);
    }
  }, [params.id]);

  const copyCodeToClipboard = () => {
    if (entityDetails?.source_code) {
      navigator.clipboard.writeText(entityDetails.source_code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="h-screen bg-[#090d16] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-cyan-400 font-mono tracking-widest text-sm uppercase">Loading Architecture Map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#090d16] flex flex-col font-sans text-slate-100 overflow-hidden relative selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <header className="px-6 py-3.5 border-b border-slate-800 bg-[#090d16]/90 backdrop-blur-md z-20 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push(`/projects/${params.id}`)}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 transition"
          >
            <ArrowLeft size={14} /> Back
          </button>
          <div className="h-4 w-px bg-slate-800"></div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-lg text-white shadow-md shadow-cyan-500/20">
              <Cpu size={16} />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                Architecture Graph
                <span className="text-[10px] font-mono font-normal px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {nodes.length} nodes • {edges.length} edges
                </span>
              </h1>
            </div>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-2">
          {/* Filter Pills */}
          <div className="flex items-center p-1 bg-slate-900/90 rounded-xl border border-slate-800 text-xs">
            {['all', 'module', 'class', 'function', 'file'].map(f => (
              <button
                key={f}
                onClick={() => handleFilterChange(f)}
                className={`px-2.5 py-1 rounded-lg capitalize transition-all ${
                  filterType === f 
                    ? 'bg-cyan-500 text-slate-950 font-semibold shadow-sm' 
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Direction Toggle */}
          <button
            onClick={handleDirectionToggle}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition"
            title="Toggle Layout Direction (Top-Bottom / Left-Right)"
          >
            <RefreshCw size={13} /> {layoutDirection === 'TB' ? 'Vertical' : 'Horizontal'}
          </button>

          {/* Findings Quick Button */}
          {findings.length > 0 && (
            <button
              onClick={() => {
                if (!selectedNodeId) setSelectedNodeId('findings-global');
                setActiveTab('findings');
              }}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-300 hover:bg-amber-900/40 transition font-medium"
            >
              <ShieldAlert size={14} /> {findings.length} Smells
            </button>
          )}
        </div>
      </header>

      {/* Main Canvas & Drawers */}
      <div className="flex-1 flex overflow-hidden relative z-10">
        <div className={`flex-1 relative transition-all duration-300 ease-out ${selectedNodeId ? 'w-2/3 pr-[33%]' : 'w-full'}`}>
          <ReactFlow
            proOptions={{ hideAttribution: true }}
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            className="bg-transparent"
          >
            <Background color="#1e293b" gap={24} size={1} />
            <Controls className="bg-slate-900 border-slate-800 fill-slate-300 shadow-xl" />
            <MiniMap 
              nodeStrokeColor="#1e293b"
              nodeColor="#334155"
              maskColor="rgba(9, 13, 22, 0.7)"
              style={{ backgroundColor: '#090d16', border: '1px solid #1e293b', borderRadius: '12px' }}
            />
          </ReactFlow>
        </div>

        {/* Selected Node / Findings Side Panel */}
        <AnimatePresence>
          {selectedNodeId && (
            <motion.div 
              initial={{ x: '100%', opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 220 }}
              className="absolute right-0 top-0 w-1/3 h-full bg-slate-900/95 backdrop-blur-2xl border-l border-slate-800 shadow-2xl flex flex-col z-20"
            >
              {/* Drawer Header */}
              <div className="p-5 border-b border-slate-800 flex justify-between items-start">
                <div className="min-w-0 flex-1 pr-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-cyan-950 text-cyan-400 border border-cyan-800">
                      {entityDetails ? entityDetails.type : 'Component'}
                    </span>
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-white truncate" title={entityDetails?.name}>
                    {entityDetails ? entityDetails.name : 'Inspecting Component...'}
                  </h2>
                </div>
                <button 
                  onClick={() => setSelectedNodeId(null)}
                  className="text-slate-400 hover:text-white p-1.5 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 transition"
                >
                  <X size={16} />
                </button>
              </div>
              
              {/* Tabs Bar */}
              <div className="flex border-b border-slate-800 bg-slate-950/40 text-xs">
                <button 
                  onClick={() => setActiveTab('overview')}
                  className={`flex-1 py-3 font-medium transition-all flex items-center justify-center gap-1.5 ${
                    activeTab === 'overview' 
                      ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-950/20' 
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Activity size={14} /> Overview
                </button>
                <button 
                  onClick={() => setActiveTab('logic')}
                  className={`flex-1 py-3 font-medium transition-all flex items-center justify-center gap-1.5 ${
                    activeTab === 'logic' 
                      ? 'text-indigo-400 border-b-2 border-indigo-400 bg-indigo-950/20' 
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Terminal size={14} /> Source
                </button>
                <button 
                  onClick={() => setActiveTab('findings')}
                  className={`flex-1 py-3 font-medium transition-all flex items-center justify-center gap-1.5 ${
                    activeTab === 'findings' 
                      ? 'text-amber-400 border-b-2 border-amber-400 bg-amber-950/20' 
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <ShieldAlert size={14} /> Smells ({findings.length})
                </button>
              </div>

              {/* Drawer Tab Content */}
              <div className="p-5 flex-1 overflow-y-auto custom-scrollbar space-y-6">
                {!entityDetails && activeTab !== 'findings' ? (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-3">
                    <div className="w-8 h-8 border-2 border-slate-600 border-t-cyan-500 rounded-full animate-spin"></div>
                    <p className="font-mono text-xs uppercase tracking-widest text-cyan-500">Resolving AST Symbols...</p>
                  </div>
                ) : (
                  <>
                    {/* Tab 1: Overview */}
                    {activeTab === 'overview' && entityDetails && (
                      <div className="space-y-6">
                        {/* Meta Card */}
                        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-3">
                          <div className="flex items-center gap-2 text-xs text-slate-300">
                            <FileText size={14} className="text-slate-500 flex-shrink-0" />
                            <span className="font-mono text-slate-200 truncate" title={entityDetails.file_path}>
                              {entityDetails.file_path || 'No path specified'}
                            </span>
                          </div>
                          {entityDetails.start_line && (
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                              <Code size={14} className="text-slate-500" />
                              <span>Lines: <span className="text-slate-200 font-mono">{entityDetails.start_line}</span> to <span className="text-slate-200 font-mono">{entityDetails.end_line}</span></span>
                            </div>
                          )}
                          <div className="flex items-center gap-2 text-xs text-slate-400">
                            <GitMerge size={14} className="text-slate-500" />
                            <span>Kind: <span className="text-slate-200 font-mono capitalize">{entityDetails.type}</span></span>
                          </div>
                        </div>

                        {/* Direct Relationships */}
                        <div className="space-y-4">
                          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                            <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block mb-2">
                              Calls ({entityDetails.callees?.length || 0})
                            </span>
                            <ul className="text-xs space-y-1.5 text-slate-300">
                              {(!entityDetails.callees || entityDetails.callees.length === 0) ? (
                                <li className="text-slate-500 italic text-[11px]">No outgoing function calls</li>
                              ) : (
                                entityDetails.callees.map((c: any) => (
                                  <li key={c.id} className="flex items-center gap-2 font-mono">
                                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>
                                    <span className="truncate">{c.name}</span>
                                  </li>
                                ))
                              )}
                            </ul>
                          </div>

                          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block mb-2">
                              Called By ({entityDetails.callers?.length || 0})
                            </span>
                            <ul className="text-xs space-y-1.5 text-slate-300">
                              {(!entityDetails.callers || entityDetails.callers.length === 0) ? (
                                <li className="text-slate-500 italic text-[11px]">No incoming callers (entrypoint or orphan)</li>
                              ) : (
                                entityDetails.callers.map((c: any) => (
                                  <li key={c.id} className="flex items-center gap-2 font-mono">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                                    <span className="truncate">{c.name}</span>
                                  </li>
                                ))
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Tab 2: Source Code */}
                    {activeTab === 'logic' && entityDetails && (
                      <div className="h-full flex flex-col space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono text-slate-400">
                            {entityDetails.file_path ? entityDetails.file_path.split('/').pop() : 'Source'}
                          </span>
                          <button
                            onClick={copyCodeToClipboard}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition"
                          >
                            {copiedCode ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                            {copiedCode ? 'Copied' : 'Copy'}
                          </button>
                        </div>
                        
                        <div className="flex-1 bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-inner">
                          <pre className="p-4 overflow-x-auto text-xs text-slate-300 font-mono leading-relaxed h-[calc(100vh-270px)] custom-scrollbar">
                            <code>{entityDetails.source_code || "// No source code available"}</code>
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Tab 3: Architectural Findings & Smells */}
                    {activeTab === 'findings' && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                            Detected Architecture Smells
                          </h3>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                            {findings.length} findings
                          </span>
                        </div>

                        {findings.length === 0 ? (
                          <div className="p-8 text-center text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800">
                            <ShieldCheck size={28} className="mx-auto mb-2 text-emerald-400" />
                            <p className="text-sm font-medium text-slate-300">Clean Architecture</p>
                            <p className="text-xs text-slate-500 mt-1">No cyclic dependencies, orphan dead code, or god components detected.</p>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {findings.map((f, idx) => (
                              <div 
                                key={idx} 
                                className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                                  f.severity === 'WARNING' 
                                    ? 'bg-amber-950/20 border-amber-800/50 text-amber-200' 
                                    : 'bg-blue-950/20 border-blue-800/50 text-blue-200'
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-bold tracking-wider font-mono text-[10px] px-1.5 py-0.5 rounded bg-black/40">
                                    {f.type}
                                  </span>
                                  <span className="text-[10px] uppercase font-semibold opacity-75">
                                    {f.severity}
                                  </span>
                                </div>
                                <p className="text-slate-300 text-xs leading-relaxed">{f.description}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Floating Chat Button */}
        <div className="absolute bottom-6 right-6 z-30">
          <AnimatePresence>
            {!isChatOpen && (
              <motion.button
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                onClick={() => setIsChatOpen(true)}
                className="w-13 h-13 p-3.5 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all hover:scale-105"
                title="Open CodeAtlas AI Chat"
              >
                <Sparkles size={22} className="text-white" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Floating Chat Drawer */}
        <AnimatePresence>
          {isChatOpen && (
            <motion.div
              initial={{ opacity: 0, y: 30, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 30, scale: 0.95 }}
              className="absolute bottom-6 right-6 w-96 h-[520px] bg-slate-900/95 backdrop-blur-2xl border border-slate-800 rounded-2xl shadow-2xl flex flex-col z-40 overflow-hidden"
            >
              {/* Chat Header */}
              <div className="p-4 bg-slate-950/70 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg">
                    <Sparkles size={16} />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white tracking-wide">CodeAtlas Architecture AI</h3>
                    <p className="text-[10px] text-emerald-400 flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> RAG Intelligence Online
                    </p>
                  </div>
                </div>
                <button onClick={() => setIsChatOpen(false)} className="text-slate-400 hover:text-white transition">
                  <X size={16} />
                </button>
              </div>

              {/* Chat Messages Body */}
              <div className="flex-1 p-4 overflow-y-auto custom-scrollbar flex flex-col gap-3">
                {chatMessages.map((msg, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, y: 5 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    key={idx} 
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[85%] p-3 rounded-2xl text-xs leading-relaxed ${
                      msg.role === 'user' 
                        ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-tr-xs' 
                        : 'bg-slate-950/80 text-slate-200 border border-slate-800 rounded-tl-xs whitespace-pre-wrap'
                    }`}>
                      {msg.text}
                    </div>
                  </motion.div>
                ))}
                {isTyping && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                    <div className="bg-slate-950 border border-slate-800 p-3 rounded-2xl rounded-tl-xs flex gap-1 items-center">
                      <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Chat Input */}
              <div className="p-3 border-t border-slate-800 bg-slate-950/50">
                <form 
                  onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
                  className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl p-1.5 pl-3.5 focus-within:border-cyan-500/50"
                >
                  <input 
                    type="text" 
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    placeholder="Ask about architecture, callers..." 
                    className="flex-1 bg-transparent border-none outline-none text-xs text-slate-100 placeholder-slate-500"
                  />
                  <button 
                    type="submit" 
                    disabled={!currentMessage.trim() || isTyping} 
                    className="p-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 disabled:opacity-40 rounded-lg text-white transition"
                  >
                    <Send size={12} />
                  </button>
                </form>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
