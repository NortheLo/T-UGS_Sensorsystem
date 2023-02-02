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
MAX_STEP_TIME = 1300
MIN_STEP_TIME = 300
LP_FRQ = 50
DELTA_TIME_SAMPLE = 1/RATE
RESMPL_FACTOR = 8

class microphoneDetector():
    audio = pyaudio.PyAudio()
    calib_buffer = [[], []]
    lock = threading.Lock()
    new_data = False
    stopEvent = Event()
    stream = None
    callback = None
    device = None
    audio_data = None
    fifo = np.zeros(int((CHUNK/RESMPL_FACTOR)*30))
    enableFilter = False
    threshold = 500
     
    def __init__(self):
        #self.calibrate()

        # start recording
        self.stream = self.audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=self.selectMic(),
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
        self.device = int(input())
        return self.device

    def callbackAudio(self, in_data, frame_count, time_info, flag):
        
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        if(self.enableFilter):
            sos_bp = signal.butter(10, LP_FRQ, 'lp', fs=RATE, output='sos')
            audio_data = signal.sosfilt(sos_bp, audio_data)
        
        self.lock.acquire()
        self.audio_data = audio_data
        self.new_data = True
        self.lock.release()
       
        return (in_data, pyaudio.paContinue)

    def setThreshold(self, buffer):
        # Setting the THRESHOLD above a noise corridor the average

        #peak = np.amax(buffer)
        avg = np.average(buffer)
        self.threshold = avg 
        
        #print("Max: " + str(peak) +
        print("    Avg: " + str(avg) + "    Threshold: " + str(self.threshold))

    def intoFifo(self):
        if self.new_data == True:
            self.fifo = np.roll(self.fifo, CHUNK//RESMPL_FACTOR)
            idx = 0
            self.lock.acquire()
            for i in range(0, CHUNK, RESMPL_FACTOR):
                self.fifo[idx] = self.audio_data[i]
                idx += 1
            self.new_data = False
            self.lock.release()

            self.stepTimedelta(np.absolute(self.fifo))
                

    def deleteFifoSection(self, buffer, index):
        section = index // (CHUNK/8)
         
        for i in range(section, section+(CHUNK//RESMPL_FACTOR), 1):
            buffer[i] = 0

    def stepTimedelta(self, buffer):
        idx_Peak = np.where(buffer > self.threshold)[0]
        #time_deltas = np.diff(idx)
        #print("Time deltas:", time_deltas)
      
        for idx in idx_Peak:
            for idy in idx_Peak:
                time_delta = (idx - idy) * DELTA_TIME_SAMPLE

                if time_delta < MAX_STEP_TIME and time_delta > MIN_STEP_TIME:
                    print("Step ", time_delta)
      
       # for i in range(len(FRQ_OF_INTEREST)):
       #     #print("Observing freq: " + str(FRQ_OF_INTEREST[i]*10) + "Hz")
       #     freqbins_over_time = self.fifo[FRQ_OF_INTEREST[i], :]
       #     idx = np.where(freqbins_over_time > self.threshold[i])
       #     #print("idx %s" % idx)
       #     time_deltas = PERIOD * np.diff(idx)
       #     print("Step time deltas: \n%s" % time_deltas)
       #     
       #     for j in time_deltas[0]:
       #         if j < MAX_STEP_TIME and j > MIN_STEP_TIME:
       #             self.callback(j)

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
        buffer = []
        print("Calibration\nPlease dont make any noises!")
        
       #i = 0
       #while i  < 5:
       #    if self.new_data == True:
       #        buffer += self.audio_data
       #    i += 1
       #self.setThreshold(buffer)    

        print ("\n+---------------------------------+")
        print ("| Press Ctrl+C to Break Recording |")
        print ("+---------------------------------+\n")

        while (not self.stopEvent.is_set()):
            self.intoFifo()
            
        self.closeAudio()

