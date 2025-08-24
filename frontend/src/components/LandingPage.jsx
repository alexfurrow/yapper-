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
            <span className="title-line">Your Personal</span>
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
            {/* Organic flowing forms inspired by SEO Hyojung */}
            <div className="art-layer layer-1">
              <div className="organic-shape blob-1"></div>
              <div className="organic-shape blob-2"></div>
              <div className="organic-shape blob-3"></div>
            </div>
            <div className="art-layer layer-2">
              <div className="organic-shape wave-1"></div>
              <div className="organic-shape wave-2"></div>
              <div className="organic-shape cloud-1"></div>
            </div>
            <div className="art-layer layer-3">
              <div className="organic-shape mist-1"></div>
              <div className="organic-shape mist-2"></div>
              <div className="organic-shape breath-1"></div>
            </div>
            {/* Ethereal text elements */}
            <div className="text-elements">
              <div className="floating-text text-1">thoughts</div>
              <div className="floating-text text-2">memories</div>
              <div className="floating-text text-3">ideas</div>
              <div className="floating-text text-4">dreams</div>
              <div className="floating-text text-5">feelings</div>
            </div>
            {/* Subtle light effects */}
            <div className="light-effects">
              <div className="light-orb orb-1"></div>
              <div className="light-orb orb-2"></div>
              <div className="light-orb orb-3"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Social Proof */}
      <div className="social-proof">
        <p className="trust-text">Trusted by thousands of thinkers worldwide</p>
        <div className="testimonial">
          <div className="quote">"Yapper has transformed how I capture and reflect on my thoughts. It's like having a conversation with my future self."</div>
          <div className="author">- Alex M., Creative Thinker</div>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
