from typing import Any


def success_response(
    data: Any = None,
    *,
    message: str | None = None,
) -> dict[str, Any]:
    """
    Build a standard successful API response.
    """

    response: dict[str, Any] = {
        "success": True,
    }

    if message is not None:
        response["message"] = message

    if data is not None:
        response["data"] = data

    return response