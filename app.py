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

from dotenv import load_dotenv
import boto3

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "https://audio-app-phi.vercel.app" # Vercel hosted frontend
    # "http://localhost:5173" local React.js server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
ENDPOINT_PASSWORD = os.getenv("ENDPOINT_PASSWORD")
ENDPOINT_REGION = os.getenv("ENDPOINT_REGION")
bucket_name = os.getenv("BUCKET_NAME")

s3 = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id='minio',
    aws_secret_access_key=ENDPOINT_PASSWORD,
    region_name=ENDPOINT_REGION,
)

existing_buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
if bucket_name not in existing_buckets:
    s3.create_bucket(Bucket=bucket_name)

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

        # Configuring app to export to object store
        looped_audio.export(output_path, format="mp3") # input_path[-3:]

        s3.upload_file(output_path, bucket_name, output_path)

        # Generating a url
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': output_path},
            ExpiresIn=3600
        )

        return url
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