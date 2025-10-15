from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.transcribe import router as transcribe_router
import os
from dotenv import load_dotenv

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

app = FastAPI(title="FastAPI Gemini Transcriber")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(transcribe_router)
