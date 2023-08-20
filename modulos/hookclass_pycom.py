from microdot import Microdot


class WebHook: #dentro de las rutas de esta clase se llama a los 3 métodos que tiene disponible la clase webhook_handler
               #hook_handler=webhook_handler()
    def __init__(self, webhook_port, agent_hook_handler):
        self.webhook_port = webhook_port
        self.hook_handler = agent_hook_handler
        self.webhook_url = None
        self.cont_issued_creds = 0

    def webhook_server_init(self):
        self.webhook_url = "http://192.168.1.137:{}/webhooks".format(self.webhook_port) #yo estoy corriendo el servidor Microdot en el Pycom, 
                                                                                        #entonces el endpoint del Webhook está en la ip del Pycom
        print("Se ha iniciado el Microdot en el puerto: {}".format(self.webhook_port))


        app = Microdot()

        @app.route('/webhooks/topic/connections/', methods=['POST']) #el request que se pasa por argumento es la petición que se ha hecho a ese endpoint
        def conn_handler(request):
            hook_notif = request.json
            self.hook_handler.estado_conexion(hook_notif)
            return 'OK'           

        @app.route('/webhooks/topic/out_of_band/', methods=['POST'])
        def out_of_band(request):
            print("out_of_band")
            hook_notif = request.json
            self.hook_handler.estado_conexion(hook_notif)
            return 'OK'
            
        @app.route('/webhooks/topic/issue_credential_v2_0/', methods=['POST'])
        def cred_handler(request):
            if request.content_type=="application/json":
                print("JSON")
                hook_notif = request.json
                self.hook_handler.estado_conexion(hook_notif)
                print(hook_notif)
                self.hook_handler.emitir_credencial(hook_notif)
            else:
                print("La petición no tiene contenido de tipo json")
            return 'OK'        

        @app.route('/webhooks/topic/issue_credential_v2_0_indy/', methods=['POST'])
        def cred_handler_indy(request):
            hook_notif = request.json
            return 'OK'
                    
        @app.route('/webhooks/topic/basicmessages/', methods=['POST'])
        def message_handler(request):
            print("Bassic Messsages: ")
            hook_notif =request.json
            return 'OK'

        @app.route('/webhooks/topic/forward/', methods=['POST'])
        def forward_handler(request):
            hook_notif =request.json
            return 'OK' 

        @app.route('/webhooks/topic/revocation_registry/', methods=['POST'])
        def revocation_registry(request):
            hook_notif = request.json
            print("-"*40)
            print("revocation_registry: {}".format(hook_notif))
            print("-"*40)
            return 'OK'  


        @app.route('/webhooks/topic/present_proof_v2_0/', methods=['POST'])
        def proof_handler(request):
            hook_notif = request.json
            self.hook_handler.estado_prueba(hook_notif)
            return 'OK'

        @app.route('/webhooks/topic/issuer_cred_rev/', methods=['POST'])
        def cred_revocation(request):
            hook_notif = request.json
            return 'OK'

        @app.route('/webhooks/topic/problem_report/', methods=['POST'])
        def problem_report(request):
            hook_notif = request.json
            print("-"*40)
            print("problem_handler: {}".format(hook_notif))
            print("-"*40)
            return 'OK'  

        @app.get('/shutdown')
        def shutdown(request):
            request.app.shutdown()
            return 'The server is shutting down...'
        
        app.run(host='192.168.1.137', port=self.webhook_port, debug=False)
        #debug en True para que se vea en la consola la respuesta: GET /webhooks 200  




