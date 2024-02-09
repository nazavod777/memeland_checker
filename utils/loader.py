import asyncio

semaphore: asyncio.Semaphore
lock: asyncio.Lock = asyncio.Lock()
