import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv("HOST")

if __name__ == "__main__":
    uvicorn.run("app:app", host=HOST, port=8080, reload=True)
# localhost: 127.0.0.1
# online deployment: 0.0.0.0"