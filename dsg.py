import numpy as np
import math
import copy
from math import *
from server import *

HS_PHOTO_WIDTH = 32
HS_PHOTO_HEIGHT = 24
HS_PHOTO_CORNER_OFF = 7

HS_CLUSTER_NUM = 3
HS_KMEAN_MAX_ITER = 5
HS_SMART_MAX_ITER = 3
HS_ITER_THRESHOLD = 1.0

HOT_PIXEL_TEMPERATURE = 10.0
EARTH_MIN_TEMPERATURE = -80.0
HS_PHOTO_ERTH_MIN_AREA = 20

HS_POINTS_NUM = 32
HS_NUM = 6

ANGLE_DEV_NUM = 8

HS_EARTH_RADIUS = 6371

photos_storage = np.zeros((6, HS_PHOTO_HEIGHT, HS_PHOTO_WIDTH))
mag_storage = np.zeros((6, 3))
sun_storage = np.zeros((6, 4))
angvel_storage = np.zeros((6, 3))
accel_storage = np.zeros((6, 3))
            
def HS_PI():
    return 3.14159265358979323846

class hs_photo_data_t:
    def __init__(self):
        self.min_temp = 0
        self.max_temp = 0
    
        self.centers = np.zeros((HS_CLUSTER_NUM))
        self.cluster_volumes = np.zeros((HS_CLUSTER_NUM))
        self.clustered = np.zeros((HS_PHOTO_HEIGHT, HS_PHOTO_WIDTH))
    
        self.horizon_points_num = 0
        self.number_clust_iteration = 0
        self.horizon_points = np.zeros((HS_POINTS_NUM, 2))
        self.horizon_vectors = np.zeros((HS_POINTS_NUM, 3))


class hs_vectors_data_t:
    def __init__(self):
        self.heap = np.zeros((HS_NUM * HS_POINTS_NUM, 3))
        self.hs_vectors = np.zeros((HS_NUM, HS_POINTS_NUM, 3))
        self.hs_vectors_num = np.zeros((HS_NUM))
        self.heap_size = 0

class hs_alg_data_t:
    def __init__(self):
        self.read_errors = 0
        self.clust_num_iter = 0
        self.clust_temp = np.zeros((3))
        self.num_horizon_points = 0
        self.angle_deviations = np.zeros((ANGLE_DEV_NUM))

def Coordinate_Transformation_CubeSat_to_OM(vect, N):
    x0 = vect[0]
    y0 = vect[1]
    z0 = vect[2]
    x = x0
    y = y0
    z = z0

    match N:
        case 1:
            x = -x0
            y = -z0
            z = y0
        case 2:
            x = -y0
            y = -z0
            z = -x0
        case 3:
            x = x0
            y = -z0
            z = -y0
        case 4:
            x = y0
            y = -z0
            z = x0
        case 5:
            x = -x0
            y = y0
            z = z0

    vect[0] = x
    vect[1] = y
    vect[2] = z

def Coordinate_Transformation_OM_to_CubeSat(vect, N):
    x0 = vect[0]
    y0 = vect[1]
    z0 = vect[2]
    x = x0
    y = y0
    z = z0

    match N:
        case 1:
            x = -x0
            y = z0
            z = -y0
        case 2:
            x = -z0
            y = -x0
            z = -y0
        case 3:
            x = x0
            y = -z0
            z = -y0
        case 4:
            x = z0
            y = x0
            z = -y0
        case 5:
            x = -x0
            y = y0
            z = z0
        case 6:
            x = -x0
            y = -y0
            z = -z0

    vect[0] = x
    vect[1] = y
    vect[2] = z

#          #
# Converts #
#          #

