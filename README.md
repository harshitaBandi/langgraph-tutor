# LangGraph Tutor

An AI tutoring system that teaches you stuff in 5 steps, then tests what you learned. Built with FastAPI, LangGraph, and GPT-4.

## What does it do?

You give it a topic (literally anything - "Python functions", "how photosynthesis works", "World War 2", whatever), and it:
1. Teaches you the topic in 5 easy steps (streams them in real-time)
2. Generates a quiz based on what it just taught you
3. Grades your answers and tells you what you got wrong
4. Lets you retake the quiz if you want


## Features

- **5-step teaching flow** - Breaks down topics into digestible chunks
- **Real-time streaming** - Content appears as it's generated (no waiting for everything to finish)
- **Dynamic assessments** - Questions are generated based on the actual teaching content, not hardcoded
- **Smart grading** - Tells you what you got right/wrong and why
- **Retake options** - Get new questions or review the same ones
- **UI** - React frontend that's actually usable

## What you need

- Python 3.9 or higher
- An OpenAI API key (get one at https://platform.openai.com/api-keys)
- Node.js 16+ (for the frontend)

## Getting started

### 1. Install Python stuff

First, clone or download this repo, then:

```bash
# Create a virtual environment 
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Set up your API key

Create a `.env` file in the root directory:

```bash
touch .env  # Mac/Linux
# or just create it manually on Windows
```

Put this in it:

```
OPENAI_API_KEY=sk-your-actual-key-here
```


### 3. Start the backend

```bash
python main.py
```

You should see something like:

```
============================================================
🚀 Starting LangGraph Tutor Application
============================================================
📡 Server: http://0.0.0.0:8000
🌐 React Frontend: http://localhost:3000
🔌 WebSocket: ws://localhost:8000/ws/{session_id}
📚 API Docs: http://localhost:8000/docs
============================================================
```

The server is running.

### 4. Start the frontend (optional but recommended)

Open a new terminal:

```bash
cd frontend
npm install
npm start
```

This opens http://localhost:3000 in your browser. Much easier than using the API directly.

## How to use it

### Using the web UI (easiest way)

1. Open http://localhost:3000
2. Go to the "Connection" tab
3. Enter a topic (try "Python functions" or "Machine Learning basics")
4. Click "Connect & Start Teaching"
5. Watch the "Teaching Steps" tab - 5 steps will stream in
6. When done, go to "Assessment" tab and answer the questions
7. Submit and see your grade
8. Retake if you want


### Using the API directly

If you're a developer and want to integrate this, here's how:

#### Connect via WebSocket

```python
import asyncio
import websockets
import json

async def learn():
    uri = "ws://localhost:8000/ws/my-session"
    
    async with websockets.connect(uri) as ws:
        # Get welcome message
        welcome = await ws.recv()
        print(json.loads(welcome))
        
        # Send your topic
        await ws.send(json.dumps({"topic": "Python Functions"}))
        
        # Get teaching steps
        async for msg in ws:
            data = json.loads(msg)
            print(data)

asyncio.run(learn())
```

#### Submit an assessment

```python
import requests

response = requests.post(
    "http://localhost:8000/api/assessments/YOUR_ASSESSMENT_ID/submit",
    json={
        "assessment_id": "YOUR_ASSESSMENT_ID",
        "answers": [
            {"question_id": "q_1", "answer": "Option A"},
            {"question_id": "q_2", "answer": "Option B"},
        ]
    }
)

print(response.json())
```

The assessment ID comes from the WebSocket `assessment.ready` message.

## Project structure

```
random/
├── app/                    # Backend code
│   ├── main.py            # FastAPI server
│   ├── agent.py           # LangGraph agent (does the teaching)
│   ├── models.py          # Data models
│   ├── assessment_generator.py  # Makes the quizzes
│   └── grader.py          # Grades answers
│
├── frontend/               # React app
│   └── src/
│       ├── App.js
│       └── components/    # UI components
│
├── main.py                # Entry point
├── requirements.txt       # Python deps
└── README.md             # This file
```

## API endpoints

**WebSocket:** `ws://localhost:8000/ws/{session_id}`

**REST:**
- `GET /` - API info
- `POST /api/assessments/{id}/submit` - Submit answers
- `GET /api/assessments/{id}/grade` - Get your grade
- `POST /api/assessments/retake` - Retake quiz
- `GET /api/sessions/{id}` - Session info
- `GET /api/assessments/{id}` - Assessment details

Check out http://localhost:8000/docs for interactive API docs.

## Common issues

**"Module not found"**
- Make sure your venv is activated
- Run `pip install -r requirements.txt` again

**"OPENAI_API_KEY not found"**
- Check that `.env` file exists
- Make sure it has `OPENAI_API_KEY=sk-...` (no spaces around =)
- Restart the server

**WebSocket won't connect**
- Is the server running? Check port 8000
- Try the URL: `ws://localhost:8000/ws/test-123`

**Frontend won't start**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

**Port 8000 already in use**
- Kill whatever's using it, or change the port in `main.py`

## How it works (briefly)

1. You connect via WebSocket and send a topic
2. The LangGraph agent uses GPT-4 to generate 5 teaching steps
3. Steps stream back to you in real-time
4. After step 5, it generates an assessment using the teaching content
5. You answer the questions
6. The grader scores them and gives feedback
7. You can retake if needed

The cool part is that questions are generated based on what was actually taught, not just the topic name. So if the AI teaches you about "Python functions" in a specific way, the questions will match that.

## Configuration

Default settings:
- 5 questions per assessment
- Medium difficulty
- 70% to pass
- MCQ format only


## Deployment

For production, you'll want to:

1. Deploy the backend (Railway, Render, Heroku all work)
2. Set the `OPENAI_API_KEY` environment variable
3. Build and deploy the frontend (Netlify, Vercel, etc.)
4. Update the frontend to point to your backend URL

The backend is just a FastAPI app, so standard deployment methods work. The frontend is a React app - build it with `npm run build` and deploy the `build` folder.

## Example topics

You can  teach anything:
- "Python functions"
- "How photosynthesis works"
- "World War 2"
- "Machine Learning basics"
- "REST APIs"
- "How to make pizza"

The AI adapts to whatever you give it.

## More docs

For detailed stuff (architecture, API specs, etc.), check out `DOCUMENTATION.md`. This README is just the basics to get you started.

## Tips

- Start with a simple topic to see how it works
- The UI makes everything easier - use it
- Check server logs if something's not working
- Questions are generated fresh each time, so retakes give you new questions

## That's it

Start the server, open the frontend, pick a topic, and start learning. If something breaks, check the troubleshooting section above.
