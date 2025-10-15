from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.audio_processor import process_audio_file

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        result = await process_audio_file(audio_bytes)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})
