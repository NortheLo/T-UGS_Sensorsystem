from mpu6050 import mpu6050
import time
import math
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue


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
#sen2 = mpu6050(0x69)
def checkSensors():
    sen1.set_accel_range(sen1.ACCEL_RANGE_2G)
    print("Reading sensor sensitivity. For optimal precision value should be -+2g")
    print("First 6050 at I2C adress 0x68: " + str(sen1.read_accel_range()) + "g")
  #  print("Second 6050 at I2C adress 0x69: " + str(sen2.read_accel_range()) + "g")

    #enabel fifo
    sen1.configure_fifo(sen1.FIFO_FLAG_AXYZ)
    sen1.enable_fifo()
    sen1.set_sample_rate_divider(19)
    sen1.reset_fifo()
    

    # if (sen1.read_accel_range() != 2) or (sen2.read_accel_range() != 2):
    #     print("ERROR: Sensors are not used in the correct full scale range!")
    #     return True
    # else:
    #     return True
    return True


def update(frame):
    global figure
    global x_data
    global y_data
    global line
    global animation
    #x_data.append(datetime.datetime.now())
    
    fifoLen=sen1.get_fifo_length()
    if fifoLen < 6:
        print("achtung")
    print(fifoLen//6*6)
    accels = sen1.get_fifo_data_acc(fifoLen//6*6)
    
    y_data += accels[0]
    if len(y_data) > 5000:
        overweight = len(y_data) - 5000
        del y_data[0:overweight]
    x_data = range(0,len(y_data))
    line.set_data(x_data,y_data)
    figure.gca().relim()
    figure.gca().autoscale_view()
    return line,

def sensor_loop():
    time_a=datetime.datetime.now()
    cnt = 0
    while True:
        delta=datetime.datetime.now()-time_a
        time_a=datetime.datetime.now()
        print(delta.total_seconds()*1000)
        # len=sen1.get_fifo_length()
        #accels = sen1.get_fifo_data_acc(len)
        

        #print(accels)
        accl_dat1 = sen1.get_accel_data()
        print(accl_dat1)
        #accl_dat2 = sen2.get_accel_data()
        #gyro_dat1 = sen1.get_gyro_data()
        #gyro_dat2 = sen2.get_gyro_data()
        

        # Extracting the accelerations and gyro values from the dict; QnD approach
        # for k, v in accl_dat1.items():
        #     if k == 'x':
        #         accl1_x[cnt] = "{:10.4f}".format(v)
        #     if k == 'y':
        #         accl1_y[cnt] = "{:10.4f}".format(v)
        #     if k == 'z':
        #         accl1_z[cnt] = "{:10.4f}".format(v)

        # for k, v in accl_dat2.items():
        #     if k == 'x':
        #         accl2_x[cnt] = "{:10.4f}".format(v)
        #     if k == 'y':
        #         accl2_y[cnt] = "{:10.4f}".format(v)
        #     if k == 'z':
        #         accl2_z[cnt] = "{:10.4f}".format(v)
        
        # for k, v in gyro_dat1.items():
        #     if k == 'x':
        #         gyro1_x[cnt] = "{:10.4f}".format(v)
        #     if k == 'y':
        #         gyro1_y[cnt] = "{:10.4f}".format(v)
        #     if k == 'z':
        #         gyro1_z[cnt] = "{:10.4f}".format(v)

        # for k, v in gyro_dat2.items():
        #     if k == 'x':
        #         gyro2_x[cnt] = "{:10.4f}".format(v)
        #     if k == 'y':
        #         gyro2_y[cnt] = "{:10.4f}".format(v)
        #     if k == 'z':
        #         gyro2_z[cnt] = "{:10.4f}".format(v)

        #accl_vec[cnt] = math.sqrt(pow(accl1_x[cnt], 2) + pow(accl1_y[cnt], 2) + pow(accl1_z[cnt], 2))
        # print("+----Accleration-------------||----Gyro-----------------+")
        # print("|" + str(accl1_x[cnt])
        #    + " | " + str(accl1_y[cnt]) 
        #    + " | " + str(accl1_z[cnt]) 
        #    + " || " + str(gyro1_x[cnt])
        #    + " | " + str(gyro1_y[cnt])
        #    + " | " + str(gyro1_z[cnt]) 
        #    + "|")
        
        # cnt += 1
        # if cnt >= (WINDOW * SAMPLE_RATE):
        #     cnt = 0
        # #     #sen1_fft = np.abs(np.fft.fft(accl1_z))
        #     #sen2_fft = np.abs(np.fft.fft(gyro1_y))   
        #     #plt.plot(t, sen1_fft)
        #     #plt.plot(t, sen1_fft)

        #     #plt.plot(t, sen2_fft)
        #     plt.plot(t,accl1_x)
            
        #     plt.pause(0.001)

def main():
    global figure
    global x_data
    global y_data
    global line
    global animation
    global dataQueue
    if(checkSensors()):
        x_data, y_data = [], []

        figure = plt.figure()
        line, = plt.plot(x_data, y_data, '-')
        #sen1.reset_fifo()
        #animation = FuncAnimation(figure, update, interval=1)
        #plt.show()
        sensor_loop()

if __name__ == "__main__":
    main()










