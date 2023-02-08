import time
import sys
import threading
from threading import Thread
from threading import Event
import pyaudio
import numpy as np
import pylab
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fftshift
import scipy.fftpack
from scipy.ndimage import shift

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 2048
MAX_STEP_TIME = 1.3
MIN_STEP_TIME = 0.35
LP_FRQ = 50
RESMPL_FACTOR = 8
DELTA_TIME_SAMPLE = 1/(RATE//RESMPL_FACTOR)
EVENT_DURATION = 0.3
class microphoneDetector():
    audio = pyaudio.PyAudio()
    lock = threading.Lock()
    new_data = False
    stopEvent = Event()
    stream = None
    callback = None
    device = None
    audio_data = None
    fifo = np.zeros(int((CHUNK/RESMPL_FACTOR)*30))
    enableFilter = False
    threshold = 1500
    sos_lp = None
    test=0

    def __init__(self, filter=False):
        self.enableFilter = filter
       
        if(self.enableFilter):
            self.sos_lp = signal.butter(10, LP_FRQ, 'lp', fs=RATE, output='sos')

        # start recording
        self.stream = self.audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=1,
                        frames_per_buffer=CHUNK,
                        stream_callback=self.callbackAudio)

        self.stream.start_stream()
        self.thread = Thread(target=self.runner)
    

    def selectMic(self):
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):  
             if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                 print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

        print("Select microphone by id: ")
        self.device = 1#int(input())
        return self.device

    def callbackAudio(self, in_data, frame_count, time_info, flag):
        
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        if(self.enableFilter):
            audio_data = signal.sosfilt(self.sos_lp, audio_data)
        
        self.lock.acquire()
        self.audio_data = audio_data
        self.new_data = True
        self.lock.release()
        #print(audio_data)
       
        return (in_data, pyaudio.paContinue)

    def calibrate(self):
        print("Calibration\nPlease make some steps!")
        i = 0
        while (i  < 100) and (not self.stopEvent.is_set()):
            if self.intoFifo():
                i += 1
        self.setThreshold(self.fifo)    
        self.delFifo()        
    
    def setThreshold(self, buffer):
        # Setting the THRESHOLD above a noise corridor the average

        peak = np.amax(np.absolute(buffer))
        avg = np.average(np.absolute(buffer))
        self.threshold = (self.getRMS(buffer)+peak) /2 #~150-200 for steps when mic hole is pointing to the ground 
        #self.threshold = 150 
        print("Max: " + str(peak) + "    Avg: " + str(avg) + "    Threshold: " + str(self.threshold))

    def getRMS(self, buffer):
        rms = np.sqrt(np.mean(np.square(buffer))) 
        return rms

    def intoFifo(self):
        if self.new_data == False:
            return False
        else:
            self.fifo = np.roll(self.fifo, CHUNK//(RESMPL_FACTOR))
            idx = 0
            self.lock.acquire()
            for i in range(0, CHUNK, RESMPL_FACTOR):
                self.fifo[idx] = self.audio_data[i]
                idx += 1
            self.new_data = False
            self.lock.release()
            return True
    
    def delFifo(self, startingIndex=0):
        for i in range(startingIndex, len(self.fifo)):
            self.fifo[i] = 0

    def stepTimedelta(self, buffer):
        idx_Peak = np.where(buffer > self.threshold)[0]
        
        if(len(idx_Peak) == 0):
            return
        idx_time = (np.amax(idx_Peak)-np.amin(idx_Peak)) * DELTA_TIME_SAMPLE
        if idx_time < MAX_STEP_TIME and idx_time > MIN_STEP_TIME:
            self.callback(int(idx_time*1000))
            x_data = range(0,len(buffer))
            

            #plt.plot(x_data,buffer)
            #plt.show()
            self.delFifo(np.amax(idx_Peak)-int(EVENT_DURATION/DELTA_TIME_SAMPLE))
            #plt.plot(x_data,self.fifo)
            #plt.show()

        # for idx in idx_Peak:
        #    for idy in idx_Peak:
        #         time_delta = (idy - idx) * DELTA_TIME_SAMPLE
        #         #print(time_delta)
        #         if time_delta < MAX_STEP_TIME and time_delta > MIN_STEP_TIME:
        #             if self.getRMS(self.fifo[idy:idx]) > self.threshold:
        #                 break

        #             self.callback(time_delta)
        #             self.delFifo(idy-int(EVENT_DURATION/DELTA_TIME_SAMPLE))
        #             return

    def closeAudio(self):
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
    
    def startAsync(self):
        self.thread.start()

    def stopAsync(self):
        self.stopEvent.set()

    def setCallback(self, callback):
            self.callback = callback

    def runner(self):
        #self.calibrate()

        print ("\n+---------------------------------+")
        print ("| Press Ctrl+C to Break Recording |")
        print ("+---------------------------------+\n")

        while (not self.stopEvent.is_set()):
            if self.intoFifo():
                self.stepTimedelta(np.absolute(self.fifo))
        self.closeAudio()

def micCallback(stepDuration): # callback function
    print("mic with duration: ",stepDuration)

if __name__ == "__main__":
    micDetector = microphoneDetector(filter=True)
    micDetector.setCallback(micCallback)
    micDetector.calibrate()
    micDetector.runner()
    #micDetector.startAsync()

    while(True):
        time.sleep(60)
    micDetector.stopAsync()