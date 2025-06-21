import React, { useState, useEffect, useRef } from 'react';
import auroraImg1 from '../assets/Hardware-plannings.jpg';
import auroraImg2 from '../assets/Hardware-plannings.jpg';
import auroraImg3 from '../assets/Hardware-plannings.jpg';
// import nepheleImg2 from '../assets/nephele_2.0 - Copy.jpeg';
// import nepheleImg3 from '../assets/nephele_2.0 - Copy (2).jpeg';

const aboutContainerStyle = {
  padding: '5rem 2rem',
  background: 'linear-gradient(180deg, #f8fbff 0%, #ffffff 100%)',
  position: 'relative',
  overflow: 'hidden',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '3rem',
  flexDirection: 'row',
};

const aboutContentStyle = {
  flex: 1,
  minWidth: 0,
  textAlign: 'left',
  zIndex: 2,
};

const aboutImageAreaStyle = {
  flex: 1,
  minWidth: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  zIndex: 2,
  width: '100%',
  height: '500px',
  maxHeight: '80vh',
  overflow: 'hidden',
  position: 'relative',
};

const aboutImageTrackStyle = {
  display: 'flex',
  alignItems: 'center',
  height: '100%',
  animation: 'about-carousel-scroll 18s linear infinite',
};

const aboutImageStyle = {
  width: 'auto',
  height: '100%',
  maxHeight: '500px',
  minWidth: '600px',
  objectFit: 'cover',
  borderRadius: '2rem',
  boxShadow: '0 8px 32px rgba(0,120,212,0.10)',
  marginRight: '2rem',
  background: '#e3f0ff',
  transform: 'scale(1.04)', // very slight zoom
  transition: 'transform 0.8s cubic-bezier(0.4,0,0.2,1)',
};

const aboutHeadingStyle = {
  fontSize: '2.5rem',
  color: '#2a3a5e',
  marginBottom: '1.5rem',
  position: 'relative',
};

const aboutHighlightStyle = {
  position: 'relative',
  color: '#0078d4',
  display: 'inline-block',
};

const aboutTextStyle = {
  color: '#4a5a7a',
  maxWidth: '800px',
  margin: '0 auto 3rem 0',
  fontSize: '1.2rem',
  lineHeight: '1.7',
  position: 'relative',
};

const techListStyle = {
  display: 'flex',
  justifyContent: 'flex-start',
  gap: '1.5rem',
  flexWrap: 'wrap',
  listStyle: 'none',
  padding: 0,
  position: 'relative',
};

const techItemStyle = {
  background: 'linear-gradient(135deg, #e3f0ff 0%, #c7e2ff 100%)',
  color: '#2a3a5e',
  padding: '0.7rem 1.5rem',
  borderRadius: '2rem',
  fontWeight: '600',
  fontSize: '1.05rem',
  boxShadow: '0 2px 10px rgba(0,120,212,0.1)',
  transition: 'all 0.3s ease',
};

const decorativeShapeStyle = {
  position: 'absolute',
  borderRadius: '50%',
  background: 'rgba(224, 242, 255, 0.5)',
  zIndex: 0,
};

// Add keyframes for infinite scroll
const styleSheet = document.createElement('style');
styleSheet.innerHTML = `
@keyframes about-carousel-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
`;
document.head.appendChild(styleSheet);

