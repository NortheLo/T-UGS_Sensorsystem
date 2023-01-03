from mpu6050 import mpu6050
import time
import math
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 

import matplotlib.pyplot as plt

SAMPLE_RATE = 40
WINDOW = 1
t = np.linspace(0, WINDOW, SAMPLE_RATE * WINDOW)
plt.axis([0, 0.5, 0, 20])

accl1_x = np.zeros(SAMPLE_RATE * WINDOW)
accl2_x = np.zeros(SAMPLE_RATE * WINDOW)
accl1_y = np.zeros(SAMPLE_RATE * WINDOW)
accl2_y = np.zeros(SAMPLE_RATE * WINDOW)
accl1_z = np.zeros(SAMPLE_RATE * WINDOW)
accl2_z = np.zeros(SAMPLE_RATE * WINDOW)

gyro1_x = np.zeros(SAMPLE_RATE * WINDOW)
gyro2_x = np.zeros(SAMPLE_RATE * WINDOW)
gyro1_y = np.zeros(SAMPLE_RATE * WINDOW)
gyro2_y = np.zeros(SAMPLE_RATE * WINDOW)
gyro1_z = np.zeros(SAMPLE_RATE * WINDOW)
gyro2_z = np.zeros(SAMPLE_RATE * WINDOW)

accl_vec = np.zeros(SAMPLE_RATE * WINDOW)

sen1 = mpu6050(0x68)
sen2 = mpu6050(0x69)

def checkSensors():
    print("Reading sensor sensitivity. For optimal precision value should be -+2g")
    print("First 6050 at I2C adress 0x68: " + str(sen1.read_accel_range()) + "g")
    print("Second 6050 at I2C adress 0x69: " + str(sen2.read_accel_range()) + "g")

    if (sen1.read_accel_range() != 2) or (sen2.read_accel_range() != 2):
        print("ERROR: Sensors are not used in the correct full scale range!")
        return False
    else:
        return True


def sensor_loop():
    cnt = 0
    while True:
        accl_dat1 = sen1.get_accel_data()
        accl_dat2 = sen2.get_accel_data()
        gyro_dat1 = sen1.get_gyro_data()
        gyro_dat2 = sen2.get_gyro_data()
        
        # Extracting the accelerations and gyro values from the dict; QnD approach
        for k, v in accl_dat1.items():
            if k == 'x':
                accl1_x[cnt] = "{:10.4f}".format(v)
            if k == 'y':
                accl1_y[cnt] = "{:10.4f}".format(v)
            if k == 'z':
                accl1_z[cnt] = "{:10.4f}".format(v)

        for k, v in accl_dat2.items():
            if k == 'x':
                accl2_x[cnt] = "{:10.4f}".format(v)
            if k == 'y':
                accl2_y[cnt] = "{:10.4f}".format(v)
            if k == 'z':
                accl2_z[cnt] = "{:10.4f}".format(v)
        
        for k, v in gyro_dat1.items():
            if k == 'x':
                gyro1_x[cnt] = "{:10.4f}".format(v)
            if k == 'y':
                gyro1_y[cnt] = "{:10.4f}".format(v)
            if k == 'z':
                gyro1_z[cnt] = "{:10.4f}".format(v)

        for k, v in gyro_dat2.items():
            if k == 'x':
                gyro2_x[cnt] = "{:10.4f}".format(v)
            if k == 'y':
                gyro2_y[cnt] = "{:10.4f}".format(v)
            if k == 'z':
                gyro2_z[cnt] = "{:10.4f}".format(v)

        accl_vec[cnt] = math.sqrt(pow(accl1_x[cnt], 2) + pow(accl1_y[cnt], 2) + pow(accl1_z[cnt], 2))
        print("+----Accleration-------------||----Gyro-----------------+")
        print("|" + str(accl1_x[cnt])
           + " | " + str(accl1_y[cnt]) 
           + " | " + str(accl1_z[cnt]) 
           + " || " + str(gyro1_x[cnt])
           + " | " + str(gyro1_y[cnt])
           + " | " + str(gyro1_z[cnt]) 
           + "|")
        
        cnt += 1
        if cnt >= (WINDOW * SAMPLE_RATE):
            cnt = 0
            sen1_fft = np.abs(np.fft.fft(accl1_z))
            #sen2_fft = np.abs(np.fft.fft(gyro1_y))   
            plt.plot(t, sen1_fft)
            #plt.plot(t, sen2_fft)
            plt.draw()
            plt.pause(0.01)
            print("New FFT Plot")

def main():
    if(checkSensors()):
        sensor_loop()

if __name__ == "__main__":
    main()