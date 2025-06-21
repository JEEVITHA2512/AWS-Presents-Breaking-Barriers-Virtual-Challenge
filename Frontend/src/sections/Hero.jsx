import React from 'react';
import Lottie from 'lottie-react';
import robotAnimation from '../assets/Home_Robot.json';

const heroContainerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '4rem 2rem 2rem 2rem',
  background: 'linear-gradient(135deg, #e3f0ff 0%, #f8fbff 100%)',
  minHeight: '80vh',
  position: 'relative',
  overflow: 'hidden',
  maxWidth: '100%',
};

const heroContentStyle = {
  maxWidth: '600px',
  position: 'relative',
  zIndex: 2,
};

const heroTitleStyle = {
  fontSize: '3.5rem',
  fontWeight: '700',
  color: '#2a3a5e',
  marginBottom: '1.5rem',
  lineHeight: '1.2',
};

const heroSubtitleStyle = {
  fontSize: '1.4rem',
  color: '#4a5a7a',
  marginBottom: '2.5rem',
  lineHeight: '1.6',
};

const ctaButtonStyle = {
  display: 'inline-block',
  background: 'linear-gradient(90deg, #0078d4 0%, #005fa3 100%)',
  color: '#fff',
  padding: '1rem 2.5rem',
  borderRadius: '3rem',
  textDecoration: 'none',
  fontWeight: '600',
  fontSize: '1.1rem',
  boxShadow: '0 4px 15px rgba(0,120,212,0.25)',
  transition: 'all 0.3s ease',
};

const heroAnimationStyle = {
  width: '45%',
  height: 'auto',
  position: 'relative',
  zIndex: 1,
};

const highlightTextStyle = {
  color: '#0078d4',
};

const gradientOverlayStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '500px',
  height: '500px',
  background: 'radial-gradient(circle, rgba(224,242,255,0.5) 0%, rgba(255,255,255,0) 70%)',
  zIndex: 0,
  borderRadius: '50%',
};

const Hero = () => {
  const [isHovered, setIsHovered] = React.useState(false);
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 900);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const currentHeroContainerStyle = {
    ...heroContainerStyle,
    flexDirection: isMobile ? 'column-reverse' : 'row',
    textAlign: isMobile ? 'center' : 'left',
    padding: isMobile ? '2rem 1rem' : heroContainerStyle.padding,
  };

  const currentCtaButtonStyle = {
    ...ctaButtonStyle,
    transform: isHovered ? 'translateY(-5px)' : 'translateY(0)',
    boxShadow: isHovered 
      ? '0 10px 20px rgba(0,120,212,0.3)' 
      : '0 4px 15px rgba(0,120,212,0.25)',
  };

  const currentHeroAnimationStyle = {
    ...heroAnimationStyle,
    width: isMobile ? '70%' : heroAnimationStyle.width,
    marginBottom: isMobile ? '2rem' : 0,
    maxWidth: isMobile ? '300px' : 'none',
    alignSelf: isMobile ? 'center' : 'flex-end',
  };

  const currentHeroContentStyle = {
    ...heroContentStyle,
    textAlign: isMobile ? 'center' : 'left',
    alignItems: isMobile ? 'center' : 'flex-start',
  };

  return (
    <section id="home" style={currentHeroContainerStyle}>
      <div style={gradientOverlayStyle}></div>
      <div style={currentHeroContentStyle}>
        <h1 style={heroTitleStyle}>
          Meet <span style={highlightTextStyle}>Aurora</span> – Your AI Interview Assistant
        </h1>
        <p style={heroSubtitleStyle}>
          From resume analysis to real-time mock interviews, powered by cutting-edge AWS technology and GenAI innovation.
        </p>
        <a 
          href="#features" 
          style={currentCtaButtonStyle}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          Explore Features
        </a>
      </div>
      <div style={currentHeroAnimationStyle}>
        <Lottie 
          animationData={robotAnimation} 
          loop={true} 
          style={{ 
            width: '100%', 
            height: '100%',
            maxWidth: '100%',
            overflow: 'hidden'
          }}
        />
      </div>
    </section>
  );
};

export default Hero;
