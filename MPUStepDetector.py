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
WINDOWSIZE = 5000 # samples
SAMPLERATE = 500 # Hz

PEAKTHRESHHOLD = 200 # raw
SETTLEMAX = 500 # raw
NLARGEST = 100 # count

STEPDURATION_MIN = 50 # minimum time between steps in ms
STEPDURATION_MAX = 1300# maximum time between steps in ms

####
SAMPLETIME = 1/500*1000 # ms
####

sen1 = mpu6050(0x68)
def checkSensors():
    sen1.set_accel_range(sen1.ACCEL_RANGE_2G)
  
    #enabel fifo
    sen1.enable_fifo()
    sen1.configure_fifo(sen1.FIFO_FLAG_AXYZ)
    
    sen1.setSampleRate(SAMPLERATE)
    sen1.reset_fifo()
    return True

def calibrate(buffer):
    peaks = np.argpartition(buffer,-NLARGEST)[-NLARGEST:]
    bufferNoPeaks = np.delete(buffer,peaks)
    rms = np.sqrt(np.mean(bufferNoPeaks**2))
    return rms

def detector(rms,buffer):
    steps = []
    peakInd = np.where(buffer > (rms+PEAKTHRESHHOLD))
    #settleInd = np.argwhere(buffer < (rms+SETTLEMAX))
    #print(peakInd[0])
    last = len(buffer)
    for idx in peakInd[0]:
        if (idx - last) > STEPDURATION_MIN/SAMPLETIME and (idx - last) < STEPDURATION_MAX/SAMPLETIME:
            print(time.time(),"::STEP!")
            steps.append(idx)
        last=idx

    return steps


calibration = 0#hässlich
lines = []
calibrationDone = False
def update(frame):
    global figure
    global x_data
    global y_data
    global line
    global animation
    global calibration
    global calibrationDone
    #x_data.append(datetime.datetime.now())
    
    fifoLen=sen1.get_fifo_length()

    #print(fifoLen//6*6)
    accels = sen1.get_fifo_data_acc(fifoLen//6*6)
    
    y_data += accels[0]
    if len(y_data) > WINDOWSIZE:
        overweight = len(y_data) - WINDOWSIZE
        del y_data[0:overweight]
    x_data = range(0,len(y_data))
    line.set_data(x_data,y_data)
    figure.gca().relim()
    figure.gca().autoscale_view()
    if len(y_data) < WINDOWSIZE:
        calibration = calibrate(np.array(y_data))
        print("calibrating - please dont move! --",calibration)
    else:
        if not calibrationDone:
            print("calibration Done!")
        steps = detector(calibration,np.array(y_data))
        calibrationDone=True

        for l in lines:
            l.remove()
        lines.clear()

        for step in steps:
            markerLine = figure.gca().axvline(x=step,color='r',label='STEP',linewidth=5)
            lines.append(markerLine)



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