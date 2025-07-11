import httpx
from typing import Annotated, List, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import Field
from mcp.server.fastmcp import FastMCP


API_BASE_URL = "http://localhost:9000/1c"

mcp = FastMCP("mcp_1c")


@mcp.tool()
async def get_accounts() -> List[Dict]:
    """Получение плана счетов из 1C."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/plan_accounts")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_debit(
    account: Annotated[str, Field(description="Код счёта")],
    period_start: Annotated[str, Field(description="Дата начала периода dd-mm-yyyy")],
    period_end: Annotated[str, Field(description="Дата конца периода dd-mm-yyyy")],
) -> List[Dict]:
    """Получить сумму дебетовых оборотов по счёту за указанный период."""
    params = {"account": account, "periodStart": period_start, "periodEnd": period_end}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/turnover", params=params)
        resp.raise_for_status()
        data = resp.json()
    result = []
    for row in data:
        analytics = ", ".join(filter(None, [
            row.get("Субконто1Представление"),
            row.get("Субконто2Представление"),
            row.get("Субконто3Представление"),
        ]))
        result.append({"account": row["СчетКод"], "analytics": analytics, "amount": row["СуммаОборотДт"]})
    return result


@mcp.tool()
async def get_credit(
    account: Annotated[str, Field(description="Код счёта")],
    period_start: Annotated[str, Field(description="Дата начала периода dd-mm-yyyy")],
    period_end: Annotated[str, Field(description="Дата конца периода dd-mm-yyyy")],
) -> List[Dict]:
    """Получить сумму кредитовых оборотов по счёту за указанный период."""
    params = {"account": account, "periodStart": period_start, "periodEnd": period_end}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/turnover", params=params)
        resp.raise_for_status()
        data = resp.json()
    result = []
    for row in data:
        analytics = ", ".join(filter(None, [
            row.get("Субконто1Представление"),
            row.get("Субконто2Представление"),
            row.get("Субконто3Представление"),
        ]))
        result.append({"account": row["СчетКод"], "analytics": analytics, "amount": row["СуммаОборотКт"]})
    return result


# Dummy 1C API
@mcp.custom_route("/1c/plan_accounts", methods=["GET"])
async def dummy_plan_accounts(request: Request):
    """Заглушка для получения плана счетов."""
    data = [
        {
            "Код": "50",
            "Наименование": "Касса",
            "Представление": "Активный",
            "Забалансовый": False,
            "Валютный": False,
            "Количественный": False,
        },
        {
            "Код": "51",
            "Наименование": "Расчётные счета",
            "Представление": "Активный",
            "Забалансовый": False,
            "Валютный": True,
            "Количественный": False,
        },
    ]
    return JSONResponse(data)


@mcp.custom_route("/1c/turnover", methods=["GET"])
async def dummy_turnover(request: Request):
    """Заглушка для получения оборотов по счёту."""
    account = request.query_params.get("account", "50")
    data = [
        {
            "СчетКод": account,
            "Субконто1Представление": "Контрагент А",
            "Субконто2Представление": "Договор 1",
            "Субконто3Представление": "",
            "ОрганизацияПредставление": "ООО \"Ромашка\"",
            "ВалютаНаименование": "руб.",
            "СуммаНачальныйОстаток": 0,
            "СуммаНачальныйОстатокДт": 0,
            "СуммаНачальныйОстатокКт": 0,
            "СуммаКонечныйОстаток": 1000,
            "СуммаКонечныйОстатокДт": 1000,
            "СуммаКонечныйОстатокКт": 0,
            "СуммаОборот": 1000,
            "СуммаОборотДт": 1000,
            "СуммаОборотКт": 0,
        },
        {
            "СчетКод": account,
            "Субконто1Представление": "Контрагент Б",
            "Субконто2Представление": "Договор 2",
            "Субконто3Представление": "",
            "ОрганизацияПредставление": "ООО \"Ромашка\"",
            "ВалютаНаименование": "руб.",
            "СуммаНачальныйОстаток": 0,
            "СуммаНачальныйОстатокДт": 0,
            "СуммаНачальныйОстатокКт": 0,
            "СуммаКонечныйОстаток": 2000,
            "СуммаКонечныйОстатокДт": 0,
            "СуммаКонечныйОстатокКт": 2000,
            "СуммаОборот": 2000,
            "СуммаОборотДт": 0,
            "СуммаОборотКт": 2000,
        },
    ]
    return JSONResponse(data)


if __name__ == "__main__":
    mcp.run(transport="sse")
