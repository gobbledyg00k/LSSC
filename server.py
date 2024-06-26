from opcua import Client
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
    vector = [1,2,3]
    vector = NormVector(vector)
    return vector

def getMagFieldFromServer():
    vector = [0,0,0]
    vector[0] = serv.get_node("ns=3;s=1011/0:X").get_value()
    vector[1] = serv.get_node("ns=3;s=1011/0:Y").get_value()
    vector[2] = serv.get_node("ns=3;s=1011/0:Z").get_value()
    vector = [100,200,300]
    return vector

def getAngVelFromServer():
    vector = [0,0,0]
    vector[0] = serv.get_node("ns=3;s=1012/0:X").get_value()
    vector[1] = serv.get_node("ns=3;s=1012/0:Y").get_value()
    vector[2] = serv.get_node("ns=3;s=1012/0:Z").get_value()
    vector = [7505,15011,22517] #grad*131
    return vector

def getSunDirectionFromServer():
    vector = [0,0,0]
    vector[0] = serv.get_node("ns=3;s=1010/0:X").get_value()
    vector[1] = serv.get_node("ns=3;s=1010/0:Y").get_value()
    vector[2] = serv.get_node("ns=3;s=1010/0:Z").get_value()
    vector = [1,2,3]
    vector = NormVector(vector)
    return vector

def getOrbitHeightFromServer():
    h_orbit = serv.get_node("ns=3;i=1013").get_value()
    h_orbit = 559000
    return h_orbit/1000

def getAccelFromServer():
    vector = [0,0,0]
    vector = [1,2,3]
    return vector