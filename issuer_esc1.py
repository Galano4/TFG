import aiohttp
import asyncio
import os

from modulos import utils
from modulos.peticiones import Peticion
from modulos.hookclass import WebHook

# controlador = main + modulos ; modulos = peticiones + hooks 


class webhook_handler:

    def __init__(self, peticion, timer, max_iter):
        self.peticion = peticion
        self.timer = timer
        self.max_iter = max_iter
        self.cont_issued_creds = 0
        self.first_iter = True
        self.t=0

    async def estado_conexion(self, notif):
        print("-"*40)
        print(f"estado conexion: {notif.get('state')}")
        print("-"*40)
    


    async def estado_mensajes(self, notif):
        if notif.get('state')=="received": #a nosotros nos llega un diccionario: {'content': valor}
            valor=notif.get('content') #contenido es el valor de la clave content que es un array con los tres valores
            #valor=notif['content']
            if valor:
                self.t=valor
                utils.log_msg("temperatura")
                utils.log_msg(self.t)
            # elif 'humedad' in valor:
            #     self.cambiar_valor_h(valor.get('humedad'))
            #     utils.log_msg(self.h)
        else:
            print(notif.get('state'))
        return self.t

    async def emitir_credencial(self, notif):
        valor=await self.estado_mensajes(notif) 
        #lo que pasaba aquí es que al no esperar, se accedía antes a expedir_credencial que a estado_mensajes entonces self.t seguía siendo 0
        await self.peticion.expedir_credencial(notif, valor)

        if self.first_iter:
            self.timer.start()
            self.first_iter = False

        if notif.get("state") == "done":
            self.cont_issued_creds += 1
            
            if self.cont_issued_creds % 10 == 0:
                print(f"######## Expedidas {self.cont_issued_creds} de {self.max_iter} credenciales")
            if self.cont_issued_creds == self.max_iter:
                self.timer.stop()
                avg = self.timer.duration / self.max_iter
                utils.log_msg(f"Tiempo medio en expedir una credencial: {avg}")
                self.cont_issued_creds = 0
                self.first_iter = True
                self.timer.reset()

async def terminar(peticion, hook):
    await peticion.terminar_sesion()
    await hook.webhook_server_terminate()
    os._exit(1)

async def crear_schema(peticion):
    nombre = 'sensores-pycom'
    version = "1.0"
    atributos = [
    "temperatura"
    ]
    tag = "tituloUniversidad"
    await peticion.registrar_schema_y_creddef(nombre, version, atributos, tag)


################################### *MAIN* ###################################


async def main():
    # iniciar peticiones
    peticion = Peticion(admin_api)

    n_creds = int(input("Introducir numero de iteraciones: "))

    issue_timer = utils.log_timer(f"se han expedido {n_creds} credenciales en: ")
    
    hook_handler = webhook_handler(peticion, issue_timer, n_creds)
    
    hook = WebHook(webhook_port, hook_handler)

    # iniciar servidor a la escucha de eventos
    await hook.webhook_server_init()

    # comprobar si existe el esquema y la cred def (sino, crearlas):
    await peticion.get_creddef()

    # Generar invitacion
    invit = await peticion.crear_invitacion()



    options = "1) Generar nueva invitacion\n" "2) generar esquema\n" "3)enviar oferta\n" "4) enviar credencial\n"
    async for option in utils.prompt_loop(options):
    
        if option is not None:
            option = option.strip()
        if option is None or option in "xX":
            break
        elif option == "1":
            invit = await peticion.crear_invitacion()
        elif option == "2":
            await crear_schema(peticion)

        elif option == "3":
            conn_id=input("Mete el connection id")
            #invitation_key = input("introducir invitation_key: ")
            #conn_id=await peticion.consultar_connection_id(invitation_key)
            #utils.log_msg("Connection id asociado al invitation_key: '{}'".format(conn_id))
            await peticion.enviar_oferta_cred(conn_id)

        elif option == "4":
            cred_ex_id = input("introducir cred_ex_id: ")
            await peticion.enviar_credencial(cred_ex_id)
    
    await terminar(peticion, hook)


################################### FIN MAIN ###################################

#Se declaran las variables necesarias para el MAIN

webhook_port = 11001
admin_api = 'http://192.168.1.141:11000'
n_cred = 1

asyncio.run(main())

 #aquí se ejecuta el main de forma asíncrona, arriba se declara simplemente
#y como el main es asíncrono, en él se llaman a funciones asíncronas que son las que hemos declarado anteriormente