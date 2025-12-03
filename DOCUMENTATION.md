# Documentation

This is the detailed technical documentation. If you just want to get started, check out the README. This doc is for understanding how everything works under the hood.

## Architecture

The system has a few main pieces:

- **FastAPI server** - Handles HTTP requests and WebSocket connections
- **LangGraph agent** - Orchestrates the teaching flow (the brain)
- **Assessment generator** - Creates quizzes using GPT-4
- **Grader** - Scores your answers

Here's how they talk to each other:

```
Client (Browser/App)
    ↓ WebSocket + HTTP
FastAPI Server
    ├─→ LangGraph Agent (does the teaching)
    │       └─→ Assessment Generator (makes quizzes)
    └─→ Grader (scores answers)
```

The FastAPI server is the main entry point. It accepts WebSocket connections, receives topics, and coordinates everything. The LangGraph agent handles the teaching flow - it uses GPT-4 to generate content step by step, then triggers the assessment generator when done. The grader is separate - it just takes your answers and scores them.

### Components

**FastAPI Server (`app/main.py`)**
- Handles WebSocket connections
- Manages REST endpoints
- Keeps track of sessions and assessments (in memory for now)
- Coordinates between the agent, grader, and assessment generator

**LangGraph Agent (`app/agent.py`)**
- Runs the 5-step teaching flow
- Uses GPT-4 to generate teaching content
- Manages state (what step we're on, what's been completed)
- Triggers assessment generation after step 5

**Assessment Generator (`app/assessment_generator.py`)**
- Takes a topic and teaching content
- Uses GPT-4 to generate questions dynamically
- Creates MCQ questions based on what was actually taught
- Returns a complete assessment object

**Grader (`app/grader.py`)**
- Takes your answers and the assessment
- Scores each question based on type
- Calculates pass/fail
- Provides feedback

## User Flow

Here's what happens when you use the system:

1. You connect via WebSocket and send a topic
2. Server sends back "session started"
3. LangGraph agent starts teaching - streams 5 steps one by one
4. After step 5, agent triggers assessment generation
5. Assessment appears in your UI
6. You answer the questions and submit
7. Grader scores your answers
8. You see your grade and can retake if needed


## API & WebSocket Specs

### WebSocket Endpoint

**URL**: `ws://localhost:8000/ws/{session_id}`

The `session_id` can be anything - it's just used to identify your session. Use something unique like `user-123` or `session-abc`.

**Connection flow:**

1. Connect to the WebSocket
2. Server immediately sends you a `session.start` message
3. You send `{"topic": "Your Topic Here"}`
4. Server streams back teaching steps
5. Server sends assessment when ready

### WebSocket Messages

#### session.start

Sent right after you connect. Just tells you the session started.

```json
{
  "type": "session.start",
  "data": {
    "session_id": "your-session-id",
    "message": "Session started. Please send topic to begin teaching."
  },
  "timestamp": "2024-12-02T15:40:00Z"
}
```

#### tutor.step

Each teaching step comes through as one of these. You'll get 5 of them.

```json
{
  "type": "tutor.step",
  "data": {
    "step_number": 1,
    "title": "Step 1: Introduction to Python Functions",
    "content": "Functions in Python are reusable blocks of code...",
    "is_complete": true
  },
  "timestamp": "2024-12-02T15:40:05Z"
}
```

The `content` field has the actual teaching material. The `step_number` goes from 1 to 5.

#### assessment.ready

Sent after all 5 steps are done. Contains the full assessment.

```json
{
  "type": "assessment.ready",
  "data": {
    "assessment": {
      "id": "assessment-uuid",
      "topic": "Python Functions",
      "questions": [
        {
          "id": "q_1",
          "type": "mcq",
          "question": "What keyword defines a function?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "expected_answer": "Option A",
          "points": 10
        }
      ],
      "total_points": 50,
      "pass_threshold": 0.7
    }
  },
  "timestamp": "2024-12-02T15:40:35Z"
}
```

Save the `assessment.id` - you'll need it to submit answers.

#### tutor.complete

Sent when everything is done. Just a completion message.

