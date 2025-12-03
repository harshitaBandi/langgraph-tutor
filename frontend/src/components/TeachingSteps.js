import React from 'react';
import './TeachingSteps.css';
import LoadingSpinner from './LoadingSpinner';

function TeachingSteps({ steps, isLoading }) {
  if (steps.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>📚 Teaching Steps</h2>
        </div>
        <div className="card-body">
          <div style={{ 
            textAlign: 'center', 
            padding: '60px 40px',
            color: '#718096',
            fontSize: '1.1rem'
          }}>
            <div style={{ fontSize: '4rem', marginBottom: '20px', opacity: 0.5 }}>📖</div>
            <p style={{ fontWeight: 500, marginBottom: '10px' }}>Waiting for teaching to begin...</p>
            <p style={{ fontSize: '0.95rem', opacity: 0.8 }}>Teaching steps will appear here as they are streamed</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>📚 Teaching Steps ({steps.length}/5)</h2>
      </div>
      <div className="card-body">
      <div className="steps-container">
        {steps.map((step, index) => (
          <div key={index} className="step-card">
            <div className="step-header">
              <span className="step-number">Step {step.step_number}</span>
              <span className="step-title">{step.title}</span>
            </div>
            <div className="step-content">
              {step.content}
            </div>
          </div>
        ))}
        {isLoading && steps.length === 5 && (
          <div className="loading-assessment">
            <LoadingSpinner size="medium" />
            <p>Generating assessment based on teaching content...</p>
          </div>
        )}
      </div>
      </div>
    </div>
  );
}

export default TeachingSteps;

