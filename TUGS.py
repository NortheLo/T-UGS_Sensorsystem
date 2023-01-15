import time
import sys
import threading
import pyaudio
import numpy as np
import pylab
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fftshift
import scipy.fftpack
from scipy.ndimage import shift

## TO-DO: 
#       -Selecting the corresponding axis and calculating the delay between taps

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 2048
FIFO_WINDOW = 128
lock = threading.Lock()
new_data = False

FIFO = np.zeros((CHUNK, FIFO_WINDOW), dtype=np.int16)
 
# Two dfft buffers for double buffering 
dfft = np.zeros(CHUNK, dtype=np.int16)
dfft_buffer = np.zeros(CHUNK, dtype=np.int16)

i=0
f,ax = plt.subplots(2)

x = np.arange(10000)
y = np.random.randn(10000)

li, = ax[0].plot(x, y)
ax[0].set_xlim(0,1000)
ax[0].set_ylim(-5000,5000)
ax[0].set_title("Raw Audio Signal", loc='center', wrap=True)

li2, = ax[1].plot(x, y)
ax[1].set_xlim(0, 2e3)
ax[1].set_ylim(0,100)
ax[1].set_title("Fast Fourier Transform", loc='center', wrap=True)

plt.pause(0.001)
plt.tight_layout()

def selectMic():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    for i in range(0, numdevices):  
         if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
             print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

    print("Select microphone by id: ")
    return int(input())

def callback(in_data, frame_count, time_info, flag):
    global dfft
    global new_data
    
    audio_data = np.frombuffer(in_data, dtype=np.int16)

    # Butterworth bandpass  filter for filtering the high noised hissing from the cheap USB mic and the low end garbage
    # Butterworth bandstop to focus on the interesting frequencies for the step detection (~40Hz and ~600-700HZ)
    sos_bp = signal.butter(10, [10, 900], 'bp', fs=RATE, output='sos')
    sos_bs = signal.butter(10, [50, 600], 'bs', fs=RATE, output='sos')
    audio_data_bp = signal.sosfilt(sos_bp, audio_data)
    audio_data_bs = signal.sosfilt(sos_bs, audio_data_bp)
    
    # Blackman window function as it has the wide main lobe and surpresses more the side lobes 
    audio_data_window = audio_data_bs * np.blackman(len(audio_data_bs))
    
    time_t1 = time.time()
    lock.acquire()
    # FFT in dB drom the windowed audio signal, using all cores of the host
    dfft = 20* np.log10(np.abs(scipy.fftpack.rfft(audio_data_window)))
    new_data = True
    lock.release()
    print("Time of calculating the FFT\n--- %s seconds ----" % (time.time() - time_t1))
    
    return (in_data, pyaudio.paContinue)

def stepDetection():
    global FIFO
    global dfft 
    global dfft_buffer
    global new_data

    while True:
        if new_data == True:
            time_t1 = time.time()
            lock.acquire()
            ## Adding values to the FIFO 
            dfft_buffer = dfft
            lock.release()
            new_data = False
            plotFFT()
            ## Alternative but bit slower
            FIFO = np.roll(FIFO, 1)
            FIFO[:, 0] = dfft_buffer   
            print("Time of FIFO manipulation\n--- %s seconds ----" % (time.time() - time_t1))
        plotFFT()

def plotFFT():
    global dfft_buffer
    li2.set_xdata(np.arange(len(dfft_buffer))*10.)
    li2.set_ydata(dfft_buffer)
    plt.pause(0.0001)
    return True

def closeAudio():
        stream.stop_stream()
        stream.close()
        audio.terminate()
        sys.exit()

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=selectMic(),
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

def main():
    stream.start_stream()
    print ("\n+---------------------------------+")
    print ("| Press Ctrl+C to Break Recording |")
    print ("+---------------------------------+\n")
    keep_going = True
    
    try:
        while stream.is_active() and keep_going:
            stepDetection() 
    except (KeyboardInterrupt, SystemExit):
        keep_going = False
        closeAudio()

if __name__ == "__main__":
    main()

## Only for checking purposes ##
# Spectrogram from the windowed audio
#freq, times, spectrogram = signal.spectrogram(audio_data, RATE, window='blackman')

# Subplot with spectrogram
#spec_mesh = ax[2].pcolormesh(times, freq, 10.*np.log10(spectrogram), shading='gouraud')
#x_axis_fft = np.arange(len(audio_data))
#li.set_xdata(x_axis_fft)
#li.set_ydata(audio_data)

## Too slow
