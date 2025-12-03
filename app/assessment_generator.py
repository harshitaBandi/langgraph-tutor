import json
import uuid
import os
import random
from typing import List, Dict, Any, Optional
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from app.models import Assessment, Question, QuestionType, AssessmentGenerationRequest

load_dotenv()


def _ensure_string_content(content) -> str:
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    elif not isinstance(content, str):
        return str(content)
    return content


class AssessmentGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.9,
            api_key=SecretStr(api_key) if api_key else None
        )
    
    def generate_assessment(self, request: AssessmentGenerationRequest) -> Assessment:
        teaching_content = self._prepare_teaching_content(request.topic, request.teaching_steps)
        
        questions = self._generate_mcq_with_llm(
            request.topic,
            teaching_content,
            1,
            request.question_count,
            request.difficulty
        )
        
        return Assessment(
            id=str(uuid.uuid4()),
            topic=request.topic,
            questions=questions,
            total_points=sum(q.points for q in questions),
            pass_threshold=0.7
        )
    
    def _prepare_teaching_content(self, topic: str, teaching_steps: Optional[List[Dict[str, Any]]]) -> str:
        if not teaching_steps:
            return f"Topic: {topic}"
        
        content_parts = [f"Topic: {topic}\n\nTeaching Content:\n"]
        for step in teaching_steps:
            step_num = step.get("step_number", 0)
            title = step.get("title", "")
            content = step.get("content", "")
            content_parts.append(f"Step {step_num}: {title}\n{content}\n")
        
        return "\n".join(content_parts)
    
    def _generate_mcq_with_llm(
        self, topic: str, teaching_content: str, start_id: int, count: int, difficulty: str
    ) -> List[Question]:
        variation_hints = [
            "Focus on different aspects and perspectives",
            "Ask questions that test deeper understanding",
            "Create questions that require application of concepts",
            "Generate questions covering various subtopics",
            "Focus on practical applications and examples"
        ]
        variation = random.choice(variation_hints)
        
        prompt = f"""Generate {count} multiple choice question(s) based on the following teaching content at {difficulty} difficulty level.

TEACHING CONTENT:
{teaching_content}

CRITICAL REQUIREMENTS:
- Questions MUST be based ONLY on the teaching content provided above
- Questions should test understanding of concepts, facts, and information that were actually taught
- Do NOT ask about things not covered in the teaching content
- All options should be plausible but only one should be correct
- Questions should cover different aspects from the teaching steps
- IMPORTANT: {variation} - generate FRESH, UNIQUE questions different from previous assessments

For each question, provide:
1. A clear, specific question that tests understanding of the teaching content
2. 4 options (A, B, C, D) where only one is correct
3. The correct answer (specify which option)
4. Points value (10-15 points per question)

Return as JSON array with this structure:
[
  {{
    "question": "Question text here - must be based on the teaching content",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "correct_answer": "Option A text",
    "points": 10
  }}
]

Make questions relevant to what was actually taught and appropriate for {difficulty} level. Generate NEW, DIFFERENT questions that haven't been asked before."""

        messages = [
            SystemMessage(content="You are an expert educator creating assessment questions. Always return valid JSON."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        content = _ensure_string_content(response.content).strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            questions_data = json.loads(content)
            questions = []
            for idx, q_data in enumerate(questions_data):
                questions.append(Question(
                    id=f"q_{start_id + idx}",
                    type=QuestionType.MCQ,
                    question=q_data["question"],
                    options=q_data["options"],
                    expected_answer=q_data["correct_answer"],
                    points=q_data.get("points", 10),
                    keywords=None
                ))
            return questions
        except json.JSONDecodeError:
            return [self._create_fallback_mcq(topic, teaching_content, start_id)]
    
    def _create_fallback_mcq(self, topic: str, teaching_content: str, q_id: int) -> Question:
        try:
            prompt = f"""Generate ONE multiple choice question based on this teaching content. Return JSON:
{teaching_content}

{{
  "question": "Question based on teaching content",
  "options": ["A", "B", "C", "D"],
  "correct_answer": "A",
  "points": 10
}}"""
            messages = [
                SystemMessage(content="Return valid JSON only."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            content = _ensure_string_content(response.content).strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            q_data = json.loads(content)
            return Question(
                id=f"q_{q_id}",
                type=QuestionType.MCQ,
                question=q_data["question"],
                options=q_data["options"],
                expected_answer=q_data["correct_answer"],
                points=q_data.get("points", 10),
                keywords=None
            )
        except Exception:
            return Question(
                id=f"q_{q_id}",
                type=QuestionType.MCQ,
                question=f"What is an important aspect of {topic}?",
                options=["A relevant concept", "An unrelated concept", "Another unrelated concept", "Yet another unrelated concept"],
                expected_answer="A relevant concept",
                points=10,
                keywords=None
            )

