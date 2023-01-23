from mpu6050 import mpu6050
import time
import math
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import scipy.signal
import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import lfilter
from scipy.signal import savgol_filter

#tried savgol, lfilter, butterworth

###SETTINGS###
WINDOWSIZE = 2000
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
    

def update(frame):
    global figure1
    global x_data
    global y_data
    global line
    global animation
    global ax1
    global ax2
    global first
    #x_data.append(datetime.datetime.now())
    fifoLen=sen1.get_fifo_length()

    #print(fifoLen//6*6)
    if(first):
        sen1.reset_fifo()
        first=False
    accels = sen1.get_fifo_data_acc(fifoLen//6*6)
    b, a = scipy.signal.butter(3, 11/(SAMPLERATE/2), btype='low')
    #b, a = scipy.signal.butter(6, [20/(SAMPLERATE/2), 45/(SAMPLERATE/2)], btype='band')
    y_data += accels[2]
    data_calibrated = np.subtract(y_data,15250)
    window = scipy.signal.windows.tukey(len(data_calibrated))
    #window = scipy.signal.windows.hamming(len(data_calibrated))
    data_windowed = data_calibrated * window
    filtered = scipy.signal.filtfilt(b, a, data_calibrated)
    #filtered = lfilter([1.0 / 15] * 15, 1, data_calibrated)
    #filtered = savgol_filter(data_calibrated, 101, 2)
    if len(y_data) > WINDOWSIZE:
        overweight = len(y_data) - WINDOWSIZE
        del y_data[0:overweight]
    x_data = range(0,len(y_data))
    line[0].set_data(x_data,y_data)
    line[1].set_data(x_data,filtered[:WINDOWSIZE])
    #print(len(filtered[:5000]))
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
    global first
    first = True
    if(checkSensors()):
        x_data, y_data = [], []

        figure1, (ax1, ax2) = plt.subplots(2,1)
        #line, = plt.plot(x_data, y_data, '-')
        line1, = ax1.plot([], [], lw=2, color='r')
        line2, = ax2.plot([], [], lw=2, color='b')
        line = [line1, line2]

        #sen1.reset_fifo()
        animation = FuncAnimation(figure1, update, interval=1, repeat=False)
        plt.show()
        

if __name__ == "__main__":
    main()
    print("test")