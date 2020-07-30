import aiohttp
from aiohttp import ClientSession
import asyncio


async def fetch_status(session, url, value):
    """
    Sends a request and returns a coroutine for the response.
    """

    response = await session.request(method="GET", url=url)
    return {"value": value, "url": url, "response": response}


async def make_requests(requests):
    """
    Executes requests and returns a future for the list of responses.
    """

    async with ClientSession() as session:
        tasks = []
        for request in requests:
            tasks.append(fetch_status(session, **request))
        return await asyncio.gather(*tasks)


def get_responses(requests):
    """
    Synchronous function that executes HTTP requests, blocks until they're complete,
    and returns responses.
    """

    return asyncio.run(make_requests(requests))

