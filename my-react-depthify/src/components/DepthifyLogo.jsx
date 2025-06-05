import React from 'react';

export default function DepthifyLogo({ size = "h-8 w-8" }) {
  return (
    <div className={`${size} relative flex items-center justify-center`}>
      {/* Background layers for depth effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-pink-500 to-purple-600 rounded-lg transform rotate-6 opacity-30"></div>
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg transform rotate-3 opacity-50"></div>
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg transform rotate-1 opacity-70"></div>
      
      {/* Main logo shape */}
      <div className="relative bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-lg shadow-xl transform transition-transform duration-300 hover:scale-110 hover:rotate-2 w-full h-full flex items-center justify-center">
        {/* 3D effect inner shadow */}
        <div className="absolute inset-1 bg-gradient-to-tl from-white/20 to-transparent rounded-md"></div>
        
        {/* Letter D with depth */}
        <div className="relative">
          {/* Shadow layers */}
          <div className="absolute text-black/20 font-bold text-lg transform translate-x-1 translate-y-1">D</div>
          <div className="absolute text-black/10 font-bold text-lg transform translate-x-2 translate-y-2">D</div>
          
          {/* Main letter */}
          <div className="relative text-white font-bold text-lg">D</div>
        </div>
      </div>
      
      {/* Floating particles for magic effect */}
      <div className="absolute -top-1 -right-1 w-1 h-1 bg-cyan-400 rounded-full animate-pulse"></div>
      <div className="absolute -bottom-1 -left-1 w-1 h-1 bg-pink-400 rounded-full animate-pulse delay-300"></div>
    </div>
  );
}