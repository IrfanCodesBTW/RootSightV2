from typing import Any


def success_response(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}


def error_response(message: str, code: int) -> dict[str, Any]:
    return {"success": False, "error": message, "code": code}
