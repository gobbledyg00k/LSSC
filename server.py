from opcua import Client
import struct
import math

url = "opc.tcp://Gobbledygook:53530/OPCUA/SimulationServer"
serv = Client(url)

def ServerInit():
    serv.connect()

def NormVector(vec):
    norm = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1] + vec[2]*vec[2])
    vec[0] = vec[0]/norm
    vec[1] = vec[1]/norm
    vec[2] = vec[2]/norm
    return vec

def getNadirFromServer():
    vector = [0,0,0]
    vector[0] = serv.get_node("ns=3;s=1009/0:X").get_value()
    vector[1] = serv.get_node("ns=3;s=1009/0:Y").get_value()
    vector[2] = serv.get_node("ns=3;s=1009/0:Z").get_value()
    # vector = [1,2,3]
    vector = NormVector(vector)
    print(vector, end='')
    return vector

def getMagFieldFromServer():
    vector = [0,0,0]
    vector[0] = serv.get_node("ns=3;s=1011/0:X").get_value()
    vector[1] = serv.get_node("ns=3;s=1011/0:Y").get_value()
    vector[2] = serv.get_node("ns=3;s=1011/0:Z").get_value()
    # vector = [100,200,300]
    print(vector, end='')
    return vector

def getAngVelFromServer():
    vector = [0,0,0]
    vector[0] = serv.get_node("ns=3;s=1012/0:X").get_value()
    vector[1] = serv.get_node("ns=3;s=1012/0:Y").get_value()
    vector[2] = serv.get_node("ns=3;s=1012/0:Z").get_value()
    # vector = [7505,15011,22517] #grad*131
    vector[0] *= 131
    vector[1] *= 131
    vector[2] *= 131
    print(vector, end='')
    return vector

def getSunDirectionFromServer():
    vector = [0,0,0]
    vector[0] = serv.get_node("ns=3;s=1010/0:X").get_value()
    vector[1] = serv.get_node("ns=3;s=1010/0:Y").get_value()
    vector[2] = serv.get_node("ns=3;s=1010/0:Z").get_value()
    # vector = [1,2,3]
    vector = NormVector(vector)
    print(vector, end='')
    return vector

def getOrbitHeightFromServer():
    h_orbit = serv.get_node("ns=3;i=1013").get_value()
    # h_orbit = 559000
    return h_orbit/1000

def getAccelFromServer():
    vector = [0,0,0]
    # vector = [1,2,3]
    
    print(vector, end='')
    return vector

def getCoilByByte(addr):
    match addr:
        case 1:
            coil = "ns=3;i=1015"
        case 2:
            coil = "ns=3;i=1016"
        case 3:
            coil = "ns=3;i=1017"
        case 4:
            coil = "ns=3;i=1018"
        case 5:
            coil = "ns=3;i=1019"
        case 6:
            coil = "ns=3;i=1020"
        case _:
            coil = "error"
    return coil

def sendPWMOnServer(data):
    for i in range(int(len(data)/5)):
        tmp = data[i*5:i*5+4]
        pwm = struct.unpack('<f',tmp)[0]
        coil = getCoilByByte(data[i*5+4])

        if( pwm > 100):
            pwm = 1.0
        elif( pwm < -100):
            pwm = -1.0
        else:
            pwm = pwm/100

        if(coil != "error"):
            print(coil)
            print(pwm)
            serv.get_node(coil).set_value(pwm)

# if __name__ == "__main__":
#     tmp = b'\x01\x01\x41\xF0\x01\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03'
#     zero = b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x02\x00\x00\x00\x00\x03'
#     ServerInit()
#     sendPWMOnServer(tmp)