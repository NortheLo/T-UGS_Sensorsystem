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
PERIOD = CHUNK * 1/RATE * 1e3 # Time in ms between samplepoints
FIFO_WINDOW = 32
THRESHOLD_COEFF = 0.85 
MAX_STEP_TIME = 1300
MIN_STEP_TIME = 300
BANDPASS_FRQ = [10, 900]
BANDSTOP_FRQ = [50, 600]
FRQ_OF_INTEREST = [2] # Each frequency bin has a bw of 10.7hz (44.1kHz/2) / 2048 (nb of bins of the fft); So index multiply; 20Hz is interesting aswell as 400Hz;
                          # The higher frequencies seem to be more interesting to find out the hardness of the materials of the shoes and ground

class microphoneDetector():
    fifo = np.zeros((CHUNK, FIFO_WINDOW), dtype=np.int16)
    # Two dfft buffers for double buffering 
    dfft = np.zeros(CHUNK, dtype=np.int16)
    dfft_buffer = np.zeros(CHUNK, dtype=np.int16)
    calib_buffer = [[], []]
    lock = threading.Lock()
    threshold = [60, 60]
    new_data = False
    audio = pyaudio.PyAudio()
    stopEvent = Event()
    stream = None
    callback = None
    device = None
     
    def __init__(self):
        self.calibrate()

        # start recording
        self.stream = self.audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=self.device,
                        frames_per_buffer=CHUNK,
                        stream_callback=self.callbackFiltered)

        self.stream.start_stream()
        self.thread = Thread(target=self.runner)
    
    def calibrate(self):
            print("Started calibration routine")
            self.stream = self.audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=self.selectMic(),
                            frames_per_buffer=CHUNK,
                            stream_callback=self.callbackNonFiltered)
            self.new_data = False
            self.stream.start_stream()
            print("Calibrating...\nPlease be silent")
            while True:
                time.sleep(5)
                break
            print("Calibration ended!\nCalc the threshold based on the noise and input level")
            self.calcThreshold()
            self.closeAudio()

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

    def callbackNonFiltered(self, in_data, frame_count, time_info, flag):
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        dfft_calib = 20* np.log10(np.abs(scipy.fftpack.fft(audio_data)))
        self.calib_buffer[0].append(dfft_calib[FRQ_OF_INTEREST[0]])
        #self.calib_buffer[1].append(dfft_calib[FRQ_OF_INTEREST[1]])

        #print(dfft_calib)
        return (in_data, pyaudio.paContinue)

    def callbackFiltered(self, in_data, frame_count, time_info, flag):
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        # Butterworth bandpass  filter for filtering the high noised hissing from the cheap USB mic and the low end garbage
        # Butterworth bandstop to focus on the interesting frequencies for the step detection (~40Hz and ~600-700HZ)
        sos_bp = signal.butter(10, BANDPASS_FRQ, 'bp', fs=RATE, output='sos')
        sos_bs = signal.butter(10, BANDSTOP_FRQ, 'bs', fs=RATE, output='sos')
        audio_data_bp = signal.sosfilt(sos_bp, audio_data)
        audio_data_bs = signal.sosfilt(sos_bs, audio_data_bp)

        # Blackman window function as it has a wide main lobe and surpresses more the side lobes 
        audio_data_window = audio_data_bs * np.blackman(len(audio_data_bs))

        #time_t1 = time.time()
        self.lock.acquire()
        # FFT in dB drom the windowed audio signal
        self.dfft = 20* np.log10(np.abs(scipy.fftpack.fft(audio_data_window)))
        self.new_data = True
        self.lock.release()

        #print("Time of calculating the FFT\n--- %s seconds ----" % (time.time() - time_t1))
        return (in_data, pyaudio.paContinue)

    def calcThreshold(self):
        # Setting the THRESHOLD above a noise corridor the average
        max_frq = [0, 0] 
        avg_frq = [0, 0]

        for i in range(len(FRQ_OF_INTEREST)):
            max_frq[i] = np.amax(self.calib_buffer[i])
            avg_frq[i] = np.average(self.calib_buffer[i])

        for j in range(len(self.threshold)):
            self.threshold[j] = avg_frq[j] * THRESHOLD_COEFF
        
        #self.threshold[0] = 80
        print("Freq: " + str(FRQ_OF_INTEREST[0]*10) + "Hz    Max: " + str(max_frq[0]) + "    Avg: " + str(avg_frq[0]) + "    Threshold: " + str(self.threshold[0]))
        #print("Freq: " + str(FRQ_OF_INTEREST[1]*10) + "Hz    Max: " + str(max_frq[1]) + "    Avg: " + str(avg_frq[1]) + "    Threshold: " + str(self.threshold[1]))


    def intoFifo(self):
        while True:
            if self.new_data == True:
                
                self.lock.acquire()
                self.dfft_buffer = self.dfft
                self.new_data = False
                self.lock.release()
                
                #time_t1 = time.time()
                # Shift array to the left and in the first column is the backside buffer of the dfft 
                self.fifo = np.roll(self.fifo, 1)
                self.fifo[:, 0] = self.dfft_buffer
                #print("Time of FIFO manipulation\n--- %s seconds ----" % (time.time() - time_t1))

                # For seeing the values in the 20Hz bin in the FIFO
                print("FIFO at 20Hz ", self.fifo[2, :])
                #print("FIFO at 400Hz ", self.fifo[75, :])
                self.stepTimedelta()

    def stepTimedelta(self):
        for i in range(len(FRQ_OF_INTEREST)):
            #print("Observing freq: " + str(FRQ_OF_INTEREST[i]*10) + "Hz")
            freqbins_over_time = self.fifo[FRQ_OF_INTEREST[i], :]
            idx = np.where(freqbins_over_time > self.threshold[i])
            #print("idx %s" % idx)
            time_deltas = PERIOD * np.diff(idx)
            print("Step time deltas: \n%s" % time_deltas)
            
            for j in time_deltas[0]:
                if j < MAX_STEP_TIME and j > MIN_STEP_TIME:
                    self.callback(j)

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
        print ("\n+---------------------------------+")
        print ("| Press Ctrl+C to Break Recording |")
        print ("+---------------------------------+\n")

        while (not self.stopEvent.is_set()):
            self.intoFifo()
        self.closeAudio()
