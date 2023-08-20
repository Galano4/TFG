import ujson
import urequests
import utime


#MODULO PROGRAMADO EN MICROPYTHON PARA QUE EL HOLDER HAGA PETICIONES AL FRAMEWORK A TRAVÉS DE LA API

def encode_params(params): #se utiliza para codificar en la URL los parámetros referentes a la consulta/query (lo que va detrás de ?)
    encoded_params = []
    for key, value in params.items():
        encoded_param = '{}={}'.format(key, value)
        encoded_params.append(encoded_param) #auto_accept=true
    return '&'.join(encoded_params) #ej: ?auto_accept=true&key=valor



class Peticion:
    def __init__(self, admin_api):
        self.admin_api = admin_api
        self.cred_id = None

    def crear_invitacion(self, use_did_exchange: bool = True, auto_accept: bool = True):
        if use_did_exchange:
            auto_accept_json = ujson.dumps(auto_accept) #convierte de objeto en Python a json, porque hay que mandarlo en la petición
            invi_params = {'auto_accept': auto_accept_json} #este es el parámetro a codificar que va en la parte de la consulta de la petición, es prescindible
            payload = {'handshake_protocols': ['rfc23'], 'use_public_did': False} #va a ser el cuerpo de la invitación
            url = '{}{}'.format(self.admin_api, '/out-of-band/create-invitation')
            url_params = encode_params(invi_params)
            url += '?' + url_params
            invitacion = urequests.post(url, json=payload)
        else:
            url = '{}{}'.format(self.admin_api, '/connections/create-invitation')
            invitacion = urequests.post(url, json=payload)
        
        data=invitacion.text
        clave_invitacion=data[data.find('"invitation":')+14:] #14 es las comillas más invitacion más el espacio y los dos puntos
        print("Lo que hay que introducir en los Detalles de la Invitacion: {}".format(clave_invitacion))
        
        return invitacion
    
    def recibir_invitacion(self):
        while True:
            details = input("Detalles de la invitacion: ")# la invitación se introduce en forma de diccionario 
            if details:
                try:
                    details=ujson.loads(details) #se utiliza para convertir de formato JSON a objeto de Python.
                    #dumps al contrario, details=ujson.dumps(details)
                    break
                except ValueError as e:
                    print("Invalid invitation:", str(e))
        
        # Resto del código para establecer la conexión

        params = {}


        if '/out-of-band/' in details.get("@type", ""):
            # Reusar conexiones existentes si hay conexiones anteriores entre ambos agentes
            params["use_existing_connection"] = "true"
            url_params = encode_params(params)
            url2 = '{}{}'.format(self.admin_api, '/out-of-band/receive-invitation') 
            url2 += '?' + url_params
            conexion = urequests.post(url2, json=details)
        else:
            url3 = '{}{}'.format(self.admin_api, '/connections/receive-invitation')
            conexion = urequests.post(url3, json=details)
        
        return conexion
    

    def aceptar_invitacion(self, con_id):
        path = '{}/didexchange/{}/accept-invitation'.format(self.admin_api, con_id)
        aceptar_invit =  urequests.post(path)
        #print()
        return 'Status code aceptar_invitacion: {}'.format(aceptar_invit.status_code) #'Connection_id: {}'.format(aceptar_invit.text)
    
    
    def consultar_cred_ex_id(self, con_id):
        params={'connection_id': con_id}
        url_params = encode_params(params)
        url='{}/issue-credential-2.0/records'.format(self.admin_api)
        url += '?' + url_params
        respuesta=urequests.get(url)
        valor=respuesta.json().get("results")
        for dato in valor:
            valor_record=dato.get("cred_ex_record")
            print(valor_record)
            if valor_record.get('state')=='offer-received':
                return valor_record.get('cred_ex_id')
            else:
                return 1    


    def enviar_mensaje(self, mensaje, connection_id):
        cuerpo={"content": mensaje}
        print(cuerpo)
        url_mensaje="{}/connections/{}/send-message".format(self.admin_api,connection_id)
        urequests.post(url_mensaje,json=cuerpo)




    #con esto conseguimos el invitation_key asociado al connection id desde la perspectiva del holder,
    #y utilizamos esta invitation_key (que es la misma en el issuer) para saber su connection id,
    #para enviar la credencial
    def consultar_invitation_key(self, con_id):
        respuesta=urequests.get('{}/connections/{}'.format(self.admin_api, con_id))
        valor=respuesta.json().get("invitation_key")
        return valor
    

    
    # #def format_date_time(timestamp):
    #     # Obtener la fecha y hora en segundos desde el inicio del tiempo Unix
    #     time_tuple = utime.localtime(timestamp)
    
    #     # Extraer los componentes de la fecha y hora
    #     year, month, day, hour, minute, second, _, _ = time_tuple
    
    #     # Crear una cadena con el formato deseado
    #     formatted_date_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}:{:06d}".format(year, month, day, hour, minute, second, 0)
    
    #     return formatted_date_time


    def enviar_propuesta_cred(self, con_id, t):
        # Obtener el tiempo actual en segundos desde la época
        #fecha = utime.time()
        #Convertir el tiempo actual a una tupla de tiempo
        #fecha = self.format_date_time(fecha)
        #fecha = datetime.now()
        #fecha = fecha.strftime("%Y-%m-%d %H:%M:%S:%f")
        proposal_body = {
            "auto_remove": True,
            "connection_id": con_id,
            "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": [
                {
                "name": "temperatura",
                "value": t
                }
            ]
            },
            "filter": {
                "indy": {
                    "cred_def_id": "XXFm7jVVMEV6UhKifRNDEx:3:CL:8:valoresPycom",
                    "issuer_did": "XXFm7jVVMEV6UhKifRNDEx",
                    "schema_id": "XXFm7jVVMEV6UhKifRNDEx:2:sensores-pycom:1.0",
                    "schema_issuer_did": "XXFm7jVVMEV6UhKifRNDEx",
                    "schema_name": "sensores-pycom",
                    "schema_version": "1.0"
                }
            },
            "trace": False
        }
        #Send issuer a credential proposal
        urequests.post('{}/issue-credential-2.0/send-proposal'.format(self.admin_api), json=proposal_body)
    
    def enviar_peticion_cred(self, cred_ex_id):
        urequests.post('{}/issue-credential-2.0/records/'.format(self.admin_api)+'{}/send-request'.format(cred_ex_id))
        #urequests.post('{}/issue-credential-2.0/records/{}/send-request'.format(self.admin_api,cred_ex_id))

    def almacenar_credencial(self, cred_ex_id):
        urequests.post('{}/issue-credential-2.0/records/{}/store'.format(self.admin_api,cred_ex_id))


    def expedir_credencial(self, notif):
            state = notif.get('state')
            con_id = notif.get('connection_id')
            cred_ex_id = notif.get('cred_ex_id')
            resultado = 0
            if state == 'proposal-received':
                # issuer contesta con una oferta send-offer
                self.enviar_oferta_cred(con_id)
            elif state == 'offer-received':
                print("updated a 24/07")
                # holder contesta con una propuesta send-request
                self.enviar_peticion_cred(cred_ex_id)
            elif state== 'request-received':
                # issuer expide la credencial
                self.enviar_credencial(cred_ex_id)
            elif state == 'credential-received':
                # holder ha recibido la credencial
                print("updated a 24/07")
                #self.almacenar_credencial(cred_ex_id)
            elif state == 'done':
                resultado = 1
                # issuer ha recibido un ack indicando que el holder ha recibido la credencial
            else:
                print("-"*40)
                print("estado de la credencial: {}".format(state))
                print("-"*40)


            return resultado


