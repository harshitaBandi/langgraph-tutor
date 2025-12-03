import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import Tabs from './components/Tabs';
import ConnectionPanel from './components/ConnectionPanel';
import TeachingSteps from './components/TeachingSteps';
import Assessment from './components/Assessment';
import Messages from './components/Messages';

function App() {
  const [activeTab, setActiveTab] = useState('connection');
  const [connected, setConnected] = useState(false);
  const [topic, setTopic] = useState('');
  const [steps, setSteps] = useState([]);
  const [currentAssessment, setCurrentAssessment] = useState(null);
  const [gradeReport, setGradeReport] = useState(null);
  const [assessmentIdForRetake, setAssessmentIdForRetake] = useState(null);
  const [retakeKey, setRetakeKey] = useState(0);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef(null);
  const topicRef = useRef('');

  const tabs = [
    { id: 'connection', label: 'Connection', icon: '🔌' },
    { id: 'teaching', label: 'Teaching Steps', icon: '📚', badge: steps.length > 0 ? steps.length : null },
    { id: 'assessment', label: 'Assessment', icon: '📝', badge: currentAssessment ? 'Ready' : null },
    { id: 'messages', label: 'Messages', icon: '💬', badge: messages.length > 0 ? messages.length : null },
  ];

  const connect = (sid, top) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsUrl = `ws://localhost:8000/ws/${sid}`;
    const websocket = new WebSocket(wsUrl);
    wsRef.current = websocket;

    websocket.onopen = () => {
      setConnected(true);
      setTopic(top);
      topicRef.current = top;
      setSteps([]);
      setCurrentAssessment(null);
      setGradeReport(null);
      setMessages([]);
      setIsLoading(true);
      addMessage('Connected to server', 'info');
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (error) {
        console.error('Error parsing message:', error);
        addMessage(`Error: ${error.message}`, 'error');
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      addMessage('WebSocket error occurred', 'error');
    };

    websocket.onclose = () => {
      setConnected(false);
      addMessage('Connection closed', 'info');
    };
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  };

  const handleMessage = (data) => {
    addMessage(JSON.stringify(data, null, 2), data.type);

    switch (data.type) {
      case 'session.start':
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const topicToSend = topicRef.current || topic;
          if (topicToSend) {
            wsRef.current.send(JSON.stringify({ topic: topicToSend }));
            addMessage(`Sent topic: ${topicToSend}`, 'info');
          } else {
            addMessage('Error: No topic available to send', 'error');
          }
        }
        break;

      case 'tutor.step':
        setSteps(prev => [...prev, data.data]);
        if (data.data.step_number === 5) {
          setIsLoading(true);
        }
        break;

      case 'assessment.ready':
        setIsLoading(false);
        setCurrentAssessment(data.data.assessment);
        setAssessmentIdForRetake(data.data.assessment.id); // Store ID for retake
        break;

      case 'tutor.complete':
        setIsLoading(false);
        addMessage(data.data.message, 'info');
        break;

      case 'error':
        addMessage(`Error: ${data.data.message}`, 'error');
        break;

      default:
        break;
    }
  };

  const addMessage = (message, type = 'info') => {
    setMessages(prev => [...prev, { message, type, timestamp: new Date() }]);
  };

  const submitAssessment = async (answers) => {
    if (!currentAssessment) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/assessments/${currentAssessment.id}/submit`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            assessment_id: currentAssessment.id,
            answers: answers,
          }),
        }
      );

      const result = await response.json();
      setGradeReport(result.grade_report);
      if (currentAssessment && currentAssessment.id) {
        setAssessmentIdForRetake(currentAssessment.id);
      }
    } catch (error) {
      addMessage(`Error submitting assessment: ${error.message}`, 'error');
    }
  };

  const handleRetake = async (assessmentId, generateNew) => {
    try {
      const response = await fetch(
        'http://localhost:8000/api/assessments/retake',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            assessment_id: assessmentId,
            generate_new: generateNew,
          }),
        }
      );

      const result = await response.json();
      
      if (result.assessment) {
        setCurrentAssessment(result.assessment);
        setAssessmentIdForRetake(result.assessment.id);
        setGradeReport(null);
        setRetakeKey(prev => prev + 1);
        
        addMessage(
          generateNew 
            ? '✨ New assessment generated with fresh questions! Good luck!' 
            : '🔄 Same assessment loaded. Review the teaching steps before retaking.',
          'info'
        );
        
        if (generateNew && result.remediation_steps) {
          addMessage(
            `💡 Tip: Review teaching steps ${result.remediation_steps.join(', ')} before retaking.`,
            'info'
          );
        }
      } else {
        throw new Error(result.message || 'Failed to retake assessment');
      }
    } catch (error) {
      addMessage(`Error retaking assessment: ${error.message}`, 'error');
      throw error;
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'connection':
        return (
          <ConnectionPanel
            connected={connected}
            onConnect={connect}
            onDisconnect={disconnect}
          />
        );
      case 'teaching':
        return <TeachingSteps steps={steps} isLoading={isLoading && steps.length === 5} />;
      case 'assessment':
        return (
          <Assessment
            key={`assessment-${currentAssessment?.id || 'none'}-${gradeReport ? 'graded' : 'active'}-${retakeKey}`}
            assessment={currentAssessment}
            gradeReport={gradeReport}
            onSubmit={submitAssessment}
            onRetake={handleRetake}
            assessmentId={assessmentIdForRetake || currentAssessment?.id}
          />
        );
      case 'messages':
        return <Messages messages={messages} />;
      default:
        return null;
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🎓 LangGraph Tutor</h1>
        <p>Real-time AI-powered learning platform</p>
      </header>

      <div className="app-container">
        <div className="tabs-wrapper">
          <Tabs activeTab={activeTab} onTabChange={setActiveTab} tabs={tabs} />
          <div className="tab-content">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

