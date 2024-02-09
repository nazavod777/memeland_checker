import aiohttp
from loguru import logger

from data import config


async def change_proxy_by_url(private_key: str) -> None:
    while True:
        try:
            async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(
                        use_dns_cache=False,
                        verify_ssl=False,
                        ssl=None
                    )
            ) as client:
                r: aiohttp.ClientResponse = await client.get(url=config.CHANGE_PROXY_URL)

                logger.success(f'{private_key} | Successfully Chaing Proxy by URL, status: {r.status}')

        except Exception as error:
            logger.error(f'{private_key} | Unexpected Error When Changing Proxy: {error}')

        else:
            return
