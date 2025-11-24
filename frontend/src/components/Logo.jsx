import React from 'react';

const Logo = ({ className = "", size = "default" }) => {
  const sizeClasses = {
    small: "text-lg",
    default: "text-2xl",
    large: "text-3xl",
    xlarge: "text-4xl"
  };

  const textSize = sizeClasses[size] || sizeClasses.default;

  return (
    <div className={`relative inline-flex items-baseline ${className}`}>
      {/* Main logo text with elegant styling */}
      <div className="relative">
        {/* "No" in elegant serif-style */}
        <span 
          className={`${textSize} font-light tracking-tight`}
          style={{
            fontFamily: "'Playfair Display', 'Georgia', serif",
            background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            textShadow: '0 0 30px rgba(251, 191, 36, 0.3)',
            letterSpacing: '-0.02em'
          }}
        >
          No
        </span>
        
        {/* "Fees" with emphasis */}
        <span 
          className={`${textSize} font-bold italic`}
          style={{
            fontFamily: "'Playfair Display', 'Georgia', serif",
            background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            textShadow: '0 0 30px rgba(251, 191, 36, 0.4)',
            letterSpacing: '-0.01em'
          }}
        >
          Fees
        </span>
        
        {/* "Apts" in sleek modern style */}
        <span 
          className={`${textSize} font-semibold`}
          style={{
            fontFamily: "'Montserrat', 'Helvetica', sans-serif",
            background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            textShadow: '0 0 30px rgba(251, 191, 36, 0.3)',
            letterSpacing: '0.05em'
          }}
        >
          Apts
        </span>
        
        {/* ".com" as elegant suffix */}
        <span 
          className="text-xs font-light ml-0.5 align-top"
          style={{
            fontFamily: "'Montserrat', 'Helvetica', sans-serif",
            color: '#f59e0b',
            letterSpacing: '0.1em',
            opacity: 0.9
          }}
        >
          .com
        </span>
      </div>
      
      {/* Subtle underline accent */}
      <div 
        className="absolute -bottom-1 left-0 h-0.5 rounded-full"
        style={{
          width: '100%',
          background: 'linear-gradient(90deg, transparent 0%, #f59e0b 20%, #d97706 80%, transparent 100%)',
          opacity: 0.4
        }}
      />
    </div>
  );
};

export default Logo;
