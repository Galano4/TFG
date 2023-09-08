import aiohttp
import asyncio
import base64
import binascii
import json
from urllib.parse import urlparse
from . import utils

class Peticion:
    def __init__(self, admin_api):
        self.admin_api = admin_api
        self.session = aiohttp.ClientSession(admin_api)
        self.cred_id = None
    
    async def terminar_sesion(self):
        if self.session:
            await self.session.close()
            print('cerrando sesion')
              

    async def admin_request(self, method, path, data=None, text=False, params=None,headers=None, respuesta=True) -> aiohttp.ClientResponse:
        #el objeto ClientResponse se formará a partir de la respuesta correspondiente a la session.request
        #y este objeto permite ver todo acerca de la respuesta a través de sus datos miembro y métodos

        async with self.session.request(method, path, json=data, params=params, headers=headers) as response:
            if respuesta:
                if response.content_type.startswith('text/plain')==False:
                    resp = await response.json()
                    print(resp)
                else:
                    resp= await response.text()
                    #resp=json.dumps(resp) lo comento porque no va a convertir a JSON algo que no se puede porque es un string con espacios
                    #debería ser "400" : "Schema titulo..." cosa que no tiene sentido
                    #"400: Schema sensores-pycom 1.0 already exists"
                    print("Respuesta: {}".format(resp))
                    #resp='400: This schema already exists'
                    #esto ocurre cuando se hace el POST  a schemas
            else:
                resp = 1                                           

        return resp


    #función para ver las credenciales almacenadas por el Holder
    async def get_cred_id(self):
        credentials = await self.admin_request('GET', '/credentials')
        credencial = credentials.get('results')[0]
        cred_id = credencial.get("referent")
        self.cred_id = cred_id
        print(f"cred_id: {cred_id}")

    async def crear_invitacion( self, use_did_exchange: bool = True, auto_accept: bool = True):
        if use_did_exchange:
            invi_params = {"auto_accept": json.dumps(auto_accept)}
            payload = {
            "handshake_protocols": ["rfc23"],
            "use_public_did": False
            }
            invitacion = await self.admin_request('POST', '/out-of-band/create-invitation', payload, params=invi_params)
        else:
            invitacion = await self.admin_request('POST', '/connections/create-invitation')

        invitacion2=json.dumps(invitacion.get('invitation'))
        print("-"*40)
        print("Detalles de la invitacion: {}".format(invitacion2))
        
        return invitacion


    async def recibir_invitacion(self):
        async for details in utils.prompt_loop("Detalles de la invitacion:"):
            b64_invite = None
            try:
                url = urlparse(details)
                query = url.query
                if query and "c_i=" in query:
                    pos = query.index("c_i=") + 4
                    b64_invite = query[pos:]
                elif query and "oob=" in query:
                    pos = query.index("oob=") + 4
                    b64_invite = query[pos:]
                else:
                    b64_invite = details
            except ValueError:
                b64_invite = details


            if b64_invite:
                try:
                    padlen = 4 - len(b64_invite) % 4
                    if padlen <= 2:
                        b64_invite += "=" * padlen
                        invite_json = base64.urlsafe_b64decode(b64_invite)
                        details = invite_json.decode("utf-8")
                except binascii.Error:
                    pass
                except UnicodeDecodeError:
                    pass
            if details:

                try:
                    details = json.loads(details)
                    break

                except json.JSONDecodeError as e:
                    utils.log_msg("Invalid invitation:", str(e))
                    
        params={}
        with utils.log_timer("Connect duration:"):
            if '/out-of-band/' in details.get("@type", ""):
            # Reusar conexiones existentes si hay conexiones anteriores entre ambos agentes
                params["use_existing_connection"] = "true"
                conexion = await self.admin_request('POST', '/out-of-band/receive-invitation', details, params=params)
            else:
                conexion = await self.admin_request('POST', '/connections/receive-invitation', details, params=params)
        return conexion


    async def aceptar_invitacion(self, con_id):
        path = '/didexchange/' + con_id + '/accept-invitation'
        aceptar_invit = await self.admin_request('POST', path)
        return aceptar_invit


    async def get_creddef(self):
        #/credential-definitions/created?issuer_did=AWGhunMpKHqhPVnCucaZEv, 
        params={"issuer_did": "AWGhunMpKHqhPVnCucaZEv"}
        cred_def = await self.admin_request('GET', '/credential-definitions/created', params=params)#ve las credenciales definidas por ese issuer en el ledger
        comprobar = cred_def.get("credential_definition_ids")
        if comprobar :
            utils.log_msg("Ya existe el esquema y la credential definition en el ledger y en la wallet")
        else:
            utils.log_msg("Creando esquema y Credential definition")
            nombre = "sensores-pycom"
            version = "1.0"
            atributos = [
            "numero_serie",
            "modelo",
            "firmware"
            ]
            tag = "valoresPycom"
            await self.registrar_schema_y_creddef(nombre, version, atributos, tag)
        
    async def registrar_schema_y_creddef(self, schema_name, schema_version, schema_attrs, tag):
        schema_body = {
        "schema_name": schema_name,
        "schema_version": schema_version,
        "attributes": schema_attrs
        } #cuerpo en JSON
        headers_schema = {}
        headers_schema["Accept"] = "application/json"
        #header={"Accept":"application/json"}
        schema_response = await self.admin_request('POST', '/schemas', schema_body)#, text=False, headers=headers_schema)

        if not "already exists" in schema_response:
            utils.log_json(json.dumps(schema_response), label='Schema:')
            #print("Respuesta esquema: {}".format(schema_response))
            #response_data= await schema_response.text()
            #utils.log_json(json.dumps(response_data), label='Schema:')
        else:
            resp_schema_id = await self.admin_request('GET', '/schemas/created')
            print(schema_response)
                       
        await asyncio.sleep(4.0)
        if "schema_id" in schema_response:
            schema_id = schema_response["schema_id"]
            utils.log_msg("Schema ID:", schema_id)
        else:
            if "schema_ids" in resp_schema_id:
                schema_id=resp_schema_id["schema_ids"] #schema_id es una lista
                schema_id=schema_id[0] #se coge el primer y única componente de la lista
                utils.log_msg("Schema ID:", schema_id)
            else:
                print("Schema: No se ha creado correctamente")
        

        # crear el credential definition
        creddef_tag = tag #"valoresPycom"
        creddef_body = {
        "revocation_registry_size": 1000,
        "schema_id": schema_id,
        "support_revocation": True,
        "tag": creddef_tag
        }
        creddef_response = await self.admin_request('POST', '/credential-definitions', creddef_body)
        print(f"Esta es la respuesta de la credencial {creddef_response}")

        #falta de sincronización entre la definición de una credencial en el ledger y su ausencia en la wallet


        await asyncio.sleep(4.0)
        if "credential_definition_id" in creddef_response:
            creddef_id = creddef_response["credential_definition_id"]
        else:
            
            #400: Credential definition AWGhunMpKHqhPVnCucaZEv:3:CL:30:valoresPycom is on ledger default but not in wallet 
            #esto para cuando la definición de la credencial se ha hecho en el ledger pero no en la wallet
            if "Credential definition" in creddef_response:
                pos=creddef_response.find('definition ')
                pos_final=creddef_response.find(' is')
                creddef_id=creddef_response[pos+11:pos_final]
                await self.admin_request('POST', '/credential-definitions/{}/write_record'.format(creddef_id))
                #publica esa definición de la credencial en la wallet del agente que quería hacer la definición
                utils.log_msg(creddef_id)
            else:
                #400: Cred def for AWGhunMpKHqhPVnCucaZEv:2:sensores-pycom:1.0 valoresPycom already exists
                #este es el caso en el que está tanto en el ledger como en la wallet
                if "Cred def" in creddef_response:
                    pos=creddef_response.find('for ')
                    pos_final=creddef_response.find(':2')
                    creddef_id=creddef_response[pos+4:pos_final]
                else:    
                    print("creddef: No se ha registrado bien")

        utils.log_msg("Cred def ID:", creddef_id)


    async def enviar_propuesta_cred(self, con_id):
        proposal_body = {
            "auto_remove": True,
            "connection_id": con_id,
            "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": [
                {
                "name": "numero_serie", #alternativa-->FCC ID: número de identificación de la Comisión Federal de Comunicaciones 
                "value": "08B1-2VJ2200"
                },
                {
                "name": "modelo",
                "value": "Pycom Pysense V2.0 X"
                },
                {
                "name": "firmware", 
                "value": "Pycom MicroPython 1.20.2.rc9 [v1.11-1a257d8] on 2020-06-10; FiPy with ESP32"
                }
                ]
            },
            "filter": {
                "indy": {
                    "cred_def_id": "AWGhunMpKHqhPVnCucaZEv:3:CL:8:valoresPycom",
                    "issuer_did": "AWGhunMpKHqhPVnCucaZEv",
                    "schema_id": "AWGhunMpKHqhPVnCucaZEv:2:sensores-pycom:1.0",
                    "schema_issuer_did": "AWGhunMpKHqhPVnCucaZEv",
                    "schema_name": "sensores-pycom",
                    "schema_version": "1.0"
                }
            },
            "trace": False
    }
        await self.admin_request('POST', '/issue-credential-2.0/send-proposal', proposal_body)

    #el connection id acuerdate de que es diferente en cada agente, aunque la conexión sea la misma
    #entonces tienes que poner el connection_id del issuer para esa conexión con el holder
    async def expedir_credencial(self, notif, t):
            state = notif.get('state')
            con_id = notif.get('connection_id')
            cred_ex_id = notif.get('cred_ex_id')
            utils.log_msg("Este es el cred_ex_id: {}".format(cred_ex_id))
            resultado = 0
            print(state)
            if state == 'proposal-received':
                print("ESTÁ EN PROPUESTA RECIBIDA")
                # issuer contesta con una oferta send-offer
                await self.enviar_oferta_cred(con_id)
            elif state == 'offer-received':
                # holder contesta con una propuesta send-request
                await self.enviar_peticion_cred(cred_ex_id)
            elif state== 'request-received':
                # issuer expide la credencial
                await self.enviar_credencial(cred_ex_id)
            elif state == 'credential-received':
                # holder ha recibido la credencial
                await self.almacenar_credencial(cred_ex_id)
            elif state == 'done':
                resultado = 1
                # issuer ha recibido un ack indicando que el holder ha recibido la credencial
            else:
                print("-"*40)
                print(f"estado de la credencial: {state}")
                print("-"*40)

            return resultado


            
    # async def consultar_connection_id(self, inv_key):
    #     #es como si hicieras GET /connections/{invitation_key} pero no hay un método definido en la API
    #     #o que en GET /connections/{conn_id} se hace realmente 192.168.1.141:12000/connections?conn_id=f244b080-5f0b-4b55-a560-dc37777acb2c
    #     #192.168.1.141:12000/connections?invitation_key=4iTpwQn4682AJ2beA4doxMhYgbRc1rHg8hxaTMd3Zkoe
    #     params={"invitation_key": inv_key}
    #     results=await self.admin_request('GET', '/connections', params=params)
    #     valor_results=results.get("results")
    #     #utils.log_msg(valor_results[0])
    #     valor_connection_id=(valor_results[0]).get("connection_id")
    #     return  valor_connection_id
    #     #json.dumps(valor_connection_id)

    #65e09d5d-ad06-4eb3-8550-27865ecb871a
    async def enviar_oferta_cred(self, con_id):

        offer_request = {
            "auto_issue": False,
            "auto_remove": True,
            "connection_id": con_id,
            "credential_preview": {
                "@type": "issue-credential/2.0/credential-preview",
                "attributes": [
                {
                "name": "numero_serie", #alternativa-->FCC ID: número de identificación de la Comisión Federal de Comunicaciones 
                "value": "08B1-2VJ2200"
                },
                {
                "name": "modelo",
                "value": "Pycom Pysense V2.0 X"
                },
                {
                "name": "firmware", 
                "value": "Pycom MicroPython 1.20.2.rc9 [v1.11-1a257d8] on 2020-06-10; FiPy with ESP32"
                }
                ]
            },
            "filter": {
                "indy": {
                    "cred_def_id": "AWGhunMpKHqhPVnCucaZEv:3:CL:8:valoresPycom",
                    "issuer_did": "AWGhunMpKHqhPVnCucaZEv",
                    "schema_id": "AWGhunMpKHqhPVnCucaZEv:2:sensores-pycom:1.0",
                    "schema_issuer_did": "AWGhunMpKHqhPVnCucaZEv",
                    "schema_name": "sensores-pycom",
                    "schema_version": "1.0"
                }
            },
            "trace": False                      
        }
        await self.admin_request('POST', '/issue-credential-2.0/send-offer', offer_request)


    async def enviar_peticion_cred(self, cred_ex_id):
        await self.admin_request('POST', '/issue-credential-2.0/records/{}/send-request'.format(cred_ex_id))
    
    
    async def enviar_credencial(self, cred_ex_id):
        await self.admin_request('POST', '/issue-credential-2.0/records/{}/issue'.format(cred_ex_id), {"comment": "issuing credential, cred_ex_id: {}".format(cred_ex_id)})
    
    
    async def almacenar_credencial(self, cred_ex_id):
    
        await self.admin_request('POST', '/issue-credential-2.0/records/{}/store'.format(cred_ex_id))
    
    
    
    # async def enviar_peticion_prueba(self, con_id, escenario_3=False):
    #     if escenario_3:
    #         proof_request = {
    #         "connection_id": con_id,
    #         "presentation_request": {
    #         "indy": {
    #         "name": "Proof request",
    #         "non_revoked": {
    #         "to": int(time.time() - 1)
    #         },
    #         "requested_attributes": {
    #         "0_name_uuid": {
    #         "name": "nombre",
    #         "non_revoked": {
    #         "to": int(time.time() - 1)
    #         },
    #         "restrictions": [
    #         {
    #         "schema_name": "sensores-pycom"
    #         }
    #         ]
    #         }
    #         },
    #         "requested_predicates": {
    #         "0_edad_uuid": {
    #         "name": "edad",
    #         "non_revoked": {
    #         "to": int(time.time() - 1)
    #         },
    #         "p_type": ">=",
    #         "p_value": 18,
    #         "restrictions": [
    #         {
    #         "schema_name": "sensores-pycom"
    #         }
    #         ]
    #         }
    #         },
    #         "version": "1.0"
    #         }
    #         },
    #         "trace": False
    #         }
    #     else:
    #         proof_request = {
    #         "connection_id": con_id,
    #         "presentation_request": {
    #         "indy": {
    #         "name": "Proof request",
    #         "requested_attributes": {
    #         "0_name_uuid": {
    #         "name": "nombre",
    #         "restrictions": [
    #         {
    #         "schema_name": "sensores-pycom"
    #         }
    #         ]
    #         }
    #         },
    #         "requested_predicates": {
    #           "0_edad_uuid": {
    #         "name": "edad",
    #         "p_type": ">=",
    #         "p_value": 18,
    #         "restrictions": [
    #         {
    #         "schema_name": "sensores-pycom"
    #         }
    #         ]
    #         }
    #         },
    #         "version": "1.0"
    #         }
    #         },
    #         "trace": False
    #         }
    #     await self.admin_request('POST', '/present-proof-2.0/send-request', proof_request)


    # async def enviar_prueba(self, notif):
    #     state = notif.get('state')
    #     pres_ex_id = notif.get('pres_ex_id')
    #     result = 0

    #     if state == "request-received":
    #         await self.enviar_presentacion_prueba(pres_ex_id)
    #     elif state == "presentation-received":
    #         await self.verificar_prueba(pres_ex_id)
    #     elif state == "done":
    #         result = 1
    #     return result



    # async def enviar_presentacion_prueba(self, pres_ex_id):
    #     presentation = {
    #         "indy": {
    #             "requested_attributes": {
    #                 "0_name_uuid": {
    #                 "cred_id": self.cred_id,
    #                 "revealed": True
    #                 }
    #             },

    #             "requested_predicates": {
    #                 "0_edad_uuid": {
    #                 "cred_id": self.cred_id
    #                 }
    #             },
    #             "self_attested_attributes": {}
    #         }
    #     }
    #     await self.admin_request('POST', f'/present-proof-2.0/records/{pres_ex_id}/send-presentation', presentation)


    async def verificar_prueba(self, pres_ex_id):
        verificacion = await self.admin_request('POST', f"/present-proof-2.0/records/{pres_ex_id}/verify-presentation")
        # print("-"*40)
        # print(f"verificacion: {verificacion}")
        # print("-"*40)