import httpx
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Annotated, List, Dict, Optional
from pydantic import Field
from mcp.server.fastmcp import FastMCP

API_BASE_URL = "http://localhost:9000/1c"

mcp = FastMCP("mcp_wilarus")

# --- Tools interacting with dummy 1C API ---

@mcp.tool()
async def get_nomenclature(name: Annotated[str, Field(description="Наименование товара")]) -> Optional[Dict]:
    """Проверить наличие номенклатуры в 1С по имени."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/nomenclature", params={"name": name})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

@mcp.tool()
async def create_nomenclature(name: Annotated[str, Field(description="Наименование")], unit: Annotated[str, Field(description="Единица измерения")]) -> Dict:
    """Создать новую номенклатуру в 1С."""
    payload = {"name": name, "unit": unit}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE_URL}/nomenclature", json=payload)
        resp.raise_for_status()
        return resp.json()

@mcp.tool()
async def get_contractor(inn: Annotated[str, Field(description="ИНН контрагента")]) -> Optional[Dict]:
    """Найти контрагента по ИНН."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/contractors", params={"inn": inn})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

@mcp.tool()
async def create_contractor(name: str, inn: str, account: str, bank: str) -> Dict:
    """Создать карточку контрагента."""
    payload = {"name": name, "inn": inn, "account": account, "bank": bank}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE_URL}/contractors", json=payload)
        resp.raise_for_status()
        return resp.json()

@mcp.tool()
async def create_payment(data: Dict) -> Dict:
    """Создать платёжное поручение."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE_URL}/payments", json=data)
        resp.raise_for_status()
        return resp.json()

@mcp.tool()
async def create_receipt(data: Dict) -> Dict:
    """Создать документ поступления товаров."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE_URL}/receipts", json=data)
        resp.raise_for_status()
        return resp.json()

@mcp.tool()
async def get_receipt_status(receipt_id: str) -> Dict:
    """Получить статус документа поступления."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/receipts/{receipt_id}")
        resp.raise_for_status()
        return resp.json()

# --- Dummy 1C API implementation ---

nomenclature_db: Dict[str, Dict] = {}
contractor_db: Dict[str, Dict] = {}
payment_db: Dict[str, Dict] = {}
receipt_db: Dict[str, Dict] = {}

@mcp.custom_route("/1c/nomenclature", methods=["GET"])
async def api_get_nomenclature(request: Request):
    name = request.query_params.get("name")
    for nid, item in nomenclature_db.items():
        if item["name"].lower() == name.lower():
            return JSONResponse({"id": nid, **item})
    return JSONResponse({"detail": "not found"}, status_code=404)

@mcp.custom_route("/1c/nomenclature", methods=["POST"])
async def api_create_nomenclature(request: Request):
    data = await request.json()
    nid = str(len(nomenclature_db) + 1)
    nomenclature_db[nid] = data
    return JSONResponse({"id": nid, **data})

@mcp.custom_route("/1c/contractors", methods=["GET"])
async def api_get_contractor(request: Request):
    inn = request.query_params.get("inn")
    for cid, c in contractor_db.items():
        if c["inn"] == inn:
            return JSONResponse({"id": cid, **c})
    return JSONResponse({"detail": "not found"}, status_code=404)

@mcp.custom_route("/1c/contractors", methods=["POST"])
async def api_create_contractor(request: Request):
    data = await request.json()
    cid = str(len(contractor_db) + 1)
    contractor_db[cid] = data
    return JSONResponse({"id": cid, **data})

@mcp.custom_route("/1c/payments", methods=["POST"])
async def api_create_payment(request: Request):
    data = await request.json()
    pid = str(len(payment_db) + 1)
    payment_db[pid] = {"status": "created", **data}
    return JSONResponse({"payment_id": pid, "status": "created"})

@mcp.custom_route("/1c/receipts", methods=["POST"])
async def api_create_receipt(request: Request):
    data = await request.json()
    rid = str(len(receipt_db) + 1)
    receipt_db[rid] = {"status": "created", **data}
    return JSONResponse({"receipt_id": rid, "status": "created"})

@mcp.custom_route("/1c/receipts/{rid}", methods=["GET"])
async def api_get_receipt(request: Request, rid: str):
    rec = receipt_db.get(rid)
    if not rec:
        return JSONResponse({"detail": "not found"}, status_code=404)
    return JSONResponse({"receipt_id": rid, "status": rec["status"]})

if __name__ == "__main__":
    mcp.run(transport="sse")
