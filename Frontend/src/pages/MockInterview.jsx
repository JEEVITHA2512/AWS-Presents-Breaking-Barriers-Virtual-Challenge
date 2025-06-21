import React, { useRef, useState } from 'react';

const MockInterview = () => {
  const fileInputRef = useRef(null);
  const [resumeName, setResumeName] = useState('');
  const [uploadMessage, setUploadMessage] = useState('');

  const handleResumeUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setResumeName(file.name);
      setUploadMessage('Resume uploaded successfully!');
      // Here you would handle the upload to AWS S3 or backend
    } else {
      setResumeName('');
      setUploadMessage('');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      background: 'linear-gradient(120deg, #f8fbff 0%, #e3f0ff 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 0,
      margin: 0,
      position: 'relative',
      overflow: 'hidden',
    }}>
      <h1 style={{ fontSize: '2.5rem', color: '#8E44AD', fontWeight: 800, marginBottom: '2rem', letterSpacing: '-1px', textAlign: 'center' }}>
        Your AI Interview Assistant
      </h1>
      <h2 style={{ fontSize: '2rem', color: '#0078d4', marginBottom: '1.2rem', fontWeight: 700, textAlign: 'center' }}>
        Mock Interview
      </h2>
      <div style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '2.5rem',
        width: '100%',
        maxWidth: 1200,
        margin: '0 auto',
      }}>
        <div style={{ flex: 1, minWidth: 300, textAlign: 'right', fontSize: '1.2rem', color: '#4a5a7a', fontWeight: 500 }}>
          Welcome to the Mock Interview page! Here you can practice and prepare for your interviews with Aurora.
        </div>
        <div style={{ flex: 1, minWidth: 300, textAlign: 'left', fontSize: '1.2rem', color: '#4a5a7a', fontWeight: 500 }}>
          <span style={{ color: '#C51A4A', fontWeight: 600 }}>Upload your resume below to get personalized feedback and AI-powered analysis.</span>
        </div>
      </div>
      <div style={{ margin: '2.5rem auto 1.5rem', maxWidth: 400, background: 'none', borderRadius: 0, boxShadow: 'none', padding: 0, display: 'flex', justifyContent: 'center' }}>
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleResumeUpload}
        />
        <button
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
          style={{
            background: 'linear-gradient(90deg, #0078d4 0%, #61DAFB 100%)',
            color: '#fff',
            border: 'none',
            borderRadius: '2rem',
            padding: '0.8rem 2.2rem',
            fontWeight: 600,
            fontSize: '1.1rem',
            cursor: 'pointer',
            boxShadow: '0 2px 10px rgba(0,120,212,0.10)',
            marginBottom: '1rem',
            transition: 'background 0.2s, color 0.2s',
          }}
        >
          Upload Resume
        </button>
        {resumeName && (
          <div style={{ marginLeft: '1rem', color: '#2a3a5e', fontWeight: 500, alignSelf: 'center' }}>
            <span>Uploaded: {resumeName}</span>
          </div>
        )}
        {uploadMessage && (
          <div style={{ marginLeft: '1rem', color: '#10A37F', fontWeight: 600, alignSelf: 'center' }}>
            {uploadMessage}
          </div>
        )}
      </div>
      <div style={{ marginTop: '2.5rem', color: '#8E44AD', fontWeight: 500, fontSize: '1.1rem', textAlign: 'center' }}>
        <span>Tip: A well-formatted resume increases your chances of getting noticed. Our AI will analyze your resume and provide actionable feedback!</span>
      </div>
    </div>
  );
};

export default MockInterview;
