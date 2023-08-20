from peticiones_pycom import Peticion
from hookclass_pycom import WebHook
import os
import time
import urequests
import machine
import _thread
import pycom
from pycoproc import Pycoproc


# Light Sensor (LTR329ALS01)
# Temperature / Humidity Sensor (SI7006A20)
# Pressure Sensor (MPL3115A2)

from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,PRESSURE, ALTITUDE

pycom.heartbeat(False)
pycom.rgbled(0x0A0A08) # white

py = Pycoproc() #es la versión 2 de Pycoproc porque es el Pysense 2

alt = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
#print("MPL3115A2 temperature: " + str(alt.temperature()))
press = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters
print("Pressure: " + str(press.pressure()))
# send to pybytes


dht = SI7006A20(py)
print("Temperature: " + str(dht.temperature())+ " deg C and Relative Humidity: " + str(dht.humidity()) + " %RH")
print("Dew point: "+ str(dht.dew_point()) + " deg C") # punto de rocío--> para ver la humedad
#change to your ambient temperature
t_ambient = str(dht.temperature())
humedad=str(dht.humidity())
#print("Humidity Ambient for " + str(t_ambient) + " deg C is " + str(dht.humid_ambient(t_ambient)) + "%RH")


# li = LTR329ALS01(py)
# luz=str(li.light())
#print("Light (channel Blue lux, channel Red lux): " + str(li.light()))


time.sleep(3)

#CONTROLADOR HOLDER EN MICROPYTHON

class webhook_handler:

    def __init__(self, peticion, max_iter):
        self.peticion = peticion
        self.max_iter = max_iter
        self.contador = 0



    def estado_conexion(self, notif):
        print("-"*40)
        print("estado conexion: {}".format(notif.get('state')))
        print("-"*40)
        if notif.get("state") == 'completed':
            connection_id = notif.get("connection_id")


    def emitir_credencial(self, notif):
        
        self.peticion.expedir_credencial(notif)

        if notif.get("state") == "done":
            self.cont_issued_creds += 1
            if self.cont_issued_creds % 10 == 0:    
                print("######## Expedidas {} de {} credenciales".format(self.cont_issued_creds,self.max_iter))


# def terminar(peticion, hook): LLAMA A MÉTODOS DE LA CLASE Peticion y Webhook 
# #definidas en peticiones.py y hookclass.py pertinentemente
#     await peticion.terminar_sesion()
#     await hook.webhook_server_terminate()
#     os._exit(1)

webhook_port = 12001
admin_api = 'http://192.168.1.141:12000'
n_cred = 1 #es el numero de iteraciones
peticion=Peticion(admin_api) #estamos creando un objeto Peticion que permite hacer peticiones desde un dispositivo que soporta solo micropython


###################################  *MAIN*  ###################################



#NO SE CREA LA INVITACIÓN PORQUE LO HACE EL ISSUER

"""invitacion=peticion.crear_invitacion()
print("Status code: {}".format(invitacion.status_code))
print("Invitation: {}".format(invitacion.text))"""

def iniciar_webhook():
    hook_handler=webhook_handler(peticion, n_cred)
    hook_=WebHook(webhook_port, hook_handler)
    hook_.webhook_server_init()


_thread.start_new_thread(iniciar_webhook,())

time.sleep(1)

def terminar():
#     # server=False
#     # hook=iniciar_webhook(server)
#     # hook.webhook_server_terminate()
    urequests.get('http://192.168.1.137:12001/shutdown')
    _thread.exit()
    
#se ejecuta la función iniciar_webhook en la hebra, y en esta función se abre un servidor para atender
#las peticiones que provienen desde el framework


conexion=peticion.recibir_invitacion() #está en json
print("Status code: {}".format(conexion.status_code))
#print("Invitation received: {}".format(conexion.text))

if conexion.status_code == 200:
    # Ahora puedes acceder a los datos y extraer la información que necesitas
    connection_id = conexion.json().get('connection_id')        
    # Imprimir el valor de 'connection_id'
    print("Connection id: {}".format(connection_id))
else:
    print('Error en la solicitud:', conexion.status_code)


#connection_id = response_data.get('connection_id')
#ya arriba definido, es para recordar

#EL HOLDER ACEPTA LA INVITACIÓN 

peticion.aceptar_invitacion(connection_id)
print("-"*40)
cuerpo_mensaje_temperatura=t_ambient#{"temperatura":t_ambient}
peticion.enviar_mensaje(cuerpo_mensaje_temperatura, connection_id)
# cuerpo_mensaje_humedad={"humedad":humedad}
# peticion.enviar_mensaje(cuerpo_mensaje_humedad, connection_id)
print("-"*40)
peticion.enviar_propuesta_cred(connection_id, t_ambient)


options = "1) Input New Invitation\n" "2) send cred proposal\n" "3)send request\n" "4) store credential\n" "5) salir\n"

print(options)

while True:
    for option in input(options):
        if option is not None:
            option = option.strip() #quita los espacios
        if option is None or option in "xX":
            break
        elif option == "1":
            print("Introducir detalles de la invitacion")
            conexion = peticion.recibir_invitacion()
            # print(conexion)
            # print(’conexion es :{}’.format(type(conexion)))
            connection_id = conexion.json().get('connection_id')
            print("connection_id: {}".format(connection_id))
            # Aceptar la inviation
            peticion.aceptar_invitacion(connection_id)
            cuerpo_mensaje_temperatura=t_ambient#{"temperatura":t_ambient}
            peticion.enviar_mensaje(t_ambient, connection_id) #cuerpo_mensaje_temperatura
            # cuerpo_mensaje_humedad={"humedad":humedad}
            # peticion.enviar_mensaje(cuerpo_mensaje_humedad, connection_id)
            # print(f"aceptar_invitacion: {algo}")
            # print(type(algo))

        elif option == "2":
            peticion.enviar_propuesta_cred(connection_id, t_ambient)
        elif option == "3":
            cred_ex_id=peticion.consultar_cred_ex_id(connection_id)
            print("Cred ex id: {}".format(cred_ex_id))
            #urequests.post('{}/issue-credential-2.0/records/'.format(admin_api)+'{}/send-request'.format(cred_ex_id))
            peticion.enviar_peticion_cred(cred_ex_id)
        elif option == "4":
            peticion.almacenar_credencial(cred_ex_id)
        elif option == "5":       
            terminar()
            os._exit(1)

##############################################################
# 
 



###################################################


# print("Ya puedes enviar la propuesta")
#variable=peticion.enviar_propuesta_cred(connection_id)
#print("PROPUESTA: {}".format(variable.json()))

###########################################

# invitation_key=peticion.consultar_invitation_key(connection_id)

# print("Este es el invitation_key para facilitarselo al issuer: {}".format(invitation_key))
# print("\n")
# print("Ahora el issuer te manda la oferta")

# #############################

# cred_ex_id = input("introducir cred_ex_id para enviar la peticion de credencial: ")
# #peticion.enviar_peticion_cred(cred_ex_id)

# ##################################################

# print("Ya puedes almacenar la credencial")
# cred_ex_id = input("introducir cred_ex_id: ")
# peticion.almacenar_credencial(cred_ex_id)


#"""

