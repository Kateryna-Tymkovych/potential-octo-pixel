from httpx import AsyncClient

async def assert_authorization(
    client: AsyncClient,
    method: str,
    url: str,
    expected_status: int,
    **kwargs
):
    """
    Helper to verify that a specific client receives the expected status code.

    :param client: The httpx AsyncClient instance to use.
    :param method: HTTP method (GET, POST, etc.).
    :param url: Endpoint URL.
    :param expected_status: The HTTP status code we expect.
    :param kwargs: Additional arguments for the httpx client (json, params, etc.).
    """
    # Resolve the method on the client
    func = getattr(client, method.lower())
    response = await func(url, **kwargs)

    assert response.status_code == expected_status, (
        f"Auth Failure: {method} {url} "
        f"expected {expected_status}, but got {response.status_code}. "
        f"Response: {response.text}"
    )
    return response