```json
{
  "type": "tutor.complete",
  "data": {
    "message": "Teaching session completed. Assessment is ready!"
  },
  "timestamp": "2024-12-02T15:40:30Z"
}
```

#### error

If something goes wrong, you'll get this.

```json
{
  "type": "error",
  "data": {
    "message": "Topic is required"
  },
  "timestamp": "2024-12-02T15:40:00Z"
}
```

Common errors:
- Topic not provided
- WebSocket connection lost
- Assessment generation failed

### REST Endpoints

#### Submit Assessment

**POST** `/api/assessments/{assessment_id}/submit`

Submit your answers. The `assessment_id` comes from the `assessment.ready` WebSocket message.

**Request:**
```json
{
  "assessment_id": "assessment-uuid",
  "answers": [
    {
      "question_id": "q_1",
      "answer": "Option A"
    },
    {
      "question_id": "q_2",
      "answer": "Option B"
    }
  ]
}
```

**Response:**
```json
{
  "assessment_id": "assessment-uuid",
  "grade_report": {
    "assessment_id": "assessment-uuid",
    "total_score": 85.0,
    "max_score": 100.0,
    "percentage": 0.85,
    "passed": true,
    "question_grades": [
      {
        "question_id": "q_1",
        "score": 10.0,
        "max_score": 10.0,
        "is_correct": true,
        "feedback": "Correct!"
      }
    ],
    "feedback": "Congratulations! You passed with 85.0%..."
  },
  "submitted_at": "2024-12-02T15:45:00Z"
}
```

**Errors:**
- `404` - Assessment not found
- `400` - Assessment ID doesn't match or invalid format

#### Get Grade Report

**GET** `/api/assessments/{assessment_id}/grade`

