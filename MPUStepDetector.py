from mpu6050 import mpu6050
import time
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import scipy.signal
from threading import Thread
from threading import Event
import matplotlib.pyplot as plt
import datetime

###SETTINGS###
SENSORAXIS = 2
WINDOWSIZE = 5000 # samples
FILTER_WINDOWSIZE = 2000 #samples
FILTER_APPENDIDX = 1000# samples
SAMPLERATE = 500 # Hz

PEAKTHRESHHOLD = 300 # raw
SETTLEMAX = 500 # raw
NLARGEST = 100 # count
EVENTDURATION = 500 # ms

STEPDURATION_MIN = 550 # minimum time between steps in ms
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
    stopEvent = Event()
    enableFilter=True
    last=datetime.datetime.now()
    test=0
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
        if len(self.buffer) > WINDOWSIZE:
            overweight = len(self.buffer) - WINDOWSIZE
            self.deleteWindow(self.buffer,overweight)
        #print(len(rawData))
        #print(len(self.buffer))
        return len(rawData),self.buffer

    def deleteWindow(self,buffer,upTo):
        del buffer[0:upTo]
        x_data = range(0,len(buffer))
        #print(self.buffer)

    def detector(self,rms,threshhold):
        readLen,wUpdate=self.updateWindowedBuffer()
        
        self.stepTracker=np.subtract(self.stepTracker,readLen).tolist()
        self.test+=readLen
        #print(self.test)
        #print(self.stepTracker)
        self.stepTracker = [i for i in self.stepTracker if i > 0]

        data = np.array(wUpdate)
        data_calibrated = np.subtract(data,rms)
        if(len(data) < 30):
            return

        if(self.enableFilter):
            window = scipy.signal.windows.tukey(len(data_calibrated))
            data_windowed = data_calibrated * window
            filteredBuf = scipy.signal.filtfilt(self.filtB,self.filtA,data_windowed)[:WINDOWSIZE]
            buffer = filteredBuf
        else:
            buffer = data_calibrated

        peakInd = np.where(buffer > threshhold)[0]

        #print(buffer)
        # if(len(peakInd)>0):
        #     print(peakInd[0])
        for idx in peakInd:
            for idx2 in peakInd:
                stepDuration = (idx - idx2) * SAMPLETIME
                if stepDuration > STEPDURATION_MIN and stepDuration < STEPDURATION_MAX: # if positive, idx is greater and therefore we have to delete up to idx2 to prevent deleting both steps         
                    already = np.any(np.isclose(self.stepTracker,idx,atol=EVENTDURATION/SAMPLETIME))

                    
                    print(time.time(),"::STEP!")
                    self.stepTracker.append(idx2)
                    x_data = range(0,len(self.buffer))
                    #plt.plot(x_data,self.buffer)
                    #plt.show()
                    self.deleteWindow(self.buffer,idx2+int(EVENTDURATION/SAMPLETIME))
                    x_data = range(0,len(self.buffer))
                    #plt.plot(x_data,self.buffer)
                    #plt.show()
                    if(self.callback != None):
                        self.callback(stepDuration)
                    self.sen1.reset_fifo()

                    return

#Problem for Doku: signal gets filteres everytime, whole buffer changes, end is abrupt and generates unwanted spikes --> Hamming window



    def setFilterParameters(self,centerFreq,order):
        self.filtB, self.filtA = scipy.signal.butter(order, centerFreq/(SAMPLERATE/2), btype='low')

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
        print("calibrating center frequency - walk around (at least 5 steps)")
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
            if(centerFreq<1):
                centerFreq = abs(fftX[np.argsort(-fftY)[1]])
            b, a = scipy.signal.butter(3, centerFreq/(SAMPLERATE/2), btype='low')
            buf = scipy.signal.filtfilt(b, a, data_calibrated)
        else:
            buf=data_calibrated

        sorted_indices = np.argsort(buf)
        sorted_data = buf[sorted_indices]
        mean_max = np.mean(sorted_data[-NLARGEST : ])
        threshhold = (mean_max + (rmsPeaks-rms))/2
        #threshhold currently is between max noise and mean of peaks
        print(threshhold)
        print(centerFreq)
        return centerFreq,threshhold


    def calibrate(self):
        self.calibration_rms,rmsPeaks = self.calibrate_still()
        self.calibration_center,self.calibration_threshhold = self.calibrate_Steps(self.calibration_rms,rmsPeaks)
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
        while(not self.stopEvent.is_set()):
            self.detector(self.calibration_rms,self.calibration_threshhold)
            time.sleep(LOOPDELAY)
        print("exiting...")

    def startAsync(self):    
        self.thread.start()

    def stopAsync(self):
        self.stopEvent.set()

def test(var):
    print("hooray: ",var)



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
    #sd.calibrate()
    sd.setFilterParameters(100,3)
    sd.enableFilter(False)
    sd.runner()
    while(True):
        time.sleep(1)
