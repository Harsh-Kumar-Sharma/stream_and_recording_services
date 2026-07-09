import httpx


async def is_http_reachable(url: str, timeout_seconds: float = 0.5) -> bool:
    if not url:
        return False

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(url.rstrip("/"))
        return response.status_code < 500
    except httpx.HTTPError:
        return False
