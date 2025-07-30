import shutil
import os
import sys

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from audio_operations import loop_audio
from pydub import AudioSegment

from dotenv import load_dotenv
import boto3

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "https://audio-app-phi.vercel.app", # Vercel hosted frontend
    "http://localhost:5173" # local React.js server
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
ENDPOINT_ID = os.getenv("ENDPOINT_ID")
ENDPOINT_PASSWORD = os.getenv("ENDPOINT_PASSWORD")
ENDPOINT_REGION = os.getenv("ENDPOINT_REGION")
bucket_name = os.getenv("BUCKET_NAME")

s3 = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ENDPOINT_ID,
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
    try:
        global input_path, output_path

        input_path = f"static/temp_{file.filename}"
        output_path = f"{file.filename}"
        # Checking the file name
        await generate_file_name(hours)
        # print(f"Output Path: {output_path}", file=sys.stderr)

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        audio_file = AudioSegment.from_file(input_path)
        looped_audio, file_type, export_format = loop_audio(audio_file, file.filename, hours)

        # Configuring app to export to object store
        #looped_audio.export(output_path, format="mp3") # input_path[-3:]

        # Uploading the AudioSegment object
        s3.upload_file(looped_audio, bucket_name, output_path)

        # Generating a url
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': output_path},
            ExpiresIn=3600
        )
        # Clearing the files after the upload is complete
        await clear_old_files()
        return url
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise HTTPException(status_code=500, detail="Audio could not be looped")

async def generate_file_name(hours: int):
    global output_path
    o = output_path.split(".")
    output_path = f"{o[0]}_looped_{hours}h.{o[-1]}"

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