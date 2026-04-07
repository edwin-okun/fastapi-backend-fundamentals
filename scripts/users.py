import httpx
import asyncio
import random
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime

RETRYABLE_STATUS_CODES = {502, 503, 504}


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def retry_httpx(
    fn: Callable[[], Awaitable[httpx.Response]],
    *,
    retries: int = 3,
    base_delay: float = 0.5,
) -> httpx.Response:
    for attempt in range(1, retries + 2):
        logger.debug(f"{datetime.now()} : Attempt {attempt} for function {fn.__name__}")

        try:
            response = await fn()
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in RETRYABLE_STATUS_CODES or attempt > retries:
                raise
            logger.info(f"{datetime.now()} : Attempt {attempt} got {exc.response.status_code}, retrying...")

        delay = base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0, delay * 0.2)
        logger.info(f"{datetime.now()} : Waiting {delay + jitter:.2f}s before next attempt")
        await asyncio.sleep(delay + jitter)
        


BASE_URL = "http://127.0.0.1:8000/api/v1"

async def create_user(name: str):
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0), base_url=BASE_URL) as client:
        response = await retry_httpx(
            lambda: client.post("/users/create", params={"name": name}),
            retries=2,
            base_delay=1.0,
        )
        return response.json()


NAMES = ["Alice", "Bob", "Charlie", "Dave", "Eve"]

for name in NAMES:
    logger.info(f"{datetime.now()} : Creating user: {name}")
    asyncio.run(create_user(name))

    print(f"{datetime.now()} : Finished attempts: {name}\n")