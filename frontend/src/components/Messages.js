import React, { useEffect, useRef } from 'react';
import './Messages.css';

function Messages({ messages }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="card messages-card">
      <div className="card-header">
        <h2>💬 Messages</h2>
      </div>
      <div className="card-body">
        <div className="messages-container">
        {messages.length === 0 ? (
          <div style={{ 
            color: '#718096', 
            textAlign: 'center', 
            padding: '40px 20px',
            fontSize: '1rem'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '15px', opacity: 0.5 }}>💬</div>
            <p style={{ fontWeight: 500 }}>No messages yet</p>
            <p style={{ fontSize: '0.9rem', opacity: 0.8, marginTop: '5px' }}>Messages will appear here</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message message-${msg.type}`}>
              <div className="message-header">
                <span className="message-type">{msg.type}</span>
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <pre className="message-content">{msg.message}</pre>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      </div>
    </div>
  );
}

export default Messages;

