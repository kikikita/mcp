from typing import List, Dict
import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("documents")

DB_PATH = "db_create/documents.db"


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool()
def list_documents() -> List[Dict[str, str]]:
    """
    Получить список всех документов с их идентификаторами и именами файлов.

    Возвращает:
        [
          {"id": int, "name": str},
          …
        ]
    """
    conn = _get_db_connection()
    rows = conn.execute("SELECT id, name FROM documents ORDER BY id").fetchall()
    conn.close()
    return [{"id": row["id"], "name": row["name"]} for row in rows]


@mcp.tool()
def get_document_text(doc_number: int) -> str:
    """
    Вернуть полный текст документа по его номеру (1–31).

    Параметры
    ----------
    doc_number : int
        Идентификатор документа (= имя файла без расширения).

    Исключения
    ----------
    ValueError — если документа с таким номером нет.
    """
    conn = _get_db_connection()
    row = conn.execute(
        "SELECT content FROM documents WHERE id = ?",
        (doc_number,)
    ).fetchone()
    conn.close()
    if row is None:
        raise ValueError(f"Документ с номером {doc_number} не найден.")
    return row["content"]


@mcp.tool()
def search_document(doc_number: int, query: str) -> List[Dict[str, str]]:
    """
    Найти строку(и), содержащие `query`, внутри указанного документа.

    Возвращает:
        [
          {"line_number": int, "text": str},
          …
        ]
    """
    full_text = get_document_text(doc_number)   # используем уже готовый инструмент
    matches = []
    for i, line in enumerate(full_text.splitlines(), start=1):
        if query.lower() in line.lower():
            matches.append({"line_number": i, "text": line})
    return matches



if __name__ == "__main__":

    mcp.run()
