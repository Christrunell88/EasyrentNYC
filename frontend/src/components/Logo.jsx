import React from 'react';

const Logo = ({ className = "", variant = "full", size = "default" }) => {
  const sizeClasses = {
    small: "h-8",
    default: "h-10",
    large: "h-14",
    xlarge: "h-20"
  };

  const heightClass = sizeClasses[size] || sizeClasses.default;

  // Icon only variant
  if (variant === "icon") {
    return (
      <svg 
        className={`${heightClass} w-auto ${className}`}
        viewBox="0 0 100 100" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Modern building silhouette with skyline */}
        <defs>
          <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{stopColor: '#f59e0b', stopOpacity: 1}} />
            <stop offset="100%" style={{stopColor: '#d97706', stopOpacity: 1}} />
          </linearGradient>
        </defs>
        
        {/* Main building */}
        <rect x="35" y="20" width="30" height="60" fill="url(#logoGradient)" rx="2"/>
        
        {/* Windows pattern */}
        <g opacity="0.3">
          <rect x="40" y="28" width="6" height="6" fill="white" rx="1"/>
          <rect x="40" y="38" width="6" height="6" fill="white" rx="1"/>
          <rect x="40" y="48" width="6" height="6" fill="white" rx="1"/>
          <rect x="40" y="58" width="6" height="6" fill="white" rx="1"/>
          
          <rect x="54" y="28" width="6" height="6" fill="white" rx="1"/>
          <rect x="54" y="38" width="6" height="6" fill="white" rx="1"/>
          <rect x="54" y="48" width="6" height="6" fill="white" rx="1"/>
          <rect x="54" y="58" width="6" height="6" fill="white" rx="1"/>
        </g>
        
        {/* Accent buildings (skyline) */}
        <rect x="20" y="45" width="12" height="35" fill="url(#logoGradient)" opacity="0.7" rx="1"/>
        <rect x="68" y="35" width="12" height="45" fill="url(#logoGradient)" opacity="0.7" rx="1"/>
        
        {/* Base line */}
        <rect x="15" y="80" width="70" height="3" fill="url(#logoGradient)"/>
        
        {/* "No Fee" badge */}
        <circle cx="75" cy="30" r="12" fill="#ef4444"/>
        <text x="75" y="33" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">NO</text>
        <text x="75" y="40" textAnchor="middle" fill="white" fontSize="6" fontWeight="bold">FEE</text>
      </svg>
    );
  }

  // Full logo with text
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg 
        className={heightClass}
        viewBox="0 0 100 100" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{stopColor: '#f59e0b', stopOpacity: 1}} />
            <stop offset="100%" style={{stopColor: '#d97706', stopOpacity: 1}} />
          </linearGradient>
        </defs>
        
        {/* Main building */}
        <rect x="35" y="20" width="30" height="60" fill="url(#logoGradient)" rx="2"/>
        
        {/* Windows pattern */}
        <g opacity="0.3">
          <rect x="40" y="28" width="6" height="6" fill="white" rx="1"/>
          <rect x="40" y="38" width="6" height="6" fill="white" rx="1"/>
          <rect x="40" y="48" width="6" height="6" fill="white" rx="1"/>
          <rect x="40" y="58" width="6" height="6" fill="white" rx="1"/>
          
          <rect x="54" y="28" width="6" height="6" fill="white" rx="1"/>
          <rect x="54" y="38" width="6" height="6" fill="white" rx="1"/>
          <rect x="54" y="48" width="6" height="6" fill="white" rx="1"/>
          <rect x="54" y="58" width="6" height="6" fill="white" rx="1"/>
        </g>
        
        {/* Accent buildings */}
        <rect x="20" y="45" width="12" height="35" fill="url(#logoGradient)" opacity="0.7" rx="1"/>
        <rect x="68" y="35" width="12" height="45" fill="url(#logoGradient)" opacity="0.7" rx="1"/>
        
        {/* Base */}
        <rect x="15" y="80" width="70" height="3" fill="url(#logoGradient)"/>
        
        {/* Badge */}
        <circle cx="75" cy="30" r="12" fill="#ef4444"/>
        <text x="75" y="33" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">NO</text>
        <text x="75" y="40" textAnchor="middle" fill="white" fontSize="6" fontWeight="bold">FEE</text>
      </svg>
      
      <div className="flex flex-col">
        <span className="text-xl font-bold warm-gradient-text tracking-tight leading-none">
          NoFeesApts
        </span>
        <span className="text-xs text-amber-500 font-semibold tracking-wider">
          .com
        </span>
      </div>
    </div>
  );
};

export default Logo;
