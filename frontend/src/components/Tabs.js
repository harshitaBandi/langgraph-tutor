import React from 'react';
import './Tabs.css';

function Tabs({ activeTab, onTabChange, tabs }) {
  return (
    <div className="tabs-container">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
          {tab.badge && <span className="tab-badge">{tab.badge}</span>}
        </button>
      ))}
    </div>
  );
}

export default Tabs;