Get your grade report (after you've submitted).

**Response:**
```json
{
  "assessment_id": "assessment-uuid",
  "grade_report": { ... },
  "has_grade": true
}
```

If you haven't submitted yet:
```json
{
  "message": "Please submit your assessment first",
  "assessment_id": "assessment-uuid",
  "has_grade": false
}
```

#### Retake Assessment

**POST** `/api/assessments/retake`

Get a new assessment or retake the same one.

**Request:**
```json
{
  "assessment_id": "assessment-uuid",
  "generate_new": true
}
```

Set `generate_new: true` for new questions, `false` for the same ones.

**Response (new assessment):**
```json
{
  "message": "New assessment generated",
  "original_assessment_id": "old-uuid",
  "new_assessment_id": "new-uuid",
  "assessment": { ... },
  "remediation_steps": [1, 2, 3, 4, 5]
}
```

**Response (same assessment):**
```json
{
  "message": "Retake with same assessment",
  "assessment_id": "assessment-uuid",
  "assessment": { ... },
  "remediation_steps": [1, 2, 3, 4, 5],
  "guidance": "Please review the teaching steps before retaking."
}
```

#### Get Session Info

**GET** `/api/sessions/{session_id}`

Get info about a session (what topic, what steps were completed, etc.).

**Response:**
```json
{
  "topic": "Python Functions",
  "started_at": "2024-12-02T15:40:00Z",
  "steps_completed": [ ... ],
  "assessment": "assessment-uuid"
}
```

#### Get Assessment Details

**GET** `/api/assessments/{assessment_id}`

Get the full assessment (questions, answers, etc.).

**Response:**
```json
{
  "id": "assessment-uuid",
  "topic": "Python Functions",
  "questions": [ ... ],
  "total_points": 100,
  "pass_threshold": 0.7,
  "created_at": "2024-12-02T15:40:35Z"
}
```

## LangGraph Agent

The agent is what does the teaching. It's built with LangGraph, which is basically a state machine for AI agents.

### What it does

1. Takes a topic
2. Generates 5 teaching steps using GPT-4
3. Streams them back one by one
4. After step 5, triggers assessment generation
5. Returns the assessment

### The 5 steps

The agent structures teaching into 5 steps:

1. **Introduction** - Overview, why it matters, what you'll learn
2. **Core Concepts** - The fundamentals, basic terminology
3. **Examples** - Real examples, practical use cases
4. **Advanced Topics** - Deeper stuff, edge cases, best practices
5. **Summary** - Recap, practice tips, prep for assessment

Each step builds on the previous ones. GPT-4 uses the conversation history to keep things coherent.

### How it works

The agent uses LangGraph's state machine. Here's the flow:

```
Start → Teach Step → Check if done → Generate Assessment → Complete
```

The state includes:
- Current step number (1-5)
- Completed steps (array of step objects)
- Topic
- Assessment status
- Messages (conversation history)

After each step, it checks: "Are we at step 5 yet?" If yes, it moves to assessment generation. If no, it continues teaching.

### Assessment generation trigger

After step 5 completes, the agent automatically calls the assessment generator. It passes:
- The topic
- All 5 teaching steps (so questions can be based on what was actually taught)
- Question count (default 5)
- Difficulty (default "medium")

The assessment generator uses GPT-4 to create questions based on the teaching content, not just the topic name. This means questions actually match what was taught.

## Assessment Generation

The assessment generator creates quizzes dynamically. No hardcoded questions - everything is generated by GPT-4.

### How it works

1. Takes the topic and teaching steps
2. Uses GPT-4 to analyze what was taught
3. Generates questions based on that content
4. Creates expected answers and grading criteria
5. Returns a complete assessment object

### Input

```python
{
    "topic": "Python Functions",
    "question_count": 5,  # 3-10, default 5
    "difficulty": "medium",  # "easy", "medium", "hard"
    "teaching_steps": [  # The 5 steps that were taught
        {
            "step_number": 1,
            "title": "...",
            "content": "..."
        },
        ...
    ]
}
```

### Output

An assessment object with:
- Unique ID
- Topic
- List of questions (each with ID, type, question text, options, expected answer, points)
- Total points
- Pass threshold (default 70%)

### Question types

Currently only **MCQ (Multiple Choice)** questions are generated. Each question has:
- 4 options
- One correct answer
- Points value (usually 10-15 per question)

The generator could support short answer and coding questions, but we're keeping it simple with just MCQ for now.

### Important detail

Questions are generated based on the **teaching steps content**, not just the topic. So if the AI teaches "Python Functions" in a specific way, the questions will match that teaching style and content. This makes assessments more relevant and fair.

## Grading Logic

The grader scores your answers and determines pass/fail.

### MCQ Grading

Simple - exact match or not.

- Your answer matches expected answer exactly → Full points
- Doesn't match → Zero points

Example:
- Expected: "Option A"
- You answer "Option A" → 10/10 points
- You answer "Option B" → 0/10 points

### Short Answer Grading (if implemented)

Uses keyword matching:

- Answer contains all keywords → Full points
- Answer contains 50-99% of keywords → 70% of points
- Answer contains less than 50% → 30% of points

Example:
- Keywords: ["function", "reusable", "code"]
- Your answer has all 3 → 15/15 points
- Your answer has 2 → 10.5/15 points
- Your answer has 1 → 4.5/15 points

### Coding Grading (if implemented)

Uses a rubric:

- Function/class defined → 40%
- Has implementation → 30%
- Good structure → 30%

Also checks for syntax errors - if code doesn't compile, you get zero.

### Pass/Fail

Default threshold is 70%. So:
- Score ≥ 70% → Pass
- Score < 70% → Fail

You can configure this per assessment if needed.

### Remediation

When you get a question wrong, the system suggests which teaching steps to review. For example:
- Question 1 wrong → Review steps 1, 2
- Question 3 wrong → Review steps 3, 4, 5

These remediation steps are included in the grade report so you know what to study.

## Sample Topic & Assessment

Let's walk through a real example.

### Topic: Python Functions

#### Step 1: Introduction
Functions in Python are reusable blocks of code that perform specific tasks. They help organize code, reduce repetition, and make programs more maintainable.

#### Step 2: Core Concepts
Key concepts: function definition (`def` keyword), parameters (inputs), return values (outputs), function calls.

#### Step 3: Examples
```python
def greet(name):
    return f"Hello, {name}!"

result = greet("Alice")
print(result)  # Output: Hello, Alice!
```

#### Step 4: Advanced Topics
Default parameters, keyword arguments, `*args`, `**kwargs`, lambda functions, decorators.

#### Step 5: Summary
Functions are essential for code organization. Practice writing functions for common tasks.

### Sample Assessment

After these 5 steps, you might get questions like:

**Question 1 (MCQ - 10 points)**
What keyword is used to define a function in Python?
- A) `function`
- B) `def`
- C) `func`
- D) `define`

