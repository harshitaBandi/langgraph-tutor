#!/usr/bin/env python3
import uvicorn
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("📝 Please create a .env file with your OPENAI_API_KEY")
        print("   Example: OPENAI_API_KEY=your_key_here\n")
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("=" * 60)
    print("🚀 Starting LangGraph Tutor Application")
    print("=" * 60)
    print(f"📡 Server: http://{host}:{port}")
    print(f"🌐 React Frontend: http://localhost:3000")
    print(f"🔌 WebSocket: ws://localhost:{port}/ws/{{session_id}}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    uvicorn.run("app.main:app", host=host, port=port, reload=reload, log_level="info")

