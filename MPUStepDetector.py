from mpu6050 import mpu6050
import time
import math
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import scipy.signal
import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue

###SETTINGS###
SENSORAXIS = 1
WINDOWSIZE = 5000 # samples
SAMPLERATE = 500 # Hz

PEAKTHRESHHOLD = 500 # raw
SETTLEMAX = 500 # raw
NLARGEST = 100 # count

STEPDURATION_MIN = 50 # minimum time between steps in ms
STEPDURATION_MAX = 1300# maximum time between steps in ms

LOWPASS_CUTOFF = 45 #Hz
CALIBRATION_SAMPLES = 5000
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

def getRMS(buffer):
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

def fftCalc(buffer):
    N = len(buffer)
    yf = fft(buffer)
    xf = fftfreq(N,1/SAMPLERATE)
    return (xf,np.abs(yf))

def calibrate_still():
    print("calibrating still - dont move")
    data = []
    while True:
        time.sleep(0.1)
        fifoLen=sen1.get_fifo_length()
        if(fifoLen > 0):
            accels = sen1.get_fifo_data_acc(fifoLen//6*6)
            data += accels[SENSORAXIS]
        if(len(data) > CALIBRATION_SAMPLES):
            print("calibrate still success - RMS:")
            rms = getRMS(data)
            print(rms)
            return rms
    

def calibrate_centerFrequency(rms):
    print("calibrating center frequency - walk around")
    data = []
    b, a = scipy.signal.butter(6, 48/(SAMPLERATE/2), btype='low')
    while True:
        time.sleep(0.1)
        fifoLen=sen1.get_fifo_length()
        if(fifoLen > 0):
            accels = sen1.get_fifo_data_acc(fifoLen//6*6)
            data += accels[SENSORAXIS]
        if(len(data) > CALIBRATION_SAMPLES):
            print("calibrate Center success - Center freq:")
            data_calibrated = np.subtract(data,rms)
            filtered = scipy.signal.filtfilt(b, a, data_calibrated)
            fftX,fftY = fftCalc(filtered)
            indexMax = np.argsort(-fftY)[0]
            centerFreq = abs(fftX[indexMax]) # remove value if 0 is the greatest ( generally remove zero..)
            print(centerFreq)
            return centerFreq


lines = []
def update(frame):
    global figure
    global x_data
    global y_data
    global line
    global animation
    global rmsCalibration
    global centerCalibration
    global filtB,filtA
    #x_data.append(datetime.datetime.now())
    if rmsCalibration == 0:
        rmsCalibration = calibrate_still()
        centerCalibration = calibrate_centerFrequency(rmsCalibration)
        filtB, filtA = scipy.signal.butter(6, centerCalibration/(SAMPLERATE/2), btype='low')

    fifoLen=sen1.get_fifo_length()
    print(fifoLen)
    #print(fifoLen//6*6)
    accels = sen1.get_fifo_data_acc(fifoLen//6*6)
    
    y_data += accels[SENSORAXIS]
    if len(y_data) > WINDOWSIZE:
        overweight = len(y_data) - WINDOWSIZE
        del y_data[0:overweight]
    x_data = range(0,len(y_data))
    if(len(y_data) > 1000):
        ydat_calib = np.subtract(y_data,rmsCalibration)
        filtered = scipy.signal.filtfilt(filtB, filtA, ydat_calib)
        line.set_data(x_data,filtered)
        figure.gca().relim()
        figure.gca().autoscale_view()
        steps = detector(rmsCalibration,np.array(filtered))
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
    global rmsCalibration
    global centerCalibration
    if(checkSensors()):
        rmsCalibration = 0
        #rmsCalibration = calibrate_still()
        x_data, y_data = [], []

        figure = plt.figure()
        line, = plt.plot(x_data, y_data, '-')
        #sen1.reset_fifo()
        animation = FuncAnimation(figure, update, interval=1)
        plt.show()

if __name__ == "__main__":
    main()