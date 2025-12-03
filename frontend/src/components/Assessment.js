import React, { useState, useEffect } from 'react';
import './Assessment.css';

function Assessment({ assessment, gradeReport, onSubmit, onRetake, assessmentId }) {
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [retaking, setRetaking] = useState(false);
  const [retakeCounter, setRetakeCounter] = useState(0);

  useEffect(() => {
    if (assessment && assessment.id && !gradeReport) {
      setAnswers({});
      setSubmitted(false);
      setRetaking(false);
    }
  }, [assessment?.id, gradeReport, retakeCounter]);

  if (!assessment && !gradeReport) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>📝 Assessment</h2>
        </div>
        <div className="card-body">
          <div style={{ 
            textAlign: 'center', 
            padding: '60px 40px',
            color: '#718096',
            fontSize: '1.1rem'
          }}>
            <div style={{ fontSize: '4rem', marginBottom: '20px', opacity: 0.5 }}>📋</div>
            <p style={{ fontWeight: 500, marginBottom: '10px' }}>Assessment will appear here</p>
            <p style={{ fontSize: '0.95rem', opacity: 0.8 }}>Complete the teaching steps to generate your assessment</p>
          </div>
        </div>
      </div>
    );
  }

  const handleRetake = async (generateNew = false) => {
    const idToUse = assessmentId || (assessment && assessment.id);
    if (!idToUse || !onRetake) {
      alert('Cannot retake assessment. Please try again.');
      return;
    }
    
    setRetaking(true);
    setAnswers({});
    setSubmitted(false);
    setRetakeCounter(prev => prev + 1);
    
    try {
      await onRetake(idToUse, generateNew);
    } catch (error) {
      alert('Failed to retake assessment. Please try again.');
    } finally {
      setRetaking(false);
    }
  };

  if (gradeReport) {
    const passed = gradeReport.passed;
    return (
      <div className="card">
        <div className="card-header">
          <h2>📊 Grade Report</h2>
        </div>
        <div className="card-body">
        <div className={`grade-header ${passed ? 'passed' : 'failed'}`}>
          <h3>{passed ? '✅ PASSED' : '❌ FAILED'}</h3>
          <div className="score-display">
            <span className="score">
              {gradeReport.total_score.toFixed(1)}/{gradeReport.max_score}
            </span>
            <span className="percentage">
              {(gradeReport.percentage * 100).toFixed(1)}%
            </span>
          </div>
        </div>
        
        <div className="feedback">
          <p>{gradeReport.feedback}</p>
        </div>

        <div className="question-grades">
          <h4>Question Details:</h4>
          {gradeReport.question_grades.map((qg, idx) => (
            <div key={idx} className="question-grade">
              <div className="question-grade-header">
                <span>Question {idx + 1}</span>
                <span className={qg.is_correct ? 'correct' : 'incorrect'}>
                  {qg.is_correct ? '✓' : '✗'} {qg.score.toFixed(1)}/{qg.max_score}
                </span>
              </div>
              <p className="question-feedback">{qg.feedback}</p>
            </div>
          ))}
        </div>

        <div className="retake-section">
          <h4>Retake Assessment</h4>
          <p style={{ color: '#718096', marginBottom: '15px' }}>
            {passed 
              ? 'Want to improve your score? You can retake the assessment.'
              : 'You can retake the assessment to improve your score. Review the teaching steps first for better results.'}
          </p>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              className="button button-secondary"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleRetake(false);
              }}
              disabled={retaking || !assessmentId}
              style={{ flex: '1', minWidth: '150px', cursor: (!assessmentId || retaking) ? 'not-allowed' : 'pointer' }}
            >
              {retaking ? 'Retaking...' : '🔄 Retake Same Assessment'}
            </button>
            <button
              className="button button-primary"
              onClick={() => handleRetake(true)}
              disabled={retaking}
              style={{ flex: '1', minWidth: '150px' }}
            >
              {retaking ? 'Generating...' : '✨ Retake New Assessment'}
            </button>
          </div>
        </div>
        </div>
      </div>
    );
  }

  const handleAnswerChange = (questionId, answer) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = () => {
    const answerArray = Object.entries(answers).map(([questionId, answer]) => ({
      question_id: questionId,
      answer: answer,
    }));

    if (answerArray.length !== assessment.questions.length) {
      alert('Please answer all questions');
      return;
    }

    onSubmit(answerArray);
    setSubmitted(true);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>📝 Assessment: {assessment.topic}</h2>
      </div>
      <div className="card-body">
        <div className="assessment-info">
          <p><strong>Total Points:</strong> {assessment.total_points}</p>
          <p><strong>Pass Threshold:</strong> {(assessment.pass_threshold * 100).toFixed(0)}%</p>
          <p><strong>Questions:</strong> {assessment.questions.length}</p>
        </div>

      <div className="questions-container">
        {assessment.questions.map((q, index) => (
          <div key={`${assessment.id}-${q.id}`} className="question-card">
            <div className="question-header">
              <span className="question-number">Question {index + 1}</span>
              <span className="question-points">{q.points} points</span>
            </div>
            <p className="question-text">{q.question}</p>
            
            {q.type === 'mcq' && q.options ? (
              <div className="options-container">
                {q.options.map((option, optIdx) => (
                  <label key={`${assessment.id}-${q.id}-${optIdx}`} className="option-label">
                    <input
                      type="radio"
                      name={`${assessment.id}-${q.id}-${retakeCounter}`}
                      value={option}
                      checked={answers[q.id] === option}
                      onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                      disabled={submitted || retaking}
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            ) : (
              <textarea
                key={`${assessment.id}-${q.id}-textarea-${retakeCounter}`}
                className="answer-textarea"
                value={answers[q.id] || ''}
                onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                placeholder="Enter your answer here..."
                disabled={submitted || retaking}
                rows={4}
              />
            )}
          </div>
        ))}
      </div>

      {!submitted && !retaking && (
        <button
          className="button button-primary"
          onClick={handleSubmit}
          style={{ marginTop: '20px', width: '100%' }}
        >
          Submit Assessment
        </button>
      )}
      </div>
    </div>
  );
}

export default Assessment;

