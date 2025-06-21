import React, { useEffect } from 'react';

const featuresContainerStyle = {
  padding: '4rem 2rem',
  background: '#fff',
  textAlign: 'center',
};

const featuresSectionBg = {
  position: 'absolute',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  zIndex: 0,
  background: 'linear-gradient(120deg, #e3f0ff 0%, #f8fbff 100%)',
  overflow: 'hidden',
};

const diagonalRoadmapContainer = {
  position: 'relative',
  zIndex: 1,
  maxWidth: '1100px',
  margin: '0 auto',
  padding: '2.5rem 0 2rem 0',
  display: 'flex',
  flexDirection: 'row',
  flexWrap: 'nowrap',
  alignItems: 'flex-end',
  minHeight: '340px', // Slightly more vertical space
  justifyContent: 'center',
  gap: '3.5rem', // Add gap between features
};

const diagonalStep = (i, total) => {
  // Alternate up/down for diagonal effect
  const isEven = i % 2 === 0;
  const baseY = isEven ? 0 : 60;
  return {
    position: 'relative',
    zIndex: 2,
    background: 'rgba(255,255,255,0.45)',
    borderRadius: '1.2rem',
    boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.10)',
    padding: '2.1rem 2.2rem 2.1rem 1.2rem',
    minWidth: '260px',
    maxWidth: '320px',
    marginLeft: i === 0 ? 0 : '-20px', // Reduce overlap for more visible gap
    marginRight: i === total - 1 ? 0 : '-20px',
    marginTop: `${baseY}px`,
    marginBottom: isEven ? '40px' : '0',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    borderLeft: '6px solid #bbdefb',
    transition: 'background 0.3s, box-shadow 0.3s, border-color 0.3s',
  };
};

const diagonalIcon = {
  width: '64px',
  height: '64px',
  borderRadius: '50%',
  background: 'linear-gradient(135deg, #90caf9 60%, #e3f0ff 100%)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '2.2rem',
  boxShadow: '0 4px 16px 0 rgba(120,180,255,0.18)',
  border: '2.5px solid #0078d4',
  marginBottom: '1.1rem',
  flexShrink: 0,
};

const roadmapContent = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  gap: '0.5rem',
};

const roadmapTitle = {
  fontSize: '1.25rem',
  fontWeight: 800,
  color: '#005fa3',
  marginBottom: '0.2rem',
  letterSpacing: '-0.5px',
};

const roadmapDesc = {
  color: '#2a3a5e',
  fontSize: '1.08rem',
  fontWeight: 500,
  lineHeight: 1.6,
};

const roadmapDetail = {
  color: '#0078d4',
  fontSize: '0.99rem',
  background: 'rgba(187,222,251,0.13)',
  borderRadius: '0.7rem',
  padding: '0.7rem 0.9rem',
  fontWeight: 500,
  marginTop: '0.5rem',
  boxShadow: '0 1px 4px rgba(0,120,212,0.06)',
};

const diagonalLine = (i, total) => {
  if (i === total - 1) return {};
  // Diagonal SVG line between steps, styled for visibility
  return {
    position: 'absolute',
    top: '50%',
    left: '100%',
    width: '90px',
    height: '0',
    zIndex: 1,
    pointerEvents: 'none',
    filter: 'drop-shadow(0 2px 8px #bbdefb88)', // Add glow to the line
  };
};

const featuresData = [
  {
    icon: '🧠',
    title: 'Face Recognition of Previously Visited Members',
    desc: 'Identifies and recognizes users who have interacted with Aurora earlier.',
    detail: 'Uses the Pi Camera to capture the user\'s face. A machine learning model running on Coral TPU processes the face data and matches it with records stored in DynamoDB. Delivers a personalized greeting and experience, making users feel remembered and valued.'
  },
  {
    icon: '📷',
    title: 'QR Code Scanner',
    desc: 'Scans QR codes to identify users and log their presence.',
    detail: 'Uses camera and Python-based QR scanning libraries. On scanning, sends data to AWS Lambda, which updates attendance records in DynamoDB. Automates attendance and check-ins, saving time and effort at events and in schools.'
  },
  {
    icon: '🗓️',
    title: 'Attendance Management',
    desc: 'Records and manages participant or student attendance.',
    detail: 'Integrated with the QR system. Stores attendance logs in DynamoDB. Can send confirmation emails using Amazon SES. Ensures accurate tracking and generates real-time reports.'
  },
  {
    icon: '🎤',
    title: 'Voice Commands',
    desc: 'Responds to spoken instructions to perform tasks.',
    detail: 'Captures voice using a microphone. Processes the input with Amazon Transcribe for speech-to-text. Executes commands using Python scripts and AWS Lambda functions. Enables hands-free operation.'
  },
  {
    icon: '💬',
    title: 'Interaction Module',
    desc: 'Interacts with users using predefined answers or dynamic AI responses.',
    detail: 'Uses a combination of LLMs (like Meta LLaMA 2) and custom-trained data. Voice interaction is enabled by Amazon Polly (TTS) and Transcribe (STT). Offers smart and relevant responses that keep users engaged.'
  },
  {
    icon: '✋',
    title: 'Handshake and Hand Gesture Recognition',
    desc: 'Detects and responds to hand movements and gestures like waves or handshakes.',
    detail: 'Utilizes the Pi Camera and ML algorithms to detect hand poses. Coral TPU accelerates gesture recognition. Adds a physical, human-like interaction layer.'
  },

  {
    icon: '🌍',
    title: 'Language Translation',
    desc: 'Translates text or voice to multiple languages.',
    detail: 'Captures spoken input. Converts it to text using Amazon Transcribe. Translates using LLMs or translation APIs. Converts back to speech using Amazon Polly. Makes Aurora inclusive and accessible to multilingual audiences.'
  },
];

