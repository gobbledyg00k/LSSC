import numpy as np
import serial
import time
from math import *
from crc16 import *
from dsg import *
from server import *

PREAMBULA = b'\xAA'
DESTINATION_ADDR = b'\xF0'
ZERO_BYTE = b'\x00'
COMMAND = b'\x93'
IMGDATANUM = b'\x00\x0C'
ZERODATANUM = b'\x00\x00'
FW_VERSION = b'OMv2.00\r\n'
TEST_DATA = b'\x00\x00\x00\x00\x00\x00\x00\x00'

ins = serial.Serial('COM4')
ins.baudrate = 1000000
ins.bytesize = 8
ins.parity   = 'N'
ins.stopbits = 1

def getSensorByByte(addr):
    sensor = -1
    match addr:
        case b'\x00':
            sensor = 0
        case b'\x01':
            sensor = 1
        case b'\x02':
            sensor = 2
        case b'\x03':
            sensor = 3
        case b'\x04':
            sensor = 4
        case b'\x05':
            sensor = 5
        case b'\x06':
            sensor = 6
        case b'\xFF':
            sensor = 255
    return sensor

def getDataNum(byte_string):
    length = len(byte_string)
    length_bytes = length.to_bytes(2, "little")
    return length_bytes

def responseCommand(byte_string):
    first_byte = byte_string[0]
    modified_byte = first_byte | 0x80
    modified_byte_string = bytes([modified_byte]) + byte_string[1:]
    return modified_byte_string

def readPacket():
    preambula = ins.read(1)
    dest_addr = ins.read(1)
    src_addr = ins.read(1)
    reserve = ins.read(2)
    command = ins.read(1)
    data_num = ins.read(2)
    num_of_data = int.from_bytes(data_num, "little")
    if(num_of_data != 0):
        ins_data = ins.read(num_of_data)
    else:
        ins_data = b''

    crc_in = ins.read(2)
    packet = preambula + dest_addr + src_addr + reserve + command + data_num + ins_data + crc_in
    # print(packet)
    return command, dest_addr, ins_data

def sendMessage(sensor, command, data):
    send_packet = PREAMBULA + DESTINATION_ADDR + sensor + ZERO_BYTE + ZERO_BYTE + \
    responseCommand(command) + getDataNum(data) + data

    send_crc = calculate_crc_16(send_packet).to_bytes(2, "little")
    send_packet = send_packet + send_crc
    ins.write(send_packet)
    print("\ngive an answer")
    # print(send_packet)

if __name__ == "__main__":
    ServerInit()
    print("server init")
    while True:
        command, sensor, in_data = readPacket()
        print("read packet ", end='')
        print(command, end='')
        # print(sensor)
        match command:
            # case b'\x00':               #Прием коэффициента ШИМ для катушек
            #     sendPWMOnServer(in_data)

            case b'\x0b':               #Получить версию прошивки
                data = FW_VERSION
                sendMessage(sensor, command, data)

            case b'\x06':               #Прочитать угды СД из памяти
                data = GetStoragedSunDirectionData(getSensorByByte(sensor))
                sendMessage(sensor, command, data)

            case b'\x13':               #Получить ИК фото с ДГ
                data = GetSingleImage(getSensorByByte(sensor))
                time.sleep(0.3)
                sendMessage(sensor, command, data)

            case b'\x14':               #Прочитать ИК фото с ДГ из памяти
                data = GetStoragedImage(getSensorByByte(sensor))
                time.sleep(0.3)
                sendMessage(sensor, command, data)

            case b'\x21':               #Получить данные с ДУС
                data = GetSingleAngVelData(getSensorByByte(sensor))
                sendMessage(sensor, command, data)

            case b'\x23':               #Получить данные с магнитометра
                data = GetSingleMagData(getSensorByByte(sensor))
                sendMessage(sensor, command, data)

            case b'\x26':               #Прочитать данные магнитометра из памяти
                data = GetStoragedMagData(getSensorByByte(sensor))
                sendMessage(sensor, command, data)
                
            case b'\x27':               #Прочитать данные ДУС, акселерометра из памяти.
                data = GetStoragedAccelData(getSensorByByte(sensor))[:-2]
                data += GetStoragedAngVelData(getSensorByByte(sensor))
                sendMessage(sensor, command, data)

            case b'\x44':               #Широковещательная. ДС, снимок и углы. Вычитывается командой 0х06
                StorageBroadcastSunDirectionData()

            case b'\x53':               #Широковещательная. ДГ, снимок. Вычитывается командой 0х14
                StorageBroadcastImages()

            case b'\x63':               #Широковещательная. Данные магнитометра. Вычитывается командой 0х26
                StorageBroadcastMagData()

            case b'\x64':               #Широковещательная. Данные ДУС и акселя.Вычитывается командой 0х27
                StorageBroadcastAngVelData()
                StorageBroadcastAccelData()
        
        print("done")
