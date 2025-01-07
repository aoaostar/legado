import httpx

http_request = httpx.AsyncClient(
    follow_redirects=True,
    transport=httpx.AsyncHTTPTransport(
        retries=0,
    ),
    timeout=3,
)
