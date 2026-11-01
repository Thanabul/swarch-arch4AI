"""Solution for Task 1 (fallback prediction). Try the task yourself first.

Copy classify() into review_service/fallback.py.
"""
import httpx

from common import settings

PENDING = {"label": None, "confidence": None, "model": "fallback", "status": "pending"}


async def classify(client: httpx.AsyncClient, text: str) -> dict:
    """Ask the inference service for a sentiment label.

    Return the inference service's JSON plus "status": "scored".
    If it does not answer within settings.INFERENCE_TIMEOUT_S seconds, or
    answers with an error, return a copy of PENDING instead: the review is
    saved, and a batch job can score it later.
    """
    try:
        # The timeout stops a hung call from holding this request for 20 s.
        r = await client.post(f"{settings.INFERENCE_URL}/predict", json={"text": text},
                              timeout=settings.INFERENCE_TIMEOUT_S)
        # Turn an HTTP 4xx or 5xx answer into an exception, so it falls back too.
        r.raise_for_status()
        return {**r.json(), "status": "scored"}
    except httpx.HTTPError:
        # HTTPError is the parent of both TimeoutException and HTTPStatusError.
        # Return a copy: PENDING is one shared dict, and callers may change the result.
        return dict(PENDING)
