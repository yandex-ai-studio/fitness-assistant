from __future__ import annotations

import os
from datetime import datetime, timezone

from fastmcp import FastMCP

mcp = FastMCP("Персональные заметки MCP")

NOTES_BY_ID: dict[int, dict] = {}
NEXT_ID = 1


@mcp.tool(description="Добавить заметку в блокнот")
def add_note(
    title: str,
    body: str,
    notebook: str | None = None,
    created_at: str | None = None,
) -> dict:
    global NEXT_ID

    title = title.strip()
    body = body.strip()
    notebook = (notebook or "").strip() or "scrapbook"
    created_at = (created_at or "").strip() or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    if not title:
        raise ValueError("заголовок не должен быть пустым")
    if not body:
        raise ValueError("текст заметки не должен быть пустым")

    note = {
        "id": NEXT_ID,
        "notebook": notebook,
        "created_at": created_at,
        "title": title,
        "body": body,
    }
    NOTES_BY_ID[NEXT_ID] = note
    NEXT_ID += 1
    return note


@mcp.tool(description="Список заметок в блокноте или всех блокнотах")
def list_notes(notebook: str | None = None, limit: int = 100) -> dict:
    if limit <= 0:
        raise ValueError("лимит должен быть положительным целым числом")

    notebook_filter = (notebook or "").strip()
    notes = list(NOTES_BY_ID.values())
    if notebook_filter:
        notes = [note for note in notes if note["notebook"] == notebook_filter]

    notes.sort(key=lambda n: (n["created_at"], n["id"]), reverse=True)
    notes = notes[:limit]
    return {"notes": notes, "count": len(notes)}


@mcp.tool(description="Получить последние n заметок из всех блокнотов")
def list_recent_notes(n: int = 10) -> dict:
    if n <= 0:
        raise ValueError("n должно быть положительным целым числом")

    notes = list(NOTES_BY_ID.values())
    notes.sort(key=lambda n_: (n_["created_at"], n_["id"]), reverse=True)
    notes = notes[:n]
    return {"notes": notes, "count": len(notes)}


@mcp.tool(description="Поиск заметок по регистронезависимому совпадению текста в заголовке/теле заметки")
def search_notes(query: str, notebook: str | None = None, limit: int = 100) -> dict:
    query = query.strip()
    if not query:
        raise ValueError("запрос не должен быть пустым")
    if limit <= 0:
        raise ValueError("лимит должен быть положительным целым числом")

    query_lower = query.lower()
    notebook_filter = (notebook or "").strip()

    notes = list(NOTES_BY_ID.values())
    if notebook_filter:
        notes = [note for note in notes if note["notebook"] == notebook_filter]

    notes = [
        note
        for note in notes
        if query_lower in note["title"].lower() or query_lower in note["body"].lower()
    ]
    notes.sort(key=lambda n: (n["created_at"], n["id"]), reverse=True)
    notes = notes[:limit]
    return {"notes": notes, "count": len(notes)}


@mcp.tool(description="Удалить заметку по note_id")
def delete_note(note_id: int) -> dict:
    if note_id <= 0:
        raise ValueError("note_id должен быть положительным целым числом")

    deleted = NOTES_BY_ID.pop(note_id, None) is not None
    return {"deleted": deleted, "note_id": note_id}


@mcp.tool(description="Переместить заметку в другой блокнот")
def move_note(note_id: int, to_notebook: str) -> dict:
    if note_id <= 0:
        raise ValueError("note_id должен быть положительным целым числом")

    to_notebook = to_notebook.strip()
    if not to_notebook:
        raise ValueError("to_notebook не должен быть пустым")

    note = NOTES_BY_ID.get(note_id)
    if note is None:
        raise ValueError(f"заметка с id={note_id} не найдена")

    note["notebook"] = to_notebook
    return note


def main() -> None:
    host = os.getenv("NOTES_HOST", "0.0.0.0")
    port = int(os.getenv("NOTES_PORT", "8000"))
    mcp.run(transport="streamable-http", host=host, port=port)


if __name__ == "__main__":
    main()
