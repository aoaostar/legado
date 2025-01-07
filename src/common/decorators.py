import asyncio
import logging
import time
from collections.abc import Callable, Coroutine


def calculate_time(name=""):
    if name is not None:
        name += ": "

    def decorator(fn) -> Callable | Coroutine:
        if asyncio.iscoroutinefunction(fn):

            async def func(*args, **kwargs):
                start_time = time.time()
                await fn(*args, **kwargs)
                logging.info(f"{name}耗时: {time.time() - start_time}s")
        else:

            def func(*args, **kwargs):
                start_time = time.time()
                fn(*args, **kwargs)
                logging.info(f"{name}耗时: {time.time() - start_time}s")

        return func

    return decorator
