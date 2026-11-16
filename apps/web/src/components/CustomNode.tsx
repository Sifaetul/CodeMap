import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Box, Code2, Folder, FileCode2, Layers, AlertTriangle, ShieldCheck } from 'lucide-react';

const CustomNode = ({ data, selected }: any) => {
  const isFolder = data.type === 'folder';
  const isFile = data.type === 'file';
  const isModule = data.type === 'module';
  const isClass = data.type === 'class';
  
  let gradient = 'from-purple-600 to-pink-500';
  let badgeColor = 'bg-purple-500/20 text-purple-300 border-purple-500/30';
  let Icon = Code2;
  
  if (isFolder) {
    gradient = 'from-amber-600 to-yellow-500';
    badgeColor = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    Icon = Folder;
  } else if (isFile) {
    gradient = 'from-emerald-600 to-teal-500';
    badgeColor = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    Icon = FileCode2;
  } else if (isModule) {
    gradient = 'from-indigo-600 to-blue-500';
    badgeColor = 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
    Icon = Layers;
  } else if (isClass) {
    gradient = 'from-cyan-600 to-blue-500';
    badgeColor = 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
    Icon = Box;
  }

  const isHighCore = data.pagerank !== undefined && data.pagerank >= 0.6;
  const isUnstable = data.instability !== undefined && data.instability >= 0.7;

  return (
    <div 
      className={`relative px-4 py-3 rounded-2xl bg-slate-900/90 border transition-all duration-200 backdrop-blur-md min-w-[210px] ${
        selected 
          ? 'border-cyan-400 ring-2 ring-cyan-400/30 shadow-lg shadow-cyan-500/20' 
          : 'border-slate-800 hover:border-slate-700 hover:bg-slate-900'
      }`}
      style={{ willChange: 'transform' }}
    >
      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-2.5 h-2.5 bg-slate-800 border-2 border-slate-500 rounded-full" 
      />

      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-xl bg-gradient-to-br ${gradient} text-white shadow-md flex-shrink-0`}>
          <Icon size={16} />
        </div>
        <div className="flex flex-col min-w-0 flex-1">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className={`text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded border ${badgeColor}`}>
              {data.type}
            </span>
            {isHighCore && (
              <span className="text-[9px] font-bold px-1 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center gap-0.5" title="Core High-Centrality Component">
                <ShieldCheck size={9} /> Core
              </span>
            )}
            {isUnstable && (
              <span className="text-[9px] font-bold px-1 py-0.2 rounded bg-amber-950 text-amber-400 border border-amber-800 flex items-center gap-0.5" title="High Instability / High Outbound Coupling">
                <AlertTriangle size={9} /> Unstable
              </span>
            )}
          </div>
          <span className="text-sm font-semibold text-slate-100 truncate block" title={data.name}>
            {data.name}
          </span>
        </div>
      </div>

      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-2.5 h-2.5 bg-slate-800 border-2 border-slate-500 rounded-full" 
      />
    </div>
  );
};

export default memo(CustomNode);
