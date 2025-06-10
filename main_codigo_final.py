# main.py -- put your code here!
from machine import Timer, Pin, UART
import time
import CCS811
import hashlib
from micropyGPS import MicropyGPS
from time import sleep
from network import LoRa

import socket
import ubinascii
import struct
import machine

i2c = I2C(0, mode=I2C.MASTER, pins=('G21','G22'), baudrate=100000)
# Adafruit sensor breakout has i2c addr: 90; Sparkfun: 91
time.sleep(2)
s = CCS811.CCS811(i2c=i2c, addr=90)

lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

dev_addr = 0x260B3E48
nwk_swkey = ubinascii.unhexlify('E5FB209C7BC20768EC23C869735786DB')
app_swkey = ubinascii.unhexlify('C6E0A1580097740454F6E76EF45F5081')

# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

# create a LoRa socket
sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
sock.setsockopt(socket.SOL_LORA, socket.SO_DR, 0)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
sock.setblocking(True)

GPS = UART(1, baudrate=9600, pins=('G12','G34'))
my_gps = MicropyGPS(location_formatting='dd')
"""            location_formatting (str): Style For Presenting Longitude/Latitude:
                   Decimal Degree Minute (ddm) - 40° 26.767′ N
                   Degrees Minutes Seconds (dms) - 40° 26′ 46″ N
                   Decimal Degrees (dd) - 40.446° N
"""

time.sleep(1)

start_time = time.time()
duracao_20_min = 20 * 60 # 1200 segundos = 20 minutos
sensor_wait = 1

while True:
    eco2_list = []
    tvoc_list = []
    try:
        if sensor_wait:
            while(True):
                if s.data_ready():
                    print('eCO2: %d ppm, TVOC: %d ppb' % (s.eCO2, s.tVOC))
                now = time.time()
                if(now - start_time >= duracao_20_min):
                    print("Já passaram 20 minutos. O sensor já está pronto.")
                    sensor_wait = False
                    time.sleep(3)
                    break
                time.sleep(3)

        start_5_min_count = time.time()
        duracao_5_min = 5 * 60

        while(True):
            now_5_min = time.time()
            if s.data_ready():
                print('eCO2: %d ppm, TVOC: %d ppb' % (s.eCO2, s.tVOC))
                eco2_list.append(s.eCO2)
                print("eCO2 added to eco2 list")
                tvoc_list.append(s.tVOC)
                print("tVOC added to tVOC list")
                time.sleep(10)
            if(now_5_min - start_5_min_count >= duracao_5_min):
                if eco2_list and tvoc_list:
                    break
        while True:
            sentence = GPS.readline()
            if sentence is not None:
                print(sentence)
                for element in range(0, len(sentence)):
                    my_gps.update(chr(sentence[element]))
                if my_gps.valid:
                    lat_raw = my_gps.latitude  # retorna: [graus_decimais, 'N' ou 'S']  
                    lon_raw = my_gps.longitude # retorna: [graus_decimais, 'E' ou 'W']

                    lat_decimal = lat_raw[0] * (-1 if lat_raw[1] == 'S' else 1)
                    lon_decimal = lon_raw[0] * (-1 if lon_raw[1] == 'W' else 1)

                    print('Lat=', lat_decimal, ' Lon=', lon_decimal)

                    lat = (int)(lat_decimal * 10000) + 900000
                    lon = (int)(lon_decimal * 10000) + 1800000

                    eco2_average = sum(eco2_list) / len(eco2_list)
                    tvoc_average = sum(tvoc_list) / len(tvoc_list)
                    print("Average eco2: ", eco2_average)
                    print("Average Tvoc: ", tvoc_average)

                    eco2 = (int)(eco2_average/100)
                    tvoc = (int)(tvoc_average/100)
                    
                    payload = []
                    payload.append((eco2 << 1) | ((tvoc >> 3)  & 0x01))
                    payload.append(((tvoc & 0x07) << 5) | ((lat >> 16) & 0x1F))
                    payload.append((lat >> 8) & 0xFF)
                    payload.append(lat & 0xFF)
                    payload.append((lon >> 16) & 0x3F)
                    payload.append((lon >> 8) & 0xFF)
                    payload.append(lon & 0xFF)
                    print("Payload:", [hex(b) for b in payload])
                    sock.send(bytes(payload))
                    print("sent")
                    time.sleep(1)
                    break
                else:
                    print("Sem fix GPS ainda...")
                    time.sleep(1)
            time.sleep(1)
    except Exception as e:
        print("Erro:", e)
        machine.reset()
