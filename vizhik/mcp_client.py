# mcp_client.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

# === Настройки ===
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8022")

app = FastAPI(title="MCP Client")


class PromptRequest(BaseModel):
    prompt: str


@app.post("/process")
async def process_prompt(request: PromptRequest):
    """
    Принимает JSON { "prompt": "..." },
    отдаёт в LLM server (сначала get_tools, затем chat) и возвращает конечный ответ.
    """
    prompt_text = request.prompt

    try:
        resp_tools = requests.get(f"{LLM_SERVER_URL}/get_tools", timeout=None)
        resp_tools.raise_for_status()
        tools_data = resp_tools.json()
        tools_list = tools_data.get("tools", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось получить tools у LLM server: {e}")

    payload = {
        "prompt": prompt_text,
        "tools": tools_list
    }
    try:
        resp_chat = requests.post(f"{LLM_SERVER_URL}/chat", json=payload)
        resp_chat.raise_for_status()
        chat_data = resp_chat.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при /chat у LLM server: {e}")

    return {"response": chat_data["response"]}