Correct answer: B) `def`

**Question 2 (MCQ - 10 points)**
What does a function return if no return statement is specified?
- A) `None`
- B) `0`
- C) `False`
- D) Error

Correct answer: A) `None`

And so on for 5 questions total.

### Scoring Example

Perfect score:
- Q1: 10/10 ✓
- Q2: 10/10 ✓
- Q3: 10/10 ✓
- Q4: 10/10 ✓
- Q5: 10/10 ✓
- **Total: 50/50 (100%) → PASS**

Partial score:
- Q1: 10/10 ✓
- Q2: 0/10 ✗
- Q3: 10/10 ✓
- Q4: 0/10 ✗
- Q5: 10/10 ✓
- **Total: 30/50 (60%) → FAIL**

The grade report would tell you which questions you got wrong and suggest reviewing steps 2 and 4.

## Retake Logic

If you fail (score < 70%), you can retake the assessment.

### Two options

**Option 1: New Assessment** (`generate_new: true`)
- Creates fresh questions
- Same topic, same difficulty
- Different question IDs and content
- Good if you want to test your knowledge again

**Option 2: Same Assessment** (`generate_new: false`)
- Returns the original questions
- Same questions and answers
- Good for practice - you can review and retry

### How it works

1. You fail an assessment
2. System shows your grade with remediation steps
3. You review the teaching steps (especially the ones you got wrong)
4. You request a retake via `/api/assessments/retake`
5. System gives you new or same assessment
6. You take it again
7. Get graded again

You can retake as many times as you want. Each retake with `generate_new: true` gives you different questions.

### Remediation guidance

When you retake, the system tells you which steps to review:

```json
{
  "remediation_steps": [1, 2, 3],
  "guidance": "Please review the teaching steps before retaking. Focus on steps 1, 2, and 3."
}
```

This helps you study the right material before retaking.

## Testing

If you want to test the system, here's how:

### Manual testing

1. Start the server
2. Connect via WebSocket
3. Send a topic
4. Verify you get 5 steps
5. Verify assessment appears
6. Submit answers
7. Check grading works
8. Test retake flow

### Unit tests (if you write them)

Test each component separately:
- Agent: Does it generate 5 steps? Does it trigger assessment?
- Grader: Does it score correctly? Does pass/fail work?
- Assessment generator: Does it create valid questions?

### Integration tests

Test the full flow:
- WebSocket connection → teaching → assessment → grading
- REST API endpoints
- Error handling

### Edge cases to test

- Empty topic
- Very long topic names
- Invalid assessment IDs
- Missing answers
- WebSocket disconnection mid-stream

## Deployment

### What you need

- Python 3.9+
- OpenAI API key
- A server to run it on

### Environment variables

Set `OPENAI_API_KEY` in your environment or `.env` file.

### Running in production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or use a process manager like systemd, supervisor, or PM2.

### Things to consider

**Current limitations:**
- Sessions and assessments stored in memory (lost on restart)
- No authentication
- No rate limiting
- Single server (no scaling)

**For production, you'd want:**
- Database for persistence (PostgreSQL, MongoDB, etc.)
- Authentication/authorization
- Rate limiting
- Redis for WebSocket connection management
- Proper logging and monitoring
- Health check endpoints
- Load balancing if scaling

But for now, the in-memory storage works fine for development and small deployments.

## That's it

This covers the main technical details. If you have questions or want to extend the system, the code is pretty straightforward - just read through `app/main.py`, `app/agent.py`, etc.

The system is designed to be simple and extensible. Want to add a new question type? Modify the assessment generator. Want different grading logic? Change the grader. Want more teaching steps? Update the agent.

Good luck!
