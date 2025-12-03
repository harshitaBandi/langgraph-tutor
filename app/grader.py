from typing import List
from app.models import Assessment, Question, QuestionGrade, GradeReport, AssessmentSubmission, QuestionType


class Grader:
    def grade_assessment(self, assessment: Assessment, submission: AssessmentSubmission) -> GradeReport:
        question_grades = []
        answer_map = {a.question_id: a.answer for a in submission.answers}
        total_score = 0.0
        max_score = float(assessment.total_points)
        
        for question in assessment.questions:
            answer = answer_map.get(question.id, "")
            grade = self._grade_question(question, answer)
            question_grades.append(grade)
            total_score += grade.score
        
        percentage = (total_score / max_score) if max_score > 0 else 0.0
        passed = percentage >= assessment.pass_threshold
        
        return GradeReport(
            assessment_id=assessment.id,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            passed=passed,
            question_grades=question_grades,
            feedback=self._generate_feedback(question_grades, passed, percentage)
        )
    
    def _grade_question(self, question: Question, answer: str) -> QuestionGrade:
        answer = answer.strip()
        
        if question.type == QuestionType.MCQ:
            return self._grade_mcq(question, answer)
        elif question.type == QuestionType.SHORT_ANSWER:
            return self._grade_short_answer(question, answer)
        elif question.type == QuestionType.CODING:
            return self._grade_coding(question, answer)
        
        return QuestionGrade(
            question_id=question.id,
            score=0.0,
            max_score=float(question.points),
            is_correct=False,
            feedback="Unknown question type"
        )
    
    def _grade_mcq(self, question: Question, answer: str) -> QuestionGrade:
        is_correct = answer.lower().strip() == question.expected_answer.lower().strip()
        score = float(question.points) if is_correct else 0.0
        
        return QuestionGrade(
            question_id=question.id,
            score=score,
            max_score=float(question.points),
            is_correct=is_correct,
            feedback="Correct!" if is_correct else f"Incorrect. The correct answer is: {question.expected_answer}",
            remediation_steps=None if is_correct else [1, 2]
        )
    
    def _grade_short_answer(self, question: Question, answer: str) -> QuestionGrade:
        if not answer:
            return QuestionGrade(
                question_id=question.id,
                score=0.0,
                max_score=float(question.points),
                is_correct=False,
                feedback="No answer provided",
                remediation_steps=[3, 4]
            )
        
        answer_lower = answer.lower()
        keywords = [k.lower() for k in (question.keywords or [])]
        matched_keywords = sum(1 for keyword in keywords if keyword in answer_lower)
        total_keywords = len(keywords) if keywords else 1
        
        if matched_keywords == total_keywords:
            score = float(question.points)
            is_correct = True
            feedback = "Excellent answer! All key concepts covered."
        elif matched_keywords >= total_keywords * 0.5:
            score = float(question.points) * 0.7
            is_correct = False
            feedback = f"Good attempt! You covered {matched_keywords}/{total_keywords} key concepts. Consider including more details."
        else:
            score = float(question.points) * 0.3
            is_correct = False
            feedback = "Your answer is partially correct but missing key concepts. Consider revisiting the teaching steps."
        
        return QuestionGrade(
            question_id=question.id,
            score=score,
            max_score=float(question.points),
            is_correct=is_correct,
            feedback=feedback,
            remediation_steps=None if is_correct else [3, 4, 5]
        )
    
    def _grade_coding(self, question: Question, answer: str) -> QuestionGrade:
        if not answer:
            return QuestionGrade(
                question_id=question.id,
                score=0.0,
                max_score=float(question.points),
                is_correct=False,
                feedback="No code provided",
                remediation_steps=[4, 5]
            )
        
        try:
            compile(answer, "<string>", "exec")
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        
        if not syntax_valid:
            return QuestionGrade(
                question_id=question.id,
                score=0.0,
                max_score=float(question.points),
                is_correct=False,
                feedback="Code has syntax errors. Please fix and resubmit.",
                remediation_steps=[4, 5]
            )
        
        rubric_score = 0.0
        if "def" in answer or "class" in answer:
            rubric_score += 0.4
        if any(keyword in answer.lower() for keyword in ["return", "print", "pass"]):
            rubric_score += 0.3
        if len(answer.split("\n")) > 3:
            rubric_score += 0.3
        
        score = float(question.points) * rubric_score
        is_correct = rubric_score >= 0.8
        
        return QuestionGrade(
            question_id=question.id,
            score=score,
            max_score=float(question.points),
            is_correct=is_correct,
            feedback="Great code! It follows best practices and demonstrates the concept well." if is_correct else f"Your code is on the right track but could be improved. Score: {rubric_score*100:.0f}% based on rubric criteria.",
            remediation_steps=None if is_correct else [4, 5]
        )
    
    def _generate_feedback(self, question_grades: List[QuestionGrade], passed: bool, percentage: float) -> str:
        correct_count = sum(1 for g in question_grades if g.is_correct)
        total_questions = len(question_grades)
        
        if passed:
            return f"Congratulations! You passed with {percentage*100:.1f}%. You answered {correct_count}/{total_questions} questions correctly. Great work on mastering this topic!"
        
        failed_questions = [g for g in question_grades if not g.is_correct]
        remediation_steps = set()
        for g in failed_questions:
            if g.remediation_steps:
                remediation_steps.update(g.remediation_steps)
        
        remediation_text = f"Consider revisiting steps: {', '.join(map(str, sorted(remediation_steps)))}" if remediation_steps else "Please review the teaching material."
        
        return f"You scored {percentage*100:.1f}% but did not meet the passing threshold. You answered {correct_count}/{total_questions} questions correctly. {remediation_text} You can retake the assessment after reviewing."