const Features = () => {
  // Add keyframes for the animation only once
  useEffect(() => {
    if (typeof window !== 'undefined' && typeof document !== 'undefined') {
      if (!document.getElementById('features-title-shimmer-style')) {
        const style = document.createElement('style');
        style.id = 'features-title-shimmer-style';
        style.innerHTML = `@keyframes featuresTitleShimmer {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }`;
        document.head.appendChild(style);
      }
      if (!document.getElementById('hanking-animation-style')) {
        const style = document.createElement('style');
        style.id = 'hanking-animation-style';
        style.innerHTML = `@keyframes hanking {
          0% { transform: rotate(-10deg); }
          50% { transform: rotate(10deg); }
          100% { transform: rotate(-10deg); }
        }
        @keyframes hanking-string {
          0% { transform: rotate(-10deg); }
          50% { transform: rotate(10deg); }
          100% { transform: rotate(-10deg); }
        }`;
        document.head.appendChild(style);
      }
    }
  }, []);

  return (
    <section id="features" style={{...featuresContainerStyle, position:'relative', overflow:'hidden'}}>
      <div style={featuresSectionBg}></div>
      <h2 style={{
        fontSize: '2.3rem',
        fontWeight: 900,
        color: '#005fa3',
        marginBottom: '0.7rem',
        letterSpacing: '-1px',
        zIndex: 2,
        position: 'relative',
        textShadow: '0 2px 12px #e3f0ff',
      }}>Features</h2>
      <div style={{fontSize:'1.18rem', color:'#4a5a7a', marginBottom:'2.5rem', zIndex:2, position:'relative', fontWeight:500}}>
        Follow Aurora's journey and see how each feature builds on the last to create a seamless experience.
      </div>
      <div style={{
        ...diagonalRoadmapContainer,
        flexWrap: 'nowrap',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
        maxWidth: '100%',
        width: '100vw',
        margin: '0',
        padding: '2.5rem 0 2rem 0',
        gap: '1.5rem',
        minHeight: '340px', // Slightly more vertical space
      }}>
        {featuresData.slice(0,5).map((f, i, arr) => (
          <div key={i} style={{
            ...diagonalStep(i, arr.length),
            minWidth: '0',
            maxWidth: '20vw',
            flex: 1,
            marginLeft: i === 0 ? 0 : 0,
            marginRight: i === arr.length - 1 ? 0 : 0,
            marginTop: i % 2 === 0 ? '0' : '70px',
            marginBottom: i % 2 === 0 ? '70px' : '0',
          }}>
            {/* Hanging string effect */}
            <div style={{
              width: '2px',
              height: '38px',
              background: 'linear-gradient(to bottom, #b0c4de 60%, #fff 100%)',
              margin: '0 auto',
              position: 'relative',
              zIndex: 3,
              top: '-38px',
              left: 0,
              right: 0,
              animation: 'hanking-string 1.6s cubic-bezier(.36,.07,.19,.97) infinite alternate',
              transformOrigin: '50% 0',
            }} />
            {/* Pin/nail effect */}
            <div style={{
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              background: 'radial-gradient(circle at 30% 30%, #e3f0ff 60%, #b0c4de 100%)',
              border: '2px solid #b0c4de',
              position: 'absolute',
              left: '50%',
              top: '-48px',
              transform: 'translateX(-50%)',
              zIndex: 4,
              boxShadow: '0 2px 8px #bbdefb88',
            }} />
            <div style={{
              ...diagonalIcon,
              animation: 'hanking 1.6s cubic-bezier(.36,.07,.19,.97) infinite alternate',
              transformOrigin: '50% 0',
            }}>{f.icon}</div>
            <div style={roadmapContent}>
              <div style={roadmapTitle}>{f.title}</div>
              <div style={roadmapDesc}>{f.desc}</div>
              <div style={roadmapDetail}>{f.detail}</div>
            </div>
            {/* Diagonal SVG line to next step */}
            {i < arr.length - 1 && (
              <svg style={diagonalLine(i, arr.length)} width="90" height="90" viewBox="0 0 90 90">
                <polyline
                  points={i % 2 === 0 ? '0,45 90,90' : '0,45 90,0'}
                  fill="none"
                  stroke="#bbdefb"
                  strokeWidth="6"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </div>
        ))}
      </div>
    </section>
  );
};

export default Features;
