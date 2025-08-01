from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from llm_handlers import generate_with_llm, format_mcp_prompt
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import os

app = FastAPI()

# Serve static files from 'static' (not 'frontend')
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html on root route
@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Your model and endpoint
class QueryRequest(BaseModel):
    query: str
    model: str = "gemini"

@app.post("/query_northwind")
async def query_northwind(data: QueryRequest):
    try:
        # Step 1: Get OData query string from LLM
        odata_query = await generate_with_llm(data.query, data.model)

        # Step 2: Compose full URL
        base_url = "https://services.odata.org/V4/Northwind/Northwind.svc/"
        full_url = f"{base_url}{odata_query}"

        # Step 3: Call Northwind API
        import requests
        response = requests.get(full_url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            raise Exception(f"❌ Northwind query failed: {response.status_code} - {response.text}")

        return { "results": response.json() }

    except Exception as e:
        return { "detail": f"❌ LLM/Northwind Query Failed: {e}" }


# Optional CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
