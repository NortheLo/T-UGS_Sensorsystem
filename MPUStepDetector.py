from mpu6050 import mpu6050
import time
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import scipy.signal
from threading import Thread
from threading import Event
import matplotlib.pyplot as plt
import datetime
import math

###SETTINGS###
SENSORAXIS = 2
WINDOWSIZE = 3000 # samples
FILTER_INVALIDZONE = 150
FILTER_MIN = 20 # Hz
SAMPLERATE = 500 # Hz

THRESHHOLD_SCALER=0.5
PEAKTHRESHHOLD = 300 # raw
SETTLEMAX = 500 # raw
NLARGEST = 100 # count
EVENTDURATION = 300 # ms

STEPDURATION_MIN = 350 # minimum time between steps in ms
STEPDURATION_MAX = 1300# maximum time between steps in ms

LOOPDELAY = 0.001 #s

###CALIBRATION SETTINGS###
CALIBRATION_SAMPLES = 5000
NOTCHFREQ = 50
QUALITYFACTOR=30

###CALCULATED VALUES###
SAMPLETIME = 1/SAMPLERATE*1000 # ms


###################################################

class MPUStepDetector():
    buffer = []
    stepTracker = [5000,5000,4000]
    callback = None
    calibration_rms = 15250
    calibration_center = 20
    calibration_threshhold = PEAKTHRESHHOLD
    calibration_level_1m = 0
    stopEvent = Event()
    enableFilter=True
    last=datetime.datetime.now()
    test=False
    invalidRange = 0
    def __init__(self, address):
        self.sen1 = mpu6050(address)
        self.sen1.set_accel_range(self.sen1.ACCEL_RANGE_2G)
        self.sen1.enable_fifo()
        self.sen1.configure_fifo(self.sen1.FIFO_FLAG_AXYZ)
        self.sen1.setSampleRate(SAMPLERATE)
        self.sen1.reset_fifo()
        self.setFilterParameters(100,3)
        self.thread = Thread(target = self.runner)
        x = range(0,5000)
        y = range(0,5000)
        self.counter = 0
            
        
        

        
    def getRMS(self,buffer):
        peaks = np.argpartition(buffer,-NLARGEST)[-NLARGEST:]
        bufferNoPeaks = np.delete(buffer,peaks)
        rms = np.sqrt(np.mean(bufferNoPeaks**2))
        rmsPeaks = np.sqrt(np.mean(np.array(buffer)[peaks]**2))
        return rms,rmsPeaks

    def getRawBuffer(self):
        fifoLen = self.sen1.get_fifo_length()
        accels = self.sen1.get_fifo_data_acc(fifoLen)
        return accels[SENSORAXIS]

    def updateWindowedBuffer(self):
        rawData = self.getRawBuffer()
        self.buffer += rawData
        overweight=0
        if len(self.buffer) > WINDOWSIZE:
            overweight = len(self.buffer) - WINDOWSIZE
            self.deleteWindow(self.buffer,overweight)
        #print(len(rawData))
        #print(len(self.buffer))
        return overweight,self.buffer

    def deleteWindow(self,buffer,upTo):
        del buffer[0:upTo]
        x_data = range(0,len(buffer))
        #print(self.buffer)

    def detector(self,rms,threshhold):
        readLen,wUpdate=self.updateWindowedBuffer()
        
        self.stepTracker=np.subtract(self.stepTracker,readLen).tolist()
        
        if(self.invalidRange > 0):
            self.invalidRange-=readLen

        data = np.array(wUpdate)
        data_calibrated = np.subtract(data,rms)
        #print(len(data))
        if(len(data) < 50):
            return
	
        if(self.enableFilter):
            window = scipy.signal.windows.tukey(len(data_calibrated))
            data_windowed = data_calibrated * window
            filteredBuf = scipy.signal.filtfilt(self.filtB,self.filtA,data_calibrated)[:WINDOWSIZE]
            buffer = filteredBuf[FILTER_INVALIDZONE:len(data_calibrated)-FILTER_INVALIDZONE]
        else:
            buffer = data_calibrated
        validBuffer = buffer[int(self.invalidRange+EVENTDURATION/SAMPLETIME):]
        peakInd = np.where(buffer > threshhold)[0]
        
        for idx in peakInd:
            for idx2 in peakInd:
                stepDuration = (idx - idx2) * SAMPLETIME
                if stepDuration > STEPDURATION_MIN and stepDuration < STEPDURATION_MAX: # if positive, idx is greater and therefore we have to delete up to idx2 to prevent deleting both steps     
                    #theoretically we have to check if there are peaks between the peaks, and if, we have to classify if it is noise or not. but this gets out of hand quickly.
                    #check RMS between peaks
                    rmsCheck,rmsP = self.getRMS(buffer[idx2:idx])
                    if(rmsCheck > threshhold):
                        print("excessive noise detected, invalidating step!")
                        self.deleteWindow(self.buffer,idx2+int(EVENTDURATION/SAMPLETIME)+FILTER_INVALIDZONE)
                        self.sen1.reset_fifo()
                        return
                    

                    distance = 0
                    faktor = ((buffer[idx2]+buffer[idx])/2) / self.calibration_level_1m
                    if(faktor > 1): # farther than 1m
                        distance = 3/math.sqrt(faktor)
                    #print(distance)

                    self.invalidRange=idx2
                    x_data = range(0,len(self.buffer))
                    #plt.plot(x_data,self.buffer)
                    #plt.show()
                    self.deleteWindow(self.buffer,idx2+int(EVENTDURATION/SAMPLETIME)+FILTER_INVALIDZONE)
                    x_data = range(0,len(self.buffer))
                    #plt.plot(x_data,self.buffer)
                    #plt.show()
                    print(int(stepDuration),"::STEP!")
                    if(self.callback != None):
                        self.callback(int(stepDuration))
                    self.sen1.reset_fifo()
                    return

