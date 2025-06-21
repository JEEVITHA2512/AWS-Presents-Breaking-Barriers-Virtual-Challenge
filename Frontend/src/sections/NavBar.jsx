import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './NavBar.css';
import RoboTop from '../assets/Robo-top.png';

const NavBar = () => {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('home');
  const [isScrolled, setIsScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [clickedLink, setClickedLink] = useState(null);

  // Generate random particles for logo animation
  const particles = Array.from({ length: 8 }, (_, i) => ({
    id: i,
    top: `${Math.random() * 100}%`,
    left: `${Math.random() * 100}%`,
    delay: Math.random() * 0.5,
    x: (Math.random() - 0.5) * 40, // random x direction
    y: (Math.random() - 0.5) * 40, // random y direction
  }));
  // Handle scroll to detect current section and navbar style changes
  const handleScroll = useCallback(() => {
    // Update scrolled state for navbar style
    setIsScrolled(window.scrollY > 20);

    // Calculate scroll progress for the progress bar
    const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const scrolled = (winScroll / height) * 100;
    document.documentElement.style.setProperty('--scroll-width', `${scrolled}%`);

    // Determine which section is currently in view
    const sections = ['home', 'about', 'features', 'videos'];
    const currentPosition = window.scrollY + window.innerHeight / 3;
    
    for (const section of sections) {
      const element = document.getElementById(section);
      if (element) {
        const { top, bottom } = element.getBoundingClientRect();
        const elementTop = top + window.scrollY;
        const elementBottom = bottom + window.scrollY;
        
        if (currentPosition >= elementTop && currentPosition <= elementBottom) {
          setActiveSection(section);
          break;
        }
      }
    }
  }, []);

  // Check for mobile view
  const checkMobile = useCallback(() => {
    setIsMobile(window.innerWidth <= 768);
    // Close menu if window is resized to desktop
    if (window.innerWidth > 768) {
      setMenuOpen(false);
    }
  }, []);


  // Smooth scroll to section
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      window.scrollTo({
        top: element.offsetTop - 80, // Account for navbar height
        behavior: 'smooth'
      });
      setActiveSection(sectionId);
      // Close mobile menu after navigation
      if (isMobile) {
        setMenuOpen(false);
      }
    }
  };
  useEffect(() => {
    // Set up event listeners
    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', checkMobile);
    
    // Initial checks
    handleScroll();
    checkMobile();
    
    // Clean up
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', checkMobile);
    };
  }, [handleScroll, checkMobile]);

  // Detect if on /mock-interview and set no active nav link
  useEffect(() => {
    if (window.location.pathname === '/mock-interview') {
      setActiveSection('');
    }
  }, []);

  // Navigation links
  const navLinks = [
    { id: 'home', label: 'Home' },
    { id: 'about', label: 'About Aurora' },
    { id: 'features', label: 'Features' },
    { id: 'videos', label: 'Videos' }
  ];

  return (
    <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`}>
      <div className="navbar-content" style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
          <div className="logo" onClick={() => {
            if (window.location.pathname === '/mock-interview') {
              navigate('/');
            } else {
              scrollToSection('home');
            }
          }}>
            <img src={RoboTop} alt="Robo-top" className="logo-robo" />
            <span className="logo-highlight">Aur</span>ora
            <div className="logo-particles">
              {particles.map(particle => (
                <div
                  key={particle.id}
                  className="particle"
                  style={{
                    top: particle.top,
                    left: particle.left,
                    animationDelay: `${particle.delay}s`,
                    '--x': `${particle.x}px`,
                    '--y': `${particle.y}px`
                  }}
                />
              ))}
            </div>
          </div>
        </div>
        <div className={`nav-menu ${menuOpen ? 'open' : ''}`} style={{ marginLeft: '2rem' }}>
          {navLinks.map(link => (
            <a
              key={link.id}
              href={`#${link.id}`}
              className={`nav-link ${activeSection === link.id ? 'active' : ''} ${clickedLink === link.id ? 'nav-link-clicked' : ''}`}
              onClick={e => {
                e.preventDefault();
                setClickedLink(link.id);
                if (window.location.pathname === '/mock-interview') {
                  navigate(`/#${link.id}`);
                } else {
                  scrollToSection(link.id);
                }
                setTimeout(() => setClickedLink(null), 300);
              }}
            >
              {link.label}
            </a>
          ))}
        </div>
        <a href="/mock-interview" className="mock-interview-link" style={{
          fontWeight: 600,
          fontSize: '1.1rem',
          color: '#0078d4',
          textDecoration: 'none',
          marginLeft: 'auto',
          letterSpacing: '0.5px',
          padding: '0.5rem 1.2rem',
          borderRadius: '2rem',
          background: 'linear-gradient(90deg, #e3f0ff 0%, #c7e2ff 100%)',
          boxShadow: '0 2px 10px rgba(0,120,212,0.08)',
          transition: 'background 0.2s, color 0.2s',
          alignSelf: 'center',
          zIndex: 10
        }}>Mock Interview</a>
      </div>
    </nav>
  );
};

export default NavBar;