"""
Para cerrar adecuadamente la sesión del cliente ClientSession en aiohttp, debes llamar al método close() en el momento adecuado. 
La forma más común de hacerlo es utilizando el bloque async with, que asegura que la sesión se cierre automáticamente al salir del bloque. Aquí tienes un ejemplo:

python
Copy code
import aiohttp
import asyncio

async def main():
    admin_api = 'http://example.com/admin'
    async with aiohttp.ClientSession() as session:
        async with session.get(admin_api) as response:
            data = await response.text()
            print(data)
    
    # La sesión del cliente se cierra automáticamente al salir del bloque 'async with'

asyncio.run(main())
En este ejemplo, la sesión del cliente se abre utilizando async with aiohttp.ClientSession() as session. Dentro del bloque async with,
realizas tus solicitudes HTTP y trabajas con la respuesta. 


******Al salir del bloque async with, la sesión se cierra automáticamente.******

"""

import aiohttp
import asyncio

async def main():
    admin_api = 'http://192.168.1.139:11000/schemas'
    async with aiohttp.ClientSession() as session:
        async with session.get(admin_api) as response:
            data = await response.text()
            print(data)

asyncio.run(main())
