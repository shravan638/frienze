from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import logging

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Frienze API")

# 2. Allow your website to talk to your server (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Route to show your website
@app.get("/")
async def read_index():
    return FileResponse('index.html')

# 4. Simple Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Frienze API"}

# 5. Basic WebSocket (The "Ear" of your AI)
@app.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"🎤 Voice session started: {session_id}")
    try:
        while True:
            # This waits for voice data from the website
            data = await websocket.receive_text()
            # For now, it just echoes back so you know it works
            await websocket.send_text(f"Frienze heard: {data}")
    except WebSocketDisconnect:
        logger.info(f"🔌 Session {session_id} disconnected")

if __name__ == "__main__":
    print("🚀 Frienze is launching! Go to http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)