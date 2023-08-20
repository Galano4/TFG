

import aiohttp
import asyncio

async def main():
    admin_api = 'http://192.168.1.139:11000'
    async with aiohttp.ClientSession() as session:
        async with session.get(admin_api) as response:
            data = await response.text()
            print(data)

asyncio.run(main())
