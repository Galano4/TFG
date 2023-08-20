class webhook_handler:

    def __init__(self, peticion, role, timer, max_iter):
        self.peticion = peticion
        #self.role = role
        #self.timer = timer
        self.max_iter = max_iter
        self.contador = 0
        self.first_iter = True



    def estado_conexion(self, notif):
        print("-"*40)
        print("estado conexion: {}".format(notif.get('state')))
        print("-"*40)
        if notif.get("state") == 'completed':
            con_id = notif.get("connection_id")
            print("connection_id: {}".format(con_id))

        print("-"*40)
        print("Enviando propuesta credencial")
        print("-"*40)
        # Enviar propuesta credencial
        #self.peticion.enviar_propuesta_cred(con_id)



    def emitir_credencial(self, notif):

        #self.peticion.expedir_credencial(notif)

        print("emitir_Credencial")

        if notif.get("state") == "done":
            print("-"*40)
            print("credencial expedido")
            print("-"*40)

        # Una vez expedida la credencial --> issuer solicita prueba
        """if self.role == 'verifier_escenario_':
            escenario_ = True
        else:
            escenario_ = False
            print('Comenzando bucle de verificacion de credenciales')
            self.timer.start()
            for i in range(self.max_iter):
                self.peticion.enviar_peticion_prueba(notif.get('connection_id'), escenario_)"""



    def estado_prueba(self, notif):

        print("estado_prueba")


        """self.peticion.enviar_prueba(notif)

        if notif.get("state") == "done":
            self.contador += 1

            if self.contador % 10 == 0:
                print(f"######## Verificadas {self.contador} de {self.max_iter} credenciales")

            if self.contador == self.max_iter:
                self.timer.stop()
                avg = self.timer.duration / self.max_iter
                #utils.log_msg(f"Tiempo medio en verificar una credencial:{avg}")"""



class WebHook: #dentro de las rutas de esta clase se llama a los 3 métodos que tiene disponible la clase webhook_handler
               #hook_handler=webhook_handler()
    def __init__(self, webhook_port, agent_hook_handler):
        self.webhook_port = webhook_port
        self.hook_handler = agent_hook_handler
        self.webhook_site = None
        self.webhook_url = None

    def webhook_server_terminate(self):
        if self.webhook_site:
            self.webhook_site.stop()
            print("Parando el servidor webhook")

    def webhook_server_init(self):
        self.webhook_url = "http://localhost:{}/webhooks".format(str(self.webhook_port))

        app = microdot.Microdot()

        @app.route('/webhooks/topic/connections/', methods=['POST'])
        def conn_handler(request):
            hook_notif = request.json()
            self.hook_handler.estado_conexion(hook_notif)
            return Response(status=200)

        @app.route('/webhooks/topic/out_of_band/', methods=['POST'])
        def out_of_band(request):
            hook_notif = request.json()
            self.hook_handler.estado_conexion(hook_notif)
            return Response(status=200)

        @app.route('/webhooks/topic/bassicmessage/', methods=['POST'])
        def message_handler(request):
            return Response(status=200)

        @app.route('/webhooks/topic/forward/', methods=['POST'])
        def forward_handler(request):
            return Response(status=200)

        @app.route('/webhooks/topic/issue_credential_v2_0/', methods=['POST'])
        def cred_handler(request):
            hook_notif = request.json()
            self.hook_handler.emitir_credencial(hook_notif)
            return Response(status=200)

        @app.route('/webhooks/topic/issue_credential_v2_0_indy/', methods=['POST'])
        def cred_handler_indy(request):
            hook_notif = request.json()
            return Response(status=200)

        @app.route('/webhooks/topic/present_proof_v2_0/', methods=['POST'])
        def proof_handler(request):
            hook_notif = request.json()
            self.hook_handler.estado_prueba(hook_notif)
            return Response(status=200)

        @app.route('/webhooks/topic/revocation_registry/', methods=['POST'])
        def revocation_registry(request):
            hook_notif = request.json()
            print("-"*40)
            print("revocation_registry: {}".format(hook_notif))
            print("-"*40)
            return Response(status=200)

        @app.route('/webhooks/topic/issuer_cred_rev/', methods=['POST'])
        def cred_revocation(request):
            hook_notif = request.json()
            return Response(status=200)

        @app.route('/webhooks/topic/problem_report/', methods=['POST'])
        def problem_report(request):
            hook_notif = request.json()
            print("-"*40)
            print("problem_handler: {}".format(hook_notif))
            print("-"*40)
            return Response(status=200)

        self.webhook_site = microdot.Server(app, port=self.webhook_port, host='0.0.0.0')
        self.webhook_site.start()



class Peticion:
    def __init__(self, admin_api):
        self.admin_api = admin_api
        self.cred_id = None

webhook_port = 11001
admin_api = 'http://0.0.0.0:11000'
n_cred = 1 #es el numero de iteraciones

peti=Peticion(admin_api)

hook_handler=webhook_handler(peti, 0, n_cred)

webhook_=WebHook(webhook_port, hook_handler)

webhook_.webhook_server_init()
