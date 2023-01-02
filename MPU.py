# Reading and evaluating values in the time domain 
# from the MPU-6050 with a moving average and a threshold
 
from mpu6050 import mpu6050
import time
import numpy as np

sen1 = mpu6050(0x68)
sen2 = mpu6050(0x69)

threshold = 0.40
detection = False
hysteresis = 10
window_size = 5

print("MPU 1 Range: " + str(sen1.read_accel_range()))
print("MPU 2 Range: " + str(sen2.read_accel_range()))

accl_dat1 = sen1.get_accel_data()
accl_dat2 = sen2.get_accel_data()

sen1_arr = np.empty(window_size, dtype='float32')
sen2_arr = np.empty(window_size, dtype='float32')
cnt = 0

while True:
    accl_dat1 = sen1.get_accel_data()
    accl_dat2 = sen2.get_accel_data()
    
    # Extracting the z-axis data from the dict
    for k, v in accl_dat1.items():
        if k == 'z':
            sen1_z = v

    for k, v in accl_dat2.items():
        if k == 'z':
            sen2_z = v

    # When detecting do not generate new avg because it would spoil the threshold comparision
    if detection == False:
        sen1_arr[cnt] = sen1_z
        sen1_avg = np.average(sen1_arr)
        sen2_arr[cnt] = sen2_z
        sen2_avg = np.average(sen2_arr)
    print("Sensor 1: " + str(sen1_z) + " Sensor 1 Avg: " + str(sen1_avg))
    print("Sensor 2: " + str(sen2_z) + " Sensor 2 Avg: " + str(sen2_avg))
    
    if ((sen1_z - sen1_avg) > threshold) and ((sen2_z - sen2_avg) > threshold):
        detection = True
        hysteresis = 0
        print("-------------------------------------\nStep detected!!\n-------------------------------------")

    elif detection == True:
        hysteresis += 1
        if hysteresis == 10:
            detection = False 

    cnt += 1
    if cnt > (window_size - 1):
        cnt = 0    