#Problem for Doku: signal gets filteres everytime, whole buffer changes, end is abrupt and generates unwanted spikes --> tukey window
#tukey window too much latency and really not good.


    def setFilterParameters(self,centerFreq,order):
        #self.filtB, self.filtA = scipy.signal.butter(order, centerFreq/(SAMPLERATE/2), btype='low')
        self.filtB, self.filtA = scipy.signal.butter(3, [centerFreq-20, centerFreq+20],fs=SAMPLERATE, btype='band')

    def fftCalc(self,buffer):
        N = len(buffer)
        yf = fft(buffer)
        xf = fftfreq(N,1/SAMPLERATE)
        return (xf,np.abs(yf))

    def setCallback(self,callback):
        self.callback = callback

    def calibrate_still(self):
        print("calibrating still - dont move")
        data = []
        while True:
            time.sleep(0.1)
            fifoLen=self.sen1.get_fifo_length()
            if(fifoLen > 0):
                accels = self.sen1.get_fifo_data_acc(fifoLen//6*6)
                data += accels[2]
            if(len(data) > CALIBRATION_SAMPLES):
                print("calibrate still success - RMS:")
                rms,rmsPeaks = self.getRMS(data)
                print(rms)
                print(rmsPeaks)
                return rms,rmsPeaks
        

    def calibrate_Steps(self,rms,rmsPeaks):
        print("calibrating center frequency - walk around at 1m distance to the sensor(at least 5 steps)")
        data = []
        b, a = scipy.signal.iirnotch(NOTCHFREQ,QUALITYFACTOR,SAMPLERATE)
        #scipy.signal.butter(3, 48/(SAMPLERATE/2), btype='low')
        while len(data) < CALIBRATION_SAMPLES:
            time.sleep(0.1)
            fifoLen=self.sen1.get_fifo_length()
            if(fifoLen > 0):
                accels = self.sen1.get_fifo_data_acc(fifoLen//6*6)
                data += accels[SENSORAXIS]

        print("calibrate Center success - mean and center freq:")
        data_calibrated = np.subtract(data,rms)
        centerFreq=0
        if(self.enableFilter):
            filtered = scipy.signal.filtfilt(b, a, data_calibrated)
            fftX,fftY = self.fftCalc(filtered)
            centerFreq = abs(fftX[np.argsort(-fftY)[0]])
            i=1
            while(centerFreq<FILTER_MIN or len(fftX) == i-1):
                centerFreq = abs(fftX[np.argsort(-fftY)[i]])
                i+=1
            if(centerFreq < FILTER_MIN):
                print("center frequency would be below limit. capping to minimum frequency.")
            b, a = scipy.signal.butter(3, centerFreq/(SAMPLERATE/2), btype='low')
            buf = scipy.signal.filtfilt(b, a, data_calibrated)
        else:
            buf=data_calibrated

        sorted_indices = np.argsort(buf)
        sorted_data = buf[sorted_indices]
        mean_max = np.mean(sorted_data[-NLARGEST : ])
        threshhold = (mean_max + (rmsPeaks-rms))/2#(1-THRESHHOLD_SCALER)*mean_max + THRESHHOLD_SCALER*(rmsPeaks-rms)
        #threshhold currently is between max noise and mean of peaks
        print(threshhold)
        print(centerFreq)
        return centerFreq,threshhold,(rmsPeaks-rms)


    def calibrate(self):
        self.calibration_rms,rmsPeaks = self.calibrate_still()
        self.calibration_center,self.calibration_threshhold,self.calibration_level_1m = self.calibrate_Steps(self.calibration_rms,rmsPeaks)
        print("threshhold: ",self.calibration_threshhold)
        if(self.enableFilter):
            self.setFilterParameters(self.calibration_center,3)

    def setRms(self,rms):
        self.calibration_rms = rms
    def setThreshhold(self,thresh):
        self.calibration_threshhold=thresh
    def enableFilter(self,status):
        self.enableFilter=status

    def runner(self):
        print("starting")
        while(not self.stopEvent.is_set()):
            self.detector(self.calibration_rms,self.calibration_threshhold)
            time.sleep(LOOPDELAY)
        print("exiting...")

    def startAsync(self):    
        self.thread.start()

    def stopAsync(self):
        self.stopEvent.set()

def test(var):
    pass
    #print("hooray: ",var)



# if __name__ == "__main__":
#     global sd 
#     sd = MPUStepDetector(0x68)
#     sd.setCallback(test)
#     #sd.calibrate()
#     sd.setFilterParameters(20,3)
#     sd.startAsync()
#     while(True):
#         time.sleep(1)

if __name__ == "__main__":
    global sd 
    sd = MPUStepDetector(0x68)
    sd.setCallback(test)
    sd.calibrate()
    #sd.setFilterParameters(11,3)
    sd.enableFilter(True)
    sd.runner()
    while(True):
        time.sleep(1)
