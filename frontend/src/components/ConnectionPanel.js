import React, { useState } from 'react';

function ConnectionPanel({ connected, onConnect, onDisconnect }) {
  const [sessionId, setSessionId] = useState('');
  const [topic, setTopic] = useState('');

  const handleConnect = () => {
    if (!topic.trim()) {
      alert('⚠️ Please enter a topic to learn');
      return;
    }

    const sid = sessionId.trim() || `session-${Date.now()}`;
    onConnect(sid, topic.trim());
  };

  return (
    <div className="card no-padding-top">
      <div className="card-header">
        <h2>🔌 Connection</h2>
      </div>
      <div className="card-body">
      
      <div className="input-group">
        <label>Session ID:</label>
        <input
          type="text"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Leave empty for auto-generated"
          disabled={connected}
        />
      </div>

      <div className="input-group">
        <label>Topic: <span style={{ color: 'red' }}>*</span></label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter topic to learn (e.g., Machine Learning, Python Functions)"
          disabled={connected}
          required
        />
      </div>

      <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
        <button
          className="button button-primary"
          onClick={handleConnect}
          disabled={connected}
        >
          {connected ? 'Connected' : 'Connect & Start Teaching'}
        </button>
        
        <button
          className="button button-secondary"
          onClick={onDisconnect}
          disabled={!connected}
        >
          Disconnect
        </button>
      </div>

      <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
        <span className="status-icon">
          {connected ? '✓' : '○'}
        </span>
        <span>{connected ? 'Connected' : 'Disconnected'}</span>
      </div>
      </div>
    </div>
  );
}

export default ConnectionPanel;

