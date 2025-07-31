import os
import json
import httpx

# Gemini (Google AI)
async def call_gemini(prompt):
    api_key = os.getenv("AIzaSyCYPqGe52Hzz8UI1vPh7gnFDgpFUd4QWiM")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

# OpenAI
async def call_openai(prompt):
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Claude
async def call_claude(prompt):
    api_key = os.getenv("CLAUDE_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            content=json.dumps(payload)
        )
        data = response.json()
        return data["content"][0]["text"]

# Main router
async def get_llm_response(prompt, llm):
    if llm.lower() == "gemini":
        return await call_gemini(prompt)
    elif llm.lower() == "openai":
        return await call_openai(prompt)
    elif llm.lower() == "claude":
        return await call_claude(prompt)
    else:
        return f"Unsupported LLM: {llm}"
