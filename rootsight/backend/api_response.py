from typing import Any


def success_response(data: Any) -> dict[str, Any]:
    return {"data": data, "error": None}


def error_response(message: str) -> dict[str, Any]:
    return {"data": None, "error": message}
