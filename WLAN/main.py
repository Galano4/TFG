# main.py -- put your code here!
from network import WLAN
import machine


wlan = WLAN(mode=WLAN.STA)
#wlan.ifconfig(config=('192.168.xxx.xxx', '255.255.255.0', '192.168.xxx.xxx', '192.168.xxx.xxx')) # (ip, subnet_mask, gateway, DNS_server)
wlan.connect(ssid='WIFI_FREILICA', auth=(WLAN.WPA2, 'xxxxxx'))

while not wlan.isconnected():
    machine.idle()
print("WiFi connected succesfully")
print(wlan.ifconfig())
