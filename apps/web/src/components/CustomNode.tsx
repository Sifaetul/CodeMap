import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Box, Code2, Folder, FileCode2 } from 'lucide-react';

const CustomNode = ({ data, selected }: any) => {
  const isFolder = data.type === 'folder';
  const isFile = data.type === 'file';
  const isClass = data.type === 'class';
  
  let gradient = 'from-purple-600 to-pink-500';
  let shadow = 'shadow-[0_0_15px_rgba(216,180,254,0.3)]';
  let Icon = Code2;
  
  if (isFolder) {
    gradient = 'from-yellow-600 to-amber-500';
    shadow = 'shadow-[0_0_15px_rgba(251,191,36,0.3)]';
    Icon = Folder;
  } else if (isFile) {
    gradient = 'from-emerald-600 to-teal-500';
    shadow = 'shadow-[0_0_15px_rgba(52,211,153,0.3)]';
    Icon = FileCode2;
  } else if (isClass) {
    gradient = 'from-blue-600 to-cyan-400';
    shadow = 'shadow-[0_0_15px_rgba(56,189,248,0.3)]';
    Icon = Box;
  }

  return (
    <div className={`relative px-4 py-3 rounded-xl bg-gray-900 border border-gray-700 transition-all duration-300 transform hover:scale-105 ${selected ? 'ring-2 ring-cyan-400 ' + shadow : 'hover:border-gray-500'} backdrop-blur-md bg-opacity-90 min-w-[200px]`}>
      
      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-3 h-3 bg-gray-800 border-2 border-gray-400 rounded-full" 
      />

      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-gradient-to-br ${gradient} text-white shadow-lg`}>
          <Icon size={16} />
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] uppercase font-bold tracking-wider text-gray-400">
            {data.type}
          </span>
          <span className="text-sm font-semibold text-gray-100 truncate w-[140px]" title={data.name}>
            {data.name}
          </span>
        </div>
      </div>

      <div className="absolute top-2 right-2 flex space-x-1">
        {!isFolder && !isFile && <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></div>}
      </div>

      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-3 h-3 bg-gray-800 border-2 border-gray-400 rounded-full" 
      />
    </div>
  );
};

export default memo(CustomNode);
