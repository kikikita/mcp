import aiohttp
import asyncio
import bs4
import datetime
import json
import json
import pathlib
import urllib.parse
from typing import Annotated
from typing import List, Dict
from typing import TypedDict

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from readability.readability import Document


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


mcp = FastMCP("web_search", port=4200, host="0.0.0.0")
LOG = pathlib.Path("logs/search_queries.jsonl")
SEARX_ENDPOINT = "http://localhost:8080/search"  # ← единое имя


@mcp.tool()
async def web_search(
        query: Annotated[str, Field(description="Строка запроса", max_length=256)]
) -> list[SearchResult]:
    """
Выполняет поиск в интернете по заданному запросу.

Этот инструмент используется для получения актуальной информации из веб-поиска.
Возвращает список релевантных результатов с заголовками, URL и краткими описаниями.

Args:
    query: Поисковый запрос (максимум 256 символов)
    limit: Количество результатов для возврата (от 1 до 10)

Returns:
    Список словарей с полями: title (заголовок), url (ссылка), snippet (отрывок)
"""
    params = {'q': query, 'format': 'json', 'language': 'ru', 'safesearch': 1, "limit": 5}
    url = f"{SEARX_ENDPOINT}?{urllib.parse.urlencode(params)}"
    async with aiohttp.ClientSession() as s:
        data = await (await s.get(url)).json()
    out = [{
        "title": r["title"],
        "url": r["url"],
        "snippet": r.get("content", "")
    } for r in data["results"][:5]]
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({"ts": datetime.datetime.utcnow().isoformat(),
                            "query": query, "results": out}) + "\n")
    return out


async def fetch_article(url: str) -> str:
    async with aiohttp.ClientSession() as s:
        html = await (await s.get(url, timeout=10)).text()
    doc = Document(html)
    clean_html = bs4.BeautifulSoup(doc.summary(), "html.parser").get_text(" ", strip=True)
    return clean_html


@mcp.tool()
async def fetch_and_read(url: Annotated[str, Field(description="url скачиваемой страницы")]) -> str:
    """Скачивает страницу и возвращает очищенный текст (первые 3000 симв.). Используется для уточние информации"""
    return await fetch_article(url)


if __name__ == "__main__":
    mcp.run(transport="sse")
