import shutil
import os
import sys
from http.client import HTTPException

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from audio_operations import loop_audio
from fastapi.responses import FileResponse, StreamingResponse
from pydub import AudioSegment
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://localhost:5173",  # local React.js server
    "https://audio-app-phi.vercel.app" # Vercel hosted frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins
)

@app.get("/")
def welcome():
    return "Hello World!"

input_path = ""
output_path = ""

@app.post("/convert_audio")
async def convert_audio(hours: int, file: UploadFile):
    # Clearing the old files before beginning a new conversion
    await clear_old_files()
    try:
        global input_path, output_path

        input_path = f"static/temp_{file.filename}"
        output_path = f"static/looped_{file.filename}"

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        audio_file = AudioSegment.from_file(input_path)
        looped_audio, file_type, export_format = loop_audio(audio_file, file.filename, hours)
        looped_audio.export(output_path, format="mp3") # input_path[-3:]

        return FileResponse(output_path, media_type="audio/mp3", filename=output_path)
        # return StreamingResponse(output_path, media_type="audio/mpeg")
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise Exception(str(e))

async def clear_old_files():
    try:
        global input_path, output_path
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        input_path, output_path = "", ""
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise Exception(str(e))