const About = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [hoveredTech, setHoveredTech] = useState(null);
  const [isMobile, setIsMobile] = useState(false);
  const aboutSectionRef = useRef(null);

  // Responsive layout
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 900);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Scroll animation for content
  useEffect(() => {
    const handleScroll = () => {
      if (aboutSectionRef.current) {
        const rect = aboutSectionRef.current.getBoundingClientRect();
        setIsVisible(rect.top <= window.innerHeight * 0.75);
      }
    };
    handleScroll();
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const getTechItemStyle = (tech) => ({
    ...techItemStyle,
    transform: hoveredTech === tech ? 'translateY(-5px)' : 'translateY(0)',
    boxShadow: hoveredTech === tech 
      ? '0 6px 15px rgba(0,120,212,0.15)' 
      : '0 2px 10px rgba(0,120,212,0.1)',
  });

  // Responsive container
  const currentAboutContainerStyle = {
    ...aboutContainerStyle,
    flexDirection: isMobile ? 'column-reverse' : 'row',
    textAlign: isMobile ? 'center' : 'left',
    gap: isMobile ? '2rem' : '3rem',
    alignItems: isMobile ? 'flex-start' : 'center',
    padding: isMobile ? '3rem 1rem' : aboutContainerStyle.padding,
  };
  const currentAboutContentStyle = {
    ...aboutContentStyle,
    alignItems: isMobile ? 'center' : 'flex-start',
    textAlign: isMobile ? 'center' : 'left',
    margin: isMobile ? '0 auto' : 0,
    opacity: isVisible ? 1 : 0,
    transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
    transition: 'opacity 0.8s ease, transform 0.8s ease',
  };
  const currentAboutImageAreaStyle = {
    ...aboutImageAreaStyle,
    width: isMobile ? '100%' : '50vw',
    height: isMobile ? '300px' : aboutImageAreaStyle.height,
    maxHeight: isMobile ? '300px' : aboutImageAreaStyle.maxHeight,
    marginBottom: isMobile ? '2rem' : 0,
  };
  const currentAboutImageTrackStyle = {
    ...aboutImageTrackStyle,
    width: isMobile ? '200vw' : '100vw',
    animationDuration: isMobile ? '12s' : '18s',
  };
  const currentAboutImageStyle = {
    ...aboutImageStyle,
    minWidth: isMobile ? '80vw' : '600px',
    maxWidth: isMobile ? '90vw' : '800px',
    height: isMobile ? '100%' : aboutImageStyle.height,
  };

  const technologies = [
    { name: 'Raspberry Pi', color: '#C51A4A' },
    { name: 'AWS', color: '#FF9900' },
    { name: 'React', color: '#61DAFB' },
    { name: 'LLMs', color: '#10A37F' },
    { name: 'GenAI', color: '#8E44AD' }
  ];

  // For future: add more images to this array
  const images = [
    auroraImg1,
    auroraImg2,
    auroraImg3
  ];

  // Infinite scroll logic: duplicate images for seamless loop
  const infiniteImages = [...images, ...images];

  return (
    <section id="about" ref={aboutSectionRef} style={currentAboutContainerStyle}>
      {/* Decorative shapes */}
      <div style={{
        ...decorativeShapeStyle,
        width: '300px',
        height: '300px',
        top: '10%',
        left: '-150px',
      }}></div>
      <div style={{
        ...decorativeShapeStyle,
        width: '200px',
        height: '200px',
        bottom: '10%',
        right: '-100px',
      }}></div>
      <div style={currentAboutContentStyle}>
        <h2 style={aboutHeadingStyle}>
          About <span style={aboutHighlightStyle}>Aurora</span>
        </h2>
        <p style={aboutTextStyle}>
          Aurora is an AI-powered interview assistant robot designed to revolutionize how 
          candidates prepare for interviews with real-time feedback, comprehensive resume analysis,
          and personalized coaching. Built by a passionate team using cutting-edge technologies 
          including Raspberry Pi, AWS services, React, and advanced LLMs, Aurora is constantly evolving—look 
          out for Aurora and the upcoming 3.0 upgrade with even more powerful features!
        </p>
        <ul style={techListStyle}>
          {technologies.map((tech) => (
            <li 
              key={tech.name}
              style={{
                ...getTechItemStyle(tech.name),
                borderLeft: `4px solid ${tech.color}`
              }}
              onMouseEnter={() => setHoveredTech(tech.name)}
              onMouseLeave={() => setHoveredTech(null)}
            >
              {tech.name}
            </li>
          ))}
        </ul>
      </div>
      <div style={currentAboutImageAreaStyle}>
        <div style={currentAboutImageTrackStyle}>
          {infiniteImages.map((img, idx) => (
            <img
              key={idx}
              src={img}
              alt="Aurora robot"
              style={currentAboutImageStyle}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default About;
