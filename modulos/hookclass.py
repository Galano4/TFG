from aiohttp import web
import asyncio
import json


class WebHook:

    def __init__(self, webhook_port, agent_hook_handler):
        self.webhook_port = webhook_port
        self.hook_handler = agent_hook_handler
        self.webhook_site = None
        self.webhook_url = None

    async def webhook_server_terminate(self):
        if self.webhook_site:
            await self.webhook_site.stop()
            print("parando webhook server")

    async def webhook_server_init(self):
        self.webhook_url = "http://192.168.201.192:{}/webhooks".format(str(self.webhook_port))
        app = web.Application()
        app.add_routes(
        [
        web.post("/webhooks/topic/connections/", self.conn_handler),
        web.post("/webhooks/topic/out_of_band/", self.out_of_band),
        web.post("/webhooks/topic/basicmessages/", self.message_handler),
        web.post("/webhooks/topic/forward/", self.forward_handler),
        web.post("/webhooks/topic/issue_credential_v2_0/",self.cred_handler),
        web.post("/webhooks/topic/issue_credential_v2_0_indy/", self.cred_handler_indy),
        web.post("/webhooks/topic/present_proof_v2_0/", self.proof_handler),
        web.post("/webhooks/topic/revocation_registry/", self.revocation_registry), 
        web.post("/webhooks/topic/issuer_cred_rev/", self.cred_revocation),
        web.post("/webhooks/topic/problem_report/", self.problem_report),
        ]
        )
        runner = web.AppRunner(app)
        await runner.setup()
        self.webhook_site = web.TCPSite(runner, '192.168.201.192', self.webhook_port)
        await self.webhook_site.start()
    
    
    async def conn_handler(self, request):
        hook_notif = await request.json() #osea pasa de algo que está en json a un objeto (hook_notif) en python, 
        #porque básicamente lo que te están pasando en json representa un objeto
        await self.hook_handler.estado_conexion(hook_notif)
        return web.Response(status=200)



    async def out_of_band(self, request):
        hook_notif = await request.json()
        await self.hook_handler.estado_conexion(hook_notif)
        return web.Response(status=200)


    async def cred_handler(self, request):
        hook_notif = await request.json()
        print(hook_notif)
        await self.hook_handler.emitir_credencial(hook_notif)
        return web.Response(status=200)
    

    async def cred_handler_indy(self, request):
        hook_notif = await request.json()
        return web.Response(status=200)
    

    async def revocation_registry(self, request):
        hook_notif = await request.json()
        print("-"*40)
        print(f"revocation_registry: {hook_notif}")
        print("-"*40)
        return web.Response(status=200)
    

    async def cred_revocation(self, request):
        hook_notif = await request.json()
        return web.Response(status=200)
    

    async def proof_handler(self, request):
        hook_notif = await request.json()
        await self.hook_handler.estado_prueba(hook_notif)
        return web.Response(status=200)
    
    async def problem_report(self, request):
        hook_notif = await request.json()
        print("-"*40)
        print(f"problem_handler: {hook_notif}")
        print("-"*40)
        return web.Response(status=200)
    
    async def message_handler(self, request):
        hook_notif= await request.json()
        await self.hook_handler.estado_mensajes(hook_notif)
        return web.Response(status=200)
    
    async def forward_handler(self, request):
        return web.Response(status=200)