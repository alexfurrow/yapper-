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
            <span className="title-line highlight">Journal Assistant</span>
          </h1>
          
          <p className="hero-subtitle">
            Transform your thoughts into insights with AI-powered journaling. 
            Write, reflect, and discover patterns in your daily life.
          </p>

          <div className="hero-features">
            <div className="feature">
              <div className="feature-icon">✍️</div>
              <span>Smart Writing</span>
            </div>
            <div className="feature">
              <div className="feature-icon">🤖</div>
              <span>AI Insights</span>
            </div>
            <div className="feature">
              <div className="feature-icon">🔒</div>
              <span>Private & Secure</span>
            </div>
          </div>

          <div className="cta-buttons">
            <button 
              className="cta-primary"
              onClick={() => navigate('/register')}
            >
              Start Journaling Free
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
          <div className="journal-preview">
            <div className="journal-page">
              <div className="journal-line"></div>
              <div className="journal-line short"></div>
              <div className="journal-line"></div>
              <div className="journal-line short"></div>
              <div className="journal-line"></div>
            </div>
            <div className="ai-insight">
              <div className="insight-icon">💡</div>
              <div className="insight-text">
                <div className="insight-line"></div>
                <div className="insight-line short"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Social Proof */}
      <div className="social-proof">
        <p className="trust-text">Trusted by thousands of users worldwide</p>
        <div className="testimonial">
          <div className="quote">"Yapper has transformed how I reflect on my day. The AI insights are incredibly helpful!"</div>
          <div className="author">- Sarah M., Journal Enthusiast</div>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
