from mpu6050 import mpu6050
import time
import numpy as np
from scipy.fft import fft, ifft, fftfreq, fftshift 
import scipy.signal
from threading import Thread
from threading import Event

###SETTINGS###
SENSORAXIS = 2
WINDOWSIZE = 5000 # samples
SAMPLERATE = 500 # Hz

PEAKTHRESHHOLD = 500 # raw
SETTLEMAX = 500 # raw
NLARGEST = 100 # count
EVENTDURATION = 200 # ms

STEPDURATION_MIN = 50 # minimum time between steps in ms
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
    callback = None
    calibration_rms = 15300
    calibration_center = 20
    calibration_threshhold = PEAKTHRESHHOLD
    stopEvent = Event()

    def __init__(self, address):
        self.sen1 = mpu6050(address)
        self.sen1.set_accel_range(self.sen1.ACCEL_RANGE_2G)
        self.sen1.enable_fifo()
        self.sen1.configure_fifo(self.sen1.FIFO_FLAG_AXYZ)
        self.sen1.setSampleRate(SAMPLERATE)
        self.sen1.reset_fifo()
        self.setFilterParameters(100,3)
        self.thread = Thread(target = self.runner)

    def getRMS(self,buffer):
        peaks = np.argpartition(buffer,-NLARGEST)[-NLARGEST:]
        bufferNoPeaks = np.delete(buffer,peaks)
        rms = np.sqrt(np.mean(bufferNoPeaks**2))
        return rms

    def getRawBuffer(self):
        fifoLen = self.sen1.get_fifo_length()
        accels = self.sen1.get_fifo_data_acc(fifoLen)
        return accels[SENSORAXIS]

    def updateWindowedBuffer(self):
        self.buffer += self.getRawBuffer()
        if len(self.buffer) > WINDOWSIZE:
            overweight = len(self.buffer) - WINDOWSIZE
            self.deleteWindow(overweight)
        return self.buffer

    def deleteWindow(self,upTo):
        del self.buffer[0:upTo]

    def detector(self,rms,threshhold):
        data = np.array(self.updateWindowedBuffer())
        data_calibrated = np.subtract(data,rms)
        if(len(data) < 30):
            return
        filteredBuf = scipy.signal.filtfilt(self.filtB,self.filtA,data_calibrated)[:WINDOWSIZE]
        buffer = filteredBuf
        peakInd = np.where(data_calibrated > threshhold)
        #print(buffer)
        last = len(buffer)
        for idx in peakInd[0]:
            stepDuration = (idx - last) * SAMPLETIME
            if stepDuration > STEPDURATION_MIN and stepDuration < STEPDURATION_MAX:
                print(time.time(),"::STEP!")
                self.deleteWindow(idx+int(EVENTDURATION/SAMPLETIME))
                if(self.callback != None):
                    self.callback(stepDuration)
            last=idx

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
                rms = self.getRMS(data)
                print(rms)
                return rms
        

    def calibrate_Steps(self,rms):
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
        filtered = scipy.signal.filtfilt(b, a, data_calibrated)
        fftX,fftY = self.fftCalc(filtered)
        centerFreq = abs(fftX[np.argsort(-fftY)[0]])
        if(centerFreq<1):
            centerFreq = abs(fftX[np.argsort(-fftY)[1]])
        b, a = scipy.signal.butter(3, centerFreq/(SAMPLERATE/2), btype='low')
        filtered = scipy.signal.filtfilt(b, a, data_calibrated)
        filtered_sorted_indices = np.argsort(filtered)
        sorted_data = filtered[filtered_sorted_indices]
        mean_StepThreshhold = np.mean(sorted_data[-NLARGEST : ])
        print(mean_StepThreshhold)
        print(centerFreq)
        return centerFreq,mean_StepThreshhold


    def calibrate(self):
        self.calibration_rms = self.calibrate_still()
        self.calibration_center,self.calibration_threshhold = self.calibrate_Steps(self.calibration_rms)
        self.setFilterParameters(self.calibration_center,3)

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

if __name__ == "__main__":
    global sd 
    sd = MPUStepDetector(0x68)
    sd.setCallback(test)
    sd.calibrate()
    sd.startAsync()
    while(True):
        time.sleep(1)