def Scale(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def ConvertMagVectorToBytes(vector):
    length = len(vector)
    converted = b''
    for i in range(0, length, 1):
        converted += np.uint16(Scale(vector[i], -800.0, 800.0, 0, 65535)).tobytes()
    return converted + b'\x14'

def ConvertSunVectorToBytes(vector):
    length = len(vector)
    converted = b''
    for i in range(0, length, 1):
        converted += np.float32(vector[i]).tobytes()
    return converted + b'\x00\x00'

def ConvertAngVelVectorToBytes(vector):
    length = len(vector)
    converted = b'\x00\x14'
    for i in range(0, length, 1):
        converted += np.int16(vector[i])
    return converted

def ConvertAccelVectorToBytes(vector):
    length = len(vector)
    converted = b''
    for i in range(0, length, 1):
        converted += np.int16(vector[i])
    converted += b'\x00\x14'
    return converted

#                #
# Horizon Sensor #
#                #

def HS_get_vectors_from_points(hs_prop):
    x_cor = y_cor = r = zenith = azimuth = 0
   
    for i in range(hs_prop.horizon_points_num):
        x_cor = hs_prop.horizon_points[i][1] - float(HS_PHOTO_HEIGHT) / 2
        y_cor = float(HS_PHOTO_WIDTH) / 2 - hs_prop.horizon_points[i][0]
        r = sqrt(x_cor * x_cor + y_cor * y_cor)
        zenith = r / (float(HS_PHOTO_WIDTH) / 2) * 55 * HS_PI() / 180
        azimuth = atan2(y_cor, x_cor)
        hs_prop.horizon_vectors[i][0] = sin(zenith) * cos(azimuth)
        hs_prop.horizon_vectors[i][1] = sin(zenith) * sin(azimuth)
        hs_prop.horizon_vectors[i][2] = cos(zenith)
   
    return 0


def getGeneratedPixel(x, y, hs_num, h_orbit, nadir_vector):
    
    earth_angle = nadir_to_pixel_angle = 0
    hs_prop = hs_photo_data_t()
   
    hs_prop.horizon_points_num = 1

    hs_prop.horizon_points[0][0] = x
    hs_prop.horizon_points[0][1] = y
    HS_get_vectors_from_points(hs_prop)

    Coordinate_Transformation_OM_to_CubeSat(hs_prop.horizon_vectors[0], hs_num)
   
   
    earth_angle = asin(HS_EARTH_RADIUS / (HS_EARTH_RADIUS + h_orbit))
    nadir_to_pixel_angle = acos(np.dot(nadir_vector, hs_prop.horizon_vectors[0]))

    earth_angle = asin(HS_EARTH_RADIUS / (HS_EARTH_RADIUS + h_orbit))
    nadir_to_pixel_angle = acos(np.dot(nadir_vector, hs_prop.horizon_vectors[0]))
    if (nadir_to_pixel_angle <= earth_angle):
        return -49 + (40*np.random.rand() - 20)
    elif( (nadir_to_pixel_angle-earth_angle) > 0.1 ):
        return -253 + (40*np.random.rand() - 20)
    else:
        return -150 + (40*np.random.rand() - 20)

def GenerateHsImage(img, hs_num, h_orbit, nadir_vector):
    for j in range(HS_PHOTO_HEIGHT):
        for i in range(HS_PHOTO_WIDTH):
            img[j][i] = getGeneratedPixel(i + 0.5, j + 0.5, hs_num, h_orbit, nadir_vector)

def GetSingleImage(hs_num):
    nadir_vector = getNadirFromServer()
    h_orbit = getOrbitHeightFromServer()
    img = b''
    for j in range(HS_PHOTO_HEIGHT):
        for i in range(HS_PHOTO_WIDTH):
            img += np.float32(getGeneratedPixel(i + 0.5, j + 0.5, hs_num, h_orbit, nadir_vector)).tobytes()
    return img

def StorageBroadcastImages():
    nadir_vector = getNadirFromServer()
    #h_orbit = getHeightFromServer()
    h_orbit = 545
    for i in range(6):
        GenerateHsImage(photos_storage[i], i + 1, h_orbit, nadir_vector)

def GetStoragedImage(hs_num):
    img = b''
    for j in range(HS_PHOTO_HEIGHT):
        for i in range(HS_PHOTO_WIDTH):
            img += np.float32(photos_storage[hs_num - 1, j, i]).tobytes()
    return img

#            #
# Mag Sensor #
#            #

def GetHsMagData(storage, hs_num, vector):
    Coordinate_Transformation_CubeSat_to_OM(vector, hs_num)
    storage[0] = -1 * vector[0]  #Перевод в систему координат магнитометра
    storage[1] = -1 * vector[1]  #Перевод в систему координат магнитометра
    storage[2] = vector[2]

def GetSingleMagData(hs_num):
    mag_vector = getMagFieldFromServer()
    if (hs_num == 255):
        mag_vector[0] = -1 *  mag_vector[0]  #Перевод в систему координат магнитометра
        mag_vector[1] = -1 *  mag_vector[1]  #Перевод в систему координат магнитометра
        return ConvertMagVectorToBytes(mag_vector)
    else:
        Coordinate_Transformation_CubeSat_to_OM(mag_vector, hs_num)        
        mag_vector[0] = -1 *  mag_vector[0]  #Перевод в систему координат магнитометра
        mag_vector[1] = -1 *  mag_vector[1]  #Перевод в систему координат магнитометра
        return ConvertMagVectorToBytes(mag_vector)

def StorageBroadcastMagData():
    mag_vector = getMagFieldFromServer()
    for i in range (6):
        vec_to_send = copy.deepcopy(mag_vector)
        GetHsMagData(mag_storage[i], i, vec_to_send)

def GetStoragedMagData(hs_num):
    return ConvertMagVectorToBytes(mag_storage[hs_num])

#                #
# Sun-dir Sensor #
#                #

def GetHSSunDirectionData(storage, hs_num, temp_vec):
    Coordinate_Transformation_CubeSat_to_OM(temp_vec, hs_num)
    zenith = np.float32(math.degrees(math.acos(temp_vec[2] / np.linalg.norm(temp_vec))))
    azimuth = np.float32(math.degrees(math.atan2(temp_vec[1], temp_vec[0])))
    if zenith > 60.0 or zenith < -60.0:
        storage[0] = np.float32(0.0)
        storage[1] = np.float32(0.0)
        storage[2] = np.float32(0.0)
        storage[3] = np.float32(0.0)
    else:
        storage[0] = np.float32(1.0)
        storage[1] = np.float32(1.0)
        storage[2] = zenith
        storage[3] = azimuth 

def StorageBroadcastSunDirectionData():
    sun_vector = getSunDirectionFromServer()
    for i in range (6):
        vec_to_send = copy.deepcopy(sun_vector)
        GetHSSunDirectionData(sun_storage[i], i, vec_to_send)

def GetStoragedSunDirectionData(hs_num):
    return ConvertSunVectorToBytes(sun_storage[hs_num])

#                #
# Ang-vel Sensor #
#                #

def GetHsAngVelData(storage, hs_num, vector):
    Coordinate_Transformation_CubeSat_to_OM(vector, hs_num)
    storage[0] = -1 * vector[0]  #Перевод в систему координат гиро
    storage[1] = -1 * vector[1]  #Перевод в систему координат гиро
    storage[2] = -1 * vector[2]  #Перевод в систему координат гиро

def GetSingleAngVelData(hs_num):
    vel_vector = getAngVelFromServer()
    Coordinate_Transformation_CubeSat_to_OM(vel_vector, hs_num)
    res = b'\x00\x14'
    res += np.int16(-1 * vel_vector[0]).tobytes()  #Перевод в систему координат гиро
    res += np.int16(-1 * vel_vector[1]).tobytes()  #Перевод в систему координат гиро
    res += np.int16(-1 * vel_vector[2]).tobytes()  #Перевод в систему координат гиро
    return res

def StorageBroadcastAngVelData():
    vel_vector = getAngVelFromServer()
    for i in range (6):
        vec_to_send = copy.deepcopy(vel_vector)
        GetHsAngVelData(angvel_storage[i], i, vec_to_send)

def GetStoragedAngVelData(hs_num):
    return ConvertAngVelVectorToBytes(angvel_storage[hs_num])

#              #
# Accel Sensor #
#              #

def GetHsAccelData(storage, hs_num, vector):
    Coordinate_Transformation_CubeSat_to_OM(vector, hs_num)
    storage[0] = -1 * vector[0]  #Перевод в систему координат акселя
    storage[1] = -1 * vector[1]  #Перевод в систему координат акселя
    storage[2] = -1 * vector[2]  #Перевод в систему координат акселя

def GetSingleAccelData(hs_num):
    accel_vector = getAccelFromServer()
    Coordinate_Transformation_CubeSat_to_OM(accel_vector, hs_num)
    res = b''
    res += np.int16(-1 * accel_vector[0]).tobytes()  #Перевод в систему координат акселя
    res += np.int16(-1 * accel_vector[1]).tobytes()  #Перевод в систему координат акселя
    res += np.int16(-1 * accel_vector[2]).tobytes()  #Перевод в систему координат акселя
    res += b'\x00\x14'
    return res

def StorageBroadcastAccelData():
    accel_vector = getAccelFromServer()
    for i in range (6):
        vec_to_send = copy.deepcopy(accel_vector)
        GetHsAccelData(accel_storage[i], i, vec_to_send)

def GetStoragedAccelData(hs_num):
    return ConvertAccelVectorToBytes(accel_storage[hs_num])