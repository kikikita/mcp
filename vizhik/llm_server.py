# llm_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import httpx
from openai import OpenAI  # pip install openai-python-sdk

# === Настройки ===
# URL, по которому у нас «отвечает» vLLM (совместимый с OpenAI-API)
LLM_BASE_URL = os.getenv("LLM_SERVER_URL", "http://0.0.0.0:8000/v1")

# URL, по которому развернут ваш MCP server (тот, что уже создан на 9000)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9000")

# === Инициализация FastAPI и клиента OpenAI/vLLM ===
app = FastAPI(title="LLM Server")

# Клиент, который будет стучаться в vLLM (OpenAI-совместимый)
llm_client = OpenAI(
    base_url=LLM_BASE_URL,
    api_key="empty"  # vLLM обычно не проверяет API-ключ, поэтому «empty»
)

# === Pydantic‐модели ===
class ChatRequest(BaseModel):
    prompt: str
    # Список описаний функций (инструментов), которые LLM может вызвать
    tools: list


@app.get("/get_tools")
async def get_tools():
    """
    Возвращает MCP server’у список всех доступных инструментов.
    MCP client при старте звонит сюда, чтобы получить tools и передать их в vLLM.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Запрашиваем у «вашего» MCP server’а (порт 9000) список
            # функций, доступных для вызова (ваша реализация в вопросе).
            resp = await client.get(f"{MCP_SERVER_URL}/get_tools")
            resp.raise_for_status()
            data = resp.json()
            return data  # ожидается формат {"tools": [ … ]}
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при get_tools: {e}")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Основной эндпоинт: принимает { prompt, tools }, делает первый запрос в vLLM,
    смотрит, есть ли function_call. Если он есть — дозванивается до MCP server
    за результатом функции, затем отправляет второй запрос в vLLM, чтобы получить финальный
    ответ. Возвращает MCP client’у JSON {"response": "..."}.
    """
    prompt_text = request.prompt
    tools = request.tools  # это список dict’ов с описаниями функций (schema json‐schema)

    # 1) Составляем «начальные» сообщения для vLLM
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can use tools."},
        {"role": "user", "content": prompt_text}
    ]
    while True:
        try:
            # 2) Первый запрос в vLLM (с инструментами, tool_choice="auto").
            completion = llm_client.chat.completions.create(
                model="",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                extra_body={"min_tokens": 5},
                stream=False
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при обращении к vLLM: {e}")

        # 3) Проверяем, не захотел ли LLM вызвать функцию
        first_choice = completion.choices[0]
        finish_reason = first_choice.finish_reason
        print(first_choice)
        # Если vLLM не вернул function_call, значит — просто обычный текст
        if finish_reason != "tool_calls":
            text = first_choice.message.content
            return {"response": text}

        # === Если пришёл function_call ===
        tool_calls = getattr(first_choice.message, "tool_calls", None)
        call = tool_calls[0]
        tool_name = call.function.name
        # Аргументы функции — это JSON строка, разбираем её
        func_args = json.loads(call.function.arguments or "{}")

        # 4) Вызываем MCP server, чтобы получить результат функции
        #    POST http://localhost:9000/get_data {"tool":tool_name, "parameters":func_args}
        async with httpx.AsyncClient() as client:
            try:
                tool_req = {"tool": tool_name, "parameters": func_args}
                resp = await client.post(f"{MCP_SERVER_URL}/get_data", json=tool_req)
                resp.raise_for_status()
                tool_result = resp.json()["result"]
            except httpx.HTTPStatusError as he:
                code = he.response.status_code
                detail = he.response.json().get("detail", he.response.text)
                raise HTTPException(status_code=code, detail=f"Ошибка MCP server при {tool_name}: {detail}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка при get_data: {e}")

        # 5) Делаем «второй» запрос в vLLM, чтобы сконкатенировать function_call + результат функции
        #    и получить финальный текст.
        messages.append({
            "role": "assistant",
            "content": f'{{"name": "{tool_name}", "arguments": "{func_args}"}}'
        })
        messages.append({
            "role": "function",
            "name": tool_name,
            "content": json.dumps(tool_result)
        })
        messages.append({
            "role": "user",
            "content": "Дай финальный ответ в виде цифры подразделения или вызови следующий инструмент в виде JSON"
        })
