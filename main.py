from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import pdfplumber
from docx import Document
import pytesseract
from io import BytesIO
import requests  # Or requests if you're calling Groq directly
import os

app = FastAPI()

class FileInput(BaseModel):
    filename: str
    filedata: str

@app.post("/process")
def process_file(input: FileInput):
    filename = input.filename
    binary = base64.b64decode(input.filedata)
    extracted_text = ""

    if filename.lower().endswith(".pdf"):
        with pdfplumber.open(BytesIO(binary)) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""
    elif filename.lower().endswith(".docx"):
        doc = Document(BytesIO(binary))
        for para in doc.paragraphs:
            extracted_text += para.text + "\n"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    prompt = f"""Extract the main insights, action points, and any important table data from the following text:\n\n{extracted_text[:8000]}"""
    response = call_groq(prompt)
    return {"insights": response}

def call_groq(prompt: str) -> str:
    import requests
    groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-saba-24b",
        "messages": [
            {"role": "system", "content": "You are a document analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    res = requests.post(groq_api_url, headers=headers, json=payload)
    if res.status_code != 200:
        raise Exception(res.text)
    return res.json()["choices"][0]["message"]["content"]
