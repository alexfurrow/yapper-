import React, { useContext } from 'react';
import { NavigationContext } from '../App';
import './LandingPage.css';

function LandingPage() {
  const { navigate } = useContext(NavigationContext);

  return (
    <div className="landing-page">
      {/* Animated Background */}
      <div className="background-animation">
        <div className="floating-shapes">
          <div className="shape shape-1"></div>
          <div className="shape shape-2"></div>
          <div className="shape shape-3"></div>
          <div className="shape shape-4"></div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            <span className="title-line">Welcome to</span>
            <span className="title-line highlight">Yapper</span>
          </h1>
          
          <p className="hero-subtitle">
            Enhance your memory, brighten your thinking, and chronicle your life. 
            Transform your thoughts into something beautiful.
          </p>

          <div className="hero-features">
            <div className="feature">
              <div className="feature-icon">🎤</div>
              <span>Yap directly into the mic</span>
            </div>
            <div className="feature">
              <div className="feature-icon">✍️</div>
              <span>Write like you mean it</span>
            </div>
            <div className="feature">
              <div className="feature-icon">🔄</div>
              <span>Engage your past self</span>
            </div>
          </div>

          <div className="cta-buttons">
            <button 
              className="cta-primary"
              onClick={() => navigate('/register')}
            >
              Start Yapping Free
            </button>
            <button 
              className="cta-secondary"
              onClick={() => navigate('/login')}
            >
              Sign In
            </button>
          </div>
        </div>

        <div className="hero-visual">
          <div className="abstract-artwork">
            {/* Abstract geometric shapes inspired by SEO Yeo Hon */}
            <div className="art-layer layer-1">
              <div className="geometric-shape circle-1"></div>
              <div className="geometric-shape square-1"></div>
              <div className="geometric-shape triangle-1"></div>
            </div>
            <div className="art-layer layer-2">
              <div className="geometric-shape circle-2"></div>
              <div className="geometric-shape rectangle-1"></div>
              <div className="geometric-shape oval-1"></div>
            </div>
            <div className="art-layer layer-3">
              <div className="geometric-shape hexagon-1"></div>
              <div className="geometric-shape circle-3"></div>
              <div className="geometric-shape diamond-1"></div>
            </div>
            {/* Floating text elements */}
            <div className="text-elements">
              <div className="floating-text text-1">thoughts</div>
              <div className="floating-text text-2">memories</div>
              <div className="floating-text text-3">ideas</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;