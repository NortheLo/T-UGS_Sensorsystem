from mpu6050 import mpu6050
import time
import math
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue

sen1 = mpu6050(0x68)
def checkSensors():
    sen1.set_accel_range(sen1.ACCEL_RANGE_2G)
  
    #enabel fifo
    sen1.enable_fifo()
    sen1.configure_fifo(sen1.FIFO_FLAG_AXYZ)
    
    sen1.setSampleRate(500)
    sen1.reset_fifo()
    return True
    


def update(frame):
    global figure
    global x_data
    global y_data
    global line
    global animation
    #x_data.append(datetime.datetime.now())
    
    fifoLen=sen1.get_fifo_length()

    #print(fifoLen//6*6)
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
        animation = FuncAnimation(figure, update, interval=1)
        plt.show()

if __name__ == "__main__":
    main()