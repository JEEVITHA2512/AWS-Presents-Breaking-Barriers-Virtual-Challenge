import React from 'react';
import { Hero, About, Features, Videos, Footer } from './sections';
import './App.css';

function App() {
  return (
    <div className="app-wrapper">
      <main className="main-content">
        <Hero />
        <About />
        <Features />
        <Videos />
        {/* <Contact /> removed */}
      </main>
      <Footer />
    </div>
  );
}

export default App;
