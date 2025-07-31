from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from llm_handlers import get_llm_response  # Must exist
import requests
import urllib.parse
import os
import json
import re
import openai
import google.generativeai as genai
import anthropic

# Initialize FastAPI app
app = FastAPI()


# Mount the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM Client Setup
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

# Request Schema
class QueryInput(BaseModel):
    query: str
    model: str  # "openai", "gemini", "claude"

# Utility: Extract entities from Northwind OData
@app.get("/northwind_entities")
def get_entities():
    service_url = "https://services.odata.org/V4/Northwind/Northwind.svc/$metadata"
    response = requests.get(service_url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch metadata")
    return {"metadata": response.text}

# MCP-style Instruction Format
def format_mcp_prompt(user_input):
    return f"""
You are an expert in constructing OData queries. Convert the user's question to a valid OData query for the Northwind service.
Response format:
{{
  "entity": "<entity>",
  "filter": "<odata_filter_expression>"
}}
User query: {user_input}
"""

# Multi-LLM Handler
def generate_with_llm(model: str, prompt: str):
    if model == "openai":
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message["content"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"openai error: {e}")

    elif model == "gemini":
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"gemini error: {e}")

    elif model == "claude":
        try:
            response = claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"claude error: {e}")

    else:
        raise HTTPException(status_code=400, detail="Invalid model")

# Main Endpoint
@app.post("/query_northwind")
def query_northwind(data: QueryInput):
    prompt = format_mcp_prompt(data.query)
    response_text = generate_with_llm(data.model, prompt)

    try:
        match = re.search(r'\{.*?\}', response_text, re.DOTALL)
        json_str = match.group(0)
        query_data = json.loads(json_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM output: {e}\n{response_text}")

    entity = query_data.get("entity")
    odata_filter = urllib.parse.quote(query_data.get("filter"))
    full_url = f"https://services.odata.org/V4/Northwind/Northwind.svc/{entity}?$filter={odata_filter}"

    response = requests.get(full_url, headers={"Accept": "application/json"})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Northwind query failed")

    return response.json()

# Health check
@app.get("/")
def root():
    return {"message": "Northwind LLM Query API is running."}
