import React, { useEffect, useState } from 'react';
import './NotFound.css';

const NotFound = () => {
  const [countdown, setCountdown] = useState(5);
  
  useEffect(() => {
    // Countdown timer
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      // Redirect to home page when countdown reaches 0
      window.location.href = '/';
    }
  }, [countdown]);
  
  return (
    <div className="not-found-container">
      <div className="not-found-content">
        <div className="not-found-code">404</div>
        <h1 className="not-found-title">Page Not Found</h1>
        <p className="not-found-message">
          Oops! The page you are looking for doesn't exist or has been moved.
        </p>
        <div className="not-found-redirect">
          Redirecting to home page in <span className="countdown">{countdown}</span> seconds...
        </div>
        <a href="/" className="not-found-button">
          Go Home Now
        </a>
      </div>
      
      {/* Animated background elements */}
      <div className="animated-background">
        {Array.from({ length: 20 }).map((_, index) => (
          <div 
            key={index} 
            className="floating-particle"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDuration: `${Math.random() * 10 + 10}s`,
              animationDelay: `${Math.random() * 5}s`,
              width: `${Math.random() * 20 + 5}px`,
              height: `${Math.random() * 20 + 5}px`,
              opacity: Math.random() * 0.5 + 0.1
            }}
          ></div>
        ))}
      </div>
    </div>
  );
};

export default NotFound;
