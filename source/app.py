from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import sys

# Add current directory to path explicitly
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # Insert at beginning for priority

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

# Add a query parameter endpoint for easier testing
@app.get("/api")
def read_item_query(prompt: str):
    """
        Endpoint pro zpracovani textu pomoci OpenAI API (query parameter version).
        - prompt: text, ktery chceme zpracovat
    """
    response = oapi.get_response(prompt)
    return {"response": response, 
            "output_text": response.output_text,
            }