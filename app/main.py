import json
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.models import AssessmentSubmission, RetakeRequest
from app.agent import TutorAgent
from app.grader import Grader
from app.assessment_generator import AssessmentGenerator

app = FastAPI(title="LangGraph Tutor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, dict] = {}
assessments: Dict[str, dict] = {}
grade_reports: Dict[str, dict] = {}
active_connections: Dict[str, WebSocket] = {}

tutor_agent = TutorAgent()
grader = Grader()
assessment_generator = AssessmentGenerator()


@app.get("/")
async def root():
    return {
        "message": "LangGraph Tutor API",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/{session_id}",
            "submit_assessment": "/api/assessments/{assessment_id}/submit",
            "get_grade": "/api/assessments/{assessment_id}/grade",
            "retake": "/api/assessments/retake"
        }
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        await websocket.send_json({
            "type": "session.start",
            "data": {
                "session_id": session_id,
                "message": "Session started. Please send topic to begin teaching."
            },
            "timestamp": datetime.now().isoformat()
        })
        
        topic_data = await websocket.receive_json()
        topic = topic_data.get("topic", "")
        
        if not topic:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Topic is required"},
                "timestamp": datetime.now().isoformat()
            })
            return
        
        sessions[session_id] = {
            "topic": topic,
            "started_at": datetime.now().isoformat(),
            "steps_completed": [],
            "assessment": None
        }
        
        async for message in tutor_agent.stream_teaching(topic, session_id):
            await websocket.send_json({
                **message,
                "timestamp": datetime.now().isoformat()
            })
            
            if message["type"] == "tutor.step":
                sessions[session_id]["steps_completed"].append(message["data"])
            
            if message["type"] == "assessment.ready":
                assessment_data = message["data"]["assessment"]
                assessment_id = assessment_data["id"]
                assessments[assessment_id] = assessment_data
                sessions[session_id]["assessment"] = assessment_id
        
    except WebSocketDisconnect:
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)},
            "timestamp": datetime.now().isoformat()
        })


@app.post("/api/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id: str, submission: AssessmentSubmission):
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if submission.assessment_id != assessment_id:
        raise HTTPException(status_code=400, detail="Assessment ID mismatch")
    
    from app.models import Assessment
    assessment = Assessment(**assessments[assessment_id])
    grade_report = grader.grade_assessment(assessment, submission)
    grade_reports[assessment_id] = grade_report.model_dump(mode='json')
    
    return {
        "assessment_id": assessment_id,
        "grade_report": grade_report.model_dump(mode='json'),
        "submitted_at": submission.submitted_at.isoformat()
    }


@app.get("/api/assessments/{assessment_id}/grade")
async def get_grade(assessment_id: str):
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if assessment_id not in grade_reports:
        return {
            "message": "Please submit your assessment first",
            "assessment_id": assessment_id,
            "has_grade": False
        }
    
    return {
        "assessment_id": assessment_id,
        "grade_report": grade_reports[assessment_id],
        "has_grade": True
    }


@app.post("/api/assessments/retake")
async def retake_assessment(request: RetakeRequest):
    if request.assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    original_assessment = assessments[request.assessment_id]
    
    teaching_steps = None
    for session_data in sessions.values():
        if session_data.get("assessment") == request.assessment_id:
            teaching_steps = session_data.get("steps_completed", [])
            break
    
    if request.generate_new:
        from app.models import AssessmentGenerationRequest
        gen_request = AssessmentGenerationRequest(
            topic=original_assessment["topic"],
            question_count=5,
            difficulty="medium",
            teaching_steps=teaching_steps
        )
        new_assessment = assessment_generator.generate_assessment(gen_request)
        assessments[new_assessment.id] = new_assessment.model_dump(mode='json')
        
        return {
            "message": "New assessment generated",
            "original_assessment_id": request.assessment_id,
            "new_assessment_id": new_assessment.id,
            "assessment": new_assessment.model_dump(mode='json'),
            "remediation_steps": [1, 2, 3, 4, 5]
        }
    
    return {
        "message": "Retake with same assessment",
        "assessment_id": request.assessment_id,
        "assessment": original_assessment,
        "remediation_steps": [1, 2, 3, 4, 5],
        "guidance": "Please review the teaching steps before retaking."
    }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@app.get("/api/assessments/{assessment_id}")
async def get_assessment(assessment_id: str):
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessments[assessment_id]

