from mpu6050 import mpu6050
import time
import math
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue

###SETTINGS###
WINDOWSIZE = 5000
SAMPLERATE = 500

sen1 = mpu6050(0x68)
def checkSensors():
    sen1.set_accel_range(sen1.ACCEL_RANGE_2G)
  
    #enabel fifo
    sen1.enable_fifo()
    sen1.configure_fifo(sen1.FIFO_FLAG_AXYZ)
    
    sen1.setSampleRate(SAMPLERATE)
    sen1.reset_fifo()
    return True
    

def fftCalc(buffer,line):
    N = len(buffer)
    yf = fft(buffer)
    xf = fftfreq(N,1/SAMPLERATE)
    #print(xf)
    #print(np.abs(yf))
    line.set_data(xf,np.abs(yf))

def update(frame):
    global figure1
    global x_data
    global y_data
    global line
    global animation
    global ax1
    global ax2
    #x_data.append(datetime.datetime.now())
    fifoLen=sen1.get_fifo_length()

    #print(fifoLen//6*6)
    accels = sen1.get_fifo_data_acc(fifoLen//6*6)
    
    y_data += accels[1]
    #print(np.abs(accels[0]))
    # test = []
    # for i in range(0,len(accels[0])):
    #     test.append(accels[1][i] )

    #y_data += test
    if len(y_data) > WINDOWSIZE:
        overweight = len(y_data) - WINDOWSIZE
        del y_data[0:overweight]
    x_data = range(0,len(y_data))
    ydat_calib = np.subtract(y_data,15300)
    line[0].set_data(x_data,ydat_calib)
    
    fftCalc(ydat_calib,line[1])

    ax1.autoscale_view()
    ax1.relim()
    
    
    
    #ax2.set_ylim(-5, 10) WARUM?!
    #ax2.set_xlim(0,200)
    ax2.autoscale_view(scalex=True,scaley=True,tight=False)
    ax2.relim()
    return line,

        



def main():
    global figure1
    global figure2
    global figure2_axis
    global x_data
    global y_data
    global ax1
    global ax2
    global line
    global animation

    if(checkSensors()):
        x_data, y_data = [], []

        figure1, (ax1, ax2) = plt.subplots(2,1)
        #line, = plt.plot(x_data, y_data, '-')
        line1, = ax1.plot([], [], lw=2, color='r')
        line2, = ax2.plot([], [], lw=2, color='r')
        line = [line1, line2]

        #sen1.reset_fifo()
        animation = FuncAnimation(figure1, update, interval=1, repeat=False)
        plt.show()

if __name__ == "__main__":
    main()