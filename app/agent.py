import os
from typing import Annotated, Literal, TypedDict, Any
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

from app.models import TutorStep
from app.assessment_generator import AssessmentGenerator

load_dotenv()


class AgentState(TypedDict):
    """State for LangGraph agent."""
    messages: Annotated[list, add_messages]
    topic: str
    current_step: int
    steps_completed: list
    assessment_generated: bool
    assessment: dict | None
    session_id: str


class TutorAgent:
    """LangGraph-based tutor agent that teaches in 5 steps."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            api_key=SecretStr(api_key) if api_key else None
        )
        self.assessment_generator = AssessmentGenerator()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Any:
        workflow = StateGraph(AgentState)
        
        workflow.add_node("teach_step", self._teach_step)
        workflow.add_node("check_completion", self._check_completion)
        workflow.add_node("generate_assessment", self._generate_assessment_tool)
        workflow.add_node("complete", self._complete_session)
        
        workflow.set_entry_point("teach_step")
        workflow.add_conditional_edges(
            "teach_step",
            self._should_continue,
            {"continue": "teach_step", "check": "check_completion"}
        )
        workflow.add_conditional_edges(
            "check_completion",
            self._should_generate_assessment,
            {"generate": "generate_assessment", "complete": "complete"}
        )
        workflow.add_edge("generate_assessment", "complete")
        workflow.add_edge("complete", END)
        
        return workflow.compile()
    
    def _teach_step(self, state: AgentState) -> AgentState:
        current_step = state.get("current_step", 0)
        topic = state.get("topic", "")
        
        if current_step >= 5:
            return state
        
        step_number = current_step + 1
        system_prompt = (
            f"You are a helpful tutor teaching the topic: {topic}. "
            f"You are currently on step {step_number} of 5. "
            "Each step should build on the previous ones and be clear and concise. "
            "Provide educational content that progressively teaches the topic."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Provide step {step_number} of teaching {topic}. "
                                f"Make it clear, educational, and build on previous steps.")
        ]
        
        response = self.llm.invoke(messages)
        step_content = response.content
        if isinstance(step_content, list):
            step_content = " ".join(str(item) for item in step_content)
        elif not isinstance(step_content, str):
            step_content = str(step_content)
        
        tutor_step = TutorStep(
            step_number=step_number,
            title=f"Step {step_number}: Introduction to {topic}",
            content=step_content,
            is_complete=True
        )
        
        steps_completed = state.get("steps_completed", [])
        steps_completed.append(tutor_step.model_dump())
        
        return {
            **state,
            "current_step": step_number,
            "steps_completed": steps_completed,
            "messages": state.get("messages", []) + [
                {"role": "assistant", "content": step_content, "step": step_number}
            ]
        }
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "check"]:
        return "continue" if state.get("current_step", 0) < 5 else "check"
    
    def _check_completion(self, state: AgentState) -> AgentState:
        return state
    
    def _should_generate_assessment(self, state: AgentState) -> Literal["generate", "complete"]:
        return "generate" if not state.get("assessment_generated", False) else "complete"
    
    def _generate_assessment_tool(self, state: AgentState) -> AgentState:
        from app.models import AssessmentGenerationRequest
        
        request = AssessmentGenerationRequest(
            topic=state.get("topic", ""),
            question_count=5,
            difficulty="medium",
            teaching_steps=state.get("steps_completed", [])
        )
        
        assessment = self.assessment_generator.generate_assessment(request)
        
        return {
            **state,
            "assessment_generated": True,
            "assessment": assessment.model_dump(mode='json'),
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": f"Assessment generated for {state.get('topic', '')} with {len(assessment.questions)} questions.",
                "type": "assessment_ready"
            }]
        }
    
    def _complete_session(self, state: AgentState) -> AgentState:
        return {
            **state,
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": "Teaching session completed. Assessment is ready!",
                "type": "tutor_complete"
            }]
        }
    
    async def stream_teaching(self, topic: str, session_id: str):
        initial_state: AgentState = {
            "messages": [],
            "topic": topic,
            "current_step": 0,
            "steps_completed": [],
            "assessment_generated": False,
            "assessment": None,
            "session_id": session_id
        }
        
        last_step_count = 0
        
        async for state_update in self.graph.astream(initial_state):
            for node_name, node_state in state_update.items():
                if node_name == "teach_step":
                    steps_completed = node_state.get("steps_completed", [])
                    if len(steps_completed) > last_step_count:
                        for step in steps_completed[last_step_count:]:
                            yield {
                                "type": "tutor.step",
                                "data": {
                                    "step_number": step["step_number"],
                                    "title": step["title"],
                                    "content": step["content"],
                                    "is_complete": step.get("is_complete", True)
                                }
                            }
                        last_step_count = len(steps_completed)
                
                elif node_name == "generate_assessment":
                    assessment = node_state.get("assessment")
                    if assessment:
                        yield {
                            "type": "assessment.ready",
                            "data": {"assessment": assessment}
                        }
                
                elif node_name == "complete":
                    yield {
                        "type": "tutor.complete",
                        "data": {"message": "Teaching session completed!"}
                    }

