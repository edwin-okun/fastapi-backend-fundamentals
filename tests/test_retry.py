from unittest.mock import AsyncMock, patch

import httpx
import pytest

from scripts.retry import retry_httpx


def _ok_response(status_code=200):
    return httpx.Response(status_code, request=httpx.Request("GET", "http://test"))


def _error_response(status_code=500):
    return httpx.Response(status_code, request=httpx.Request("GET", "http://test"))


@pytest.mark.asyncio
@patch("scripts.retry.asyncio.sleep", new_callable=AsyncMock)
async def test_returns_on_first_success(mock_sleep):
    fn = AsyncMock(return_value=_ok_response())

    result = await retry_httpx(fn, retries=2, base_delay=0.1)

    assert result.status_code == 200
    assert fn.await_count == 1
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
@patch("scripts.retry.asyncio.sleep", new_callable=AsyncMock)
async def test_retries_on_connect_error_then_succeeds(mock_sleep):
    fn = AsyncMock(side_effect=[httpx.ConnectError("down"), _ok_response()])

    result = await retry_httpx(fn, retries=2, base_delay=0.1)

    assert result.status_code == 200
    assert fn.await_count == 2
    assert mock_sleep.await_count == 1


@pytest.mark.asyncio
@patch("scripts.retry.asyncio.sleep", new_callable=AsyncMock)
async def test_retries_on_timeout_then_succeeds(mock_sleep):
    fn = AsyncMock(
        side_effect=[httpx.ConnectTimeout("slow"), httpx.ReadTimeout("slow"), _ok_response()]
    )

    result = await retry_httpx(fn, retries=3, base_delay=0.1)

    assert result.status_code == 200
    assert fn.await_count == 3
    assert mock_sleep.await_count == 2


@pytest.mark.asyncio
@patch("scripts.retry.asyncio.sleep", new_callable=AsyncMock)
async def test_raises_after_exhausting_retries(mock_sleep):
    fn = AsyncMock(side_effect=httpx.ConnectError("down"))

    with pytest.raises(httpx.ConnectError):
        await retry_httpx(fn, retries=2, base_delay=0.1)

    # 1 initial + 2 retries = 3 total attempts
    assert fn.await_count == 3
    assert mock_sleep.await_count == 2


@pytest.mark.asyncio
@patch("scripts.retry.asyncio.sleep", new_callable=AsyncMock)
async def test_non_retryable_exception_raises_immediately(mock_sleep):
    fn = AsyncMock(side_effect=httpx.DecodingError("bad json"))

    with pytest.raises(httpx.DecodingError):
        await retry_httpx(fn, retries=2, base_delay=0.1)

    assert fn.await_count == 1
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
@patch("scripts.retry.asyncio.sleep", new_callable=AsyncMock)
async def test_http_5xx_is_not_retried(mock_sleep):
    """raise_for_status() throws HTTPStatusError, which is not in RETRYABLE_EXCEPTIONS."""
    fn = AsyncMock(return_value=_error_response(500))

    with pytest.raises(httpx.HTTPStatusError):
        await retry_httpx(fn, retries=2, base_delay=0.1)

    assert fn.await_count == 1
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
@patch("scripts.retry.asyncio.sleep", new_callable=AsyncMock)
async def test_exponential_backoff_delays(mock_sleep):
    fn = AsyncMock(
        side_effect=[httpx.ConnectError("down"), httpx.ConnectError("down"), _ok_response()]
    )

    with patch("scripts.retry.random.uniform", return_value=0):  # zero jitter
        await retry_httpx(fn, retries=3, base_delay=1.0)

    # delay = base_delay * 2^(attempt-1): 1st retry → 1.0s, 2nd retry → 2.0s
    mock_sleep.assert_any_await(1.0)
    mock_sleep.assert_any_await(2.0)
