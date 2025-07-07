import os
import sqlite3
import subprocess
from docx import Document as DocxDocument

DOCS_DIR = "docs"
DB_PATH = "documents.db"

# 1. Создаём/открываем базу и таблицу
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,     -- 1,2,...,31
        name TEXT,                  -- "1.docx", "2.doc" и т.д.
        content TEXT                -- весь извлечённый текст
    )
""")
conn.commit()

# 2. Функции для извлечения текста

def extract_from_docx(path):
    """
    Читает .docx с помощью python-docx и возвращает весь текст.
    """
    doc = DocxDocument(path)
    full_text = [p.text for p in doc.paragraphs]
    return "\n".join(full_text)


def extract_from_doc(path):
    """
    Пытается извлечь текст из .doc через внешнюю утилиту antiword.
    antiword должна быть установлена в системе (например, через apt, yum или аналог).
    Если antiword не найдена или при ошибке возврата текста, возвращает пустую строку.
    """
    try:
        # Запускаем antiword и читаем результат
        completed = subprocess.run(
            ["antiword", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True
        )
        text = completed.stdout.decode("utf-8", errors="ignore")
        return text
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Если antiword не установлена или произошла ошибка, возвращаем пустой текст
        return ""

# 3. Перебираем все файлы в docs/
for filename in os.listdir(DOCS_DIR):
    name, ext = os.path.splitext(filename)
    if ext.lower() not in (".docx", ".doc"):
        continue

    # проверяем, что имя файла — число 1..31
    try:
        doc_id = int(name)
    except ValueError:
        continue

    full_path = os.path.join(DOCS_DIR, filename)
    if ext.lower() == ".docx":
        content = extract_from_docx(full_path)
    else:
        content = extract_from_doc(full_path)

    # Сохраняем или обновляем запись
    cursor.execute(
        "INSERT OR REPLACE INTO documents (id, name, content) VALUES (?, ?, ?)",
        (doc_id, filename, content)
    )
    conn.commit()

conn.close()