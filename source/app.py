from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import sys

# Add the directory containing api_call.py to the Python path
# This uses the current script's directory as reference
current_dir = os.path.dirname(os.path.abspath(__file__))
# Adjust '../other_directory' to match the relative path to your api_call.py
sys.path.append(os.path.join(current_dir, './source'))

print("Python path:", sys.path)

import api_call as oapi

app = FastAPI()

origins = ["*"]

app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def read_root():
    """
        Zakldani endpoint pro testovani, zda je aplikace dostupna. Neni dulezity, ale je fajn ho mit.
    """
    return {"message": "Hello, World!"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(os.path.dirname(__file__), "favicon.ico"))

@app.get("/api/{prompt}")
def read_item(prompt: str):
    """
        Endpoint pro zpracovani textu pomoci OpenAI API.
        - prompt: text, ktery chceme zpracovat
    """
    response = oapi.get_response(prompt)
    return {"response": response, 
            "output_text": response.output_text,
            }