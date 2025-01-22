import httpx

http_request = httpx.AsyncClient(
    follow_redirects=True,
    transport=httpx.AsyncHTTPTransport(
        retries=3,
    ),
    timeout=60 * 3,
)
