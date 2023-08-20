

""""
import machine
from network import WLAN

wlan = WLAN() # get current object, without changing the mode
if machine.reset_cause() != machine.SOFT_RESET:
    wlan.init(mode=WLAN.STA)
    # configuration below MUST match your home router settings!!
    wlan.ifconfig(config=('192.168.1.137', '255.255.255.0', '192.168.1.1', '46.6.113.34')) # (ip, subnet_mask, gateway, DNS_server)

if not wlan.isconnected():
    # change the line below to match your network ssid, security and password
    wlan.connect('MIWIFI_csA3_2G', auth=(WLAN.WPA2, 'NxYRZxy3'), timeout=5000)
    print("connecting",end='')
    while not wlan.isconnected():
        time.sleep(1)
        print(".",end='')
    print("connected")
"""



# main.py -- put your code here!
from network import WLAN
import machine


wlan = WLAN(mode=WLAN.STA)

#wlan.connect(ssid='TFG_Pablo', auth=(WLAN.WPA2, 'tfgrafa2023!'))
#wlan.connect(ssid='WIFI_FREILICA', auth=(WLAN.WPA2, 'pJi7QuDE'))
wlan.connect(ssid='MIWIFI_csA3_2G', auth=(WLAN.WPA2, 'NxYRZxy3'))
while not wlan.isconnected():
    machine.idle()
print("WiFi connected succesfully")
print(wlan.ifconfig())
#print(wlan.ifconfig(config=('192.168.160.156', '255.255.255.0', '192.168.160.12', '192.168.160.12')))
