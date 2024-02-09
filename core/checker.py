import aiohttp
from aiohttp_proxy import ProxyConnector
from eth_account import Account
from eth_account.account import LocalAccount
from eth_account.messages import encode_defunct
from loguru import logger
from pyuseragents import random as random_useragent

from data import config
from utils import change_proxy_by_url
from utils import loader, append_file


class Checker:
    def __init__(self,
                 private_key: str,
                 proxy: str | None = None) -> None:
        self.private_key: str = private_key
        self.proxy: str | None = proxy
        self.account: LocalAccount = Account.from_key(private_key=private_key)

    def sign_message(self,
                     sign_text: str) -> str:
        return Account.sign_message(signable_message=encode_defunct(
            text=sign_text),
            private_key=self.account.key).signature.hex()

    async def do_login(self,
                       client: aiohttp.ClientSession) -> str | None:
        response_text: None = None

        sign_text: str = 'The wallet will be used for MEME allocation. If you referred friends, family, lovers or ' \
                         'strangers, ensure this wallet has the NFT you referred.\n\nBut also...\n\nNever gonna give ' \
                         'you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make ' \
                         'you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\n\nWallet: ' + \
                         self.account.address[:5] + "..." + self.account.address[-4:]

        while True:
            try:
                signed_message: str = self.sign_message(sign_text=sign_text)

                r: aiohttp.ClientResponse = await client.post(url='https://memefarm-api.memecoin.org/user/wallet-auth',
                                                              json={
                                                                  'address': self.account.address,
                                                                  'delegate': self.account.address,
                                                                  'message': sign_text,
                                                                  'signature': signed_message
                                                              },
                                                              headers={
                                                                  'content-type': 'application/json',
                                                              })

                response_text: str = await r.text()

                if '<title>Access denied |' in await r.text():
                    logger.info(f'{self.private_key} | CloudFlare')
                    client.headers['user-agent']: str = random_useragent()

                    if config.CHANGE_PROXY_URL:
                        await change_proxy_by_url(private_key=self.private_key)
                        continue

                if (await r.json()).get('error', '') == 'unauthorized':
                    logger.error(f'{self.private_key} | Not Registered')

                    await append_file(file_folder='result/not_registered.txt',
                                      file_content=f'{self.private_key}\n')

                    return

                return (await r.json(content_type=None))['accessToken']

            except Exception as error:
                if response_text:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при авторизации: {error}, ответ: '
                                 f'{response_text}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при авторизации: {error}')

    async def check_sybil(self,
                          client: aiohttp.ClientSession) -> bool:
        response_text: None = None

        while True:
            try:
                r: aiohttp.ClientResponse = await client.get(url='https://memefarm-api.memecoin.org/user/results')

                response_text: str = await r.text()

                return (await r.json(content_type=None))['results'][0]['won']

            except Exception as error:
                if response_text:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при проверке на Sybil: {error}, '
                                 f'ответ: {response_text}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при проверке на Sybil: {error}')

    async def start_checker(self) -> None:
        async with aiohttp.ClientSession(
                connector=ProxyConnector.from_url(
                    url=self.proxy,
                    use_dns_cache=False,
                    verify_ssl=False,
                    ssl=None
                ) if self.proxy
                else aiohttp.TCPConnector(
                    use_dns_cache=False,
                    verify_ssl=False,
                    ssl=None
                ),
                headers={
                    'accept': 'application/json',
                    'accept-language': 'ru,en;q=0.9',
                    'origin': 'https://www.memecoin.org',
                    'user-agent': random_useragent()
                }
        ) as client:
            access_token: str | None = await self.do_login(client=client)

            if not access_token:
                return

            client.headers['authorization']: str = f'Bearer {access_token}'

            check_sybil_result: bool = await self.check_sybil(client=client)

            if check_sybil_result:
                await append_file(file_folder='result/human.txt',
                                  file_content=f'{self.private_key}\n')

                logger.success(f'{self.private_key} | Human')
                return

            await append_file(file_folder='result/robot.txt',
                              file_content=f'{self.private_key}\n')

            logger.error(f'{self.private_key} | Robot')


async def start_checker(private_key: str,
                        proxy: str | None = None) -> None:
    async with loader.semaphore:
        try:
            if config.CHANGE_PROXY_URL:
                await change_proxy_by_url(private_key=private_key)

            await Checker(private_key=private_key,
                          proxy=proxy).start_checker()

        except Exception as error:
            logger.error(f'{private_key} | Unexpected Error: {error}')

            await append_file(file_folder='result/errors.txt',
                              file_content=f'{private_key}\n')
