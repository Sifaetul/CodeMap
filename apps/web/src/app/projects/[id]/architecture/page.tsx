'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import ReactFlow, { Background, Controls, MiniMap, useNodesState, useEdgesState, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Code, GitMerge, FileText, ArrowLeft, Terminal, Cpu, MessageSquare, Send, Sparkles, X } from 'lucide-react';
import CustomNode from '@/components/CustomNode';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  dagreGraph.setGraph({ rankdir: direction, ranksep: 100, nodesep: 80 });

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
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [entityDetails, setEntityDetails] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'logic'>('overview');
  
  // Chat state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<{role: 'user'|'ai', text: string}[]>([
    { role: 'ai', text: 'Hello! I am your CodeAtlas AI. You can ask me anything about this architecture.' }
  ]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

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
        setChatMessages(prev => [...prev, { role: 'ai', text: 'Sorry, my neural link to the backend is currently offline.' }]);
      }
    } catch(e) {
      setChatMessages(prev => [...prev, { role: 'ai', text: 'Connection error while contacting AI core.' }]);
    } finally {
      setIsTyping(false);
    }
  };


  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

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
          
          const styledNodes = data.nodes.map((n: any) => ({
            ...n,
            type: n.type === 'folder' || n.type === 'file' ? 'custom' : 'custom',
            data: {
              ...n.data,
              type: n.data.label.split(':')[0].trim(),
              name: n.data.label.split(':')[1].trim()
            }
          }));
          
          const styledEdges = data.edges.map((e: any) => {
            const isCall = e.type === 'call';
            return {
              ...e,
              type: 'smoothstep',
              animated: true,
              markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 15,
                height: 15,
                color: isCall ? '#06b6d4' : '#a855f7',
              },
              style: isCall ? {
                strokeWidth: 3,
                stroke: '#06b6d4',
                filter: 'drop-shadow(0 0 10px #06b6d4)',
                opacity: 0.9,
              } : {
                strokeWidth: 2,
                stroke: '#a855f7',
                strokeDasharray: '8,8',
                filter: 'drop-shadow(0 0 5px rgba(168, 85, 247, 0.5))',
                opacity: 0.7,
              },
            };
          });

          const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(styledNodes, styledEdges, 'TB');
          setNodes(layoutedNodes);
          setEdges(layoutedEdges);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, [params.id, router, setNodes, setEdges]);

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

  if (loading) {
    return (
      <div className="h-screen bg-[#050505] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-cyan-400 font-mono tracking-widest text-sm uppercase">Initializing Neural Link...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#050505] flex flex-col font-sans text-gray-200 overflow-hidden relative">
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none z-0"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600/20 rounded-full blur-[120px] pointer-events-none z-0"></div>

      <header className="p-5 border-b border-gray-800/60 bg-gray-950/40 backdrop-blur-md z-10 flex justify-between items-center relative shadow-md">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.4)]">
            <Cpu size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">CodeAtlas Engine</h1>
            <p className="text-gray-400 text-xs font-mono uppercase tracking-widest mt-1">Live Telemetry & Topology Matrix</p>
          </div>
        </div>
        <button 
          onClick={() => router.push(`/projects/${params.id}`)}
          className="flex items-center gap-2 text-sm font-medium text-gray-300 bg-gray-800/80 hover:bg-gray-700 hover:text-white px-4 py-2 rounded-lg transition-all border border-gray-700 shadow-sm"
        >
          <ArrowLeft size={16} /> Exit Matrix
        </button>
      </header>

      <div className="flex-1 flex overflow-hidden relative z-10">
        <div className={`flex-1 relative transition-all duration-500 ease-out ${selectedNodeId ? 'w-2/3 pr-[33%]' : 'w-full'}`}>
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
            <Background color="#1f2937" gap={20} size={1.5} />
            <Controls className="bg-gray-900 border-gray-700 fill-gray-300 shadow-xl" />
            <MiniMap 
              nodeStrokeColor="#1e293b"
              nodeColor="#334155"
              maskColor="rgba(0, 0, 0, 0.4)"
              style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
            />
          </ReactFlow>
        </div>

        <AnimatePresence>
          {selectedNodeId && (
            <motion.div 
              initial={{ x: '100%', opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="absolute right-0 top-0 w-1/3 h-full bg-gray-950/80 backdrop-blur-2xl border-l border-gray-800 shadow-[-20px_0_40px_rgba(0,0,0,0.5)] flex flex-col z-20"
            >
              <div className="p-5 border-b border-gray-800/60 flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-500/20 text-blue-400 border border-blue-500/30">
                      Entity Viewer
                    </span>
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                  </div>
                  <h2 className="text-2xl font-bold text-white break-words pr-8">
                    {entityDetails ? entityDetails.name : 'Analyzing...'}
                  </h2>
                </div>
                <button 
                  onClick={() => setSelectedNodeId(null)}
                  className="text-gray-500 hover:text-white p-2 rounded-lg bg-gray-900 border border-gray-800 transition-colors hover:bg-gray-800"
                >
                  ✕
                </button>
              </div>
              
              <div className="flex border-b border-gray-800">
                <button 
                  onClick={() => setActiveTab('overview')}
                  className={`flex-1 py-3 text-sm font-medium transition-all ${activeTab === 'overview' ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-900/10' : 'text-gray-400 hover:text-gray-200'}`}
                >
                  <Activity size={16} className="inline mr-2" /> Overview
                </button>
                <button 
                  onClick={() => setActiveTab('logic')}
                  className={`flex-1 py-3 text-sm font-medium transition-all ${activeTab === 'logic' ? 'text-purple-400 border-b-2 border-purple-400 bg-purple-900/10' : 'text-gray-400 hover:text-gray-200'}`}
                >
                  <Terminal size={16} className="inline mr-2" /> Source Code
                </button>
              </div>

              <div className="p-5 flex-1 overflow-y-auto custom-scrollbar">
                {!entityDetails ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-500 space-y-4">
                    <div className="w-8 h-8 border-2 border-gray-600 border-t-cyan-500 rounded-full animate-spin"></div>
                    <p className="font-mono text-sm uppercase tracking-widest text-cyan-500/70">Decoding matrix...</p>
                  </div>
                ) : (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    {activeTab === 'overview' && (
                      <div className="space-y-6">
                        <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800/80 shadow-inner">
                          <div className="flex items-center gap-3 text-sm text-gray-300">
                            <FileText size={16} className="text-gray-500" />
                            <span className="font-mono bg-gray-950 px-2 py-1 rounded text-xs border border-gray-800 truncate" title={entityDetails.file_path}>
                              {entityDetails.file_path}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-sm text-gray-400 mt-3">
                            <Code size={16} className="text-gray-500" />
                            <span>Lines: <span className="text-white font-mono">{entityDetails.start_line}</span> to <span className="text-white font-mono">{entityDetails.end_line}</span></span>
                          </div>
                          <div className="flex items-center gap-3 text-sm text-gray-400 mt-3">
                            <GitMerge size={16} className="text-gray-500" />
                            <span>Type: <span className="text-white font-mono capitalize">{entityDetails.type}</span></span>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full shadow-[0_0_8px_rgba(6,182,212,0.8)]"></div> Telemetry & Impact
                          </h4>
                          <div className="space-y-4">
                            <div className="bg-gradient-to-r from-blue-900/20 to-transparent p-4 rounded-xl border border-blue-900/40 border-l-2 border-l-blue-500 hover:bg-blue-900/30 transition-colors">
                              <span className="text-[10px] font-bold text-blue-400 uppercase block mb-2 tracking-wider">Depends On (Uses)</span>
                              <ul className="text-sm space-y-2 text-gray-300">
                                {entityDetails.callees.length === 0 ? <li className="text-gray-600 italic font-mono text-xs">No outgoing calls detected</li> :
                                  entityDetails.callees.map((c: any) => <li key={c.id} className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-blue-500/80"></div><span className="font-mono">{c.name}</span></li>)
                                }
                              </ul>
                            </div>
                            
                            <div className="bg-gradient-to-r from-purple-900/20 to-transparent p-4 rounded-xl border border-purple-900/40 border-l-2 border-l-purple-500 hover:bg-purple-900/30 transition-colors">
                              <span className="text-[10px] font-bold text-purple-400 uppercase block mb-2 tracking-wider">Affected By (Impact)</span>
                              <p className="text-xs text-gray-400 mb-3 leading-relaxed">Modifying this entity will affect the following dependents:</p>
                              <ul className="text-sm space-y-2 text-gray-300">
                                {entityDetails.callers.length === 0 ? <li className="text-gray-600 italic font-mono text-xs">No incoming calls detected</li> :
                                  entityDetails.callers.map((c: any) => <li key={c.id} className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-purple-500/80"></div><span className="font-mono">{c.name}</span></li>)
                                }
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {activeTab === 'logic' && (
                      <div className="h-full flex flex-col">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
                            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div> Live Source Code
                          </h4>
                          <span className="text-[10px] text-gray-500 font-mono bg-gray-900 px-2 py-0.5 rounded border border-gray-800">Read-Only</span>
                        </div>
                        
                        <div className="flex-1 bg-[#0d1117] rounded-xl overflow-hidden border border-gray-800 shadow-[inset_0_2px_15px_rgba(0,0,0,0.6)]">
                          <div className="flex items-center px-4 py-2 bg-gray-900/80 border-b border-gray-800 backdrop-blur">
                            <div className="flex space-x-2">
                              <div className="w-2.5 h-2.5 rounded-full bg-red-500/80 shadow-[0_0_5px_rgba(239,68,68,0.5)]"></div>
                              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80 shadow-[0_0_5px_rgba(234,179,8,0.5)]"></div>
                              <div className="w-2.5 h-2.5 rounded-full bg-green-500/80 shadow-[0_0_5px_rgba(34,197,94,0.5)]"></div>
                            </div>
                            <div className="mx-auto text-[10px] text-gray-500 font-mono">{entityDetails.file_path.split('/').pop()}</div>
                          </div>
                          <pre className="p-5 overflow-x-auto text-[13px] text-gray-300 font-mono leading-relaxed h-[calc(100vh-320px)] custom-scrollbar">
                            <code className="text-cyan-200">{entityDetails.source_code || "// Source code could not be loaded or analyzed"}</code>
                          </pre>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat FAB */}
        <div className="absolute bottom-6 right-6 z-30">
          <AnimatePresence>
            {!isChatOpen && (
              <motion.button
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                onClick={() => setIsChatOpen(true)}
                className="w-14 h-14 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(147,51,234,0.5)] hover:shadow-[0_0_30px_rgba(147,51,234,0.8)] transition-all"
              >
                <Sparkles size={24} className="text-white" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Floating Chat Window */}
        <AnimatePresence>
          {isChatOpen && (
            <motion.div
              initial={{ opacity: 0, y: 50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 50, scale: 0.9 }}
              className="absolute bottom-6 right-6 w-96 h-[500px] bg-gray-950/90 backdrop-blur-2xl border border-gray-800 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.8)] flex flex-col z-40 overflow-hidden"
            >
              {/* Chat Header */}
              <div className="p-4 bg-gradient-to-r from-purple-900/40 to-blue-900/40 border-b border-gray-800 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-purple-500/20 rounded-lg text-purple-400">
                    <Sparkles size={16} />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-wide">CodeAtlas AI</h3>
                    <p className="text-[10px] text-green-400 flex items-center gap-1 font-mono uppercase">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span> Online
                    </p>
                  </div>
                </div>
                <button onClick={() => setIsChatOpen(false)} className="text-gray-400 hover:text-white transition-colors">
                  <X size={18} />
                </button>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 p-4 overflow-y-auto custom-scrollbar flex flex-col gap-4">
                {chatMessages.map((msg, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, y: 5 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    key={idx} 
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-gray-800 text-gray-200 border border-gray-700 rounded-tl-sm'}`}>
                      {msg.text}
                    </div>
                  </motion.div>
                ))}
                {isTyping && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                    <div className="bg-gray-800 border border-gray-700 p-4 rounded-2xl rounded-tl-sm flex gap-1 items-center">
                      <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Chat Input */}
              <div className="p-3 border-t border-gray-800 bg-gray-900/50">
                <form 
                  onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
                  className="flex items-center gap-2 bg-gray-950 border border-gray-700 rounded-full p-1 pl-4"
                >
                  <input 
                    type="text" 
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    placeholder="Ask about this architecture..." 
                    className="flex-1 bg-transparent border-none outline-none text-sm text-gray-200 placeholder-gray-500"
                  />
                  <button type="submit" disabled={!currentMessage.trim() || isTyping} className="p-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-full text-white transition-colors">
                    <Send size={14} />
                  </button>
                </form>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>


      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.2);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.15);
          border-radius: 10px;
        }
        .react-flow__attribution { display: none !important; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
}
